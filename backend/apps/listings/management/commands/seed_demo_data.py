import io
import itertools
import random
import time
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

# 6 sellers + 2 buyer-only accounts, so the marketplace visibly has multiple
# independent sellers, not just one.
DEMO_USERS = [
    {"username": "alice_seller", "email": "alice@example.com", "active_role": "seller"},
    {"username": "bob_carpenter", "email": "bob@example.com", "active_role": "seller"},
    {"username": "carol_both", "email": "carol@example.com", "active_role": "seller"},
    {"username": "dan_electronics", "email": "dan@example.com", "active_role": "seller"},
    {"username": "mira_outdoors", "email": "mira@example.com", "active_role": "seller"},
    {"username": "sam_musician", "email": "sam@example.com", "active_role": "seller"},
    {"username": "zara_renter", "email": "zara@example.com", "active_role": "buyer"},
    {"username": "omar_renter", "email": "omar@example.com", "active_role": "buyer"},
]
SELLER_USERNAMES = [u["username"] for u in DEMO_USERS if u["active_role"] == "seller"]

# city -> (province, latitude, longitude) - real coordinates so the geo
# radius search has something meaningful to filter on.
CITIES = {
    "Lahore": ("Punjab", 31.5497, 74.3436),
    "Karachi": ("Sindh", 24.8607, 67.0011),
    "Islamabad": ("Islamabad Capital Territory", 33.6844, 73.0479),
    "Faisalabad": ("Punjab", 31.4504, 73.1350),
    "Multan": ("Punjab", 30.1575, 71.5249),
    "Peshawar": ("Khyber Pakhtunkhwa", 34.0151, 71.5249),
}

# One already-verified, freely-licensed Wikimedia Commons photo per category.
# Reused across every listing in that category (see _create_listings) rather
# than fetched once per listing - with 100+ listings, hitting Commons 100+
# times back-to-back is exactly what caused "some photos show, some don't"
# in the first version of this script (transient timeouts/rate-limiting on
# a handful of the many requests). Reusing ~10 cached downloads for the
# whole run removes almost all of that risk. "Other" category items rotate
# through the full pool for a bit of variety since their subjects vary.
CATEGORY_PHOTOS = {
    "tools-equipment": "CordlessDrill.jpg",
    "cameras-photography": "DSLR Camera with Lens on a Tripod head.jpg",
    "camping-outdoor": "Camping Tents in the Woods.jpg",
    "party-events": "Speaker JBL GO.jpg",
    "electronics-gadgets": "Projector in frame.jpg",
    "sports-fitness": "Mountain bike.JPG",
    "furniture-home": "Folding table and chairs (3356667238).jpg",
    "musical-instruments": "Acoustic bass guitar 1.jpg",
    "vehicles-transport": "Pressure Wash.JPG",
    "other": "Coll. Marcè CL - Polaroid land camera Mod 95 1948.jpg",
}

