from flask_mongoengine import MongoEngine
from flask import Flask

db = MongoEngine()

from .user_model import User
from .roles_model import Role
from .permission_model import Permission

def init_db(app: Flask):
    db.init_app(app)
