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
    page = int(request.args.get("page", 1))
    user = User.objects.with_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    departments = [
        "IT Department",
        "HR Department",
        "Finance Department",
        "Marketing Department",
    ]
    roles = Role.objects()
    form = EditUserForm()
    if request.method == "POST":
        form.username.data = user.username
        form.department.data = request.form.get("department")
        form.roles.data = request.form.get("roles")

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

        # อัปเดตตารางผู้ใช้
        users = User.objects.skip((page - 1) * 10).limit(10)

        # ตรวจสอบว่าเป็นคำขอ HTMX หรือไม่
        # ถ้าใช่ให้ส่งกลับ HTML ของตารางผู้ใช้

        if request.headers.get("HX-Request"):
            return render_template(
                "/users-management/users-table.html",
                users=users,
                page=page,
                total_pages=(User.objects.count() + 9) // 10,
            )
        # ถ้าไม่ใช่ให้เปลี่ยนเส้นทางไปยังหน้า users-management
        # โดยไม่ต้องโหลดใหม่ทั้งหน้า
        else:
            return redirect(url_for("users_management.users_management"))

    form.username.data = user.username
    form.department.data = user.department
    form.roles.data = ",".join(user.roles)

    return render_template(
        "/users-management/form-edit-user-role.html",
        user=user,
        departments=departments,
        roles=roles,
        form=form,
        page=page,
    )


@module.route("/load-users-table", methods=["GET", "POST"])
@login_required
def load_users_table():
    page = int(request.args.get("page", 1))  # รับค่าหน้าปัจจุบันจาก query string
    per_page = 10  # จำนวนผู้ใช้ต่อหน้า
    total_users = User.objects.count()  # จำนวนผู้ใช้ทั้งหมด
    total_pages = (total_users + per_page - 1) // per_page  # คำนวณจำนวนหน้าทั้งหมด

    # ดึงข้อมูลผู้ใช้เฉพาะหน้าปัจจุบัน
    users = User.objects.skip((page - 1) * per_page).limit(per_page)

    # Debug: ตรวจสอบข้อมูล
    print(f"Users: {users}")
    print(f"Page: {page}, Total Pages: {total_pages}")

    return render_template(
        "/users-management/users-table.html",
        users=users,  # ส่งผู้ใช้ในหน้าปัจจุบัน
        page=page,
        total_pages=total_pages,  # จำนวนหน้าทั้งหมด
    )
