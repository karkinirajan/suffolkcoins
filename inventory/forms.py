import re

from django import forms

from .models import ContactMessage

FIELD = (
    "mt-1 block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 "
    "placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-green-600 sm:text-sm sm:leading-6"
)
PHONE = re.compile(r"^\+?\(?[0-9][0-9 ()\-.]{5,28}[0-9]$")


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "phone", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"class": FIELD, "autocomplete": "name"}),
            "phone": forms.TextInput(
                attrs={"class": FIELD, "autocomplete": "tel", "inputmode": "tel"}
            ),
            "message": forms.Textarea(attrs={"class": FIELD + " min-h-32", "rows": 5}),
        }
        labels = {"name": "Full name", "phone": "Phone No", "message": "Message"}

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        if not PHONE.match(phone):
            raise forms.ValidationError("Enter a phone number, for example 631 555 0100.")
        return phone

    def clean_name(self):
        return " ".join(self.cleaned_data["name"].split())
