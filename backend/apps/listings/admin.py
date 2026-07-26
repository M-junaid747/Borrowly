from django.contrib import admin

from .models import Availability, Category, Listing, ListingImage


class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 1


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ["title", "owner", "price_amount", "price_unit", "city", "is_active", "created_at"]
    list_filter = ["is_active", "category", "price_unit"]
    search_fields = ["title", "description", "city"]
    inlines = [ListingImageInline]


admin.site.register(Category)
admin.site.register(Availability)
