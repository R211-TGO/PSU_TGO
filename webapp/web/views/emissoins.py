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

    materials = Material.objects(
        scope=int(scope_id), sub_scope=int(sub_scope_id), year=year
    )

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
        )

    # ถ้าไม่ใช่ HTMX ให้โหลดหน้าเต็ม
    return render_template(
        "emissions-scope/view-emissions.html",
        scope_id=scope_id,
        sub_scope_id=sub_scope_id,
        user=current_user,
        year=year,
    )


@module.route("/load-material-form", methods=["GET"])
@login_required
def load_material_form():
    month_id = request.args.get("month_id")
    head = request.args.get("head")
    year = request.args.get("year")
    month = request.args.get("month")
    amount = request.args.get("amount")

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
    )


@module.route("/load-materials-form", methods=["GET"])
def load_materials_form():
    """
    ฟังก์ชันนี้ใช้สำหรับโหลดฟอร์มของ materials ทั้งหมดในเดือนนั้น
    """
    month_id = request.args.get("month_id")
    year = request.args.get("year")
    sub_scope_id = request.args.get("sub_scope_id")
    scope_id = request.args.get("scope_id")
    print(f"Received month_id: {month_id}, year: {year}")
    form = MaterialForm()  # สร้างฟอร์มใหม่
    materials = Material.objects(month=int(month_id), year=year)
    scope = Scope.objects(
        ghg_scope=int(scope_id), ghg_sup_scope=int(sub_scope_id)
    ).first()
    if not scope:
        return jsonify({"error": "Scope not found"}), 404

    head_table = scope.head_table
    print(head_table)
    return render_template(
        "emissions-scope/partials/materials-form.html",
        form=form,
        user=current_user,
        month_id=month_id,
        materials=materials,
        year=year,
        head_table=head_table,
    )


