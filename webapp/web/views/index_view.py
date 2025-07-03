from flask import Blueprint, render_template
from flask_login import login_required, logout_user, current_user

module = Blueprint("index", __name__)


@module.route("/")
@login_required
def index():
    user = current_user
    return render_template("/index/index.html", user=user)
