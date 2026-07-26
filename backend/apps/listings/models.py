from django.conf import settings
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=60, unique=True)
    # The "Other" row: when a listing points at this category, its
    # custom_category text field holds the seller's own category name.
    is_other = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Listing(models.Model):
    class PriceUnit(models.TextChoices):
        HOUR = "hour", "Per hour"
        DAY = "day", "Per day"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="listings")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="listings")
    custom_category = models.CharField(
        max_length=60, blank=True, help_text="Only used when category is 'Other'."
    )
    title = models.CharField(max_length=120)
    description = models.TextField()

    # Seller picks the unit that makes sense for their item.
    price_amount = models.DecimalField(max_digits=8, decimal_places=2)
    price_unit = models.CharField(max_length=10, choices=PriceUnit.choices, default=PriceUnit.DAY)

    # Location: structured fields the seller always fills in, plus optional
    # precise coordinates and/or a Google Maps link for exact pickup spots.
    city = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    address = models.CharField(max_length=255, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    location_link = models.URLField(blank=True, help_text="Optional Google Maps link to the pickup location.")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["latitude", "longitude"]),
            models.Index(fields=["city", "province"]),
        ]

    def __str__(self):
        return self.title

    @property
    def category_label(self):
        if self.category and self.category.is_other and self.custom_category:
            return self.custom_category
        return self.category.name if self.category else ""


class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="listings/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["uploaded_at"]


class Availability(models.Model):
    """A date range during which the owner marks the item unavailable (e.g. already booked elsewhere)."""

    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="blocked_dates")
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        ordering = ["start_date"]
