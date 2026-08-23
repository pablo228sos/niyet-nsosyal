const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

const copy = {
  en: {
    feed: 'Feed', following: 'Following', explore: 'Explore', communities: 'Communities', messages: 'Messages', profile: 'Profile', compose: 'Post',
    layerSub: 'interaction layer', layerNote: 'Concept integration for NSosyal. Research prototype.', concept: 'Concept prototype', search: 'Search NSosyal',
    placeholder: 'What is happening?', publish: 'Post', demoHelp: 'Try: ask for help', demoCollab: 'Try: find a collaborator', demoNormal: 'Try: normal post',
    intentTitle: 'This post may need a human response', intentSub: 'NIYET suggests an intent. You confirm before routing.', modelSuggestion: 'model suggestion', modelScope: 'Model scope: Turkish controlled development data',
    ask: 'ASK', feedback: 'FEEDBACK', collaborate: 'COLLABORATE', discuss: 'DISCUSS', notNow: 'Not now', route: 'Route with NIYET', privateNote: 'You stay in control',
    previewTitle: 'Responder preview', previewSub: 'What a routed request looks like on the other side', live: 'live', waiting: 'WAITING', noRoute: 'no route yet', previewEmpty: 'Use one of the demo posts or write a Turkish response-seeking post.',
    technicalDetails: 'Technical details', accept: 'Accept', skip: 'Skip', attention: 'Session capacity', pause: 'Routing is on', pauseSub: 'The matched responder can pause new requests',
    trends: 'Trends for you', trend2: 'Artificial Intelligence', trend3: 'Robotics', posts: 'posts', post1Copy: 'We finally got the robot stable on straight lines. Turns are still the hard part. Testing a new PID profile tonight.', post2Copy: 'Looking for one frontend developer for a weekend prototype. React is enough. Small team, clear scope.', routed: 'Routed with NIYET', demoMedia: 'PID response trace · demo media',
    techSub: 'Development diagnostics, not calibrated probabilities', retrievalSimilarity: 'Retrieval similarity', developmentUtility: 'Development utility', selectedIntent: 'Selected intent', techNote: 'These values are internal development signals and are not shown to users as probabilities.',
    gate: 'Response gate', gateSub: 'response / none', intentStep: 'Intent', intentStepSub: '4-way classifier', retrieve: 'Retrieve', retrieveSub: 'candidate set', allocate: 'Allocate', allocateSub: 'shared capacity',
    pipelineLive: 'live pipeline', pipelineFallback: 'demo fallback', pipelineChecking: 'checking pipeline', analyzing: 'analyzing', eligible: 'eligible match', noCandidate: 'no eligible candidate',
    routeFound: 'NIYET selected a responder after eligibility and shared-capacity allocation.', routeNoMatch: 'The request is open, but no responder passed the current routing threshold.', normalPost: 'The response gate treated this as a normal post. NIYET stays out of the flow.',
    confirmedIntent: 'confirmed intent', modelScopeShort: 'Turkish development model', routedToast: 'Matching window updated', postedToast: 'Post published to the demo feed', skippedToast: 'Responder skipped. Request was reallocated.', pausedToast: 'Responder routing paused', resumedToast: 'Responder routing resumed', acceptedToast: 'Responder accepted the request', accepted: 'Accepted',
    useAnyway: 'Use NIYET anyway', windowTitle: 'Matching window', windowSub: 'Open requests are allocated together', openRequest: 'open request', openRequests: 'open requests', batchLive: 'batch allocation active', singleWindow: 'one open request', sessionOnly: 'Browser-session state'
  },
  tr: {
    feed: 'Akış', following: 'Takip', explore: 'Keşfet', communities: 'Topluluklar', messages: 'Mesajlar', profile: 'Profil', compose: 'Gönderi',
    layerSub: 'etkileşim katmanı', layerNote: 'NSosyal için konsept entegrasyon. Araştırma prototipi.', concept: 'Konsept prototip', search: 'NSosyal içinde ara',
    placeholder: 'Neler oluyor?', publish: 'Gönder', demoHelp: 'Dene: yardım iste', demoCollab: 'Dene: ekip arkadaşı bul', demoNormal: 'Dene: normal gönderi',
    intentTitle: 'Bu gönderi insan yanıtı arıyor olabilir', intentSub: 'NIYET bir niyet önerir. Yönlendirmeden önce sen onaylarsın.', modelSuggestion: 'model önerisi', modelScope: 'Model kapsamı: Türkçe kontrollü geliştirme verisi',
    ask: 'SORU', feedback: 'GERİ BİLDİRİM', collaborate: 'İŞ BİRLİĞİ', discuss: 'TARTIŞ', notNow: 'Şimdi değil', route: 'NIYET ile yönlendir', privateNote: 'Kontrol sende',
    previewTitle: 'Cevaplayıcı önizlemesi', previewSub: 'Yönlendirilen isteğin diğer tarafta görünümü', live: 'aktif', waiting: 'BEKLİYOR', noRoute: 'henüz yönlendirme yok', previewEmpty: 'Demo gönderilerinden birini kullan veya Türkçe yanıt arayan bir gönderi yaz.',
    technicalDetails: 'Teknik ayrıntılar', accept: 'Kabul et', skip: 'Geç', attention: 'Oturum kapasitesi', pause: 'Yönlendirme açık', pauseSub: 'Eşleşen kişi yeni istekleri duraklatabilir',
    trends: 'Senin için trendler', trend2: 'Yapay Zeka', trend3: 'Robotik', posts: 'gönderi', post1Copy: 'Robotu düz çizgide sonunda kararlı hale getirdik. Virajlar hala zor. Bu gece yeni PID profilini test ediyoruz.', post2Copy: 'Hafta sonu prototipi için bir frontend geliştirici arıyoruz. React yeterli. Küçük ekip, net kapsam.', routed: 'NIYET ile yönlendirildi', demoMedia: 'PID yanıt grafiği · demo medya',
    techSub: 'Geliştirme tanıları, kalibre edilmiş olasılıklar değil', retrievalSimilarity: 'Erişim benzerliği', developmentUtility: 'Geliştirme fayda puanı', selectedIntent: 'Seçilen niyet', techNote: 'Bu değerler iç geliştirme sinyalleridir ve kullanıcıya olasılık olarak gösterilmez.',
    gate: 'Yanıt kapısı', gateSub: 'yanıt / normal', intentStep: 'Niyet', intentStepSub: '4 sınıflı model', retrieve: 'Aday bul', retrieveSub: 'aday havuzu', allocate: 'Dağıt', allocateSub: 'ortak kapasite',
    pipelineLive: 'canlı pipeline', pipelineFallback: 'demo yedeği', pipelineChecking: 'pipeline kontrol ediliyor', analyzing: 'analiz ediliyor', eligible: 'uygun eşleşme', noCandidate: 'uygun aday yok',
    routeFound: 'NIYET uygunluk ve ortak kapasite dağıtımından sonra bir cevaplayıcı seçti.', routeNoMatch: 'İstek açık ancak mevcut eşik altında uygun cevaplayıcı bulunamadı.', normalPost: 'Yanıt kapısı bunu normal gönderi olarak değerlendirdi. NIYET akışa girmiyor.',
    confirmedIntent: 'onaylanan niyet', modelScopeShort: 'Türkçe geliştirme modeli', routedToast: 'Eşleştirme penceresi güncellendi', postedToast: 'Gönderi demo akışına eklendi', skippedToast: 'Cevaplayıcı geçti. İstek tekrar dağıtıldı.', pausedToast: 'Cevaplayıcı yönlendirmesi durduruldu', resumedToast: 'Cevaplayıcı yönlendirmesi açıldı', acceptedToast: 'Cevaplayıcı isteği kabul etti', accepted: 'Kabul edildi',
    useAnyway: 'Yine de NIYET kullan', windowTitle: 'Eşleştirme penceresi', windowSub: 'Açık istekler birlikte dağıtılır', openRequest: 'açık istek', openRequests: 'açık istek', batchLive: 'toplu dağıtım aktif', singleWindow: 'bir açık istek', sessionOnly: 'Tarayıcı oturum durumu'
  }
};

