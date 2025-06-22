from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, logout_user, current_user
from ..forms.user_form import LoginForm, RegisterForm, EditUserForm, EditprofileForm
from ...services.user_service import UserService
from ...models import User, Role, Permission, Scope, FormAndFormula
from ...models.materail_model import Material, QuantityType  # เพิ่ม import QuantityType
from ..forms.material_form import MaterialForm
import datetime

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
    # year = request.form.get("year")
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
        current_year=current_year,  # ส่งปีปัจจุบันไปยังเทมเพลต
        # selected_year=year,  # ใช้ปีที่เลือกหรือปีปัจจุบัน
    )


@module.route("/load-emissions-table", methods=["GET"])
@login_required
def load_emissions_table():
    scope_id = request.args.get("scope_id")
    sub_scope_id = request.args.get("sub_scope_id")
    year = request.args.get("year") or datetime.datetime.now().year
    page = int(request.args.get("page", 1))

    scope = Scope.objects(
        ghg_scope=int(scope_id), ghg_sup_scope=int(sub_scope_id)
    ).first()
    if not scope:
        return jsonify({"error": "Scope not found"}), 404

    head_table = scope.head_table

    # Use the new function to calculate grouped input types
    current_headers, materials_form, total_pages, items_per_page = (
        calculate_grouped_input_types(head_table, page)
    )

    materials = Material.objects(
        scope=int(scope_id), sub_scope=int(sub_scope_id), year=int(year)
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
        month=month,
    )


def calculate_result(material):
    """
    Calculate the result based on the formula and update the material's result field.

    Args:
        material (Material): The material object to update.
    """
    form_and_formula = FormAndFormula.objects(material_name=material.name).first()
    if not form_and_formula:
        print(f"Form and Formula not found for material: {material.name}")
        return

    # Prepare variables for the formula
    variables = {
        var: 0 for var in form_and_formula.variables
    }  # Default all variables to 0
    for qt in material.quantity_type:
        if qt.field in variables:
            variables[qt.field] = qt.amount

    try:
        # Evaluate the formula using the variables
        result = eval(form_and_formula.formula, {}, variables)
        material.result = float(result)  # Save the result as a float
        material.save()
    except Exception as e:
        print(f"Error calculating result for material {material.name}: {e}")


def save_material(scope_id, sub_scope_id, month_id, year, material_data):
    """
    Save a single material to the database and calculate its result.
    """
    head = material_data["head"]
    field = material_data["field"]
    amount = material_data["amount"]

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
        material.department = current_user.department
        material.campus = current_user.campus
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
            department=current_user.department,
            campus=current_user.campus,
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
        ghg_scope=int(scope_id), ghg_sup_scope=int(sub_scope_id)
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
        department=current_user.department,
        campus=current_user.campus,
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
        department=current_user.department,
        campus=current_user.campus,
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
        ghg_scope=int(scope_id), ghg_sup_scope=int(sub_scope_id)
    ).first()
    head_table = scope.head_table if scope else []

    current_headers, materials_form, total_pages, items_per_page = (
        calculate_grouped_input_types(head_table, page)
    )

    materials = Material.objects(
        scope=int(scope_id),
        sub_scope=int(sub_scope_id),
        year=int(year),
        department=current_user.department,
        campus=current_user.campus,
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
        department=current_user.department,
        campus=current_user.campus,
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
        ghg_scope=int(scope_id), ghg_sup_scope=int(sub_scope_id)
    ).first()
    head_table = scope.head_table if scope else []

    current_headers, materials_form, total_pages, items_per_page = (
        calculate_grouped_input_types(head_table, page)
    )

    materials = Material.objects(
        scope=int(scope_id),
        sub_scope=int(sub_scope_id),
        year=int(year),
        department=current_user.department,
        campus=current_user.campus,
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
