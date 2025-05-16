# backend/papri_project/settings.py
import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')) # Load .env from backend dir

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Should point to 'backend'

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'your-default-secret-key-in-dev-only')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    'rest_framework',
    'corsheaders',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'django_celery_results', # Optional: if using Django DB for Celery results
    'django_celery_beat',   # Optional: for scheduled tasks

    'api',
    'ai_agents', # For Scrapy settings if structured as app
    # 'payments', # If you have the payments app
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'papri_project.urls'
TEMPLATES = [ # ... (Ensure frontend/templates is in DIRS if Django serves it) ...
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(os.path.dirname(BASE_DIR), 'frontend', 'templates')], # Points to ../frontend/templates
        'APP_DIRS': True,
        # ... (options) ...
    },
]
WSGI_APPLICATION = 'papri_project.wsgi.application'

DATABASES = { # ... (MySQL config from .env) ...
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'), 'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'), 'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'), 'OPTIONS': {'charset': 'utf8mb4'},
    }
}

# AUTH & ALLAUTH
AUTHENTICATION_BACKENDS = ('django.contrib.auth.backends.ModelBackend', 'allauth.account.auth_backends.AuthenticationBackend',)
SITE_ID = 1
ACCOUNT_EMAIL_VERIFICATION = os.getenv('ACCOUNT_EMAIL_VERIFICATION', 'optional')
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
LOGIN_REDIRECT_URL = '/app/' # To papriapp.html served by Django
LOGOUT_REDIRECT_URL = '/'
SOCIALACCOUNT_PROVIDERS = {'google': {'SCOPE': ['profile', 'email'], 'AUTH_PARAMS': {'access_type': 'online'}, 'OAUTH_PKCE_ENABLED': True}}

# REST FRAMEWORK
REST_FRAMEWORK = { # ... (pagination, auth, permissions as in Step 37) ...
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination', 'PAGE_SIZE': 10,
    'DEFAULT_AUTHENTICATION_CLASSES': ('rest_framework.authentication.SessionAuthentication',),
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticatedOrReadOnly',)
}

# CELERY (ensure broker URL is for production if not Redis on localhost)
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'django-db') # Using django-celery-results
CELERY_ACCEPT_CONTENT = ['json']; CELERY_TASK_SERIALIZER = 'json'; CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Africa/Nairobi'; CELERY_TASK_TRACK_STARTED = True; CELERY_RESULT_EXTENDED = True
# CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler' # For scheduled tasks

# CORS
CORS_ALLOW_ALL_ORIGINS = DEBUG # For dev
# CORS_ALLOWED_ORIGINS = [os.getenv('FRONTEND_URL', 'http://localhost:3000')] # For prod
CORS_ALLOW_CREDENTIALS = True

# FILE UPLOADS & STATIC FILES
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(os.path.dirname(BASE_DIR), 'frontend', 'static')] # frontend/static
# STATIC_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'staticfiles_collected') # For collectstatic in prod
MEDIA_URL = '/media/' # For user uploads like query images, temp downloads
MEDIA_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'media')

# LOGGING (Basic example, expand for production)
LOGGING = {
    'version': 1, 'disable_existing_loggers': False,
    'formatters': {'verbose': {'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}','style': '{',}},
    'handlers': {'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'}},
    'root': {'handlers': ['console'], 'level': 'INFO' if not DEBUG else 'DEBUG'},
    'loggers': {
        'django': {'handlers': ['console'], 'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'), 'propagate': False},
        'api': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': True},
        'ai_agents': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': True},
        'celery': {'handlers': ['console'], 'level': 'INFO', 'propagate': True},
    }
}

# PAPRI SPECIFIC SETTINGS
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
VIMEO_ACCESS_TOKEN = os.getenv('VIMEO_ACCESS_TOKEN')
# DAILYMOTION keys are URLs, used directly if needed

QDRANT_URL = os.getenv('QDRANT_URL', 'http://localhost:6334')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY', None)
QDRANT_COLLECTION_TRANSCRIPTS = "papri_transcript_embeddings_v1"
QDRANT_COLLECTION_VISUAL = "papri_visual_embeddings_v1"
SENTENCE_TRANSFORMER_MODEL = 'all-MiniLM-L6-v2'
VISUAL_CNN_MODEL_NAME = "ResNet50" # Or "EfficientNetV2S"
# FORCE_REINDEX_VISUAL = False # Add to .env if you want to control this

MAX_API_RESULTS_PER_SOURCE = 7
MAX_SCRAPED_ITEMS_PER_SOURCE = 5
SCRAPE_INTER_PLATFORM_DELAY_SECONDS = 2

# Add your SCRAPEABLE_PLATFORMS config here or load from a JSON/YAML file
# EXAMPLE:
SCRAPEABLE_PLATFORMS_CONFIG = [
    {
        'name': 'PeerTube_Tilvids_Test', 'spider_name': 'peertube', 
        'base_url': 'https://tilvids.com', 
        'search_path_template': '/search/videos?search={query}&searchTarget=local', 
        'default_listing_url': 'https://tilvids.com/videos/recently-added',
        'is_active': True # Add a flag to easily enable/disable
    }
]
