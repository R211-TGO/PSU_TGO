from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, logout_user, current_user
from ..forms.user_form import LoginForm, RegisterForm, EditUserForm, EditprofileForm
from ...services.user_service import UserService
from ...models import User, Role, Permission

module = Blueprint("profile", __name__, url_prefix="/profile")

@module.route("/", methods=["get", "post"])
@login_required
def profile():
    return render_template("/profile/profile.html", user=current_user)


@module.route("/load-edit-profile", methods=["GET", "POST"])
@login_required
def load_edit_profile():
    user = current_user  # ใช้ current_user เพื่อดึงข้อมูลผู้ใช้ที่ล็อกอินอยู่
    if not user:
        return jsonify({"error": "User not found"}), 404

    # ตัวอย่างข้อมูล Department
    departments = [
        "IT Department",
        "HR Department",
        "Finance Department",
        "Marketing Department",
    ]

    form = EditprofileForm()
    if request.method == "POST":
        # กรอกข้อมูลจากฟอร์ม
        form.username.data = request.form.get("username")
        form.email.data = request.form.get("email")
        form.department.data = request.form.get("department")

        # เรียกใช้ UserService เพื่อแก้ไขข้อมูล
        edit_result = UserService.edit_profile(form)
        if not edit_result["success"]:
            return render_template(
                "/profile/form-edit-profile.html",
                user=user,
                departments=departments,
                form=form,
                error_msg=edit_result["error_msg"],
            )
        return redirect(url_for("profile.profile"))

    # แสดงฟอร์มพร้อมข้อมูลผู้ใช้งาน
    form.username.data = user.username
    form.email.data = user.email
    form.department.data = user.department

    return render_template(
        "/profile/form-edit-profile.html",
        user=user,
        departments=departments,
        form=form,
    )