# Create and send an invoice

Create and send a Stripe-hosted invoice in minutes.

## Running the sample

1. Build the server

~~~
pip3 install -r requirements.txt
~~~

2. Run the server

~~~
export FLASK_APP=server.py
python3 -m flask run --port=4242
~~~


## Testing the webhook

Use the Stripe CLI to test your webhook locally. Download [the CLI](https://github.com/stripe/stripe-cli) and log in with your Stripe account. Alternatively, use a service like ngrok to make your local endpoint publicly accessible.

Set up event forwarding with the CLI to send all Stripe events in your 
 to your local webhook endpoint.

~~~
stripe listen --forward-to localhost:4242/webhook
~~~

Use the CLI to simulate specific events that test your webhook application logic by sending a POST request to your webhook endpoint with a mocked Stripe event object.

~~~
stripe trigger payment_intent.succeeded
~~~