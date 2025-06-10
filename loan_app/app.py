import os
from datetime import datetime, date
import threading
import time
import smtplib
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from sqlalchemy.orm import Session
from .models import get_session, Payment

try:
    from flask import Flask, render_template, request, redirect, url_for
except Exception:
    # Flask might not be available in the execution environment
    Flask = None
    def render_template(*a, **kw):
        return "Flask not available"
    def request():
        pass
    def redirect(url):
        return url
    def url_for(name):
        return name

PRINCIPAL = 120000.0
START_DATE = date(2019, 10, 1)
RATE_CHANGE_DATE = date(2020, 10, 1)
INITIAL_RATE = 0.10
RATE_AFTER_CHANGE = 0.12
BORROWER_NAME = "Hassan Majied"
PROPERTY_ADDRESS = "761 W Pratt St, Baltimore, MD"
BORROWER_EMAIL = "micki+hassan@thegreengroupllc.com"
LENDER_EMAIL = "micki@gmail.com"

app = Flask(__name__) if Flask else None

def init_db():
    # Ensure the database and tables exist
    session = get_session()
    session.close()


def add_month(d: date) -> date:
    year = d.year + (d.month // 12)
    month = d.month % 12 + 1
    return date(year, month, d.day)


def load_payments():
    session = get_session()
    try:
        payments = session.query(Payment).order_by(Payment.date).all()
        return [(p.amount, p.date) for p in payments]
    finally:
        session.close()


def save_payment(amount: float, d: date):
    session = get_session()
    try:
        session.add(Payment(amount=amount, date=d))
        session.commit()
    finally:
        session.close()


def interest_rate(for_date: date) -> float:
    return RATE_AFTER_CHANGE if for_date >= RATE_CHANGE_DATE else INITIAL_RATE


def calculate_state(as_of: date = date.today()):
    payments = load_payments()
    principal = PRINCIPAL
    unpaid_interest = 0.0
    current = START_DATE
    idx = 0
    while current < as_of:
        rate = interest_rate(current)
        monthly_interest = principal * rate / 12
        unpaid_interest += monthly_interest
        next_month = add_month(current)
        while idx < len(payments) and payments[idx][1] < next_month:
            amt = payments[idx][0]
            if amt <= unpaid_interest:
                unpaid_interest -= amt
                amt = 0
            else:
                amt -= unpaid_interest
                unpaid_interest = 0
            principal -= amt
            idx += 1
        current = next_month
    return principal, unpaid_interest


class SimplePDFWriter:
    def __init__(self):
        self.objects = []

    def add(self, obj: str):
        self.objects.append(obj)

    def build(self) -> bytes:
        pdf = b"%PDF-1.4\n"
        offsets = [0]
        for obj in self.objects:
            offsets.append(len(pdf))
            pdf += obj.encode("latin1") + b"\n"
        xref_pos = len(pdf)
        pdf += f"xref\n0 {len(self.objects)+1}\n".encode("latin1")
        pdf += b"0000000000 65535 f \n"
        for off in offsets[1:]:
            pdf += f"{off:010d} 00000 n \n".encode("latin1")
        pdf += b"trailer\n"
        pdf += f"<< /Size {len(self.objects)+1} /Root 1 0 R >>\n".encode("latin1")
        pdf += b"startxref\n"
        pdf += f"{xref_pos}\n".encode("latin1")
        pdf += b"%%EOF"
        return pdf


def generate_pdf(lines, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    writer = SimplePDFWriter()
    writer.add("1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj")
    writer.add("2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj")
    writer.add(
        "3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>endobj"
    )
    content = "BT /F1 12 Tf "
    y = 750
    for line in lines:
        safe = line.replace("(", "[").replace(")", "]")
        content += f"1 0 0 1 50 {y} Tm ({safe}) Tj "
        y -= 15
    content += "ET"
    writer.add(f"4 0 obj<< /Length {len(content)} >>stream\n{content}\nendstream\nendobj")
    writer.add("5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj")
    pdf_bytes = writer.build()
    with open(filename, "wb") as f:
        f.write(pdf_bytes)
    return filename


def email_statement(pdf_path: str, period: str):
    msg = MIMEMultipart()
    msg['From'] = LENDER_EMAIL
    msg['To'] = ", ".join([LENDER_EMAIL, BORROWER_EMAIL])
    msg['Subject'] = f"Loan Statement – 761 W Pratt – {period}"
    msg.attach(MIMEText("Attached is your loan statement for the month."))

    with open(pdf_path, 'rb') as f:
        part = MIMEBase('application', 'pdf')
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(pdf_path)}"')
        msg.attach(part)

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            # TODO: authenticate via OAuth2 or app password
            # server.login('you@gmail.com', 'password')
            server.sendmail(LENDER_EMAIL, [LENDER_EMAIL, BORROWER_EMAIL], msg.as_string())
    except Exception as e:
        print('Email failed:', e)


def generate_statement(as_of: date = None):
    if as_of is None:
        as_of = date.today()
    principal, interest = calculate_state(as_of)
    payments = load_payments()
    total_paid = sum(p[0] for p in payments)
    lines = [
        f"Loan Statement for {BORROWER_NAME}",
        f"Property: {PROPERTY_ADDRESS}",
        f"Statement Period: {as_of.strftime('%B %Y')}",
        "",
        f"Original Principal: ${PRINCIPAL:,.2f}",
        f"Current Principal Balance: ${principal:,.2f}",
        f"Accrued Interest: ${interest:,.2f}",
        f"Total Paid to Date: ${total_paid:,.2f}",
        "",
        "Payments:"
    ]
    for amt, d in payments:
        lines.append(f"{d.isoformat()} - ${amt:,.2f}")
    filename = os.path.join('statements', f"statement_{as_of.strftime('%Y_%m')}.pdf")
    return generate_pdf(lines, filename)


def scheduler_loop():
    while True:
        now = datetime.now()
        if now.day == 1:
            pdf = generate_statement(now.date())
            email_statement(pdf, now.strftime('%B %Y'))
            time.sleep(86400)  # wait a day to avoid duplicate
        time.sleep(3600)


if app:
    @app.route('/add-payment', methods=['GET', 'POST'])
    def add_payment():
        if request.method == 'POST':
            amount = float(request.form['amount'])
            d = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            save_payment(amount, d)
            return redirect(url_for('add_payment'))
        return render_template('add_payment.html')


def start_scheduler():
    t = threading.Thread(target=scheduler_loop, daemon=True)
    t.start()


if __name__ == '__main__':
    init_db()
    if app:
        start_scheduler()
        app.run(debug=True)
