"""
SAP Employee Self-Service Portal — MVP with mock data
-------------------------------------------------------
This is a prototype. All employee data comes from mock_data.py instead
of a real SAP system. To connect to real SAP later, replace the functions
in sap_connector.py with real RFC/OData calls — nothing else needs to change.
"""

import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, send_file, send_from_directory, flash

from sap_connector import (
    authenticate_employee,
    authenticate_manager,
    get_payslip,
    get_attendance_summary,
    get_month_calendar,
    create_request,
    list_requests,
    get_request,
    get_employee,
    list_all_requests,
    get_request_by_id,
    set_request_status,
)
from pdf_generator import generate_payslip_pdf, generate_attestation_pdf

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

UPLOAD_FOLDER = "/tmp/ess_uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_IMAGE_EXT = {"png", "jpg", "jpeg", "webp", "heic"}


def save_certificate_image(file_storage):
    """Save an uploaded medical certificate image, return its stored filename or None."""
    if not file_storage or file_storage.filename == "":
        return None
    ext = file_storage.filename.rsplit(".", 1)[-1].lower() if "." in file_storage.filename else ""
    if ext not in ALLOWED_IMAGE_EXT:
        return None
    stored_name = f"{uuid.uuid4().hex}.{ext}"
    file_storage.save(os.path.join(UPLOAD_FOLDER, stored_name))
    return stored_name


def login_required(view_func):
    from functools import wraps

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if "employee_id" not in session:
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapper


def manager_required(view_func):
    from functools import wraps

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if session.get("role") != "manager":
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapper


@app.route("/", methods=["GET"])
def index():
    if session.get("role") == "manager":
        return redirect(url_for("admin_requests"))
    if "employee_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        manager = authenticate_manager(username, password)
        if manager:
            session.clear()
            session["employee_id"] = manager["employee_id"]
            session["employee_name"] = manager["full_name"]
            session["role"] = "manager"
            return redirect(url_for("admin_requests"))

        employee = authenticate_employee(username, password)
        if employee:
            session.clear()
            session["employee_id"] = employee["employee_id"]
            session["employee_name"] = employee["full_name"]
            session["role"] = "employee"
            return redirect(url_for("dashboard"))

        flash("اسم المستخدم أو كلمة السر غير صحيحة", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    attendance = get_attendance_summary(session["employee_id"])
    return render_template(
        "dashboard.html",
        employee_name=session["employee_name"],
        attendance=attendance,
    )


@app.route("/agenda")
@login_required
def agenda():
    month = request.args.get("month") or datetime.now().strftime("%Y-%m")
    cal_data = get_month_calendar(session["employee_id"], month)

    # compute previous/next month for navigation
    year, mo = map(int, month.split("-"))
    prev_year, prev_mo = (year - 1, 12) if mo == 1 else (year, mo - 1)
    next_year, next_mo = (year + 1, 1) if mo == 12 else (year, mo + 1)

    return render_template(
        "agenda.html",
        cal=cal_data,
        month=month,
        prev_month=f"{prev_year:04d}-{prev_mo:02d}",
        next_month=f"{next_year:04d}-{next_mo:02d}",
    )


@app.route("/payslip", methods=["GET", "POST"])
@login_required
def payslip():
    month = request.values.get("month") or datetime.now().strftime("%Y-%m")
    data = get_payslip(session["employee_id"], month)
    return render_template("payslip.html", payslip=data, month=month)


@app.route("/payslip/pdf")
@login_required
def payslip_pdf():
    month = request.args.get("month") or datetime.now().strftime("%Y-%m")
    data = get_payslip(session["employee_id"], month)
    if not data:
        flash("لا توجد بيانات لهذا الشهر", "error")
        return redirect(url_for("payslip"))
    path = generate_payslip_pdf(data)
    return send_file(path, as_attachment=True, download_name=f"payslip_{month}.pdf")


@app.route("/requests", methods=["GET", "POST"])
@login_required
def requests_page():
    if request.method == "POST":
        req_type = request.form.get("type")
        extra = {}
        if req_type == "autorisation_absence":
            extra = {
                "date_debut": request.form.get("date_debut"),
                "date_fin": request.form.get("date_fin"),
                "motif": request.form.get("motif"),
            }
        elif req_type == "absence_maladie":
            image_filename = save_certificate_image(request.files.get("certificat"))
            extra = {
                "date_debut": request.form.get("date_debut"),
                "date_fin": request.form.get("date_fin"),
                "note": request.form.get("note"),
                "certificat_filename": image_filename,
            }
        create_request(session["employee_id"], req_type, **extra)
        flash("تم إرسال طلبك بنجاح، فانتظار موافقة المسؤول", "success")
        return redirect(url_for("requests_page"))

    all_requests = list_requests(session["employee_id"])
    return render_template("requests.html", requests=all_requests)


@app.route("/uploads/<filename>")
@login_required
def uploaded_certificate(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route("/requests/<int:request_id>/pdf")
@login_required
def request_pdf(request_id):
    req = get_request(session["employee_id"], request_id)
    if not req or req["status"] != "approved":
        flash("الطلب غير موافق عليه بعد", "error")
        return redirect(url_for("requests_page"))
    if req["type"] not in ("attestation_travail", "attestation_salaire"):
        flash("لا يوجد PDF لهذا النوع من الطلبات", "error")
        return redirect(url_for("requests_page"))
    employee = get_employee(session["employee_id"])
    path = generate_attestation_pdf(employee, req)
    return send_file(path, as_attachment=True, download_name=f"document_{request_id}.pdf")


REQUEST_TYPE_LABELS = {
    "attestation_travail": "Attestation de travail",
    "attestation_salaire": "Attestation de salaire",
    "autorisation_absence": "Autorisation d'absence",
    "absence_maladie": "Absence maladie",
}


@app.route("/admin/requests")
@manager_required
def admin_requests():
    status_filter = request.args.get("status", "pending")
    if status_filter == "all":
        items = list_all_requests()
    else:
        items = list_all_requests(status=status_filter)

    # enrich with employee name + human label, most recent first
    enriched = []
    for r in sorted(items, key=lambda x: x["id"], reverse=True):
        emp = get_employee(r["employee_id"])
        enriched.append({
            **r,
            "employee_name": emp["full_name"] if emp else r["employee_id"],
            "type_label": REQUEST_TYPE_LABELS.get(r["type"], r["type"]),
        })

    return render_template(
        "admin.html",
        requests=enriched,
        status_filter=status_filter,
        manager_name=session["employee_name"],
    )


@app.route("/admin/requests/<int:request_id>/approve", methods=["POST"])
@manager_required
def admin_approve(request_id):
    set_request_status(request_id, "approved")
    flash("تم قبول الطلب", "success")
    return redirect(url_for("admin_requests", status=request.form.get("status_filter", "pending")))


@app.route("/admin/requests/<int:request_id>/reject", methods=["POST"])
@manager_required
def admin_reject(request_id):
    set_request_status(request_id, "rejected")
    flash("تم رفض الطلب", "error")
    return redirect(url_for("admin_requests", status=request.form.get("status_filter", "pending")))


@app.route("/admin/uploads/<filename>")
@manager_required
def admin_uploaded_certificate(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
