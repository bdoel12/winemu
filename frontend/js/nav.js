// Shared navigation HTML
function getBottomNav(activePage) {
  const pages = [
    { id: 'home', icon: 'home', label: 'Home', href: '/feed.html' },
    { id: 'search', icon: 'search', label: 'Cari', href: '/search.html' },
    { id: 'report', icon: 'add', label: 'Lapor', href: '/report.html', isFab: true },
    { id: 'chat', icon: 'chat', label: 'Chat', href: '/chat.html' },
    { id: 'profile', icon: 'person', label: 'Profil', href: '/profile.html' },
  ];

  const items = pages.map(p => {
    if (p.isFab) {
      return `<a href="${p.href}" class="flex flex-col items-center justify-center -mt-6 hover:scale-105 active:scale-95 transition-transform">
        <div class="bg-[#314E52] text-white rounded-full w-14 h-14 flex items-center justify-center shadow-lg border-4 border-surface-container-lowest">
          <span class="material-symbols-outlined text-[28px]" style="font-variation-settings:'FILL' 0;">add</span>
        </div>
      </a>`;
    }
    const isActive = p.id === activePage;
    return `<a href="${p.href}" data-nav="${p.id}" class="flex flex-col items-center justify-center ${isActive ? 'text-[#314E52]' : 'text-on-surface-variant'} hover:bg-surface-container-high active:scale-90 transition-all rounded-xl p-2">
      <span class="material-symbols-outlined" style="font-variation-settings:'FILL' ${isActive ? '1' : '0'};">${p.icon}</span>
      <span style="font-size:10px;font-weight:600;margin-top:2px;">${p.label}</span>
    </a>`;
  }).join('');

  return `<nav class="fixed bottom-0 left-0 w-full z-50 flex justify-around items-center px-4 py-2 md:hidden bg-surface-container-lowest shadow-[0_-4px_20px_-4px_rgba(49,78,82,0.08)] rounded-t-xl border-t border-surface-container-highest">
    ${items}
  </nav>`;
}

function getTopBar(title = 'Winemu', activePage = '') {
  const navLinks = [
    { id: 'home', label: 'Home', href: '/feed.html' },
    { id: 'search', label: 'Cari', href: '/search.html' },
    { id: 'report', label: 'Lapor', href: '/report.html' },
    { id: 'chat', label: 'Chat', href: '/chat.html' },
    { id: 'profile', label: 'Profil', href: '/profile.html' },
  ];

  const links = navLinks.map(l =>
    `<a href="${l.href}" class="${l.id === activePage ? 'text-primary font-bold' : 'text-on-surface-variant'} hover:scale-105 transition-transform duration-200">${l.label}</a>`
  ).join('');

  return `<header class="sticky top-0 bg-[#F8F5F0] z-50 border-b border-surface-container-highest shadow-sm">
    <div class="flex justify-between items-center w-full px-4 py-3 max-w-[1200px] mx-auto">
      <div class="font-headline-md text-xl text-primary font-bold tracking-tight">Winemu</div>
      <nav class="hidden md:flex items-center gap-8">${links}</nav>
      <div class="flex items-center gap-2">
        <a href="/search.html" class="text-primary p-1 hover:scale-105 transition-transform">
          <span class="material-symbols-outlined">search</span>
        </a>
        <a href="/notifications.html" class="text-primary p-1 hover:scale-105 transition-transform relative" id="notif-btn">
          <span class="material-symbols-outlined">notifications</span>
          <span id="notif-badge" class="hidden absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white rounded-full text-[9px] flex items-center justify-center font-bold"></span>
        </a>
      </div>
    </div>
  </header>`;
}

function injectNav(activePage) {
  document.getElementById('bottom-nav').innerHTML = getBottomNav(activePage);
  document.getElementById('top-bar').innerHTML = getTopBar('Winemu', activePage);
  loadNotifBadge();
  // Tampilkan notif yang tertunda dari halaman sebelumnya
  _flushPendingToasts();
}

async function loadNotifBadge() {
  if (!api.getToken()) return;
  try {
    const r = await api.get('/notifications?per_page=1');
    if (r?.data?.unread_count > 0) {
      const badge = document.getElementById('notif-badge');
      if (badge) {
        badge.textContent = r.data.unread_count > 9 ? '9+' : r.data.unread_count;
        badge.classList.remove('hidden');
        badge.classList.add('flex');
      }
    }
  } catch (e) {}
}

// ── Notifikasi Toast yang Persist Lintas Halaman ──────────────────────────────
//
// Masalah: Socket.IO terhubung ulang setiap ganti halaman. Notifikasi yang
// datang saat user sedang navigasi hilang begitu saja karena DOM lama sudah
// di-unload.
//
// Solusi:
// 1. Setiap notif yang masuk disimpan ke sessionStorage sebagai antrian.
// 2. Setiap halaman baru load, antrian dicek → ditampilkan satu per satu.
// 3. Web Notifications API digunakan kalau izin sudah diberikan → notif
//    muncul di luar browser bahkan saat tab di-minimize.

var NOTIF_QUEUE_KEY = 'winemu_notif_queue';

function _saveToQueue(data) {
  try {
    var queue = JSON.parse(sessionStorage.getItem(NOTIF_QUEUE_KEY) || '[]');
    // Tambah timestamp agar bisa diurutkan / di-dedupe
    data._queuedAt = Date.now();
    queue.push(data);
    // Batasi antrian maksimal 10 agar tidak overflow
    if (queue.length > 10) queue = queue.slice(queue.length - 10);
    sessionStorage.setItem(NOTIF_QUEUE_KEY, JSON.stringify(queue));
  } catch (e) {}
}

