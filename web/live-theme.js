(() => {
  const root = document.documentElement;
  const metaTheme = document.querySelector('meta[name="theme-color"]');
  const copy = {
    en: {
      home: 'Home', notifications: 'Notifications', messages: 'Messages', discover: 'Discover', gameHub: 'Game Hub',
      communities: 'Communities', saved: 'Saved', likes: 'Likes', newPost: 'New post', media: 'Media', theme: 'Dark mode',
      search: 'Search', popular: 'Popular', viewAll: 'View all', trendActive: 'active now', trendGrowing: 'growing', trendToday: 'today'
    },
    tr: {
      home: 'Ana Sayfa', notifications: 'Bildirimler', messages: 'Mesajlar', discover: 'Keşfet', gameHub: 'Oyun Merkezi',
      communities: 'Topluluklar', saved: 'Kaydedilenler', likes: 'Beğeniler', newPost: 'Yeni gönderi', media: 'Medya', theme: 'Karanlık mod',
      search: 'Ara', popular: 'Popüler', viewAll: 'Tümünü gör', trendActive: 'şimdi aktif', trendGrowing: 'yükseliyor', trendToday: 'bugün'
    }
  };

  function currentLanguage() {
    return root.lang === 'tr' ? 'tr' : 'en';
  }

  function currentTheme() {
    return root.dataset.theme === 'dark' ? 'dark' : 'light';
  }

  function applyShellCopy() {
    const lang = currentLanguage();
    document.querySelectorAll('[data-shell-copy]').forEach((node) => {
      const value = copy[lang][node.dataset.shellCopy];
      if (value) node.textContent = value;
    });
    document.querySelectorAll('[data-shell-placeholder]').forEach((node) => {
      const value = copy[lang][node.dataset.shellPlaceholder];
      if (value) node.placeholder = value;
    });
  }

  function applyTheme(theme, persist = true) {
    const next = theme === 'dark' ? 'dark' : 'light';
    root.dataset.theme = next;
    if (persist) localStorage.setItem('drsk-live-theme', next);
    if (metaTheme) metaTheme.content = next === 'dark' ? '#181b23' : '#ffffff';
    document.querySelectorAll('[data-theme-toggle]').forEach((button) => {
      const dark = next === 'dark';
      button.setAttribute('aria-pressed', String(dark));
      button.setAttribute('aria-label', dark ? 'Use light theme' : 'Use dark theme');
      const indicator = button.querySelector('.switch-mini');
      if (indicator) indicator.setAttribute('aria-hidden', 'true');
    });
  }

  const savedTheme = localStorage.getItem('drsk-live-theme');
  const preferredTheme = window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  applyTheme(savedTheme || preferredTheme, Boolean(savedTheme));
  applyShellCopy();

  document.querySelectorAll('[data-theme-toggle]').forEach((button) => {
    button.addEventListener('click', () => applyTheme(currentTheme() === 'dark' ? 'light' : 'dark'));
  });

  document.querySelector('[data-shell-scroll-compose]')?.addEventListener('click', () => {
    document.querySelector('#composer')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    window.setTimeout(() => document.querySelector('#requestText')?.focus(), 250);
  });

  new MutationObserver((mutations) => {
    if (mutations.some((item) => item.attributeName === 'lang')) applyShellCopy();
  }).observe(root, { attributes: true, attributeFilter: ['lang'] });
})();
