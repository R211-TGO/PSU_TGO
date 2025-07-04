from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, logout_user, current_user
from ..forms.user_form import LoginForm, RegisterForm, EditUserForm, EditprofileForm
from ...services.user_service import UserService
from ...models import User, Role, Permission, FormAndFormula, Scope, Material, InputType
from ..views.emissoins import calculate_result
import datetime


module = Blueprint("form_management", __name__, url_prefix="/form-management")


@module.route("/", methods=["GET"])
@login_required
def form_management():
    forms = FormAndFormula.objects()
    return render_template("/form-management/form-management.html", forms=forms)


@module.route("/load-add-form", methods=["GET"])
@login_required
def load_add_form_and_formula():
    return render_template("/form-management/add-form-and-formula.html")


@module.route("/edit-form", methods=["POST"])
@login_required
def edit_form_and_formula():
    form_id = request.form.get("form_id")
    
    if not form_id:
        return render_template(
            "/form-management/edit-form-and-formula.html",
            error_msg="No form ID provided"
        )
    
    try:
        from bson import ObjectId
        form = FormAndFormula.objects(id=ObjectId(form_id)).first()
        
        if not form:
            return render_template(
                "/form-management/edit-form-and-formula.html",
                error_msg="Form not found"
            )
        
        # อัปเดตข้อมูล form
        form.name = request.form.get("name")
        form.material_name = request.form.get("material_name")
        form.desc_form = request.form.get("desc_form")
        form.desc_formula = request.form.get("desc_formula")
        form.desc_formula2 = request.form.get("desc_formula2", "")
        form.formula = request.form.get("formula")
        form.formula2 = request.form.get("formula2", "")
        
        # อัปเดต input fields
        input_fields = []
        variables = []
        
        fields = request.form.getlist("field")
        labels = request.form.getlist("label")
        input_types = request.form.getlist("input_type")
        units = request.form.getlist("unit")
        
        for i in range(len(fields)):
            field = fields[i]
            label = labels[i] if i < len(labels) else ""
            input_type = input_types[i] if i < len(input_types) else "text"
            unit = units[i] if i < len(units) else ""
            
            if field and input_type:
                input_fields.append(InputType.create_input(field, label, input_type, unit))
                variables.append(field)
        
        form.input_types = input_fields
        form.variables = variables
        form.save()
        
        return redirect(url_for("form_management.form_management"))
        
    except Exception as e:
        return render_template(
            "/form-management/edit-form-and-formula.html",
            form=form if 'form' in locals() else None,
            error_msg=f"Failed to update form: {str(e)}"
        )

@module.route("/load-edit-form", methods=["GET"])
@login_required
def load_edit_form_and_formula():
    form_id = request.args.get("form_id")
    
    if not form_id:
        return render_template(
            "/form-management/edit-form-and-formula.html",
            error_msg="No form ID provided"
        )
    
    try:
        from bson import ObjectId
        from bson.errors import InvalidId
        
        try:
            object_id = ObjectId(form_id)
        except InvalidId:
            return render_template(
                "/form-management/edit-form-and-formula.html",
                error_msg="Invalid form ID format"
            )
        
        form = FormAndFormula.objects(id=object_id).first()
        if not form:
            return render_template(
                "/form-management/edit-form-and-formula.html",
                error_msg="Form not found"
            )
        
        return render_template("/form-management/edit-form-and-formula.html", form=form)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template(
            "/form-management/edit-form-and-formula.html",
            error_msg=f"Error loading form: {str(e)}"
        )

