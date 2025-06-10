from datetime import date
from apscheduler.schedulers.background import BackgroundScheduler

from models import get_session, Payment
from utils import generate_pdf, BORROWER_EMAIL, LENDER_EMAIL
from utils import BORROWER_NAME, PROPERTY_ADDRESS
import smtplib
from email.message import EmailMessage


scheduler = BackgroundScheduler()


def send_statement():
    session = get_session()
    payments = [
        {'amount': p.amount, 'date': p.date}
        for p in session.query(Payment).all()
    ]
    filename = f'statement_{date.today().isoformat()}.pdf'
    generate_pdf(payments, date.today(), filename)
    send_email(filename)


def send_email(filename: str):
    msg = EmailMessage()
    msg['Subject'] = f'Loan Statement – 761 W Pratt – {date.today().strftime("%B %Y")}'
    msg['From'] = LENDER_EMAIL
    msg['To'] = ', '.join([LENDER_EMAIL, BORROWER_EMAIL])
    msg.set_content('Attached is your loan statement for the month.')
    with open(filename, 'rb') as f:
        msg.add_attachment(f.read(), maintype='application', subtype='pdf', filename=filename)
    # Here we would use OAuth2 or app password
    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        # smtp.login('user', 'password')
        # smtp.send_message(msg)
        pass


def start():
    scheduler.add_job(send_statement, 'cron', day=1, hour=0, minute=0)
    scheduler.start()
