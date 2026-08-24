const landing = document.querySelector('#landingPage');
const experience = document.querySelector('#productExperience');
const experienceClose = document.querySelector('#experienceClose');
const menuToggle = document.querySelector('#menuToggle');
const mobileMenu = document.querySelector('#mobileMenu');
const video = document.querySelector('#backgroundVideo');
const videoToggle = document.querySelector('#videoToggle');

const landingCopy = {
  en: {
    navHome: 'Home', navProduct: 'Product', navEvidence: 'Evidence', navAllocation: 'Allocation Lab', openDrsk: 'Open DRSK',
    trust: 'SOURCECHAIN · DRSK · NIYET', headlineOne: 'Evidence-Aware', headlineTwo: 'Social Coordination',
    subhead: 'Trace claims to evidence, make uncertainty visible, and route human attention through one research-grade social layer.',
    cta: 'Explore the live system', statEngines: 'Coordinated engines', statIntents: 'Intent routes', statTrace: 'Truthful evidence trace',
    statLanguages: 'Interface languages', pauseMotion: 'Pause motion', resumeMotion: 'Resume motion', backLanding: 'Back to landing',
    menuOpen: 'Open navigation', menuClose: 'Close navigation'
  },
  tr: {
    navHome: 'Ana Sayfa', navProduct: 'Ürün', navEvidence: 'Kanıt', navAllocation: 'Dağıtım Laboratuvarı', openDrsk: "DRSK'yi Aç",
    trust: 'SOURCECHAIN · DRSK · NIYET', headlineOne: 'Kanıt Duyarlı', headlineTwo: 'Sosyal Koordinasyon',
    subhead: 'İddiaları kanıta bağla, belirsizliği görünür kıl ve insan dikkatini araştırma düzeyinde tek bir sosyal katmanda yönlendir.',
    cta: 'Canlı sistemi keşfet', statEngines: 'Koordine motor', statIntents: 'Niyet rotası', statTrace: 'Dürüst kanıt izi',
    statLanguages: 'Arayüz dili', pauseMotion: 'Hareketi duraklat', resumeMotion: 'Hareketi sürdür', backLanding: 'Açılışa dön',
    menuOpen: 'Gezinmeyi aç', menuClose: 'Gezinmeyi kapat'
  }
};

const reduceQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
const query = new URLSearchParams(window.location.search);
let reducedMotion = reduceQuery.matches || query.get('reduce') === '1';
let userPaused = false;
let lastLandingFocus = null;

function landingText(key) {
  const language = localStorage.getItem('drsk-language') || 'en';
  return landingCopy[language]?.[key] || landingCopy.en[key] || key;
}

function applyLandingLanguage(language, persist = true) {
  const next = language === 'tr' ? 'tr' : 'en';
  if (persist) localStorage.setItem('drsk-language', next);
  document.querySelectorAll('[data-landing-key]').forEach((node) => {
    node.textContent = landingCopy[next][node.dataset.landingKey] || node.textContent;
  });
  document.querySelectorAll('[data-landing-lang]').forEach((button) => {
    const active = button.dataset.landingLang === next;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  });
  menuToggle.setAttribute('aria-label', landingCopy[next][mobileMenu.hidden ? 'menuOpen' : 'menuClose']);
  updateVideoToggle(next);
  if (persist) document.querySelector(`.lang-switch button[data-lang="${next}"]`)?.click();
}

function updateVideoToggle(language = localStorage.getItem('drsk-language') || 'en') {
  const paused = video.paused;
  const key = paused ? 'resumeMotion' : 'pauseMotion';
  const label = landingCopy[language]?.[key] || landingCopy.en[key];
  videoToggle.querySelector('b').textContent = label;
  videoToggle.setAttribute('aria-label', label);
  videoToggle.setAttribute('aria-pressed', String(paused));
  videoToggle.querySelector('span').textContent = paused ? '▶' : 'Ⅱ';
}

function setMenu(open) {
  mobileMenu.hidden = !open;
  menuToggle.classList.toggle('open', open);
  menuToggle.setAttribute('aria-expanded', String(open));
  document.body.classList.toggle('menu-open', open);
  menuToggle.setAttribute('aria-label', landingText(open ? 'menuClose' : 'menuOpen'));
  if (open) mobileMenu.querySelector('button, a')?.focus();
}

function openExperience(trigger = document.activeElement) {
  lastLandingFocus = trigger;
  setMenu(false);
  experience.hidden = false;
  document.body.classList.add('experience-open');
  landing.setAttribute('aria-hidden', 'true');
  landing.inert = true;
  video.pause();
  experienceClose.focus();
  history.replaceState(null, '', '#product');
}

