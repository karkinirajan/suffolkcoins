"""The settings, read in fresh interpreters with chosen environment variables."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SNIPPET = """
import json
from suffolkcoins import settings as s
print(json.dumps({k: getattr(s, k, None) for k in (
    'DEBUG', 'SECRET_KEY', 'ALLOWED_HOSTS', 'CSRF_TRUSTED_ORIGINS', 'HTTPS_ONLY', 'SECURE_SSL_REDIRECT',
    'SESSION_COOKIE_SECURE', 'CSRF_COOKIE_SECURE', 'SECURE_HSTS_SECONDS', 'X_FRAME_OPTIONS',
    'GOOGLE_APPLICATION_CREDENTIALS', 'INVENTORY_SHEET_ID', 'INVENTORY_CACHE_SECONDS')}, default=str))
"""


def load(**env):
    clean = {
        k: v
        for k, v in os.environ.items()
        if k
        not in {
            "DEBUG",
            "SECRET_KEY",
            "ALLOWED_HOSTS",
            "CSRF_TRUSTED_ORIGINS",
            "HTTPS_ONLY",
            "HSTS_SECONDS",
            "GOOGLE_APPLICATION_CREDENTIALS",
            "INVENTORY_SHEET_ID",
            "INVENTORY_CACHE_SECONDS",
            "DATABASE_PATH",
        }
    }
    clean.update(PYTHONPATH=str(ROOT), **env)
    result = subprocess.run(
        [sys.executable, "-c", SNIPPET], env=clean, capture_output=True, text=True, cwd="/"
    )
    return result


def settings_of(**env):
    result = load(**env)
    assert result.returncode == 0, result.stderr[-400:]
    return json.loads(result.stdout)


def test_production_needs_a_secret_key_instead_of_using_one_from_the_code():
    result = load()
    assert result.returncode != 0 and "Set the SECRET_KEY" in result.stderr


def test_debug_is_off_unless_asked_for():
    s = settings_of(SECRET_KEY="x" * 50, ALLOWED_HOSTS="example.com")
    assert s["DEBUG"] is False


def test_local_development_works_with_debug_on_and_no_configuration():
    s = settings_of(DEBUG="true")
    assert (
        s["DEBUG"] is True
        and s["ALLOWED_HOSTS"] == ["localhost", "127.0.0.1"]
        and s["HTTPS_ONLY"] is False
    )
    assert s["SECURE_SSL_REDIRECT"] is None  # no redirect loop on localhost


def test_production_hardening_is_on_by_default():
    s = settings_of(SECRET_KEY="x" * 50, ALLOWED_HOSTS="example.com,www.example.com")
    assert s["ALLOWED_HOSTS"] == ["example.com", "www.example.com"]
    assert s["HTTPS_ONLY"] is True and s["SECURE_SSL_REDIRECT"] is True
    assert s["SESSION_COOKIE_SECURE"] is True and s["CSRF_COOKIE_SECURE"] is True
    assert s["SECURE_HSTS_SECONDS"] == 3600 and s["X_FRAME_OPTIONS"] == "DENY"


def test_no_host_is_allowed_unless_named():
    assert settings_of(SECRET_KEY="x" * 50)["ALLOWED_HOSTS"] == []


def test_https_only_can_be_switched_off_for_a_plain_http_deployment():
    s = settings_of(SECRET_KEY="x" * 50, ALLOWED_HOSTS="a.com", HTTPS_ONLY="false")
    assert s["SECURE_SSL_REDIRECT"] is None and s["SESSION_COOKIE_SECURE"] is None


def test_hsts_and_trusted_origins_come_from_the_environment():
    s = settings_of(
        SECRET_KEY="x" * 50,
        ALLOWED_HOSTS="a.com",
        HSTS_SECONDS="31536000",
        CSRF_TRUSTED_ORIGINS="https://a.com, https://b.com",
    )
    assert s["SECURE_HSTS_SECONDS"] == 31536000 and s["CSRF_TRUSTED_ORIGINS"] == [
        "https://a.com",
        "https://b.com",
    ]


def test_an_empty_variable_counts_as_unset():
    result = load(SECRET_KEY="", DEBUG="")
    assert result.returncode != 0  # still no key, and DEBUG did not turn into something truthy


def test_the_google_settings_come_from_the_environment_and_default_to_nothing():
    default = settings_of(DEBUG="true")
    assert (
        default["GOOGLE_APPLICATION_CREDENTIALS"],
        default["INVENTORY_SHEET_ID"],
        default["INVENTORY_CACHE_SECONDS"],
    ) == ("", "", 300)
    s = settings_of(
        DEBUG="true",
        GOOGLE_APPLICATION_CREDENTIALS="/keys/k.json",
        INVENTORY_SHEET_ID="abc",
        INVENTORY_CACHE_SECONDS="60",
    )
    assert (
        s["GOOGLE_APPLICATION_CREDENTIALS"],
        s["INVENTORY_SHEET_ID"],
        s["INVENTORY_CACHE_SECONDS"],
    ) == ("/keys/k.json", "abc", 60)


def test_the_project_folder_is_not_a_template_directory():
    from django.conf import settings

    dirs = [Path(d) for d in settings.TEMPLATES[0]["DIRS"]]
    assert dirs == [ROOT / "templates"]


def test_the_media_folder_is_set():
    from django.conf import settings

    assert Path(settings.MEDIA_ROOT).name == "media"


@pytest.mark.parametrize("name", ["credentials.json"])
def test_the_key_file_is_ignored_by_git_and_never_read_from_the_project_folder(name):
    assert name in (ROOT / ".gitignore").read_text()
    from django.conf import settings

    assert (
        not settings.GOOGLE_APPLICATION_CREDENTIALS.endswith(name)
        or settings.GOOGLE_APPLICATION_CREDENTIALS == ""
    )
