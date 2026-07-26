import io
import random

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from PIL import Image, ImageDraw, ImageFont

from apps.listings.models import Category, Listing

User = get_user_model()

DEMO_PASSWORD = "DemoPass123!"

DEMO_USERS = [
    {"username": "alice_seller", "email": "alice@example.com", "active_role": "seller"},
    {"username": "bob_renter", "email": "bob@example.com", "active_role": "buyer"},
    {"username": "carol_both", "email": "carol@example.com", "active_role": "seller"},
]

# (owner_username, title, description, category_slug, price_amount, price_unit, city, province, [custom_category])
DEMO_LISTINGS = [
    ("alice_seller", "Cordless Power Drill", "18V cordless drill with two batteries and a case. Great for hanging shelves or small home projects.", "tools-equipment", 8, "day", "Lahore", "Punjab"),
    ("alice_seller", "Canon DSLR Camera Kit", "Canon EOS 200D with 18-55mm lens, extra battery, and a 32GB SD card.", "cameras-photography", 12, "day", "Lahore", "Punjab"),
    ("alice_seller", "4-Person Camping Tent", "Waterproof dome tent, sets up in under 10 minutes. Includes stakes and rainfly.", "camping-outdoor", 6, "day", "Lahore", "Punjab"),
    ("alice_seller", "Bluetooth Party Speaker", "Loud portable speaker with LED lights, perfect for backyard parties.", "party-events", 5, "hour", "Lahore", "Punjab"),
    ("carol_both", "Projector & Screen Combo", "1080p projector with a 100-inch pull-up screen. Great for movie nights or presentations.", "electronics-gadgets", 4, "hour", "Karachi", "Sindh"),
    ("carol_both", "Mountain Bike (Large)", "27-speed mountain bike, recently serviced, helmet included.", "sports-fitness", 10, "day", "Karachi", "Sindh"),
    ("carol_both", "Folding Banquet Tables (x4)", "Four 6-foot folding tables, ideal for events and gatherings.", "party-events", 15, "day", "Karachi", "Sindh"),
    ("carol_both", "Acoustic Guitar", "Full-size acoustic guitar with a soft case and spare strings.", "musical-instruments", 5, "day", "Karachi", "Sindh"),
    ("carol_both", "Pressure Washer", "Electric pressure washer, great for driveways, decks, and cars.", "tools-equipment", 9, "day", "Karachi", "Sindh"),
    ("alice_seller", "Vintage Polaroid Camera", "Working vintage instant camera - a fun, unusual rental for photoshoots or events.", "other", 20, "day", "Lahore", "Punjab", "Vintage Cameras"),
]

PALETTE = ["#0F6E5C", "#14A97F", "#E88C2E", "#2F6690", "#8E5B3F", "#5B6B62"]


class Command(BaseCommand):
    help = "Seed the database with demo accounts and listings so a fresh deployment has content to show."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing demo users (and their listings, via cascade) first, then recreate everything.",
        )

    def handle(self, *args, **options):
        if Category.objects.count() == 0:
            self.stdout.write("No categories found - loading the categories fixture first…")
            call_command("loaddata", "categories")

        if options["reset"]:
            User.objects.filter(username__in=[u["username"] for u in DEMO_USERS]).delete()
            self.stdout.write(self.style.WARNING("Deleted existing demo users (and their listings)."))

        with transaction.atomic():
            users = self._create_users()
            self._create_listings(users)

        self.stdout.write(self.style.SUCCESS("Demo data ready: 3 accounts, 10 listings."))
        self.stdout.write(f"Login with any of: {', '.join(u['username'] for u in DEMO_USERS)} / password: {DEMO_PASSWORD}")

    def _create_users(self):
        users = {}
        for spec in DEMO_USERS:
            user, created = User.objects.get_or_create(
                username=spec["username"],
                defaults={"email": spec["email"], "active_role": spec["active_role"]},
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()
                self.stdout.write(f"Created user '{user.username}'")
            else:
                self.stdout.write(f"User '{user.username}' already exists, reusing it")
            users[spec["username"]] = user
        return users

    def _create_listings(self, users):
        for entry in DEMO_LISTINGS:
            owner_username, title, description, category_slug, price_amount, price_unit, city, province = entry[:8]
            custom_category = entry[8] if len(entry) > 8 else ""

            owner = users[owner_username]
            category = Category.objects.get(slug=category_slug)

            listing, created = Listing.objects.get_or_create(
                owner=owner,
                title=title,
                defaults={
                    "description": description,
                    "category": category,
                    "custom_category": custom_category,
                    "price_amount": price_amount,
                    "price_unit": price_unit,
                    "city": city,
                    "province": province,
                },
            )
            if not created:
                self.stdout.write(f"Listing '{title}' already exists, skipping")
                continue

            listing.images.create(image=self._placeholder_image(title))
            self.stdout.write(f"Created listing '{title}' for {owner_username}")

    def _placeholder_image(self, title):
        """Generates a simple colored placeholder photo so listing cards aren't empty - no external downloads needed."""
        color = random.choice(PALETTE)
        img = Image.new("RGB", (640, 480), color=color)
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
        except OSError:
            font = ImageFont.load_default()

        text = title
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((640 - text_w) / 2, (480 - text_h) / 2), text, fill="white", font=font)

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        filename = f"{title.lower().replace(' ', '-')}.jpg"
        return ContentFile(buffer.getvalue(), name=filename)