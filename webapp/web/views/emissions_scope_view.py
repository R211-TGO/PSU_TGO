from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, logout_user, current_user
from ..forms.user_form import LoginForm, RegisterForm, EditUserForm, EditprofileForm
from ...services.user_service import UserService
from ...models import User, Role, Permission

module = Blueprint("emissions_scope", __name__, url_prefix="/emissions-scope")

@module.route("/", methods=["get", "post"])
@login_required
def emissions_scope():
    return render_template("/emissions-scope/emissions-scope.html", user=current_user)

