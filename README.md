# Barber Booking Bot

Telegram bot for barber shops with:

- customer self-booking
- shop-admin booking management
- super-admin shop provisioning
- PostgreSQL-backed schedules and bookings
- reminder worker loop

## Main Features

- Deep-link entry per shop: `?start=shopcode_<id>`
- Multi-shop support
- Customer phone capture and booking history
- Admin service management
- Per-barber schedule editing
- Quick temporary time blocking
- DB-level booking overlap protection

## Required Environment Variables

- `TELEGRAM_BOT_TOKEN`
- `DATABASE_URL`

## Optional Environment Variables

- `REDIS_URL`
- `OWNER_TELEGRAM_IDS`
- `REMINDER_LOOP_ENABLED`

## Run Locally

```bash
pip install -r requirements.txt
python bot.py
```

## Deploy on Railway

This bot runs as a long-running worker, not a web server. Railway can start it with:

```bash
python bot.py
```

The repository includes `railway.toml` with that start command.

Required Railway variables:

- `APP_ENV=production`
- `TELEGRAM_BOT_TOKEN`
- `DATABASE_URL`
- `REDIS_URL`
- `OWNER_TELEGRAM_IDS`

Use one running bot replica per Telegram bot token. Long polling should not be horizontally scaled with the same token.

## Tests

```bash
python -m unittest discover -s tests -v
```

`tests/test_smoke.py` is skipped automatically when `DATABASE_URL` is not configured.
