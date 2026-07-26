from datetime import datetime, timedelta, timezone

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.listings.models import Category, Listing

from .models import Booking

User = get_user_model()


class BookingTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="testpass123")
        self.renter = User.objects.create_user(username="renter", password="testpass123")
        category = Category.objects.create(name="Tools & Equipment", slug="tools-equipment")

        self.daily_listing = Listing.objects.create(
            owner=self.owner, category=category, title="Drill", description="Cordless drill",
            price_amount=10, price_unit=Listing.PriceUnit.DAY, city="Lahore", province="Punjab",
        )
        self.hourly_listing = Listing.objects.create(
            owner=self.owner, category=category, title="Projector", description="HD projector",
            price_amount=5, price_unit=Listing.PriceUnit.HOUR, city="Lahore", province="Punjab",
        )

    def test_daily_booking_total_price(self):
        self.client.force_authenticate(user=self.renter)
        url = reverse("booking-list-create")
        start = datetime.now(timezone.utc) + timedelta(days=1)
        end = start + timedelta(days=4)  # 4 rental days
        response = self.client.post(url, {
            "listing_id": self.daily_listing.id, "start_datetime": start, "end_datetime": end,
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["total_price"], "40.00")

    def test_hourly_booking_total_price(self):
        self.client.force_authenticate(user=self.renter)
        url = reverse("booking-list-create")
        start = datetime.now(timezone.utc) + timedelta(days=1)
        end = start + timedelta(hours=3)
        response = self.client.post(url, {
            "listing_id": self.hourly_listing.id, "start_datetime": start, "end_datetime": end,
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["total_price"], "15.00")

    def test_only_buying_mode_users_can_create_bookings(self):
        seller_mode_user = User.objects.create_user(username="sellermode", password="testpass123", active_role="seller")
        self.client.force_authenticate(user=seller_mode_user)
        url = reverse("booking-list-create")
        start = datetime.now(timezone.utc) + timedelta(days=1)
        end = start + timedelta(days=2)
        response = self.client.post(url, {
            "listing_id": self.daily_listing.id, "start_datetime": start, "end_datetime": end,
        })
        self.assertEqual(response.status_code, 400)

    def test_dummy_checkout_marks_booking_paid(self):
        booking = Booking.objects.create(
            listing=self.daily_listing, renter=self.renter,
            start_datetime=datetime.now(timezone.utc),
            end_datetime=datetime.now(timezone.utc) + timedelta(days=2),
            total_price=20, status=Booking.Status.CONFIRMED,
        )
        self.client.force_authenticate(user=self.renter)
        url = reverse("booking-dummy-pay", args=[booking.id])

        bad_response = self.client.post(url, {
            "name_on_card": "Jane Doe", "card_number": "123", "expiry": "13/99", "cvv": "1",
        })
        self.assertEqual(bad_response.status_code, 400)

        good_response = self.client.post(url, {
            "name_on_card": "Jane Doe", "card_number": "4242424242424242", "expiry": "12/29", "cvv": "123",
        })
        self.assertEqual(good_response.status_code, 200)
        self.assertEqual(good_response.data["status"], "paid")
        booking = Booking.objects.create(
            listing=self.daily_listing, renter=self.renter,
            start_datetime=datetime.now(timezone.utc),
            end_datetime=datetime.now(timezone.utc) + timedelta(days=2),
            total_price=20,
        )
        url = reverse("booking-detail", args=[booking.id])

        self.client.force_authenticate(user=self.renter)
        response = self.client.patch(url, {"status": "confirmed"})
        self.assertEqual(response.status_code, 403)

        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(url, {"status": "confirmed"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "confirmed")
