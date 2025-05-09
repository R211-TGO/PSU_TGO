from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, logout_user, current_user
from ..forms.user_form import LoginForm, RegisterForm, EditUserForm, EditprofileForm
from ...services.user_service import UserService
from ...models import User, Role, Permission

module = Blueprint("users_management", __name__, url_prefix="/users-management")

@module.route("/", methods=["get", "post"])
@login_required
def users_management():
    users = User.objects()
    return render_template("/users-management/users-management.html", users=users)


@module.route("/load-edit-user-role", methods=["GET", "POST"])
@login_required
def load_edit_user_role():
    user_id = request.args.get("user_id")
    user = User.objects.with_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # ตัวอย่างข้อมูล Department และ Role
    departments = [
        "IT Department",
        "HR Department",
        "Finance Department",
        "Marketing Department",
    ]
    roles = ["admin", "user", "manager", "viewer"]

    form = EditUserForm()
    users = User.objects()
    if request.method == "POST":
        # กรอกข้อมูลจากฟอร์ม
        form.username.data = user.username
        form.department.data = request.form.get("department")
        form.roles.data = request.form.get("roles")

        # เรียกใช้ UserService เพื่อแก้ไขข้อมูล
        edit_result = UserService.edit_user(form)
        if not edit_result["success"]:
            return render_template(
                "/users-management/form-edit-user-role.html",
                user=user,
                departments=departments,
                roles=roles,
                form=form,
                error_msg=edit_result["error_msg"],
            )
        return render_template("/users-management/users-management.html", users=users)

    # แสดงฟอร์มพร้อมข้อมูลผู้ใช้งาน
    form.username.data = user.username
    form.department.data = user.department
    form.roles.data = ",".join(user.roles)

    return render_template(
        "/users-management/form-edit-user-role.html",
        user=user,
        departments=departments,
        roles=roles,
        form=form,
    )

