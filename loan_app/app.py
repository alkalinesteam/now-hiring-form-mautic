from datetime import datetime
from flask import Flask, request, render_template, redirect, url_for

from .models import get_session, Payment
from .utils import calculate_balances

app = Flask(__name__)

@app.route('/add-payment', methods=['GET', 'POST'])
def add_payment():
    session = get_session()
    if request.method == 'POST':
        amount = float(request.form['amount'])
        date_str = request.form['date']
        pay_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        payment = Payment(amount=amount, date=pay_date)
        session.add(payment)
        session.commit()
        return redirect(url_for('add_payment'))
    payments = [
        {'amount': p.amount, 'date': p.date}
        for p in session.query(Payment).order_by(Payment.date).all()
    ]
    balances = calculate_balances(payments)
    return render_template('add_payment.html', balances=balances)

if __name__ == '__main__':
    app.run(debug=True)
