// Komponen sidebar navigasi desktop bersama, dipakai di semua halaman frontend/desktop/*.html.
// Mengikuti pola yang sama dengan js/nav.js (versi mobile): satu fungsi generator HTML,
// dipanggil lewat injectDesktopNav() saat halaman dimuat.

function getDesktopSidebar(activePage) {
  const pages = [
    { id: 'home', icon: 'home', label: 'Feed', href: '/desktop/feed.html' },
    { id: 'search', icon: 'search', label: 'Cari', href: '/desktop/search.html' },
    { id: 'report', icon: 'add_box', label: 'Lapor', href: '/desktop/report.html' },
    { id: 'notifications', icon: 'notifications', label: 'Notifikasi', href: '/desktop/notifications.html' },
    { id: 'chat', icon: 'mail', label: 'Pesan', href: '/desktop/chat.html' },
    { id: 'profile', icon: 'person', label: 'Profil', href: '/desktop/profile.html' },
  ];

  const user = (typeof api !== 'undefined' && api.getUser) ? api.getUser() : null;
  const avatarHtml = user?.avatar_url
    ? `<img src="${user.avatar_url}" class="w-6 h-6 rounded-full object-cover border border-white/30" alt="${user.full_name || ''}">`
    : `<div class="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center text-[10px] font-bold text-white">${(user?.full_name || user?.username || '?')[0]?.toUpperCase() || '?'}</div>`;

  const links = pages.map(p => {
    const isActive = p.id === activePage;
    const activeClass = isActive
      ? 'bg-white/20 text-white font-bold'
      : 'text-white/80 hover:bg-white/10 hover:text-white';
    const fill = isActive ? "font-variation-settings: 'FILL' 1;" : '';
    return `<a href="${p.href}" class="flex items-center gap-4 px-4 py-3 rounded-xl transition-colors duration-200 ${activeClass}">
      <span class="material-symbols-outlined text-2xl" style="${fill}">${p.icon}</span>
      <span class="text-body-md text-lg sidebar-label">${p.label}</span>
    </a>`;
  }).join('');

  return `<nav id="desktop-nav" class="fixed left-0 top-0 h-screen w-64 flex flex-col py-8 px-4 z-50 transition-all duration-300" style="background-color:#314E52;">
    <div class="mb-10 px-4">
      <a href="/desktop/feed.html" class="font-display-lg text-3xl text-white sidebar-label" style="font-family:'Philosopher',serif;">Winemu</a>
    </div>
    <div class="flex-1 flex flex-col gap-2">
      ${links}
    </div>
    <div class="mt-auto pt-4 border-t border-white/10 flex flex-col gap-2">
      <a href="/desktop/settings.html" class="flex items-center gap-4 px-4 py-3 rounded-xl text-white/80 hover:bg-white/10 hover:text-white transition-colors duration-200">
        <span class="material-symbols-outlined text-2xl">settings</span>
        <span class="text-body-md sidebar-label">Pengaturan</span>
      </a>
      <button onclick="desktopLogout()" class="flex items-center gap-4 px-4 py-3 rounded-xl text-white/70 hover:bg-white/10 hover:text-white transition-colors duration-200 text-left">
        <span class="material-symbols-outlined text-2xl">logout</span>
        <span class="text-body-md sidebar-label">Keluar</span>
      </button>
    </div>
    <button id="sidebar-toggle" onclick="toggleSidebar()" title="Perluas/Kecilkan" class="absolute -right-3 bottom-8 w-6 h-6 rounded-full bg-white text-primary flex items-center justify-center shadow-md hover:bg-surface-container-low transition-colors z-10" style="border:1px solid #c1c8c9;">
      <span class="material-symbols-outlined text-[14px]" id="sidebar-chevron">chevron_left</span>
    </button>
  </nav>`;
}

function injectDesktopNav(activePage) {
  const container = document.getElementById('desktop-sidebar');
  if (container) container.outerHTML = getDesktopSidebar(activePage);
  // Tampilkan notifikasi yang tertunda dari halaman sebelumnya
  if (typeof _flushPendingToasts === 'function') _flushPendingToasts();
}

function desktopLogout() {
  if (!confirm('Yakin ingin keluar?')) return;
  if (typeof api !== 'undefined') {
    api.post('/auth/logout').finally(() => {
      api.clearTokens();
      window.location.href = '/desktop/login.html';
    });
  }
}

function toggleSidebar() {
  const nav = document.getElementById('desktop-nav');
  const chevron = document.getElementById('sidebar-chevron');
  const labels = document.querySelectorAll('.sidebar-label');
  const collapsed = nav.style.width === '72px';
  if (collapsed) {
    nav.style.width = '256px';
    if (chevron) chevron.textContent = 'chevron_left';
    labels.forEach(l => { l.style.display = ''; });
    document.querySelectorAll('.ml-64').forEach(el => el.style.marginLeft = '256px');
    sessionStorage.setItem('sidebarCollapsed', '0');
  } else {
    nav.style.width = '72px';
    if (chevron) chevron.textContent = 'chevron_right';
    labels.forEach(l => { l.style.display = 'none'; });
    document.querySelectorAll('.ml-64').forEach(el => el.style.marginLeft = '72px');
    sessionStorage.setItem('sidebarCollapsed', '1');
  }
}

function initSidebarState() {
  if (sessionStorage.getItem('sidebarCollapsed') === '1') {
    const nav = document.getElementById('desktop-nav');
    if (!nav) return;
    nav.style.width = '72px';
    const chevron = document.getElementById('sidebar-chevron');
    if (chevron) chevron.textContent = 'chevron_right';
    document.querySelectorAll('.sidebar-label').forEach(l => { l.style.display = 'none'; });
    document.querySelectorAll('.ml-64').forEach(el => el.style.marginLeft = '72px');
  }
}
document.addEventListener('DOMContentLoaded', initSidebarState);

// Switch manual ke versi mobile, dipakai oleh link "Beralih ke versi mobile" di tiap halaman.
function switchToMobileView() {
  sessionStorage.setItem('winemu_view_override', 'mobile');
  const mobilePath = window.location.pathname.replace('/desktop', '') || '/';
  window.location.href = mobilePath;
}
