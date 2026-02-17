-- Clean slate
TRUNCATE bookings, time_off, work_hours, services, barbers, shops CASCADE;

-- 1. Create Shop
INSERT INTO shops (name, timezone) VALUES ('Top Barber Tashkent', 'Asia/Tashkent');

-- 2. Create Barbers (for Shop ID 1)
INSERT INTO barbers (shop_id, display_name) VALUES 
(1, 'Aziz'),
(1, 'Bekzod');

-- 3. Create Services
INSERT INTO services (shop_id, name, duration_min) VALUES
(1, 'Erkaklar sochi (Haircut)', 30),
(1, 'Soqol (Beard Trim)', 20),
(1, 'Kompleks (Hair + Beard)', 50);

-- 4. Set Work Hours (0=Mon ... 6=Sun)
-- Aziz: Mon-Fri 10:00 - 20:00, Lunch 13-14 usually handled by blocking but here just open slots
INSERT INTO work_hours (barber_id, dow, start_time, end_time, slot_step_min) 
SELECT id, 0, '10:00', '20:00', 30 FROM barbers WHERE display_name='Aziz'; -- Mon
INSERT INTO work_hours (barber_id, dow, start_time, end_time, slot_step_min) 
SELECT id, 1, '10:00', '20:00', 30 FROM barbers WHERE display_name='Aziz'; -- Tue
INSERT INTO work_hours (barber_id, dow, start_time, end_time, slot_step_min) 
SELECT id, 2, '10:00', '20:00', 30 FROM barbers WHERE display_name='Aziz'; -- Wed
INSERT INTO work_hours (barber_id, dow, start_time, end_time, slot_step_min) 
SELECT id, 3, '10:00', '20:00', 30 FROM barbers WHERE display_name='Aziz'; -- Thu
INSERT INTO work_hours (barber_id, dow, start_time, end_time, slot_step_min) 
SELECT id, 4, '10:00', '20:00', 30 FROM barbers WHERE display_name='Aziz'; -- Fri

-- Bekzod: Wed-Sun 11:00 - 21:00
INSERT INTO work_hours (barber_id, dow, start_time, end_time, slot_step_min) 
SELECT id, 2, '11:00', '21:00', 30 FROM barbers WHERE display_name='Bekzod'; -- Wed
INSERT INTO work_hours (barber_id, dow, start_time, end_time, slot_step_min) 
SELECT id, 3, '11:00', '21:00', 30 FROM barbers WHERE display_name='Bekzod'; -- Thu
INSERT INTO work_hours (barber_id, dow, start_time, end_time, slot_step_min) 
SELECT id, 4, '11:00', '21:00', 30 FROM barbers WHERE display_name='Bekzod'; -- Fri
INSERT INTO work_hours (barber_id, dow, start_time, end_time, slot_step_min) 
SELECT id, 5, '11:00', '21:00', 30 FROM barbers WHERE display_name='Bekzod'; -- Sat
INSERT INTO work_hours (barber_id, dow, start_time, end_time, slot_step_min) 
SELECT id, 6, '11:00', '21:00', 30 FROM barbers WHERE display_name='Bekzod'; -- Sun
