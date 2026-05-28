// ═══ LexaTrace — Main Application Script ═══

document.addEventListener('DOMContentLoaded', () => {
  initNavbar();
  initScrollAnimations();
  initUploadArea();
  initCounters();
  initDashboardAnimation();
});

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
    if (cfg.decimals) {
      el.textContent = value.toFixed(cfg.decimals) + cfg.suffix;
    } else {
      el.textContent = Math.floor(value).toLocaleString() + cfg.suffix;
    }
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
        const offset = circumference - (score / 100) * circumference;
        ring.style.strokeDashoffset = offset;
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
    const files = e.dataTransfer.files;
    if (files.length) startAnalysis(files[0].name);
  });

  input.addEventListener('change', () => {
    if (input.files.length) startAnalysis(input.files[0].name);
  });
}

// ── Simulated Analysis Pipeline ──
function startAnalysis(filename) {
  const area = document.getElementById('upload-area');
  const progress = document.getElementById('analysis-progress');

  // Update upload area to show selected file
  area.innerHTML = `
    <div style="font-size:36px;margin-bottom:12px;">📄</div>
    <h3 style="margin-bottom:4px;">${escapeHtml(filename)}</h3>
    <p style="color:var(--text-muted);font-size:13px;">Analysis in progress...</p>
  `;
  area.style.cursor = 'default';
  area.style.borderColor = 'var(--accent-blue)';
  area.style.animation = 'pulse-glow 2s ease-in-out infinite';

  progress.classList.add('active');

  const steps = ['upload', 'extract', 'embed', 'search', 'report'];
  let current = 0;

  function runStep() {
    if (current >= steps.length) {
      completeAnalysis(filename);
      return;
    }
    const stepId = steps[current];
    const stepEl = document.getElementById('step-' + stepId);
    const barEl = document.getElementById('bar-' + stepId);

    stepEl.classList.add('active');
    stepEl.querySelector('.step-indicator').innerHTML = '<div class="spinner"></div>';

    // Animate progress bar
    let barProgress = 0;
    const barInterval = setInterval(() => {
      barProgress += Math.random() * 15 + 5;
      if (barProgress > 100) barProgress = 100;
      barEl.style.width = barProgress + '%';
      if (barProgress >= 100) {
        clearInterval(barInterval);
        stepEl.classList.remove('active');
        stepEl.classList.add('done');
        stepEl.querySelector('.step-indicator').innerHTML = '✓';
        current++;
        setTimeout(runStep, 300);
      }
    }, 200);
  }

  setTimeout(runStep, 500);
}

function completeAnalysis(filename) {
  const area = document.getElementById('upload-area');
  area.style.animation = 'none';
  area.style.borderColor = 'var(--risk-low)';
  area.style.borderStyle = 'solid';
  area.innerHTML = `
    <div style="font-size:48px;margin-bottom:12px;">✅</div>
    <h3 style="color:var(--risk-low);margin-bottom:4px;">Analysis Complete!</h3>
    <p style="color:var(--text-secondary);font-size:14px;margin-bottom:16px;">${escapeHtml(filename)} — 16 matches found across 4 databases</p>
    <a href="#dashboard" class="btn-primary" style="display:inline-block;font-size:14px;padding:10px 24px;">View Results ↓</a>
  `;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
