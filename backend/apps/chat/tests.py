from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.listings.models import Category, Listing

from .models import Message

User = get_user_model()


class ChatPermissionTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="testpass123", active_role="seller")
        self.buyer = User.objects.create_user(username="buyer", password="testpass123")  # default: buyer
        category = Category.objects.create(name="Tools & Equipment", slug="tools-equipment")
        self.listing = Listing.objects.create(
            owner=self.owner, category=category, title="Drill", description="Cordless drill",
            price_amount=10, price_unit=Listing.PriceUnit.DAY, city="Lahore", province="Punjab",
        )

    def test_buyer_can_message_seller(self):
        self.client.force_authenticate(user=self.buyer)
        url = reverse("chat-conversation", args=[self.listing.id, self.owner.id])
        response = self.client.post(url, {"body": "Is this available this weekend?"})
        self.assertEqual(response.status_code, 201)

    def test_selling_mode_user_cannot_start_a_chat_about_someone_elses_listing(self):
        browsing_seller = User.objects.create_user(username="otherseller", password="testpass123", active_role="seller")
        self.client.force_authenticate(user=browsing_seller)
        url = reverse("chat-conversation", args=[self.listing.id, self.owner.id])
        response = self.client.post(url, {"body": "Hey"})
        self.assertEqual(response.status_code, 403)

    def test_owner_can_always_reply_regardless_of_active_role(self):
        Message.objects.create(listing=self.listing, sender=self.buyer, recipient=self.owner, body="Hi there")
        # Owner is in "seller" mode already, but even if they were in buyer
        # mode elsewhere, replying about their own listing must still work.
        self.owner.active_role = "buyer"
        self.owner.save(update_fields=["active_role"])
        self.client.force_authenticate(user=self.owner)
        url = reverse("chat-conversation", args=[self.listing.id, self.buyer.id])
        response = self.client.post(url, {"body": "Yes, still available!"})
        self.assertEqual(response.status_code, 201)

    def test_fetching_thread_marks_messages_read(self):
        Message.objects.create(listing=self.listing, sender=self.buyer, recipient=self.owner, body="Hello?")
        self.client.force_authenticate(user=self.owner)
        unread_before = self.client.get(reverse("chat-unread-count")).data["count"]
        self.assertEqual(unread_before, 1)

        self.client.get(reverse("chat-conversation", args=[self.listing.id, self.buyer.id]))

        unread_after = self.client.get(reverse("chat-unread-count")).data["count"]
        self.assertEqual(unread_after, 0)

    def test_inbox_groups_threads_with_role_and_unread_count(self):
        Message.objects.create(listing=self.listing, sender=self.buyer, recipient=self.owner, body="Hello?")
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(reverse("chat-inbox"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        thread = response.data[0]
        self.assertEqual(thread["role"], "seller")
        self.assertEqual(thread["unread_count"], 1)
