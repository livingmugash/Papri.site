# backend/papri_project/settings.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR should point to the 'backend' directory
BASE_DIR = Path(__file__).resolve().parent.parent 
PROJECT_ROOT_DIR = BASE_DIR.parent # This should be the 'papri' main directory

load_dotenv(os.path.join(BASE_DIR, '.env')) # Load .env from backend dir

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-fallback-key-for-dev')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites', # Required by allauth

    'rest_framework',
    'corsheaders',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'django_celery_results',
    'django_celery_beat',

    'api.apps.ApiConfig', # Use AppConfig
    'ai_agents.apps.AiAgentsConfig', # If making ai_agents a Django app for models/management commands
    # 'payments.apps.PaymentsConfig', # If payments is a separate app
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # For serving static files in prod if not using S3 directly
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware', # allauth middleware
]

ROOT_URLCONF = 'papri_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(PROJECT_ROOT_DIR, 'frontend', 'templates')], # Corrected path
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.static', # For {% static %} tag
                'django.template.context_processors.media', # For media URLs
            ],
        },
    },
]

WSGI_APPLICATION = 'papri_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.mysql'),
        'NAME': os.getenv('DB_NAME', 'papri_db_dev'),
        'USER': os.getenv('DB_USER', 'papri_user_dev'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'papri_pass_dev'),
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {'charset': 'utf8mb4'},
    }
}

# AUTHENTICATION
AUTHENTICATION_BACKENDS = ('django.contrib.auth.backends.ModelBackend', 'allauth.account.auth_backends.AuthenticationBackend',)
SITE_ID = 1 # Required by allauth
LOGIN_URL = '/accounts/login/' # allauth's login page
LOGIN_REDIRECT_URL = '/app/' # Redirect here after successful login
LOGOUT_REDIRECT_URL = '/'    # Redirect here after logout

ACCOUNT_EMAIL_VERIFICATION = os.getenv('ACCOUNT_EMAIL_VERIFICATION', 'optional')
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False # Use email as the username effectively
ACCOUNT_ADAPTER = 'allauth.account.adapter.DefaultAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'allauth.socialaccount.adapter.DefaultSocialAccountAdapter'
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'APP': { # Client ID and Secret for Google OAuth
            'client_id': os.getenv('GOOGLE_CLIENT_ID'),
            'secret': os.getenv('GOOGLE_CLIENT_SECRET'),
            'key': '' # Not used by Google provider
        }
    }
}

# Password validation (Django defaults are good)
# ...

LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.getenv('TIME_ZONE', 'Africa/Nairobi')
USE_I18N = True
USE_L10N = True # Localized formatting
USE_TZ = True


# STATIC & MEDIA FILES
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(PROJECT_ROOT_DIR, 'frontend', 'static')]
# STATIC_ROOT = os.path.join(PROJECT_ROOT_DIR, 'staticfiles_collected') # For production 'collectstatic'
# MEDIA_URL = '/media/'
# MEDIA_ROOT = os.path.join(PROJECT_ROOT_DIR, 'mediafiles') # For user uploads and temp files
# Ensure MEDIA_ROOT has write permissions for Celery workers (e.g., for temp_video_downloads)
MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles_storage') # Store media within backend for simplicity in dev
MEDIA_URL = '/mediafiles_storage/'


# Simplified static files for production with WhiteNoise
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST FRAMEWORK
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        # 'rest_framework_simplejwt.authentication.JWTAuthentication', # If using JWT later
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer' if DEBUG else 'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 12, # Default page size for DRF views
    'PAGE_SIZE_QUERY_PARAM': 'page_size', # Allow client to set page size
    'MAX_PAGE_SIZE': 100
}

# CELERY
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'django-db') # Using django-celery-results for storing results in Django DB
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_RESULT_EXTENDED = True # Store more task metadata
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler' # For periodic tasks

# CORS
CORS_ALLOW_CREDENTIALS = True
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True # For local development ease
else:
    CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:8000,http://127.0.0.1:8000').split(',')
    # Add your production frontend domain(s) here

