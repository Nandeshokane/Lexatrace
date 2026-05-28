// ═══ LexaTrace — Main Application Script ═══
// Connects to the FastAPI backend at /api/*

const API_BASE = '';  // Same origin when served by FastAPI

document.addEventListener('DOMContentLoaded', () => {
  initNavbar();
  initScrollAnimations();
  initUploadArea();
  initCounters();
  initDashboardAnimation();
  initAuthUI();
});

// ── Auth State ──
let authToken = localStorage.getItem('lexatrace_token') || null;
let currentUser = JSON.parse(localStorage.getItem('lexatrace_user') || 'null');

function setAuth(token, user) {
  authToken = token;
  currentUser = user;
  localStorage.setItem('lexatrace_token', token);
  localStorage.setItem('lexatrace_user', JSON.stringify(user));
  updateAuthUI();
}

function clearAuth() {
  authToken = null;
  currentUser = null;
  localStorage.removeItem('lexatrace_token');
  localStorage.removeItem('lexatrace_user');
  updateAuthUI();
}

function authHeaders() {
  return authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
}

// ── Auth UI ──
function initAuthUI() {
  // Add auth modal to DOM
  const modal = document.createElement('div');
  modal.id = 'auth-modal';
  modal.innerHTML = `
    <div style="position:fixed;inset:0;background:rgba(0,0,0,0.7);z-index:9999;display:flex;align-items:center;justify-content:center;backdrop-filter:blur(8px);">
      <div style="background:var(--bg-secondary);border:1px solid var(--border-color);border-radius:var(--radius-xl);padding:40px;max-width:420px;width:90%;">
        <h2 style="font-size:24px;font-weight:700;margin-bottom:8px;">
          <span class="gradient-text" id="auth-title">Sign Up</span>
        </h2>
        <p style="color:var(--text-secondary);font-size:14px;margin-bottom:24px;" id="auth-subtitle">Create your account to start scanning</p>
        <div id="auth-error" style="display:none;background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);color:#ef4444;padding:10px 14px;border-radius:8px;font-size:13px;margin-bottom:16px;"></div>
        <div id="auth-username-field" style="margin-bottom:14px;">
          <label style="display:block;font-size:12px;font-weight:600;color:var(--text-secondary);margin-bottom:6px;">Username</label>
          <input id="auth-username" type="text" placeholder="johndoe" style="width:100%;padding:10px 14px;background:var(--bg-primary);border:1px solid var(--border-color);border-radius:8px;color:var(--text-primary);font-size:14px;outline:none;">
        </div>
        <div style="margin-bottom:14px;">
          <label style="display:block;font-size:12px;font-weight:600;color:var(--text-secondary);margin-bottom:6px;">Email</label>
          <input id="auth-email" type="email" placeholder="you@example.com" style="width:100%;padding:10px 14px;background:var(--bg-primary);border:1px solid var(--border-color);border-radius:8px;color:var(--text-primary);font-size:14px;outline:none;">
        </div>
        <div style="margin-bottom:24px;">
          <label style="display:block;font-size:12px;font-weight:600;color:var(--text-secondary);margin-bottom:6px;">Password</label>
          <input id="auth-password" type="password" placeholder="••••••••" style="width:100%;padding:10px 14px;background:var(--bg-primary);border:1px solid var(--border-color);border-radius:8px;color:var(--text-primary);font-size:14px;outline:none;">
        </div>
        <button id="auth-submit" class="btn-primary" style="width:100%;text-align:center;font-size:15px;">Create Account</button>
        <p style="text-align:center;margin-top:16px;font-size:13px;color:var(--text-secondary);">
          <span id="auth-toggle-text">Already have an account?</span>
          <a href="#" id="auth-toggle" style="color:var(--accent-blue);text-decoration:none;font-weight:600;"> Login</a>
        </p>
        <button id="auth-close" style="position:absolute;top:16px;right:16px;background:none;border:none;color:var(--text-muted);font-size:20px;cursor:pointer;">✕</button>
      </div>
    </div>
  `;
  modal.style.display = 'none';
  document.body.appendChild(modal);

  // Event listeners
  document.getElementById('auth-toggle').addEventListener('click', (e) => {
    e.preventDefault();
    toggleAuthMode();
  });
  document.getElementById('auth-submit').addEventListener('click', handleAuth);
  document.getElementById('auth-close').addEventListener('click', () => {
    modal.style.display = 'none';
  });
  document.getElementById('auth-password').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleAuth();
  });

  updateAuthUI();
}

