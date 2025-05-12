import mongoengine as me
from flask_login import UserMixin, current_user
import datetime

def generate_default_email():
    """
    Generate a default email with an incrementing number.
    Example: user1@example.com, user2@example.com, etc.
    """
    last_user = User.objects.order_by("-created_date").first()
    if last_user and last_user.email and last_user.email.startswith("user"):
        # Extract the number from the last email and increment it
        try:
            last_number = int(last_user.email.split("@")[0][4:])  # Extract number after "user"
            return f"user{last_number + 1}@example.com"
        except ValueError:
            pass
    # Default to user1@example.com if no valid email exists
    return "user1@example.com"

class User(me.Document, UserMixin):
    username = me.StringField(required=True, unique=True)
    password = me.StringField(required=True)
    roles = me.ListField(me.StringField(), default=["user"]) 
    email = me.EmailField(required=False, unique=True, sparse=False, default=generate_default_email)
    campus = me.StringField(required=True, default="Not yet allocated")
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