# LOGGING (More detailed for V1)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module}:{lineno} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file_django': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/django.log'),
            'maxBytes': 1024*1024*5, # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'file_papri': { # For our app specific logs
            'level': 'DEBUG', # Capture more detail from our app
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/papri_app.log'),
            'maxBytes': 1024*1024*5, # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': { # Catch-all logger
        'handlers': ['console', 'file_django'],
        'level': 'WARNING', # Root logger level
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file_django'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False, # Don't pass to root
        },
        'api': { # Logger for your 'api' app
            'handlers': ['console', 'file_papri'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'ai_agents': { # Logger for your 'ai_agents'
            'handlers': ['console', 'file_papri'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file_papri'], # Send Celery logs to papri_app.log too
            'level': 'INFO',
            'propagate': False,
        },
        'qdrant_client': { # For Qdrant client library if it uses logging
             'handlers': ['console', 'file_papri'],
             'level': 'INFO',
             'propagate': False,
        },
        'PIL.Image': { # Pillow image library logging
            'handlers': ['console', 'file_papri'],
            'level': 'INFO',
            'propagate': False,
        }
    },
}
# Ensure logs directory exists
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)


# PAPRI SPECIFIC AI & SCRAPER SETTINGS
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
VIMEO_ACCESS_TOKEN = os.getenv('VIMEO_ACCESS_TOKEN')

QDRANT_URL = os.getenv('QDRANT_URL', 'http://localhost:6334')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY', None)
QDRANT_COLLECTION_TRANSCRIPTS = os.getenv('QDRANT_COLLECTION_TRANSCRIPTS', "papri_transcript_embeddings_v1_1") # Versioned
QDRANT_COLLECTION_VISUAL = os.getenv('QDRANT_COLLECTION_VISUAL', "papri_visual_embeddings_v1_1") # Versioned
SENTENCE_TRANSFORMER_MODEL = os.getenv('SENTENCE_TRANSFORMER_MODEL', 'all-MiniLM-L6-v2')
VISUAL_CNN_MODEL_NAME = os.getenv('VISUAL_CNN_MODEL_NAME',"ResNet50")
FORCE_REINDEX_VISUAL = os.getenv('FORCE_REINDEX_VISUAL', 'False') == 'True'

MAX_API_RESULTS_PER_SOURCE = int(os.getenv('MAX_API_RESULTS_PER_SOURCE', 7))
MAX_SCRAPED_ITEMS_PER_SOURCE = int(os.getenv('MAX_SCRAPED_ITEMS_PER_SOURCE', 5))
SCRAPE_INTER_PLATFORM_DELAY_SECONDS = int(os.getenv('SCRAPE_INTER_PLATFORM_DELAY_SECONDS', 2))

# Load SCRAPEABLE_PLATFORMS from a JSON string in .env or a separate config file for flexibility
# For example, in .env:
# SCRAPEABLE_PLATFORMS_JSON='[{"name": "PeerTube_Tilvids_Test", "spider_name": "peertube", ...}]'
try:
    SCRAPEABLE_PLATFORMS_CONFIG = json.loads(os.getenv('SCRAPEABLE_PLATFORMS_JSON', '[]'))
except json.JSONDecodeError:
    SCRAPEABLE_PLATFORMS_CONFIG = []
if not SCRAPEABLE_PLATFORMS_CONFIG and DEBUG: # Add a default for dev if not in .env
    SCRAPEABLE_PLATFORMS_CONFIG.append({
        'name': 'PeerTube_Tilvids_Dev', 'spider_name': 'peertube', 
        'base_url': 'https://tilvids.com', # EXAMPLE - REPLACE WITH YOUR TARGET
        'search_path_template': '/search/videos?search={query}&searchTarget=local', 
        'default_listing_url': 'https://tilvids.com/videos/recently-added',
        'is_active': True
    })

# Email settings for Django Allauth (e.g., for password reset)
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend') # Default to console for dev
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'webmaster@localhost')

# Define where Celery Beat schedule is stored if using DB scheduler
# CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