CATEGORY_ITEMS = {
    "tools-equipment": [
        ("Cordless Power Drill", "18V cordless drill with two batteries and a case."),
        ("Circular Saw", "7-1/4 inch circular saw, great for framing and sheet goods."),
        ("Angle Grinder", "4.5 inch angle grinder with spare cutting discs."),
        ("Impact Wrench", "Cordless impact wrench for automotive and heavy fastening work."),
        ("Bench Vice", "Heavy-duty 6 inch bench vice, clamps to any workbench."),
        ("Extension Ladder (8ft)", "Aluminum extension ladder, rated for household and light trade use."),
        ("Wet/Dry Shop Vacuum", "16-gallon shop vac for job site or garage cleanup."),
        ("Tile Cutter", "Manual tile cutter for ceramic and porcelain tile up to 24 inches."),
        ("Paint Sprayer", "Airless paint sprayer, covers a room in a fraction of the time of a roller."),
        ("Chainsaw", "Gas-powered chainsaw with 16 inch bar, recently serviced."),
        ("Belt Sander", "3x21 inch belt sander with dust bag."),
        ("Nail Gun", "Pneumatic framing nail gun, compressor not included."),
        ("Pipe Wrench Set", "Set of 3 pipe wrenches (10, 14, 18 inch)."),
        ("Concrete Mixer", "Small electric concrete mixer for patio and garden projects."),
        ("Pressure Washer", "Electric pressure washer, great for driveways, decks, and cars."),
    ],
    "cameras-photography": [
        ("Canon DSLR Camera Kit", "Canon EOS 200D with 18-55mm lens, extra battery, and a 32GB SD card."),
        ("Mirrorless Camera with Lens", "Compact mirrorless camera, great for travel and everyday shooting."),
        ("GoPro Action Camera", "Waterproof action camera with mounts for helmets, bikes, and boards."),
        ("Camera Tripod (Heavy Duty)", "Aluminum tripod, holds up to 8kg, adjustable to 170cm."),
        ("Ring Light with Stand", "18 inch ring light with phone/camera mount, dimmable."),
        ("Studio Softbox Lighting Kit", "Two softboxes on stands, ideal for product or portrait shoots."),
        ("Drone with 4K Camera", "Foldable drone with stabilized 4K camera and two batteries."),
        ("Instant Print Camera", "Instant film camera - fun for events, prints on the spot."),
        ("Camera Gimbal Stabilizer", "3-axis handheld gimbal for smooth video with your phone or camera."),
        ("Underwater Camera Housing", "Waterproof housing rated to 40m, fits most mirrorless bodies."),
        ("Telephoto Zoom Lens", "70-200mm telephoto lens, great for sports and wildlife."),
        ("Green Screen Backdrop Kit", "6x9ft collapsible green screen with stand."),
        ("External Flash Speedlite", "On-camera flash with adjustable head and diffuser."),
    ],
    "camping-outdoor": [
        ("4-Person Camping Tent", "Waterproof dome tent, sets up in under 10 minutes."),
        ("2-Person Backpacking Tent", "Ultralight tent for hikers, packs down to the size of a water bottle."),
        ("Sleeping Bag (Cold Weather)", "Rated to -5°C, machine washable."),
        ("Camping Stove (Propane)", "Two-burner propane camp stove."),
        ("Portable Camping Chairs (Set of 4)", "Folding chairs with cup holders and carry bags."),
        ("Cooler Box (60L)", "Hard-shell cooler, keeps ice for up to 4 days."),
        ("Hiking Backpack (65L)", "Multi-day hiking pack with rain cover."),
        ("Portable Water Filter", "Pump filter, removes bacteria and protozoa from stream water."),
        ("Camping Hammock", "Double hammock with tree straps included."),
        ("Inflatable Kayak", "Single-person inflatable kayak with paddle and pump."),
        ("Fishing Rod & Tackle Set", "Spinning rod and reel combo with a small tackle box."),
        ("Headlamp (Rechargeable)", "USB-rechargeable headlamp, 300 lumens."),
        ("Portable Camping Table", "Folding aluminum table, packs flat."),
    ],
    "party-events": [
        ("Bluetooth Party Speaker", "Loud portable speaker with LED lights, perfect for backyard parties."),
        ("Folding Banquet Tables (x4)", "Four 6-foot folding tables, ideal for events and gatherings."),
        ("Chiavari Chairs (Set of 10)", "Elegant chiavari chairs for weddings and formal events."),
        ("LED Dance Floor Panels", "Interlocking LED dance floor tiles, app-controlled patterns."),
        ("Photo Booth with Props", "Freestanding photo booth with backdrop and prop box."),
        ("Cotton Candy Machine", "Tabletop cotton candy machine with sugar floss and cones."),
        ("Popcorn Cart", "Vintage-style popcorn cart with warming light."),
        ("Karaoke Machine System", "Karaoke system with two wireless mics and speaker."),
        ("Balloon Arch Kit", "Balloon arch frame and pump, reusable for any event."),
        ("Outdoor Party Tent (10x20)", "Pop-up party tent with sidewalls, seats up to 40 guests underneath."),
        ("Chocolate Fountain", "3-tier chocolate fountain, serves up to 50 guests."),
        ("DJ Mixer & Turntable Set", "2-deck DJ controller with mixer, USB/Bluetooth compatible."),
        ("String Light Set (100ft)", "Warm white outdoor string lights, weatherproof."),
    ],
    "electronics-gadgets": [
        ("Projector & Screen Combo", "1080p projector with a 100-inch pull-up screen."),
        ("Portable Power Station", "1000Wh power station, great for camping or backup power."),
        ("Gaming Console (Latest Gen)", "Console with two controllers and three games."),
        ("VR Headset", "Standalone VR headset with two controllers."),
        ("Noise-Cancelling Headphones", "Over-ear ANC headphones, great for travel or focus work."),
        ("Portable Air Conditioner", "Portable AC unit for a single room, window vent kit included."),
        ("3D Printer", "FDM 3D printer, beginner-friendly with a heated bed."),
        ("Smart Home Hub Kit", "Hub plus 3 smart plugs and a motion sensor."),
        ("Handheld Steamer", "Garment steamer for events or quick touch-ups."),
        ("Laptop (Business Grade)", "Lightweight laptop, good for presentations or remote work."),
        ("External Monitor (27-inch)", "1440p monitor with HDMI and USB-C input."),
        ("Bluetooth PA System", "Compact PA system with wireless mic, good for small talks."),
    ],
    "sports-fitness": [
        ("Mountain Bike (Large)", "27-speed mountain bike, recently serviced, helmet included."),
        ("Road Bike (Medium)", "Lightweight road bike, good for long rides."),
        ("Treadmill (Foldable)", "Foldable treadmill for home use, up to 12km/h."),
        ("Kayak (Single Person)", "Sit-on-top kayak with paddle."),
        ("Stand-Up Paddleboard", "Inflatable SUP with pump, paddle, and leash."),
        ("Snowboard with Bindings", "All-mountain snowboard, bindings included, boots not included."),
        ("Golf Club Set", "Full set of clubs with a stand bag."),
        ("Tennis Racket Set (x2)", "Two rackets and a tube of balls."),
        ("Rock Climbing Harness Kit", "Harness, helmet, and belay device for indoor/outdoor climbing."),
        ("Yoga Mat & Block Set", "Non-slip mat with two blocks and a strap."),
        ("Adjustable Dumbbell Set", "Pair of adjustable dumbbells, 5-25kg each."),
        ("Camping Cot", "Folding camp cot, holds up to 130kg."),
    ],
    "furniture-home": [
        ("Folding Guest Bed", "Folding guest bed with mattress, sets up in under a minute."),
        ("Office Desk (Standing)", "Electric height-adjustable standing desk."),
        ("Bookshelf (5-Tier)", "Sturdy 5-tier bookshelf, easy to disassemble for transport."),
        ("Patio Furniture Set", "2 chairs and a small table, weatherproof."),
        ("Area Rug (8x10)", "Neutral-tone area rug, great for staging or short-term use."),
        ("Dining Table (Extendable)", "Seats 4-8 with the extension leaf in."),
        ("Recliner Chair", "Comfortable fabric recliner, one owner."),
        ("Storage Ottoman", "Ottoman with hidden storage, doubles as extra seating."),
        ("Bunk Bed Frame", "Metal bunk bed frame, mattresses not included."),
        ("Vacuum Cleaner (Cordless)", "Cordless stick vacuum, good for a quick deep clean."),
        ("Air Purifier", "HEPA air purifier, covers rooms up to 40 sq m."),
        ("Space Heater", "Electric space heater with tip-over safety shutoff."),
    ],
    "vehicles-transport": [
        ("Electric Scooter", "Foldable electric scooter, ~25km range per charge."),
        ("Cargo Trailer (Small)", "Small utility trailer, good for moving furniture or yard waste."),
        ("Roof Rack Cargo Box", "Hard-shell roof box, fits most crossbar systems."),
        ("Electric Bike (E-Bike)", "Pedal-assist e-bike, good for commuting."),
        ("Car Jump Starter Kit", "Portable jump starter with air compressor and USB ports."),
        ("Motorcycle Helmet (Full Face)", "DOT-rated full-face helmet, size medium."),
        ("Dashcam (Dual Channel)", "Front and rear dashcam with night vision."),
        ("Car Roof Tent", "Hard-shell rooftop tent, sets up in a few minutes."),
        ("Tow Hitch Cargo Carrier", "Hitch-mounted cargo carrier, foldable when not in use."),
        ("Utility Trailer", "Open utility trailer, good for hauling bikes or gear."),
        ("Car Vacuum (Portable)", "Corded car vacuum with several attachments."),
        ("Roof Bike Rack", "Fork-mount roof bike rack, fits one bike."),
    ],
    "musical-instruments": [
        ("Acoustic Guitar", "Full-size acoustic guitar with a soft case and spare strings."),
        ("Electric Guitar with Amp", "Electric guitar plus a small practice amp."),
        ("Digital Piano (88-Key)", "Weighted 88-key digital piano with sustain pedal."),
        ("Drum Kit (Full Set)", "5-piece drum kit with cymbals and stool."),
        ("Violin (Full Size)", "Full-size violin with bow and case."),
        ("Saxophone (Alto)", "Alto sax, recently serviced, reeds included."),
        ("DJ Controller", "2-channel DJ controller, works with most DJ software."),
        ("Ukulele", "Concert-size ukulele with gig bag."),
        ("Portable PA Speaker for Gigs", "Battery-powered PA speaker with mixer input, good for small gigs."),
        ("Microphone & Stand Kit", "Dynamic mic, stand, and XLR cable."),
        ("Keyboard Synthesizer", "61-key synth with built-in sounds and sequencer."),
        ("Cajon Percussion Box", "Cajon drum box with adjustable snare."),
    ],
    "other": [
        ("Vintage Polaroid Camera", "Working vintage instant camera - a fun, unusual rental for photoshoots or events.", "Vintage Cameras"),
        ("Superhero Costume Set", "Adult-size costume set, good for parties or cosplay events.", "Costumes"),
        ("Board Game Collection (10 games)", "A curated box of 10 popular board games for game night.", "Board Games"),
        ("Aquarium Setup (20 Gallon)", "Complete 20 gallon aquarium with filter and light, fish not included.", "Aquariums"),
        ("Telescope (Beginner)", "Beginner-friendly telescope, good for viewing the moon and planets.", "Telescopes"),
        ("Sewing Machine", "Basic sewing machine, good for hemming and small projects.", "Sewing Equipment"),
        ("Metal Detector", "Entry-level metal detector, headphones included.", "Metal Detectors"),
        ("Tabletop Arcade Machine", "Countertop arcade machine with 60 classic games built in.", "Arcade Machines"),
        ("Beekeeping Suit & Tools", "Full beekeeping suit, smoker, and hive tool.", "Beekeeping Gear"),
        ("Antique Typewriter", "Working antique typewriter, great as a prop or for enthusiasts.", "Vintage Typewriters"),
    ],
}

