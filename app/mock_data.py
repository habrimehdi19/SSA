"""
Mock data — simulates what would come from SAP HCM (Infotypes 0002, 0008, 2001, 2002, etc.)
Replace this with real SAP calls in sap_connector.py when ready.
"""

EMPLOYEES = {
    "1001": {
        "employee_id": "1001",
        "username": "j.alaoui",
        "password": "demo1234",  # In production: hashed, never plain text
        "full_name": "Jamal Alaoui",
        "position": "Technicien Maintenance",
        "department": "Production",
        "hire_date": "2019-03-01",
        "national_id": "AB123456",
    },
    "1002": {
        "employee_id": "1002",
        "username": "s.bennani",
        "password": "demo1234",
        "full_name": "Sara Bennani",
        "position": "Comptable",
        "department": "Finance",
        "hire_date": "2021-09-15",
        "national_id": "CD654321",
    },
}

MANAGERS = {
    "9001": {
        "employee_id": "9001",
        "username": "m.idrissi",
        "password": "manager1234",
        "full_name": "Karim Idrissi",
        "position": "Responsable RH",
    },
}

# key: (employee_id, "YYYY-MM")
PAYSLIPS = {
    ("1001", "2026-08"): {
        "employee_id": "1001",
        "month": "2026-08",
        "base_salary": 8500.00,
        "bonuses": 500.00,
        "deductions": {"CNSS": 297.50, "AMO": 187.00, "IR": 780.00},
        "net_salary": 7735.50,
        "currency": "MAD",
    },
    ("1002", "2026-08"): {
        "employee_id": "1002",
        "month": "2026-08",
        "base_salary": 9200.00,
        "bonuses": 0.00,
        "deductions": {"CNSS": 322.00, "AMO": 202.40, "IR": 950.00},
        "net_salary": 7725.60,
        "currency": "MAD",
    },
}

# Day-level attendance events per employee.
# status one of: "absence_maladie", "absence_autorisation", "absence_injustifiee", "retard"
# For "retard", extra key "minutes" gives how late.
# Any day not listed here (and not a weekend) is considered "present".
ATTENDANCE_EVENTS = {
    "1001": [
        {"date": "2026-08-05", "status": "retard", "minutes": 15},
        {"date": "2026-08-12", "status": "retard", "minutes": 30},
        {"date": "2026-08-18", "status": "absence_maladie", "note": "Grippe"},
        {"date": "2026-08-21", "status": "absence_autorisation", "note": "Rendez-vous administratif"},
        {"date": "2026-07-03", "status": "absence_injustifiee"},
        {"date": "2026-05-22", "status": "absence_autorisation", "note": "Congé exceptionnel"},
        {"date": "2026-02-10", "status": "absence_maladie", "note": "Maladie"},
    ],
    "1002": [
        {"date": "2026-08-08", "status": "retard", "minutes": 10},
        {"date": "2026-08-25", "status": "retard", "minutes": 30},
        {"date": "2026-06-15", "status": "absence_autorisation", "note": "Congé payé"},
    ],
}

# Requests submitted by employees: attestations, autorisation d'absence, justificatif médical
# type: "attestation_travail" | "attestation_salaire" | "autorisation_absence" | "justificatif_maladie"
REQUESTS = []
_next_request_id = 1


def next_request_id():
    global _next_request_id
    rid = _next_request_id
    _next_request_id += 1
    return rid


def get_attendance_events(employee_id):
    return ATTENDANCE_EVENTS.get(employee_id, [])
