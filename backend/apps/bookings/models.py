from django.conf import settings
from django.db import models


class Booking(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        CONFIRMED = "confirmed", "Confirmed"
        PAID = "paid", "Paid"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    listing = models.ForeignKey("listings.Listing", on_delete=models.CASCADE, related_name="bookings")
    renter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings_made")
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    total_price = models.DecimalField(max_digits=9, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REQUESTED)
    stripe_checkout_session_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Booking #{self.id} - {self.listing.title}"
