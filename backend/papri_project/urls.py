# backend/payments/urls.py
from django.urls import path
from .views import CreatePaymentIntentView, MpesaSTKPushView, MpesaCallbackView

urlpatterns = [
    path('create-payment-intent/', CreatePaymentIntentView.as_view(), name='create_payment_intent'),
    path('mpesa-stk-push/', MpesaSTKPushView.as_view(), name='mpesa_stk_push'),
    path('mpesa-callback/', MpesaCallbackView.as_view(), name='mpesa_callback'),
    # Add other payment URLs here
]

# backend/papri_project/urls.py (add this)
# ... other imports
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')), # For Google Sign-In
    path('api/', include('api.urls')),         # For your main app APIs
    path('payments/', include('payments.urls')), # For payment APIs
    # TODO: Add a catch-all for frontend routing if using a SPA framework for papriapp.html
]
