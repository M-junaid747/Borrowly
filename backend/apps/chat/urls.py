from django.urls import path

from .views import ConversationView, InboxView, UnreadCountView

urlpatterns = [
    path("inbox/", InboxView.as_view(), name="chat-inbox"),
    path("unread-count/", UnreadCountView.as_view(), name="chat-unread-count"),
    path("<int:listing_id>/<int:other_user_id>/", ConversationView.as_view(), name="chat-conversation"),
]
