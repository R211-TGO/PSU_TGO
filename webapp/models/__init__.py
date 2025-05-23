from flask_mongoengine import MongoEngine
from flask import Flask

db = MongoEngine()

from .user_model import User
from .roles_model import Role
from .permission_model import Permission
from .materail_model import Material
from .scope_model import Scope
from .form_and_formula_model import FormAndFormula, InputType

def init_db(app: Flask):
    db.init_app(app)
