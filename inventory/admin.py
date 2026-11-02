from django.contrib import admin

from .models import ContactMessage, Inventory


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "created_at", "handled")
    list_filter = ("handled", "created_at")
    search_fields = ("name", "phone", "message")
    readonly_fields = ("name", "phone", "message", "created_at")
    list_editable = ("handled",)

    def has_add_permission(self, request):
        return False  # messages come from the website


admin.site.register(Inventory)
