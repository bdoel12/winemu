-- ============================================
-- WINEMU SEED DATA
-- Run this after schema.sql (or after flask db upgrade)
-- Import via phpMyAdmin: select database `winemu` -> Import -> choose this file
-- ============================================

USE winemu;

INSERT INTO categories (name, slug, icon, is_active, created_at) VALUES
('Elektronik', 'elektronik', 'devices', 1, NOW()),
('Dokumen', 'dokumen', 'description', 1, NOW()),
('Dompet & Uang', 'dompet-uang', 'wallet', 1, NOW()),
('Kunci & Akses', 'kunci-akses', 'key', 1, NOW()),
('Tas & Ransel', 'tas-ransel', 'backpack', 1, NOW()),
('Perhiasan', 'perhiasan', 'diamond', 1, NOW()),
('Kendaraan', 'kendaraan', 'directions_car', 1, NOW()),
('Hewan Peliharaan', 'hewan-peliharaan', 'pets', 1, NOW()),
('Pakaian', 'pakaian', 'checkroom', 1, NOW()),
('Lainnya', 'lainnya', 'category', 1, NOW());

-- NOTE: This file seeds categories only. Default admin & demo user accounts
-- must be created with `python seed.py` from the backend/ folder, which uses
-- bcrypt with a random salt via app/models/user.py:set_password(). Running
-- raw INSERT statements for the users table would either require a fixed
-- (and therefore insecure) bcrypt hash, or fail password verification.
--
-- After running this file, cd into backend/ and run:
--   python seed.py
-- This creates:
--   Admin: admin@winemu.id / admin123
--   Demo:  demo@winemu.id  / demo123

