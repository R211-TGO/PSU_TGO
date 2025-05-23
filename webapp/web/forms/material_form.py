from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, FieldList, FormField
from wtforms.validators import DataRequired, Optional


class QuantityTypeForm(FlaskForm):
    field = StringField("Field", validators=[DataRequired()])
    label = StringField("Label", validators=[DataRequired()])
    amount = FloatField("Amount", validators=[DataRequired()])
    unit = StringField("Unit", validators=[DataRequired()])


class MaterialForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    scope = StringField("Scope", validators=[DataRequired()])
    form_and_formula = StringField("Form and Formula", validators=[DataRequired()])
    quantity_type = FieldList(FormField(QuantityTypeForm), min_entries=1)
    year = IntegerField("Year", validators=[DataRequired()])
    month = IntegerField("Month", validators=[DataRequired()])
    day = IntegerField("Day", validators=[DataRequired()])
    sub_scope = StringField("Sub Scope", validators=[DataRequired()])
