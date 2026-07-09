# Winemu — Frontend

Tampilan antarmuka Winemu berbasis HTML statis dengan Tailwind CSS dan Vanilla JavaScript.

---

## Struktur Folder
frontend/
├── desktop/               # Versi tampilan desktop
│   ├── index.html         # Landing page desktop
│   ├── feed.html          # Feed utama desktop
│   ├── chat.html          # Halaman chat desktop
│   ├── search.html        # Pencarian desktop
│   ├── report.html        # Form laporan desktop
│   ├── report-detail.html
│   ├── report-edit.html
│   ├── notifications.html
│   ├── profile.html
│   ├── user-profile.html
│   ├── settings.html
│   ├── status-serah-terima.html
│   ├── login.html
│   ├── register.html
│   ├── forgot-password.html
│   ├── reset-password.html
│   └── js/
│       └── desktop-nav.js # Navigasi sidebar desktop
├── admin/                 # Panel admin
├── js/
│   ├── api.js             # API client, auth helper, token management
│   ├── nav.js             # Bottom nav, notifikasi realtime via Socket.IO
│   └── permissions.js     # Dialog izin lokasi & notifikasi (muncul sekali)
├── index.html             # Landing page mobile
├── feed.html              # Feed utama mobile
├── chat.html
├── search.html
├── report.html
├── report-detail.html
├── report-edit.html
├── notifications.html
├── profile.html
├── user-profile.html
├── settings.html
├── status-serah-terima.html
├── login.html
├── register.html
├── forgot-password.html
└── reset-password.html

---

## Cara Menjalankan

Tidak perlu build tool atau npm. Cukup serve sebagai static file.

**Opsi 1 — Python HTTP Server:**
```bash
cd frontend
python -m http.server 8080
```

**Opsi 2 — VS Code Live Server:**
Klik kanan `index.html` → Open with Live Server

Akses di: `http://localhost:8080`

---

## Konfigurasi API

Semua request ke backend dikelola melalui `js/api.js`. Pastikan base URL sudah sesuai dengan alamat backend yang berjalan.

Cek baris berikut di `api.js`:
```js
const BASE_URL = 'http://localhost:5000/api';
```

Sesuaikan jika backend berjalan di port atau host yang berbeda.

---

## Catatan Penting

- Halaman yang memerlukan login akan redirect otomatis ke `login.html` jika token tidak ditemukan
- `device-redirect.js` mendeteksi ukuran layar dan mengarahkan ke versi mobile atau desktop secara otomatis
- Dialog izin browser (lokasi & notifikasi) hanya muncul **sekali** saat pertama masuk ke feed, disimpan via `localStorage`
- Notifikasi realtime menggunakan Socket.IO yang di-bootstrap otomatis oleh `nav.js`
