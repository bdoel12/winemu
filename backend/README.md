# Winemu — Backend

REST API berbasis Flask dengan SQLAlchemy, Socket.IO, dan JWT authentication.

---

## Struktur Folder
backend/
├── app/
│   ├── init.py          # App factory (create_app)
│   ├── models/              # SQLAlchemy models
│   │   ├── user.py
│   │   ├── report.py
│   │   ├── chat.py
│   │   ├── notification.py
│   │   └── ...              # 18 tabel total
│   ├── routes/              # Blueprint routes
│   │   ├── auth.py          # Register, login, forgot password
│   │   ├── reports.py       # CRUD laporan
│   │   ├── chat.py          # Chat & pesan
│   │   ├── notifications.py
│   │   ├── users.py
│   │   ├── search.py
│   │   └── ...              # 11 blueprint total
│   ├── helpers/             # Utility functions
│   │   ├── auth_helper.py   # JWT decode, require_auth decorator
│   │   └── ...
│   └── sockets/             # Socket.IO event handlers
├── migrations/              # Flask-Migrate migration files
├── run.py                   # Entry point
├── requirements.txt
└── .env                     # Konfigurasi environment (tidak di-push)

---

## Instalasi

```bash
cd backend
pip install -r requirements.txt
```

---

## Konfigurasi `.env`

Buat file `.env` di folder `backend/`:

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=winemu_db
DB_USER=root
DB_PASSWORD=

SECRET_KEY=ganti_dengan_secret_key_acak
JWT_SECRET_KEY=ganti_dengan_jwt_secret_acak

FLASK_ENV=development
FLASK_DEBUG=True
```

---

## Migrasi Database

```bash
# Inisialisasi (hanya pertama kali)
flask db init

# Buat file migrasi
flask db migrate -m "initial migration"

# Terapkan ke database
flask db upgrade
```

---

## Menjalankan Server

```bash
python run.py
```

Server berjalan di: `http://localhost:5000`

---

## Endpoint Utama

| Method | Endpoint | Keterangan |
|---|---|---|
| POST | `/api/auth/register` | Daftar akun baru |
| POST | `/api/auth/login` | Login, mendapat JWT token |
| POST | `/api/auth/forgot-password` | Request reset password |
| GET | `/api/reports` | Ambil daftar laporan |
| POST | `/api/reports` | Buat laporan baru |
| GET | `/api/reports/<id>` | Detail laporan |
| PUT | `/api/reports/<id>` | Edit laporan |
| DELETE | `/api/reports/<id>` | Hapus laporan |
| GET | `/api/notifications` | Ambil notifikasi user |
| GET | `/api/chat/rooms` | Daftar ruang chat |
| POST | `/api/chat/rooms/<id>/messages` | Kirim pesan |
| GET | `/api/users/me` | Profil user login |
| GET | `/api/search` | Pencarian laporan |

Semua endpoint yang memerlukan autentikasi harus menyertakan header:
Authorization: Bearer <token>

---

## Tech Stack

- **Framework:** Flask
- **ORM:** SQLAlchemy + Flask-Migrate
- **Auth:** JWT (PyJWT + bcrypt)
- **Realtime:** Flask-SocketIO
- **Database:** MySQL (via PyMySQL)
