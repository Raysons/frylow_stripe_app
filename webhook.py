#! /usr/bin/env python3.6

import json
import os
import stripe
from flask import Flask, jsonify, request
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load Stripe keys securely
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
endpoint_secret = os.getenv('STRIPE_WEBHOOK_SECRET')

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    event = None
    payload = request.data

    try:
        event = json.loads(payload)
    except json.decoder.JSONDecodeError as e:
        print('⚠️  Webhook error while parsing basic request. ' + str(e))
        return jsonify(success=False)

    if endpoint_secret:
        sig_header = request.headers.get('stripe-signature')
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except stripe.error.SignatureVerificationError as e:
            print('⚠️  Webhook signature verification failed. ' + str(e))
            return jsonify(success=False)

    # Handle the event
    if event['type'] == 'invoice.paid':
        invoice = event['data']['object']
        print(f"✅ Invoice paid: {invoice['id']}")

    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        print(f"❌ Payment failed: {invoice['id']}")

    else:
        print('Unhandled event type {}'.format(event['type']))

    return jsonify(success=True)
