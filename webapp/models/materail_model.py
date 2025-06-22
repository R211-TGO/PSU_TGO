import mongoengine as me
import datetime


class QuantityType(me.EmbeddedDocument):
    field = me.StringField(required=True)
    label = me.StringField(required=True)
    amount = me.FloatField(required=True)
    unit = me.StringField(required=True)


class Material(me.Document):
    name = me.StringField(required=True)
    scope = me.IntField(required=True)
    form_and_formula = me.StringField(required=True)
    year = me.IntField(required=True)
    month = me.IntField(required=True)
    day = me.IntField(required=True)
    result = me.DynamicField(
        default=None
    )  # ใช้ DynamicField เพื่อรองรับค่า null หรือค่าประเภทอื่น
    create_date = me.DateTimeField(default=datetime.datetime.now)
    update_date = me.DateTimeField(default=datetime.datetime.now)
    edit_by_id = me.StringField(required=True)  # แก้ไขให้เป็น StringField
    sub_scope = me.IntField(required=True)
    department = me.StringField(required=True)
    campus = me.StringField(required=True)
    quantity_type = me.EmbeddedDocumentListField(QuantityType)

    meta = {
        "collection": "materials",
        "indexes": ["name", "scope", "year", "month", "day"],
    }
