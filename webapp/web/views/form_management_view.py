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

# เพิ่ม route ใหม่
@module.route("/get-sub-scopes/<int:main_scope>", methods=["GET"])
@login_required
def get_sub_scopes(main_scope):
    """
    ดึง sub scopes ตาม main scope ที่เลือก และ render template
    """
    try:
        print(f"get_sub_scopes called with main_scope: {main_scope}")
        print(f"Request args: {request.args}")
        print(f"Request values: {request.values}")
        
        # Query sub scopes จาก Scope model โดยใช้ ghg_scope
        sub_scopes_query = Scope.objects(ghg_scope=main_scope)
        print(f"Found {len(sub_scopes_query)} sub scopes for scope {main_scope}")
        
        # ใช้ set เพื่อเก็บ ghg_sup_scope ที่ไม่ซ้ำ
        seen_sup_scopes = set()
        unique_sub_scopes = []
        
        for scope in sub_scopes_query:
            if scope.ghg_sup_scope not in seen_sup_scopes:
                seen_sup_scopes.add(scope.ghg_sup_scope)
                unique_sub_scopes.append(scope)
                print(f"Added sub scope: {scope.ghg_sup_scope} - {scope.ghg_name}")
        
        print(f"Unique sub scopes: {len(unique_sub_scopes)}")
        
        # รับค่า selected_value จาก query parameter (สำหรับ edit form)
        selected_value = request.args.get('selected', None)
        print(f"Selected value from query: {selected_value}")
        
        if selected_value:
            try:
                selected_value = int(selected_value)
                print(f"Converted selected value: {selected_value}")
            except ValueError:
                selected_value = None
                print("Failed to convert selected value to int")
        
        # Render template
        template_content = render_template(
            "form-management/partials/sub-scope-select.html", 
            sub_scopes=unique_sub_scopes,
            selected_value=selected_value
        )
        
        print(f"Template rendered successfully, length: {len(template_content)}")
        return template_content
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in get_sub_scopes: {str(e)}")
        print(f"Full traceback: {error_details}")
        
        # Return simple error HTML
        error_html = f'''
        <select name="sup_scope" id="sub-scope" class="select select-bordered w-full mt-1" required>
            <option value="">Error loading sub scopes: {str(e)}</option>
        </select>
        '''
        return error_html


@module.route("/load-add-form", methods=["GET"])
@login_required
def load_add_form_and_formula():
    """
    โหลดหน้าเพิ่มฟอร์มใหม่ พร้อมรองรับ default scope
    """
    default_scope = request.args.get('default_scope', None)
    
    return render_template(
        "/form-management/add-form-and-formula.html",
        default_scope=default_scope
    )


# อัปเดต edit_form_and_formula function เพื่อรองรับ scope
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
        
        name = request.form.get("name")
        
        # อัปเดตข้อมูล form ตาม Model
        form.name = name  # ใช้ string ตรงๆ
        form.material_name = request.form.get("material_name")
        form.desc_form = request.form.get("desc_form")
        form.desc_formula = request.form.get("desc_formula")
        form.desc_formula2 = request.form.get("desc_formula2", "")
        form.formula = request.form.get("formula")
        form.formula2 = request.form.get("formula2", "")
        
        # เพิ่มการอัปเดต scope ตาม Model
        ghg_scope = request.form.get("scope")
        ghg_sup_scope = request.form.get("sup_scope")
        if ghg_scope and ghg_sup_scope:
            form.ghg_scope = int(ghg_scope)  # ใช้ ghg_scope
            try:
                form.ghg_sup_scope = int(ghg_sup_scope)  # ใช้ ghg_sup_scope
            except ValueError:
                return render_template(
                    "/form-management/edit-form-and-formula.html",
                    form=form,
                    error_msg="Sub Scope ต้องเป็นตัวเลขเท่านั้น"
                )
        
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
            form=None,  # ส่ง None แทน
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
                form=None,  # ส่ง None แทน
                error_msg="Invalid form ID format"
            )
        
        form = FormAndFormula.objects(id=object_id).first()
        if not form:
            return render_template(
                "/form-management/edit-form-and-formula.html",
                form=None,  # ส่ง None แทน
                error_msg="Form not found"
            )
        
        return render_template("/form-management/edit-form-and-formula.html", form=form)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template(
            "/form-management/edit-form-and-formula.html",
            form=None,  # ส่ง None แทน
            error_msg=f"Error loading form: {str(e)}"
        )

