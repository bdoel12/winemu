# Winemu — Database

Skema database MySQL untuk aplikasi Winemu.

---

## Setup Awal

Pastikan MySQL sudah berjalan, lalu buat database:

```sql
CREATE DATABASE winemu_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Kemudian jalankan migrasi dari folder backend:

```bash
cd backend
flask db upgrade
```

---

## Daftar Tabel

| Tabel | Keterangan |
|---|---|
| `users` | Data akun pengguna |
| `reports` | Laporan barang hilang / ditemukan |
| `report_images` | Foto-foto yang dilampirkan ke laporan |
| `report_categories` | Kategori barang (dokumen, elektronik, dll) |
| `comments` | Komentar di laporan |
| `likes` | Like pada laporan |
| `claims` | Klaim kepemilikan barang |
| `chat_rooms` | Ruang percakapan antar user |
| `chat_participants` | Anggota dalam ruang chat |
| `messages` | Pesan dalam chat |
| `message_reads` | Status baca pesan |
| `notifications` | Notifikasi per user |
| `follows` | Relasi follow antar user |
| `locations` | Data lokasi laporan |
| `verification_questions` | Pertanyaan verifikasi klaim |
| `verification_answers` | Jawaban verifikasi klaim |
| `password_reset_tokens` | Token reset password |
| `user_sessions` | Sesi login aktif |

---

## Relasi Penting
users ──< reports ──< report_images
──< comments
──< likes
──< claims ──< verification_answers
──< chat_participants >── chat_rooms ──< messages
──< notifications

---

## Koneksi

Konfigurasi koneksi ada di file `.env` pada folder `backend/`:

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=winemu_db
DB_USER=root
DB_PASSWORD=
```

---

## Backup & Restore

**Backup:**
```bash
mysqldump -u root -p winemu_db > winemu_backup.sql
```

**Restore:**
```bash
mysql -u root -p winemu_db < winemu_backup.sql
```

---

## Catatan

- Gunakan `utf8mb4` agar mendukung emoji dan karakter khusus
- Semua tabel menggunakan `InnoDB` engine untuk mendukung foreign key
- Jangan edit tabel migrasi secara manual — selalu gunakan `flask db migrate`
