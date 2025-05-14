# backend/payments/views.py
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .services import StripeService, MpesaService, PaypalService
import random
import string
from django.core.mail import send_mail
from django.conf import settings
# from api.models import SignupCode # You'll need a model to store these

# Placeholder for SignupCode model - create this in api/models.py
# class SignupCode(models.Model):
#     email = models.EmailField(unique=True)
#     code = models.CharField(max_length=6, unique=True)
#     is_used = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)

def generate_signup_code():
    return ''.join(random.choices(string.digits, k=6))

class CreatePaymentIntentView(APIView):
    permission_classes = [permissions.AllowAny] # Or IsAuthenticated if user must be logged in first

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        payment_method_id = request.data.get('payment_method_id')
        amount = request.data.get('amount') # Expected in cents
        currency = request.data.get('currency', 'usd')

        if not all([email, payment_method_id, amount]):
            return Response({'error': 'Missing required fields.'}, status=status.HTTP_400_BAD_REQUEST)

        stripe_service = StripeService()
        result = stripe_service.create_payment_intent(amount, currency, email, payment_method_id)

        if result.get('success'):
            # Generate and send signup code
            signup_code_value = generate_signup_code()
            # TODO: Save signup_code_value to SignupCode model associated with email
            # Example: SignupCode.objects.create(email=email, code=signup_code_value)
            try:
                send_mail(
                    'Your Papri Signup Code',
                    f'Thank you for subscribing to Papri! Your signup code is: {signup_code_value}\n\nPlease use this code to create your account.',
                    settings.DEFAULT_FROM_EMAIL, # Configure in settings.py
                    [email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error sending signup email: {e}") # Log this error

            return Response({
                'success': True,
                'client_secret': result.get('client_secret'), # For frontend if requires_action
                'signup_code': signup_code_value # Send code to frontend
            }, status=status.HTTP_200_OK)
        elif result.get('requires_action'):
             return Response({
                'requires_action': True,
                'client_secret': result.get('client_secret')
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': result.get('error', 'Payment failed')}, status=status.HTTP_400_BAD_REQUEST)

class MpesaSTKPushView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request, *args, **kwargs):
        phone_number = request.data.get('mpesa_phone')
        email = request.data.get('email') # For account reference and sending code
        amount = request.data.get('amount') # This should be KES amount for Mpesa

        if not all([phone_number, email, amount]):
             return Response({'error': 'Missing required Mpesa fields.'}, status=status.HTTP_400_BAD_REQUEST)

        # TODO: Convert amount to KES if not already (use a fixed rate for now or get from frontend)
        # For now, assume 'amount' is already in KES from frontend logic
        kes_amount = amount # Expected in KES base unit (e.g., 600 for 600 KES)

        account_ref = f"PAPRI{email.split('@')[0]}"[:10] # Example reference
        mpesa_service = MpesaService()
        result = mpesa_service.initiate_stk_push(phone_number, kes_amount, account_ref)

        if result.get('success'):
            # STK push initiated. Payment is not confirmed yet.
            # Frontend will show "waiting" message.
            # Backend needs a callback from Mpesa to confirm.
            # For demo, we can simulate success and send code.
            signup_code_value = generate_signup_code()
            # TODO: Save signup_code_value, but mark as pending Mpesa confirmation
            # Send email with code and mention it's pending Mpesa
            return Response({
                'success': True,
                'message': result.get('message'),
                'signup_code': signup_code_value # For demo purposes, real flow would wait for callback
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': result.get('error', 'Mpesa STK push failed')}, status=status.HTTP_400_BAD_REQUEST)

class MpesaCallbackView(APIView):
    permission_classes = [permissions.AllowAny] # Mpesa will call this, no auth
    def post(self, request, *args, **kwargs):
        # This is where Safaricom Mpesa API sends the transaction status
        mpesa_data = request.data
        print("Mpesa Callback Received:", mpesa_data)
        # TODO: Process the callback data
        # - Validate the source of the request (from Safaricom)
        # - Check the ResultCode (0 means success)
        # - If successful, find the pending transaction (e.g., by CheckoutRequestID)
        # - Mark the payment as complete in your database
        # - Provision access/send confirmed signup code (if not sent before)
        # - Potentially use Django Channels or SSE to notify frontend in real-time
        return Response({'ResultCode': 0, 'ResultDesc': 'Accepted'}, status=status.HTTP_200_OK)


# Add similar views for PayPal (e.g., create_paypal_order, capture_paypal_order)
# Add view for Flutterwave (initiate and handle callback)
# Add view for Bank Transfer (user confirms, backend admin verifies)
