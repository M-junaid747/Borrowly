from rest_framework import serializers

from apps.bookings.models import Booking

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    booking_id = serializers.PrimaryKeyRelatedField(source="booking", queryset=Booking.objects.all(), write_only=True)
    reviewer_username = serializers.CharField(source="reviewer.username", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "booking_id", "reviewer_username", "reviewee", "rating", "comment", "created_at"]
        read_only_fields = ["created_at"]

    def validate(self, attrs):
        booking = attrs["booking"]
        request_user = self.context["request"].user
        if booking.status != Booking.Status.COMPLETED:
            raise serializers.ValidationError("You can only review completed bookings.")
        if request_user.id not in (booking.renter_id, booking.listing.owner_id):
            raise serializers.ValidationError("You are not part of this booking.")
        if hasattr(booking, "review"):
            raise serializers.ValidationError("This booking has already been reviewed.")
        return attrs

    def create(self, validated_data):
        validated_data["reviewer"] = self.context["request"].user
        review = super().create(validated_data)
        review.reviewee.recalculate_rating()
        return review
