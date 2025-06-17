from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, logout_user, current_user
from ..forms.user_form import LoginForm, RegisterForm, EditUserForm, EditprofileForm
from ...services.user_service import UserService
from ...models import User, Role, Permission, Scope, FormAndFormula
from ...models.materail_model import Material, QuantityType  # เพิ่ม import QuantityType
from ..forms.material_form import MaterialForm
import datetime

module = Blueprint("emissions", __name__, url_prefix="/emissions")


@module.route("/emissions-table", methods=["POST"])
@login_required
def view_emissions():
    # รับค่า scope_id และ sub_scope_id จาก POST request
    scope_id = request.form.get("scope_id")
    sub_scope_id = request.form.get("sub_scope_id")
    # ดึงปีจาก Material
    years = sorted(Material.objects().distinct("year"))
    # ถ้ามีปีใน database ใช้ปีแรก, ถ้าไม่มีให้ใช้ปีปัจจุบัน
    start_year = years[0] if years else datetime.datetime.now().year
    # ปีปัจจุบัน
    current_year = datetime.datetime.now().year
    years = list(range(start_year, current_year + 1))
    # year_list = list(range(start_year, current_year + 1))
    scope = Scope.objects(
        ghg_scope=int(scope_id), ghg_sup_scope=int(sub_scope_id)
    ).first()
    if scope:
        ghg_name = scope.ghg_name
    else:
        ghg_name = "Unknown Scope"

    return render_template(
        "emissions-scope/view-emissions.html",
        scope_id=scope_id,
        sub_scope_id=sub_scope_id,
        user=current_user,
        years=years,
        ghg_name=ghg_name,
    )


@module.route("/load-emissions-table", methods=["GET"])
@login_required
def load_emissions_table():
    scope_id = request.args.get("scope_id")
    sub_scope_id = request.args.get("sub_scope_id")
    print(
        f"Received scope_id>>>>>>>>>>>>>>>>>>>>z: {scope_id}, sub_scope_id: {sub_scope_id}"
    )
    page = int(request.args.get("page", 1))
    year = request.args.get("year") or datetime.datetime.now().year  # ใช้ปีล่าสุดถ้าไม่ระบุ
    items_per_page = 4
    print(f"Received year: {year}")
    if not scope_id or not sub_scope_id:
        return jsonify({"error": "Invalid scope or sub-scope ID"}), 400

    scope = Scope.objects(
        ghg_scope=int(scope_id), ghg_sup_scope=int(sub_scope_id)
    ).first()
    if not scope:
        return jsonify({"error": "Scope not found"}), 404

    head_table = scope.head_table
    total_headers = len(head_table)
    total_pages = (total_headers + items_per_page - 1) // items_per_page

    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page
    current_headers = head_table[start_index:end_index]
    materials_form = []
    for head in head_table:
        form_and_formula_item = FormAndFormula.objects(material_name=head).first()
        # for i in form_and_formula_item.input_types:
        #     print(f"Input Type: {i.input_type}, Field: {i.field}")

        if form_and_formula_item:
            materials_form.append(form_and_formula_item.input_types)
            print(f"Form and Formula found for head: {head}")

    print(f"form_and_formula: {materials_form[0][0].input_type}")
    materials = Material.objects(
        scope=int(scope_id), sub_scope=int(sub_scope_id), year=year
    )
    print(f"Materials found: {len(materials_form),materials_form}")

    # Debugging: ตรวจสอบค่าที่ส่งกลับ
    print(
        f"Scope ID: {scope_id}, Sub Scope ID: {sub_scope_id}, Page: {page}, Total Pages: {total_pages}"
    )

    # ตรวจสอบว่าเป็นคำขอ HTMX หรือไม่
    if request.headers.get("HX-Request"):
        return render_template(
            "emissions-scope/partials/emissions-table.html",
            scope=scope,
            scope_id=scope_id,
            sub_scope_id=sub_scope_id,
            materials=materials,
            head_table=current_headers,
            total_pages=total_pages,
            page=page,
            user=current_user,
            year=year,
            materials_form=materials_form,
        )

    # ถ้าไม่ใช่ HTMX ให้โหลดหน้าเต็ม
    return render_template(
        "emissions-scope/view-emissions.html",
        scope_id=scope_id,
        sub_scope_id=sub_scope_id,
        user=current_user,
        year=year,
        materials_form=materials_form,  # ส่งค่า materials_form ด้วย
    )


