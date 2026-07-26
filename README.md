# Borrowly — Peer-to-Peer Item Rental Platform

A location-based marketplace where people rent out everyday items they own but
rarely use — tools, cameras, camping gear, party supplies, electronics — to
others nearby, and rent from others in return. One account, two modes: switch
between **Buying** and **Selling** anytime.

## Features

- **JWT authentication** — register once, use the same account to buy or sell
- **Buyer / Seller mode switch** — a single account can browse & rent, or list
  & manage items, with permissions enforced per mode on the backend
- **Flexible pricing** — sellers price per hour or per day, seller's choice
- **Location-based search** — radius search by distance (Haversine, no PostGIS
  required), plus city/province/address, optional coordinates, and an
  optional Google Maps link per listing
- **Multi-photo listings** across 9 categories + a custom "Other" category
- **In-app chat** — real inbox grouped by conversation, unread-message
  tracking, polling-based near-real-time updates
- **Booking workflow** — request → owner confirms/declines → dummy checkout
  → paid, with total price computed from the listing's own pricing unit
- **Ratings & reviews** tied to completed bookings
- **Django admin** for moderation and data inspection

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Django, Django REST Framework, SimpleJWT |
| Database | PostgreSQL (production) / SQLite (local dev) |
| Frontend | React (Vite), React Router |
| Images | Pillow (demo data), Django `ImageField` uploads |
| Payments | Dummy checkout included; Stripe Checkout wired but optional |
| Hosting | Render (backend + Postgres), Netlify (frontend) |

## Project Structure

\```
item-rental-platform/
├── backend/
│   ├── config/                  # Django settings, root URLs
│   ├── apps/
│   │   ├── users/                # Auth, profiles, buyer/seller mode
│   │   ├── listings/              # Categories, listings, images, geo search
│   │   ├── bookings/              # Booking workflow, dummy checkout
│   │   ├── chat/                  # Messaging, inbox, unread tracking
│   │   └── reviews/                # Ratings & reviews
│   ├── requirements.txt
│   ├── build.sh                  # Render build/deploy script
│   └── Procfile
└── frontend/
    ├── src/
    │   ├── pages/                 # Home, Login, Register, Dashboard, etc.
    │   ├── components/            # NavBar, ListingCard, ChatThread, etc.
    │   └── api.js                 # API client
    ├── netlify.toml
    └── package.json
\```

## Local Development

**Backend**
\```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # edit SECRET_KEY at minimum
python manage.py migrate
python manage.py loaddata categories
python manage.py seed_demo_data   # optional: 3 demo accounts + 10 listings
python manage.py runserver
\```
Runs at `http://localhost:8000`. Admin at `/admin/` (create one with `python manage.py createsuperuser`).

**Frontend**
\```bash
cd frontend
npm install
cp .env.example .env              # VITE_API_BASE_URL=http://localhost:8000/api
npm run dev
\```
Runs at `http://localhost:5173`.

**Tests**
\```bash
cd backend && source venv/bin/activate
python manage.py test
\```

## Demo Data

Running `python manage.py seed_demo_data` creates 3 accounts and 10 listings so the app has content to show immediately:

| Username | Password | Mode |
|---|---|---|
| `alice_seller` | `DemoPass123!` | Seller (5 listings) |
| `bob_renter` | `DemoPass123!` | Buyer (no listings — good for testing booking/chat) |
| `carol_both` | `DemoPass123!` | Seller (5 listings) — try switching to Buying mode too |

Safe to re-run (idempotent); use `--reset` to wipe and recreate the demo accounts.

## Environment Variables

**`backend/.env`**

| Variable | Notes |
|---|---|
| `SECRET_KEY` | Any long random string |
| `DEBUG` | `True` locally, `False` in production |
| `ALLOWED_HOSTS` | Comma-separated, e.g. `localhost,yourapp.onrender.com` |
| `DATABASE_URL` | Empty = SQLite locally; Postgres URL in production |
| `CORS_ALLOWED_ORIGINS` | Your frontend's URL |
| `STRIPE_SECRET_KEY` | Optional — only needed for the real Stripe checkout path |

**`frontend/.env`**

| Variable | Notes |
|---|---|
| `VITE_API_BASE_URL` | Backend API root, ending in `/api` |

## Deployment

Backend on **Render** (free web service + free Postgres, reads `build.sh`/`Procfile` natively), frontend on **Netlify** (free static hosting for the Vite build).

1. Push this repo to GitHub.
2. Render → New Web Service → root directory `backend` → build command `./build.sh` → start command `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`.
3. Attach a free Render Postgres instance as `DATABASE_URL`.
4. Netlify → New site from Git → base directory `frontend` → publish directory `frontend/dist`.
5. Set `VITE_API_BASE_URL` on Netlify and `CORS_ALLOWED_ORIGINS`/`ALLOWED_HOSTS` on Render to match each other's live URLs.

## License

Not yet specified. Add a `LICENSE` file (e.g. MIT) before treating this as open source.