@module.route("/add-form", methods=["POST"])
@login_required
def add_form_and_formula():
    try:
        name = request.form.get("name")
        desc_form = request.form.get("desc_form")
        desc_formula = request.form.get("desc_formula")
        desc_formula2 = request.form.get("desc_formula2", "")
        material_name = request.form.get("material_name")
        formula = request.form.get("formula")
        formula2 = request.form.get("formula2", "")

        # ตรวจสอบข้อมูลที่จำเป็น
        if not name or not material_name or not formula:
            return jsonify({
                "success": False,
                "message": "กรุณากรอกข้อมูลให้ครบถ้วน: ชื่อฟอร์ม, ชื่อวัสดุ, และสูตรคำนวณ"
            }), 400

        # ตรวจสอบว่าชื่อฟอร์มซ้ำหรือไม่
        existing_form_name = FormAndFormula.objects(name=name).first()
        if existing_form_name:
            return jsonify({
                "success": False,
                "message": f'ชื่อฟอร์ม "{name}" มีอยู่แล้ว กรุณาใช้ชื่ออื่น'
            }), 409

        # ตรวจสอบว่าชื่อวัสดุซ้ำหรือไม่
        existing_material = FormAndFormula.objects(material_name=material_name).first()
        if existing_material:
            return jsonify({
                "success": False,
                "message": f'ชื่อวัสดุ "{material_name}" มีอยู่แล้ว กรุณาใช้ชื่ออื่น'
            }), 409

        # ดึงข้อมูล input fields จากฟอร์ม
        input_fields = []
        variables = []

        fields = request.form.getlist("field")
        labels = request.form.getlist("label")
        input_types = request.form.getlist("input_type")
        units = request.form.getlist("unit")

        # ลูปผ่านข้อมูลที่ดึงมา
        for i in range(len(fields)):
            field = fields[i] if i < len(fields) else ""
            label = labels[i] if i < len(labels) else ""
            input_type = input_types[i] if i < len(input_types) else "text"
            unit = units[i] if i < len(units) else ""

            if field and input_type:
                input_fields.append(InputType.create_input(field, label, input_type, unit))
                variables.append(field)

        # สร้าง FormAndFormula object ใหม่
        new_form = FormAndFormula(
            name=name,
            desc_form=desc_form,
            desc_formula=desc_formula,
            desc_formula2=desc_formula2,
            material_name=material_name,
            formula=formula,
            formula2=formula2,
            input_types=input_fields,
            variables=variables
        )

        # บันทึกลง MongoDB
        new_form.save()

        # สำเร็จ → ส่ง JSON response แทน redirect
        return jsonify({
            "success": True,
            "message": f'สร้างฟอร์ม "{name}" สำเร็จแล้ว',
            "redirect_url": url_for("form_management.form_management")
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        
        # จัดการ error ตามประเภท
        error_message = str(e)
        if "duplicate key error" in error_message:
            if "name_1" in error_message:
                error_message = f'ชื่อฟอร์ม "{name}" มีอยู่แล้ว กรุณาใช้ชื่ออื่น'
            elif "material_name_1" in error_message:
                error_message = f'ชื่อวัสดุ "{material_name}" มีอยู่แล้ว กรุณาใช้ชื่ออื่น'
        elif "NotUniqueError" in str(type(e)):
            if "name" in str(e):
                error_message = f'ชื่อฟอร์ม "{name}" มีอยู่แล้ว กรุณาใช้ชื่ออื่น'
            elif "material_name" in str(e):
                error_message = f'ชื่อวัสดุ "{material_name}" มีอยู่แล้ว กรุณาใช้ชื่ออื่น'
        else:
            error_message = f'เกิดข้อผิดพลาดในการบันทึกฟอร์ม: {str(e)}'
        
        return jsonify({
            "success": False,
            "message": error_message
        }), 500

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

@module.route("/get-form-data/<form_id>", methods=["GET"])
@login_required
def get_form_data(form_id):
    try:
        from bson import ObjectId
        from bson.errors import InvalidId
        
        try:
            object_id = ObjectId(form_id)
        except InvalidId:
            return jsonify({"success": False, "message": "Invalid form ID format"})
        
        form = FormAndFormula.objects(id=object_id).first()
        if not form:
            return jsonify({"success": False, "message": "Form not found"})
        
        # แปลงข้อมูลเป็น dict
        form_data = {
            "id": str(form.id),
            "name": form.name,
            "material_name": form.material_name,
            "desc_form": form.desc_form,
            "desc_formula": form.desc_formula,
            "desc_formula2": form.desc_formula2 or "",
            "formula": form.formula,
            "formula2": form.formula2 or "",
            "input_types": []
        }
        
        # แปลง input_types
        if form.input_types:
            for input_field in form.input_types:
                form_data["input_types"].append({
                    "field": input_field.field,
                    "label": input_field.label,
                    "input_type": input_field.input_type,
                    "unit": input_field.unit
                })
        
        return jsonify({"success": True, "form": form_data})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error loading form: {str(e)}"})
