const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

const labCopy = {
  en: {
    feed: 'Feed', evidenceNav: 'Evidence', allocationLab: 'Allocation Lab', researchPrototype: 'Research prototype',
    productDescriptor: 'Hybrid Social Intelligence', backToFeed: '← Back to feed', labTitle: 'Allocation Lab',
    labSub: 'Same requests. Same responder capacity. Different allocation strategies.', devBenchmark: 'Development benchmark',
    stepRetrieve: 'Retrieve', stepRetrieveSub: 'Only responders who accept the intent and pass the topic floor enter the candidate graph.',
    stepConstrain: 'Constrain', stepConstrainSub: 'Each responder has one slot in this lab, so requests compete for limited attention.',
    stepAllocate: 'Allocate', stepAllocateSub: 'Greedy chooses locally. Global assignment evaluates the batch together.',
    expControls: 'Experiment controls', topicFloor: 'Topic floor', floorSub: 'Weak retrieval edges are removed before optimization.',
    whatChanged: 'What changed?', baseline: 'Baseline', greedyTitle: 'Capacity-aware greedy', localChoice: 'local choice',
    globalTitle: 'Global allocation', batchChoice: 'batch choice',
    coverage: 'Coverage', meanRelevance: 'Mean relevance', totalRelevance: 'Total relevance',
    noteTitle: 'How to read this lab',
    noteBody: 'The benchmark is currently marked team_review_pending. Relevance grades are development labels. The lab makes the algorithm, tradeoffs and failure cases inspectable without presenting draft labels as field performance.',
    draftPointsVsGreedy: 'draft relevance points vs greedy', noAssignmentFloor: 'No assignment cleared the current topic floor.',
    apiOffline: 'API offline', noSyntheticFallback: 'no synthetic fallback', expApiUnavailable: 'The experiment API is unavailable.',
    reloadWhenReady: 'No fallback metrics are shown. Reload after the live backend is available.'
  },
  tr: {
    feed: 'Akış', evidenceNav: 'Kanıt', allocationLab: 'Dağıtım Laboratuvarı', researchPrototype: 'Araştırma prototipi',
    productDescriptor: 'Hibrit Sosyal Zeka', backToFeed: '← Akışa dön', labTitle: 'Dağıtım Laboratuvarı',
    labSub: 'Aynı istekler. Aynı cevaplayıcı kapasitesi. Farklı dağıtım stratejileri.', devBenchmark: 'Geliştirme kıyaslaması',
    stepRetrieve: 'Aday Bul', stepRetrieveSub: 'Yalnızca niyeti kabul eden ve konu eşiğini geçen cevaplayıcılar aday grafiğine girer.',
    stepConstrain: 'Kısıtla', stepConstrainSub: 'Bu laboratuvarda her cevaplayıcının bir slotu vardır, bu nedenle istekler sınırlı dikkat için yarışır.',
    stepAllocate: 'Dağıt', stepAllocateSub: 'Açgözlü yöntem yerel olarak seçer. Küresel atama grubu birlikte değerlendirir.',
    expControls: 'Deney kontrolleri', topicFloor: 'Konu eşiği', floorSub: 'Optimizasyondan önce zayıf erişim bağlantıları kaldırılır.',
    whatChanged: 'Ne değişti?', baseline: 'Temel Çizgi', greedyTitle: 'Kapasite duyarlı açgözlü', localChoice: 'yerel seçim',
    globalTitle: 'Küresel dağıtım', batchChoice: 'grup seçimi',
    coverage: 'Kapsam', meanRelevance: 'Ortalama uygunluk', totalRelevance: 'Toplam uygunluk',
    noteTitle: 'Bu laboratuvar nasıl okunmalı',
    noteBody: 'Kıyaslama şu anda team_review_pending olarak işaretlenmiştir. Uygunluk dereceleri geliştirme etiketleridir. Laboratuvar, taslak etiketleri saha performansı gibi sunmadan algoritmayı, ödünleşimleri ve başarısızlık durumlarını incelenebilir kılar.',
    draftPointsVsGreedy: 'açgözlüye karşı taslak uygunluk puanı', noAssignmentFloor: 'Mevcut konu eşiğini geçen atama bulunamadı.',
    apiOffline: 'API çevrimdışı', noSyntheticFallback: 'sentetik yedek yok', expApiUnavailable: 'Deney API\'si kullanılamıyor.',
    reloadWhenReady: 'Yedek metrik gösterilmez. Canlı arka uç hazır olduğunda yenileyin.'
  }
};