# อัปเดต add_form_and_formula function
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
        
        # เพิ่มการรับค่า scope ตาม Model
        ghg_scope = request.form.get("scope")
        ghg_sup_scope = request.form.get("sup_scope")

        # Debug: แสดงข้อมูลที่ได้รับ (ลบออกหลังจากแก้ไขเสร็จ)
        print(f"Debug - Received data:")
        print(f"name: '{name}'")
        print(f"material_name: '{material_name}'")
        print(f"ghg_scope: '{ghg_scope}'")
        print(f"ghg_sup_scope: '{ghg_sup_scope}'")

        # ตรวจสอบข้อมูลที่จำเป็น
        if not name or not material_name or not formula or not ghg_scope or not ghg_sup_scope:
            missing_fields = []
            if not name: missing_fields.append("ชื่อฟอร์ม")
            if not material_name: missing_fields.append("ชื่อวัสดุ")
            if not formula: missing_fields.append("สูตรคำนวณ")
            if not ghg_scope: missing_fields.append("Scope หลัก")
            if not ghg_sup_scope: missing_fields.append("Sub Scope")
            
            return jsonify({
                "success": False,
                "message": f"กรุณากรอกข้อมูลให้ครบถ้วน: {', '.join(missing_fields)}"
            }), 400

        # ตรวจสอบว่าชื่อฟอร์มซ้ำหรือไม่ (ใช้ string แทน int)
        existing_form_name = FormAndFormula.objects(name=name).first()
        if existing_form_name:
            print(f"Debug - Found existing form with name: {existing_form_name.name}")
            return jsonify({
                "success": False,
                "message": f'ชื่อฟอร์ม "{name}" มีอยู่แล้ว กรุณาใช้ชื่ออื่น'
            }), 409

        # ตรวจสอบว่าชื่อวัสดุซ้ำหรือไม่
        existing_material = FormAndFormula.objects(material_name=material_name).first()
        if existing_material:
            print(f"Debug - Found existing material with name: {existing_material.material_name}")
            return jsonify({
                "success": False,
                "message": f'ชื่อวัสดุ "{material_name}" มีอยู่แล้ว กรุณาใช้ชื่ออื่น'
            }, 409)

        # ตรวจสอบว่า ghg_sup_scope สามารถแปลงเป็น int ได้หรือไม่
        try:
            ghg_sup_scope_int = int(ghg_sup_scope)
        except ValueError:
            return jsonify({
                "success": False,
                "message": "Sub Scope ต้องเป็นตัวเลขเท่านั้น"
            }), 400

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

        # สร้าง FormAndFormula object ใหม่ตาม Model
        new_form = FormAndFormula(
            name=name,  # ใช้ string ตรงๆ
            desc_form=desc_form,
            desc_formula=desc_formula,
            desc_formula2=desc_formula2,
            material_name=material_name,
            formula=formula,
            formula2=formula2,
            ghg_scope=int(ghg_scope),  # ใช้ ghg_scope
            ghg_sup_scope=ghg_sup_scope_int,  # ใช้ int ที่แปลงแล้ว
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
        print(f"Debug - Exception occurred: {error_message}")
        
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
        
        # แปลงข้อมูลเป็น dict ตาม Model
        form_data = {
            "id": str(form.id),
            "name": form.name,
            "material_name": form.material_name,
            "desc_form": form.desc_form,
            "desc_formula": form.desc_formula,
            "desc_formula2": form.desc_formula2 or "",
            "formula": form.formula,
            "formula2": form.formula2 or "",
            "ghg_scope": form.ghg_scope,  # เพิ่ม ghg_scope
            "ghg_sup_scope": form.ghg_sup_scope,  # เพิ่ม ghg_sup_scope
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

# เพิ่ม delete route
@module.route("/delete-form/<form_id>", methods=["DELETE"])
@login_required
def delete_form(form_id):
    try:
        from bson import ObjectId
        from bson.errors import InvalidId
        
        try:
            object_id = ObjectId(form_id)
        except InvalidId:
            return jsonify({"success": False, "message": "Invalid form ID format"}), 400
        
        form = FormAndFormula.objects(id=object_id).first()
        if not form:
            return jsonify({"success": False, "message": "Form not found"}), 404
        
        form_name = form.name
        form.delete()
        
        return jsonify({
            "success": True,
            "message": f"Form '{form_name}' deleted successfully"
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": f"Error deleting form: {str(e)}"
        }), 500
