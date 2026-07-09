// Winemu API Client
const API_BASE = '/api/v1';

const api = {
  getToken() { return localStorage.getItem('access_token'); },
  setTokens(access, refresh) {
    localStorage.setItem('access_token', access);
    if (refresh) localStorage.setItem('refresh_token', refresh);
  },
  clearTokens() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  },
  getUser() {
    try { return JSON.parse(localStorage.getItem('user') || 'null'); } catch { return null; }
  },
  setUser(u) { localStorage.setItem('user', JSON.stringify(u)); },

  async request(method, path, body = null, isFormData = false) {
    const headers = {};
    const token = this.getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
    if (!isFormData) headers['Content-Type'] = 'application/json';

    const opts = { method, headers };
    if (body) opts.body = isFormData ? body : JSON.stringify(body);

    let resp = await fetch(API_BASE + path, opts);

    // Try refresh if 401
    if (resp.status === 401 && localStorage.getItem('refresh_token')) {
      const refreshed = await this.refreshToken();
      if (refreshed) {
        headers['Authorization'] = `Bearer ${this.getToken()}`;
        resp = await fetch(API_BASE + path, { ...opts, headers });
      } else {
        this.clearTokens();
        const loginPath = window.location.pathname.startsWith('/desktop/') ? '/desktop/login.html' : '/login.html';
        window.location.href = loginPath;
        return null;
      }
    }
    try {
      return await resp.json();
    } catch(e) {
      // Server returned non-JSON (e.g. 500 HTML page)
      console.error('API parse error', resp.status, resp.url);
      return { status: 'error', message: `Server error (${resp.status})`, _parseError: true };
    }
  },

  async refreshToken() {
    const refresh = localStorage.getItem('refresh_token');
    if (!refresh) return false;
    const resp = await fetch(API_BASE + '/auth/refresh', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${refresh}`, 'Content-Type': 'application/json' }
    });
    if (resp.ok) {
      const data = await resp.json();
      if (data.data?.access_token) {
        localStorage.setItem('access_token', data.data.access_token);
        return true;
      }
    }
    return false;
  },

  get(path) { return this.request('GET', path); },
  post(path, body) { return this.request('POST', path, body); },
  put(path, body) { return this.request('PUT', path, body); },
  delete(path) { return this.request('DELETE', path); },
  postForm(path, formData) { return this.request('POST', path, formData, true); },
  putForm(path, formData) { return this.request('PUT', path, formData, true); },
};

// Auth guard
function requireAuth() {
  if (!api.getToken()) {
    const loginPath = window.location.pathname.startsWith('/desktop/') ? '/desktop/login.html' : '/login.html';
    window.location.href = loginPath;
    return false;
  }
  return true;
}

function isLoggedIn() {
  return !!api.getToken();
}

// Toast notification
function showToast(message, type = 'success') {
  // Beberapa pemanggilan di seluruh aplikasi mengirim boolean (true = error)
  // alih-alih string type. Diterima di sini agar tetap tampil benar tanpa
  // perlu mengubah setiap titik panggilan satu per satu.
  if (type === true) type = 'error';
  if (type === false) type = 'success';

  const existing = document.getElementById('toast-container');
  if (existing) existing.remove();

  const container = document.createElement('div');
  container.id = 'toast-container';
  container.style.cssText = `
    position: fixed; bottom: 80px; left: 50%; transform: translateX(-50%);
    z-index: 9999; padding: 12px 24px; border-radius: 12px;
    font-family: 'Plus Jakarta Sans', sans-serif; font-size: 14px;
    font-weight: 600; color: white; box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    background: ${type === 'success' ? '#314e52' : type === 'error' ? '#ba1a1a' : '#7d562d'};
  `;
  container.textContent = message;
  document.body.appendChild(container);

  setTimeout(() => container.remove(), 3000);
}

// Format relative time
function timeAgo(dateStr) {
  const date = new Date(dateStr);
  const now = new Date();
  const diff = Math.floor((now - date) / 1000);
  if (diff < 60) return 'Baru saja';
  if (diff < 3600) return `${Math.floor(diff / 60)} menit lalu`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} jam lalu`;
  if (diff < 604800) return `${Math.floor(diff / 86400)} hari lalu`;
  return date.toLocaleDateString('id-ID');
}

// Update nav active state
function setActiveNav(page) {
  document.querySelectorAll('[data-nav]').forEach(el => {
    const nav = el.getAttribute('data-nav');
    const isActive = nav === page;
    el.classList.toggle('text-primary', isActive);
    el.classList.toggle('text-on-surface-variant', !isActive);
    const icon = el.querySelector('.material-symbols-outlined');
    if (icon) {
      icon.style.fontVariationSettings = isActive ? "'FILL' 1" : "'FILL' 0";
    }
  });
}

// Load user avatar in header
async function loadUserInNav() {
  const user = api.getUser();
  if (user) {
    const avatarEls = document.querySelectorAll('[data-user-avatar]');
    avatarEls.forEach(el => {
      if (user.avatar_url) {
        el.src = user.avatar_url;
      }
    });
  }
}
