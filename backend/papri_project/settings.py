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
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000", # If your frontend runs on a different port
    "https_your_production_domain.com",
]

# Add REST Framework settings (if not already present)
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer', # If you want the browsable API
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,  # Default number of items per page
    'PAGE_SIZE_QUERY_PARAM': 'page_size',
    'MAX_PAGE_SIZE': 100 
    # Throttling can be added later
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day'
    }
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
ACCOUNT_USERNAME_REQUIRED = False # If using email as primary identifier
LOGIN_REDIRECT_URL = 'papriapp.html' # Where to redirect after login (can be frontend URL)
LOGOUT_REDIRECT_URL = 'index.html' # Where to redirect after logout

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
        'APP': {
            'client_id': 'YOUR_GOOGLE_CLIENT_ID',
            'secret': 'YOUR_GOOGLE_CLIENT_SECRET',
            'key': '' # Can be left empty
        }
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
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
SESSION_COOKIE_SAMESITE = 'Lax' # Or 'None' if cross-site, requires Secure
CSRF_COOKIE_SAMESITE = 'Lax'    # Or 'None' if cross-site, requires Secure
SESSION_COOKIE_SECURE = False   # Set to True in production with HTTPS
CSRF_COOKIE_SECURE = False      # Set to True in production with HTTPS

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
DAILYMOTION_PUBLIC_KEY = os.getenv('DAILYMOTION_PUBLIC_KEY') # URL given, not key
DAILYMOTION_PRIVATE_KEY = os.getenv('DAILYMOTION_PRIVATE_KEY') # URL given, not key

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
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')

# Geolocation Currency Display (example rates, fetch dynamically in production)