let language = localStorage.getItem('drsk-language') || 'en';
let selectedIntent = 'ask';
let latestDecision = null;
let currentRequestId = null;
let routingEnabled = false;
let pipelineLive = false;
let analyzeTimer;
let toastTimer;
let openRequests = loadJson('drsk-open-requests', []);
let responderState = loadJson('drsk-responder-state', null);

function text(key) { return copy[language][key] || key; }
function loadJson(key, fallback) {
  try { return JSON.parse(sessionStorage.getItem(key)) ?? fallback; }
  catch (_) { return fallback; }
}
function saveSession() {
  sessionStorage.setItem('drsk-open-requests', JSON.stringify(openRequests));
  if (responderState) sessionStorage.setItem('drsk-responder-state', JSON.stringify(responderState));
}
function makeRequestId() { return `req-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`; }
function escapeHtml(value) { const node = document.createElement('span'); node.textContent = value; return node.innerHTML; }
function formatDevelopmentValue(value) { return typeof value === 'number' ? value.toFixed(3) : 'n/a'; }

function applyLanguage(nextLanguage) {
  language = nextLanguage;
  localStorage.setItem('drsk-language', language);
  document.documentElement.lang = language;
  $$('[data-i18n]').forEach((node) => { node.textContent = text(node.dataset.i18n); });
  $$('[data-i18n-placeholder]').forEach((node) => { node.placeholder = text(node.dataset.i18nPlaceholder); });
  $$('.lang-switch button').forEach((button) => {
    const active = button.dataset.lang === language;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  });
  renderPipelineState();
  renderMatchingWindow();
  updateBudget();
  if (latestDecision?.response_needed && routingEnabled) renderMatchPreview(latestDecision);
}