function _clearQueue() {
  try { sessionStorage.removeItem(NOTIF_QUEUE_KEY); } catch (e) {}
}

function _flushPendingToasts() {
  try {
    var queue = JSON.parse(sessionStorage.getItem(NOTIF_QUEUE_KEY) || '[]');
    if (!queue.length) return;
    _clearQueue();
    // Tampilkan satu per satu dengan jeda kecil agar tidak menumpuk
    queue.forEach(function(data, i) {
      setTimeout(function() { showNotifToast(data); }, i * 600);
    });
  } catch (e) {}
}

// ── Web Notification (muncul di luar tab/browser) ─────────────────────────────
function _sendWebNotification(data) {
  if (!('Notification' in window)) return;
  if (Notification.permission !== 'granted') return;
  try {
    var n = new Notification(data.title || 'Winemu', {
      body: data.message || '',
      icon: '/favicon.ico',
      tag: 'winemu-notif-' + (data.type || 'general'),
      renotify: true,
    });
    n.onclick = function() {
      window.focus();
      window.location.href = '/notifications.html';
      n.close();
    };
  } catch (e) {}
}

// ── Realtime Notification via Socket.IO ──────────────────────────────────────
(function bootstrapSocket() {
  if (!api.getToken()) return;
  var user = api.getUser();
  if (!user) return;

  var script = document.createElement('script');
  script.src = 'https://cdn.socket.io/4.7.5/socket.io.min.js';
  script.onload = function () {
    var socket = io({ transports: ['websocket', 'polling'] });

    socket.on('connect', function() {
      socket.emit('join_user_room', { user_id: user.id });
    });

    socket.on('new_notification', function(data) {
      // Update badge
      var badge = document.getElementById('notif-badge');
      if (badge) {
        badge.style.cssText = 'position:absolute;top:-2px;right:-2px;width:10px;height:10px;border-radius:50%;background:#ba1a1a;border:2px solid #fcf9f4;display:block;';
        badge.textContent = '';
      }

      // Simpan ke queue (untuk bertahan saat pindah halaman)
      _saveToQueue(data);

      // Tampilkan toast di halaman saat ini
      showNotifToast(data);

      // Kirim juga Web Notification (muncul di luar tab)
      _sendWebNotification(data);
    });

    socket.on('new_message', function() {
      loadNotifBadge();
    });

    window._winemuSocket = socket;
  };
  document.head.appendChild(script);
})();

// ── Toast UI ──────────────────────────────────────────────────────────────────
function showNotifToast(data) {
  // Inject animasi kalau belum ada
  if (!document.getElementById('notif-toast-style')) {
    var style = document.createElement('style');
    style.id = 'notif-toast-style';
    style.textContent = `
      @keyframes slideInRight {
        from { transform: translateX(110%); opacity: 0; }
        to   { transform: translateX(0);    opacity: 1; }
      }
      @keyframes slideOutRight {
        from { transform: translateX(0);    opacity: 1; }
        to   { transform: translateX(110%); opacity: 0; }
      }
    `;
    document.head.appendChild(style);
  }

  var iconMap = { chat: 'chat', like: 'favorite', comment: 'comment', claim: 'assignment_turned_in' };
  var icon = iconMap[data.type] || 'notifications';

  // Buat wrapper stack kalau belum ada (supaya bisa tumpuk beberapa toast)
  var stack = document.getElementById('notif-toast-stack');
  if (!stack) {
    stack = document.createElement('div');
    stack.id = 'notif-toast-stack';
    stack.style.cssText = 'position:fixed;bottom:5.5rem;right:1rem;z-index:9999;display:flex;flex-direction:column-reverse;gap:8px;max-width:320px;width:calc(100% - 2rem);';
    document.body.appendChild(stack);
  }

  var toast = document.createElement('div');
  toast.style.cssText = `
    background:#1a373b; color:#fff;
    border-radius:1rem; padding:0.875rem 1rem;
    display:flex; align-items:flex-start; gap:0.75rem;
    box-shadow:0 8px 32px rgba(0,0,0,0.25);
    animation:slideInRight 0.35s cubic-bezier(0.34,1.56,0.64,1);
    cursor:pointer; width:100%;
  `;
  toast.innerHTML = `
    <span class="material-symbols-outlined" style="font-size:22px;flex-shrink:0;margin-top:1px;font-variation-settings:'FILL' 1;">${icon}</span>
    <div style="flex:1;min-width:0;">
      <div style="font-weight:700;font-size:13px;line-height:1.3;">${data.title || 'Notifikasi baru'}</div>
      <div style="font-size:12px;opacity:0.85;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${data.message || ''}</div>
    </div>
    <button style="background:rgba(255,255,255,0.15);border:none;color:#fff;border-radius:50%;width:22px;height:22px;display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0;cursor:pointer;">✕</button>
  `;

  // Klik tombol close
  toast.querySelector('button').addEventListener('click', function(e) {
    e.stopPropagation();
    _dismissToast(toast);
  });

  // Klik body toast → ke halaman notifikasi
  toast.addEventListener('click', function() {
    window.location.href = '/notifications.html';
  });

  stack.appendChild(toast);

  // Auto-dismiss setelah 3 detik
  var timer = setTimeout(function() { _dismissToast(toast); }, 3000);
  toast._dismissTimer = timer;
}

function _dismissToast(toast) {
  if (toast._dismissed) return;
  toast._dismissed = true;
  clearTimeout(toast._dismissTimer);
  toast.style.animation = 'slideOutRight 0.25s ease forwards';
  setTimeout(function() {
    if (toast.parentElement) toast.remove();
    // Hapus stack kalau kosong
    var stack = document.getElementById('notif-toast-stack');
    if (stack && !stack.children.length) stack.remove();
  }, 260);
}
