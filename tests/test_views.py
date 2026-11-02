import re
from unittest.mock import patch

import pytest
from django.test import Client
from django.urls import reverse

from inventory.drive import InventoryNotConfigured, InventoryUnavailable
from inventory.models import ContactMessage

VALID = {"name": "Jane Doe", "phone": "631 555 0100", "message": "Do you have 1964 half dollars?"}


class TestHomePage:
    def test_it_renders_with_the_banners_the_form_and_the_footer(self, client):
        response = client.get("/")
        html = response.content.decode()
        assert response.status_code == 200
        assert html.count("data-slide") == 3 and 'name="website"' in html
        assert "banner1.jpg" in html and "css/site.css" in html and "js/carousel.js" in html
        assert "suffolkcoins.com, All rights reserved" in html

    def test_no_page_loads_a_script_or_style_from_a_third_party(self, client):
        """It used to load the Tailwind play CDN (development only) and Alpine.js from unpkg."""
        html = client.get("/").content.decode()
        assert not re.findall(r'(?:src|href)="https?://', html)
        assert "cdn.tailwindcss.com" not in html and "unpkg.com" not in html

    def test_the_date_is_filled_in_instead_of_the_word_Date(self, client):
        html = client.get("/").content.decode()
        assert re.search(
            r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), \d{1,2} [A-Z][a-z]+ \d{4}",
            html,
        )
        assert ">\n          Date\n" not in html

    def test_the_inventory_link_opens_in_a_new_tab_safely(self, client):
        html = client.get("/").content.decode()
        assert 'target="_blank" rel="noopener"' in html

    def test_only_get_is_allowed(self, client):
        assert client.post("/").status_code == 405


class TestInventoryPage:
    def test_the_pdf_is_shown_in_the_browser(self, client):
        with patch("inventory.views.inventory_pdf", return_value=b"%PDF-1.7 data"):
            response = client.get(reverse("inventory"))
        assert response.status_code == 200 and response.content == b"%PDF-1.7 data"
        assert response["Content-Type"] == "application/pdf"
        assert response["Content-Disposition"] == 'inline; filename="inventory.pdf"'

    def test_not_set_up_is_a_503_in_plain_text(self, client):
        with patch("inventory.views.inventory_pdf", side_effect=InventoryNotConfigured):
            response = client.get("/inventory/")
        assert response.status_code == 503 and response["Content-Type"].startswith("text/plain")

    def test_google_failing_is_a_502_that_leaks_nothing(self, client):
        with patch(
            "inventory.views.inventory_pdf",
            side_effect=InventoryUnavailable("403 forbidden for service account x@y.iam"),
        ):
            response = client.get("/inventory/")
        assert response.status_code == 502 and b"iam" not in response.content

    def test_only_get_is_allowed(self, client):
        assert client.post("/inventory/").status_code == 405


@pytest.mark.django_db
class TestContactForm:
    def test_a_valid_message_is_saved_and_the_visitor_is_thanked(self, client):
        response = client.post("/contact/", VALID, follow=True)
        assert response.redirect_chain == [("/#contact", 302)]
        assert "we will call you back" in response.content.decode()
        message = ContactMessage.objects.get()
        assert (message.name, message.phone, message.handled) == ("Jane Doe", "631 555 0100", False)
        assert message.message == VALID["message"] and message.created_at is not None

    def test_the_name_is_tidied(self, client):
        client.post("/contact/", {**VALID, "name": "  Jane    Q   Doe "})
        assert ContactMessage.objects.get().name == "Jane Q Doe"

    @pytest.mark.parametrize(
        "change",
        [
            {"name": ""},
            {"phone": ""},
            {"message": ""},
            {"name": "x" * 101},
            {"message": "m" * 2001},
        ],
    )
    def test_incomplete_or_oversized_input_is_refused_with_the_errors_shown(self, client, change):
        response = client.post("/contact/", {**VALID, **change})
        assert response.status_code == 400
        assert ContactMessage.objects.count() == 0
        assert "text-red-700" in response.content.decode()

    @pytest.mark.parametrize(
        "phone",
        ["abc", "12", "<script>alert(1)</script>", "1" * 40, "+++++++", "hello world 1234567"],
    )
    def test_a_phone_number_has_to_look_like_one(self, client, phone):
        assert client.post("/contact/", {**VALID, "phone": phone}).status_code == 400
        assert ContactMessage.objects.count() == 0

    @pytest.mark.parametrize(
        "phone",
        ["631 555 0100", "(631) 555-0100", "+1 631 555 0100", "6315550100", "+44 20 7946 0958"],
    )
    def test_ordinary_phone_numbers_are_accepted(self, client, phone):
        assert client.post("/contact/", {**VALID, "phone": phone}).status_code == 302

    def test_the_visitors_input_is_shown_back_escaped(self, client):
        response = client.post(
            "/contact/", {"name": '"><script>alert(1)</script>', "phone": "bad", "message": "x"}
        )
        html = response.content.decode()
        assert "<script>alert(1)</script>" not in html and "&lt;script&gt;" in html

    def test_a_bot_that_fills_the_hidden_field_looks_successful_but_nothing_is_stored(self, client):
        response = client.post(
            "/contact/", {**VALID, "website": "http://spam.example"}, follow=True
        )
        assert (
            response.redirect_chain == [("/#contact", 302)]
            and "we will call you back" in response.content.decode()
        )
        assert ContactMessage.objects.count() == 0

    def test_the_form_needs_the_csrf_token(self):
        strict = Client(enforce_csrf_checks=True)
        assert strict.post("/contact/", VALID).status_code == 403
        assert ContactMessage.objects.count() == 0

    def test_get_is_not_allowed(self, client):
        assert client.get("/contact/").status_code == 405


@pytest.mark.django_db
class TestAdmin:
    @pytest.fixture
    def staff(self, client, django_user_model):
        user = django_user_model.objects.create_superuser(
            "boss", "boss@example.com", "pw-for-tests-123"
        )
        client.force_login(user)
        return client

    def test_messages_are_listed_and_cannot_be_added_by_hand(self, staff):
        ContactMessage.objects.create(name="Jane", phone="631 555 0100", message="hi")
        page = staff.get("/admin/inventory/contactmessage/")
        assert page.status_code == 200 and "Jane" in page.content.decode()
        assert staff.get("/admin/inventory/contactmessage/add/").status_code == 403

    def test_an_inventory_item_without_a_name_does_not_break_the_admin_list(self, staff):
        from inventory.models import Inventory

        item = Inventory.objects.create(name=None)
        assert str(item) == f"Inventory item {item.pk}"
        assert staff.get("/admin/inventory/inventory/").status_code == 200

    def test_the_admin_needs_a_login(self, client):
        assert client.get("/admin/inventory/contactmessage/").status_code == 302


def test_the_wsgi_and_asgi_applications_load():
    from suffolkcoins.asgi import application as asgi_app
    from suffolkcoins.wsgi import application as wsgi_app

    assert callable(wsgi_app) and callable(asgi_app)