function showToast(messageKey) {
  const toast = $('#toast');
  $('#toastText').textContent = text(messageKey);
  toast.classList.add('visible');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('visible'), 2200);
}

function renderPipelineState(checking = false) {
  const state = $('#pipelineState');
  state.classList.remove('live', 'fallback');
  if (checking) { state.textContent = text('pipelineChecking'); return; }
  if (pipelineLive) { state.classList.add('live'); state.textContent = text('pipelineLive'); }
  else { state.classList.add('fallback'); state.textContent = text('pipelineFallback'); }
}

async function checkPipeline() {
  renderPipelineState(true);
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);
    const response = await fetch('/api', { cache: 'no-store', signal: controller.signal });
    clearTimeout(timeout);
    if (!response.ok) throw new Error('api unavailable');
    const payload = await response.json();
    pipelineLive = payload.status === 'ok';
    if (!responderState && payload.default_responder_state) {
      responderState = payload.default_responder_state;
      saveSession();
    }
  } catch (_) { pipelineLive = false; }
  renderPipelineState();
  updateBudget();
}

function localNeedsResponse(value) {
  if (value.trim().length < 12) return false;
  return /\?|yardım|nasıl|neden|sence|sizce|arıyorum|katıl|öner|help|feedback|looking for|collab/i.test(value.toLocaleLowerCase('tr-TR'));
}
function localIntent(value) {
  const lower = value.toLocaleLowerCase('tr-TR');
  if (/(ekip|birlikte|arıyorum|collab|teammate|looking for)/i.test(lower)) return 'collaborate';
  if (/(feedback|yorum|değerlendir|sence|sizce|review)/i.test(lower)) return 'feedback';
  if (/(tartış|discuss|görüş|fikirler)/i.test(lower)) return 'discuss';
  return 'ask';
}

async function callPipeline(value, intentOverride = null, excluded = []) {
  if (!pipelineLive) {
    const responseNeeded = Boolean(intentOverride) || localNeedsResponse(value);
    return {
      response_needed: responseNeeded,
      intent: responseNeeded ? (intentOverride || localIntent(value)).toUpperCase() : null,
      intent_source: intentOverride ? 'user_confirmed' : 'fallback',
      match: null,
      technical: { development_utility: null, retrieval_similarity: null },
      fallback: true
    };
  }
  const body = { text: value, responder_state: responderState, exclude_responder_ids: excluded };
  if (intentOverride) body.intent_override = intentOverride;
  const response = await fetch('/api', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  if (!response.ok) throw new Error('routing request failed');
  const payload = await response.json();
  if (payload.responder_state) { responderState = payload.responder_state; saveSession(); }
  return payload;
}

async function callBatch(requests) {
  const response = await fetch('/api', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ requests, responder_state: responderState })
  });
  if (!response.ok) throw new Error('batch routing failed');
  const payload = await response.json();
  if (payload.responder_state) { responderState = payload.responder_state; saveSession(); }
  return payload;
}

