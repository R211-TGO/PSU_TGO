import mongoengine as me
import datetime


class Scope(me.Document):
    ghg_scope = me.IntField(required=True)  # Scope เช่น 1
    ghg_sup_scope = me.IntField(required=True)  # Scope หลัก เช่น 1
    ghg_name = me.StringField(required=True)  # ชื่อ GHG
    ghg_desc = me.StringField(required=False, default="")  # คำอธิบาย GHG
    campus = me.StringField(required=True)
    department = me.StringField(required=True)
    head_table = me.ListField(
        me.StringField(), default=[]
    )  # รายการหัวข้อ เช่น ["transport", "vehicle"]
    create_date = me.DateTimeField(default=datetime.datetime.now)  # วันที่สร้าง
    update_date = me.DateTimeField(default=datetime.datetime.now)  # วันที่อัปเดต

    meta = {
        "collection": "scope",  # ชื่อคอลเลกชันใน MongoDB
        "indexes": ["ghg_scope", "ghg_sup_scope"],  # ดัชนีสำหรับการค้นหา
    }
