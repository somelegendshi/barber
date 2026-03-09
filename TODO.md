# Project TODO & Backlog

## 🔴 HIGH PRIORITY (Critical)
- [ ] Add **Price** column to `services` table and update all handlers.
- [ ] Implement **Financial Analytics** (Daily/Weekly revenue stats).

## 🟡 MEDIUM PRIORITY (Improvements)
- [ ] **Split-Shifts:** Allow barbers to have multiple work windows per day (e.g., 10-14 and 16-20).
- [ ] **Admin Notifications:** Ensure specific shop owners get notified on every booking/cancellation.
- [ ] **Caching:** Cache admin status in FSM to reduce DB load.

## 🟢 LOW PRIORITY (Polish)
- [ ] **Portfolio:** Add image support for barbers to show their work.
- [ ] **Feedback:** Ask customers for a rating (1-5 stars) after their appointment.

## ✅ DONE
- [x] Implement **Super-Admin Menu** (`/boss`) to create shops and assign managers via menu.
- [x] Time Picker fixed to support 24/7 schedules and any start/end combinations.
- [x] Menu-driven Custom Hours (Time Picker).
- [x] Global Customer History & Cancellation.
- [x] Identity-First Admin Routing.
- [x] System Health & Error Pages.
- [x] Automated Reminders (Worker).