let isLoginMode = false;

function toggleAuthMode() {
  isLoginMode = !isLoginMode;
  document.getElementById('auth-title').textContent = isLoginMode ? 'Welcome Back' : 'Sign Up';
  document.getElementById('auth-subtitle').textContent = isLoginMode ? 'Login to your account' : 'Create your account to start scanning';
  document.getElementById('auth-submit').textContent = isLoginMode ? 'Login' : 'Create Account';
  document.getElementById('auth-toggle-text').textContent = isLoginMode ? "Don't have an account?" : 'Already have an account?';
  document.getElementById('auth-toggle').textContent = isLoginMode ? ' Sign Up' : ' Login';
  document.getElementById('auth-username-field').style.display = isLoginMode ? 'none' : 'block';
  document.getElementById('auth-error').style.display = 'none';
}

function showAuthModal() {
  document.getElementById('auth-modal').style.display = 'block';
}

function updateAuthUI() {
  const cta = document.querySelector('.nav-cta');
  if (cta) {
    if (authToken && currentUser) {
      cta.textContent = `👤 ${currentUser.username}`;
      cta.onclick = (e) => { e.preventDefault(); if(confirm('Logout?')) clearAuth(); };
    } else {
      cta.textContent = 'Start Scanning';
      cta.onclick = (e) => { e.preventDefault(); showAuthModal(); };
    }
  }
}

