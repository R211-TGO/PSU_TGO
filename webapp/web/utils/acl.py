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


def permissions_required_any(required_permissions: list[str]):
    """
    ตรวจสอบว่า user มี permission อย่างน้อย 1 ตัวใน list ที่ต้องการ
    รองรับ: 1 user หลาย roles, 1 role หลาย permissions
    
    Example:
    @permissions_required_any(['view_users', 'edit_users'])
    # User ต้องมี permission อย่างน้อย 1 ใน 2 ตัวนี้
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user or not current_user.is_authenticated:
                abort(401)
            
            if not current_user.roles:
                abort(403)
            
            try:
                user_permissions = _get_user_permissions()
                has_permission = any(perm in user_permissions for perm in required_permissions)
                
                if has_permission:
                    return func(*args, **kwargs)
                else:
                    abort(403)
                    
            except Exception:
                abort(403)

        return wrapper
    return decorator


def permissions_required_all(required_permissions: list[str]):
    """
    ตรวจสอบว่า user มี permission ครบทุกตัวใน list ที่ต้องการ
    รองรับ: 1 user หลาย roles, 1 role หลาย permissions
    
    Example:
    @permissions_required_all(['view_users', 'edit_users', 'delete_users'])
    # User ต้องมี permission ครบทั้ง 3 ตัว
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user or not current_user.is_authenticated:
                abort(401)
            
            if not current_user.roles:
                abort(403)
            
            try:
                user_permissions = _get_user_permissions()
                has_all_permissions = all(perm in user_permissions for perm in required_permissions)
                
                if has_all_permissions:
                    return func(*args, **kwargs)
                else:
                    abort(403)
                    
            except Exception:
                abort(403)

        return wrapper
    return decorator


def permissions_required(required_permissions: list[str]):
    """
    Alias สำหรับ permissions_required_any เพื่อ backward compatibility
    """
    return permissions_required_any(required_permissions)


def _get_user_permissions():
    """
    Helper function: รวม permissions จากทุก roles ของ user
    """
    user_permissions = set()  # ใช้ set เพื่อไม่ให้ซ้ำ
    
    for role_name in current_user.roles:
        role = Role.objects(name=role_name).first()
        if role and role.permission:
            # ถ้า permission เป็น list
            if isinstance(role.permission, list):
                user_permissions.update(role.permission)
            # ถ้า permission เป็น string
            else:
                user_permissions.add(role.permission)
    
    return list(user_permissions)


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
