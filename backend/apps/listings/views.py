from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Availability, Category, Listing, ListingImage
from .serializers import (
    AvailabilitySerializer,
    CategorySerializer,
    ListingDetailSerializer,
    ListingImageSerializer,
    ListingListSerializer,
)
from .utils import annotate_distance


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner_id == request.user.id


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


class ListingListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["category"]
    search_fields = ["title", "description"]

    def get_serializer_class(self):
        return ListingDetailSerializer if self.request.method == "POST" else ListingListSerializer

    def get_queryset(self):
        queryset = Listing.objects.filter(is_active=True).select_related("owner", "category").prefetch_related("images")

        min_price = self.request.query_params.get("min_price")
        max_price = self.request.query_params.get("max_price")
        if min_price:
            queryset = queryset.filter(price_amount__gte=min_price)
        if max_price:
            queryset = queryset.filter(price_amount__lte=max_price)

        lat = self.request.query_params.get("lat")
        lng = self.request.query_params.get("lng")
        if lat and lng:
            try:
                lat, lng = float(lat), float(lng)
            except ValueError as exc:
                raise ValidationError("lat/lng must be numeric") from exc
            queryset = queryset.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
            queryset = annotate_distance(queryset, lat, lng)
            radius_km = float(self.request.query_params.get("radius_km", 25))
            queryset = queryset.filter(distance_km__lte=radius_km).order_by("distance_km")
        return queryset

    def perform_create(self, serializer):
        # Listing management is a "Selling mode" action - switch modes to do it.
        if self.request.user.active_role != self.request.user.ROLE_SELLER:
            raise ValidationError("Switch to selling mode before listing an item.")
        serializer.save(owner=self.request.user)

    def get_serializer_context(self):
        return {"request": self.request}


class MyListingsView(generics.ListAPIView):
    serializer_class = ListingListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Listing.objects.filter(owner=self.request.user).select_related("owner", "category").prefetch_related("images")

    def get_serializer_context(self):
        return {"request": self.request}


class ListingDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Listing.objects.select_related("owner", "category").prefetch_related("images", "blocked_dates")
    serializer_class = ListingDetailSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]


class ListingImageUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, listing_id):
        listing = generics.get_object_or_404(Listing, id=listing_id)
        if listing.owner_id != request.user.id:
            return Response({"detail": "Not your listing."}, status=status.HTTP_403_FORBIDDEN)
        image_file = request.FILES.get("image")
        if not image_file:
            return Response({"detail": "No image provided."}, status=status.HTTP_400_BAD_REQUEST)
        image = ListingImage.objects.create(listing=listing, image=image_file)
        return Response(ListingImageSerializer(image, context={"request": request}).data, status=status.HTTP_201_CREATED)


class AvailabilityCreateView(generics.CreateAPIView):
    serializer_class = AvailabilitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        listing = generics.get_object_or_404(Listing, id=self.kwargs["listing_id"])
        if listing.owner_id != self.request.user.id:
            raise ValidationError("Not your listing.")
        serializer.save(listing=listing)
