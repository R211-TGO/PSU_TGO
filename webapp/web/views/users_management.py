from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, logout_user, current_user
from ..forms.user_form import LoginForm, RegisterForm, EditUserForm, EditprofileForm
from ...services.user_service import UserService
from ...models import User, Role, Permission
from ..utils.acl import permissions_required_all

module = Blueprint("users_management", __name__, url_prefix="/users-management")


# Centralized campus and department data
CAMPUS_DEPARTMENTS = {
    "hatyai": [
        "president",
        "IT Department",
        "HR Department1",
        "Finance Department1",
        "Marketing Department1",
    ],
    "phuket": [
        "president",
        "IT Department",
        "HR Department",
        "Finance Department", 
        "Marketing Department",
    ],
    "surat": [
        "president",
        "IT Department",
        "HR Department",
        "Finance Department",
        "Marketing Department",
    ],
    "trang": [
        "president",
        "IT Department",
        "HR Department",
        "Finance Department",
        "Marketing Department",
    ],
}


def get_campuses():
    """Get list of all available campuses"""
    return list(CAMPUS_DEPARTMENTS.keys())


def get_departments(campus):
    """Get departments for a specific campus"""
    if not campus or campus == "none" or campus == "All Campuses":
        return get_all_unique_departments()
    
    return CAMPUS_DEPARTMENTS.get(campus, [])


def get_all_unique_departments():
    """Get all unique department names across all campuses"""
    all_departments = []
    for campus_departments in CAMPUS_DEPARTMENTS.values():
        all_departments.extend(campus_departments)
    
    # Return unique departments sorted alphabetically
    return sorted(list(set(all_departments))) 


def normalize_department_name(department):
    """Remove trailing numbers from department names"""
    if not department:
        return department
    
    import re
    normalized = re.sub(r'\d+$', '', department).strip()
    return normalized if normalized else department


def get_user_department_for_campus(user_department, user_campus):
    """Get the correct department name for a user"""
    if not user_department or not user_campus:
        return user_department
    
    normalized_dept = normalize_department_name(user_department)
    available_departments = get_departments(user_campus)
    
    # Try exact match first
    if normalized_dept in available_departments:
        return normalized_dept
    
    # Try normalized match
    for dept in available_departments:
        if normalize_department_name(dept) == normalize_department_name(user_department):
            return dept
    
    return user_department


@module.route("/", methods=["get", "post"])
@login_required
@permissions_required_all(["view_users_management"])
# @permissions_required_all(['edit_management', 'view_management'])
def users_management():
    users = User.objects()
    return render_template(
        "/users-management/users-management.html",
        users=users,
        campuses=get_campuses(),
        departments=get_all_unique_departments(),
    )


@module.route("/load-edit-user-role", methods=["GET", "POST"])
@login_required
@permissions_required_all(['edit_users_management'])
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
                departments=get_all_unique_departments(),
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
                departments=get_all_unique_departments(),
                selected_campus=selected_campus,
                selected_department=selected_department,
                search_query=search_query,  # ส่ง search กลับไปด้วย
            )
        else:
            return redirect(url_for("users_management.users_management"))

    form.username.data = user.username
    form.campus.data = user.campus if user.campus else "none"
    
    # Set department with normalization
    user_department = user.department if user.department else "none"
    if user_department != "none" and user.campus:
        form.department.data = get_user_department_for_campus(user_department, user.campus)
    else:
        form.department.data = user_department
    
    form.roles.data = ",".join(user.roles) if user.roles and len(user.roles) > 0 else ""

    return render_template(
        "/users-management/form-edit-user-role.html",
        user=user,
        campuses=get_campuses(),
        departments=get_all_unique_departments(),
        roles=roles,
        form=form,
        page=page,
        selected_campus=selected_campus,
        selected_department=selected_department,
        search_query=search_query,  # ส่ง search กลับไปด้วย
    )


@module.route("/load-users-table", methods=["GET", "POST"])
@login_required
@permissions_required_all(["view_users_management"])
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
        departments=get_all_unique_departments(),
        selected_campus=selected_campus,
        selected_department=selected_department,
        search_query=search_query,
    )


@module.route("/load-departments", methods=["GET", "POST"])
@login_required
@permissions_required_all(['view_users_management'])
def load_departments():
    """Load department dropdown based on selected campus"""
    if request.method == "POST":
        selected_campus = request.form.get("campus", "")
        current_selected_department = request.form.get("department", "")
    else:
        selected_campus = request.args.get("campus", "")
        current_selected_department = request.args.get("department", "")
    
    if not selected_campus or selected_campus == "All Campuses":
        departments_list = get_all_unique_departments()
    else:
        departments_list = get_departments(selected_campus)
    
    return render_template(
        "/users-management/partials/department_dropdown.html",
        departments=departments_list,
        selected_department=current_selected_department
    )


@module.route("/load-departments-edit", methods=["POST"])
@login_required
@permissions_required_all(['edit_users_management'])
def load_departments_edit():
    """Load department dropdown for edit form"""
    selected_campus = request.form.get("campus", "")
    current_selected_department = request.form.get("department", "")
    is_change = request.form.get("is_change", "false") == "true"
    
    if not selected_campus or selected_campus == "none":
        departments_list = get_all_unique_departments()
    else:
        departments_list = get_departments(selected_campus)
    
    if is_change:
        current_selected_department = "none"
    elif current_selected_department:
        current_selected_department = get_user_department_for_campus(current_selected_department, selected_campus)
    
    return render_template(
        "/users-management/partials/department_edit_dropdown.html",
        departments=departments_list,
        selected_department=current_selected_department
    )


@module.route("/load-campuses", methods=["GET"])
@login_required
@permissions_required_all(['view_users_management'])
def load_campuses():
    """Load campus dropdown"""
    selected_campus = request.args.get("campus", "")
    
    return render_template(
        "/users-management/partials/campus_dropdown.html",
        campuses=get_campuses(),
        selected_campus=selected_campus
    )



