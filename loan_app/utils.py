from datetime import date, timedelta
from typing import List

from fpdf import FPDF

# Loan details
PRINCIPAL = 120000.0
START_DATE = date(2019, 10, 1)
RATE_SCHEDULE = [
    (date(2019, 10, 1), 0.10),
    (date(2020, 10, 1), 0.12),
]
BORROWER_NAME = 'Hassan Majied'
PROPERTY_ADDRESS = '761 W Pratt St, Baltimore, MD'
BORROWER_EMAIL = 'micki+hassan@thegreengroupllc.com'
LENDER_EMAIL = 'micki@gmail.com'

def get_rate(for_date: date) -> float:
    current = RATE_SCHEDULE[0][1]
    for start, rate in RATE_SCHEDULE:
        if for_date >= start:
            current = rate
        else:
            break
    return current

def accrue_interest(balance: float, start: date, end: date) -> float:
    """Accrue interest between two dates."""
    current_date = start
    accrued = 0.0
    while current_date < end:
        next_month = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1)
        period_end = min(next_month, end)
        rate = get_rate(current_date)
        days = (period_end - current_date).days
        accrued += balance * rate / 365 * days
        current_date = period_end
    return accrued

def calculate_balances(payments: List[dict]) -> dict:
    """Return current principal and interest balances."""
    principal = PRINCIPAL
    interest = 0.0
    last_date = START_DATE
    for p in sorted(payments, key=lambda x: x['date']):
        interest += accrue_interest(principal, last_date, p['date'])
        payment_amount = p['amount']
        if payment_amount >= interest:
            payment_amount -= interest
            interest = 0.0
            principal -= payment_amount
        else:
            interest -= payment_amount
        last_date = p['date']
    interest += accrue_interest(principal, last_date, date.today())
    return {
        'principal': round(principal, 2),
        'interest': round(interest, 2),
        'total': round(principal + interest, 2),
    }

def generate_pdf(payments: List[dict], statement_date: date, filename: str) -> None:
    balances = calculate_balances(payments)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Helvetica', size=12)
    pdf.cell(0, 10, f'Loan Statement - {PROPERTY_ADDRESS}', ln=1)
    pdf.cell(0, 10, f'Statement Date: {statement_date.isoformat()}', ln=1)
    pdf.cell(0, 10, f'Borrower: {BORROWER_NAME}', ln=1)
    pdf.cell(0, 10, f'Original Principal: ${PRINCIPAL:,.2f}', ln=1)
    pdf.cell(0, 10, f'Current Balance: ${balances["total"]:,.2f}', ln=1)
    pdf.ln(10)
    pdf.cell(0, 10, 'Payments:', ln=1)
    for p in payments:
        pdf.cell(0, 10, f"{p['date'].isoformat()} - ${p['amount']:,.2f}", ln=1)
    pdf.output(filename)
