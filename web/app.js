const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

const copy = {
  en: {
    feed: 'Feed', following: 'Following', explore: 'Explore', communities: 'Communities', messages: 'Messages', profile: 'Profile', compose: 'Post',
    layerSub: 'interaction layer', layerNote: 'Concept integration for NSosyal. Research prototype.', concept: 'Concept prototype', search: 'Search NSosyal',
    placeholder: 'What is happening?', publish: 'Post', demoHelp: 'Try: ask for help', demoCollab: 'Try: find a collaborator', demoNormal: 'Try: normal post',
    intentTitle: 'This post may need a human response', intentSub: 'NIYET suggests an intent. You confirm before routing.', modelSuggestion: 'model suggestion', modelScope: 'Model scope: Turkish controlled development data',
    ask: 'ASK', feedback: 'FEEDBACK', collaborate: 'COLLABORATE', discuss: 'DISCUSS', notNow: 'Not now', route: 'Route with NIYET', privateNote: 'You stay in control',
    previewTitle: 'Responder preview', previewSub: 'What the request looks like on the responder side', live: 'live', waiting: 'WAITING', noRoute: 'no route yet', previewEmpty: 'Route a response-seeking post to see the responder side.',
    technicalDetails: 'Technical details', accept: 'Accept', skip: 'Skip', attention: 'Session capacity', pause: 'Routing is on', pauseSub: 'The matched responder can pause new requests',
    trends: 'Trends for you', trend2: 'Artificial Intelligence', trend3: 'Robotics', posts: 'posts', post1Copy: 'We finally got the robot stable on straight lines. Turns are still the hard part. Testing a new PID profile tonight.', post2Copy: 'Looking for one frontend developer for a weekend prototype. React is enough. Small team, clear scope.', routed: 'Routed with NIYET', demoMedia: 'PID response trace · demo media',
    techSub: 'Development diagnostics, not calibrated probabilities', retrievalSimilarity: 'Retrieval similarity', developmentUtility: 'Development utility', selectedIntent: 'Selected intent', techNote: 'These values are internal development signals and are not shown to users as probabilities.',
    gate: 'Response gate', gateSub: 'response / none', intentStep: 'Intent', intentStepSub: '4-way classifier', retrieve: 'Retrieve', retrieveSub: 'candidate set', allocate: 'Allocate', allocateSub: 'shared capacity',
    pipelineLive: 'live pipeline', pipelineFallback: 'demo fallback', pipelineChecking: 'checking pipeline', analyzing: 'analyzing', eligible: 'eligible match', noCandidate: 'no eligible candidate',
    routeFound: 'NIYET selected a responder after eligibility and shared-capacity allocation.', routeNoMatch: 'The request is open, but no responder passed the current routing threshold.', normalPost: 'The response gate treated this as a normal post. NIYET stays out of the flow.',
    confirmedIntent: 'confirmed intent', modelScopeShort: 'Turkish development model', routedToast: 'Matching window updated', postedToast: 'Post published to the demo feed', skippedToast: 'Responder skipped. Request was reallocated.', pausedToast: 'Responder routing paused', resumedToast: 'Responder routing resumed', acceptedToast: 'Responder accepted the request', accepted: 'Accepted',
    useAnyway: 'Use NIYET anyway', windowTitle: 'Matching window', windowSub: 'Open requests are allocated together', openRequest: 'open request', openRequests: 'open requests', batchLive: 'batch allocation active', singleWindow: 'one open request', sessionOnly: 'Browser-session state',
    responderSide: 'Responder side', authorSide: 'Author side', openResponder: 'Open responder view', close: 'Close', reset: 'Reset demo', resetToast: 'Demo session reset',
    topicsPrefix: 'topic profile', requestsEnabled: 'requests enabled', slotsAvailable: 'attention slots available', linkCopied: 'Link copied', followingToast: 'Following feed selected',
    viewExploreTitle: 'Explore', viewExploreText: 'Discover conversations by topic instead of follower count.', viewCommunitiesTitle: 'Communities', viewCommunitiesText: 'Small spaces for shared interests and recurring collaboration.', viewMessagesTitle: 'Messages', viewMessagesText: 'Direct conversations remain separate from NIYET routing.', viewProfileTitle: 'Profile', viewProfileText: 'Your public profile and interaction preferences.',
    demoLabel: 'demo', people: 'members', recent: 'recent', noMessages: 'No unread messages', profileBio: 'Building robotics and social AI prototypes.',
    now: 'now'
  },
  tr: {
    feed: 'Akış', following: 'Takip', explore: 'Keşfet', communities: 'Topluluklar', messages: 'Mesajlar', profile: 'Profil', compose: 'Gönderi',
    layerSub: 'etkileşim katmanı', layerNote: 'NSosyal için konsept entegrasyon. Araştırma prototipi.', concept: 'Konsept prototip', search: 'NSosyal içinde ara',
    placeholder: 'Neler oluyor?', publish: 'Gönder', demoHelp: 'Dene: yardım iste', demoCollab: 'Dene: ekip arkadaşı bul', demoNormal: 'Dene: normal gönderi',
    intentTitle: 'Bu gönderi insan yanıtı arıyor olabilir', intentSub: 'NIYET bir niyet önerir. Yönlendirmeden önce sen onaylarsın.', modelSuggestion: 'model önerisi', modelScope: 'Model kapsamı: Türkçe kontrollü geliştirme verisi',
    ask: 'SORU', feedback: 'GERİ BİLDİRİM', collaborate: 'İŞ BİRLİĞİ', discuss: 'TARTIŞ', notNow: 'Şimdi değil', route: 'NIYET ile yönlendir', privateNote: 'Kontrol sende',
    previewTitle: 'Cevaplayıcı önizlemesi', previewSub: 'İsteğin cevaplayıcı tarafında nasıl göründüğü', live: 'aktif', waiting: 'BEKLİYOR', noRoute: 'henüz yönlendirme yok', previewEmpty: 'Cevaplayıcı tarafını görmek için yanıt arayan bir gönderiyi yönlendir.',
    technicalDetails: 'Teknik ayrıntılar', accept: 'Kabul et', skip: 'Geç', attention: 'Oturum kapasitesi', pause: 'Yönlendirme açık', pauseSub: 'Eşleşen kişi yeni istekleri duraklatabilir',
    trends: 'Senin için trendler', trend2: 'Yapay Zeka', trend3: 'Robotik', posts: 'gönderi', post1Copy: 'Robotu düz çizgide sonunda kararlı hale getirdik. Virajlar hala zor. Bu gece yeni PID profilini test ediyoruz.', post2Copy: 'Hafta sonu prototipi için bir frontend geliştirici arıyoruz. React yeterli. Küçük ekip, net kapsam.', routed: 'NIYET ile yönlendirildi', demoMedia: 'PID yanıt grafiği · demo medya',
    techSub: 'Geliştirme tanıları, kalibre edilmiş olasılıklar değil', retrievalSimilarity: 'Erişim benzerliği', developmentUtility: 'Geliştirme fayda puanı', selectedIntent: 'Seçilen niyet', techNote: 'Bu değerler iç geliştirme sinyalleridir ve kullanıcıya olasılık olarak gösterilmez.',
    gate: 'Yanıt kapısı', gateSub: 'yanıt / normal', intentStep: 'Niyet', intentStepSub: '4 sınıflı model', retrieve: 'Aday bul', retrieveSub: 'aday havuzu', allocate: 'Dağıt', allocateSub: 'ortak kapasite',
    pipelineLive: 'canlı pipeline', pipelineFallback: 'demo yedeği', pipelineChecking: 'pipeline kontrol ediliyor', analyzing: 'analiz ediliyor', eligible: 'uygun eşleşme', noCandidate: 'uygun aday yok',
    routeFound: 'NIYET uygunluk ve ortak kapasite dağıtımından sonra bir cevaplayıcı seçti.', routeNoMatch: 'İstek açık ancak mevcut eşik altında uygun cevaplayıcı bulunamadı.', normalPost: 'Yanıt kapısı bunu normal gönderi olarak değerlendirdi. NIYET akışa girmiyor.',
    confirmedIntent: 'onaylanan niyet', modelScopeShort: 'Türkçe geliştirme modeli', routedToast: 'Eşleştirme penceresi güncellendi', postedToast: 'Gönderi demo akışına eklendi', skippedToast: 'Cevaplayıcı geçti. İstek tekrar dağıtıldı.', pausedToast: 'Cevaplayıcı yönlendirmesi durduruldu', resumedToast: 'Cevaplayıcı yönlendirmesi açıldı', acceptedToast: 'Cevaplayıcı isteği kabul etti', accepted: 'Kabul edildi',
    useAnyway: 'Yine de NIYET kullan', windowTitle: 'Eşleştirme penceresi', windowSub: 'Açık istekler birlikte dağıtılır', openRequest: 'açık istek', openRequests: 'açık istek', batchLive: 'toplu dağıtım aktif', singleWindow: 'bir açık istek', sessionOnly: 'Tarayıcı oturum durumu',
    responderSide: 'Cevaplayıcı tarafı', authorSide: 'Gönderi sahibi', openResponder: 'Cevaplayıcı görünümünü aç', close: 'Kapat', reset: 'Demoyu sıfırla', resetToast: 'Demo oturumu sıfırlandı',
    topicsPrefix: 'konu profili', requestsEnabled: 'istekleri açık', slotsAvailable: 'dikkat kapasitesi uygun', linkCopied: 'Bağlantı kopyalandı', followingToast: 'Takip akışı seçildi',
    viewExploreTitle: 'Keşfet', viewExploreText: 'Takipçi sayısından bağımsız olarak konuya göre konuşmaları keşfet.', viewCommunitiesTitle: 'Topluluklar', viewCommunitiesText: 'Ortak ilgi alanları ve tekrar eden iş birlikleri için küçük alanlar.', viewMessagesTitle: 'Mesajlar', viewMessagesText: 'Doğrudan konuşmalar NIYET yönlendirmesinden ayrı kalır.', viewProfileTitle: 'Profil', viewProfileText: 'Herkese açık profilin ve etkileşim tercihlerin.',
    demoLabel: 'demo', people: 'üye', recent: 'yakın zamanda', noMessages: 'Okunmamış mesaj yok', profileBio: 'Robotik ve sosyal yapay zeka prototipleri geliştiriyorum.',
    now: 'şimdi'
  }
};

