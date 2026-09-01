"""
Generates PDF files for payslips and attestations using ReportLab.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

OUTPUT_DIR = "/tmp/generated_pdfs"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_payslip_pdf(payslip):
    path = os.path.join(OUTPUT_DIR, f"payslip_{payslip['employee_id']}_{payslip['month']}.pdf")
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, height - 2 * cm, "Bulletin de Paie")

    c.setFont("Helvetica", 11)
    y = height - 3.5 * cm
    c.drawString(2 * cm, y, f"Employé ID: {payslip['employee_id']}")
    y -= 0.7 * cm
    c.drawString(2 * cm, y, f"Mois: {payslip['month']}")
    y -= 1 * cm

    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, y, "Rubrique")
    c.drawString(12 * cm, y, "Montant")
    y -= 0.5 * cm
    c.line(2 * cm, y, 18 * cm, y)
    y -= 0.7 * cm

    c.setFont("Helvetica", 11)
    rows = [
        ("Salaire de base", payslip["base_salary"]),
        ("Primes", payslip["bonuses"]),
    ]
    for label, amount in rows:
        c.drawString(2 * cm, y, label)
        c.drawString(12 * cm, y, f"{amount:.2f} {payslip['currency']}")
        y -= 0.6 * cm

    y -= 0.3 * cm
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(2 * cm, y, "Retenues:")
    y -= 0.6 * cm
    c.setFont("Helvetica", 10)
    for label, amount in payslip["deductions"].items():
        c.drawString(2.5 * cm, y, f"- {label}")
        c.drawString(12 * cm, y, f"-{amount:.2f} {payslip['currency']}")
        y -= 0.5 * cm

    y -= 0.5 * cm
    c.line(2 * cm, y, 18 * cm, y)
    y -= 0.8 * cm
    c.setFont("Helvetica-Bold", 13)
    c.drawString(2 * cm, y, "Net à payer")
    c.drawString(12 * cm, y, f"{payslip['net_salary']:.2f} {payslip['currency']}")

    c.save()
    return path


def generate_attestation_pdf(employee, attestation_request):
    att_type = attestation_request["type"]
    title = "Attestation de Travail" if att_type == "attestation_travail" else "Attestation de Salaire"
    path = os.path.join(OUTPUT_DIR, f"attestation_{attestation_request['id']}.pdf")
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 3 * cm, title)

    c.setFont("Helvetica", 12)
    y = height - 6 * cm
    lines = [
        f"Nous soussignés, certifions que M./Mme {employee['full_name']},",
        f"titulaire de la CIN n° {employee['national_id']},",
        f"occupe le poste de {employee['position']} au sein du département {employee['department']},",
        f"depuis le {employee['hire_date']}.",
        "",
        "La présente attestation est délivrée à l'intéressé(e) pour servir et valoir",
        "ce que de droit.",
    ]
    for line in lines:
        c.drawString(2.5 * cm, y, line)
        y -= 0.8 * cm

    c.save()
    return path
