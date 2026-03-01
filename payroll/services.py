from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import calendar


def generate_payslip_pdf(payroll, buffer):
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("PAYSLIP", styles['Title']))
    elements.append(Spacer(1, 12))
    month_name = calendar.month_name[payroll.month]
    elements.append(Paragraph(f"Employee: {payroll.employee.full_name}", styles['Normal']))
    elements.append(Paragraph(f"Period: {month_name} {payroll.year}", styles['Normal']))
    elements.append(Paragraph(f"Department: {payroll.employee.department}", styles['Normal']))
    elements.append(Spacer(1, 12))

    data = [['Description', 'Amount']]
    data.append(['Basic Salary', f"${payroll.basic_salary:,.2f}"])
    for a in payroll.allowances.all():
        data.append([f"Allowance: {a.name}", f"${a.amount:,.2f}"])
    for d in payroll.deductions.all():
        data.append([f"Deduction: {d.name}", f"-${d.amount:,.2f}"])
    data.append(['NET SALARY', f"${payroll.net_salary:,.2f}"])

    table = Table(data, colWidths=[350, 150])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#343a40')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#198754')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    elements.append(table)
    doc.build(elements)

