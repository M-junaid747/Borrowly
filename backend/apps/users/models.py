from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_BUYER = "buyer"
    ROLE_SELLER = "seller"
    ACTIVE_ROLE_CHOICES = [(ROLE_BUYER, "Buyer"), (ROLE_SELLER, "Seller")]

    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    rating_count = models.PositiveIntegerField(default=0)
    # Every account can both buy and sell. active_role only controls which
    # mode/dashboard is currently active (see SwitchRoleView) - it is not a
    # permission gate.
    active_role = models.CharField(max_length=10, choices=ACTIVE_ROLE_CHOICES, default=ROLE_BUYER)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

    def recalculate_rating(self):
        """Recompute average_rating from all reviews received by this user."""
        from apps.reviews.models import Review

        reviews = Review.objects.filter(reviewee=self)
        count = reviews.count()
        if count == 0:
            self.average_rating = 0
            self.rating_count = 0
        else:
            total = sum(r.rating for r in reviews)
            self.average_rating = round(total / count, 2)
            self.rating_count = count
        self.save(update_fields=["average_rating", "rating_count"])