async function handleAuth() {
  const errorEl = document.getElementById('auth-error');
  errorEl.style.display = 'none';

  const email = document.getElementById('auth-email').value.trim();
  const password = document.getElementById('auth-password').value;
  const username = document.getElementById('auth-username').value.trim();

  if (!email || !password || (!isLoginMode && !username)) {
    errorEl.textContent = 'Please fill all fields';
    errorEl.style.display = 'block';
    return;
  }

  try {
    let res;
    if (isLoginMode) {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);
      res = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData,
      });
    } else {
      res = await fetch(`${API_BASE}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password }),
      });
    }

    const data = await res.json();
    if (!res.ok) {
      errorEl.textContent = data.detail || 'Authentication failed';
      errorEl.style.display = 'block';
      return;
    }

    setAuth(data.access_token, { id: data.user_id, username: data.username });
    document.getElementById('auth-modal').style.display = 'none';
  } catch (err) {
    errorEl.textContent = 'Connection error. Is the backend running?';
    errorEl.style.display = 'block';
  }
}

// ── Navbar scroll effect ──
function initNavbar() {
  const navbar = document.getElementById('navbar');
  window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 50);
  });
}

// ── Intersection Observer for scroll animations ──
function initScrollAnimations() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        setTimeout(() => entry.target.classList.add('visible'), i * 80);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });
  document.querySelectorAll('.animate-in').forEach(el => observer.observe(el));
}

// ── Counter animation ──
function initCounters() {
  const targets = [
    { id: 'stat-docs', end: 52400, suffix: '+' },
    { id: 'stat-patents', end: 100, suffix: 'M+' },
    { id: 'stat-accuracy', end: 97.3, suffix: '%', decimals: 1 },
    { id: 'stat-users', end: 2800, suffix: '+' }
  ];
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const cfg = targets.find(t => t.id === entry.target.id);
        if (cfg) animateCounter(entry.target, cfg);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });
  targets.forEach(t => {
    const el = document.getElementById(t.id);
    if (el) observer.observe(el);
  });
}

function animateCounter(el, cfg) {
  const duration = 2000;
  const start = performance.now();
  const tick = (now) => {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const value = eased * cfg.end;
    el.textContent = cfg.decimals ? value.toFixed(cfg.decimals) + cfg.suffix : Math.floor(value).toLocaleString() + cfg.suffix;
    if (progress < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

// ── Dashboard ring animation ──
function initDashboardAnimation() {
  const ring = document.getElementById('score-ring-fill');
  const scoreVal = document.getElementById('score-value');
  if (!ring || !scoreVal) return;
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const score = 73;
        const circumference = 2 * Math.PI * 85;
        ring.style.strokeDashoffset = circumference - (score / 100) * circumference;
        animateCounter(scoreVal, { end: score, suffix: '' });
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.3 });
  observer.observe(ring.closest('.dashboard-preview'));
}

// ── File Upload Area ──
function initUploadArea() {
  const area = document.getElementById('upload-area');
  const btn = document.getElementById('upload-btn');
  const input = document.getElementById('file-input');
  if (!area || !btn || !input) return;

  btn.addEventListener('click', (e) => { e.stopPropagation(); input.click(); });
  area.addEventListener('click', () => input.click());

  ['dragenter', 'dragover'].forEach(evt =>
    area.addEventListener(evt, (e) => { e.preventDefault(); area.classList.add('drag-over'); })
  );
  ['dragleave', 'drop'].forEach(evt =>
    area.addEventListener(evt, (e) => { e.preventDefault(); area.classList.remove('drag-over'); })
  );
  area.addEventListener('drop', (e) => {
    if (e.dataTransfer.files.length) handleFileUpload(e.dataTransfer.files[0]);
  });
  input.addEventListener('change', () => {
    if (input.files.length) handleFileUpload(input.files[0]);
  });
}

async function handleFileUpload(file) {
  // Check auth
  if (!authToken) {
    showAuthModal();
    return;
  }

  const area = document.getElementById('upload-area');
  const progress = document.getElementById('analysis-progress');

  area.innerHTML = `
    <div style="font-size:36px;margin-bottom:12px;">📄</div>
    <h3 style="margin-bottom:4px;">${escapeHtml(file.name)}</h3>
    <p style="color:var(--text-muted);font-size:13px;">Uploading to server...</p>
  `;
  area.style.cursor = 'default';
  area.style.borderColor = 'var(--accent-blue)';
  area.style.animation = 'pulse-glow 2s ease-in-out infinite';

  try {
    // Step 1: Upload file
    const formData = new FormData();
    formData.append('file', file);

    const uploadRes = await fetch(`${API_BASE}/api/upload`, {
      method: 'POST',
      headers: authHeaders(),
      body: formData,
    });

    if (!uploadRes.ok) {
      const err = await uploadRes.json();
      throw new Error(err.detail || 'Upload failed');
    }

    const uploadData = await uploadRes.json();
    area.querySelector('p').textContent = `Uploaded! Starting analysis...`;

    // Step 2: Trigger analysis
    const analyzeRes = await fetch(`${API_BASE}/api/analyze/${uploadData.file_id}`, {
      method: 'POST',
      headers: authHeaders(),
    });

    if (!analyzeRes.ok) throw new Error('Failed to start analysis');
    const analyzeData = await analyzeRes.json();

    // Step 3: Show progress and poll for results
    progress.classList.add('active');
    pollAnalysis(analyzeData.job_id, file.name);

  } catch (err) {
    area.innerHTML = `
      <div style="font-size:36px;margin-bottom:12px;">❌</div>
      <h3 style="color:var(--risk-high);margin-bottom:4px;">Upload Failed</h3>
      <p style="color:var(--text-secondary);font-size:14px;">${escapeHtml(err.message)}</p>
      <button class="upload-btn" onclick="location.reload()">Try Again</button>
    `;
    area.style.animation = 'none';
    area.style.borderColor = 'var(--risk-high)';
  }
}

async function pollAnalysis(jobId, filename) {
  const steps = ['upload', 'extract', 'embed', 'search', 'report'];
  const statusMap = {
    'pending': 0, 'extracting': 1, 'chunking': 1,
    'embedding': 2, 'searching': 3, 'scoring': 4, 'completed': 5, 'failed': -1,
  };

  let lastStep = -1;

  const poll = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/analysis/${jobId}`, { headers: authHeaders() });
      if (!res.ok) return;
      const data = await res.json();

      const currentStep = statusMap[data.status] ?? 0;

      // Update progress UI
      for (let i = 0; i < steps.length; i++) {
        const stepEl = document.getElementById('step-' + steps[i]);
        const barEl = document.getElementById('bar-' + steps[i]);
        if (i < currentStep) {
          stepEl.classList.remove('active');
          stepEl.classList.add('done');
          stepEl.querySelector('.step-indicator').innerHTML = '✓';
          barEl.style.width = '100%';
        } else if (i === currentStep && currentStep < 5) {
          stepEl.classList.add('active');
          stepEl.querySelector('.step-indicator').innerHTML = '<div class="spinner"></div>';
          barEl.style.width = '60%';
        }
      }

      if (data.status === 'completed') {
        // Mark all done
        steps.forEach(s => {
          const el = document.getElementById('step-' + s);
          const bar = document.getElementById('bar-' + s);
          el.classList.remove('active'); el.classList.add('done');
          el.querySelector('.step-indicator').innerHTML = '✓';
          bar.style.width = '100%';
        });
        completeAnalysis(filename, data);
        return;
      } else if (data.status === 'failed') {
        const area = document.getElementById('upload-area');
        area.style.animation = 'none';
        area.innerHTML = `<div style="font-size:36px;">❌</div><h3 style="color:var(--risk-high);">Analysis Failed</h3><p style="color:var(--text-secondary);font-size:14px;">${escapeHtml(data.error || 'Unknown error')}</p>`;
        return;
      }

      setTimeout(poll, 1500);
    } catch {
      setTimeout(poll, 2000);
    }
  };

  setTimeout(poll, 1000);
}

