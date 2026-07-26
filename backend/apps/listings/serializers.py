from rest_framework import serializers

from apps.users.serializers import UserPublicSerializer

from .models import Availability, Category, Listing, ListingImage


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "is_other"]


class ListingImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingImage
        fields = ["id", "image", "uploaded_at"]


class AvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Availability
        fields = ["id", "start_date", "end_date"]


class ListingListSerializer(serializers.ModelSerializer):
    owner = UserPublicSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    category_label = serializers.CharField(read_only=True)
    thumbnail = serializers.SerializerMethodField()
    distance_km = serializers.FloatField(read_only=True, required=False)

    class Meta:
        model = Listing
        fields = [
            "id", "title", "price_amount", "price_unit", "city", "province",
            "latitude", "longitude", "owner", "category", "category_label",
            "thumbnail", "distance_km",
        ]

    def get_thumbnail(self, obj):
        first_image = obj.images.first()
        if first_image:
            request = self.context.get("request")
            url = first_image.image.url
            return request.build_absolute_uri(url) if request else url
        return None


class ListingDetailSerializer(serializers.ModelSerializer):
    owner = UserPublicSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        source="category", queryset=Category.objects.all(), write_only=True
    )
    category_label = serializers.CharField(read_only=True)
    images = ListingImageSerializer(many=True, read_only=True)
    blocked_dates = AvailabilitySerializer(many=True, read_only=True)

    class Meta:
        model = Listing
        fields = [
            "id", "owner", "category", "category_id", "category_label", "custom_category",
            "title", "description", "price_amount", "price_unit",
            "city", "province", "address", "latitude", "longitude", "location_link",
            "is_active", "images", "blocked_dates", "created_at",
        ]
        read_only_fields = ["owner", "created_at"]

    def validate(self, attrs):
        category = attrs.get("category", getattr(self.instance, "category", None))
        custom_category = attrs.get("custom_category", getattr(self.instance, "custom_category", ""))
        if category and category.is_other and not custom_category:
            raise serializers.ValidationError(
                {"custom_category": "Enter a category name since you selected 'Other'."}
            )
        return attrs

    def create(self, validated_data):
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)
