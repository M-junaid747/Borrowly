from rest_framework import serializers

from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source="sender.username", read_only=True)

    class Meta:
        model = Message
        fields = ["id", "listing", "sender", "sender_username", "recipient", "body", "is_read", "created_at"]
        read_only_fields = ["sender", "listing", "recipient", "is_read", "created_at"]

    def create(self, validated_data):
        validated_data["sender"] = self.context["request"].user
        return super().create(validated_data)
