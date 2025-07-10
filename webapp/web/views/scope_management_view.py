from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from ...models import Scope, FormAndFormula

module = Blueprint("scope_management", __name__, url_prefix="/scope")

# Campus และ Department ทั้งหมด
CAMPUS_DEPARTMENTS = {
    "hatyai": [
        "president",
        "IT Department",
        "HR Department1",
        "Finance Department1",
        "Marketing Department1",
    ],
    "phuket": [
        "president",
        "IT Department",
        "HR Department",
        "Finance Department",
        "Marketing Department",
    ],
    "surat": [
        "president",
        "IT Department",
        "HR Department",
        "Finance Department",
        "Marketing Department",
    ],
    "trang": [
        "president",
        "IT Department",
        "HR Department",
        "Finance Department",
        "Marketing Department",
    ],
}


@module.route("/", methods=["GET"])
@login_required
def scope_page():
    """
    แสดงหน้าหลักสำหรับจัดการ Scope โดยดึงข้อมูลเฉพาะ campus='base'
    """
    try:
        base_scopes = Scope.objects(campus="base").order_by(
            "ghg_scope", "ghg_sup_scope"
        )

        scopes_by_type = {1: [], 2: [], 3: []}
        for s in base_scopes:
            if s.ghg_scope in scopes_by_type:
                scopes_by_type[s.ghg_scope].append(s)

        return render_template(
            "/scope/scope_management.html", scopes_by_type=scopes_by_type
        )
    except Exception as e:
        flash(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {e}", "error")
        return render_template(
            "/scope/scope_management.html", scopes_by_type={1: [], 2: [], 3: []}
        )


@module.route("/add", methods=["POST"])
@login_required
def add_scope():
    """
    จัดการการสร้าง Scope ใหม่จากการส่งข้อมูลผ่านฟอร์มใน Modal
    และบันทึกข้อมูล material (head_table) ด้วย
    """
    try:
        ghg_scope = int(request.form.get("ghg_scope"))
        ghg_sup_scope = int(request.form.get("ghg_sup_scope"))
        ghg_name = request.form.get("ghg_name")
        ghg_desc = request.form.get("ghg_desc")
        selected_materials = request.form.getlist("head_table")  # รับค่า material

        if not all([ghg_scope, ghg_sup_scope, ghg_name, ghg_desc]):
            flash("กรุณากรอกข้อมูลบังคับให้ครบทุกช่อง", "error")
            return redirect(url_for("scope_management.scope_page"))

        existing_scope = Scope.objects(
            ghg_scope=ghg_scope, ghg_sup_scope=ghg_sup_scope, campus="base"
        ).first()
        if existing_scope:
            flash(f"Scope {ghg_scope}.{ghg_sup_scope} มีอยู่แล้วในระบบ", "error")
            return redirect(url_for("scope_management.scope_page"))

        # 1. สร้าง base scope
        base_scope = Scope(
            ghg_scope=ghg_scope,
            ghg_sup_scope=ghg_sup_scope,
            ghg_name=ghg_name,
            ghg_desc=ghg_desc,
            campus="base",
            department="base",
            head_table=selected_materials,  # บันทึก material
        )
        base_scope.save()

        # 2. สร้าง scope สำหรับทุก campus/department
        for campus, departments in CAMPUS_DEPARTMENTS.items():
            for department in departments:
                scope = Scope(
                    ghg_scope=ghg_scope,
                    ghg_sup_scope=ghg_sup_scope,
                    ghg_name=ghg_name,
                    ghg_desc=ghg_desc,
                    campus=campus,
                    department=department,
                    head_table=selected_materials,  # บันทึก material
                )
                scope.save()

        flash("สร้าง Scope ใหม่สำเร็จแล้ว", "success")
    except Exception as e:
        flash(f"เกิดข้อผิดพลาดในการสร้าง Scope: {e}", "error")

    return redirect(url_for("scope_management.scope_page"))


@module.route("/update/<scope_id>", methods=["POST"])
@login_required
def update_scope(scope_id):
    """
    อัปเดตข้อมูล Scope ที่มีอยู่
    การอัปเดตจะแก้ไข name, description และ material (head_table)
    ของทุก Scope ที่มี ghg_scope และ ghg_sup_scope เดียวกัน
    """
    try:
        # ดึงข้อมูลใหม่จากฟอร์ม
        new_ghg_name = request.form.get("ghg_name")
        new_ghg_desc = request.form.get("ghg_desc")
        selected_materials = request.form.getlist("head_table")

        if not all([new_ghg_name, new_ghg_desc]):
            flash("กรุณากรอกข้อมูล Name และ Description ให้ครบถ้วน", "error")
            return redirect(url_for("scope_management.scope_page"))

        # ค้นหา 'base' scope เพื่อใช้เป็นตัวอ้างอิง
        base_scope = Scope.objects.get(id=scope_id, campus="base")
        if not base_scope:
            flash("ไม่พบ Scope ที่ต้องการแก้ไข", "error")
            return redirect(url_for("scope_management.scope_page"))

        # อัปเดตเอกสารทั้งหมดที่มี ghg_scope และ ghg_sup_scope เดียวกัน
        Scope.objects(
            ghg_scope=base_scope.ghg_scope, ghg_sup_scope=base_scope.ghg_sup_scope
        ).update(
            set__ghg_name=new_ghg_name,
            set__ghg_desc=new_ghg_desc,
            set__head_table=selected_materials,  # อัปเดต field head_table
        )

        flash(
            f"อัปเดตข้อมูล Scope {base_scope.ghg_scope}.{base_scope.ghg_sup_scope} สำเร็จแล้ว",
            "success",
        )
    except Exception as e:
        flash(f"เกิดข้อผิดพลาดในการอัปเดต Scope: {e}", "error")

    return redirect(url_for("scope_management.scope_page"))


@module.route("/load-add-form")
@login_required
def load_add_scope_form():
    """
    โหลดฟอร์ม HTML สำหรับการ 'เพิ่ม' scope ใหม่ (สำหรับ HTMX)
    """
    try:
        default_scope = request.args.get("default_scope", 1, type=int)

        # สำหรับหน้า Add เราจะเริ่มต้นด้วยรายการ Material ที่ว่างเปล่า
        # เพราะเรายังไม่รู้ว่าผู้ใช้จะเลือก Scope/Sub-Scope อะไร
        # รายการ Material จะถูกโหลดแบบ Dynamic ด้วย HTMX ทีหลัง
        return render_template(
            "/scope/partials/add_scope_form.html",
            default_scope=default_scope,
            materials=[],  # ส่ง list ว่างเปล่าไปให้ template
        )
    except Exception as e:
        return (
            f'<div class="p-4 text-red-700 bg-red-100 border border-red-400 rounded">An error occurred: {e}</div>',
            500,
        )


@module.route("/load-edit-form/<scope_id>")
@login_required
def load_edit_scope_form(scope_id):
    """
    โหลดฟอร์ม HTML สำหรับการ 'แก้ไข' scope ที่มีอยู่ (สำหรับ HTMX)
    พร้อมดึงรายการ material ที่กรองแล้วมาแสดงผลตอนเริ่มต้น
    """
    try:
        scope_to_edit = Scope.objects.get(id=scope_id)

        # ดึงรายการ material ที่กรองตาม scope และ sup_scope ของเอกสารที่กำลังแก้ไข
        materials_for_this_scope = FormAndFormula.objects(
            ghg_scope=scope_to_edit.ghg_scope, ghg_sup_scope=scope_to_edit.ghg_sup_scope
        ).distinct("material_name")

        return render_template(
            "/scope/partials/edit_scope_form.html",
            scope=scope_to_edit,
            materials=materials_for_this_scope,
        )
    except Scope.DoesNotExist:
        return (
            '<div class="p-4 text-red-700 bg-red-100 border border-red-400 rounded">Error: Scope not found.</div>',
            404,
        )
    except Exception as e:
        return (f'<p class="text-error">Error: {e}</p>', 500)


@module.route("/load-materials", methods=["POST"])
@login_required
def load_materials_for_scope():
    """
    (สำหรับ HTMX) โหลดรายการ material checkboxes โดยกรองจาก ghg_scope
    และ ghg_sup_scope ที่ส่งมาจากฟอร์ม
    """
    try:
        print(777777777777)
        scope = int(request.form.get("ghg_scope"))
        sup_scope = int(request.form.get("ghg_sup_scope"))
        scope_id = request.form.get("scope_id")  # รับ ID ของ scope ที่กำลังแก้ไข (ถ้ามี)

        # ค้นหา material ที่ตรงกับ scope และ sup-scope ที่ระบุ
        filtered_materials = FormAndFormula.objects(
            ghg_scope=scope, ghg_sup_scope=sup_scope
        )

        # ตรวจสอบ material ที่เคยถูกเลือกไว้ (สำหรับหน้า Edit)
        selected_materials = []
        if scope_id:
            current_scope = Scope.objects.get(id=scope_id)
            if current_scope.head_table:
                selected_materials = current_scope.head_table
        print(filtered_materials)
        print(selected_materials)

        # Render HTML Partial เฉพาะส่วนของ Checkbox
        return render_template(
            "/scope/partials/_material_checkboxes.html",
            materials=filtered_materials,
            selected_materials=selected_materials,
        )

    except (ValueError, TypeError):
        print(555555555555555555555555555555)
        # ถ้าผู้ใช้ยังกรอกข้อมูลไม่ครบ ก็ส่งค่าว่างกลับไป
        return ""
    except Exception as e:
        print(555555555555555555555555555555)
        # ส่งข้อความ Error กลับไปแสดงผล
        return f'<p class="text-error">Error loading materials: {e}</p>'
