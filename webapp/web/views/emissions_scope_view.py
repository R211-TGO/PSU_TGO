from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from ...models.scope_model import Scope

module = Blueprint("emissions_scope", __name__, url_prefix="/emissions-scope")

@module.route("/", methods=["GET"])
@login_required
def emissions_scope():
    # ดึงข้อมูล Scope ทั้งหมดจากฐานข้อมูล
    scopes = Scope.objects().order_by("ghg_scope")
    # จัดกลุ่ม Scope ตาม ghg_scope
    grouped_scopes = {}
    for scope in scopes:
        main_scope = f"Scope {scope.ghg_scope}"  # ใช้ ghg_scope เป็นหัวข้อหลัก
        if main_scope not in grouped_scopes:
            grouped_scopes[main_scope] = []
        grouped_scopes[main_scope].append({
            "id": scope.ghg_sup_scope,  # ใช้ ghg_sup_scope เป็นหัวข้อย่อย
            "title": scope.ghg_name,
            "progress": 0,  # Mockup progress เป็น 0%
            "status": "Not started"  # Mockup status
        })
    return render_template(
        "/emissions-scope/emissions-scope.html",
        user=current_user,
        mockup_data={
            "overall_progress": 0,  # Mockup progress รวม
            "total_sources": len(scopes),
            "in_progress": 0,
            "not_started": len(scopes),
            "completed": 0,
            "scopes": grouped_scopes
        }
    )


@module.route("/add", methods=["GET", "POST"])
@login_required
def add_scope():
    if request.method == "POST":
        action = request.form.get("action")  # ตรวจสอบการกระทำ (fetch_sub_scope หรือ save)
        ghg_scope = request.form.get("ghg_scope")
        ghg_sup_scope = request.form.get("ghg_sup_scope")
        ghg_name = request.form.get("ghg_name")
        ghg_desc = request.form.get("ghg_desc")

        # หากผู้ใช้กดปุ่ม "บันทึก"
        if action == "save":
            # ตรวจสอบว่าทุกช่องถูกกรอก
            if not ghg_scope or not ghg_sup_scope or not ghg_name or not ghg_desc:
                scopes = Scope.objects.distinct("ghg_scope")
                latest_sub_scope = None
                return render_template(
                    "/emissions-scope/add-scope.html",
                    error="กรุณากรอกข้อมูลให้ครบทุกช่อง",
                    scopes=scopes,
                    latest_sub_scope=latest_sub_scope
                )

            # ตรวจสอบว่ามี Scope ซ้ำหรือไม่
            existing_scope = Scope.objects(
                ghg_scope=int(ghg_scope),
                ghg_sup_scope=int(ghg_sup_scope)
            ).first()
            if existing_scope:
                scopes = Scope.objects.distinct("ghg_scope")
                latest_sub_scope = None
                return render_template(
                    "/emissions-scope/add-scope.html",
                    error="Scope และ Sub-Scope นี้มีอยู่แล้ว",
                    scopes=scopes,
                    latest_sub_scope=latest_sub_scope
                )

            # สร้าง Scope ใหม่
            scope = Scope(
                ghg_scope=int(ghg_scope),
                ghg_sup_scope=int(ghg_sup_scope),
                ghg_name=ghg_name,
                ghg_desc=ghg_desc
            )
            scope.save()

            # เรนเดอร์ HTML ของ add-scope-success.html
            return render_template(
                "/emissions-scope/add-scope-success.html",
                success="Scope added successfully!"
            )

    # กรณี GET: ดึง Scope หลักทั้งหมด
    scopes = Scope.objects.distinct("ghg_scope")
    latest_sub_scope = None
    return render_template(
        "/emissions-scope/add-scope.html",
        scopes=scopes,
        latest_sub_scope=latest_sub_scope
    )


@module.route("/get-latest-sub-scope", methods=["POST"])
@login_required
def get_latest_sub_scope():
    ghg_scope = request.json.get("ghg_scope")  # รับข้อมูลจาก JSON
    if not ghg_scope or not ghg_scope.isdigit():
        return jsonify({"latest_sub_scope": 1})  # ถ้า Scope หลักว่างหรือไม่ใช่ตัวเลข ให้เริ่มที่ 1
    ghg_scope = int(ghg_scope)
    latest_sub_scope = Scope.objects(ghg_scope=ghg_scope).order_by("-ghg_sup_scope").first()
    latest_sub_scope = latest_sub_scope.ghg_sup_scope + 1 if latest_sub_scope else 1
    return jsonify({"latest_sub_scope": latest_sub_scope})

@module.route("/edit/<int:ghg_scope>", methods=["GET", "POST"])
@login_required
def edit_scope(ghg_scope):
    scope = Scope.objects(ghg_scope=ghg_scope).first()
    if not scope:
        return redirect(url_for("emissions_scope.emissions_scope"))
    if request.method == "POST":
        scope.ghg_name = request.form.get("ghg_name")
        scope.ghg_desc = request.form.get("ghg_desc")
        scope.save()
        return render_template("/emissions-scope/edit-scope-success.html")
    return render_template("/emissions-scope/edit-scope.html", scope=scope)