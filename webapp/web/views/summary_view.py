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

    # รับ scope ที่เลือกและ sub scope ที่เคยติ๊กไว้
    selected_scopes = request.form.getlist("selected_scopes")
    current_selected_sub_scopes = request.form.getlist("selected_sub_scopes")
    

    if not selected_scopes:
        # ถ้าไม่มี scope ใดถูกเลือก ให้แสดง sub scope ทั้งหมดในระบบ
        # เพื่อให้ยังคงเห็น sub scope ที่เคยติ๊กไว้
        sub_scopes = Scope.objects(
            campus=user.campus,
            department=user.department,
        ).order_by('ghg_scope', 'ghg_sup_scope')
    else:
        # ถ้ามี scope ที่เลือก ให้แสดงเฉพาะ sub scope ในสโคปนั้น
        sub_scopes = Scope.objects(
            campus=user.campus,
            department=user.department,
            ghg_scope__in=[int(scope) for scope in selected_scopes],
        ).order_by('ghg_scope', 'ghg_sup_scope')
    

    return render_template(
        "/summary/partials/sub_scope_dropdown.html", 
        sub_scopes=sub_scopes,
        current_selected_sub_scopes=current_selected_sub_scopes
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


@module.route("/clear-stats", methods=["POST"])
@login_required
def clear_stats():
    """HTMX endpoint สำหรับ clear stats เมื่อ scope เปลี่ยน"""
    return '<div id="stats-container"><div class="text-center text-gray-500 p-8">Select Sub Scopes to view statistics</div></div>'


@module.route("/clear-charts", methods=["POST"])
@login_required
def clear_charts():
    """HTMX endpoint สำหรับ clear charts เมื่อ scope เปลี่ยน"""
    return '<div id="charts-container"><div class="text-center text-gray-500 p-8">Select Sub Scopes to view charts</div></div>'


@module.route("/stats", methods=["POST"])
@login_required
def get_stats():
    """HTMX endpoint สำหรับ stats - คิวรี่ใหม่ทุกครั้ง"""
    user = current_user

    selected_scopes = request.form.getlist("selected_scopes")
    selected_sub_scopes = request.form.getlist("selected_sub_scopes")
    time_period = request.form.get("time_period", "week")

    if not selected_sub_scopes:
        return '<div id="stats-container"><div class="text-center text-gray-500 p-8">Select Sub Scopes to view statistics</div></div>'

    # คิวรี่ใหม่ทุกครั้ง - กรองตาม scope ที่เลือกและ sub scope ที่เลือก
    scope_object_ids = [ObjectId(scope_id) for scope_id in selected_sub_scopes]
    
    # ดึง sub scope objects ทั้งหมดที่เลือก
    all_selected_sub_scopes = Scope.objects(
        id__in=scope_object_ids,
        campus=user.campus,
        department=user.department
    )
    
    # กรองเฉพาะ sub scope ที่อยู่ใน scope ที่เลือก (ถ้ามี scope ที่เลือก)
    if selected_scopes:
        valid_sub_scopes = [
            scope for scope in all_selected_sub_scopes 
            if scope.ghg_scope in [int(s) for s in selected_scopes]
        ]
    else:
        # ถ้าไม่มี scope หลักที่เลือก ให้ใช้ sub scope ทั้งหมดที่เลือก
        valid_sub_scopes = list(all_selected_sub_scopes)
    
    valid_sub_scope_ids = [str(scope.id) for scope in valid_sub_scopes]
    
    if not valid_sub_scope_ids:
        return '<div id="stats-container"><div class="text-center text-gray-500 p-8">No valid data for current selection</div></div>'
    
    data = calculate_emissions_data(user, valid_sub_scope_ids, time_period)
    return render_template(
        "/summary/start_partial.html", data=data, time_period=time_period
    )


@module.route("/charts", methods=["POST"])
@login_required
def get_charts():
    """HTMX endpoint สำหรับ charts - คิวรี่ใหม่ทุกครั้ง"""
    user = current_user

    selected_scopes = request.form.getlist("selected_scopes")
    selected_sub_scopes = request.form.getlist("selected_sub_scopes")
    time_period = request.form.get("time_period", "week")

    if not selected_sub_scopes:
        return '<div id="charts-container"><div class="text-center text-gray-500 p-8">Select Sub Scopes to view charts</div></div>'

    # คิวรี่ใหม่ทุกครั้ง - กรองตาม scope ที่เลือกและ sub scope ที่เลือก
    scope_object_ids = [ObjectId(scope_id) for scope_id in selected_sub_scopes]
    
    # ดึง sub scope objects ทั้งหมดที่เลือก
    all_selected_sub_scopes = Scope.objects(
        id__in=scope_object_ids,
        campus=user.campus,
        department=user.department
    )
    
    # กรองเฉพาะ sub scope ที่อยู่ใน scope ที่เลือก (ถ้ามี scope ที่เลือก)
    if selected_scopes:
        valid_sub_scopes = [
            scope for scope in all_selected_sub_scopes 
            if scope.ghg_scope in [int(s) for s in selected_scopes]
        ]
    else:
        # ถ้าไม่มี scope หลักที่เลือก ให้ใช้ sub scope ทั้งหมดที่เลือก
        valid_sub_scopes = list(all_selected_sub_scopes)
    
    valid_sub_scope_ids = [str(scope.id) for scope in valid_sub_scopes]
    
    if not valid_sub_scope_ids:
        return '<div id="charts-container"><div class="text-center text-gray-500 p-8">No valid data for current selection</div></div>'
    
    data = calculate_emissions_data(user, valid_sub_scope_ids, time_period)
    return render_template("/summary/charts_partial.html", data=data)


def calculate_emissions_data(user, sub_scopes, time_period):
    """คำนวณข้อมูล emissions - คิวรี่ใหม่ทุกครั้ง"""
    today = datetime.now()
    days = {"week": 7, "month": 30, "year": 365}
    start_date = today - timedelta(days=days[time_period])


    # แปลง string IDs เป็น ObjectId
    scope_object_ids = [ObjectId(scope_id) for scope_id in sub_scopes]

    # ดึง scope objects จาก IDs
    scopes = Scope.objects(
        id__in=scope_object_ids,
        campus=user.campus,
        department=user.department
    )

    # คิวรี่ materials ใหม่ทุกครั้ง
    materials = Material.objects(
        campus=user.campus,
        department=user.department,
        scope__in=[s.ghg_scope for s in scopes],
        sub_scope__in=[s.ghg_sup_scope for s in scopes],
        create_date__gte=start_date
    )

    # จัดกลุ่มตามวันที่
    daily_data = {}
    for material in materials:
        date_key = datetime(material.year, material.month, material.day).strftime("%B")
        daily_data[date_key] = daily_data.get(date_key, 0) + (material.result or 0)

    # จัดกลุ่มตาม scope
    category_data = {}
    scope_data = {}
    for scope in scopes:
        scope_name = f"Scope {scope.ghg_scope}"
        emissions = sum(
            m.result or 0 for m in materials 
            if m.scope == scope.ghg_scope and m.sub_scope == scope.ghg_sup_scope
        )
        category_data[scope_name] = category_data.get(scope_name, 0) + emissions

        scope_key = f"Scope {scope.ghg_scope}.{scope.ghg_sup_scope}"
        scope_data[scope_key] = {
            "ghg_scope": scope.ghg_scope,
            "ghg_sup_scope": scope.ghg_sup_scope,
            "emissions": emissions,
            "scope_object": scope,
            "ghg_name": scope.ghg_name
        }

    total_emissions = sum(m.result or 0 for m in materials)
    daily_average = total_emissions / days[time_period] if days[time_period] > 0 else 0

    return {
        "total_emissions": round(total_emissions, 2),
        "daily_average": round(daily_average, 2),
        "daily_data": daily_data,
        "category_data": category_data,
        "materials_count": materials.count(),
        "scope_data": scope_data,
    }


@module.route("/update-badges", methods=["POST"])
@login_required
def update_badges():
    """HTMX endpoint สำหรับอัปเดต badges"""
    user = current_user
    
    selected_scopes = request.form.getlist('selected_scopes')
    selected_sub_scopes = request.form.getlist('selected_sub_scopes')
    
    
    # ดึงข้อมูล sub scopes ที่เลือกทั้งหมด
    sub_scope_objects = []
    if selected_sub_scopes:
        scope_object_ids = [ObjectId(scope_id) for scope_id in selected_sub_scopes]
        all_sub_scopes = Scope.objects(id__in=scope_object_ids)
        
        # กรองเฉพาะ sub scope ที่อยู่ใน scope ที่เลือก (ถ้ามี scope ที่เลือก)
        if selected_scopes:
            sub_scope_objects = [
                scope for scope in all_sub_scopes 
                if scope.ghg_scope in [int(s) for s in selected_scopes]
            ]
        else:
            sub_scope_objects = list(all_sub_scopes)
    
    # จัดกลุ่ม sub scopes ตาม main scope
    scope_groups = {}
    for sub_scope in sub_scope_objects:
        main_scope = sub_scope.ghg_scope
        if main_scope not in scope_groups:
            scope_groups[main_scope] = []
        scope_groups[main_scope].append(sub_scope)
    
    # ตรวจสอบว่าเลือกครบทุก sub scope ในแต่ละ main scope หรือไม่
    scope_badges = []
    
    for main_scope in selected_scopes:
        main_scope_int = int(main_scope)
        
        # หาจำนวน sub scope ทั้งหมดใน main scope นี้
        total_sub_scopes = Scope.objects(
            campus=user.campus,
            department=user.department,
            ghg_scope=main_scope_int
        ).count()
        
        # หาจำนวน sub scope ที่เลือกใน main scope นี้
        selected_in_scope = len(scope_groups.get(main_scope_int, []))
        
        if selected_in_scope == 0:
            # ไม่ได้เลือก sub scope ใดเลย แสดงแค่ scope หลัก
            scope_badges.append({
                'type': 'scope_only',
                'text': f'Scope {main_scope}',
                'class': 'badge-accent'
            })
        elif selected_in_scope == total_sub_scopes and total_sub_scopes > 0:
            # เลือกครบทุก sub scope ในสโคปนี้
            scope_badges.append({
                'type': 'scope_all',
                'text': f'Scope {main_scope} (ทั้งหมด)',
                'class': 'badge-success'
            })
        else:
            # เลือกบางส่วน แสดง sub scope ที่เลือก
            for sub_scope in scope_groups.get(main_scope_int, []):
                scope_badges.append({
                    'type': 'sub_scope',
                    'text': f'{sub_scope.ghg_name}',
                    'class': 'badge-info'
                })
    
    # ถ้าไม่มี scope หลักที่เลือก แต่มี sub scope ที่เลือก ให้แสดง sub scope ทั้งหมด
    if not selected_scopes and sub_scope_objects:
        for sub_scope in sub_scope_objects:
            scope_badges.append({
                'type': 'sub_scope',
                'text': f'Scope ({sub_scope.ghg_scope}.{sub_scope.ghg_sup_scope}) {sub_scope.ghg_name}',
                'class': 'badge-info'
            })
    
    return render_template("/summary/partials/active_badges.html", 
                         selected_scopes=selected_scopes,
                         sub_scope_objects=sub_scope_objects,
                         scope_badges=scope_badges,
                         user=user)