# backend/api/urls.py
from django.urls import path, include # include is needed if you have nested URLs like for auth
from .views import (
    UserDetailView,
    auth_status_view, # Function-based view
    InitiateSearchView,
    SearchStatusView,
    SearchResultsView,
    VerifySignupCodeView,
    ActivateAccountWithCodeView
)

# If you plan to use DRF's router for ViewSets later, you would define it here.
# from rest_framework.routers import DefaultRouter
# router = DefaultRouter()
# router.register(r'videos', VideoViewSet, basename='video') # Example

app_name = 'api' # Namespace for the app's URLs

urlpatterns = [
    # --- User Authentication & Details ---
    path('auth/user/', UserDetailView.as_view(), name='user_detail'),
    path('auth/status/', auth_status_view, name='auth_status'),
    # Allauth URLs will be included in the project's urls.py: path('accounts/', include('allauth.urls')),

    # --- Search Task Endpoints ---
    path('search/initiate/', InitiateSearchView.as_view(), name='initiate_search'),
    path('search/status/<uuid:task_id>/', SearchStatusView.as_view(), name='search_status'), # Using <uuid:task_id>
    path('search/results/<uuid:task_id>/', SearchResultsView.as_view(), name='search_results'),

    # --- Signup Code & Account Activation ---
    path('auth/verify-code/', VerifySignupCodeView.as_view(), name='verify_signup_code'),
    path('auth/activate-account/', ActivateAccountWithCodeView.as_view(), name='activate_account_with_code'),

    # Example for ViewSet if you use it later:
    # path('', include(router.urls)),
]
