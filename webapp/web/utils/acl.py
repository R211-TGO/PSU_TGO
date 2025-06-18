from flask import abort, Flask, request, redirect, url_for
from flask_login import current_user, LoginManager, login_url
from functools import wraps
from ...models import User, Role, Permission

login_manager = LoginManager()


def init_acl(app: Flask):
    login_manager.init_app(app)


def roles_required(required_roles: list[str]):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user or not current_user.is_authenticated:
                abort(401)  # Unauthorized
            if current_user.role in required_roles:
                return func(*args, **kwargs)
            else:
                abort(403)  # Forbidden

        return wrapper

    return decorator


def permissions_required(required_permissions: list[str]):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user or not current_user.is_authenticated:
                abort(401)  # Unauthorized
            print(55555555555555555)
            # Query role ของ user
            try:
                user_role = Role.objects(name=current_user.roles[0]).first()
                print(user_role)
                if not user_role:

                    print(55555555555555555)
                    abort(403)  # ไม่พบ role
                print(user_role.name)
                
                # เช็คว่า user มี permission ที่ต้องการหรือไม่
                user_permissions = user_role.permission
                print(user_permissions)
                
                # เช็คว่ามี permission อย่างน้อย 1 ตัวที่ตรงกับที่ต้องการ
                print(required_permissions)
                has_permission = user_permissions in required_permissions
                
                if has_permission:
                    print(111111111)
                    return func(*args, **kwargs)
                else:
                    abort(403)  # Forbidden - ไม่มี permission
                    
            except Exception as e:
                print(8888)
                abort(403)  # Error occurred

        return wrapper

    return decorator


def permissions_required2(permission: list[str]):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user or not current_user.is_authenticated:
                abort(401)  # Unauthorized
            if current_user.has_permission(permission):
                return func(*args, **kwargs)
            else:
                abort(403)

        return wrapper

    return decorator


@login_manager.user_loader
def load_user(user_id):
    return User.objects.with_id(user_id)


@login_manager.unauthorized_handler
def unauthorized_callback():
    if request.method == "GET":
        response = redirect(login_url("users.login", request.url))
        return response

    return redirect(url_for("users.login"))
