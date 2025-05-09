from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, logout_user, current_user
from ..forms.user_form import LoginForm, RegisterForm, EditUserForm, EditprofileForm
from ...services.user_service import UserService
from ...models import User, Role, Permission

module = Blueprint("role_management", __name__, url_prefix="/role-management")

@module.route("/", methods=["GET", "POST"])
@login_required
def role_management():
    roles = Role.objects()
    return render_template("/role-management/role-management.html", roles=roles)


@module.route("/load-add-role", methods=["GET"])
@login_required
def load_add_role():
    # ดึงข้อมูล Permission ทั้งหมดจากฐานข้อมูล
    permissions = Permission.objects()

    return render_template(
        "/role-management/add-role.html",
        permissions=permissions
    )


@module.route("/add-role", methods=["POST"])
@login_required
def add_role():
    name = request.form.get("name")
    description = request.form.get("description")
    permissions = request.form.getlist("permissions")

    existing_role = Role.objects(name=name).first()
    if existing_role:
        permissions_list = Permission.objects()
        return render_template(
            "/role-management/add-role.html",
            error_msg="Role already exists",
            permissions=permissions_list
        )

    try:
        role = Role(name=name, description=description, permission=permissions)
        role.save()
    except Exception as e:
        permissions_list = Permission.objects()
        return render_template(
            "/role-management/add-role.html",
            error_msg=f"Failed to create role: {str(e)}",
            permissions=permissions_list
        )

    # สำเร็จ → redirect ไป roles-management
    return redirect(url_for("role_management.role_management"))