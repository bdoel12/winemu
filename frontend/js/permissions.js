/**
 * Winemu - Permission Request Dialog
 *
 * Aturan:
 * - Hanya muncul SEKALI SELAMANYA per browser (localStorage flag).
 * - Hanya minta Lokasi + Notifikasi. Mikrofon & Kamera diminta saat panggilan.
 */
(function () {
  function init() {
    if (typeof api === 'undefined' || !api.getToken()) return;

    // Sudah pernah tampil? Skip selamanya.
    if (localStorage.getItem('winemu_perms_shown') === '1') return;

    // Set flag SEKARANG sebelum apapun dirender
    localStorage.setItem('winemu_perms_shown', '1');

    _buildDialog();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // ── Styles ─────────────────────────────────────────────────────────────
  function _injectStyles() {
    if (document.getElementById('perm-dialog-style')) return;
    var s = document.createElement('style');
    s.id = 'perm-dialog-style';
    s.textContent = `
      @keyframes permBackdropIn { from{opacity:0} to{opacity:1} }
      @keyframes permCardIn {
        from { opacity:0; transform:scale(0.93) translateY(-12px); }
        to   { opacity:1; transform:scale(1)    translateY(0);     }
      }
      @keyframes permCardOut {
        from { opacity:1; transform:scale(1)    translateY(0);    }
        to   { opacity:0; transform:scale(0.93) translateY(-8px); }
      }
      #perm-dialog-backdrop { animation: permBackdropIn 0.22s ease forwards; }
      #perm-dialog-card     { animation: permCardIn 0.28s cubic-bezier(0.34,1.56,0.64,1) forwards; }
      .perm-item {
        display:flex; align-items:center; gap:12px;
        padding:10px 0; border-bottom:1px solid #e5e2dd;
      }
      .perm-item:last-child { border-bottom:none; }
      .perm-icon-wrap {
        width:40px; height:40px; border-radius:50%;
        display:flex; align-items:center; justify-content:center; flex-shrink:0;
      }
      .perm-status {
        width:22px; height:22px; border-radius:50%;
        display:flex; align-items:center; justify-content:center;
        font-size:13px; flex-shrink:0; margin-left:auto;
      }
      .perm-status.granted { background:#d4edda; color:#1e7e34; }
      .perm-status.denied  { background:#f8d7da; color:#721c24; }
      .perm-status.pending { background:#e5e2dd; color:#414849; }
    `;
    document.head.appendChild(s);
  }

  // ── Hanya Lokasi + Notifikasi ──────────────────────────────────────────
  var PERMISSIONS = [
    {
      id:'location', label:'Lokasi',
      desc:'Untuk menampilkan laporan di sekitar Anda',
      icon:'location_on', color:'#314E52', bg:'#e8f4f1',
      request: function() {
        return new Promise(function(resolve) {
          if (!navigator.geolocation) return resolve('denied');
          navigator.geolocation.getCurrentPosition(
            function(){ resolve('granted'); },
            function(){ resolve('denied'); },
            { timeout: 8000 }
          );
        });
      }
    },
    {
      id:'notifications', label:'Notifikasi',
      desc:'Untuk menerima pemberitahuan klaim, pesan, dan like',
      icon:'notifications_active', color:'#5c4a9e', bg:'#ede7f6',
      request: function() {
        if (!('Notification' in window)) return Promise.resolve('denied');
        return Notification.requestPermission()
          .then(function(r){ return r === 'granted' ? 'granted' : 'denied'; });
      }
    },
  ];

  // ── Build dialog ───────────────────────────────────────────────────────
  function _buildDialog() {
    _injectStyles();

    var backdrop = document.createElement('div');
    backdrop.id = 'perm-dialog-backdrop';
    backdrop.style.cssText = [
      'position:fixed;inset:0;z-index:99999;',
      'background:rgba(0,0,0,0.5);backdrop-filter:blur(4px);',
      'display:flex;align-items:center;justify-content:center;',
      'padding:16px;',
    ].join('');

    var card = document.createElement('div');
    card.id = 'perm-dialog-card';
    card.style.cssText = [
      'width:100%;max-width:400px;',
      'background:#fcf9f4;border-radius:20px;',
      'padding:24px;',
      "font-family:'Plus Jakarta Sans',sans-serif;",
      'box-shadow:0 24px 60px rgba(0,0,0,0.25);',
    ].join('');

    var itemsHTML = PERMISSIONS.map(function(p) {
      return '<div class="perm-item" id="perm-item-' + p.id + '">' +
        '<div class="perm-icon-wrap" style="background:' + p.bg + ';">' +
          '<span class="material-symbols-outlined" style="color:' + p.color + ';font-size:22px;font-variation-settings:\'FILL\' 1;">' + p.icon + '</span>' +
        '</div>' +
        '<div style="flex:1;min-width:0;">' +
          '<div style="font-weight:700;font-size:14px;color:#1c1c19;">' + p.label + '</div>' +
          '<div style="font-size:12px;color:#727879;margin-top:1px;">' + p.desc + '</div>' +
        '</div>' +
        '<div class="perm-status pending" id="perm-status-' + p.id + '" title="Menunggu">' +
          '<span class="material-symbols-outlined" style="font-size:15px;font-variation-settings:\'FILL\' 1;">hourglass_empty</span>' +
        '</div>' +
      '</div>';
    }).join('');

    card.innerHTML =
      '<div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">' +
        '<div style="width:40px;height:40px;border-radius:50%;background:#314E52;display:flex;align-items:center;justify-content:center;flex-shrink:0;">' +
          '<span class="material-symbols-outlined" style="color:#fff;font-size:22px;font-variation-settings:\'FILL\' 1;">security</span>' +
        '</div>' +
        '<div>' +
          '<div style="font-weight:800;font-size:18px;color:#1a373b;line-height:1.2;">Izin Aplikasi</div>' +
          '<div style="font-size:13px;color:#727879;margin-top:2px;">Winemu memerlukan izin berikut</div>' +
        '</div>' +
      '</div>' +
      '<div style="height:1px;background:#e5e2dd;margin-bottom:4px;"></div>' +
      '<div id="perm-list">' + itemsHTML + '</div>' +
      '<div style="margin-top:14px;padding:10px 12px;background:#e8f4f1;border-radius:10px;display:flex;gap:8px;align-items:flex-start;">' +
        '<span class="material-symbols-outlined" style="font-size:15px;color:#314E52;flex-shrink:0;margin-top:1px;font-variation-settings:\'FILL\' 1;">info</span>' +
        '<div style="font-size:11px;color:#2e4b4f;line-height:1.5;">Izin digunakan hanya untuk fitur aplikasi dan tidak dibagikan ke pihak ketiga. Anda dapat mengubah izin kapan saja melalui pengaturan browser.</div>' +
      '</div>' +
      '<div style="margin-top:16px;display:flex;gap:10px;">' +
        '<button id="perm-skip-btn" style="flex:1;height:46px;border-radius:12px;border:2px solid #c1c8c9;background:transparent;color:#414849;font-weight:700;font-size:14px;cursor:pointer;font-family:inherit;" onmouseover="this.style.background=\'#f0ede9\'" onmouseout="this.style.background=\'transparent\'">Lewati</button>' +
        '<button id="perm-grant-btn" style="flex:2;height:46px;border-radius:12px;border:none;background:#314E52;color:#fff;font-weight:700;font-size:14px;cursor:pointer;font-family:inherit;box-shadow:0 4px 16px rgba(49,78,82,0.3);" onmouseover="this.style.opacity=\'0.88\'" onmouseout="this.style.opacity=\'1\'">Izinkan</button>' +
      '</div>';

    backdrop.appendChild(card);
    document.body.appendChild(backdrop);

    function setStatus(id, status) {
      var el = document.getElementById('perm-status-' + id);
      if (!el) return;
      el.className = 'perm-status ' + status;
      var iconMap = { granted:'check_circle', denied:'cancel', pending:'hourglass_empty' };
      var titleMap = { granted:'Diizinkan', denied:'Ditolak', pending:'Menunggu' };
      el.title = titleMap[status] || '';
      el.innerHTML = '<span class="material-symbols-outlined" style="font-size:15px;font-variation-settings:\'FILL\' 1;">' + (iconMap[status] || 'hourglass_empty') + '</span>';
    }

    function closeDialog() {
      card.style.animation = 'permCardOut 0.2s ease forwards';
      backdrop.style.animation = 'permBackdropIn 0.2s ease reverse forwards';
      setTimeout(function() { if (backdrop.parentElement) backdrop.remove(); }, 220);
    }

    document.getElementById('perm-grant-btn').addEventListener('click', function() {
      var grantBtn = this;
      grantBtn.disabled = true;
      grantBtn.textContent = 'Memproses...';
      grantBtn.style.opacity = '0.7';
      document.getElementById('perm-skip-btn').disabled = true;

      var chain = Promise.resolve();
      PERMISSIONS.forEach(function(perm) {
        chain = chain.then(function() {
          setStatus(perm.id, 'pending');
          return perm.request()
            .then(function(result) { setStatus(perm.id, result); })
            .catch(function() { setStatus(perm.id, 'denied'); })
            .then(function() { return new Promise(function(r){ setTimeout(r, 300); }); });
        });
      });

      chain.then(function() {
        grantBtn.textContent = 'Selesai ✓';
        grantBtn.style.background = '#2e7d32';
        grantBtn.style.opacity = '1';
        setTimeout(closeDialog, 1200);
      });
    });

    document.getElementById('perm-skip-btn').addEventListener('click', closeDialog);
  }
})();
