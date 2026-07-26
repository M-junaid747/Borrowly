from rest_framework import generics, permissions

from .models import Review
from .serializers import ReviewSerializer


class ReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Review.objects.select_related("reviewer", "reviewee", "booking")
        reviewee_id = self.request.query_params.get("reviewee")
        if reviewee_id:
            queryset = queryset.filter(reviewee_id=reviewee_id)
        return queryset
