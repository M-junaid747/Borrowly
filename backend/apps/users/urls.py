from django.urls import path

from .views import MeView, RegisterView, SwitchRoleView, UserPublicDetailView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="user-register"),
    path("me/", MeView.as_view(), name="user-me"),
    path("me/role/", SwitchRoleView.as_view(), name="user-switch-role"),
    path("<int:pk>/", UserPublicDetailView.as_view(), name="user-public-detail"),
]
