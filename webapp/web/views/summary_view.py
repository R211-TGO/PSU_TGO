from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from ...models import Material, Scope
from datetime import datetime, timedelta
from bson import ObjectId

module = Blueprint("summary", __name__, url_prefix="/summary")


@module.route("/", methods=["GET"])
@login_required
def summary():
    user = current_user
    return render_template("/summary/summary.html", user=user)


@module.route("/scopes", methods=["GET"])
@login_required
def get_scopes():
    """HTMX endpoint สำหรับ load scope dropdown"""
    user = current_user

    all_scopes = Scope.objects(campus=user.campus, department=user.department)
    seen = set()
    unique_scopes = [
        s for s in all_scopes if not (s.ghg_scope in seen or seen.add(s.ghg_scope))
    ]

    return render_template(
        "/summary/partials/scope_dropdown.html", scopes=unique_scopes
    )


@module.route("/sub-scopes", methods=["POST"])
@login_required
def get_sub_scopes():
    """HTMX endpoint สำหรับ load sub scope dropdown ตาม scope ที่เลือก"""
    user = current_user

    # รับ scope ที่เลือก
    selected_scopes = request.form.getlist("selected_scopes")

    if not selected_scopes:
        return render_template(
            "/summary/partials/sub_scope_dropdown.html", sub_scopes=[]
        )

    # ดึง sub scopes ที่อยู่ใน scope ที่เลือกจาก campus และ department ที่เลือก
    sub_scopes = Scope.objects(
        campus=user.campus,
        department=user.department,
        ghg_scope__in=[int(scope) for scope in selected_scopes],
    )

    return render_template(
        "/summary/partials/sub_scope_dropdown.html", sub_scopes=sub_scopes
    )


@module.route("/api/materials", methods=["GET"])
@login_required
def get_materials():
    user = current_user

    # รับ parameters
    sub_scopes = request.args.getlist("sub_scopes[]")
    time_period = request.args.get("time_period", "week")

    if not sub_scopes:
        return jsonify(
            {
                "total_emissions": 0,
                "daily_average": 0,
                "materials_count": 0,
                "daily_data": {},
                "category_data": {},
            }
        )

    # กำหนดวันที่
    today = datetime.now()
    days = {"week": 7, "month": 30, "year": 365}
    start_date = today - timedelta(days=days[time_period])

    # Query materials
    sub_scope_ids = [int(s) for s in sub_scopes]
    materials = Material.objects(
        campus=user.campus,
        department=user.department,
        sub_scope__in=sub_scope_ids,
        create_date__gte=start_date,
    )

    # คำนวณข้อมูล
    total_emissions = sum(m.result or 0 for m in materials)
    daily_average = total_emissions / days[time_period]

    # จัดกลุ่มตามวันที่
    daily_data = {}
    for material in materials:
        date_key = f"{material.year}-{material.month:02d}-{material.day:02d}"
        daily_data[date_key] = daily_data.get(date_key, 0) + (material.result or 0)

    # จัดกลุ่มตาม scope
    category_data = {}
    for sub_scope_id in sub_scope_ids:
        scope = Scope.objects(
            campus=user.campus, department=user.department, ghg_sup_scope=sub_scope_id
        ).first()

        if scope:
            scope_name = f"Scope {scope.ghg_scope}"
            emissions = sum(
                m.result or 0 for m in materials if m.sub_scope == sub_scope_id
            )
            category_data[scope_name] = category_data.get(scope_name, 0) + emissions

    return jsonify(
        {
            "total_emissions": round(total_emissions, 2),
            "daily_average": round(daily_average, 2),
            "daily_data": daily_data,
            "category_data": category_data,
            "materials_count": materials.count(),
        }
    )


@module.route("/stats", methods=["POST"])
@login_required
def get_stats():
    """HTMX endpoint สำหรับ stats"""
    user = current_user

    sub_scopes = request.form.getlist("selected_sub_scopes")
    time_period = request.form.get("time_period", "week")

    if not sub_scopes:
        return '<div id="stats-container"><div class="text-center text-gray-500 p-8">Select Sub Scopes to view statistics</div></div>'

    data = calculate_emissions_data(user, sub_scopes, time_period)
    return render_template(
        "/summary/start_partial.html", data=data, time_period=time_period
    )


@module.route("/charts", methods=["POST"])
@login_required
def get_charts():
    """HTMX endpoint สำหรับ charts"""
    user = current_user

    sub_scopes = request.form.getlist("selected_sub_scopes")
    time_period = request.form.get("time_period", "week")

    if not sub_scopes:
        return '<div id="charts-container"><div class="text-center text-gray-500 p-8">Select Sub Scopes to view charts</div></div>'

    data = calculate_emissions_data(user, sub_scopes, time_period)
    return render_template("/summary/charts_partial.html", data=data)


def calculate_emissions_data(user, sub_scopes, time_period):
    """คำนวณข้อมูล emissions"""
    today = datetime.now()
    days = {"week": 7, "month": 30, "year": 365}

    # แปลง string IDs เป็น ObjectId
    scope_object_ids = [ObjectId(scope_id) for scope_id in sub_scopes]

    # ดึง scope objects จาก IDs
    scopes = Scope.objects(id__in=scope_object_ids)

    materials = Material.objects(
        campus=user.campus,
        department=user.department,
        scope__in=[s.ghg_scope for s in scopes],
        sub_scope__in=[s.ghg_sup_scope for s in scopes],
    )

    # จัดกลุ่มตามวันที่
    daily_data = {}
    for material in materials:
        date_key = datetime(material.year, material.month, material.day).strftime(
            "%B"
        )  # แปลงเป็นชื่อเดือน
        daily_data[date_key] = daily_data.get(date_key, 0) + (material.result or 0)

    # จัดกลุ่มตาม scope
    category_data = {}
    scope_data = {}
    for scope in scopes:
        scope_name = f"Scope {scope.ghg_scope}"
        emissions = sum(
            m.result or 0 for m in materials if m.sub_scope == scope.ghg_sup_scope
        )
        category_data[scope_name] = category_data.get(scope_name, 0) + emissions

        scope_data[scope_name] = {
            "ghg_scope": scope.ghg_scope,
            "ghg_sup_scope": scope.ghg_sup_scope,
            "emissions": emissions,
        }

    total_emissions = sum(m.result or 0 for m in materials)
    daily_average = total_emissions / days[time_period] if days[time_period] > 0 else 0

    return {
        "total_emissions": round(total_emissions, 2),
        "daily_average": round(daily_average, 2),
        "daily_data": daily_data,
        "category_data": category_data,
        "materials_count": len(materials),
        "scope_data": scope_data,
    }
