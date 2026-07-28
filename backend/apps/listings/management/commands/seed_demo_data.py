import io
import random
from urllib.parse import quote

import requests
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

# Each entry: owner, title, description, category slug, price, unit, city,
# province, [custom_category], commons_file (a real, freely-licensed photo
# filename on Wikimedia Commons - fetched via the Special:FilePath redirect,
# which is Commons' own stable hotlinking mechanism).
DEMO_LISTINGS = [
    {
        "owner": "alice_seller", "title": "Cordless Power Drill",
        "description": "18V cordless drill with two batteries and a case. Great for hanging shelves or small home projects.",
        "category_slug": "tools-equipment", "price_amount": 8, "price_unit": "day",
        "city": "Lahore", "province": "Punjab", "commons_file": "CordlessDrill.jpg",
    },
    {
        "owner": "alice_seller", "title": "Canon DSLR Camera Kit",
        "description": "Canon EOS 200D with 18-55mm lens, extra battery, and a 32GB SD card.",
        "category_slug": "cameras-photography", "price_amount": 12, "price_unit": "day",
        "city": "Lahore", "province": "Punjab", "commons_file": "DSLR Camera with Lens on a Tripod head.jpg",
    },
    {
        "owner": "alice_seller", "title": "4-Person Camping Tent",
        "description": "Waterproof dome tent, sets up in under 10 minutes. Includes stakes and rainfly.",
        "category_slug": "camping-outdoor", "price_amount": 6, "price_unit": "day",
        "city": "Lahore", "province": "Punjab", "commons_file": "Camping Tents in the Woods.jpg",
    },
    {
        "owner": "alice_seller", "title": "Bluetooth Party Speaker",
        "description": "Loud portable speaker with LED lights, perfect for backyard parties.",
        "category_slug": "party-events", "price_amount": 5, "price_unit": "hour",
        "city": "Lahore", "province": "Punjab", "commons_file": "Speaker JBL GO.jpg",
    },
    {
        "owner": "carol_both", "title": "Projector & Screen Combo",
        "description": "1080p projector with a 100-inch pull-up screen. Great for movie nights or presentations.",
        "category_slug": "electronics-gadgets", "price_amount": 4, "price_unit": "hour",
        "city": "Karachi", "province": "Sindh", "commons_file": "Projector in frame.jpg",
    },
    {
        "owner": "carol_both", "title": "Mountain Bike (Large)",
        "description": "27-speed mountain bike, recently serviced, helmet included.",
        "category_slug": "sports-fitness", "price_amount": 10, "price_unit": "day",
        "city": "Karachi", "province": "Sindh", "commons_file": "Mountain bike.JPG",
    },
    {
        "owner": "carol_both", "title": "Folding Banquet Tables (x4)",
        "description": "Four 6-foot folding tables, ideal for events and gatherings.",
        "category_slug": "party-events", "price_amount": 15, "price_unit": "day",
        "city": "Karachi", "province": "Sindh", "commons_file": "Folding table and chairs (3356667238).jpg",
    },
    {
        "owner": "carol_both", "title": "Acoustic Guitar",
        "description": "Full-size acoustic guitar with a soft case and spare strings.",
        "category_slug": "musical-instruments", "price_amount": 5, "price_unit": "day",
        "city": "Karachi", "province": "Sindh", "commons_file": "Acoustic bass guitar 1.jpg",
    },
    {
        "owner": "carol_both", "title": "Pressure Washer",
        "description": "Electric pressure washer, great for driveways, decks, and cars.",
        "category_slug": "tools-equipment", "price_amount": 9, "price_unit": "day",
        "city": "Karachi", "province": "Sindh", "commons_file": "Pressure Wash.JPG",
    },
    {
        "owner": "alice_seller", "title": "Vintage Polaroid Camera",
        "description": "Working vintage instant camera - a fun, unusual rental for photoshoots or events.",
        "category_slug": "other", "custom_category": "Vintage Cameras",
        "price_amount": 20, "price_unit": "day", "city": "Lahore", "province": "Punjab",
        "commons_file": "Coll. Marcè CL - Polaroid land camera Mod 95 1948.jpg",
    },
]

PALETTE = ["#0F6E5C", "#14A97F", "#E88C2E", "#2F6690", "#8E5B3F", "#5B6B62"]


class Command(BaseCommand):
    help = "Seed the database with demo accounts and listings (with real product photos) so a fresh deployment has content to show."

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
        for item in DEMO_LISTINGS:
            owner = users[item["owner"]]
            category = Category.objects.get(slug=item["category_slug"])

            listing, created = Listing.objects.get_or_create(
                owner=owner,
                title=item["title"],
                defaults={
                    "description": item["description"],
                    "category": category,
                    "custom_category": item.get("custom_category", ""),
                    "price_amount": item["price_amount"],
                    "price_unit": item["price_unit"],
                    "city": item["city"],
                    "province": item["province"],
                },
            )
            if not created:
                self.stdout.write(f"Listing '{item['title']}' already exists, skipping")
                continue

            image_file = self._real_photo(item["commons_file"]) or self._placeholder_image(item["title"])
            listing.images.create(image=image_file)
            self.stdout.write(f"Created listing '{item['title']}' for {item['owner']}")

    def _real_photo(self, commons_filename):
        """
        Downloads a real, freely-licensed photo from Wikimedia Commons via
        its Special:FilePath redirect (Commons' own supported hotlinking
        mechanism - stable regardless of the file's internal storage hash).
        Returns None on any failure so the caller can fall back to a
        generated placeholder instead of crashing the whole seed run.
        """
        url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{quote(commons_filename)}"
        try:
            response = requests.get(url, timeout=10, headers={"User-Agent": "Borrowly-demo-seed/1.0"})
            response.raise_for_status()
            extension = "png" if "png" in response.headers.get("Content-Type", "") else "jpg"
            filename = f"{commons_filename.rsplit('.', 1)[0].lower().replace(' ', '-')}.{extension}"
            return ContentFile(response.content, name=filename)
        except requests.RequestException as exc:
            self.stdout.write(self.style.WARNING(f"Could not fetch '{commons_filename}' ({exc}); using a placeholder instead."))
            return None

    def _placeholder_image(self, title):
        """Fallback only: a simple colored placeholder photo, used if the real photo download fails for any reason."""
        color = random.choice(PALETTE)
        img = Image.new("RGB", (640, 480), color=color)
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
        except OSError:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), title, font=font)
        text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((640 - text_w) / 2, (480 - text_h) / 2), title, fill="white", font=font)

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        filename = f"{title.lower().replace(' ', '-')}.jpg"
        return ContentFile(buffer.getvalue(), name=filename)