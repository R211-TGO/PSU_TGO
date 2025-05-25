from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, logout_user, current_user
from ..forms.user_form import LoginForm, RegisterForm, EditUserForm, EditprofileForm
from ...services.user_service import UserService
from ...models import User, Role, Permission, Scope, Material
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