function completeAnalysis(filename, data) {
  const area = document.getElementById('upload-area');
  area.style.animation = 'none';
  area.style.borderColor = 'var(--risk-low)';
  area.style.borderStyle = 'solid';

  const riskColor = { high: 'var(--risk-high)', medium: 'var(--risk-medium)', low: 'var(--risk-low)', clear: 'var(--risk-clear)' };
  const color = riskColor[data.risk_level] || 'var(--risk-clear)';

  area.innerHTML = `
    <div style="font-size:48px;margin-bottom:12px;">✅</div>
    <h3 style="color:var(--risk-low);margin-bottom:4px;">Analysis Complete!</h3>
    <p style="color:var(--text-secondary);font-size:14px;margin-bottom:8px;">${escapeHtml(filename)}</p>
    <p style="font-size:13px;color:var(--text-muted);">
      Risk Score: <strong style="color:${color};font-size:18px;">${data.risk_score}</strong>/100
      · ${data.total_matches} matches found
    </p>
    <div style="margin-top:16px;display:flex;gap:8px;justify-content:center;flex-wrap:wrap;">
      <a href="#dashboard" class="btn-primary" style="display:inline-block;font-size:13px;padding:10px 20px;">View Results ↓</a>
      <a href="/api/reports/${data.job_id}/html" target="_blank" class="btn-secondary" style="display:inline-block;font-size:13px;padding:10px 20px;">📄 Full Report</a>
    </div>
  `;

  // Update dashboard with real data if available
  if (data.matches) {
    updateDashboardWithResults(data, filename);
  }
}

function updateDashboardWithResults(data, filename) {
  // Update score ring
  const scoreVal = document.getElementById('score-value');
  const ring = document.getElementById('score-ring-fill');
  if (scoreVal && ring) {
    const score = data.risk_score;
    const circumference = 2 * Math.PI * 85;
    ring.style.strokeDashoffset = circumference - (score / 100) * circumference;
    scoreVal.textContent = Math.round(score);
  }

  // Update filename in dashboard
  const dashTitle = document.querySelector('.dash-title');
  if (dashTitle) dashTitle.textContent = `📄 ${filename}`;

  // Update risk badge
  const riskBadge = document.querySelector('.risk-badge');
  if (riskBadge) {
    riskBadge.className = `risk-badge ${data.risk_level}`;
    const labels = { high: '🔴 High Risk', medium: '⚠️ Medium Risk', low: '🟢 Low Risk', clear: '✅ Clear' };
    riskBadge.textContent = labels[data.risk_level] || 'Clear';
  }
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
