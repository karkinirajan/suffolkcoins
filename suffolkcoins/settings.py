"""
Settings for suffolkcoins, read from environment variables (``manage.py`` also loads a local ``.env``).

Nothing site-specific lives in this file any more: the secret key, the host names, the server address
and the Google sheet used to be written into it, and ``DEBUG`` was always on.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def env(name, default=""):
    """An empty variable counts as unset."""
    value = os.environ.get(name, "")
    return value if value != "" else default


def env_bool(name, default=False):
    value = env(name, None)
    return default if value is None else value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=()):
    value = env(name, None)
    return (
        list(default)
        if value is None
        else [item.strip() for item in value.split(",") if item.strip()]
    )


# --------------------------------------------------------------------------------------- core
DEBUG = env_bool("DEBUG", False)

SECRET_KEY = env("SECRET_KEY")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured(
            "Set the SECRET_KEY environment variable (or DEBUG=true for local work)."
        )
    SECRET_KEY = "insecure-key-for-local-development-only"  # noqa: S105  # nosec B105 - only ever used when DEBUG is on

# Without ALLOWED_HOSTS a production start serves nothing (Django answers 400): name the hosts.
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", ["localhost", "127.0.0.1"] if DEBUG else [])
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "inventory",
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

ROOT_URLCONF = "suffolkcoins.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # The project root used to be a template directory too, so any file in it could be rendered as a template.
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "suffolkcoins.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": env("DATABASE_PATH", str(BASE_DIR / "db.sqlite3")),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------- static and media
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = Path(env("STATIC_ROOT", str(BASE_DIR / "staticfiles")))
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(
    env("MEDIA_ROOT", str(BASE_DIR / "media"))
)  # was unset: uploads went to the working directory
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# ------------------------------------------------------------------------------ production
HTTPS_ONLY = env_bool("HTTPS_ONLY", not DEBUG)
if HTTPS_ONLY:
    # The site is expected behind a TLS-terminating proxy that sets X-Forwarded-Proto.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(env("HSTS_SECONDS", "3600"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_SECONDS > 0
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# -------------------------------------------------------------------- the live inventory list
# The inventory page exports a Google Sheet as a PDF with a service account. The key file is no
# longer read from the project folder (it was committed there): point GOOGLE_APPLICATION_CREDENTIALS at it.
GOOGLE_APPLICATION_CREDENTIALS = env("GOOGLE_APPLICATION_CREDENTIALS")
INVENTORY_SHEET_ID = env("INVENTORY_SHEET_ID")
INVENTORY_CACHE_SECONDS = int(env("INVENTORY_CACHE_SECONDS", "300"))

CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# --------------------------------------------------------------------------------- logging
# To the console (the old file handler logged every SQL query at DEBUG into an unrotated file).
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", "INFO")},
}

# ----------------------------------------------------------------------------------- admin
JAZZMIN_SETTINGS = {
    "site_title": "Suffolkcoins Admin",
    "site_header": "Suffolkcoins",
    "site_brand": "Suffolkcoins",
    "welcome_sign": "Welcome to Suffolkcoins",
    "copyright": "Suffolkcoins",
    "search_model": ["auth.User", "inventory.ContactMessage"],
    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "inventory.ContactMessage": "fas fa-comments",
        "inventory.Inventory": "fas fa-file-pdf",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    "related_modal_active": False,
    "use_google_fonts_cdn": False,  # the admin no longer calls out to Google Fonts
    "show_ui_builder": False,
    "changeform_format": "horizontal_tabs",
}
