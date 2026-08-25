const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

const LAB_COPY = {
  en: {
    productNav: 'Product navigation', homeLabel: 'DRSK home', language: 'Language', navigation: 'Navigation', menuOpen: 'Open navigation', menuClose: 'Close navigation',
    feed: 'Feed', evidence: 'Evidence', allocationLab: 'Allocation Lab', openDrsk: 'Open DRSK', backFeed: '← Back to feed',
    labSubtitle: 'Same requests. Same responder capacity. Different allocation strategies.', benchmark: 'Development benchmark', checkingApi: 'checking API',
    retrieve: 'Retrieve', retrieveText: 'Only responders who accept the intent and pass the topic floor enter the candidate graph.',
    constrain: 'Constrain', constrainText: 'Each responder has one slot in this lab, so requests compete for limited attention.',
    allocate: 'Allocate', allocateText: 'Greedy chooses locally. Global assignment evaluates the batch together.', controls: 'Experiment controls', batchGroup: 'Benchmark batch', batch: 'Batch',
    topicFloor: 'Topic floor', topicFloorHelp: 'Weak retrieval edges are removed before optimization.', whatChanged: 'What changed?', comparison: 'Allocation comparison', baseline: 'Baseline', greedyTitle: 'Capacity-aware greedy', localChoice: 'local choice', globalTitle: 'Global allocation', batchChoice: 'batch choice',
    howToRead: 'How to read this lab', labNote: 'The benchmark is currently marked team_review_pending. Relevance grades are development labels. The lab makes the algorithm, tradeoffs and failure cases inspectable without presenting draft labels as field performance.',
    coverage: 'Coverage', meanRelevance: 'Mean relevance', totalRelevance: 'Total relevance', empty: 'No assignment cleared the current topic floor.', similarity: 'lexical similarity', gradeTitle: 'Draft human relevance grade',
    summaryBest: 'Global allocation improves coverage without reducing average draft relevance in this batch.', summaryBestText: 'This is the strongest case for batch-level allocation, but it is still a development benchmark until labels are reviewed and frozen.',
    summaryTradeoff: 'Global allocation serves more requests, but the extra coverage costs some average match quality.', summaryTradeoffText: 'This is the tradeoff NIYET must manage. Raising the topic floor can remove weak candidate edges before optimization.',
    summaryQuality: 'Coverage is unchanged, but global allocation improves the average match quality in this batch.', summaryQualityText: 'The optimizer is using the same responder capacity differently rather than simply increasing the number of assignments.',
    summaryFailure: 'Global allocation is not better on every batch. This case stays visible on purpose.', summaryFailureText: 'The lab exposes failure cases and threshold sensitivity instead of selecting only examples where NIYET wins.',
    delta: 'draft relevance points vs greedy', apiError: 'The experiment API is unavailable.', apiErrorText: 'No fallback metrics are shown. Reload after the live backend is available.', noFallback: 'no synthetic fallback', status: 'Status', offline: 'offline', apiUnavailable: 'API unavailable', liveApi: 'live API'
  },
  tr: {
    productNav: 'Ürün gezinmesi', homeLabel: 'DRSK ana sayfası', language: 'Dil', navigation: 'Gezinme', menuOpen: 'Gezinmeyi aç', menuClose: 'Gezinmeyi kapat',
    feed: 'Akış', evidence: 'Kanıt', allocationLab: 'Dağıtım Laboratuvarı', openDrsk: "DRSK'yi Aç", backFeed: '← Akışa dön',
    labSubtitle: 'Aynı istekler. Aynı yanıtlayıcı kapasitesi. Farklı dağıtım stratejileri.', benchmark: 'Geliştirme karşılaştırması', checkingApi: 'API kontrol ediliyor',
    retrieve: 'Adayları getir', retrieveText: 'Yalnızca niyeti kabul eden ve konu eşiğini geçen yanıtlayıcılar aday grafiğine girer.',
    constrain: 'Kısıtla', constrainText: 'Bu laboratuvarda her yanıtlayıcının tek yuvası vardır; istekler sınırlı dikkat için yarışır.',
    allocate: 'Dağıt', allocateText: 'Greedy yerel seçim yapar. Global dağıtım tüm grubu birlikte değerlendirir.', controls: 'Deney kontrolleri', batchGroup: 'Karşılaştırma grubu', batch: 'Grup',
    topicFloor: 'Konu eşiği', topicFloorHelp: 'Zayıf getirme bağlantıları optimizasyondan önce çıkarılır.', whatChanged: 'Ne değişti?', comparison: 'Dağıtım karşılaştırması', baseline: 'Temel yöntem', greedyTitle: 'Kapasite duyarlı greedy', localChoice: 'yerel seçim', globalTitle: 'Global dağıtım', batchChoice: 'grup seçimi',
    howToRead: 'Bu laboratuvar nasıl okunur', labNote: 'Karşılaştırma team_review_pending olarak işaretlidir. İlgi dereceleri geliştirme etiketleridir. Laboratuvar, taslak etiketleri saha performansı gibi sunmadan algoritmayı, ödünleşimleri ve başarısızlık durumlarını incelenebilir kılar.',
    coverage: 'Kapsama', meanRelevance: 'Ortalama ilgi', totalRelevance: 'Toplam ilgi', empty: 'Mevcut konu eşiğini geçen dağıtım yok.', similarity: 'sözcüksel benzerlik', gradeTitle: 'Taslak insan ilgi derecesi',
    summaryBest: 'Global dağıtım bu grupta ortalama taslak ilgiyi düşürmeden kapsamayı artırıyor.', summaryBestText: 'Bu, grup düzeyi dağıtımın en güçlü örneğidir; etiketler gözden geçirilip dondurulana kadar geliştirme karşılaştırmasıdır.',
    summaryTradeoff: 'Global dağıtım daha fazla isteğe hizmet ediyor, ancak ek kapsama ortalama eşleşme kalitesini düşürüyor.', summaryTradeoffText: 'NIYET bu ödünleşimi yönetir. Konu eşiğini yükseltmek zayıf aday bağlantılarını optimizasyondan önce çıkarabilir.',
    summaryQuality: 'Kapsama aynı, fakat global dağıtım bu grupta ortalama eşleşme kalitesini yükseltiyor.', summaryQualityText: 'Optimizasyon, dağıtım sayısını artırmak yerine aynı yanıtlayıcı kapasitesini farklı kullanıyor.',
    summaryFailure: 'Global dağıtım her grupta daha iyi değil. Bu durum bilerek görünür tutuluyor.', summaryFailureText: 'Laboratuvar yalnızca NIYET’in kazandığı örnekleri seçmek yerine başarısızlıkları ve eşik hassasiyetini açığa çıkarır.',
    delta: 'greedy yöntemine göre taslak ilgi puanı', apiError: 'Deney API’sine ulaşılamıyor.', apiErrorText: 'Yedek metrik gösterilmiyor. Canlı backend kullanılabilir olduğunda yeniden yükleyin.', noFallback: 'sentetik yedek yok', status: 'Durum', offline: 'çevrimdışı', apiUnavailable: 'API kullanılamıyor', liveApi: 'canlı API'
  }
};

