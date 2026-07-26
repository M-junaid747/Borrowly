from django.urls import path

from .views import BookingDetailView, BookingListCreateView, CreateCheckoutSessionView, DummyCheckoutView

urlpatterns = [
    path("", BookingListCreateView.as_view(), name="booking-list-create"),
    path("<int:pk>/", BookingDetailView.as_view(), name="booking-detail"),
    path("<int:booking_id>/dummy-pay/", DummyCheckoutView.as_view(), name="booking-dummy-pay"),
    path("<int:booking_id>/checkout/", CreateCheckoutSessionView.as_view(), name="booking-checkout"),
]
