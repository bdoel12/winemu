# Winemu — Platform Temu Barang Hilang & Ditemukan

Aplikasi web komunitas untuk melaporkan dan mencari barang hilang/ditemukan, dibangun dengan Flask (backend REST API) dan halaman HTML/Tailwind statis (frontend) yang terhubung langsung ke API.

## Struktur Proyek

```
winemu/
├── backend/              # Flask REST API
│   ├── app/
│   │   ├── api/v1/       # Blueprint endpoint (auth, users, reports, claims, chat, admin, dst)
│   │   ├── models/       # SQLAlchemy models (User, Report, Claim, dll)
│   │   ├── schemas/      # (reserved untuk Marshmallow schemas tambahan)
│   │   ├── services/     # (reserved untuk business logic kompleks)
│   │   ├── repositories/ # (reserved untuk data access layer kompleks)
│   │   ├── middleware/   # (reserved untuk middleware kustom)
│   │   ├── utils/        # Helper: response formatter, upload handler
│   │   ├── config/       # Konfigurasi Flask (DB, JWT, upload, dll)
│   │   ├── static/       # File upload (avatar, foto laporan)
│   │   ├── sockets.py    # Event handler Flask-SocketIO (chat realtime)
│   │   └── __init__.py   # App factory
│   ├── migrations/       # Flask-Migrate / Alembic migration scripts
│   ├── requirements.txt
│   ├── seed.py            # Script seeding kategori + akun admin/demo
│   ├── run.py              # Entry point aplikasi
│   └── .env                # Konfigurasi environment
├── frontend/              # Halaman statis (HTML + TailwindCSS CDN + vanilla JS)
│   ├── js/api.js           # API client (fetch wrapper, token refresh, toast)
│   ├── js/nav.js            # Komponen navigasi bersama
│   ├── admin/                # Panel admin (dashboard, reports, users, conflicts, logs, settings)
│   └── *.html                # Halaman publik (feed, login, register, chat, dst)
├── database/
│   ├── schema.sql            # DDL referensi (hasil generate dari model SQLAlchemy)
│   └── seed.sql                # Data awal kategori (untuk import phpMyAdmin)
└── docs/
```

## Stack Teknologi

- **Backend**: Python Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-JWT-Extended, Flask-SocketIO, Flask-CORS, Marshmallow
- **Database**: MySQL (port **3308**), diakses via phpMyAdmin
- **Auth**: JWT (access + refresh token)
- **Realtime**: Flask-SocketIO untuk fitur chat
- **Maps**: LeafletJS (OpenStreetMap tiles)
- **Frontend**: HTML statis + TailwindCSS (CDN) + vanilla JavaScript, UI sesuai desain yang sudah disediakan

## Setup & Instalasi

### 1. Database (MySQL via phpMyAdmin, port 3308)

Buka phpMyAdmin Anda yang berjalan di MySQL port 3308, lalu buat database `winemu` (atau biarkan migration yang membuatnya otomatis lewat `CREATE DATABASE IF NOT EXISTS` di `database/schema.sql`).

Cara termudah — gunakan Flask-Migrate (disarankan):

```bash
cd backend
pip install -r requirements.txt
```

Edit file `.env` sesuaikan kredensial MySQL Anda:

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=winemu
DB_USER=root
DB_PASSWORD=
```

Lalu jalankan migration:

```bash
flask db upgrade
```

Ini akan membuat seluruh 12 tabel (`users`, `roles`-equivalent via `role` column, `reports`, `report_media`, `categories`, `comments`, `bookmarks`, `claims`, `notifications`, `conversations`, `messages`, `activity_logs`).

**Alternatif** — jika Anda lebih suka import manual lewat phpMyAdmin: import `database/schema.sql` lalu `database/seed.sql` melalui tab Import.

### 2. Seed Data Awal

```bash
cd backend
python seed.py
```

Ini membuat:
- 10 kategori default (Elektronik, Dokumen, dst)
- Akun admin: `admin@winemu.id` / `admin123`
- Akun demo: `demo@winemu.id` / `demo123`

### 3. Jalankan Backend

```bash
cd backend
python run.py
```

Server berjalan di `http://localhost:5000`, sekaligus melayani file frontend statis di root path (`/`, `/login.html`, `/admin/dashboard.html`, dst) dan REST API di `/api/v1/*`.

### 4. Akses Aplikasi

- Aplikasi user: `http://localhost:5000/`
- Login: `http://localhost:5000/login.html`
- Admin console: `http://localhost:5000/admin/dashboard.html` (login dengan akun `role=admin`)

## Endpoint API Utama

| Modul | Prefix | Contoh |
|---|---|---|
| Auth | `/api/v1/auth` | register, login, refresh, logout, forgot-password, reset-password |
| Users | `/api/v1/users` | profile, avatar upload, bookmarks |
| Reports | `/api/v1/reports` | CRUD laporan hilang/ditemukan, like, comment, media |
| Categories | `/api/v1/categories` | list & manage kategori |
| Claims | `/api/v1/claims` | ajukan klaim kepemilikan, approve/reject, dispute |
| Chat | `/api/v1/chat` | percakapan & pesan (realtime via SocketIO) |
| Notifications | `/api/v1/notifications` | daftar notifikasi, mark as read |
| Admin | `/api/v1/admin` | dashboard stats, kelola user, kelola laporan, resolusi konflik |

## Fitur yang Sudah Terhubung End-to-End

1. **Authentication** — Register, Login, Logout, Refresh Token, Forgot/Reset Password ✅
2. **User Profile** — Edit profil, upload avatar, bookmark ✅
3. **Reports (Destinations-equivalent)** — CRUD laporan, upload foto/video, kategori, lokasi (lat/lng), like, comment ✅
4. **Feed** — Infinite scroll, filter (hilang/ditemukan), search ✅
5. **Review/Interaksi** — Like, comment pada laporan ✅
6. **Conflict/Claim System** — Ajukan klaim dengan verifikasi ciri rahasia, approve/reject oleh pemilik atau admin, eskalasi dispute ✅
7. **Map System** — Marker Leaflet, nearby reports, detail lokasi per laporan ✅
8. **Bookmark System** — Simpan laporan favorit ✅
9. **Admin Panel** — Dashboard dengan grafik & peta operasional, kelola laporan, kelola pengguna, resolusi konflik, log sistem, pengaturan ✅
10. **Analytics Dashboard** — KPI cards (total laporan, user, status), breakdown kategori, pertumbuhan user ✅

## Catatan Produksi

- Untuk produksi, ganti `SECRET_KEY` dan `JWT_SECRET_KEY` di `.env` dengan nilai random yang kuat.
- `flask-socketio` dikonfigurasi dengan `async_mode='eventlet'`; pastikan `eventlet` terinstall (`pip install eventlet`) — sudah ada di `requirements.txt`.
- Upload media disimpan secara lokal di `backend/app/static/uploads/`. Untuk skala besar, ganti `app/utils/upload.py` agar menulis ke MinIO/S3 (kredensial sudah disiapkan di `.env`: `MINIO_*`).
- Gunakan WSGI server produksi (`gunicorn` + `eventlet` worker, atau `gevent`) ketika deploy, bukan `flask run` / dev server bawaan.
