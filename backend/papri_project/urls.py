# backend/papri_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from api.views import papri_app_view # Assuming you created this view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')), # Django Allauth URLs
    path('api/', include('api.urls', namespace='api')),
    # path('payments/', include('payments.urls', namespace='payments')), # Uncomment if using payments app

    # Serve papriapp.html - this should be protected by login
    path('app/', papri_app_view, name='papri_app_main'), 
    
    # Optional: A simple root redirect to the app if authenticated, or to landing page / login
    # path('', some_root_view_that_redirects, name='root_home'), 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Static files are typically served by runserver in DEBUG automatically via STATICFILES_DIRS
