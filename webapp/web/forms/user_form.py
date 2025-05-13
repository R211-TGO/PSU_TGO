from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField,EmailField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired()])


class EditUserForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    department = StringField("Department")
    roles = StringField("Roles")
    # Add any other fields you need for editing the user

class EditprofileForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired()])
    campus = StringField("Campus")
    department = StringField("Department")

