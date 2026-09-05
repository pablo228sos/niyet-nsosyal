// Preserve the existing evidence entry URL while opening directly on the product.
const query = new URLSearchParams(window.location.search);
function openEvidence() {
  const composer = document.querySelector('#composerText');
  if (!composer.value) composer.value = 'Research proves coffee consumption causes lower mortality.';
  composer.focus();
  composer.dispatchEvent(new Event('input', { bubbles: true }));
}
if (query.get('open') === 'evidence') {
  if (window.__drskAppReady) openEvidence();
  else window.addEventListener('drsk-app-ready', openEvidence, { once: true });
}
window.__ready = true;
