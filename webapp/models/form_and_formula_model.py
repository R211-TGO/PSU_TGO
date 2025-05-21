import mongoengine as me
import datetime


class InputType(me.EmbeddedDocument):
    field = me.StringField(required=True)  # ชื่อฟิลด์ เช่น "n"
    label = me.StringField(required=True)  # คำอธิบาย เช่น "ไนโตรเจน (N)"
    input_type = me.StringField(
        required=True, choices=["number", "text", "select"]
    )  # ประเภทอินพุต เช่น "number"
    unit = me.StringField(required=False, default="")  # หน่วย เช่น "kg"

    @staticmethod
    def create_input(field, label, input_type, unit=""):
        """
        สร้าง InputType ใหม่
        """
        return InputType(field=field, label=label, input_type=input_type, unit=unit)


class FormAndFormula(me.Document):
    name = me.StringField(
        required=True, unique=True
    )  # ชื่อฟอร์ม เช่น "สูตรคำนวณคาร์บอนฟุตพริ้นท์ปุ๋ย"
    desc_form = me.StringField(required=True)  # คำอธิบายฟอร์ม
    desc_formula = me.StringField(required=True)  # คำอธิบายสูตร
    # input_types = me.EmbeddedDocumentListField(InputType)  # รายการของอินพุต
    input_types = me.EmbeddedDocumentListField(InputType)  # รายการของอินพุต
    variables = me.ListField(
        me.StringField(), required=True
    )  # ตัวแปรที่ใช้ในสูตร เช่น ["n", "p", "k"]
    formula = me.StringField(
        required=True
    )  # สูตรคำนวณ เช่น "n * 1.2 + p * 1.1 + k * 0.9"
    create_date = me.DateTimeField(default=datetime.datetime.now)  # วันที่สร้าง
    update_date = me.DateTimeField(default=datetime.datetime.now)  # วันที่อัปเดต

    material_name = me.StringField(required=True)  # ชื่อวัสดุที่ใช้ในฟอร์ม

    def add_input_type(self, input_type):
        """
        เพิ่ม InputType ลงในฟิลด์ input_types
        """
        self.input_types.append(input_type)

    def save_form(self):
        """
        บันทึกฟอร์มลงในฐานข้อมูล
        """
        self.update_date = datetime.datetime.now()
        self.save()

    meta = {
        "collection": "form_and_formula",  # ชื่อคอลเลกชันใน MongoDB
        "indexes": ["name"],  # ดัชนีสำหรับการค้นหา
    }


# from webapp.models.form_and_formula_model import FormAndFormula, InputType

# # สร้างฟอร์มใหม่
# form = FormAndFormula(
#     name="สูตรคำนวณคาร์บอนฟุตพริ้นท์ปุ๋ย",
#     desc_form="ฟอร์มคำนวณคาร์บอนฟุตพริ้นท์จาก NPK",
#     desc_formula="สูตรนี้จะรวมคาร์บอนฟุตพริ้นท์ของ N, P, และ K โดยใช้สัดส่วนที่กำหนด",
#     variables=["n", "p", "k"],
#     formula="n * 1.2 + p * 1.1 + k * 0.9"
# )

# # เพิ่ม InputType ลงในฟอร์ม
# form.add_input_type(InputType.create_input(field="n", label="ไนโตรเจน (N)", input_type="number", unit="kg"))
# form.add_input_type(InputType.create_input(field="p", label="ฟอสฟอรัส (P)", input_type="number", unit="kg"))
# form.add_input_type(InputType.create_input(field="k", label="โพแทสเซียม (K)", input_type="number", unit="kg"))

# # บันทึกฟอร์มลงในฐานข้อมูล
# form.save_form()
