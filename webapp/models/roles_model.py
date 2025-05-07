import mongoengine as me
from flask_login import UserMixin, current_user
import datetime

class Role(me.Document, UserMixin):
    name = me.StringField(required=True, unique=True)
    permission = me.ListField(me.StringField(), default=["read"]) 
    description = me.StringField(required=False, unique=False, null=True, default="don't know")

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)

    meta = {"collection": "roles", "indexs": ["name"]}
