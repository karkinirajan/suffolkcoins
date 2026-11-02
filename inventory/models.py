from django.db import models


class Inventory(models.Model):
    """A PDF uploaded in the admin. (The public inventory list comes from the Google Sheet, not from here.)"""

    id = models.AutoField(primary_key=True)
    # null=True is deliberate: migration 0002 made it nullable and existing rows may rely on it
    name = models.CharField(  # noqa: DJ001
        max_length=100, default="Suffolk Coins Inventory Item", blank=True, null=True
    )
    file = models.FileField(upload_to="inventory_files", default="inventory_files/blank.pdf")

    class Meta:
        verbose_name_plural = "Inventories"

    def __str__(self):
        # name may be blank or null; returning it as it was made the admin list crash
        return self.name or f"Inventory item {self.pk}"


class ContactMessage(models.Model):
    """A message from the contact form on the home page. The form used to post nowhere."""

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=30)
    message = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    handled = models.BooleanField(
        default=False, help_text="Tick when the customer has been called back."
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.created_at:%Y-%m-%d %H:%M})"
