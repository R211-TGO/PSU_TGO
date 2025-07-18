from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    jsonify,
    make_response,
)
from flask_login import login_required, logout_user, current_user
from ..forms.user_form import LoginForm, RegisterForm, EditUserForm, EditprofileForm
from ...services.user_service import UserService
from ...models import User, Role, Permission, Scope, FormAndFormula
from ...models.materail_model import Material, QuantityType  # เพิ่ม import QuantityType
from ..forms.material_form import MaterialForm
import datetime
import re
from ...models.file_model import ReferenceDocument, UploadedFile
from urllib.parse import quote

module = Blueprint("emissions", __name__, url_prefix="/emissions")


def calculate_grouped_input_types(head_table, page):
    """
    Calculate and group input types by headers for pagination.

    Args:
        head_table (list): List of headers from the scope.
        items_per_page (int): Number of items per page.
        page (int): Current page number.

    Returns:
        tuple: (current_headers, materials_form, total_pages)
    """
    items_per_page = 8  # จำนวนรายการต่อหน้า
    all_input_types = []
    for head in head_table:
        form_and_formula_item = FormAndFormula.objects(material_name=head).first()
        if form_and_formula_item:
            all_input_types.extend(
                [(head, input_type) for input_type in form_and_formula_item.input_types]
            )

    total_subcategories = len(all_input_types)
    total_pages = (total_subcategories + items_per_page - 1) // items_per_page

    # Determine which subcategories to display on the current page
    start_index = (page - 1) * items_per_page
    end_index = min(start_index + items_per_page, total_subcategories)

    current_input_types = all_input_types[start_index:end_index]

    # Group input types by their headers
    grouped_input_types = {}
    for head, input_type in current_input_types:
        if head not in grouped_input_types:
            grouped_input_types[head] = []
        grouped_input_types[head].append(input_type)

    current_headers = list(grouped_input_types.keys())
    materials_form = list(grouped_input_types.values())

    return current_headers, materials_form, total_pages, items_per_page


@module.route("/emissions-table", methods=["POST"])
@login_required
def view_emissions():
    # รับค่า scope_id และ sub_scope_id จาก POST request
    scope_id = request.form.get("scope_id")
    sub_scope_id = request.form.get("sub_scope_id")
    selected_year = request.form.get("year_form_scope")
    # ดึงปีจาก Material
    years = sorted(Material.objects().distinct("year"))
    # ถ้ามีปีใน database ใช้ปีแรก, ถ้าไม่มีให้ใช้ปีปัจจุบัน
    start_year = years[0] if years else datetime.datetime.now().year
    # ปีปัจจุบัน
    current_year = datetime.datetime.now().year
    years = list(range(start_year, current_year + 1))
    # year_list = list(range(start_year, current_year + 1))
    scope = Scope.objects(
        ghg_scope=int(scope_id),
        ghg_sup_scope=int(sub_scope_id),
        department=current_user.department_key,
        campus=current_user.campus_id,
    ).first()
    if scope:
        ghg_name = scope.ghg_name
    else:
        ghg_name = "Unknown Scope"
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", selected_year)
    return render_template(
        "emissions-scope/view-emissions.html",
        scope_id=scope_id,
        sub_scope_id=sub_scope_id,
        user=current_user,
        years=years,
        ghg_name=ghg_name,
        current_year=current_year,  # ส่งปีปัจจุบันไปยังเทมเพลต
        selected_year=int(selected_year),  # ใช้ปีที่เลือกหรือปีปัจจุบัน
    )


