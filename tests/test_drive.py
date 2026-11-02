from unittest.mock import MagicMock, patch

import pytest
from googleapiclient.errors import HttpError
from httplib2 import Response

from inventory import drive
from inventory.drive import InventoryNotConfigured, InventoryUnavailable, inventory_pdf


def http_error(status=500):
    return HttpError(Response({"status": status}), b"{}")


@pytest.fixture
def configured(settings, tmp_path):
    key = tmp_path / "key.json"
    key.write_text("{}")
    settings.GOOGLE_APPLICATION_CREDENTIALS = str(key)
    settings.INVENTORY_SHEET_ID = "SHEET_ID"
    return key


class TestScope:
    def test_only_read_access_to_drive_is_requested(self):
        """The old view asked for full read and write access to the service account's whole Drive."""
        assert drive.SCOPES == ["https://www.googleapis.com/auth/drive.readonly"]


class TestBuildService:
    def test_the_key_file_and_the_read_only_scope_are_used(self, configured):
        with (
            patch("inventory.drive.Credentials") as credentials,
            patch("inventory.drive.build") as build,
        ):
            service = drive.build_drive_service()
        credentials.from_service_account_file.assert_called_once_with(
            str(configured), scopes=drive.SCOPES
        )
        build.assert_called_once_with(
            "drive",
            "v3",
            credentials=credentials.from_service_account_file.return_value,
            cache_discovery=False,
        )
        assert service is build.return_value

    @pytest.mark.parametrize("what", ["no_sheet", "no_key_setting", "key_file_missing"])
    def test_missing_configuration_is_reported_as_not_configured(self, settings, configured, what):
        if what == "no_sheet":
            settings.INVENTORY_SHEET_ID = ""
        elif what == "no_key_setting":
            settings.GOOGLE_APPLICATION_CREDENTIALS = ""
        else:
            settings.GOOGLE_APPLICATION_CREDENTIALS = str(configured) + ".missing"
        with pytest.raises(InventoryNotConfigured):
            drive.build_drive_service()


class TestExport:
    def test_the_sheet_is_exported_as_a_pdf(self):
        service = MagicMock()
        service.files.return_value.export_media.return_value.execute.return_value = b"%PDF-data"
        assert drive.export_pdf(service, "ID") == b"%PDF-data"
        service.files.return_value.export_media.assert_called_once_with(
            fileId="ID", mimeType="application/pdf"
        )


class TestCaching:
    def test_google_is_called_once_while_the_copy_is_fresh(self, configured):
        with (
            patch("inventory.drive.build_drive_service"),
            patch("inventory.drive.export_pdf", return_value=b"PDF1") as export,
        ):
            assert [inventory_pdf() for _ in range(5)] == [b"PDF1"] * 5
        assert export.call_count == 1  # the old view called Google on every request

    def test_the_sheet_id_from_the_settings_is_exported(self, configured):
        with (
            patch("inventory.drive.build_drive_service") as service,
            patch("inventory.drive.export_pdf", return_value=b"x") as export,
        ):
            inventory_pdf()
        export.assert_called_once_with(service.return_value, "SHEET_ID")

    def test_the_cache_expires_after_the_configured_time(self, configured, settings):
        from django.core.cache import cache

        settings.INVENTORY_CACHE_SECONDS = 60
        with (
            patch("inventory.drive.build_drive_service"),
            patch("inventory.drive.export_pdf", side_effect=[b"old", b"new"]) as export,
        ):
            assert inventory_pdf() == b"old"
            cache.delete(drive.FRESH_KEY)  # what the passing of 60 seconds does
            assert inventory_pdf() == b"new"
        assert export.call_count == 2

    def test_the_last_good_copy_is_served_when_google_fails(self, configured):
        from django.core.cache import cache

        with (
            patch("inventory.drive.build_drive_service"),
            patch("inventory.drive.export_pdf", side_effect=[b"good", http_error(503)]),
        ):
            assert inventory_pdf() == b"good"
            cache.delete(drive.FRESH_KEY)
            assert inventory_pdf() == b"good"

    @pytest.mark.parametrize(
        "error", [http_error(403), http_error(500), OSError("network"), ValueError("bad key")]
    )
    def test_without_an_earlier_copy_a_failure_is_reported_as_unavailable(self, configured, error):
        with (
            patch("inventory.drive.build_drive_service"),
            patch("inventory.drive.export_pdf", side_effect=error),
        ):
            with pytest.raises(InventoryUnavailable):
                inventory_pdf()

    def test_a_failure_is_not_cached(self, configured):
        with (
            patch("inventory.drive.build_drive_service"),
            patch("inventory.drive.export_pdf", side_effect=[http_error(500), b"ok"]),
        ):
            with pytest.raises(InventoryUnavailable):
                inventory_pdf()
            assert inventory_pdf() == b"ok"

    def test_not_configured_is_passed_through_and_never_hides_behind_an_old_copy(
        self, settings, configured
    ):
        with (
            patch("inventory.drive.build_drive_service"),
            patch("inventory.drive.export_pdf", return_value=b"good"),
        ):
            inventory_pdf()
        settings.INVENTORY_SHEET_ID = ""
        from django.core.cache import cache

        cache.delete(drive.FRESH_KEY)
        with patch("inventory.drive.build_drive_service", side_effect=InventoryNotConfigured):
            with pytest.raises(InventoryNotConfigured):
                inventory_pdf()

    def test_the_error_log_names_the_kind_of_error_but_not_its_text(self, configured, caplog):
        secret = "sensitive-detail-in-the-message"
        with (
            patch("inventory.drive.build_drive_service"),
            patch("inventory.drive.export_pdf", side_effect=OSError(secret)),
        ):
            with pytest.raises(InventoryUnavailable):
                inventory_pdf()
        assert "OSError" in caplog.text and secret not in caplog.text
