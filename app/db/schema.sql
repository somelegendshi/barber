CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TABLE IF NOT EXISTS shops (
  id BIGSERIAL PRIMARY KEY,
  public_code BIGINT UNIQUE,
  name TEXT NOT NULL,
  timezone TEXT NOT NULL DEFAULT 'Asia/Tashkent',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS barbers (
  id BIGSERIAL PRIMARY KEY,
  shop_id BIGINT NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
  display_name TEXT NOT NULL,
  telegram_id BIGINT, -- Admin login ID
  notify_telegram_id BIGINT, -- Barber notification ID
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

CREATE TABLE IF NOT EXISTS work_hours (
  id BIGSERIAL PRIMARY KEY,
  barber_id BIGINT NOT NULL REFERENCES barbers(id) ON DELETE CASCADE,
  dow SMALLINT NOT NULL CHECK (dow BETWEEN 0 AND 6),
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  slot_step_min INT NOT NULL DEFAULT 30 CHECK (slot_step_min > 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (
    end_time > start_time
    OR (start_time = TIME '00:00' AND end_time = TIME '00:00')
  )
);

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
  username TEXT, -- Added for SaaS
  language_code TEXT CHECK (language_code IN ('uz', 'ru')),
  phone TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

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
  reminded BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (end_at > start_at),
  CHECK (status IN ('CONFIRMED', 'CANCELLED'))
);

CREATE INDEX IF NOT EXISTS idx_barbers_shop_active
  ON barbers (shop_id, display_name)
  WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_services_shop_active
  ON services (shop_id, id)
  WHERE is_active = TRUE;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'barbers' AND column_name = 'telegram_id'
  ) THEN
    EXECUTE '
      CREATE INDEX IF NOT EXISTS idx_barbers_telegram_id
      ON barbers (telegram_id)
      WHERE telegram_id IS NOT NULL
    ';
  END IF;
END$$;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'barbers' AND column_name = 'notify_telegram_id'
  ) THEN
    EXECUTE '
      CREATE INDEX IF NOT EXISTS idx_barbers_notify_telegram_id
      ON barbers (notify_telegram_id)
      WHERE notify_telegram_id IS NOT NULL
    ';
  END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_time_off_lookup
  ON time_off (barber_id, start_at, end_at);

CREATE INDEX IF NOT EXISTS bookings_confirmed_lookup
  ON bookings (barber_id, start_at, end_at)
  WHERE status='CONFIRMED';

CREATE INDEX IF NOT EXISTS idx_bookings_shop_future
  ON bookings (shop_id, start_at)
  WHERE status='CONFIRMED';

CREATE INDEX IF NOT EXISTS idx_bookings_customer_future
  ON bookings (customer_id, start_at)
  WHERE status='CONFIRMED';

-- Hard guarantee: no overlapping confirmed bookings
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
