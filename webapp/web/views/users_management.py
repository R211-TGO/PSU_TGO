from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, logout_user, current_user
from ..forms.user_form import LoginForm, RegisterForm, EditUserForm, EditprofileForm
from ...services.user_service import UserService
from ...models import User, Role, Permission
from ..utils.acl import permissions_required

module = Blueprint("users_management", __name__, url_prefix="/users-management")


def get_campuses():
    return ["hatyai", "phuket", "surat", "trang"]


def get_departments():
    return [
        "IT Department",
        "HR Department",
        "Finance Department",
        "Marketing Department",
    ]


@module.route("/", methods=["get", "post"])
@login_required
# @permissions_required(['edit_management', 'view_management'])
def users_management():
    users = User.objects()
    return render_template(
        "/users-management/users-management.html",
        users=users,
        campuses=get_campuses(),
        departments=get_departments(),
    )


@module.route("/load-edit-user-role", methods=["GET", "POST"])
@login_required
def load_edit_user_role():
    user_id = request.args.get("user_id")
    page = int(request.args.get("page", 1))
    selected_campus = request.args.get("campus", None)
    selected_department = request.args.get("department", None)
    search_query = request.args.get("search", "").strip()  # รับค่าของ search

    user = User.objects.with_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    roles = Role.objects()
    form = EditUserForm()
    if request.method == "POST":
        form.username.data = user.username
        form.campus.data = request.form.get("campus")
        form.department.data = request.form.get("department")
        form.roles.data = request.form.get("roles")

        edit_result = UserService.edit_user(form)
        if not edit_result["success"]:
            return render_template(
                "/users-management/form-edit-user-role.html",
                user=user,
                campuses=get_campuses(),
                departments=get_departments(),
                roles=roles,
                form=form,
                error_msg=edit_result["error_msg"],
            )

        query = {}
        if selected_campus and selected_campus != "All Campuses":
            query["campus"] = selected_campus
        if selected_department and selected_department != "All Faculties":
            query["department"] = selected_department
        if search_query:  # ใช้ search ในการคิวรี่
            query["username__icontains"] = search_query

        users = User.objects(**query).skip((page - 1) * 10).limit(10)

        if request.headers.get("HX-Request"):
            return render_template(
                "/users-management/users-table.html",
                users=users,
                page=page,
                total_pages=(User.objects(**query).count() + 9) // 10,
                campuses=get_campuses(),
                departments=get_departments(),
                selected_campus=selected_campus,
                selected_department=selected_department,
                search_query=search_query,  # ส่ง search กลับไปด้วย
            )
        else:
            return redirect(url_for("users_management.users_management"))

    form.username.data = user.username
    form.campus.data = user.campus if user.campus else "none"
    form.department.data = user.department if user.department else "none"
    form.roles.data = ",".join(user.roles) if user.roles and len(user.roles) > 0 else ""

    return render_template(
        "/users-management/form-edit-user-role.html",
        user=user,
        campuses=get_campuses(),
        departments=get_departments(),
        roles=roles,
        form=form,
        page=page,
        selected_campus=selected_campus,
        selected_department=selected_department,
        search_query=search_query,  # ส่ง search กลับไปด้วย
    )


@module.route("/load-users-table", methods=["GET", "POST"])
@login_required
def load_users_table():
    page = int(request.args.get("page", 1))
    per_page = 10

    selected_campus = request.args.get("campus", None)
    selected_department = request.args.get("department", None)
    search_query = request.args.get("search", "").strip()

    query = {}
    if selected_campus and selected_campus != "All Campuses":
        query["campus"] = selected_campus
    if selected_department and selected_department != "All Faculties":
        query["department"] = selected_department
    if search_query:
        query["username__icontains"] = search_query

    total_users = User.objects(**query).count()
    total_pages = (total_users + per_page - 1) // per_page
    users = User.objects(**query).skip((page - 1) * per_page).limit(per_page)

    return render_template(
        "/users-management/users-table.html",
        users=users,
        page=page,
        total_pages=total_pages,
        campuses=get_campuses(),
        departments=get_departments(),
        selected_campus=selected_campus,
        selected_department=selected_department,
    )
