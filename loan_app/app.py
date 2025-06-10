from datetime import datetime
from flask import Flask, request, render_template_string, redirect, url_for

from models import get_session, Payment
from utils import calculate_balances

app = Flask(__name__)

form_html = """
<form method='post'>
  Amount: <input type='number' name='amount' step='0.01' required><br>
  Date: <input type='date' name='date' required><br>
  <input type='submit'>
</form>
"""

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
    html = form_html + f"<p>Principal: ${balances['principal']:.2f}<br>Interest: ${balances['interest']:.2f}<br>Total: ${balances['total']:.2f}</p>"
    return render_template_string(html)

if __name__ == '__main__':
    app.run(debug=True)
