from django.urls import path

from .views import (
    AvailabilityCreateView,
    CategoryListView,
    ListingDetailView,
    ListingImageUploadView,
    ListingListCreateView,
    MyListingsView,
)

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("mine/", MyListingsView.as_view(), name="listing-mine"),
    path("", ListingListCreateView.as_view(), name="listing-list-create"),
    path("<int:pk>/", ListingDetailView.as_view(), name="listing-detail"),
    path("<int:listing_id>/images/", ListingImageUploadView.as_view(), name="listing-image-upload"),
    path("<int:listing_id>/availability/", AvailabilityCreateView.as_view(), name="listing-availability-create"),
]
