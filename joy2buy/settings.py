"""
Django settings for the JOY2BUY project.

Every secret and every environment-specific value is read from environment
variables (loaded from a local ".env" file in development), so nothing
sensitive is stored in version control. See ".env.example" for the full list.
"""
import os
import sys
from decimal import Decimal
from pathlib import Path

import dj_database_url
from django.contrib.messages import constants as message_constants
from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    """Read a boolean environment variable ("true", "1", "yes", "on")."""
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    """Read a comma-separated environment variable as a clean list."""
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


# True while "python manage.py test" is running.
TESTING = len(sys.argv) > 1 and sys.argv[1] == "test"

# --------------------------------------------------------------------------
# Core security
# --------------------------------------------------------------------------
DEBUG = env_bool("DEBUG", default=False)

SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG or TESTING:
        # Throwaway key for local work only; sessions reset on each restart.
        SECRET_KEY = get_random_secret_key()
    else:
        raise ImproperlyConfigured(
            "The SECRET_KEY environment variable must be set when DEBUG is "
            "False."
        )

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

# --------------------------------------------------------------------------
# Applications
# --------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # Project apps
    "products.apps.ProductsConfig",
    "cart.apps.CartConfig",
    "orders.apps.OrdersConfig",
    "profiles.apps.ProfilesConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "joy2buy.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "cart.context_processors.cart",
                "products.context_processors.categories",
            ],
        },
    },
]

WSGI_APPLICATION = "joy2buy.wsgi.application"

# --------------------------------------------------------------------------
# Database
# One place, one variable: DATABASE_URL selects PostgreSQL or MySQL in
# production; without it a local SQLite file is used for development.
# --------------------------------------------------------------------------
DATABASE_URL = (
    os.environ.get("DATABASE_URL") or f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
)

DATABASES = {
    "default": dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=env_bool("DATABASE_SSL_REQUIRE", default=False),
    )
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------------------------------
# Authentication
# --------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation."
                "UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation."
                "MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation."
                "CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation."
                "NumericPasswordValidator",
    },
]

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "profiles:dashboard"
LOGOUT_REDIRECT_URL = "products:product_list"

# --------------------------------------------------------------------------
# Internationalisation
# --------------------------------------------------------------------------
LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Europe/London"
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------------
# Static files (WhiteNoise) and media files (local disk or Amazon S3)
# --------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

if TESTING:
    # Tests must not depend on "collectstatic" having been run.
    STORAGES["staticfiles"] = {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    }

USE_AWS = env_bool("USE_AWS", default=False)
if USE_AWS and not TESTING:
    # Credentials are read by boto3 from AWS_ACCESS_KEY_ID and
    # AWS_SECRET_ACCESS_KEY in the environment.
    AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME", "")
    AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "eu-west-2")
    if not AWS_STORAGE_BUCKET_NAME:
        raise ImproperlyConfigured(
            "USE_AWS is True but AWS_STORAGE_BUCKET_NAME is not set."
        )
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False
    STORAGES["default"] = {"BACKEND": "storages.backends.s3.S3Storage"}
    MEDIA_URL = (
        f"https://{AWS_STORAGE_BUCKET_NAME}.s3."
        f"{AWS_S3_REGION_NAME}.amazonaws.com/"
    )

# Uploaded images are limited to keep pages fast and storage small.
MAX_IMAGE_UPLOAD_BYTES = 2 * 1024 * 1024

# --------------------------------------------------------------------------
# Messages: map Django levels onto Bootstrap 5 alert classes
# --------------------------------------------------------------------------
MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"
MESSAGE_TAGS = {
    message_constants.DEBUG: "secondary",
    message_constants.INFO: "info",
    message_constants.SUCCESS: "success",
    message_constants.WARNING: "warning",
    message_constants.ERROR: "danger",
}

# --------------------------------------------------------------------------
# Sessions (the shopping cart lives in the session)
# --------------------------------------------------------------------------
CART_SESSION_KEY = "cart"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# --------------------------------------------------------------------------
# Store settings
# --------------------------------------------------------------------------
CURRENCY_SYMBOL = "£"
FREE_DELIVERY_THRESHOLD = Decimal(
    os.environ.get("FREE_DELIVERY_THRESHOLD") or "50.00"
)
STANDARD_DELIVERY_COST = Decimal(
    os.environ.get("STANDARD_DELIVERY_COST") or "4.99"
)
MAX_QUANTITY_PER_LINE = 20
PRODUCTS_PER_PAGE = 12

# --------------------------------------------------------------------------
# Production hardening (active whenever DEBUG is False)
# --------------------------------------------------------------------------
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

if not DEBUG and not TESTING:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", default=True)
    SESSION_COOKIE_SECURE = SECURE_SSL_REDIRECT
    CSRF_COOKIE_SECURE = SECURE_SSL_REDIRECT
    if SECURE_SSL_REDIRECT:
        SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
        SECURE_HSTS_INCLUDE_SUBDOMAINS = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}