@module.route("/load-material-form", methods=["GET"])
@login_required
def load_material_form():
    month_id = request.args.get("month_id")
    head = request.args.get("head")
    year = request.args.get("year")
    month = request.args.get("month")
    amount = request.args.get("amount")
    input_label = request.args.get("input_label")
    input_field = request.args.get("input_field")

    # ตรวจสอบข้อมูลที่จำเป็น
    if not month_id or not head:
        print("Missing month_id or head in request")
        return jsonify({"error": "Invalid month or head"}), 400

    # สร้างฟอร์มใหม่
    form = MaterialForm()  # สมมติว่าคุณมี MaterialForm อยู่แล้ว
    print(head)
    return render_template(
        "emissions-scope/partials/material-form.html",
        form=form,
        month_id=month_id,
        head=head,
        year=year,
        month=month,  # ส่งค่าเดือนด้วย
        user=current_user,  # ส่งข้อมูลผู้ใช้ปัจจุบัน
        amount=amount,  # ส่งค่า amount ด้วย
        input_label=input_label,  # ส่งค่า input_label ด้วย
        input_field=input_field,  # ส่งค่า input_field ด้วย
    )


@module.route("/load-materials-form", methods=["GET"])
@login_required
def load_materials_form():
    month_id = request.args.get("month_id")
    year = request.args.get("year")
    scope_id = request.args.get("scope_id")
    sub_scope_id = request.args.get("sub_scope_id")

    # ดึงข้อมูล materials
    materials = Material.objects(
        month=int(month_id),
        year=int(year),
        scope=int(scope_id),
        sub_scope=int(sub_scope_id),
    )

    # ดึงข้อมูล head_table และ materials_form
    scope = Scope.objects(ghg_scope=scope_id, ghg_sup_scope=sub_scope_id).first()
    head_table = scope.head_table if scope else []
    materials_form = []
    for head in head_table:
        form_and_formula = FormAndFormula.objects(material_name=head).first()
        if form_and_formula:
            materials_form.append(form_and_formula.input_types)

    # ส่งข้อมูลไปยังเทมเพลต
    return render_template(
        "emissions-scope/partials/materials-form.html",
        materials=materials,
        materials_form=materials_form,
        head_table=head_table,
        month_id=month_id,
        year=year,
        scope_id=scope_id,
        sub_scope_id=sub_scope_id,
    )


def save_material(scope_id, sub_scope_id, month_id, year, material_data):
    """
    Save a single material to the database.
    """
    head = material_data["head"]
    field = material_data["field"]
    amount = material_data["amount"]

    # ตรวจสอบว่า scope และ sub_scope มีอยู่ในฐานข้อมูล
    scope = Scope.objects(ghg_scope=int(scope_id)).first()
    sub_scope = Scope.objects(
        ghg_scope=int(scope_id), ghg_sup_scope=int(sub_scope_id)
    ).first()

    if not scope or not sub_scope:
        print(
            f"Scope or Sub-Scope not found: scope_id={scope_id}, sub_scope_id={sub_scope_id}"
        )
        return False

    material = Material.objects(
        month=int(month_id),
        name=head,
        scope=int(scope_id),
        sub_scope=int(sub_scope_id),
        year=year,
    ).first()

    form_and_formula = FormAndFormula.objects(material_name=head).first()
    if not form_and_formula:
        print(f"Form and Formula not found for material: {head}")
        return False

    # Find the input type for the given field
    input_type = form_and_formula.input_types.filter(field=field).first()
    if not input_type:
        print(f"Input type not found for field: {field} in material: {head}")
        return False
    else:
        print(f"Input type found: {input_type.label} for field: {field}")

    if material:
        # Update existing material
        updated = False
        for qt in material.quantity_type:
            if qt.field == field:
                qt.amount = float(amount)
                updated = True
        if not updated:
            material.quantity_type.append(
                QuantityType(
                    field=field,
                    label=input_type.label,
                    amount=float(amount),
                    unit=input_type.unit,
                )
            )
        material.department = current_user.department  # อ้างอิง department จากผู้ใช้ปัจจุบัน
        material.campus = current_user.campus  # อ้างอิง campus จากผู้ใช้ปัจจุบัน
        material.save()
    else:
        # Create new material
        new_material = Material(
            month=int(month_id),
            name=head,
            scope=int(scope_id),
            sub_scope=int(sub_scope_id),
            year=year,
            day=1,
            form_and_formula=form_and_formula.name,
            department=current_user.department,  # อ้างอิง department จากผู้ใช้ปัจจุบัน
            campus=current_user.campus,  # อ้างอิง campus จากผู้ใช้ปัจจุบัน
            quantity_type=[
                QuantityType(
                    field=input_type.field,
                    label=input_type.label,
                    amount=float(amount) if input_type.field == field else 0.0,
                    unit=input_type.unit,
                )
                for input_type in form_and_formula.input_types
            ],
        )
        new_material.save()
    return True


