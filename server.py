#! /usr/bin/env python3.6
import os
import stripe
from flask import Flask, request, jsonify, render_template
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Use environment variables for API keys
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')

# Simple customer storage
CUSTOMERS = [{"stripe_id": "cus_123456789", "email": "jenny.rosen@example.com"}]
PRICES = {"basic": "price_123456789", "professional": "price_987654321"}

@app.route('/')
def index():
    return render_template('index.html')

def get_or_create_customer(email):
    # Look up a customer in your database
    customers = [c for c in CUSTOMERS if c["email"] == email]
    if customers:
        customer_id = customers[0]["stripe_id"]
    else:
        # Create a new Customer
        customer = stripe.Customer.create(
            email=email,
            description="Customer for installment plan",
        )
        # Store the customer ID
        CUSTOMERS.append({"stripe_id": customer.id, "email": email})
        customer_id = customer.id
    
    return customer_id

@app.route('/create-installment-plan', methods=['POST'])
def create_installment_plan():
    data = request.json
    email = data.get('email')
    total_amount = int(data.get('amount', 1000))  # Amount in cents
    description = data.get('description', 'Payment Plan')

    if total_amount < 1:
        return jsonify({"success": False, "error": "Amount must be at least $0.01"}), 400

    
    try:
        # Get or create customer
        customer_id = get_or_create_customer(email)
        
        # Calculate installment amount (50% each)
        installment_amount = total_amount // 2
        
        # Create first invoice (due immediately)
        first_invoice = stripe.Invoice.create(
            customer=customer_id,
            collection_method='send_invoice',
            days_until_due=0,  # Due immediately
            description=f"{description} - Installment 1 of 2",
        )
        
        # Add line item for first installment
        stripe.InvoiceItem.create(
            customer=customer_id,
            amount=installment_amount,
            currency='usd',
            description=f"First installment (50%) - {description}",
            invoice=first_invoice.id
        )
        
        # Send the first invoice
        stripe.Invoice.send_invoice(first_invoice.id)
        
        # Create second invoice (due in 45 days)
        second_invoice = stripe.Invoice.create(
            customer=customer_id,
            collection_method='send_invoice',
            days_until_due=45,  # Due in 45 days from now
            description=f"{description} - Installment 2 of 2",
            auto_advance=False  # Do not send this invoice yet
        )
        
        # Add line item for second installment (50%)
        stripe.InvoiceItem.create(
            customer=customer_id,
            amount=installment_amount,  # no fee for second installment
            currency='usd',
            description=f"Second installment (50%) - {description}",
            invoice=second_invoice.id
        )
        
        # Do not send the second invoice yet
        # We will send the second invoice when its due date comes

        return jsonify({
            "success": True, 
            "first_invoice": first_invoice.id,
            "second_invoice": second_invoice.id,
            "amount_per_installment": installment_amount
        })
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        # Invalid payload
        return jsonify({"success": False}), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return jsonify({"success": False}), 400

    # Handle the event
    if event['type'] == 'invoice.paid':
        invoice = event['data']['object']
        print(f"Invoice {invoice['id']} was paid!")
        # You could add logic here to track which installment was paid
        
    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        print(f"Payment for invoice {invoice['id']} failed!")
        # You could add logic to handle failed payments

    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(port=4242, debug=True)
