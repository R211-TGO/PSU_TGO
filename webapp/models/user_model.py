import mongoengine as me
from flask_login import UserMixin, current_user
import datetime


class User(me.Document, UserMixin):
    username = me.StringField(required=True, unique=True)
    password = me.StringField(required=True)
    roles = me.ListField(me.StringField(), default=["user"]) 
    email = me.EmailField(required=False, unique=True, sparse=True, null=True, default=None)
    department = me.StringField(
        required=False, unique=False, null=True, default=""
    )
    status = me.StringField(
        required=True, default="active", choices=["active", "disactive"]
    )

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )
    last_login_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    meta = {"collection": "users", "indexs": ["username"]}

    def set_password(self, password):
        from werkzeug.security import generate_password_hash

        self.password = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash

        return bool(check_password_hash(self.password, password))
