import math

from rest_framework import serializers

from apps.listings.models import Listing

from .models import Booking


class BookingSerializer(serializers.ModelSerializer):
    listing_id = serializers.PrimaryKeyRelatedField(
        source="listing", queryset=Listing.objects.filter(is_active=True), write_only=True
    )
    listing_title = serializers.CharField(source="listing.title", read_only=True)
    price_unit = serializers.CharField(source="listing.price_unit", read_only=True)
    renter_username = serializers.CharField(source="renter.username", read_only=True)
    viewer_role = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            "id", "listing_id", "listing_title", "price_unit", "renter_username", "viewer_role",
            "start_datetime", "end_datetime", "total_price", "status", "created_at",
        ]
        read_only_fields = ["total_price", "status", "created_at"]

    def get_viewer_role(self, obj):
        request = self.context.get("request")
        if request and obj.listing.owner_id == request.user.id:
            return "seller"
        return "buyer"

    def validate(self, attrs):
        start = attrs.get("start_datetime", getattr(self.instance, "start_datetime", None))
        end = attrs.get("end_datetime", getattr(self.instance, "end_datetime", None))
        if start and end and end <= start:
            raise serializers.ValidationError("end_datetime must be after start_datetime.")
        return attrs

    def create(self, validated_data):
        listing = validated_data["listing"]
        duration = validated_data["end_datetime"] - validated_data["start_datetime"]
        if listing.price_unit == Listing.PriceUnit.HOUR:
            units = math.ceil(duration.total_seconds() / 3600)
        else:
            units = math.ceil(duration.total_seconds() / 86400)
        units = max(units, 1)
        validated_data["total_price"] = listing.price_amount * units
        validated_data["renter"] = self.context["request"].user
        return super().create(validated_data)
