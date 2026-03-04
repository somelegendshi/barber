# Barber Booking Bot - System Map (DNA)

## 🏗 Architecture Overview
- **Type:** Multi-Tenant SaaS (Identity-First)
- **Engine:** Python (Aiogram 3.x)
- **Data:** PostgreSQL
- **Timezone:** Asia/Tashkent (Forced)

## 🗄 Database Schema (Core)
- **shops:** `id`, `name`, `timezone`
- **barbers:** `id`, `shop_id`, `display_name`, `telegram_id` (Used for Admin Auth)
- **services:** `id`, `shop_id`, `name`, `duration_min`, `price` (Pending)
- **work_hours:** `id`, `barber_id`, `dow`, `start_time`, `end_time`
- **customers:** `id`, `telegram_user_id`, `full_name`, `phone`, `username`
- **bookings:** `id`, `shop_id`, `barber_id`, `service_id`, `customer_id`, `start_at`, `end_at`, `status`

## 🚦 Auth & Routing Logic
1. **Admin Routing:** `get_admin_shop_id(user_id)` checks if user is in `barbers` table.
2. **Super Admin:** Checks `OWNER_TELEGRAM_IDS` in `.env`.
3. **Deep Linking:** `t.me/bot?start=shop_X` sets `active_shop_id` in FSM state.

## ⚡ Slotting Engine
Logic located in `app/domain/slotting.py`. 
Generates 30-min windows based on:
`WorkHours` - `ExistingBookings` - `TimeOff`.

## 🛠 Critical Handlers
- `handlers_start.py`: Entry point, Identity check, Error pages.
- `handlers_owner.py`: Shop stats, booking lists, system health.
- `handlers_customer.py`: Global booking history, global cancellation.
- `handlers_booking.py`: Multi-step booking flow.
