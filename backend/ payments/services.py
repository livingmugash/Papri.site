# backend/payments/services.py
import stripe
import os
# Import Mpesa and PayPal SDKs/libraries as needed

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

class StripeService:
    def create_payment_intent(self, amount, currency, email, payment_method_id):
        try:
            # Check if customer exists, create if not
            customers = stripe.Customer.list(email=email, limit=1)
            if customers.data:
                customer_id = customers.data[0].id
            else:
                customer = stripe.Customer.create(email=email, payment_method=payment_method_id)
                customer_id = customer.id

            intent_params = {
                'amount': int(amount), # Amount in cents
                'currency': currency.lower(),
                'customer': customer_id,
                'payment_method': payment_method_id,
                'confirmation_method': 'manual', # We will confirm it
                'confirm': True, # Attempt to confirm immediately
                'description': f'Papri Pro Plan Subscription for {email}',
                'receipt_email': email,
                 # 'off_session': True, # If you plan to charge later without user being present
                 'payment_method_types': ['card'],
                 'use_stripe_sdk': True, # For SCA compliance
            }
            intent = stripe.PaymentIntent.create(**intent_params)

            return self._handle_payment_intent_response(intent)

        except stripe.error.CardError as e:
            return {'error': e.error.message, 'requires_action': False, 'success': False, 'client_secret': None}
        except Exception as e:
            return {'error': str(e), 'requires_action': False, 'success': False, 'client_secret': None}

    def _handle_payment_intent_response(self, intent):
        if intent.status == 'requires_action' or intent.status == 'requires_source_action':
            return {'error': None, 'requires_action': True, 'success': False, 'client_secret': intent.client_secret}
        elif intent.status == 'succeeded':
             # TODO: Provision access to Papri Pro features here
             # Generate and store signup code, link to user, send email
            return {'error': None, 'requires_action': False, 'success': True, 'client_secret': intent.client_secret}
        else: # requires_payment_method, requires_capture, processing, canceled
            return {'error': 'Payment failed or requires different action.', 'requires_action': False, 'success': False, 'client_secret': intent.client_secret }


class MpesaService:
    def initiate_stk_push(self, phone_number, amount, account_reference):
        # TODO: Implement Mpesa STK Push logic using your Mpesa API keys
        # This involves getting an access token, then making the STK push request
        # to Safaricom API.
        # You'll need a callback URL configured in your Mpesa developer portal
        # that Safaricom will call with the transaction status.
        print(f"Simulating Mpesa STK Push for {phone_number}, Amount: {amount}, Ref: {account_reference}")
        # In a real scenario, this would return a unique transaction ID to poll or await callback
        return {'success': True, 'message': 'STK Push initiated. Check your phone.'}

class PaypalService:
    def create_order(self, amount, currency):
        # TODO: Implement PayPal order creation using PayPal REST SDK
        print(f"Simulating PayPal order creation for {amount} {currency}")
        # This would return an approval_url or order_id for frontend to use
        return {'success': True, 'approval_url': 'https://www.paypal.com/checkoutnow?token=simulated_token'}

# ... and so on for other payment methods
