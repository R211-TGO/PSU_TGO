from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from ...models import FormAndFormula, Scope, Material
from datetime import datetime
from ..utils.acl import permissions_required_all 

module = Blueprint("emissions_scope", __name__, url_prefix="/emissions-scope")
@module.route("/", methods=["GET"])
@login_required
@permissions_required_all(['view_scope'])
def emissions_scope():
    # รับปีที่เลือกจาก query parameter หรือใช้ปีปัจจุบันเป็นค่าเริ่มต้น
    selected_year = request.args.get('year', default=datetime.now().year, type=int) 
    # ดึงข้อมูล Scope ที่ตรงกับ campus และ department ของ current_user
    scopes = Scope.objects(
        campus=current_user.campus,
        department=current_user.department
    ).order_by("ghg_scope", "ghg_sup_scope")
    
    # ดึงปีทั้งหมดที่มีในฐานข้อมูล Material สำหรับ dropdown
    all_years = Material.objects().distinct("year")
    all_years = sorted([year for year in all_years if year is not None], reverse=True)
    
    # ถ้าไม่มีปีในฐานข้อมูล ให้เพิ่มปีปัจจุบัน
    if not all_years:
        all_years = [datetime.now().year]
    elif selected_year not in all_years:
        all_years.append(selected_year)
        all_years.sort(reverse=True)
    
    # จัดกลุ่ม Scope ตาม ghg_scope
    grouped_scopes = {}
    overall_progress = 0
    total_sources = len(scopes)
    completed = 0
    in_progress = 0
    not_started = 0
    
    for scope in scopes:
        main_scope = f"Scope {scope.ghg_scope}"
        if main_scope not in grouped_scopes:
            grouped_scopes[main_scope] = []
        
        # คำนวณ Progress สำหรับ Scope นี้ (เฉพาะปีที่เลือก)
        progress = calculate_scope_progress(scope, selected_year)
        
        # กำหนดสถานะตาม Progress
        if progress == 100:
            status = "Completed"
            completed += 1
        elif progress > 0:
            status = "In progress"
            in_progress += 1
        else:
            status = "Not started"
            not_started += 1
        
        # เพิ่ม Progress รวม
        overall_progress += progress
        
        # เพิ่ม progress และ status เข้าไปใน scope object
        scope.progress = round(progress, 1)
        scope.status = status
        
        # ส่ง scope object ทั้งหมดไปเลย
        grouped_scopes[main_scope].append(scope)
    
    # คำนวณ Overall Progress
    overall_progress = round(overall_progress / total_sources, 1) if total_sources > 0 else 0
    
    return render_template(
        "/emissions-scope/emissions-scope.html",
        user=current_user,
        mockup_data={
            "overall_progress": overall_progress,
            "total_sources": total_sources,
            "in_progress": in_progress,
            "not_started": not_started,
            "completed": completed,
            "scopes": grouped_scopes,
            "selected_year": selected_year,
            "all_years": all_years
        }
    )

def calculate_scope_progress(scope, selected_year):
    """
    คำนวณ Progress ของ Scope สำหรับปีที่เลือก
    Progress = (จำนวนช่องที่กรอกแล้ว / (head_table × 12)) × 100
    """
    # จำนวน head_table
    num_head_table = len(scope.head_table)
    
    if num_head_table == 0:
        return 0  # ถ้าไม่มี head_table ให้ progress = 0
    
    # จำนวนช่องทั้งหมดที่ต้องกรอก = head_table × 12 เดือน (เฉพาะปีที่เลือก)
    total_fields_required = num_head_table * 12
    
    if total_fields_required == 0:
        return 0
    
    # ดึง Material ที่เกี่ยวข้องกับ Scope นี้ในปีที่เลือก
    materials = Material.objects(
        scope=scope.ghg_scope,
        sub_scope=scope.ghg_sup_scope,
        year=selected_year,
        campus=current_user.campus,
        department=current_user.department
    )

    # นับจำนวนช่องที่กรอกข้อมูลแล้ว
    filled_fields = len(materials)
    
    # คำนวณ Progress
    progress = (filled_fields / total_fields_required) * 100
    
    # จำกัดไม่ให้เกิน 100%
    return min(progress, 100)


