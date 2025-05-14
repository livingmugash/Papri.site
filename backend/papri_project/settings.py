# backend/papri_project/settings.py (Partial)
import os
from dotenv import load_dotenv
load_dotenv() # Load environment variables from .env file

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'your-default-secret-key')
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*'] # Adjust for production

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders', # For allowing frontend requests
    'api',
    'ai_agents',
    'payments',# Add social auth apps if using django-allauth or similar
] 


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware', # CORS
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'papri_project.urls'

TEMPLATES = [ # Ensure your frontend templates directory is added if Django serves them
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
],
},
},
]

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}

# Vector Database (Conceptual - actual connection will be in AI agent code)
# For Milvus, connection details would be managed by the Milvus client
VECTOR_DB_HOST = os.getenv('VECTOR_DB_HOST', 'localhost')
VECTOR_DB_PORT = os.getenv('VECTOR_DB_PORT', '19530')


# Password validation
# ...

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi' # EAT
USE_I18N = True
USE_L10N = True # For localized formatting of dates, numbers
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend', 'static'),
]
# For production, you'd use STATIC_ROOT and collectstatic

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS Settings (Adjust for your frontend URL in production)
CORS_ALLOW_ALL_ORIGINS = DEBUG # For development
# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:3000", # If your frontend runs on a different port
#     "https_your_production_domain.com",
# ]

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        # Add token authentication if needed for mobile/third-party APIs
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    )
}

# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# API Keys
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY') # AIzaSyDSswXFMJcD9i4jOmixzBD2vx-wmFafDNs
VIMEO_CLIENT_ID = os.getenv('VIMEO_CLIENT_ID') # 78650a6b8526e7b7445ada00753599ccfdd3119f
VIMEO_CLIENT_SECRET = os.getenv('VIMEO_CLIENT_SECRET')
VIMEO_ACCESS_TOKEN = os.getenv('VIMEO_ACCESS_TOKEN') # You'll likely need to obtain this via OAuth flow first
# DAILYMOTION_PUBLIC_KEY = os.getenv('DAILYMOTION_PUBLIC_KEY') # URL given, not key
# DAILYMOTION_PRIVATE_KEY = os.getenv('DAILYMOTION_PRIVATE_KEY') # URL given, not key

STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
MPESA_CONSUMER_KEY = os.getenv('MPESA_CONSUMER_KEY')
MPESA_CONSUMER_SECRET = os.getenv('MPESA_CONSUMER_SECRET')
PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
PAYPAL_SECRET_KEY = os.getenv('PAYPAL_SECRET_KEY')

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID') # For Google Sign-In
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

# AWS Configuration
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'eu-north-1')
# Configure S3 for static/media files if needed
# AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')

# Geolocation Currency Display (example rates, fetch dynamically in production)
CURRENCY_RATES = {
    'USD': 1.0,
    'KES': 130.0, # Example rate: 1 USD = 130 KES
    'EUR': 0.92,
    # Add more as needed
}
DEFAULT_CURRENCY = 'USD'
```
