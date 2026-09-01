"""
SAP Connector — abstraction layer
------------------------------------
Today: reads/writes mock_data.py
Tomorrow: replace internals with real SAP calls, e.g.

    from pyrfc import Connection
    conn = Connection(ashost="...", sysnr="...", client="...", user="...", passwd="...")
    result = conn.call("BAPI_EMPLOYEE_GETDATA", EMPLOYEE_ID=employee_id)

Every function signature below stays the same, so nothing in main.py
needs to change when you switch to a real SAP backend.
"""

import calendar as cal_module
from datetime import date, datetime

import mock_data as db

STATUS_LABELS = {
    "present": "Présent",
    "repos": "Repos hebdomadaire",
    "retard": "Retard",
    "absence_maladie": "Absence maladie",
    "absence_autorisation": "Absence autorisée",
    "absence_injustifiee": "Absence non justifiée",
}

STATUS_COLORS = {
    "present": "#DCEDE9",
    "repos": "#ECE7DB",
    "retard": "#F5E7CC",
    "absence_maladie": "#F5DEE0",
    "absence_autorisation": "#DFE6F4",
    "absence_injustifiee": "#E3A8AF",
}


def authenticate_employee(username, password):
    for emp in db.EMPLOYEES.values():
        if emp["username"] == username and emp["password"] == password:
            return emp
    return None


def authenticate_manager(username, password):
    for mgr in db.MANAGERS.values():
        if mgr["username"] == username and mgr["password"] == password:
            return mgr
    return None


def get_employee(employee_id):
    return db.EMPLOYEES.get(employee_id)


def get_payslip(employee_id, month):
    return db.PAYSLIPS.get((employee_id, month))


def get_attendance_summary(employee_id):
    events = db.get_attendance_events(employee_id)
    absences = [e for e in events if e["status"].startswith("absence")]
    late_total = sum(e.get("minutes", 0) for e in events if e["status"] == "retard")
    return {
        "year": datetime.now().year,
        "absences_count": len(absences),
        "late_minutes_total": late_total,
        "details": [
            {"date": e["date"], "type": STATUS_LABELS.get(e["status"], e["status"]),
             "reason": e.get("note", "")}
            for e in absences
        ],
    }


def get_month_calendar(employee_id, year_month):
    """Build a day-by-day view of a given month ('YYYY-MM').

    Returns a dict with the month's weeks (for grid rendering) and a
    flat dict of day -> event info for quick lookup/detail display.
    """
    year, month = map(int, year_month.split("-"))
    events_by_date = {e["date"]: e for e in db.get_attendance_events(employee_id)}

    _, days_in_month = cal_module.monthrange(year, month)
    today = date.today()

    days = {}
    for day_num in range(1, days_in_month + 1):
        d = date(year, month, day_num)
        iso = d.isoformat()
        event = events_by_date.get(iso)
        if event:
            status = event["status"]
        elif d.weekday() in (5, 6):  # Saturday/Sunday
            status = "repos"
        elif d > today:
            status = None  # future day, unknown yet
        else:
            status = "present"

        days[iso] = {
            "date": iso,
            "day": day_num,
            "weekday": d.weekday(),
            "status": status,
            "label": STATUS_LABELS.get(status, "—") if status else "—",
            "color": STATUS_COLORS.get(status, "#f9fafb") if status else "#f9fafb",
            "minutes": event.get("minutes") if event else None,
            "note": event.get("note") if event else None,
        }

    # calendar.Calendar gives us week rows aligned to the correct weekday
    cal = cal_module.Calendar(firstweekday=0)  # Monday first
    weeks = []
    for week in cal.monthdayscalendar(year, month):
        week_days = []
        for day_num in week:
            if day_num == 0:
                week_days.append(None)
            else:
                week_days.append(days[date(year, month, day_num).isoformat()])
        weeks.append(week_days)

    return {
        "year_month": year_month,
        "month_label": d.replace(day=1).strftime("%B %Y"),
        "weeks": weeks,
        "days": days,
    }


def create_request(employee_id, req_type, **fields):
    request_id = db.next_request_id()
    record = {
        "id": request_id,
        "employee_id": employee_id,
        "type": req_type,
        "status": "pending",  # pending -> approved / rejected
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        **fields,
    }
    db.REQUESTS.append(record)
    return record


def list_requests(employee_id):
    return [r for r in db.REQUESTS if r["employee_id"] == employee_id]


def get_request(employee_id, request_id):
    for r in db.REQUESTS:
        if r["id"] == request_id and r["employee_id"] == employee_id:
            return r
    return None


def list_all_requests(status=None):
    if status:
        return [r for r in db.REQUESTS if r["status"] == status]
    return list(db.REQUESTS)


def get_request_by_id(request_id):
    for r in db.REQUESTS:
        if r["id"] == request_id:
            return r
    return None


def set_request_status(request_id, status):
    r = get_request_by_id(request_id)
    if r:
        r["status"] = status
    return r


# --- Demo helper: kept for reference, no longer called automatically ---
def auto_approve_all_pending():
    for r in db.REQUESTS:
        if r["status"] == "pending":
            r["status"] = "approved"
