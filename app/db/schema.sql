CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TABLE IF NOT EXISTS shops (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  timezone TEXT NOT NULL DEFAULT 'Asia/Tashkent',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS barbers (
  id BIGSERIAL PRIMARY KEY,
  shop_id BIGINT NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
  display_name TEXT NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS services (
  id BIGSERIAL PRIMARY KEY,
  shop_id BIGINT NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  duration_min INT NOT NULL CHECK (duration_min > 0),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Weekly working windows per barber (0=Sun .. 6=Sat)
CREATE TABLE IF NOT EXISTS work_hours (
  id BIGSERIAL PRIMARY KEY,
  barber_id BIGINT NOT NULL REFERENCES barbers(id) ON DELETE CASCADE,
  dow SMALLINT NOT NULL CHECK (dow BETWEEN 0 AND 6),
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  slot_step_min INT NOT NULL DEFAULT 30 CHECK (slot_step_min > 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (end_time > start_time)
);

-- Exceptions: breaks, days off, etc.
CREATE TABLE IF NOT EXISTS time_off (
  id BIGSERIAL PRIMARY KEY,
  barber_id BIGINT NOT NULL REFERENCES barbers(id) ON DELETE CASCADE,
  start_at TIMESTAMPTZ NOT NULL,
  end_at TIMESTAMPTZ NOT NULL,
  reason TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (end_at > start_at)
);

CREATE TABLE IF NOT EXISTS customers (
  id BIGSERIAL PRIMARY KEY,
  telegram_user_id BIGINT NOT NULL UNIQUE,
  full_name TEXT,
  phone TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- status: CONFIRMED,CANCELLED,DONE,NO_SHOW
CREATE TABLE IF NOT EXISTS bookings (
  id BIGSERIAL PRIMARY KEY,
  shop_id BIGINT NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
  barber_id BIGINT NOT NULL REFERENCES barbers(id) ON DELETE RESTRICT,
  service_id BIGINT NOT NULL REFERENCES services(id) ON DELETE RESTRICT,
  customer_id BIGINT REFERENCES customers(id) ON DELETE SET NULL,
  customer_name TEXT NOT NULL,
  start_at TIMESTAMPTZ NOT NULL,
  end_at TIMESTAMPTZ NOT NULL,
  status TEXT NOT NULL DEFAULT 'CONFIRMED',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (end_at > start_at)
);

CREATE INDEX IF NOT EXISTS bookings_confirmed_lookup
  ON bookings (barber_id, start_at, end_at)
  WHERE status='CONFIRMED';

-- Hard guarantee: no overlapping confirmed bookings for same barber
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='no_overlap_confirmed') THEN
    ALTER TABLE bookings
    ADD CONSTRAINT no_overlap_confirmed
    EXCLUDE USING gist (
      barber_id WITH =,
      tstzrange(start_at, end_at, '[)') WITH &&
    )
    WHERE (status='CONFIRMED');
  END IF;
END$$;
