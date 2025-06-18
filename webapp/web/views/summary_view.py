from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, logout_user, current_user
from ..forms.user_form import LoginForm, RegisterForm, EditUserForm, EditprofileForm
from ...services.user_service import UserService
from ...models import User, Role, Permission

module = Blueprint("summary", __name__, url_prefix="/summary")

@module.route("/", methods=["GET", "POST"])
@login_required
def summary():
    user = current_user
    return render_template("/summary/summary.html", user=user)