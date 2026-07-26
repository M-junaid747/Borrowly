from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Category, Listing

User = get_user_model()


class ListingSearchTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="testpass123", active_role="seller")
        self.renter = User.objects.create_user(username="renter", password="testpass123")
        self.category = Category.objects.create(name="Cameras & Photography", slug="cameras-photography")
        self.other_category = Category.objects.create(name="Other", slug="other", is_other=True)

        self.near_listing = Listing.objects.create(
            owner=self.owner, category=self.category, title="DSLR Camera",
            description="Great camera", price_amount=20, price_unit=Listing.PriceUnit.DAY,
            city="New York", province="NY", latitude=40.7128, longitude=-74.0060,
        )
        self.far_listing = Listing.objects.create(
            owner=self.owner, category=self.category, title="Tent",
            description="4-person tent", price_amount=10, price_unit=Listing.PriceUnit.DAY,
            city="Los Angeles", province="CA", latitude=34.0522, longitude=-118.2437,
        )
        # No coordinates at all - must not crash distance search and must be excluded from it.
        self.no_coords_listing = Listing.objects.create(
            owner=self.owner, category=self.category, title="Board Games",
            description="Family game night box", price_amount=8, price_unit=Listing.PriceUnit.DAY,
            city="Chicago", province="IL",
        )

    def test_list_listings_public(self):
        response = self.client.get(reverse("listing-list-create"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 3)

    def test_distance_filter_excludes_far_and_coordinateless_listings(self):
        response = self.client.get(reverse("listing-list-create"), {"lat": 40.7128, "lng": -74.0060, "radius_km": 50})
        self.assertEqual(response.status_code, 200)
        titles = [item["title"] for item in response.data["results"]]
        self.assertIn("DSLR Camera", titles)
        self.assertNotIn("Tent", titles)
        self.assertNotIn("Board Games", titles)

    def test_only_selling_mode_users_can_create_listings(self):
        url = reverse("listing-list-create")
        payload = {
            "title": "Drill", "description": "Power drill", "price_amount": 5, "price_unit": "day",
            "city": "Karachi", "province": "Sindh", "category_id": self.category.id,
        }
        buyer_mode_user = User.objects.create_user(username="buyermode", password="testpass123")  # defaults to buyer
        self.client.force_authenticate(user=buyer_mode_user)
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 400)

        self.client.force_authenticate(user=self.owner)  # created with active_role="seller"
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["owner"]["username"], "owner")

    def test_other_category_requires_custom_name(self):
        url = reverse("listing-list-create")
        payload = {
            "title": "Unusual Item", "description": "Something rare", "price_amount": 5, "price_unit": "hour",
            "city": "Karachi", "province": "Sindh", "category_id": self.other_category.id,
        }
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 400)

        payload["custom_category"] = "Vintage Typewriter"
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 201)
