"""The live inventory list: a Google Sheet exported as a PDF with a service account."""

import logging
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from google.auth.exceptions import GoogleAuthError
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# Exporting a file needs read access only. The old code asked for full read and write access to
# the service account's whole Drive (and the spreadsheets scope it did not use).
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
FRESH_KEY = "inventory:pdf"
STALE_KEY = "inventory:pdf:last-good"
STALE_SECONDS = 7 * 24 * 3600


class InventoryNotConfigured(Exception):
    """No sheet or no usable key file is configured."""


class InventoryUnavailable(Exception):
    """Google could not be reached or refused, and there is no earlier copy to serve."""


def build_drive_service():
    path = settings.GOOGLE_APPLICATION_CREDENTIALS
    if not settings.INVENTORY_SHEET_ID or not path or not Path(path).is_file():
        raise InventoryNotConfigured(
            "INVENTORY_SHEET_ID or GOOGLE_APPLICATION_CREDENTIALS is not set up"
        )
    credentials = Credentials.from_service_account_file(path, scopes=SCOPES)
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def export_pdf(service, sheet_id):
    return service.files().export_media(fileId=sheet_id, mimeType="application/pdf").execute()


def inventory_pdf():
    """The PDF, from the cache when it is fresh. The old view called Google on every request, so every
    visitor (or a script) used API quota and waited for Google. If Google fails, the last good copy is served."""
    fresh = cache.get(FRESH_KEY)
    if fresh is not None:
        return fresh
    try:
        data = export_pdf(build_drive_service(), settings.INVENTORY_SHEET_ID)
    except InventoryNotConfigured:
        raise
    except (HttpError, GoogleAuthError, OSError, ValueError) as error:
        logger.error("Could not export the inventory sheet: %s", type(error).__name__)
        stale = cache.get(STALE_KEY)
        if stale is not None:
            return stale
        raise InventoryUnavailable from error
    cache.set(FRESH_KEY, data, settings.INVENTORY_CACHE_SECONDS)
    cache.set(STALE_KEY, data, STALE_SECONDS)
    return data
