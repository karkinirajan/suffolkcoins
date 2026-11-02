from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from .drive import InventoryNotConfigured, InventoryUnavailable, inventory_pdf
from .forms import ContactForm


def _home(request, form, status=200):
    return render(request, "index.html", {"form": form}, status=status)


@require_GET
def index(request):
    return _home(request, ContactForm())


@require_POST
def contact(request):
    # A field real visitors never see: bots fill it in. They are answered as if it had worked.
    if request.POST.get("website"):
        messages.success(request, "Thank you, we will call you back.")
        return redirect(reverse("index") + "#contact")
    form = ContactForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Thank you, we will call you back.")
        return redirect(reverse("index") + "#contact")
    return _home(request, form, status=400)


@require_GET
def inventory(request):
    """The inventory sheet as a PDF, shown in the browser."""
    try:
        pdf = inventory_pdf()
    except InventoryNotConfigured:
        return HttpResponse(
            "The inventory list is not available right now.", status=503, content_type="text/plain"
        )
    except InventoryUnavailable:
        return HttpResponse(
            "The inventory list could not be loaded. Please try again shortly.",
            status=502,
            content_type="text/plain",
        )
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="inventory.pdf"'
    return response
