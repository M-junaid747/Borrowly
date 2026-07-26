import re

import stripe
from django.conf import settings
from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Booking
from .serializers import BookingSerializer

stripe.api_key = settings.STRIPE_SECRET_KEY


class BookingListCreateView(generics.ListCreateAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Show bookings where the user is either the renter or the item owner.
        return Booking.objects.filter(
            Q(renter=user) | Q(listing__owner=user)
        ).select_related("listing", "renter")

    def perform_create(self, serializer):
        # Requesting a rental is a "Buying mode" action.
        if self.request.user.active_role != self.request.user.ROLE_BUYER:
            raise ValidationError("Switch to buying mode before requesting a booking.")
        serializer.save()


class BookingDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Booking.objects.select_related("listing", "renter")

    def perform_update(self, serializer):
        booking = self.get_object()
        user = self.request.user
        new_status = self.request.data.get("status")
        if new_status and new_status != booking.status:
            is_owner = booking.listing.owner_id == user.id
            is_renter = booking.renter_id == user.id
            allowed_by_owner = {"confirmed", "cancelled"}
            allowed_by_renter = {"cancelled"}
            if new_status in allowed_by_owner and is_owner:
                pass
            elif new_status in allowed_by_renter and is_renter:
                pass
            else:
                raise PermissionDenied("You cannot set this booking to that status.")
            serializer.save(status=new_status)
            return
        serializer.save()


CARD_NUMBER_RE = re.compile(r"^\d{13,19}$")
EXPIRY_RE = re.compile(r"^(0[1-9]|1[0-2])/\d{2}$")
CVV_RE = re.compile(r"^\d{3,4}$")


class DummyCheckoutView(APIView):
    """
    A fake payment gateway for the MVP: validates card-shaped input (format
    only - nothing is charged, verified, or stored) and marks the booking
    'paid'. Swap this out for CreateCheckoutSessionView below once a real
    payment provider is wired up.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, booking_id):
        booking = generics.get_object_or_404(Booking, id=booking_id)
        if booking.renter_id != request.user.id:
            return Response({"detail": "Not your booking."}, status=status.HTTP_403_FORBIDDEN)
        if booking.status != Booking.Status.CONFIRMED:
            return Response({"detail": "Booking must be confirmed by the owner first."}, status=status.HTTP_400_BAD_REQUEST)

        card_number = str(request.data.get("card_number", "")).replace(" ", "")
        expiry = str(request.data.get("expiry", ""))
        cvv = str(request.data.get("cvv", ""))
        name_on_card = str(request.data.get("name_on_card", "")).strip()

        errors = {}
        if not name_on_card:
            errors["name_on_card"] = "Required."
        if not CARD_NUMBER_RE.match(card_number):
            errors["card_number"] = "Enter a 13-19 digit card number."
        if not EXPIRY_RE.match(expiry):
            errors["expiry"] = "Use MM/YY format."
        if not CVV_RE.match(cvv):
            errors["cvv"] = "Enter a 3-4 digit CVV."
        if errors:
            raise ValidationError(errors)

        # Nothing above is persisted - this endpoint never touches real card
        # rails, it just simulates a successful charge for demo purposes.
        booking.status = Booking.Status.PAID
        booking.save(update_fields=["status"])
        return Response(BookingSerializer(booking, context={"request": request}).data)


class CreateCheckoutSessionView(APIView):
    """
    Creates a Stripe Checkout session for an already-confirmed booking.
    Requires STRIPE_SECRET_KEY to be set; on success the renter is redirected
    to Stripe's hosted payment page. Not wired into the frontend by default -
    use this once a real Stripe account replaces the dummy checkout.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, booking_id):
        booking = generics.get_object_or_404(Booking, id=booking_id)
        if booking.renter_id != request.user.id:
            return Response({"detail": "Not your booking."}, status=status.HTTP_403_FORBIDDEN)
        if booking.status != Booking.Status.CONFIRMED:
            return Response({"detail": "Booking must be confirmed by the owner first."}, status=status.HTTP_400_BAD_REQUEST)
        if not settings.STRIPE_SECRET_KEY:
            return Response({"detail": "Stripe is not configured on this server."}, status=status.HTTP_501_NOT_IMPLEMENTED)

        success_url = request.data.get("success_url", "http://localhost:5173/dashboard?success=true")
        cancel_url = request.data.get("cancel_url", "http://localhost:5173/dashboard?success=false")

        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": f"Rental: {booking.listing.title}"},
                    "unit_amount": int(booking.total_price * 100),
                },
                "quantity": 1,
            }],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"booking_id": booking.id},
        )
        booking.stripe_checkout_session_id = session.id
        booking.save(update_fields=["stripe_checkout_session_id"])
        return Response({"checkout_url": session.url})