function closeExperience() {
  if (experience.hidden) return;
  experience.hidden = true;
  document.body.classList.remove('experience-open');
  landing.removeAttribute('aria-hidden');
  landing.inert = false;
  history.replaceState(null, '', `${location.pathname}${location.search}`);
  if (!reducedMotion && !userPaused) video.play().catch(() => {});
  (lastLandingFocus || document.querySelector('.landing-cta')).focus();
}

function openEvidence(trigger) {
  openExperience(trigger);
  const composer = document.querySelector('#composerText');
  if (!composer) return;
  composer.value = 'Research proves coffee consumption causes lower mortality.';
  composer.dispatchEvent(new Event('input', { bubbles: true }));
  composer.focus();
}

function setCounterFinal(stat) {
  const target = Number(stat.dataset.target || 0);
  const decimals = Number(stat.dataset.decimals || 0);
  stat.querySelector('.stat-value').textContent = target.toFixed(decimals);
}

function animateCounter(stat, index) {
  if (stat.dataset.counted === 'true') return;
  stat.dataset.counted = 'true';
  if (reducedMotion) { setCounterFinal(stat); return; }
  const target = Number(stat.dataset.target || 0);
  const decimals = Number(stat.dataset.decimals || 0);
  const duration = 1500 + index * 80;
  const startDelay = 480 + index * 90;
  window.setTimeout(() => {
    const start = performance.now();
    const tick = (now) => {
      const progress = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - progress, 3);
      stat.querySelector('.stat-value').textContent = (target * eased).toFixed(decimals);
      if (progress < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }, startDelay);
}

document.querySelectorAll('[data-open-experience]').forEach((button) => button.addEventListener('click', () => openExperience(button)));
document.querySelectorAll('[data-open-evidence]').forEach((button) => button.addEventListener('click', () => openEvidence(button)));
document.querySelectorAll('[data-landing-home]').forEach((button) => button.addEventListener('click', () => { setMenu(false); closeExperience(); }));
document.querySelectorAll('[data-landing-lang]').forEach((button) => button.addEventListener('click', () => applyLandingLanguage(button.dataset.landingLang)));

experienceClose.addEventListener('click', closeExperience);
menuToggle.addEventListener('click', () => setMenu(mobileMenu.hidden));
mobileMenu.addEventListener('click', (event) => { if (event.target === mobileMenu) setMenu(false); });
mobileMenu.querySelectorAll('a, button').forEach((node) => node.addEventListener('click', () => {
  if (!node.hasAttribute('data-open-experience') && !node.hasAttribute('data-open-evidence')) setMenu(false);
}));

videoToggle.addEventListener('click', () => {
  if (video.paused) {
    userPaused = false;
    if (!reducedMotion) video.play().catch(() => {});
  } else {
    userPaused = true;
    video.pause();
  }
  updateVideoToggle();
});
video.addEventListener('play', updateVideoToggle);
video.addEventListener('pause', updateVideoToggle);

document.addEventListener('keydown', (event) => {
  if (event.key !== 'Escape') return;
  if (!mobileMenu.hidden) { setMenu(false); return; }
  if (document.querySelector('.explain-sheet.visible, .right-rail.mobile-open')) return;
  closeExperience();
});

window.addEventListener('resize', () => { if (window.innerWidth > 720) setMenu(false); });

reduceQuery.addEventListener('change', (event) => {
  reducedMotion = event.matches || query.get('reduce') === '1';
  document.documentElement.classList.toggle('motion-reduced', reducedMotion);
  if (reducedMotion) video.pause();
  else if (!userPaused && experience.hidden) video.play().catch(() => {});
  updateVideoToggle();
});

const stats = [...document.querySelectorAll('.landing-stat')];
if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      animateCounter(entry.target, stats.indexOf(entry.target));
      observer.unobserve(entry.target);
    });
  }, { threshold: .25 });
  stats.forEach((stat) => observer.observe(stat));
} else stats.forEach(animateCounter);

document.querySelector('.product-wordmark[href="/"]')?.addEventListener('click', (event) => { event.preventDefault(); closeExperience(); });

applyLandingLanguage(localStorage.getItem('drsk-language') || 'en', false);
document.documentElement.classList.toggle('motion-reduced', reducedMotion);
if (reducedMotion) video.pause();
else video.play().catch(() => {});
updateVideoToggle();
if (location.hash === '#product') openExperience(document.querySelector('.landing-cta'));
window.__ready = true;