async function applyStateAction(action, responderId) {
  const response = await fetch('/api', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, responder_id: responderId, responder_state: responderState })
  });
  if (!response.ok) throw new Error('state action failed');
  const payload = await response.json();
  responderState = payload.responder_state;
  saveSession();
}

function setIntent(intent) {
  selectedIntent = intent;
  $$('.intent-choice').forEach((button) => {
    const active = button.dataset.intent === selectedIntent;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  });
}
function hideIntentPanel() { $('#intentPanel').classList.remove('visible'); routingEnabled = false; }

async function analyzePost() {
  const value = $('#composerText').value.trim();
  if (value.length < 12) {
    latestDecision = null;
    hideIntentPanel();
    $('#routeResult').classList.remove('visible');
    return;
  }
  const button = $('#routeIntent');
  button.disabled = true;
  button.textContent = text('analyzing');
  try {
    latestDecision = await callPipeline(value);
    if (!latestDecision.response_needed) {
      hideIntentPanel();
      renderRouteResult('normal');
      return;
    }
    setIntent((latestDecision.intent || 'ASK').toLowerCase());
    $('#intentPanel').classList.add('visible');
    $('#routeResult').classList.remove('visible');
  } catch (_) {
    pipelineLive = false;
    renderPipelineState();
    latestDecision = await callPipeline(value);
    if (latestDecision.response_needed) {
      setIntent((latestDecision.intent || 'ASK').toLowerCase());
      $('#intentPanel').classList.add('visible');
    }
  } finally {
    button.disabled = false;
    button.textContent = text('route');
  }
}

function renderRouteResult(mode, decision = latestDecision) {
  const box = $('#routeResult');
  if (mode === 'normal') {
    box.innerHTML = `<strong>${text('normalPost')}</strong><div class="route-meta"><button class="route-chip action-chip" id="forceNiyet" type="button">${text('useAnyway')}</button></div>`;
    box.classList.add('visible');
    $('#forceNiyet').addEventListener('click', () => {
      setIntent('ask');
      $('#intentPanel').classList.add('visible');
    });
    return;
  }
  if (!decision?.match) {
    box.innerHTML = `<strong>${text('routeNoMatch')}</strong><div class="route-meta"><span class="route-chip">${text('confirmedIntent')}: ${selectedIntent.toUpperCase()}</span><span class="route-chip">${text('modelScopeShort')}</span></div>`;
    box.classList.add('visible');
    return;
  }
  box.innerHTML = `<strong>${text('routeFound')}</strong><div class="route-meta"><span class="route-chip">${escapeHtml(decision.match.name)}</span><span class="route-chip">${text('confirmedIntent')}: ${selectedIntent.toUpperCase()}</span><span class="route-chip">${openRequests.length} ${openRequests.length === 1 ? text('openRequest') : text('openRequests')}</span></div>`;
  box.classList.add('visible');
}

function renderMatchPreview(decision) {
  const card = $('#matchState');
  card.classList.remove('empty', 'loading');
  card.dataset.state = 'ready';
  if (!decision?.match) {
    $('#matchType').textContent = selectedIntent.toUpperCase();
    $('#matchStatus').textContent = text('noCandidate');
    $('#matchPostText').textContent = $('#composerText').value.trim();
    $('#matchReasons').innerHTML = '';
    $('#explainMatch').disabled = true;
    $('#acceptMatch').disabled = true;
    $('#skipMatch').disabled = false;
    updateBudget();
    return;
  }
  $('#matchType').textContent = `${selectedIntent.toUpperCase()} · ${decision.match.name}`;
  $('#matchStatus').textContent = text('eligible');
  $('#matchPostText').textContent = $('#composerText').value.trim();
  $('#matchReasons').innerHTML = decision.match.reason.map((reason) => `<div class="match-reason-line">${escapeHtml(reason)}</div>`).join('');
  $('#explainMatch').disabled = false;
  $('#acceptMatch').disabled = false;
  $('#skipMatch').disabled = false;
  $('#technicalSimilarity').textContent = formatDevelopmentValue(decision.technical?.retrieval_similarity);
  $('#technicalUtility').textContent = formatDevelopmentValue(decision.technical?.development_utility);
  $('#technicalIntent').textContent = selectedIntent.toUpperCase();
  updateBudget();
}

