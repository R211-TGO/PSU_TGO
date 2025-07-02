from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, logout_user, current_user
from ..forms.user_form import LoginForm, RegisterForm, EditUserForm, EditprofileForm
from ...services.user_service import UserService
from ...models import User, Role, Permission, FormAndFormula, Scope, Material, InputType
from ..views.emissoins import calculate_result
import datetime  # เพิ่ม import นี้


module = Blueprint("form_management", __name__, url_prefix="/form-management")


@module.route("/", methods=["GET"])
@login_required
def form_management():
    forms = FormAndFormula.objects()  # ดึงข้อมูลฟอร์มทั้งหมด
    return render_template("/form-management/form-management.html", forms=forms)


@module.route("/load-add-form", methods=["GET"])
@login_required
def load_add_form_and_formula():
    return render_template("/form-management/add-form-and-formula.html")


@module.route("/load-edit-form", methods=["GET"])
@login_required
def load_edit_form_and_formula():
    form_id = request.args.get("form_id")
    form = None
    if form_id:
        form = FormAndFormula.objects(id=form_id).first()
        if not form:
            return render_template(
                "/form-management/edit-form-and-formula.html",
                error_msg="Form not found",
            )
    return render_template("/form-management/edit-form-and-formula.html", form=form)


@module.route("/add-form", methods=["POST"])
@login_required
def add_form_and_formula():
    name = request.form.get("name")
    desc_form = request.form.get("desc_form")
    desc_formula = request.form.get("desc_formula")
    desc_formula2 = request.form.get("desc_formula2", "")  # เพิ่ม desc_formula2
    material_name = request.form.get("material_name")
    formula = request.form.get("formula")
    formula2 = request.form.get("formula2", "")  # เพิ่ม formula2

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

    try:
        # ตรวจสอบว่ามีฟอร์มที่ชื่อซ้ำหรือไม่
        existing_form = FormAndFormula.objects(name=name).first()
        if existing_form:
            return render_template(
                "/form-management/add-form-and-formula.html",
                error_msg="Form with this name already exists",
            )

        # สร้างฟอร์มใหม่
        form = FormAndFormula(
            name=name,
            desc_form=desc_form,
            desc_formula=desc_formula,
            desc_formula2=desc_formula2,  # เพิ่ม desc_formula2
            material_name=material_name,
            variables=variables,  # บันทึกตัวแปรที่ดึงมาจากฟิลด์
            formula=formula,
            formula2=formula2,  # เพิ่ม formula2
            input_types=input_fields,  # เพิ่ม input fields ลงในฟอร์ม
        )
        form.save()

    except Exception as e:
        return render_template(
            "/form-management/add-form-and-formula.html",
            error_msg=f"Failed to create form: {str(e)}",
        )

    # สำเร็จ → redirect ไปหน้า form-management
    return redirect(url_for("form_management.form_management"))


@module.route("/edit-form", methods=["POST"])
@login_required
def edit_form_and_formula():
    form_id = request.form.get("form_id")
    name = request.form.get("name")
    desc_form = request.form.get("desc_form")
    desc_formula = request.form.get("desc_formula")
    desc_formula2 = request.form.get("desc_formula2", "")
    material_name = request.form.get("material_name")
    formula = request.form.get("formula")
    formula2 = request.form.get("formula2", "")

    print(f"DEBUG: form_id={form_id}")
    print(f"DEBUG: name={name}")
    print(f"DEBUG: formula2={formula2}")
    print(f"DEBUG: desc_formula2={desc_formula2}")

    # ดึงข้อมูล input fields จากฟอร์ม
    input_fields = []
    variables = []

    fields = request.form.getlist("field")
    labels = request.form.getlist("label")
    input_types = request.form.getlist("input_type")
    units = request.form.getlist("unit")

    print(f"DEBUG: fields={fields}")
    print(f"DEBUG: labels={labels}")

    # ลูปผ่านข้อมูลที่ดึงมา
    for i in range(len(fields)):
        field = fields[i]
        label = labels[i] if i < len(labels) else ""
        input_type = input_types[i] if i < len(input_types) else "text"
        unit = units[i] if i < len(units) else ""

        if field and input_type:
            input_fields.append(InputType.create_input(field, label, input_type, unit))
            variables.append(field)

    try:
        # แก้ไขฟอร์มที่มีอยู่
        form = FormAndFormula.objects(id=form_id).first()
        if not form:
            print("DEBUG: Form not found")
            return render_template(
                "/form-management/edit-form-and-formula.html",
                error_msg="Form not found",
            )

        print(f"DEBUG: Found form: {form.name}")

        # ตรวจสอบว่ามีฟอร์มที่ชื่อซ้ำหรือไม่ (ยกเว้นฟอร์มปัจจุบัน)
        existing_form = FormAndFormula.objects(name=name, id__ne=form_id).first()
        if existing_form:
            print("DEBUG: Duplicate name found")
            return render_template(
                "/form-management/edit-form-and-formula.html",
                form=form,
                error_msg="Form with this name already exists",
            )

        # อัปเดตข้อมูลฟอร์มทีละฟิลด์
        form.name = name
        form.desc_form = desc_form
        form.desc_formula = desc_formula
        form.desc_formula2 = desc_formula2
        form.material_name = material_name
        form.variables = variables
        form.formula = formula
        form.formula2 = formula2
        form.input_types = input_fields
        form.update_date = datetime.datetime.now()
        
        # บันทึกการเปลี่ยนแปลง
        form.save()
        
        print("DEBUG: Form updated successfully")

        # ตรวจสอบว่ามี Material ที่เกี่ยวข้องหรือไม่
        materials = Material.objects(name=material_name)
        if materials:
            print(f"DEBUG: Found {len(materials)} materials to recalculate")
            for material in materials:
                calculate_result(material)
        else:
            print("DEBUG: No materials found for recalculation")

    except Exception as e:
        print(f"DEBUG: Exception occurred: {str(e)}")
        print(f"DEBUG: Exception type: {type(e)}")
        import traceback
        traceback.print_exc()
        
        return render_template(
            "/form-management/edit-form-and-formula.html",
            form=FormAndFormula.objects(id=form_id).first() if form_id else None,
            error_msg=f"Failed to update form: {str(e)}",
        )

    # สำเร็จ → redirect ไปหน้า form-management
    print("DEBUG: Redirecting to form management")
    return redirect(url_for("form_management.form_management"))


@module.route("/delete-form/<form_id>", methods=["DELETE"])
@login_required
def delete_form(form_id):
    try:
        form = FormAndFormula.objects(id=form_id).first()
        if not form:
            return jsonify({"success": False, "message": "Form not found"}), 404

        form.delete()
        return jsonify({"success": True, "message": "Form deleted successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
