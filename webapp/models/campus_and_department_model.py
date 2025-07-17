import mongoengine as me
import datetime

class CampusAndDepartment(me.Document):
    # name คือ ชื่อ campus ({"0":"hatyai"})
    name = me.DictField(required=True)
    # departments เป็น dict: {"1": "president", "2": "IT Department", ...}
    departments = me.DictField(required=True)

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(required=True, default=datetime.datetime.now)


    @staticmethod
    def get_campus_name(campus_id):
        """Get campus name from DB by id"""
        campus_obj = CampusAndDepartment.objects(id=campus_id).first()
        if campus_obj:
            return campus_obj.name["0"]  # Assuming name is a dict with key "0" for campus name
        return campus_id


    @staticmethod
    def get_department_name(campus_id, department_key):
        """Get department name by campus id and department key"""
        campus_obj = CampusAndDepartment.objects(id=campus_id).first()
        if campus_obj and department_key in campus_obj.departments:
            return campus_obj.departments[department_key]
        return department_key
    

    meta = {
            "collection": "campus_and_department",
            "indexes": ["name"],
        }