const STATE_VERSION = '4';
if (sessionStorage.getItem('drsk-state-version') !== STATE_VERSION) {
  sessionStorage.removeItem('drsk-open-requests');
  sessionStorage.removeItem('drsk-responder-state');
  sessionStorage.setItem('drsk-state-version', STATE_VERSION);
}

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
let routeResultMode = null;
let activeView = 'feed';

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
function intentLabel(intent = selectedIntent) { return text(String(intent || 'ask').toLowerCase()); }

function localizeReason(reason) {
  const raw = String(reason || '');
  if (raw.startsWith('topic profile:')) return `${text('topicsPrefix')}: ${raw.split(':').slice(1).join(':').trim()}`;
  if (raw.endsWith('requests enabled')) return `${intentLabel(raw.split(' ')[0])} ${text('requestsEnabled')}`;
  const slots = raw.match(/^(\d+\/\d+) attention slots available$/);
  if (slots) return `${slots[1]} ${text('slotsAvailable')}`;
  return raw;
}

function applyLanguage(nextLanguage) {
  language = nextLanguage;
  localStorage.setItem('drsk-language', language);
  document.documentElement.lang = language;
  $$('[data-i18n]').forEach((node) => { node.textContent = text(node.dataset.i18n); });
  $$('[data-i18n-placeholder]').forEach((node) => { node.placeholder = text(node.dataset.i18nPlaceholder); });
  $('.lang-switch')?.classList.toggle('tr', language === 'tr');
  $$('.lang-switch button').forEach((button) => {
    const active = button.dataset.lang === language;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  });
  renderPipelineState();
  renderMatchingWindow();
  updateBudget();
  renderSecondaryView();
  if (routeResultMode) renderRouteResult(routeResultMode, latestDecision);
  if (latestDecision?.response_needed && routingEnabled) renderMatchPreview(latestDecision);
  else if (!latestDecision) resetPreview();
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
  if (!state) return;
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
    routeResultMode = null;
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
    routeResultMode = null;
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
  routeResultMode = mode;
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
    box.innerHTML = `<strong>${text('routeNoMatch')}</strong><div class="route-meta"><span class="route-chip">${text('confirmedIntent')}: ${intentLabel()}</span><span class="route-chip">${text('modelScopeShort')}</span></div>`;
    box.classList.add('visible');
    return;
  }
  box.innerHTML = `<strong>${text('routeFound')}</strong><div class="route-meta"><span class="route-chip">${escapeHtml(decision.match.name)}</span><span class="route-chip">${text('confirmedIntent')}: ${intentLabel()}</span><span class="route-chip">${openRequests.length} ${openRequests.length === 1 ? text('openRequest') : text('openRequests')}</span><button class="route-chip action-chip mobile-responder-link" type="button">${text('openResponder')}</button></div>`;
  box.classList.add('visible');
  $('.mobile-responder-link', box)?.addEventListener('click', openMobileInbox);
}