@module.route("/save-materials", methods=["POST"])
@login_required
def save_materials():
    scope_id = request.form.get("scope_id")
    sub_scope_id = request.form.get("sub_scope_id")
    month_id = request.form.get("month_id")
    year = request.form.get("year")
    page = int(request.form.get("page", 1))
    input_label = request.form.get("input_label")
    input_field = request.form.get("input_field")

    # Debugging: Print received form data
    print(f"Received form data: {request.form}")

    # ตรวจสอบว่า scope และ sub_scope มีอยู่ในฐานข้อมูล
    scope = Scope.objects(ghg_scope=int(scope_id)).first()
    sub_scope = Scope.objects(
        ghg_scope=int(scope_id), ghg_sup_scope=int(sub_scope_id)
    ).first()

    if not scope or not sub_scope:
        print(
            f"Invalid scope or sub-scope ID: scope_id={scope_id}, sub_scope_id={sub_scope_id}"
        )
        return jsonify({"error": "Invalid scope or sub-scope ID"}), 400

    # Extract materials from form
    materials = []
    if "head" in request.form and "amount" in request.form:
        # Single material case (from material-form.html)
        head = request.form.get("head")
        amount = request.form.get("amount")

        form_and_formula = FormAndFormula.objects(material_name=head).first()
        if not form_and_formula:
            print(f"Form and Formula not found for material: {head}")
            return jsonify({"error": "Form and Formula not found"}), 400

        label = input_label
        field = input_field
        if not field:
            print(f"No input types found for material: {head}")
            return jsonify({"error": "No input types found"}), 400

        materials.append({"head": head, "field": field, "amount": amount})
    else:
        # Multiple materials case (from materials-form.html)
        for key in request.form.keys():
            if key.startswith("amount_"):
                parts = key.split("_")
                if len(parts) < 3:
                    print(f"Invalid key format: {key}")
                    continue
                head = parts[1]
                field = parts[2]
                amount = request.form.get(key)
                materials.append({"head": head, "field": field, "amount": amount})

    # Debugging: Print materials data
    print(f"Materials: {materials}")

    if not scope_id or not sub_scope_id or not month_id or not year or not materials:
        print("Missing required data")
        return jsonify({"error": "Missing data"}), 400

    # Save each material
    for material_data in materials:
        save_material(scope_id, sub_scope_id, month_id, year, material_data)

    # Update emissions table
    head_table = scope.head_table if scope else []
    materials_form = []
    for head in head_table:
        form_and_formula = FormAndFormula.objects(material_name=head).first()
        if form_and_formula:
            materials_form.append(form_and_formula.input_types)

    materials = Material.objects(
        scope=int(scope_id),
        sub_scope=int(sub_scope_id),
        department=current_user.department,  # อ้างอิง department จากผู้ใช้ปัจจุบัน
        campus=current_user.campus,  # อ้างอิง campus จากผู้ใช้ปัจจุบัน
    )

    items_per_page = 4
    total_headers = len(head_table)
    total_pages = (total_headers + items_per_page - 1) // items_per_page
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page
    current_headers = head_table[start_index:end_index]

    if request.headers.get("HX-Request"):
        return render_template(
            "emissions-scope/partials/emissions-table.html",
            scope=scope,
            scope_id=scope_id,
            sub_scope_id=sub_scope_id,
            materials=materials,
            head_table=current_headers,
            total_pages=total_pages,
            page=page,
            user=current_user,
            year=year,
            materials_form=materials_form,
        )
    else:
        return redirect(
            url_for(
                "emissions.view_emissions",
                scope_id=scope_id,
                sub_scope_id=sub_scope_id,
                year=year,
            )
        )
