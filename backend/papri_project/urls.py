# backend/papri_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings # For serving media files during development
from django.conf.urls.static import static # For serving media files during development

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication URLs (django-allauth)
    # This provides endpoints like /accounts/google/login/, /accounts/login/, /accounts/logout/, etc.
    path('accounts/', include('allauth.urls')),

    # Your Papri API endpoints
    path('api/', include('api.urls', namespace='api')), # Include your app's URLs

    # Your Payments API endpoints (if you created payments/urls.py separately)
    path('payments/', include('payments.urls', namespace='payments')), # Assuming you created payments app

    # TODO: Add frontend serving path if Django is serving the main papriapp.html
    # e.g., path('app/', TemplateView.as_view(template_name='papriapp.html'), name='app_home'),
]

# Serve media files during development (e.g., uploaded query images)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) # Usually handled by runserver in DEBUG
