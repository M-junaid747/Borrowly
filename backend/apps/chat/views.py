from django.db.models import Q
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.listings.models import Listing

from .models import Message
from .serializers import MessageSerializer


class ConversationView(generics.ListCreateAPIView):
    """
    GET  /api/chat/<listing_id>/<other_user_id>/  -> full thread between
         request.user and other_user for that listing, oldest first. Also
         marks any unread messages addressed to request.user as read.
    POST to the same URL to send a new message (recipient is taken from the URL).

    Sending is allowed if you own the listing (replying to an inquiry about
    your own item is always allowed) or if you're in buying mode (starting
    a conversation about someone else's item). Selling-mode users browsing
    other people's listings cannot start chats.

    The frontend polls this endpoint every few seconds, which avoids needing
    WebSockets/Redis for the MVP while still feeling close to real-time.
    """

    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        listing_id = self.kwargs["listing_id"]
        other_user_id = self.kwargs["other_user_id"]
        return Message.objects.filter(
            listing_id=listing_id
        ).filter(
            Q(sender_id=user.id, recipient_id=other_user_id) | Q(sender_id=other_user_id, recipient_id=user.id)
        )

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        Message.objects.filter(
            listing_id=self.kwargs["listing_id"],
            sender_id=self.kwargs["other_user_id"],
            recipient=request.user,
            is_read=False,
        ).update(is_read=True)
        return response

    def perform_create(self, serializer):
        listing = generics.get_object_or_404(Listing, id=self.kwargs["listing_id"])
        is_owner = listing.owner_id == self.request.user.id
        if not is_owner and self.request.user.active_role != self.request.user.ROLE_BUYER:
            raise PermissionDenied("Switch to buying mode to message sellers about their listings.")
        serializer.save(
            sender=self.request.user,
            recipient_id=self.kwargs["other_user_id"],
            listing_id=self.kwargs["listing_id"],
        )


class InboxView(APIView):
    """
    Groups the user's messages into threads (one per listing + counterpart),
    each tagged with whether the user is the "seller" (listing owner) or
    "buyer" side of that thread, plus an unread count - powers the
    dashboard message lists and the unread badge in the nav bar.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        messages = (
            Message.objects.filter(Q(sender=user) | Q(recipient=user))
            .select_related("sender", "recipient", "listing")
            .order_by("-created_at")
        )

        threads = {}
        for message in messages:
            other = message.recipient if message.sender_id == user.id else message.sender
            key = (message.listing_id, other.id)
            if key not in threads:
                threads[key] = {
                    "listing_id": message.listing_id,
                    "listing_title": message.listing.title,
                    "other_user_id": other.id,
                    "other_username": other.username,
                    "role": "seller" if message.listing.owner_id == user.id else "buyer",
                    "last_message": message.body,
                    "last_message_at": message.created_at,
                    "unread_count": 0,
                }
            if message.recipient_id == user.id and not message.is_read:
                threads[key]["unread_count"] += 1

        return Response(sorted(threads.values(), key=lambda t: t["last_message_at"], reverse=True))


class UnreadCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = Message.objects.filter(recipient=request.user, is_read=False).count()
        return Response({"count": count})