let labLanguage = localStorage.getItem('drsk-language') === 'tr' ? 'tr' : 'en';
const t = (key) => LAB_COPY[labLanguage][key] || LAB_COPY.en[key] || key;
const escapeHtml = (value) => String(value ?? '').replace(/[&<>'"]/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[character]);

let activeBatch = 0;
let floor = 0.06;
let requestToken = 0;

function pct(value) {
  return `${Math.round(Number(value || 0) * 100)}%`;
}

function relevance(value) {
  return Number(value || 0).toFixed(2);
}

function metric(label, value) {
  return `<div class="metric"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`;
}

function assignmentRow(row) {
  const grade = Number(row.draft_relevance ?? 0);
  return `
    <div class="assignment">
      <div>
        <div class="assignment-intent">
          <span class="intent-pill">${escapeHtml(row.intent)}</span>
          <span class="assignment-meta">→ ${escapeHtml(row.responder)}</span>
        </div>
        <p>${escapeHtml(row.query)}</p>
        <div class="assignment-meta">${t('similarity')} ${Number(row.similarity).toFixed(3)}</div>
      </div>
      <div class="grade g${grade}" title="${t('gradeTitle')}">${grade}/3</div>
    </div>`;
}

function renderMethod(method, prefix) {
  $(`#${prefix}Metrics`).innerHTML = [
    metric(t('coverage'), pct(method.coverage)),
    metric(t('meanRelevance'), relevance(method.mean_draft_relevance)),
    metric(t('totalRelevance'), method.total_draft_relevance),
  ].join('');

  const container = $(`#${prefix}Assignments`);
  if (!method.assignments?.length) {
    container.innerHTML = `<div class="assignment-empty">${t('empty')}</div>`;
    return;
  }
  container.innerHTML = method.assignments.map(assignmentRow).join('');
}

function renderSummary(greedy, globalMethod) {
  const coverageDelta = globalMethod.coverage - greedy.coverage;
  const relevanceDelta = globalMethod.mean_draft_relevance - greedy.mean_draft_relevance;
  const totalDelta = globalMethod.total_draft_relevance - greedy.total_draft_relevance;

  let title;
  let explanation;
  let className = 'mixed';

  if (coverageDelta > 0 && relevanceDelta >= 0) {
    title = t('summaryBest');
    explanation = t('summaryBestText');
    className = 'positive';
  } else if (coverageDelta > 0 && relevanceDelta < 0) {
    title = t('summaryTradeoff');
    explanation = t('summaryTradeoffText');
  } else if (coverageDelta === 0 && relevanceDelta > 0) {
    title = t('summaryQuality');
    explanation = t('summaryQualityText');
    className = 'positive';
  } else {
    title = t('summaryFailure');
    explanation = t('summaryFailureText');
  }

  $('#summaryTitle').textContent = title;
  $('#summaryText').textContent = explanation;

  const sign = totalDelta > 0 ? '+' : '';
  const tradeoff = $('#tradeoff');
  tradeoff.className = `tradeoff ${className}`;
  tradeoff.innerHTML = `<strong>${sign}${totalDelta}</strong><span>${t('delta')}</span>`;
}

function render(data) {
  const [greedy, globalMethod] = data.methods;
  renderMethod(greedy, 'greedy');
  renderMethod(globalMethod, 'global');
  renderSummary(greedy, globalMethod);

  const status = $('#labApiStatus');
  status.textContent = `${t('liveApi')} · ${data.review_status}`;
  status.className = 'pipeline-state ok';
  document.title = `NIYET ${t('allocationLab')} · ${t('batch')} ${data.batch_index + 1}`;
}

function renderError(message) {
  $('#summaryTitle').textContent = t('apiError');
  $('#summaryText').textContent = t('apiErrorText');
  $('#tradeoff').innerHTML = `<strong>—</strong><span>${t('noFallback')}</span>`;
  ['greedyMetrics', 'globalMetrics'].forEach((id) => {
    $(`#${id}`).innerHTML = metric(t('status'), t('offline'));
  });
  ['greedyAssignments', 'globalAssignments'].forEach((id) => {
    $(`#${id}`).innerHTML = `<div class="assignment-empty">${escapeHtml(message)}</div>`;
  });
  const status = $('#labApiStatus');
  status.textContent = t('apiUnavailable');
  status.className = 'pipeline-state error';
}

async function runExperiment() {
  const token = ++requestToken;
  $('.lab-shell').classList.add('loading');
  const url = `/api/experiment?batch=${activeBatch}&floor=${floor.toFixed(2)}`;

  try {
    const response = await fetch(url, { headers: { Accept: 'application/json' } });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    if (token !== requestToken) return;
    render(data);
  } catch (error) {
    if (token !== requestToken) return;
    renderError(error instanceof Error ? error.message : 'Unknown API error');
  } finally {
    if (token === requestToken) $('.lab-shell').classList.remove('loading');
  }
}

$$('#batchTabs button').forEach((button) => {
  button.addEventListener('click', () => {
    activeBatch = Number(button.dataset.batch);
    $$('#batchTabs button').forEach((item) => item.classList.toggle('active', item === button));
    runExperiment();
  });
});

const floorRange = $('#floorRange');
let floorTimer;
floorRange.addEventListener('input', () => {
  floor = Number(floorRange.value);
  $('#floorValue').textContent = floor.toFixed(2);
  clearTimeout(floorTimer);
  floorTimer = setTimeout(runExperiment, 120);
});

function setLabMenu(open) {
  const menu = $('#labMobileMenu');
  const toggle = $('#labMenuToggle');
  menu.hidden = !open;
  toggle.setAttribute('aria-expanded', String(open));
  toggle.setAttribute('aria-label', t(open ? 'menuClose' : 'menuOpen'));
  document.body.classList.toggle('lab-menu-open', open);
  if (open) $('a, button', menu)?.focus();
}

function applyLabLanguage(language, persist = true) {
  labLanguage = language === 'tr' ? 'tr' : 'en';
  if (persist) localStorage.setItem('drsk-language', labLanguage);
  document.documentElement.lang = labLanguage;
  $$('[data-lab-key]').forEach((node) => { node.textContent = t(node.dataset.labKey); });
  $$('[data-lab-aria]').forEach((node) => { node.setAttribute('aria-label', t(node.dataset.labAria)); });
  $$('[data-batch-label]').forEach((button) => { button.textContent = `${t('batch')} ${button.dataset.batchLabel}`; });
  $$('[data-lab-lang]').forEach((button) => {
    const active = button.dataset.labLang === labLanguage;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  });
  setLabMenu(false);
  runExperiment();
}

$$('[data-lab-lang]').forEach((button) => button.addEventListener('click', () => applyLabLanguage(button.dataset.labLang)));
$('#labMenuToggle').addEventListener('click', () => setLabMenu($('#labMobileMenu').hidden));
$('#labMobileMenu').addEventListener('click', (event) => { if (event.target === $('#labMobileMenu')) setLabMenu(false); });
document.addEventListener('keydown', (event) => { if (event.key === 'Escape') setLabMenu(false); });

applyLabLanguage(labLanguage, false);