@module.route("/add", methods=["GET", "POST"])
@login_required
@permissions_required_all(['edit_scope'])
def add_scope():
    if request.method == "POST":
        action = request.form.get("action")  # ตรวจสอบการกระทำ (fetch_sub_scope หรือ save)
        ghg_scope = request.form.get("ghg_scope")
        ghg_sup_scope = request.form.get("ghg_sup_scope")
        ghg_name = request.form.get("ghg_name")
        ghg_desc = request.form.get("ghg_desc")
        head_table = request.form.getlist("head_table")  # รับค่าของ Head Table

        # หากผู้ใช้กดปุ่ม "บันทึก"
        if action == "save":
            # ตรวจสอบว่าทุกช่องถูกกรอก
            if not ghg_scope or not ghg_sup_scope or not ghg_name or not ghg_desc or not head_table:
                # ดึงข้อมูลที่ตรงกับ campus และ department ของ current_user
                scopes = Scope.objects(
                    campus=current_user.campus,
                    department=current_user.department
                ).distinct("ghg_scope")
                latest_sub_scope = None
                # ดึง material_names ที่ตรงกับ campus และ department ของ current_user
                material_names = FormAndFormula.objects(
                    campus=current_user.campus,
                    department=current_user.department
                ).distinct("material_name")
                return render_template(
                    "/emissions-scope/add-scope.html",
                    error="กรุณากรอกข้อมูลให้ครบทุกช่อง",
                    scopes=scopes,
                    latest_sub_scope=latest_sub_scope,
                    material_names=material_names
                )

            # ตรวจสอบว่ามี Scope ซ้ำหรือไม่ (ภายใน campus และ department เดียวกัน)
            existing_scope = Scope.objects(
                ghg_scope=int(ghg_scope),
                ghg_sup_scope=int(ghg_sup_scope),
                campus=current_user.campus,
                department=current_user.department
            ).first()
            if existing_scope:
                # ดึงข้อมูลที่ตรงกับ campus และ department ของ current_user
                scopes = Scope.objects(
                    campus=current_user.campus,
                    department=current_user.department
                ).distinct("ghg_scope")
                latest_sub_scope = None
                # ดึง material_names ที่ตรงกับ campus และ department ของ current_user
                material_names = FormAndFormula.objects(
                    campus=current_user.campus,
                    department=current_user.department
                ).distinct("material_name")
                return render_template(
                    "/emissions-scope/add-scope.html",
                    error="Scope และ Sub-Scope นี้มีอยู่แล้วในแผนกและวิทยาเขตของคุณ",
                    scopes=scopes,
                    latest_sub_scope=latest_sub_scope,
                    material_names=material_names
                )

            # สร้าง Scope ใหม่พร้อมกับ campus และ department ของ current_user
            scope = Scope(
                ghg_scope=int(ghg_scope),
                ghg_sup_scope=int(ghg_sup_scope),
                ghg_name=ghg_name,
                ghg_desc=ghg_desc,
                campus=current_user.campus,  # เพิ่ม campus ของ current_user
                department=current_user.department,  # เพิ่ม department ของ current_user
                head_table=head_table  # บันทึกค่า Head Table ตามที่หน้าเว็บส่งมา
            )
            scope.save()

            # เรนเดอร์ HTML ของ add-scope-success.html
            return render_template(
                "/emissions-scope/add-scope-success.html",
                success="Scope added successfully!"
            )

    # กรณี GET: ดึง Scope หลักและ material_name ที่ตรงกับ campus และ department ของ current_user
    scopes = Scope.objects(
        campus=current_user.campus,
        department=current_user.department
    ).distinct("ghg_scope")
    latest_sub_scope = None
    
    # ดึง material_names ที่ตรงกับ campus และ department ของ current_user
    material_names_objects = FormAndFormula.objects()
    material_names = [x.material_name for x in material_names_objects]  # ดึงชื่อวัสดุทั้งหมด
    
    return render_template(
        "/emissions-scope/add-scope.html",
        scopes=scopes,
        latest_sub_scope=latest_sub_scope,
        material_names=material_names
    )



@module.route("/get-latest-sub-scope", methods=["POST"])
@login_required
@permissions_required_all(['edit_scope'])
def get_latest_sub_scope():
    ghg_scope = request.json.get("ghg_scope")  # รับข้อมูลจาก JSON
    if not ghg_scope or not ghg_scope.isdigit():
        return jsonify({"latest_sub_scope": 1})  # ถ้า Scope หลักว่างหรือไม่ใช่ตัวเลข ให้เริ่มที่ 1
    
    ghg_scope = int(ghg_scope)
    
    # แก้ไข: เพิ่มการกรองตาม campus และ department ของ current_user
    latest_sub_scope = Scope.objects(
        ghg_scope=ghg_scope,
        campus=current_user.campus,
        department=current_user.department
    ).order_by("-ghg_sup_scope").first()
    
    latest_sub_scope = latest_sub_scope.ghg_sup_scope + 1 if latest_sub_scope else 1
    return jsonify({"latest_sub_scope": latest_sub_scope})
    