@module.route("/load-emissions-table", methods=["GET"])
@login_required
def load_emissions_table():
    scope_id = request.args.get("scope_id")
    sub_scope_id = request.args.get("sub_scope_id")
    year = request.args.get("year") or datetime.datetime.now().year
    page = int(request.args.get("page", 1))

    scope = Scope.objects(
        ghg_scope=int(scope_id),
        ghg_sup_scope=int(sub_scope_id),
        campus=current_user.campus_id,
        department=current_user.department_key,
    ).first()
    if not scope:
        return jsonify({"error": "Scope not found"}), 404

    head_table = scope.head_table

    # Use the new function to calculate grouped input types
    current_headers, materials_form, total_pages, items_per_page = (
        calculate_grouped_input_types(head_table, page)
    )

    materials = Material.objects(
        scope=int(scope_id),
        sub_scope=int(sub_scope_id),
        year=int(year),
        department=current_user.department_key,
        campus=current_user.campus_id,
    )

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
            items_per_page=items_per_page,  # ส่งจำนวนรายการต่อหน้า
        )

    return render_template(
        "emissions-scope/view-emissions.html",
        scope_id=scope_id,
        sub_scope_id=sub_scope_id,
        user=current_user,
        year=year,
        materials_form=materials_form,
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
    sub_scope_id = request.args.get("sub_scope_id")
    scope_id = request.args.get("scope_id")
    unit = request.args.get("input_unit")

    # ตรวจสอบข้อมูลที่จำเป็น
    if not month_id or not head:
        print("Missing month_id or head in request")
        return jsonify({"error": "Invalid month or head"}), 400

    # สร้างฟอร์มใหม่
    form = MaterialForm()
    return render_template(
        "emissions-scope/partials/material-form.html",
        form=form,
        month_id=month_id,
        head=head,
        year=year,
        month=month,
        user=current_user,
        amount=amount,
        input_label=input_label,
        input_field=input_field,
        sub_scope_id=sub_scope_id,
        scope_id=scope_id,
        unit=unit,  # ส่งค่า unit ไปยังเทมเพลต
    )


@module.route("/load-materials-form", methods=["GET"])
@login_required
def load_materials_form():
    month_id = request.args.get("month_id")
    year = request.args.get("year")
    scope_id = request.args.get("scope_id")
    sub_scope_id = request.args.get("sub_scope_id")
    month = request.args.get("month")
    print("<<<<<<<<<<<<<<<<<<<<<<", scope_id, sub_scope_id, month_id, year)

    # ดึงข้อมูล materials
    materials = Material.objects(
        month=int(month_id),
        year=int(year),
        scope=int(scope_id),
        sub_scope=int(sub_scope_id),
    )

    # ดึงข้อมูล head_table และ materials_form
    scope = Scope.objects(
        ghg_scope=int(scope_id),
        ghg_sup_scope=int(sub_scope_id),
        department=current_user.department_key,
        campus=current_user.campus_id,
    ).first()
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
        month=month,
    )


# สมมติว่าคลาสเหล่านี้มีการ địnhหมาย ไว้แล้ว (จากโค้ดเดิมของคุณ)
# class FormAndFormula:
#     ...
#
# class Material:
#     ...