PALETTE = ["#0F6E5C", "#14A97F", "#E88C2E", "#2F6690", "#8E5B3F", "#5B6B62"]


class Command(BaseCommand):
    help = "Seed the database with several demo accounts and ~125 listings across every category."

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
            count = self._create_listings(users)

        self.stdout.write(self.style.SUCCESS(f"Demo data ready: {len(DEMO_USERS)} accounts, {count} listings."))
        self.stdout.write(f"All accounts share the password: {DEMO_PASSWORD}")
        self.stdout.write(f"Sellers: {', '.join(SELLER_USERNAMES)}")
        self.stdout.write("Buyer-only: zara_renter, omar_renter")

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
        sellers = itertools.cycle(SELLER_USERNAMES)
        cities = itertools.cycle(CITIES.items())
        other_photo_pool = itertools.cycle(CATEGORY_PHOTOS.values())
        image_cache = {}
        created_count = 0

        for category_slug, items in CATEGORY_ITEMS.items():
            category = Category.objects.get(slug=category_slug)

            for item in items:
                title, description = item[0], item[1]
                custom_category = item[2] if len(item) > 2 else ""
                owner = users[next(sellers)]
                city, (province, lat, lng) = next(cities)

                listing, created = Listing.objects.get_or_create(
                    owner=owner,
                    title=title,
                    defaults={
                        "description": description,
                        "category": category,
                        "custom_category": custom_category,
                        "price_amount": random.choice([4, 5, 6, 8, 9, 10, 12, 15, 20]),
                        "price_unit": random.choice(["hour", "day"]),
                        "city": city,
                        "province": province,
                        "latitude": lat,
                        "longitude": lng,
                    },
                )
                if not created:
                    self.stdout.write(f"Listing '{title}' already exists, skipping")
                    continue

                commons_file = next(other_photo_pool) if category_slug == "other" else CATEGORY_PHOTOS[category_slug]
                image_bytes = self._cached_download(commons_file, image_cache)
                image_file = (
                    ContentFile(image_bytes, name=f"{commons_file.rsplit('.', 1)[0].lower().replace(' ', '-')}.jpg")
                    if image_bytes
                    else self._placeholder_image(title)
                )
                listing.images.create(image=image_file)
                created_count += 1

        return created_count

    def _cached_download(self, commons_filename, cache):
        """
        Downloads a real, freely-licensed photo from Wikimedia Commons via
        its Special:FilePath redirect (Commons' own supported hotlinking
        mechanism), with retries. Results are cached by filename so a photo
        shared by many listings (one per category) is only ever downloaded
        once per run, not once per listing - this is what keeps ~125
        listings resilient instead of making ~125 fragile individual calls.
        Returns None (never raises) if every attempt fails, so the caller
        can fall back to a generated placeholder.
        """
        if commons_filename in cache:
            return cache[commons_filename]

        url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{quote(commons_filename)}"
        last_exc = None
        for attempt in range(3):
            try:
                response = requests.get(url, timeout=10, headers={"User-Agent": "Borrowly-demo-seed/1.0"})
                response.raise_for_status()
                cache[commons_filename] = response.content
                return response.content
            except requests.RequestException as exc:
                last_exc = exc
                time.sleep(1.5 * (attempt + 1))

        self.stdout.write(self.style.WARNING(f"Could not fetch '{commons_filename}' after 3 attempts ({last_exc}); using a placeholder instead."))
        cache[commons_filename] = None
        return None

    def _placeholder_image(self, title):
        """Fallback only: a simple colored placeholder photo, used if the real photo download fails for every retry."""
        color = random.choice(PALETTE)
        img = Image.new("RGB", (640, 480), color=color)
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 32)
        except OSError:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), title, font=font)
        text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((640 - text_w) / 2, (480 - text_h) / 2), title, fill="white", font=font)

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        filename = f"{title.lower().replace(' ', '-').replace('/', '-')}.jpg"
        return ContentFile(buffer.getvalue(), name=filename)