@module.route("/edit/<int:ghg_scope>/<int:ghg_sup_scope>", methods=["GET", "POST"])
@login_required
@permissions_required_all(['edit_scope'])
def edit_scope(ghg_scope, ghg_sup_scope):
    # ค้นหา Scope ที่ต้องการแก้ไขตาม campus และ department ของ current_user
    scope = Scope.objects(
        ghg_scope=ghg_scope,
        ghg_sup_scope=ghg_sup_scope,
        campus=current_user.campus,
        department=current_user.department
    ).first()
    
    if not scope:
        return render_template(
            "/emissions-scope/edit-scope-error.html",
            error="ไม่พบ Scope ที่ต้องการแก้ไข หรือคุณไม่มีสิทธิ์เข้าถึง"
        )
    
    if request.method == "POST":
        ghg_name = request.form.get("ghg_name")
        ghg_desc = request.form.get("ghg_desc")
        head_table = request.form.getlist("head_table")
        
        # ตรวจสอบข้อมูลที่จำเป็น
        if not ghg_name or not ghg_desc:
            # ดึง material_names สำหรับแสดงในฟอร์ม
            material_names_objects = FormAndFormula.objects()
            material_names = [x.material_name for x in material_names_objects]
            
            return render_template(
                "/emissions-scope/edit-scope.html",
                scope=scope,
                material_names=material_names,
                error="กรุณากรอกข้อมูลให้ครบทุกช่อง"
            )
        
        # อัปเดตข้อมูล
        scope.ghg_name = ghg_name
        scope.ghg_desc = ghg_desc
        scope.head_table = head_table if head_table else []
        scope.save()
        
        return render_template(
            "/success/success.html",
            success="แก้ไข Scope สำเร็จ!"
        )
    
    # กรณี GET: แสดงฟอร์มแก้ไข
    # ดึง material_names สำหรับแสดงใน checkbox
    material_names_objects = FormAndFormula.objects()
    material_names = [x.material_name for x in material_names_objects]
    
    return render_template(
        "/emissions-scope/edit-scope.html",
        scope=scope,
        material_names=material_names
    )



@module.route("/delete/<int:ghg_scope>/<int:ghg_sup_scope>", methods=["DELETE"])
@login_required
@permissions_required_all(['delete_scope'])
def delete_scope(ghg_scope, ghg_sup_scope):
    """ลบ Scope"""
    try:
        # ค้นหา Scope ที่ต้องการลบตาม campus และ department ของ current_user
        scope = Scope.objects(
            ghg_scope=ghg_scope,
            ghg_sup_scope=ghg_sup_scope,
            campus=current_user.campus,
            department=current_user.department
        ).first()
        
        if not scope:
            return jsonify({
                "success": False, 
                "message": "ไม่พบ Scope ที่ต้องการลบ หรือคุณไม่มีสิทธิ์เข้าถึง"
            }), 404
        
        # ตรวจสอบว่ามี Material ที่เชื่อมโยงกับ Scope นี้หรือไม่
        related_materials = Material.objects(
            scope=ghg_scope,
            sub_scope=ghg_sup_scope,
            campus=current_user.campus,
            department=current_user.department
        )
        
        if related_materials.count() > 0:
            return jsonify({
                "success": False,
                "message": f"ไม่สามารถลบ Scope ได้ เนื่องจากมีข้อมูล Material {related_materials.count()} รายการที่เชื่อมโยงอยู่"
            }), 400
        
        # ลบ Scope
        scope.delete()
        
        return jsonify({
            "success": True,
            "message": f"ลบ Scope {ghg_scope}.{ghg_sup_scope} สำเร็จ"
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"เกิดข้อผิดพลาด: {str(e)}"
        }), 500


@module.route("/scope-description/<int:ghg_scope>/<int:ghg_sup_scope>", methods=["GET"])
@login_required
def scope_description(ghg_scope, ghg_sup_scope):
    """แสดง popup description ของ Scope"""
    try:
        # ค้นหา Scope ที่ต้องการ
        scope = Scope.objects(
            ghg_scope=ghg_scope,
            ghg_sup_scope=ghg_sup_scope,
            campus=current_user.campus,
            department=current_user.department
        ).first()
        
        if not scope:
            return render_template(
                "/emissions-scope/partials/scope-description-modal.html",
                error="ไม่พบข้อมูล Scope ที่ต้องการ"
            )
        
        return render_template(
            "/emissions-scope/partials/scope-description-modal.html",
            scope=scope
        )
        
    except Exception as e:
        return render_template(
            "/emissions-scope/partials/scope-description-modal.html",
            error=f"เกิดข้อผิดพลาด: {str(e)}"
        )