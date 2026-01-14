import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url
# 1. Load environment variables
load_dotenv()

# 2. Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# 3. Security settings
# WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    'SECRET_KEY', 'django-insecure-change-me-for-production')


# 1. Update ALLOWED_HOSTS to accept the Seenode URL
# This allows all hosts if the env var isn't set (dev), or specific ones in prod
CSRF_TRUSTED_ORIGINS = [
    'https://web-sfrrulttcwj0.up-de-fra1-k8s-1.apps.run-on-seenode.com',
]

# Required because you are behind Seenode's load balancer
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

# 2. Update DEBUG
# Use a string comparison so it defaults to False in production
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = True

# ALLOWED_HOSTS = ['*']  # Allow all hosts for local development

# 4. Installed Apps
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',       # Required for Admin Panel
    'django.contrib.auth',        # Required for Login
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',  # Required for Admin styling

    # YOUR CUSTOM APP
    'tcm_admin',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'tcm.urls'

# 5. Templates (Crucial for Admin UI)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,  # Must be True to find Admin templates
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'tcm.wsgi.application'

# # 6. Database Connection (Your code)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.getenv('DB_NAME'),
#         'USER': os.getenv('DB_USER'),
#         'PASSWORD': os.getenv('DB_PASSWORD'),
#         'HOST': os.getenv('DB_HOST'),
#         'PORT': os.getenv('DB_PORT'),
#     }
# }
DATABASES = {
    'default': dj_database_url.config(
        default=f"postgres://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}",
        conn_max_age=600,
        ssl_require=True
    )
}
# # Fallback for local development if the long URL above fails or isn't set:
if 'DATABASE_URL' not in os.environ and DEBUG:
    DATABASES['default'] = {
        {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME'),
            'USER': os.getenv('DB_USER'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'HOST': os.getenv('DB_HOST'),
            'PORT': os.getenv('DB_PORT'),
        }
    }

#
# 7. Password Validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]

# 8. Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# 9. Static files (CSS, JavaScript, Images)
# This is required for the Admin panel to look correct
STATIC_URL = 'static/'

# ADD THIS LINE:
STATIC_ROOT = BASE_DIR / 'staticfiles'
# Enable WhiteNoise compression and caching
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
