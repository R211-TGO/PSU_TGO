import mongoengine as me
import datetime
from bson import ObjectId


class UploadedFile(me.EmbeddedDocument):
    id = me.ObjectIdField(default=ObjectId, primary_key=True)  # เพิ่มฟิลด์ id
    filename = me.StringField(required=True)
    content_type = me.StringField(required=True)
    data = me.BinaryField(required=True)
    upload_date = me.DateTimeField(default=datetime.datetime.now)


class ReferenceDocument(me.Document):
    scope_id = me.IntField(required=True)
    sub_scope_id = me.IntField(required=True)
    year = me.IntField(required=True)
    month = me.IntField(required=True)
    campus = me.StringField(required=True)
    department = me.StringField(required=True)
    files = me.EmbeddedDocumentListField(UploadedFile)

    meta = {
        "collection": "reference_documents",
        "indexes": [
            "scope_id",
            "sub_scope_id",
            "year",
            "month",
            "campus",
            "department",
        ],
    }