@module.route("/save-material", methods=["POST"])
@login_required
def save_material():
    month_id = request.form.get("month_id")
    head = request.form.get("head")
    amount = request.form.get("amount")
    scope_id = request.form.get("scope_id")
    sub_scope_id = request.form.get("sub_scope_id")
    page = int(request.form.get("page", 1))
    year = request.form.get("year")
    print(f"Received year: {year}")
    print(
        f"Received data: month_id={month_id}, head={head}, amount={amount}, scope_id={scope_id}, sub_scope_id={sub_scope_id}, page={page}"
    )
    # ตรวจสอบข้อมูล
    if not month_id or not head or not amount or not scope_id or not sub_scope_id:
        print("Missing data in request")
        return jsonify({"error": "Missing data"}), 400

    try:
        scope_id = int(scope_id)
        sub_scope_id = int(sub_scope_id)
        amount = float(amount)
        print(
            f"Received data: month_id={month_id}, head={head}, amount={amount}, scope_id={scope_id}, sub_scope_id={sub_scope_id}, page={page}"
        )
    except ValueError:
        return jsonify({"error": "Invalid data format"}), 400

    # หา material เดิม
    material = Material.objects(
        month=int(month_id),
        name=head,
        scope=int(scope_id),
        sub_scope=int(sub_scope_id),
        year=year,
    ).first()
    print(f"Found material: {material}")

    form_and_formula = FormAndFormula.objects(material_name=head).first()
    if form_and_formula:
        formula = form_and_formula.formula
        unit = form_and_formula.input_types[0].unit
        field = form_and_formula.input_types[0].field
        label = form_and_formula.input_types[0].label

    if material:
        # อัปเดต amount ใน quantity_type ตัวแรก
        if material.quantity_type and len(material.quantity_type) > 0:
            material.quantity_type[0].amount = amount
            material.quantity_type[0].unit = unit
            material.quantity_type[0].field = field
            material.quantity_type[0].label = label
            material.update_date = datetime.datetime.now()
        else:
            material.quantity_type = [
                QuantityType(
                    field=field,
                    label=label,
                    amount=amount,
                    unit=unit,
                )
            ]
        material.save()
    else:
        # สร้างใหม่
        material = Material(
            month=int(month_id),
            name=head,
            scope=int(scope_id),
            sub_scope=int(sub_scope_id),
            year=year,  # กำหนดค่าตามจริง
            day=1,  # กำหนดค่าตามจริง
            form_and_formula=formula,
            quantity_type=[
                QuantityType(
                    field=field,
                    label=label,
                    amount=amount,
                    unit=unit,
                )
            ],
        )
        material.save()

    # อัปเดตตาราง emissions
    materials = Material.objects(
        scope=str(scope_id), sub_scope=str(sub_scope_id), year=int(year)
    )
    scope = Scope.objects(ghg_scope=scope_id, ghg_sup_scope=sub_scope_id).first()
    head_table = scope.head_table
    items_per_page = 4
    total_headers = len(head_table)
    total_pages = (total_headers + items_per_page - 1) // items_per_page
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page
    current_headers = head_table[start_index:end_index]

    if request.headers.get("HX-Request"):
        return render_template(
            "emissions-scope/partials/emissions-table.html",
            scope_id=scope_id,
            sub_scope_id=sub_scope_id,
            materials=materials,
            head_table=current_headers,
            total_pages=total_pages,
            page=page,
            user=current_user,
            year=year,
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


@module.route("/save-materials", methods=["POST"])
@login_required
def save_materials():
    scope_id = request.form.get("scope_id")
    sub_scope_id = request.form.get("sub_scope_id")
    month_id = request.form.get("month_id")
    year = request.form.get("year")
    page = int(request.form.get("page", 1))

    # ดึงข้อมูล materials จากฟอร์ม
    materials = []
    for key in request.form.keys():
        if key.startswith("amount_"):
            parts = key.split("_")
            head = parts[1]
            quantity_type = parts[2] if len(parts) > 2 else "empty"
            amount = request.form.get(key)
            materials.append({"head": head, "type": quantity_type, "amount": amount})

    if not scope_id or not sub_scope_id or not month_id or not year or not materials:
        return jsonify({"error": "Missing data"}), 400

    # บันทึกข้อมูล materials
    for material_data in materials:
        head = material_data["head"]
        quantity_type = material_data["type"]
        amount = material_data["amount"]

        material = Material.objects(
            month=int(month_id),
            name=head,
            scope=int(scope_id),
            sub_scope=int(sub_scope_id),
            year=year,
        ).first()

        if material:
            # อัปเดตข้อมูล
            for qt in material.quantity_type:
                if qt.field == quantity_type:
                    qt.amount = float(amount)
            material.save()
        else:
            # กำหนดค่าดีฟอลต์สำหรับฟิลด์ที่จำเป็น
            default_label = "Default Label"
            default_unit = "Default Unit"
            default_day = 1
            default_formula = "Default Formula"

            # สร้าง material ใหม่
            new_material = Material(
                month=int(month_id),
                name=head,
                scope=int(scope_id),
                sub_scope=int(sub_scope_id),
                year=year,
                day=default_day,  # กำหนดค่าดีฟอลต์สำหรับ day
                form_and_formula=default_formula,  # กำหนดค่าดีฟอลต์สำหรับ form_and_formula
                quantity_type=[
                    QuantityType(
                        field=quantity_type,
                        label=default_label,  # กำหนดค่าดีฟอลต์สำหรับ label
                        amount=float(amount),
                        unit=default_unit,  # กำหนดค่าดีฟอลต์สำหรับ unit
                    )
                ],
            )
            new_material.save()

    # อัปเดตตาราง emissions
    materials = Material.objects(
        scope=str(scope_id), sub_scope=str(sub_scope_id), year=int(year)
    )
    scope = Scope.objects(ghg_scope=scope_id, ghg_sup_scope=sub_scope_id).first()
    head_table = scope.head_table
    items_per_page = 4
    total_headers = len(head_table)
    total_pages = (total_headers + items_per_page - 1) // items_per_page
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page
    current_headers = head_table[start_index:end_index]

    if request.headers.get("HX-Request"):
        return render_template(
            "emissions-scope/partials/emissions-table.html",
            scope_id=scope_id,
            sub_scope_id=sub_scope_id,
            materials=materials,
            head_table=current_headers,
            total_pages=total_pages,
            page=page,
            user=current_user,
            year=year,
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
