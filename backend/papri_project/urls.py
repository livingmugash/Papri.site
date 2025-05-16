# backend/papri_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView # For serving papriapp.html directly

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')), # Allauth URLs
    path('api/', include('api.urls', namespace='api')), # Your main API
    # path('payments/', include('payments.urls', namespace='payments')), # If payments app is separate

    # Serve papriapp.html as the main app view (requires login via allauth)
    # This assumes papriapp.html is in your root templates directory defined in settings.TEMPLATES
    path('app/', TemplateView.as_view(template_name='papriapp.html'), name='papri_app_main'),
    # You might want a view that ensures login before rendering TemplateView.
    # For now, allauth's LOGIN_REDIRECT_URL to /app/ will work after login.
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Static files are usually served by runserver in DEBUG
