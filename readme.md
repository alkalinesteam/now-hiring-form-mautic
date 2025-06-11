# Loan Tracker Flask App

This simple Flask application tracks loan payments and generates monthly PDF statements. Payments are stored in a local SQLite database. A scheduler can automatically generate and email a statement on the first of each month.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the application:
   ```bash
   python -m loan_app.app
   ```
3. To enable the scheduler, import and call `scheduler.start()` from `loan_app/scheduler.py` with valid Gmail credentials.
