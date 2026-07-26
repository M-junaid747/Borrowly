from django.contrib.auth import get_user_model
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RegisterSerializer, UserProfileSerializer, UserPublicSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserProfileSerializer(request.user).data)

    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class SwitchRoleView(APIView):
    """
    POST {"role": "seller"} or {"role": "buyer"} to switch the active
    dashboard/mode for the current user. Every account can act as both
    a buyer and a seller - this just changes which mode/dashboard/
    permissions are currently active (see listings/bookings/chat views).
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        role = request.data.get("role")
        if role not in (User.ROLE_BUYER, User.ROLE_SELLER):
            return Response({"detail": "role must be 'buyer' or 'seller'."}, status=400)
        user = request.user
        user.active_role = role
        user.save(update_fields=["active_role"])
        return Response(UserProfileSerializer(user).data)


class UserPublicDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserPublicSerializer
    permission_classes = [permissions.AllowAny]
