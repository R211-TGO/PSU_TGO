from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, logout_user, current_user
from ..forms.user_form import LoginForm, RegisterForm, EditUserForm, EditprofileForm
from ...services.user_service import UserService
from ...models import User, Role, Permission

module = Blueprint("users", __name__, url_prefix="/users")


@module.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    error_msg = ""
    if not form.validate_on_submit():
        if "password" in form.errors:
            if "Field must be at least 6 characters long." in form.errors["password"]:
                error_msg = "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"
            elif "This field is required." in form.errors["password"]:
                error_msg = "กรุณากรอกรหัสผ่าน"
            else:
                error_msg = "เกิดข้อผิดพลาดในการป้อนรหัสผ่าน"

        return render_template("/users/login.html", form=form, error_msg=error_msg)

    # Authenticate user
    login_result = UserService.login(form.username.data, form.password.data)
    if not login_result["success"]:
        return render_template(
            "/users/login.html", form=form, error_msg=login_result["error_msg"]
        )

    return redirect(request.args.get("next", url_for("index.index")))


@module.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("users.login"))


@module.route("/register", methods=["get", "post"])
def register():
    form = RegisterForm()

    if not form.validate_on_submit():
        return render_template("/users/register.html", form=form)

    register_result = UserService.register(form)
    if register_result["success"] is False:
        return render_template(
            "/users/register.html", form=form, error_msg=register_result["error_msg"]
        )

    return redirect(url_for("users.login"))


@module.route("/profile", methods=["get", "post"])
@login_required
def profile():
    return render_template("/users/profile.html", user=current_user)


@module.route("/users-management", methods=["get", "post"])
@login_required
def users_management():
    users = User.objects()
    return render_template("users/users-management.html", users=users)


@module.route("/roles-management", methods=["GET", "POST"])
@login_required
def roles_management():
    roles = Role.objects()
    return render_template("users/roles-management.html", roles=roles)


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
                "users_popup/form-edit-profile.html",
                user=user,
                departments=departments,
                form=form,
                error_msg=edit_result["error_msg"],
            )
        return redirect(url_for("users.profile"))

    # แสดงฟอร์มพร้อมข้อมูลผู้ใช้งาน
    form.username.data = user.username
    form.email.data = user.email
    form.department.data = user.department

    return render_template(
        "users_popup/form-edit-profile.html",
        user=user,
        departments=departments,
        form=form,
    )


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
                "users_popup/form-edit-user-role.html",
                user=user,
                departments=departments,
                roles=roles,
                form=form,
                error_msg=edit_result["error_msg"],
            )
        return render_template("users/users-management.html", users=users)

    # แสดงฟอร์มพร้อมข้อมูลผู้ใช้งาน
    form.username.data = user.username
    form.department.data = user.department
    form.roles.data = ",".join(user.roles)

    return render_template(
        "users_popup/form-edit-user-role.html",
        user=user,
        departments=departments,
        roles=roles,
        form=form,
    )


@module.route("/load-add-role", methods=["GET"])
@login_required
def load_add_role():
    # ดึงข้อมูล Permission ทั้งหมดจากฐานข้อมูล
    permissions = Permission.objects()

    return render_template(
        "users_popup/add_role.html",
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
            "users_popup/add_role.html",
            error_msg="Role already exists",
            permissions=permissions_list
        )

    try:
        role = Role(name=name, description=description, permission=permissions)
        role.save()
    except Exception as e:
        permissions_list = Permission.objects()
        return render_template(
            "users_popup/add_role.html",
            error_msg=f"Failed to create role: {str(e)}",
            permissions=permissions_list
        )

    # สำเร็จ → redirect ไป roles-management
    return redirect(url_for("users.roles_management"))