function renderMatchPreview(decision) {
  const card = $('#matchState');
  card.classList.remove('empty', 'loading');
  card.dataset.state = 'ready';
  if (!decision?.match) {
    $('#matchType').textContent = intentLabel();
    $('#matchStatus').textContent = text('noCandidate');
    $('#matchPostText').textContent = $('#composerText').value.trim();
    $('#matchReasons').innerHTML = '';
    $('#explainMatch').disabled = true;
    $('#acceptMatch').disabled = true;
    $('#skipMatch').disabled = false;
    updateBudget();
    updateMobileInboxButton();
    return;
  }
  $('#matchType').textContent = `${intentLabel()} · ${decision.match.name}`;
  $('#matchStatus').textContent = text('eligible');
  $('#matchPostText').textContent = $('#composerText').value.trim();
  $('#matchReasons').innerHTML = (decision.match.reason || []).map((reason) => `<div class="match-reason-line">${escapeHtml(localizeReason(reason))}</div>`).join('');
  $('#explainMatch').disabled = false;
  $('#acceptMatch').disabled = false;
  $('#skipMatch').disabled = false;
  $('#technicalSimilarity').textContent = formatDevelopmentValue(decision.technical?.retrieval_similarity);
  $('#technicalUtility').textContent = formatDevelopmentValue(decision.technical?.development_utility);
  $('#technicalIntent').textContent = intentLabel();
  updateBudget();
  updateMobileInboxButton();
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

function iconMarkup(id) { return `<svg aria-hidden="true"><use href="#${id}"></use></svg>`; }

function createPost(textValue) {
  const article = document.createElement('article');
  article.className = 'post-card demo-user-post';
  article.innerHTML = `<div class="post-grid"><div class="avatar" aria-hidden="true">AB</div><div><div class="post-head"><span class="post-name">Demo User</span><span class="post-handle">@demo.user</span><span class="post-time">· ${text('now')}</span></div><p class="post-copy"></p>${routingEnabled ? `<div class="niyet-tag"><span class="niyet-dot"></span><span data-i18n="routed">${text('routed')}</span></div>` : ''}<div class="post-actions"><button class="post-action" data-action="reply" type="button" aria-label="Reply">${iconMarkup('i-reply')}<span>0</span></button><button class="post-action" data-action="repost" type="button" aria-label="Repost">${iconMarkup('i-repeat')}<span>0</span></button><button class="post-action" data-action="like" type="button" aria-label="Like">${iconMarkup('i-heart')}<span>0</span></button><button class="post-action" data-action="share" type="button" aria-label="Share">${iconMarkup('i-share')}</button></div></div></div>`;
  $('.post-copy', article).textContent = textValue;
  $('#feedPosts').prepend(article);
  wirePostActions(article);
}

function wirePostActions(root = document) {
  $$('[data-action]', root).forEach((button) => {
    if (button.dataset.bound === 'true') return;
    button.dataset.bound = 'true';
    button.addEventListener('click', async () => {
      const action = button.dataset.action;
      const count = $('span', button);
      if (action === 'reply') {
        activateView('feed');
        $('#composerText').focus();
        return;
      }
      if (action === 'share') {
        try { await navigator.clipboard.writeText(location.href); } catch (_) {}
        showToast('linkCopied');
        return;
      }
      const active = button.classList.toggle('active-action');
      if (count) count.textContent = String(Math.max(0, Number(count.textContent || 0) + (active ? 1 : -1)));
    });
  });
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
  const daily = Math.max(1, remaining + 1);
  count.textContent = language === 'tr' ? `${remaining} slot kaldı` : `${remaining} slots remaining`;
  $('#budgetFill').style.width = `${Math.min(100, Math.max(0, (remaining / daily) * 100))}%`;
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
  updateMobileInboxButton();
}

function demoExamples() {
  if (language === 'tr') return {
    help: 'Çizgi izleyen robotum virajlarda salınım yapıyor. PID ayarına nereden başlamalıyım?',
    collab: 'Hafta sonu prototipi için FastAPI bilen bir ekip arkadaşı arıyorum. Birlikte çalışmak isteyen var mı?',
    normal: 'Bugün prototipin ilk benchmark koşusunu tamamladık. Sonuçları yarın paylaşacağız.'
  };
  return {
    help: 'My line-following robot oscillates in turns. Which PID term should I tune first?',
    collab: 'I am looking for a teammate who knows FastAPI for a weekend prototype. Who wants to collaborate?',
    normal: 'We completed the first benchmark run of the prototype today. We will share the results tomorrow.'
  };
}

function secondaryMarkup(view) {
  const views = {
    explore: {
      title: text('viewExploreTitle'), subtitle: text('viewExploreText'),
      body: `<div class="view-search"><svg><use href="#i-search"></use></svg><span>${text('search')}</span></div><div class="topic-grid"><button>#Robotics</button><button>#ArtificialIntelligence</button><button>#Accessibility</button><button>#OpenSource</button></div>`
    },
    communities: {
      title: text('viewCommunitiesTitle'), subtitle: text('viewCommunitiesText'),
      body: `<div class="community-list"><div><b>Robotics Builders</b><span>12.4K ${text('people')} · ${text('demoLabel')}</span></div><div><b>AI Research TR</b><span>8.1K ${text('people')} · ${text('demoLabel')}</span></div><div><b>Accessible Product Design</b><span>3.7K ${text('people')} · ${text('demoLabel')}</span></div></div>`
    },
    messages: {
      title: text('viewMessagesTitle'), subtitle: text('viewMessagesText'),
      body: `<div class="message-list"><div><span class="avatar green">DA</span><p><b>Deniz A.</b><small>PID notes · ${text('recent')}</small></p></div><div><span class="avatar alt">MK</span><p><b>Mert K.</b><small>Weekend prototype · ${text('recent')}</small></p></div><div class="empty-row">${text('noMessages')}</div></div>`
    },
    profile: {
      title: text('viewProfileTitle'), subtitle: text('viewProfileText'),
      body: `<div class="profile-demo"><div class="avatar profile-avatar">AB</div><h3>Demo User</h3><span>@demo.user</span><p>${text('profileBio')}</p><div class="profile-stats"><b>128 <small>${language === 'tr' ? 'takip' : 'following'}</small></b><b>342 <small>${language === 'tr' ? 'takipçi' : 'followers'}</small></b></div></div>`
    }
  };
  const item = views[view];
  if (!item) return '';
  return `<div class="secondary-head"><span class="role-badge">${text('demoLabel')}</span><h2>${item.title}</h2><p>${item.subtitle}</p></div>${item.body}`;
}

function ensureSecondaryView() {
  if ($('#secondaryView')) return;
  const section = document.createElement('section');
  section.id = 'secondaryView';
  section.className = 'secondary-view';
  $('.feed-column').appendChild(section);
}

function renderSecondaryView() {
  ensureSecondaryView();
  const secondary = $('#secondaryView');
  if (activeView === 'feed') {
    secondary.hidden = true;
    return;
  }
  secondary.innerHTML = secondaryMarkup(activeView);
  secondary.hidden = false;
}

function activateView(view) {
  activeView = view;
  const isFeed = view === 'feed';
  $('.composer').hidden = !isFeed;
  $('#feedPosts').hidden = !isFeed;
  $('.feed-tabs').hidden = !isFeed;
  $('.feed-title').textContent = isFeed ? text('feed') : text(`view${view[0].toUpperCase()}${view.slice(1)}Title`);
  renderSecondaryView();

  const viewOrder = ['feed', 'explore', 'communities', 'messages', 'profile'];
  $$('.nav-list .nav-item').forEach((button, index) => button.classList.toggle('active', viewOrder[index] === view));
  $$('.mobile-nav button').forEach((button, index) => button.classList.toggle('active', viewOrder[index] === view));
  updateMobileInboxButton();
  if (isFeed) window.scrollTo({ top: 0, behavior: 'smooth' });
}

function installNavigation() {
  const viewOrder = ['feed', 'explore', 'communities', 'messages', 'profile'];
  $$('.nav-list .nav-item').forEach((button, index) => button.addEventListener('click', () => activateView(viewOrder[index])));
  $$('.mobile-nav button').forEach((button, index) => button.addEventListener('click', () => activateView(viewOrder[index])));
  $('.compose-main')?.addEventListener('click', () => {
    activateView('feed');
    setTimeout(() => $('#composerText').focus(), 120);
  });
}

function installRoleMarkers() {
  const composer = $('.composer');
  if (composer && !$('.author-role-marker', composer)) {
    const marker = document.createElement('div');
    marker.className = 'role-marker author-role-marker';
    marker.textContent = text('authorSide');
    composer.prepend(marker);
  }
  const panelHead = $('.right-rail .side-panel-head');
  if (panelHead && !$('.responder-role-marker', panelHead)) {
    const marker = document.createElement('span');
    marker.className = 'role-marker responder-role-marker';
    marker.textContent = text('responderSide');
    panelHead.appendChild(marker);
  }
}

function installResetButton() {
  if ($('#resetDemo')) return;
  const button = document.createElement('button');
  button.id = 'resetDemo';
  button.className = 'reset-demo';
  button.type = 'button';
  button.textContent = text('reset');
  $('.header-actions')?.insertBefore(button, $('.lang-switch'));
  button.addEventListener('click', async () => {
    sessionStorage.removeItem('drsk-open-requests');
    sessionStorage.removeItem('drsk-responder-state');
    openRequests = [];
    responderState = null;
    latestDecision = null;
    currentRequestId = null;
    routingEnabled = false;
    $('#composerText').value = '';
    hideIntentPanel();
    $('#routeResult').classList.remove('visible');
    routeResultMode = null;
    renderMatchingWindow();
    resetPreview();
    await checkPipeline();
    showToast('resetToast');
  });
}

function installMobileInbox() {
  if ($('#mobileInboxButton')) return;
  const button = document.createElement('button');
  button.id = 'mobileInboxButton';
  button.className = 'mobile-inbox-fab';
  button.type = 'button';
  button.innerHTML = `<span class="mini-orb" aria-hidden="true"></span><b>${text('responderSide')}</b>`;
  document.body.appendChild(button);
  button.addEventListener('click', openMobileInbox);

  const close = document.createElement('button');
  close.id = 'mobileInboxClose';
  close.className = 'mobile-inbox-close';
  close.type = 'button';
  close.textContent = text('close');
  $('.right-rail')?.prepend(close);
  close.addEventListener('click', closeMobileInbox);
}

function openMobileInbox() {
  $('.right-rail')?.classList.add('mobile-open');
  document.body.classList.add('mobile-inbox-open');
}
function closeMobileInbox() {
  $('.right-rail')?.classList.remove('mobile-open');
  document.body.classList.remove('mobile-inbox-open');
}
function updateMobileInboxButton() {
  const button = $('#mobileInboxButton');
  if (!button) return;
  button.classList.toggle('has-match', Boolean(latestDecision?.match));
  button.hidden = activeView !== 'feed';
  const label = $('b', button);
  if (label) label.textContent = text('responderSide');
  const close = $('#mobileInboxClose');
  if (close) close.textContent = text('close');
  const author = $('.author-role-marker');
  if (author) author.textContent = text('authorSide');
  const responder = $('.responder-role-marker');
  if (responder) responder.textContent = text('responderSide');
  const reset = $('#resetDemo');
  if (reset) reset.textContent = text('reset');
}

function installProductStyles() {
  if ($('#productFixStyles')) return;
  const style = document.createElement('style');
  style.id = 'productFixStyles';
  style.textContent = `
    .role-marker{display:inline-flex;align-items:center;width:max-content;padding:4px 7px;border-radius:999px;background:#f1f5ff;color:#3158c7;font-size:8px;font-weight:850;letter-spacing:.02em}
    .author-role-marker{margin:0 0 8px 57px}.responder-role-marker{margin-left:auto}.reset-demo{border:1px solid var(--line);background:#fff;border-radius:999px;padding:6px 9px;color:var(--muted);font-size:9px;font-weight:760;cursor:pointer}
    .active-action{color:var(--blue)!important}.mobile-responder-link{display:none!important}.secondary-view{min-height:calc(100vh - 58px);padding:28px 26px;background:#fff}.secondary-view[hidden]{display:none}.secondary-head{max-width:520px;margin-bottom:24px}.secondary-head h2{font-size:28px;letter-spacing:-.04em;margin:8px 0 4px}.secondary-head p{color:var(--muted);margin:0;font-size:13px}.role-badge{display:inline-flex;padding:4px 7px;border:1px solid var(--line);border-radius:999px;color:var(--muted);font-size:8px;font-weight:800;text-transform:uppercase}
    .view-search{display:flex;align-items:center;gap:9px;padding:13px 14px;border:1px solid var(--line);border-radius:16px;background:#f7f9fb;color:var(--muted);max-width:520px}.view-search svg{width:18px;height:18px}.topic-grid{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}.topic-grid button{border:1px solid var(--line);background:#fff;border-radius:999px;padding:9px 12px;font-weight:720;font-size:11px}
    .community-list,.message-list{display:grid;gap:0;border:1px solid var(--line);border-radius:18px;overflow:hidden}.community-list>div,.message-list>div{padding:15px 16px;border-bottom:1px solid var(--line)}.community-list>div:last-child,.message-list>div:last-child{border-bottom:0}.community-list b{display:block;font-size:13px}.community-list span,.message-list small{display:block;color:var(--muted);font-size:9px;margin-top:3px}.message-list>div{display:flex;align-items:center;gap:11px}.message-list p{margin:0}.message-list .avatar{width:36px;height:36px}.empty-row{justify-content:center!important;color:var(--muted);font-size:10px}
    .profile-demo{max-width:520px;padding:22px;border:1px solid var(--line);border-radius:20px}.profile-avatar{width:64px;height:64px;font-size:18px}.profile-demo h3{margin:12px 0 1px;font-size:18px}.profile-demo>span{color:var(--muted);font-size:10px}.profile-demo p{font-size:12px}.profile-stats{display:flex;gap:22px;margin-top:14px}.profile-stats b{font-size:13px}.profile-stats small{font-size:9px;color:var(--muted);font-weight:600}
    .mobile-inbox-fab,.mobile-inbox-close{display:none}.right-rail.mobile-open{display:block!important}
    @media(max-width:860px){.mobile-responder-link{display:inline-flex!important}.mobile-inbox-fab{position:fixed;right:14px;bottom:72px;z-index:42;display:flex;align-items:center;gap:7px;border:1px solid rgba(40,100,255,.18);background:rgba(255,255,255,.96);box-shadow:0 12px 34px rgba(25,52,91,.18);border-radius:999px;padding:7px 10px 7px 7px;cursor:pointer}.mobile-inbox-fab .mini-orb{width:24px;height:24px}.mobile-inbox-fab b{font-size:9px}.mobile-inbox-fab.has-match{border-color:rgba(40,100,255,.42);box-shadow:0 12px 38px rgba(40,100,255,.22)}.right-rail.mobile-open{position:fixed;inset:0 0 0 auto;z-index:70;width:min(420px,100%);height:100dvh;overflow:auto;background:#fff;padding:52px 14px 90px;box-shadow:-24px 0 70px rgba(10,25,45,.2)}.mobile-inbox-close{display:block;position:absolute;top:12px;right:14px;border:1px solid var(--line);background:#fff;border-radius:999px;padding:7px 10px;font-size:9px;font-weight:800}.mobile-inbox-open{overflow:hidden}.right-rail.mobile-open .search-box{display:none}.right-rail.mobile-open .side-panel{margin-top:8px}.right-rail.mobile-open .side-panel:last-child{display:none}.author-role-marker{margin-left:49px}.reset-demo{display:none}}
    @media(max-width:640px){.secondary-view{padding:22px 16px 84px}.secondary-head h2{font-size:24px}.author-role-marker{margin-left:46px}.mobile-inbox-fab{bottom:66px}}
  `;
  document.head.appendChild(style);
}

function bindEvents() {
  $$('.lang-switch button').forEach((button) => button.addEventListener('click', () => applyLanguage(button.dataset.lang)));
  const textarea = $('#composerText');
  textarea.addEventListener('input', () => {
    clearTimeout(analyzeTimer);
    analyzeTimer = setTimeout(analyzePost, 650);
  });
  $$('.demo-chip').forEach((button) => button.addEventListener('click', () => {
    textarea.value = demoExamples()[button.dataset.demo];
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
    routeResultMode = null;
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
    if (event.key === 'Escape') { $('#explainSheet').classList.remove('visible'); closeMobileInbox(); }
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
    if (tab !== $$('.feed-tab')[0]) showToast('followingToast');
  }));
}

installProductStyles();
installNavigation();
installRoleMarkers();
installResetButton();
installMobileInbox();
wirePostActions();
applyLanguage(language);
bindEvents();
activateView('feed');
renderMatchingWindow();
updateBudget();
resetPreview();
checkPipeline();
