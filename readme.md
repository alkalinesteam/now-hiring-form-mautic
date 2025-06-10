# Loan Tracking Flask App

This simple Flask application tracks loan payments, calculates monthly interest, generates PDF statements and emails them to the borrower and lender.

## Features
- Add payment amounts and dates via `/add-payment` form
- Calculates interest (10% until Oct 1 2020 then 12%)
- Generates a basic PDF statement summarizing the loan
- Sends the PDF using Gmail SMTP
- Background scheduler checks daily and emails a statement on the 1st of each month

## Usage
1. Ensure Python 3 is installed along with Flask and SQLAlchemy (`pip install -r requirements.txt`).
2. Run `python -m loan_app.app` to start the web server and scheduler.
3. Navigate to `http://localhost:5000/add-payment` to record payments.
4. When deploying with Gunicorn use `loan_app.app:app` as the WSGI path.

The email function uses Gmail's SMTP server. Update authentication in `email_statement` before running in production.