CURRENCY_RATES = {
    'USD': 1.0,      # United States Dollar
    'EUR': 0.92,     # Euro (used by many European countries)
    'JPY': 155.0,    # Japanese Yen
    'GBP': 0.79,     # British Pound Sterling
    'AUD': 1.50,     # Australian Dollar
    'CAD': 1.37,     # Canadian Dollar
    'CHF': 0.90,     # Swiss Franc
    'CNY': 7.22,     # Chinese Yuan Renminbi
    'SEK': 10.85,    # Swedish Krona
    'NZD': 1.65,     # New Zealand Dollar
    'MXN': 16.80,    # Mexican Peso
    'SGD': 1.35,     # Singapore Dollar
    'HKD': 7.81,     # Hong Kong Dollar
    'NOK': 10.80,    # Norwegian Krone
    'KRW': 1350.0,   # South Korean Won
    'TRY': 32.20,    # Turkish Lira
    'RUB': 91.50,    # Russian Ruble
    'INR': 83.50,    # Indian Rupee
    'BRL': 5.15,     # Brazilian Real
    'ZAR': 18.30,    # South African Rand
    'KES': 130.0,    # Kenyan Shilling (as you had)
    'AED': 3.67,     # United Arab Emirates Dirham
    'AFN': 72.00,    # Afghan Afghani
    'ALL': 93.00,    # Albanian Lek
    'AMD': 388.00,   # Armenian Dram
    'ANG': 1.79,     # Netherlands Antillean Guilder
    'AOA': 830.00,   # Angolan Kwanza
    'ARS': 880.00,   # Argentine Peso
    'AWG': 1.79,     # Aruban Florin
    'AZN': 1.70,     # Azerbaijani Manat
    'BAM': 1.80,     # Bosnia-Herzegovina Convertible Mark
    'BBD': 2.00,     # Barbadian Dollar
    'BDT': 117.00,   # Bangladeshi Taka
    'BGN': 1.80,     # Bulgarian Lev
    'BHD': 0.38,     # Bahraini Dinar
    'BIF': 2850.00,  # Burundian Franc
    'BMD': 1.00,     # Bermudan Dollar
    'BND': 1.35,     # Brunei Dollar
    'BOB': 6.90,     # Bolivian Boliviano
    'BSD': 1.00,     # Bahamian Dollar
    'BTN': 83.50,    # Bhutanese Ngultrum
    'BWP': 13.70,    # Botswanan Pula
    'BYN': 3.25,     # Belarusian Ruble
    'BZD': 2.00,     # Belize Dollar
    'CDF': 2780.00,  # Congolese Franc
    'CLP': 925.00,   # Chilean Peso
    'COP': 3900.00,  # Colombian Peso
    'CRC': 500.00,   # Costa Rican Colón
    'CUP': 24.00,    # Cuban Peso
    'CVE': 102.00,   # Cape Verdean Escudo
    'CZK': 23.00,    # Czech Republic Koruna
    'DJF': 177.00,   # Djiboutian Franc
    'DKK': 6.85,     # Danish Krone
    'DOP': 58.00,    # Dominican Peso
    'DZD': 134.00,   # Algerian Dinar
    'EGP': 47.00,    # Egyptian Pound
    'ERN': 15.00,    # Eritrean Nakfa
    'ETB': 57.00,    # Ethiopian Birr
    'FJD': 2.25,     # Fijian Dollar
    'FKP': 0.79,     # Falkland Islands Pound
    'FOK': 6.85,     # Faroese Króna (pegged to DKK)
    'GEL': 2.68,     # Georgian Lari
    'GGP': 0.79,     # Guernsey Pound (pegged to GBP)
    'GHS': 14.50,    # Ghanaian Cedi
    'GIP': 0.79,     # Gibraltar Pound (pegged to GBP)
    'GMD': 68.00,    # Gambian Dalasi
    'GNF': 8600.00,  # Guinean Franc
    'GTQ': 7.75,     # Guatemalan Quetzal
    'GYD': 209.00,   # Guyanaese Dollar
    'HNL': 24.70,    # Honduran Lempira
    'HRK': 0.92,     # Croatian Kuna (Note: Croatia adopted EUR in 2023, but some systems might still use HRK for historical data)
    'HTG': 132.00,   # Haitian Gourde
    'HUF': 360.00,   # Hungarian Forint
    'IDR': 16000.00, # Indonesian Rupiah
    'ILS': 3.70,     # Israeli New Shekel
    'IMP': 0.79,     # Isle of Man Pound (pegged to GBP)
    'IQD': 1310.00,  # Iraqi Dinar
    'IRR': 42000.00, # Iranian Rial (official rate, market rate differs significantly)
    'ISK': 138.00,   # Icelandic Króna
    'JEP': 0.79,     # Jersey Pound (pegged to GBP)
    'JMD': 155.00,   # Jamaican Dollar
    'JOD': 0.71,     # Jordanian Dinar
    'KGS': 88.00,    # Kyrgystani Som
    'KHR': 4080.00,  # Cambodian Riel
    'KID': 1.50,     # Kiribati Dollar (pegged to AUD)
    'KMF': 450.00,   # Comorian Franc
    'KWD': 0.31,     # Kuwaiti Dinar
    'KYD': 0.83,     # Cayman Islands Dollar
    'KZT': 440.00,   # Kazakhstani Tenge
    'LAK': 20700.00, # Laotian Kip
    'LBP': 89500.00, # Lebanese Pound (official rate, market rate differs significantly)
    'LKR': 300.00,   # Sri Lankan Rupee
    'LRD': 190.00,   # Liberian Dollar
    'LSL': 18.30,    # Lesotho Loti (pegged to ZAR)
    'LYD': 4.85,     # Libyan Dinar
    'MAD': 10.00,    # Moroccan Dirham
    'MDL': 17.70,    # Moldovan Leu
    'MGA': 4350.00,  # Malagasy Ariary
    'MKD': 56.50,    # Macedonian Denar
    'MMK': 2100.00,  # Myanma Kyat
    'MNT': 3400.00,  # Mongolian Tugrik
    'MOP': 8.05,     # Macanese Pataca
    'MRU': 39.50,    # Mauritanian Ouguiya
    'MUR': 46.00,    # Mauritian Rupee
    'MVR': 15.40,    # Maldivian Rufiyaa
    'MWK': 1730.00,  # Malawian Kwacha
    'MYR': 4.70,     # Malaysian Ringgit
    'MZN': 63.80,    # Mozambican Metical
    'NAD': 18.30,    # Namibian Dollar (pegged to ZAR)
    'NGN': 1480.00,  # Nigerian Naira
    'NIO': 36.80,    # Nicaraguan Córdoba
    'NPR': 133.50,   # Nepalese Rupee
    'OMR': 0.38,     # Omani Rial
    'PAB': 1.00,     # Panamanian Balboa (pegged to USD)
    'PEN': 3.70,     # Peruvian Nuevo Sol
    'PGK': 3.85,     # Papua New Guinean Kina
    'PHP': 57.50,    # Philippine Peso
    'PKR': 278.00,   # Pakistani Rupee
    'PLN': 3.95,     # Polish Zloty
    'PYG': 7250.00,  # Paraguayan Guarani
    'QAR': 3.64,     # Qatari Rial
    'RON': 4.60,     # Romanian Leu
    'RSD': 108.00,   # Serbian Dinar
    'RWF': 1300.00,  # Rwandan Franc
    'SAR': 3.75,     # Saudi Riyal
    'SBD': 8.30,     # Solomon Islands Dollar
    'SCR': 13.50,    # Seychellois Rupee
    'SDG': 480.00,   # Sudanese Pound
    'SHP': 0.79,     # Saint Helena Pound
    'SLE': 22.50,    # Sierra Leonean Leone (new Leone)
    'SLL': 22500.00, # Sierra Leonean Leone (old Leone - might still be seen)
    'SOS': 570.00,   # Somali Shilling
    'SRD': 33.00,    # Surinamese Dollar
    'SSP': 1300.00,  # South Sudanese Pound
    'STN': 22.00,    # São Tomé and Príncipe Dobra
    'SYP': 13000.00, # Syrian Pound (official rate, market rate differs significantly)
    'SZL': 18.30,    # Swazi Lilangeni (pegged to ZAR)
    'THB': 36.50,    # Thai Baht
    'TJS': 10.90,    # Tajikistani Somoni
    'TMT': 3.50,     # Turkmenistani Manat
    'TND': 3.10,     # Tunisian Dinar
    'TOP': 2.30,     # Tongan Paʻanga
    'TTD': 6.75,     # Trinidad and Tobago Dollar
    'TVD': 1.50,     # Tuvaluan Dollar (pegged to AUD)
    'TWD': 32.20,    # New Taiwan Dollar
    'TZS': 2600.00,  # Tanzanian Shilling
    'UAH': 39.50,    # Ukrainian Hryvnia
    'UGX': 3750.00,  # Ugandan Shilling
    'UYU': 38.50,    # Uruguayan Peso
    'UZS': 12700.00, # Uzbekistan Som
    'VES': 36.50,    # Venezuelan Bolívar Soberano
    'VND': 25400.00, # Vietnamese Dong
    'VUV': 118.00,   # Vanuatu Vatu
    'WST': 2.75,     # Samoan Tala
    'XAF': 605.00,   # Central African CFA Franc
    'XCD': 2.70,     # East Caribbean Dollar
    'XOF': 605.00,   # West African CFA Franc
    'XPF': 110.00,   # CFP Franc
    'YER': 250.00,   # Yemeni Rial
    'ZMW': 27.00,    # Zambian Kwacha
    'ZWL': 13.50,    # Zimbabwean Dollar (new - ZiG, older ZWL values were much higher)
    # Add more as needed or refine based on specific regional focus
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

# Celery Configuration Options
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0') # To store task results/status
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE # Use your Django project's timezone
CELERY_TASK_TRACK_STARTED = True # To get 'STARTED' state
CELERY_TASK_SEND_SENT_EVENT = True # To send task-sent events
CELERY_RESULT_EXTENDED = True # To store more metadata about tasks

# Optional: if you want Celery Beat for scheduled tasks later
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
```

*Make sure you have Redis (or another broker like RabbitMQ) installed and running. For Redis on Ubuntu: `sudo apt install redis-server`, then `sudo systemctl start redis-server`, `sudo systemctl enable redis-server`.*
*Install Celery and Redis client for Python: `pip install celery redis`*
*If using `django-celery-results` for storing results in Django DB (alternative to Redis result backend): `pip install django-celery-results` and add `'django_celery_results'` to `INSTALLED_APPS`.*

# backend/papri_project/settings.py
# ... other settings ...

# Qdrant Vector Database Configuration
QDRANT_HOST = os.getenv('QDRANT_HOST', 'localhost')
QDRANT_PORT = int(os.getenv('QDRANT_HTTP_PORT', 6334)) # Using HTTP port for REST client, or 6333 for gRPC
QDRANT_GRPC_PORT = int(os.getenv('QDRANT_GRPC_PORT', 6333))
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY', None) # If using Qdrant Cloud with an API key
QDRANT_COLLECTION_TRANSCRIPTS = "papri_transcript_embeddings"
QDRANT_COLLECTION_VISUAL = "papri_visual_embeddings" # For later

# If using local Qdrant via HTTP/REST (simpler client setup sometimes)
QDRANT_URL = os.getenv('QDRANT_URL', f"http://{QDRANT_HOST}:{QDRANT_PORT}")


# Sentence Transformer Model (ensure this is consistent)
SENTENCE_TRANSFORMER_MODEL = 'all-MiniLM-L6-v2'
# EMBEDDING_DIMENSION will be derived from the model, but can be set if known
EMBEDDING_DIMENSION = 384 # For 'all-MiniLM-L6-v2'

# ... rest of settings ...
