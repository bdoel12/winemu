/**
 * Deteksi otomatis device desktop vs mobile, lalu redirect ke versi yang sesuai.
 *
 * Cara pakai: sertakan script ini PALING ATAS di <head>, sebelum konten lain
 * dirender, di SETIAP halaman mobile (frontend/*.html) maupun desktop
 * (frontend/desktop/*.html). Script ini akan:
 *   - Di halaman mobile: jika lebar layar >= breakpoint, redirect ke /desktop/<halaman>
 *   - Di halaman desktop: jika lebar layar < breakpoint, redirect ke /<halaman>
 *
 * Deteksi memakai window.innerWidth (bukan user-agent), karena lebih akurat
 * merepresentasikan pengalaman yang sesuai untuk ukuran layar saat ini -
 * termasuk kasus jendela browser desktop yang di-resize kecil, atau tablet
 * dalam mode lanskap.
 *
 * Sekali pengguna pindah mode secara manual (lewat link "Beralih ke versi
 * mobile/desktop"), preferensi itu disimpan di sessionStorage agar tidak
 * dipaksa redirect lagi sepanjang sesi browser itu masih terbuka.
 */
(function () {
  var DESKTOP_BREAKPOINT = 1024; // px - cocok dengan breakpoint `lg` Tailwind

  var path = window.location.pathname;
  var isDesktopPage = path.startsWith('/desktop/');

  var manualOverride = sessionStorage.getItem('winemu_view_override');
  if (manualOverride === 'desktop' || manualOverride === 'mobile') {
    // Pengguna sudah memilih manual - jangan paksa redirect otomatis.
    var wantsDesktop = manualOverride === 'desktop';
    if (wantsDesktop && !isDesktopPage) {
      window.location.replace('/desktop' + path);
    } else if (!wantsDesktop && isDesktopPage) {
      window.location.replace(path.replace('/desktop', '') || '/');
    }
    return;
  }

  var isWideScreen = window.innerWidth >= DESKTOP_BREAKPOINT;

  if (isWideScreen && !isDesktopPage) {
    window.location.replace('/desktop' + path);
  } else if (!isWideScreen && isDesktopPage) {
    var mobilePath = path.replace('/desktop', '');
    window.location.replace(mobilePath === '' ? '/' : mobilePath);
  }
})();