async function rerunOpenWindow(focusId = currentRequestId) {
  if (!pipelineLive || openRequests.length === 0) return null;
  const payload = await callBatch(openRequests);
  renderMatchingWindow();
  return payload.decisions.find((item) => item.request_id === focusId) || null;
}

async function confirmRoute() {
  const value = $('#composerText').value.trim();
  if (!value) return;
  const button = $('#routeIntent');
  button.disabled = true;
  button.textContent = text('analyzing');
  try {
    currentRequestId = makeRequestId();
    openRequests.push({ id: currentRequestId, text: value, intent_override: selectedIntent, exclude_responder_ids: [] });
    saveSession();
    latestDecision = pipelineLive ? await rerunOpenWindow(currentRequestId) : await callPipeline(value, selectedIntent);
    routingEnabled = true;
    renderRouteResult('routed', latestDecision);
    renderMatchPreview(latestDecision);
    renderMatchingWindow();
    showToast('routedToast');
  } catch (_) {
    pipelineLive = false;
    renderPipelineState();
    latestDecision = await callPipeline(value, selectedIntent);
    routingEnabled = true;
    renderRouteResult('routed', latestDecision);
    renderMatchPreview(latestDecision);
  } finally {
    button.disabled = false;
    button.textContent = text('route');
  }
}

function createPost(textValue) {
  const article = document.createElement('article');
  article.className = 'post-card';
  article.innerHTML = `<div class="post-grid"><div class="avatar" aria-hidden="true">AB</div><div><div class="post-head"><span class="post-name">Demo User</span><span class="post-handle">@demo.user</span><span class="post-time">· now</span></div><p class="post-copy"></p>${routingEnabled ? `<div class="niyet-tag"><span class="niyet-dot"></span><span>${text('routed')}</span></div>` : ''}<div class="post-actions"><button class="post-action" type="button">Reply</button><button class="post-action" type="button">Repost</button><button class="post-action" type="button">Like</button></div></div></div>`;
  $('.post-copy', article).textContent = textValue;
  $('#feedPosts').prepend(article);
}

function activeResponderId() { return latestDecision?.match?.id || null; }
function updateBudget() {
  const id = activeResponderId();
  const count = $('#budgetCount');
  if (!id || !responderState?.[id]) {
    count.textContent = text('sessionOnly');
    $('#budgetFill').style.width = '50%';
    return;
  }
  const remaining = Number(responderState[id].remaining_slots || 0);
  count.textContent = language === 'tr' ? `${remaining} slot kaldı` : `${remaining} slots remaining`;
  $('#budgetFill').style.width = `${Math.min(100, Math.max(0, remaining * 33.33))}%`;
}

function renderMatchingWindow() {
  const target = $('#matchingWindow');
  if (!target) return;
  const count = openRequests.length;
  target.innerHTML = `<div><strong>${text('windowTitle')}</strong><span>${text('windowSub')}</span></div><div class="window-state"><b>${count}</b><span>${count === 1 ? text('openRequest') : text('openRequests')}</span><small>${count > 1 ? text('batchLive') : text('singleWindow')}</small></div>`;
}

function resetPreview() {
  const card = $('#matchState');
  card.classList.add('empty');
  card.dataset.state = 'empty';
  $('#matchType').textContent = text('waiting');
  $('#matchStatus').textContent = text('noRoute');
  $('#matchPostText').textContent = text('previewEmpty');
  $('#matchReasons').innerHTML = '';
  $('#explainMatch').disabled = true;
  $('#acceptMatch').disabled = true;
  $('#skipMatch').disabled = true;
  updateBudget();
}

