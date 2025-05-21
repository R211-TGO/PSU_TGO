from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, logout_user, current_user
from ..forms.user_form import LoginForm, RegisterForm, EditUserForm, EditprofileForm
from ...services.user_service import UserService
from ...models import User, Role, Permission, Scope, Material

module = Blueprint("emissions", __name__, url_prefix="/emissions")


@module.route("/", methods=["GET", "POST"])
@login_required
def veiw_emissions():
    # รับค่า scope_id และ sub_scope_id จาก query string
    scope_id = request.args.get("scope_id")
    sub_scope_id = request.args.get("sub_scope_id")
    print("scope_id:", scope_id)
    print("sub_scope_id:", sub_scope_id)

    # ตรวจสอบว่าค่า scope_id และ sub_scope_id ไม่เป็น None
    if not scope_id or not sub_scope_id:
        return "Invalid scope or sub-scope ID", 400

    # ดึง Scope ที่ตรงกับ scope_id
    scope = Scope.objects(ghg_scope=int(scope_id)).first()  # ดึง Scope ที่ตรงกับ scope_id
    if not scope:
        return "Scope not found", 404

    print("Scope:", scope.ghg_name)

    head_table = scope.head_table  # ดึง head_table ของ scope
    print("head_table:", scope.head_table)
    materials = Material.objects(scope=int(scope_id), sub_scope=int(sub_scope_id))
    print("Materials:", materials)

    s = Scope.objects(ghg_scope=1)
    print("Scope:", s)

    return render_template(
        "emissions-scope/veiw-emissions.html",
        scope=scope,
        scope_id=scope_id,
        sub_scope_id=sub_scope_id,
        materials=materials,
        head_table=head_table,
        user=current_user,
    )


@module.route("/load-emissions-table", methods=["GET"])
@login_required
def load_emissions_table():
    # รับค่า scope_id และ sub_scope_id จาก query string
    scope_id = request.args.get("scope_id")
    sub_scope_id = request.args.get("sub_scope_id")
    print("scope_id:", scope_id)
    print("sub_scope_id:", sub_scope_id)

    # ตรวจสอบว่าค่า scope_id และ sub_scope_id ไม่เป็น None
    if not scope_id or not sub_scope_id:
        return "Invalid scope or sub-scope ID", 400

    # ดึง Scope ที่ตรงกับ scope_id
    scope = Scope.objects(ghg_scope=int(scope_id),ghg_sup_scope=int(sub_scope_id)).first()  # ดึง Scope ที่ตรงกับ scope_id
    if not scope:
        return "Scope not found", 404

    print("Scope:", scope.ghg_name)

    head_table = scope.head_table  # ดึง head_table ของ scope
    print("head_table:", scope.head_table)
    materials = Material.objects(scope=int(scope_id), sub_scope=int(sub_scope_id))
    print("Materials:", materials)

    s = Scope.objects(ghg_scope=1)
    print("Scope:", s)

    return render_template(
        "emissions-scope/partials/emissions-table.html",
        scope=scope,
        scope_id=scope_id,
        sub_scope_id=sub_scope_id,
        materials=materials,
        head_table=head_table,
        user=current_user,
    )
