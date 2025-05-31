from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, logout_user, current_user
from ..forms.user_form import LoginForm, RegisterForm, EditUserForm, EditprofileForm
from ...services.user_service import UserService
from ...models import User, Role, Permission, Scope
from ...models.materail_model import Material, QuantityType  # เพิ่ม import QuantityType
from ..forms.material_form import MaterialForm

module = Blueprint("emissions", __name__, url_prefix="/emissions")


@module.route("/emissions-table", methods=["POST"])
@login_required
def view_emissions():
    # รับค่า scope_id และ sub_scope_id จาก POST request
    scope_id = request.form.get("scope_id")
    sub_scope_id = request.form.get("sub_scope_id")

    return render_template(
        "emissions-scope/view-emissions.html",
        scope_id=scope_id,
        sub_scope_id=sub_scope_id,
        user=current_user,
    )


@module.route("/load-emissions-table", methods=["GET"])
@login_required
def load_emissions_table():
    scope_id = request.args.get("scope_id")
    sub_scope_id = request.args.get("sub_scope_id")
    page = int(request.args.get("page", 1))
    items_per_page = 4

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

    materials = Material.objects(scope=int(scope_id), sub_scope=int(sub_scope_id))

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
        )

    # ถ้าไม่ใช่ HTMX ให้โหลดหน้าเต็ม
    return render_template(
        "emissions-scope/view-emissions.html",
        scope_id=scope_id,
        sub_scope_id=sub_scope_id,
        user=current_user,
    )


@module.route("/load-material-form", methods=["GET"])
@login_required
def load_material_form():
    month_id = request.args.get("month_id")
    head = request.args.get("head")

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
        month=int(month_id), name=head, scope=int(scope_id), sub_scope=int(sub_scope_id)
    ).first()
    print(f"Found material: {material}")

    if material:
        # อัปเดต amount ใน quantity_type ตัวแรก
        if material.quantity_type and len(material.quantity_type) > 0:
            material.quantity_type[0].amount = amount
        else:
            material.quantity_type = [
                QuantityType(
                    field="default_field",
                    label="default_label",
                    amount=amount,
                    unit="หน่วย",
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
            year=2025,  # กำหนดค่าตามจริง
            day=1,  # กำหนดค่าตามจริง
            form_and_formula="",
            quantity_type=[
                QuantityType(
                    field="default_field",
                    label="default_label",
                    amount=amount,
                    unit="หน่วย",
                )
            ],
        )
        material.save()

    # อัปเดตตาราง emissions
    materials = Material.objects(scope=str(scope_id), sub_scope=str(sub_scope_id))
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
            scope=scope,
            scope_id=scope_id,
            sub_scope_id=sub_scope_id,
            materials=materials,
            head_table=current_headers,
            total_pages=total_pages,
            page=page,
            user=current_user,
        )
    else:
        return redirect(
            url_for(
                "emissions.view_emissions", scope_id=scope_id, sub_scope_id=sub_scope_id
            )
        )