function bindEvents() {
  $$('.lang-switch button').forEach((button) => button.addEventListener('click', () => applyLanguage(button.dataset.lang)));
  const textarea = $('#composerText');
  textarea.addEventListener('input', () => {
    clearTimeout(analyzeTimer);
    analyzeTimer = setTimeout(analyzePost, 650);
  });
  $$('.demo-chip').forEach((button) => button.addEventListener('click', () => {
    const examples = {
      help: 'Çizgi izleyen robotum virajlarda salınım yapıyor. PID ayarına nereden başlamalıyım?',
      collab: 'Hafta sonu prototipi için FastAPI bilen bir ekip arkadaşı arıyorum. Birlikte çalışmak isteyen var mı?',
      normal: 'Bugün prototipin ilk benchmark koşusunu tamamladık. Sonuçları yarın paylaşacağız.'
    };
    textarea.value = examples[button.dataset.demo];
    textarea.focus();
    analyzePost();
  }));
  $$('.intent-choice').forEach((button) => button.addEventListener('click', () => setIntent(button.dataset.intent)));
  $('#dismissIntent').addEventListener('click', hideIntentPanel);
  $('#routeIntent').addEventListener('click', confirmRoute);
  $('#publishPost').addEventListener('click', () => {
    const value = textarea.value.trim();
    if (!value) return;
    createPost(value);
    textarea.value = '';
    latestDecision = null;
    routingEnabled = false;
    hideIntentPanel();
    $('#routeResult').classList.remove('visible');
    resetPreview();
    showToast('postedToast');
  });
  $('#acceptMatch').addEventListener('click', async () => {
    const responderId = activeResponderId();
    if ($('#acceptMatch').disabled || !responderId) return;
    try { await applyStateAction('accept', responderId); } catch (_) {}
    openRequests = openRequests.filter((item) => item.id !== currentRequestId);
    saveSession();
    renderMatchingWindow();
    updateBudget();
    $('#matchStatus').textContent = text('accepted');
    $('#acceptMatch').disabled = true;
    showToast('acceptedToast');
  });
  $('#skipMatch').addEventListener('click', async () => {
    const responderId = activeResponderId();
    const item = openRequests.find((request) => request.id === currentRequestId);
    if (item && responderId) {
      item.exclude_responder_ids = [...new Set([...(item.exclude_responder_ids || []), responderId])];
      saveSession();
      try {
        latestDecision = await rerunOpenWindow(currentRequestId);
        renderRouteResult('routed', latestDecision);
        renderMatchPreview(latestDecision);
      } catch (_) { resetPreview(); }
    } else resetPreview();
    showToast('skippedToast');
  });
  $('#explainMatch').addEventListener('click', () => {
    if (!$('#explainMatch').disabled) $('#explainSheet').classList.add('visible');
  });
  $('#closeSheet').addEventListener('click', () => $('#explainSheet').classList.remove('visible'));
  $('#explainSheet').addEventListener('click', (event) => {
    if (event.target === $('#explainSheet')) $('#explainSheet').classList.remove('visible');
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') $('#explainSheet').classList.remove('visible');
  });
  $('#routingSwitch').addEventListener('click', async (event) => {
    const button = event.currentTarget;
    const off = button.classList.toggle('off');
    button.setAttribute('aria-pressed', String(!off));
    const responderId = activeResponderId();
    if (responderId && pipelineLive) {
      try {
        await applyStateAction(off ? 'pause' : 'resume', responderId);
        latestDecision = await rerunOpenWindow(currentRequestId) || latestDecision;
        renderMatchPreview(latestDecision);
      } catch (_) {}
    }
    $('#pauseTitle').textContent = off ? (language === 'tr' ? 'Yönlendirme duraklatıldı' : 'Routing is paused') : text('pause');
    showToast(off ? 'pausedToast' : 'resumedToast');
  });
  $$('.feed-tab').forEach((tab) => tab.addEventListener('click', () => {
    $$('.feed-tab').forEach((node) => node.classList.remove('active'));
    tab.classList.add('active');
  }));
}

applyLanguage(language);
bindEvents();
renderMatchingWindow();
updateBudget();
resetPreview();
checkPipeline();
