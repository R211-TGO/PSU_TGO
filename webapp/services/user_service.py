from ..models.user_model import User
from flask_login import login_user, logout_user, current_user
from ..web.forms.user_form import RegisterForm, EditUserForm, EditprofileForm
import datetime


class UserService:
    @staticmethod
    def login(username: str, password: str):
        user = User.objects(username=username).first()
        error_msg = ""
        if not user or not user.check_password(password):
            error_msg = "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"

        if user and user.status == "disactive":
            error_msg = "บัญชีของท่านถูกลบออกจากระบบ"

        if error_msg:
            return {"error_msg": error_msg, "success": False}
        login_user(user)
        user.last_login_date = datetime.datetime.now()
        user.save()
        return {"error_msg": "", "success": True}

    @staticmethod
    def register(form: RegisterForm):
        username = form.username.data
        existing_user = User.objects(username=username).first()
        if existing_user:
            return {"success": False, "error_msg": "ชื่อผู้ใช้ซ้ำ"}

        if form.password.data != form.confirm_password.data:
            return {"success": False, "error_msg": "รหัสผ่านไม่ตรงกัน"}

        user = User(username=username)
        user.set_password(form.password.data)
        user.save()
        return {"success": True, "error_msg": ""}

    @staticmethod
    def edit_user(form: EditUserForm):
        user = User.objects(username=form.username.data).first()
        if not user:
            return {"success": False, "error_msg": "ไม่พบผู้ใช้"}

        user.username = form.username.data
        user.campus = form.campus.data
        user.department = form.department.data
        user.email = form.email.data
        user.roles = form.roles.data.split(",")
        user.save()
        return {"success": True, "error_msg": ""}

    @staticmethod
    def edit_profile(form: EditprofileForm):
        user = User.objects(id=current_user.id).first()
        if not user:
            return {"success": False, "error_msg": "ไม่พบผู้ใช้"}

        user.username = form.username.data
        user.email = form.email.data
        user.campus = form.campus.data
        user.department = form.department.data
        user.save()
        return {"success": True, "error_msg": ""}

    @staticmethod
    def est_password(username: str, password: str):
        user = User.objects(username=username).first()
        pass

        return {"success": True, "error_msg": ""}

    @staticmethod
    def change_password(new_password: str):
        user = User.objects(id=current_user.id).first()
        if not user:
            return {"success": False, "error_msg": "ไม่พบผู้ใช้"}

        user.set_password(new_password)
        user.save()
        return {"success": True, "error_msg": ""}