let language = localStorage.getItem('drsk-language') || 'en';
let activeBatch = 0;
let floor = 0.06;
let requestToken = 0;

function text(key) { return labCopy[language]?.[key] || labCopy.en[key] || key; }

function applyLanguage(nextLanguage, persist = true) {
  language = nextLanguage;
  if (persist) localStorage.setItem('drsk-language', language);
  document.documentElement.lang = language;
  $$('[data-i18n]').forEach((node) => { node.textContent = text(node.dataset.i18n); });
  $$('.lang-switch button').forEach((button) => {
    const active = button.dataset.lang === language;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  });
  runExperiment();
}

function pct(value) {
  return `${Math.round(Number(value || 0) * 100)}%`;
}

function relevance(value) {
  return Number(value || 0).toFixed(2);
}

function metric(label, value) {
  return `<div class="metric"><span>${label}</span><strong>${value}</strong></div>`;
}

function assignmentRow(row) {
  const grade = Number(row.draft_relevance ?? 0);
  return `
    <div class="assignment">
      <div>
        <div class="assignment-intent">
          <span class="intent-pill">${row.intent}</span>
          <span class="assignment-meta">→ ${row.responder}</span>
        </div>
        <p>${row.query}</p>
        <div class="assignment-meta">similarity ${Number(row.similarity).toFixed(3)}</div>
      </div>
      <div class="grade g${grade}" title="Draft relevance grade">${grade}/3</div>
    </div>`;
}

