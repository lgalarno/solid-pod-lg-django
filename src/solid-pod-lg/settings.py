"""
Django settings for solid-pod-lg project.

Generated by 'django-admin startproject' using Django 4.2.5.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
from dotenv import dotenv_values

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

config = dotenv_values(BASE_DIR / '.env')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config["DJANGO_SECRET_KEY"]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = str(config["DEBUG"]) == "1"  # 1 == True

ALLOWED_HOSTS = config["ALLOWED_HOSTS"].split(',') if config["ALLOWED_HOSTS"] else []

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    'django.contrib.sitemaps',
    "django.contrib.staticfiles",
    # third party
    "crispy_forms",
    "crispy_bootstrap5",
    # custom app
    'accounts',
    'pod_registration',
    'pod_session',
    'connector'
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "solid-pod-lg.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates']
        ,
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "solid-pod-lg.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
#
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "db.sqlite3",
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': config.get('DATABASE_ENGINE'),
        'HOST': config.get('DATABASE_HOST'),
        'PORT': config.get('DATABASE_PORT'),
        'USER': config.get('DATABASE_USER'),
        'PASSWORD': config.get('DATABASE_PASSWORD'),
        'NAME': config.get('DATABASE_NAME'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'use_unicode': True, },
    },
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True



######################################################################
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/
######################################################################
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = config.get('STATIC_ROOT')
MEDIA_ROOT = config.get('MEDIA_ROOT', BASE_DIR / '..' / "media")
# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

######################################################################
# LOGIN/LOGOUT REDIRECT
######################################################################
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/account/login/'
LOGIN_REDIRECT_URL = '/pod_registration/dashboard/'

######################################################################
# CRISPY_FORMS
######################################################################
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

######################################################################
# APP variables
######################################################################

OID_CALLBACK_URI = config["OID_CALLBACK_URI"]
CLIENT_NAME = config["CLIENT_NAME"]
CLIENT_CONTACT = config["CLIENT_CONTACT"]
CLIENT_URL = config["CLIENT_URL"]
