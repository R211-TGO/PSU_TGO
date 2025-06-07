from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from ...models import FormAndFormula, Scope

module = Blueprint("emissions_scope", __name__, url_prefix="/emissions-scope")

@module.route("/", methods=["GET"])
@login_required
def emissions_scope():
    # ดึงข้อมูล Scope ที่ตรงกับ campus และ department ของ current_user
    scopes = Scope.objects(
        campus=current_user.campus,
        department=current_user.department
    ).order_by("ghg_scope")
    
    # จัดกลุ่ม Scope ตาม ghg_scope
    grouped_scopes = {}
    for scope in scopes:
        main_scope = f"Scope {scope.ghg_scope}"
        if main_scope not in grouped_scopes:
            grouped_scopes[main_scope] = []
        grouped_scopes[main_scope].append({
            "id": scope.ghg_sup_scope,
            "title": scope.ghg_name,
            "progress": 0,
            "status": "Not started"
        })
    
    return render_template(
        "/emissions-scope/emissions-scope.html",
        user=current_user,
        mockup_data={
            "overall_progress": 0,
            "total_sources": len(scopes),
            "in_progress": 0,
            "not_started": len(scopes),
            "completed": 0,
            "scopes": grouped_scopes
        }
    )


@module.route("/add", methods=["GET", "POST"])
@login_required
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