def calculate_result(material):
    """
    คำนวณผลลัพธ์จากสูตรและอัปเดต field result ของ material
    ฟังก์ชันนี้ถูกแก้ไขให้รองรับชื่อตัวแปรภาษาไทยในสูตร

    Args:
        material (Material): a object material ที่ต้องการอัปเดต
    """
    # ดึงข้อมูลสูตรจากฐานข้อมูล
    form_and_formula = FormAndFormula.objects(material_name=material.name).first()
    if not form_and_formula:
        print(f"ไม่พบสูตรสำหรับ material: {material.name}")
        return

    # --- ส่วนที่แก้ไข ---

    # 1. สร้าง mapping ระหว่างชื่อตัวแปรภาษาไทย กับชื่อที่ปลอดภัย (Safe ASCII names)
    # เช่น {'ความหนา': 'var_0', 'ความยาว': 'var_1'}
    variable_mapping = {
        original_var: f"var_{i}"
        for i, original_var in enumerate(form_and_formula.variables)
    }

    # 2. เตรียม dictionary ของตัวแปรที่แปลงชื่อแล้วสำหรับใช้ใน eval()
    sanitized_variables = {}
    # กำหนดค่าเริ่มต้นสำหรับทุกตัวแปรเป็น 0
    for safe_name in variable_mapping.values():
        sanitized_variables[safe_name] = 0

    # อัปเดตค่าจาก material ที่มีอยู่
    for qt in material.quantity_type:
        # ตรวจสอบว่า field จาก material เป็นหนึ่งในตัวแปรที่กำหนดไว้ในสูตรหรือไม่
        if qt.field in variable_mapping:
            # ดึงชื่อที่ปลอดภัย (เช่น 'var_0') มาใช้เป็น key
            safe_name = variable_mapping[qt.field]
            sanitized_variables[safe_name] = qt.amount

    # 3. แปลงสตริงสูตร โดยแทนที่ชื่อตัวแปรภาษาไทยด้วยชื่อที่ปลอดภัย
    sanitized_formula = form_and_formula.formula
    # เรียงลำดับ key ตามความยาวจากมากไปน้อย เพื่อป้องกันการแทนที่ผิดพลาด
    # เช่น ป้องกันการแทนที่ "ความหนา" ซึ่งเป็นส่วนหนึ่งของ "ความหนาแน่น" ก่อน
    sorted_vars = sorted(variable_mapping.keys(), key=len, reverse=True)

    for original_var in sorted_vars:
        safe_name = variable_mapping[original_var]
        # ใช้ regular expression (\b) เพื่อให้มั่นใจว่าแทนที่ทั้งคำเท่านั้น
        sanitized_formula = re.sub(
            r"\b" + re.escape(original_var) + r"\b", safe_name, sanitized_formula
        )

    # --- สิ้นสุดส่วนที่แก้ไข ---

    try:
        # 4. ประมวลผลสูตรที่แปลงแล้วด้วยตัวแปรที่แปลงแล้ว
        print(f"Executing sanitized formula: {sanitized_formula}")
        print(f"With variables: {sanitized_variables}")

        result = eval(sanitized_formula, {}, sanitized_variables)
        material.result = float(result)  # บันทึกผลลัพธ์เป็น float
        material.save()
        print(f"คำนวณผลลัพธ์สำหรับ {material.name} สำเร็จ: {material.result}")

    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการคำนวณผลลัพธ์สำหรับ {material.name}: {e}")
        print("--- Debug Information ---")
        print(f"Original formula: {form_and_formula.formula}")
        print(f"Sanitized formula: {sanitized_formula}")
        print(f"Sanitized variables: {sanitized_variables}")
        print("-----------------------")


def save_material(scope_id, sub_scope_id, month_id, year, material_data):
    """
    Save a single material to the database and calculate its result.
    """
    head = material_data["head"]
    field = material_data["field"]
    amount = material_data["amount"]

    # scope = Scope.objects(
    #     ghg_scope=int(scope_id),
    #     ghg_sup_scope=int(sub_scope_id),
    #     department=current_user.department_key,
    #     campus=current_user.campus_id,
    # ).first()
    # sub_scope = Scope.objects(
    #     ghg_scope=int(scope_id), ghg_sup_scope=int(sub_scope_id)
    # ).first()

    # if not scope or not sub_scope:
    #     print(
    #         f"Scope or Sub-Scope not found: scope_id={scope_id}, sub_scope_id={sub_scope_id}"
    #     )
    #     return False

    material = Material.objects(
        month=int(month_id),
        name=head,
        scope=int(scope_id),
        sub_scope=int(sub_scope_id),
        year=year,
        department=current_user.department_key,
        campus=current_user.campus_id,
    ).first()

    form_and_formula = FormAndFormula.objects(material_name=head).first()
    if not form_and_formula:
        print(f"Form and Formula not found for material: {head}")
        return False

    input_type = form_and_formula.input_types.filter(field=field).first()
    if not input_type:
        print(f"Input type not found for field: {field} in material: {head}")
        return False

    if material:
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
        material.department = current_user.department_key
        material.campus = current_user.campus_id
        material.edit_by_id = str(current_user.id)  # อัปเดต edit_by_id
        material.update_date = datetime.datetime.now()  # อัปเดต update_date
        material.save()
    else:
        new_material = Material(
            month=int(month_id),
            name=head,
            scope=int(scope_id),
            sub_scope=int(sub_scope_id),
            year=year,
            day=1,
            form_and_formula=form_and_formula.name,
            department=current_user.department_key,
            campus=current_user.campus_id,
            edit_by_id=str(current_user.id),  # เซฟ edit_by_id
            update_date=datetime.datetime.now(),  # เซฟ update_date
            quantity_type=[
                QuantityType(
                    field=field,
                    label=input_type.label,
                    amount=float(amount),
                    unit=input_type.unit,
                )
            ],
        )
        new_material.save()
        material = new_material

    # Calculate and update the result
    calculate_result(material)
    return True


