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
    'django.contrib.sites', # Required by allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google', # For Google Sign-In
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

# Add REST Framework settings (if not already present)
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication', # Good for web clients
        # 'rest_framework_simplejwt.authentication.JWTAuthentication', # If using JWT
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly', # Or more specific permissions
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        # Add BrowsableAPIRenderer if you want the browsable API for development
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    # Throttling can be added later
    # 'DEFAULT_THROTTLE_CLASSES': [
    #     'rest_framework.throttling.AnonRateThrottle',
    #     'rest_framework.throttling.UserRateThrottle'
    # ],
    # 'DEFAULT_THROTTLE_RATES': {
    #     'anon': '100/day',
    #     'user': '1000/day'
    # }
}

# Allauth settings
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend', # Needed to login by username in Django admin
    'allauth.account.auth_backends.AuthenticationBackend', # Allauth specific authentication methods
)

SITE_ID = 1 # Django sites framework

ACCOUNT_EMAIL_VERIFICATION = 'optional' # Or 'mandatory' or 'none'
ACCOUNT_AUTHENTICATION_METHOD = 'email' # Or 'username' or 'username_email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
# ACCOUNT_USERNAME_REQUIRED = False # If using email as primary identifier
# LOGIN_REDIRECT_URL = '/' # Where to redirect after login (can be frontend URL)
# LOGOUT_REDIRECT_URL = '/' # Where to redirect after logout

# Provider specific settings for Google (placeholders for now)
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
        # You'll need to add your Google API client ID and secret here later
        # 'APP': {
        #     'client_id': 'YOUR_GOOGLE_CLIENT_ID',
        #     'secret': 'YOUR_GOOGLE_CLIENT_SECRET',
        #     'key': '' # Can be left empty
        # }
    }
}

# CORS settings (adjust origins as needed for development and production)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000", # Example for a React frontend
    "http://127.0.0.1:3000",
    "http://localhost:8080", # Example for Vue/other frontend dev server
    "http://127.0.0.1:8080",
    # Add your frontend production domain here
]
CORS_ALLOW_CREDENTIALS = True # Important for session-based auth / cookies

# CSRF settings - if your frontend and backend are on different subdomains/ports
# CSRF_TRUSTED_ORIGINS = [
#     "http://localhost:3000",
#     "http://127.0.0.1:3000",
# ]
# SESSION_COOKIE_SAMESITE = 'Lax' # Or 'None' if cross-site, requires Secure
# CSRF_COOKIE_SAMESITE = 'Lax'    # Or 'None' if cross-site, requires Secure
# SESSION_COOKIE_SECURE = False   # Set to True in production with HTTPS
# CSRF_COOKIE_SECURE = False      # Set to True in production with HTTPS

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

# backend/papri_project/settings.py (Allauth additions)
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',        # Needed to login by username in Django admin
    'allauth.account.auth_backends.AuthenticationBackend', # Allauth specific authentication methods
]

SITE_ID = 1 # Required by allauth

ACCOUNT_AUTHENTICATION_METHOD = 'email' # Or 'username_email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False # If email is primary identifier
ACCOUNT_EMAIL_VERIFICATION = 'optional' # Or 'mandatory'
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 5
ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = 300 # 5 minutes

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True, # Recommended for security
        'APP': { # Stored in Django Admin > Social Applications
            'client_id': GOOGLE_CLIENT_ID,
            'secret': GOOGLE_CLIENT_SECRET,
            'key': '' # Not typically used for Google
        }
    }
}
LOGIN_REDIRECT_URL = '/app/' # Redirect to papriapp.html after login
LOGOUT_REDIRECT_URL = '/'   # Redirect to landing page after logout
ACCOUNT_LOGOUT_ON_GET = True # For easier logout links

# Media files (user-uploaded content)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'media') # Creates a 'media' folder at the same level as 'backend' and 'frontend'

# ... rest of settings ...
