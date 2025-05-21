from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, logout_user, current_user
from ..forms.user_form import LoginForm, RegisterForm, EditUserForm, EditprofileForm
from ...services.user_service import UserService
from ...models import User, Role, Permission

module = Blueprint("form_management", __name__, url_prefix="/form-management")

@module.route("/", methods=["GET", "POST"])
@login_required
def form_management():
    roles = Role.objects()
    return render_template("/form-management/form-management.html", roles=roles)