function renderMethod(method, prefix) {
  $(`#${prefix}Metrics`).innerHTML = [
    metric(text('coverage'), pct(method.coverage)),
    metric(text('meanRelevance'), relevance(method.mean_draft_relevance)),
    metric(text('totalRelevance'), method.total_draft_relevance),
  ].join('');

  const container = $(`#${prefix}Assignments`);
  if (!method.assignments?.length) {
    container.innerHTML = `<div class="assignment-empty">${text('noAssignmentFloor')}</div>`;
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

  if (language === 'tr') {
    if (coverageDelta > 0 && relevanceDelta >= 0) {
      title = 'Küresel dağıtım bu grupta ortalama taslak uygunluğu düşürmeden kapsamı artırıyor.';
      explanation = 'Bu durum grup düzeyinde dağıtım için en güçlü senaryodur, ancak etiketler incelenip dondurulana kadar geliştirme kıyaslamasıdır.';
      className = 'positive';
    } else if (coverageDelta > 0 && relevanceDelta < 0) {
      title = 'Küresel dağıtım daha fazla isteğe yanıt veriyor, ancak ekstra kapsam ortalama eşleşme kalitesinden bir miktar ödün veriyor.';
      explanation = 'Bu NIYET\'in yönetmesi gereken ödünleşimdir. Konu eşiğini yükseltmek optimizasyondan önce zayıf aday bağlantılarını kaldırabilir.';
    } else if (coverageDelta === 0 && relevanceDelta > 0) {
      title = 'Kapsam değişmedi, ancak küresel dağıtım bu gruptaki ortalama eşleşme kalitesini artırıyor.';
      explanation = 'Optimize edici, atama sayısını artırmak yerine aynı cevaplayıcı kapasitesini farklı şekilde kullanıyor.';
      className = 'positive';
    } else {
      title = 'Küresel dağıtım her grupta daha iyi değildir. Bu durum kasıtlı olarak görünür bırakılmıştır.';
      explanation = 'Laboratuvar, yalnızca NIYET\'in kazandığı durumları seçmek yerine başarısızlık durumlarını ve eşik duyarlılığını göstermek için tasarlanmıştır.';
    }
  } else {
    if (coverageDelta > 0 && relevanceDelta >= 0) {
      title = 'Global allocation improves coverage without reducing average draft relevance in this batch.';
      explanation = 'This is the strongest case for batch-level allocation, but it is still a development benchmark until labels are reviewed and frozen.';
      className = 'positive';
    } else if (coverageDelta > 0 && relevanceDelta < 0) {
      title = 'Global allocation serves more requests, but the extra coverage costs some average match quality.';
      explanation = 'This is the tradeoff NIYET must manage. Raising the topic floor can remove weak candidate edges before optimization.';
    } else if (coverageDelta === 0 && relevanceDelta > 0) {
      title = 'Coverage is unchanged, but global allocation improves the average match quality in this batch.';
      explanation = 'The optimizer is using the same responder capacity differently rather than simply increasing the number of assignments.';
      className = 'positive';
    } else {
      title = 'Global allocation is not better on every batch. This case stays visible on purpose.';
      explanation = 'The lab is designed to expose failure cases and threshold sensitivity instead of selecting only examples where NIYET wins.';
    }
  }

  $('#summaryTitle').textContent = title;
  $('#summaryText').textContent = explanation;

  const sign = totalDelta > 0 ? '+' : '';
  const tradeoff = $('#tradeoff');
  tradeoff.className = `tradeoff ${className}`;
  tradeoff.innerHTML = `<strong>${sign}${totalDelta}</strong><span>${text('draftPointsVsGreedy')}</span>`;
}

function render(data) {
  const [greedy, globalMethod] = data.methods;
  renderMethod(greedy, 'greedy');
  renderMethod(globalMethod, 'global');
  renderSummary(greedy, globalMethod);

  const status = $('#labApiStatus');
  status.textContent = `live API · ${data.review_status}`;
  status.className = 'pipeline-state ok';
  document.title = `DRSK Allocation Lab · Batch ${data.batch_index + 1}`;
}

function renderError(message) {
  $('#summaryTitle').textContent = text('expApiUnavailable');
  $('#summaryText').textContent = text('reloadWhenReady');
  $('#tradeoff').innerHTML = `<strong>—</strong><span>${text('noSyntheticFallback')}</span>`;
  ['greedyMetrics', 'globalMetrics'].forEach((id) => {
    $(`#${id}`).innerHTML = metric(text('apiOffline'), 'offline');
  });
  ['greedyAssignments', 'globalAssignments'].forEach((id) => {
    $(`#${id}`).innerHTML = `<div class="assignment-empty">${message}</div>`;
  });
  const status = $('#labApiStatus');
  status.textContent = text('apiOffline');
  status.className = 'pipeline-state error';
}

async function runExperiment() {
  const token = ++requestToken;
  $('.lab-shell')?.classList.add('loading');
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
    if (token === requestToken) $('.lab-shell')?.classList.remove('loading');
  }
}

$$('#batchTabs button').forEach((button) => {
  button.addEventListener('click', () => {
    activeBatch = Number(button.dataset.batch);
    $$('#batchTabs button').forEach((item) => item.classList.toggle('active', item === button));
    runExperiment();
  });
});

$$('.lang-switch button').forEach((button) => {
  button.addEventListener('click', () => applyLanguage(button.dataset.lang));
});

const floorRange = $('#floorRange');
let floorTimer;
if (floorRange) {
  floorRange.addEventListener('input', () => {
    floor = Number(floorRange.value);
    $('#floorValue').textContent = floor.toFixed(2);
    clearTimeout(floorTimer);
    floorTimer = setTimeout(runExperiment, 120);
  });
}

applyLanguage(language, false);
runExperiment();