@module.route("/save-materials", methods=["POST"])
@login_required
def save_materials():
    scope_id = request.form.get("scope_id")
    sub_scope_id = request.form.get("sub_scope_id")
    month_id = request.form.get("month_id")
    year = request.form.get("year")
    page = int(request.form.get("page", 1))  # รับค่าหน้าปัจจุบัน
    input_label = request.form.get("input_label")
    input_field = request.form.get("input_field")

    # Debugging: Print received form data
    print(f"Received form data: {request.form}")

    # ตรวจสอบว่า scope และ sub_scope มีอยู่ในฐานข้อมูล
    scope = Scope.objects(
        ghg_scope=int(scope_id),
        ghg_sup_scope=int(sub_scope_id),
        department=current_user.department_key,
        campus=current_user.campus_id,
    ).first()

    if not scope:
        print(
            f"Invalid scope or sub-scope ID: scope_id={scope_id}, sub_scope_id={sub_scope_id}"
        )
        return jsonify({"error": "Invalid scope or sub-scope ID"}), 400

    head_table = scope.head_table
    print(f"Head table before saving materials: {head_table}")  # Debugging

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

        # label = input_label
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

                # เพิ่มเงื่อนไขตรวจสอบ amount ก่อน append
                if amount and amount.strip():  # เซฟเฉพาะฟิลด์ที่มีการกรอกข้อมูล
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
    head_table = scope.head_table  # Re-fetch head_table after saving materials
    print(f"Head table after saving materials: {head_table}")  # Debugging

    current_headers, materials_form, total_pages, items_per_page = (
        calculate_grouped_input_types(head_table, page)
    )

    # สร้าง materials_form ใหม่ตาม current_headers
    materials_form = []
    for head in current_headers:
        form_and_formula = FormAndFormula.objects(material_name=head).first()
        if form_and_formula:
            materials_form.append(form_and_formula.input_types)

    # กรองข้อมูล Material ตามปีที่เลือก
    materials = Material.objects(
        scope=int(scope_id),
        sub_scope=int(sub_scope_id),
        year=int(year),
        department=current_user.department_key,
        campus=current_user.campus_id,
    )

    if request.headers.get("HX-Request"):
        print(
            f"Rendering emissions table with scope_id: {scope_id}, sub_scope_id: {sub_scope_id}, year: {year}, page: {page}"
        )
        return render_template(
            "emissions-scope/partials/emissions-table.html",
            scope=scope,
            scope_id=scope_id,
            sub_scope_id=sub_scope_id,
            materials=materials,
            head_table=current_headers,
            total_pages=total_pages,
            page=page,  # ส่งหน้าปัจจุบันกลับไปยังเทมเพลต
            user=current_user,
            year=year,
            materials_form=materials_form,
            items_per_page=items_per_page,  # ส่งจำนวนรายการต่อหน้า
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


@module.route("/delete-material", methods=["POST"])
@login_required
def delete_material():
    scope_id = request.form.get("scope_id")
    sub_scope_id = request.form.get("sub_scope_id")
    month_id = request.form.get("month_id")
    year = request.form.get("year")
    head = request.form.get("head")
    input_field = request.form.get("input_field")
    page = int(request.form.get("page", 1))

    material = Material.objects(
        month=int(month_id),
        name=head,
        scope=int(scope_id),
        sub_scope=int(sub_scope_id),
        year=int(year),
        department=current_user.department_key,
        campus=current_user.campus_id,
    ).first()

    if material:
        material.quantity_type = [
            qt for qt in material.quantity_type if qt.field != input_field
        ]
        material.edit_by_id = str(current_user.id)  # อัปเดต edit_by_id
        material.update_date = datetime.datetime.now()  # อัปเดต update_date
        material.save()

        # Calculate and update the result
        calculate_result(material)

    # Refresh the table after deletion
    scope = Scope.objects(
        ghg_scope=int(scope_id),
        ghg_sup_scope=int(sub_scope_id),
        department=current_user.department_key,
        campus=current_user.campus_id,
    ).first()
    head_table = scope.head_table if scope else []

    current_headers, materials_form, total_pages, items_per_page = (
        calculate_grouped_input_types(head_table, page)
    )

    materials = Material.objects(
        scope=int(scope_id),
        sub_scope=int(sub_scope_id),
        year=int(year),
        department=current_user.department_key,
        campus=current_user.campus_id,
    )

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
            items_per_page=items_per_page,
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


@module.route("/delete-all-materials", methods=["POST"])
@login_required
def delete_all_materials():
    scope_id = request.form.get("scope_id")
    sub_scope_id = request.form.get("sub_scope_id")
    month_id = request.form.get("month_id")
    year = request.form.get("year")
    page = int(request.form.get("page", 1))

    materials = Material.objects(
        month=int(month_id),
        scope=int(scope_id),
        sub_scope=int(sub_scope_id),
        year=int(year),
        department=current_user.department_key,
        campus=current_user.campus_id,
    )

    if materials:
        for material in materials:
            material.quantity_type = []  # Clear quantity_type
            material.edit_by_id = str(current_user.id)  # Update edit_by_id
            material.update_date = datetime.datetime.now()  # Update update_date
            material.save()

            # Calculate and update the result
            calculate_result(material)

    # Refresh the table after deletion
    scope = Scope.objects(
        ghg_scope=int(scope_id),
        ghg_sup_scope=int(sub_scope_id),
        department=current_user.department_key,
        campus=current_user.campus_id,
    ).first()
    head_table = scope.head_table if scope else []

    current_headers, materials_form, total_pages, items_per_page = (
        calculate_grouped_input_types(head_table, page)
    )

    materials = Material.objects(
        scope=int(scope_id),
        sub_scope=int(sub_scope_id),
        year=int(year),
        department=current_user.department_key,
        campus=current_user.campus_id,
    )

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
            items_per_page=items_per_page,
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


@module.route("/load-upload-modal", methods=["GET"])
@login_required
def load_upload_modal(
    month_id=None, year=None, scope_id=None, sub_scope_id=None, month=None
):
    # หากค่าพารามิเตอร์ไม่ได้ถูกส่งมา ให้ดึงค่าจาก request.args
    month_id = month_id or request.args.get("month_id")
    year = year or request.args.get("year")
    scope_id = scope_id or request.args.get("scope_id")
    sub_scope_id = sub_scope_id or request.args.get("sub_scope_id")
    month = month or request.args.get("month")

    # ตรวจสอบค่าที่ได้รับ
    print(
        f"month_id: {month_id}, year: {year}, scope_id: {scope_id}, sub_scope_id: {sub_scope_id}, month: {month}"
    )

    # ตรวจสอบว่าค่าพารามิเตอร์ไม่เป็น None
    if not all([month_id, year, scope_id, sub_scope_id]):
        return jsonify({"error": "Missing required parameters"}), 400

    documents = ReferenceDocument.objects(
        scope_id=int(scope_id),
        sub_scope_id=int(sub_scope_id),
        year=int(year),
        month=int(month_id),
        campus=current_user.campus_id,
        department=current_user.department_key,
    ).first()

    if not documents:
        documents = ReferenceDocument(
            scope_id=int(scope_id),
            sub_scope_id=int(sub_scope_id),
            year=int(year),
            month=int(month_id),
            campus=current_user.campus_id,
            department=current_user.department_key,
            files=[],
        )
        documents.save()

    return render_template(
        "emissions-scope/partials/upload-modal.html",
        documents=documents,
        month_id=month_id,
        year=year,
        scope_id=scope_id,
        sub_scope_id=sub_scope_id,
        month=month,
    )


@module.route("/upload-file", methods=["POST"])
@login_required
def upload_file():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    scope_id = request.form.get("scope_id")
    sub_scope_id = request.form.get("sub_scope_id")
    year = request.form.get("year")
    month_id = request.form.get("month_id")
    month = request.form.get("month")  # เพิ่มการดึงค่า month

    # ตรวจสอบว่าค่าพารามิเตอร์ไม่เป็น None
    if not all([scope_id, sub_scope_id, year, month_id]):
        return jsonify({"error": "Missing required parameters"}), 400

    document = ReferenceDocument.objects(
        scope_id=int(scope_id),
        sub_scope_id=int(sub_scope_id),
        year=int(year),
        month=int(month_id),
        campus=current_user.campus_id,
        department=current_user.department_key,
    ).first()

    if not document:
        document = ReferenceDocument(
            scope_id=int(scope_id),
            sub_scope_id=int(sub_scope_id),
            year=int(year),
            month=int(month_id),
            campus=current_user.campus_id,
            department=current_user.department_key,
            files=[],
        )

    document.files.append(
        UploadedFile(
            filename=file.filename,
            content_type=file.content_type,
            data=file.read(),
        )
    )
    document.save()

    # ส่งค่าพารามิเตอร์ไปยัง load_upload_modal
    return load_upload_modal(
        month_id=month_id,
        year=year,
        scope_id=scope_id,
        sub_scope_id=sub_scope_id,
        month=month,
    )


@module.route("/download-file/<file_id>", methods=["GET"])
@login_required
def download_file(file_id):
    document = ReferenceDocument.objects(files__id=file_id).first()
    print(f"Downloading file with ID: {file_id}")
    if not document:
        return jsonify({"error": "File not found"}), 404

    file = next((f for f in document.files if str(f.id) == file_id), None)
    if not file:
        return jsonify({"error": "File not found"}), 404

    # เข้ารหัสชื่อไฟล์เป็น UTF-8
    encoded_filename = quote(file.filename)

    response = make_response(file.data)
    response.headers["Content-Type"] = file.content_type
    response.headers["Content-Disposition"] = (
        f"attachment; filename*=UTF-8''{encoded_filename}"
    )
    return response


@module.route("/delete-file/<file_id>", methods=["POST"])
@login_required
def delete_file(file_id):
    print(f"Deleting file with ID: {file_id}")
    scope_id = request.form.get("scope_id")
    sub_scope_id = request.form.get("sub_scope_id")
    year = request.form.get("year")
    month_id = request.form.get("month_id")
    month = request.form.get("month")  # เพิ่มการดึงค่า month

    if not file_id:
        print("Missing file_id")
        return jsonify({"error": "Missing file_id"}), 400

    document = ReferenceDocument.objects(files__id=file_id).first()
    if not document:
        print(f"Document not found for file_id: {file_id}")
        return jsonify({"error": "File not found"}), 404

    document.files = [f for f in document.files if str(f.id) != file_id]
    document.save()

    # ส่งค่าพารามิเตอร์ไปยัง load_upload_modal
    return load_upload_modal(
        month_id=month_id,
        year=year,
        scope_id=scope_id,
        sub_scope_id=sub_scope_id,
        month=month,
    )
