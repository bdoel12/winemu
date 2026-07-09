# Winemu 🔍

Platform temu barang berbasis komunitas yang terpercaya. Laporkan barang hilang, temukan barang orang lain, dan bantu sesama melalui feed sosial.

---

## Cara Menjalankan Aplikasi

### Prasyarat

Pastikan sudah terinstall:
- Python 3.10+
- pip
- MySQL / XAMPP
- Git

---

### 1. Clone Repository

```bash
git clone https://github.com/username/winemu.git
cd winemu
```

### 2. Setup Backend

```bash
cd backend
pip install -r requirements.txt
```

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

### 3. Setup Database

Buat database di MySQL:

```sql
CREATE DATABASE winemu_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Lalu jalankan migrasi:

```bash
flask db upgrade
```

### 4. Jalankan Backend

```bash
python run.py
```

Backend berjalan di: `http://localhost:5000`

---

### 5. Jalankan Frontend

Frontend adalah static HTML — tidak perlu build tool. Cukup serve dengan web server sederhana.

Opsi 1 — Python:
```bash
cd frontend
python -m http.server 8080
```

Opsi 2 — VS Code Live Server:
Klik kanan `index.html` → Open with Live Server

Akses di browser: `http://localhost:8080`

---

## Struktur Folder
winemu/
├── backend/
│   ├── app/
│   │   ├── models/        # SQLAlchemy models
│   │   ├── routes/        # Blueprint routes (API)
│   │   ├── helpers/       # Utility functions
│   │   └── init.py    # App factory
│   ├── migrations/        # Flask-Migrate files
│   ├── run.py
│   └── requirements.txt
└── frontend/
├── desktop/           # Tampilan desktop
├── js/
│   ├── api.js         # API client & auth helper
│   ├── nav.js         # Navigasi & notifikasi realtime
│   └── permissions.js # Dialog izin browser
├── index.html
├── feed.html
├── chat.html
├── report.html
└── ...

---

## Cara Masuk ke Aplikasi

### Daftar Akun Baru
1. Buka `http://localhost:8080`
2. Klik **Daftar Sekarang**
3. Isi nama, email, dan password
4. Klik **Daftar**

### Login
1. Buka `http://localhost:8080`
2. Klik **Masuk ke Akun**
3. Masukkan email dan password
4. Klik **Masuk**

Setelah login, akan diarahkan otomatis ke halaman **Feed**.

---

## Fitur Utama

- **Feed Laporan** — Lihat laporan barang hilang & ditemukan di sekitar Anda
- **Pencarian** — Cari barang berdasarkan nama, kategori, atau lokasi
- **Chat Realtime** — Hubungi pelapor langsung via Socket.IO
- **Notifikasi** — Notif realtime untuk klaim, like, komentar, dan pesan masuk
- **Lokasi** — Tampilan berbasis peta dengan Leaflet.js
- **Autentikasi** — JWT-based auth, register, login, forgot password

---

## Tech Stack

| Layer | Teknologi |
|---|---|
| Frontend | HTML, Tailwind CSS, Vanilla JS |
| Backend | Python, Flask, SQLAlchemy |
| Database | MySQL |
| Realtime | Socket.IO |
| Auth | JWT |
| Maps | Leaflet.js |

---

## Catatan

- Pastikan MySQL sudah berjalan sebelum menjalankan backend
- File `.env` tidak ikut di-push ke GitHub (sudah ada di `.gitignore`)
- Izin browser (lokasi & notifikasi) akan diminta otomatis saat pertama kali masuk ke feed

---

© 2026 Winemu Ecosystem · Yogyakarta, ID · ꦮꦶꦤꦼꦩꦸ
