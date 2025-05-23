from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, logout_user, current_user
from ..forms.user_form import LoginForm, RegisterForm, EditUserForm, EditprofileForm
from ...services.user_service import UserService
from ...models import User, Role, Permission, FormAndFormula, Scope, Material, InputType

module = Blueprint("form_management", __name__, url_prefix="/form-management")

@module.route("/", methods=["GET"])
@login_required
def form_management():
    forms = FormAndFormula.objects()  # ดึงข้อมูลฟอร์มทั้งหมด
    return render_template("/form-management/form-management.html", forms=forms)

@module.route("/load-add-form", methods=["GET"])
@login_required
def load_add_form_and_formula():
    form_id = request.args.get("form_id")
    form = None
    if form_id:
        form = FormAndFormula.objects(id=form_id).first()
    return render_template(
        "/form-management/add-form-and-formula.html",
        form=form
    )

@module.route("/add-form", methods=["POST"])
@login_required
def add_form_and_formula():
    name = request.form.get("name")
    desc_form = request.form.get("desc_form")
    desc_formula = request.form.get("desc_formula")
    material_name = request.form.get("material_name")
    formula = request.form.get("formula")

    print(request.form)  # ตรวจสอบข้อมูลที่ส่งมาจากฟรอนต์เอนด์

    # ดึงข้อมูล input fields จากฟอร์ม
    input_fields = []
    variables = []  # ตัวแปรที่ใช้ในสูตร

    # ใช้ getlist() เพื่อดึงค่าที่ซ้ำกัน
    fields = request.form.getlist("field")
    labels = request.form.getlist("label")
    input_types = request.form.getlist("input_type")
    units = request.form.getlist("unit")

    # ลูปผ่านข้อมูลที่ดึงมา
    for i in range(len(fields)):
        field = fields[i]
        label = labels[i] if i < len(labels) else ""
        input_type = input_types[i] if i < len(input_types) else "text"
        unit = units[i] if i < len(units) else ""

        if field and input_type:
            input_fields.append(InputType.create_input(field, label, input_type, unit))
            variables.append(field)  # เพิ่ม field ลงในตัวแปร variables

    # ตรวจสอบว่ามีฟอร์มที่ชื่อซ้ำหรือไม่
    existing_form = FormAndFormula.objects(name=name).first()
    if existing_form:
        return render_template(
            "/form-management/add-form-and-formula.html",
            error_msg="Form with this name already exists"
        )

    try:
        # สร้างฟอร์มใหม่
        form = FormAndFormula(
            name=name,
            desc_form=desc_form,
            desc_formula=desc_formula,
            material_name=material_name,
            variables=variables,  # บันทึกตัวแปรที่ดึงมาจากฟิลด์
            formula=formula,
            input_types=input_fields  # เพิ่ม input fields ลงในฟอร์ม
        )
        form.save()
    except Exception as e:
        return render_template(
            "/form-management/add-form-and-formula.html",
            error_msg=f"Failed to create form: {str(e)}"
        )

    # สำเร็จ → redirect ไปหน้า form-management
    return redirect(url_for("form_management.form_management"))