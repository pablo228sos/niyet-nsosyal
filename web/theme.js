/* Shared appearance preference. Dark is the supplied NIYET brand's default. */
(() => {
  let selected = 'dark';
  try { selected = localStorage.getItem('niyet-theme') === 'light' ? 'light' : 'dark'; } catch (_) {}
  document.documentElement.dataset.theme = selected;
  const sync = () => {
    const tr = document.documentElement.lang === 'tr';
    document.querySelectorAll('[data-theme-toggle]').forEach(button => {
      const light = document.documentElement.dataset.theme === 'light';
      button.setAttribute('aria-pressed', String(light));
      button.setAttribute('aria-label', tr ? 'Açık tema' : 'Light appearance');
      button.title = tr ? 'Temayı değiştir' : 'Change appearance';
    });
  };
  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-theme-toggle]').forEach(button => button.addEventListener('click', () => {
      selected = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
      document.documentElement.dataset.theme = selected;
      try { localStorage.setItem('niyet-theme', selected); } catch (_) {}
      sync();
    }));
    new MutationObserver(sync).observe(document.documentElement, { attributes: true, attributeFilter: ['lang'] });
    sync();
  });
})();
