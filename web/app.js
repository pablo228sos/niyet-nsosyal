const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

const copy = {
  en: {
    feed: 'Feed', following: 'Following', explore: 'Explore', communities: 'Communities', messages: 'Messages', profile: 'Profile', compose: 'Post',
    layerSub: 'interaction layer', layerNote: 'Concept integration for NSosyal. Research prototype.', concept: 'Concept prototype', search: 'Search NSosyal',
    productDescriptor: 'Evidence-aware social coordination', productNav: 'Product navigation', evidenceNav: 'Evidence', allocationLab: 'Allocation Lab', technical: 'Technical', researchPrototype: 'Research prototype', heroKicker: 'Context before reaction', heroTitle: 'A social feed that can trace evidence and route human attention.', heroText: 'DRSK connects SOURCECHAIN verification with NIYET coordination—without hiding uncertainty or presenting development signals as probabilities.', systemLayers: 'DRSK system layers', verifyClaims: 'Verify claims', routeAttention: 'Route attention',
    placeholder: 'What is happening?', publish: 'Post', demoHelp: 'Try: ask for help', demoCollab: 'Try: find a collaborator', demoNormal: 'Try: normal post',
    intentTitle: 'This post may need a human response', intentSub: 'NIYET suggests an intent. You confirm before routing.', modelSuggestion: 'model suggestion', modelScope: 'Model scope: Turkish controlled development data',
    ask: 'ASK', feedback: 'FEEDBACK', collaborate: 'COLLABORATE', discuss: 'DISCUSS', notNow: 'Not now', route: 'Route with NIYET', privateNote: 'You stay in control',
    previewTitle: 'Responder preview', previewSub: 'What the request looks like on the responder side', live: 'live', waiting: 'WAITING', noRoute: 'no route yet', previewEmpty: 'Route a response-seeking post to see the responder side.',
    technicalDetails: 'Technical details', accept: 'Accept', skip: 'Skip', attention: 'Session capacity', pause: 'Routing is on', pauseSub: 'The matched responder can pause new requests',
    trends: 'Trends for you', trend2: 'Artificial Intelligence', trend3: 'Robotics', trendTechnology: 'Technology · Trending', trendAi: 'AI · Trending', trendEngineering: 'Engineering · Trending', demoFeed: 'demo feed', posts: 'posts', post1Copy: 'We finally got the robot stable on straight lines. Turns are still the hard part. Testing a new PID profile tonight.', post2Copy: 'Looking for one frontend developer for a weekend prototype. React is enough. Small team, clear scope.', routed: 'Routed with NIYET', demoMedia: 'PID response trace · demo media',
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
    evidenceTitle: 'Evidence check', evidenceWaiting: 'Not checked', showEvidence: 'Show evidence', hideEvidence: 'Hide evidence', evidenceUnavailable: 'Evidence check unavailable', evidenceNotRequired: 'No factual claim needs checking', askPerson: 'Ask a relevant person', askingPerson: 'Requesting human review', claimsLabel: 'Claim', sourceLabel: 'Open source', passageLabel: 'Evidence passage', distortionLabel: 'Distortion Lens', resolutionLabel: 'Resolution', noEvidence: 'No supporting source was found in the controlled corpus', claimSignal: 'Claim signal', evidenceSignal: 'Source passage', singleHop: 'Single-hop transformation shown from the current evidence item', lineageLabel: 'Evidence lineage', sourceCount: 'source URL', sourceCountPlural: 'source URLs', originCount: 'independent origin', originCountPlural: 'independent origins',
    primaryNav: 'Primary navigation', languageLabel: 'Language', demoPrompts: 'Demo prompts', postTools: 'Post tools', media: 'Media', poll: 'Poll', location: 'Location', contextSidebar: 'Context sidebar', mobileNav: 'Mobile navigation', reply: 'Reply', repost: 'Repost', like: 'Like', share: 'Share', toggleRouting: 'Toggle NIYET routing', close: 'Close', notRun: 'not run', skipToFeed: 'Skip to feed',
    now: 'now'
  },
  tr: {
    feed: 'Akış', following: 'Takip', explore: 'Keşfet', communities: 'Topluluklar', messages: 'Mesajlar', profile: 'Profil', compose: 'Gönderi',
    layerSub: 'etkileşim katmanı', layerNote: 'NSosyal için konsept entegrasyon. Araştırma prototipi.', concept: 'Konsept prototip', search: 'NSosyal içinde ara',
    productDescriptor: 'Kanıt duyarlı sosyal koordinasyon', productNav: 'Ürün gezinmesi', evidenceNav: 'Kanıt', allocationLab: 'Dağıtım Laboratuvarı', technical: 'Teknik', researchPrototype: 'Araştırma prototipi', heroKicker: 'Tepkiden önce bağlam', heroTitle: 'Kanıtın izini süren ve insan dikkatini yönlendiren bir sosyal akış.', heroText: 'DRSK, SOURCECHAIN doğrulamasıyla NIYET koordinasyonunu birleştirir; belirsizliği saklamaz ve geliştirme sinyallerini olasılık gibi sunmaz.', systemLayers: 'DRSK sistem katmanları', verifyClaims: 'İddiaları doğrula', routeAttention: 'Dikkati yönlendir',
    placeholder: 'Neler oluyor?', publish: 'Gönder', demoHelp: 'Dene: yardım iste', demoCollab: 'Dene: ekip arkadaşı bul', demoNormal: 'Dene: normal gönderi',
    intentTitle: 'Bu gönderi insan yanıtı arıyor olabilir', intentSub: 'NIYET bir niyet önerir. Yönlendirmeden önce sen onaylarsın.', modelSuggestion: 'model önerisi', modelScope: 'Model kapsamı: Türkçe kontrollü geliştirme verisi',
    ask: 'SORU', feedback: 'GERİ BİLDİRİM', collaborate: 'İŞ BİRLİĞİ', discuss: 'TARTIŞ', notNow: 'Şimdi değil', route: 'NIYET ile yönlendir', privateNote: 'Kontrol sende',
    previewTitle: 'Cevaplayıcı önizlemesi', previewSub: 'İsteğin cevaplayıcı tarafında nasıl göründüğü', live: 'aktif', waiting: 'BEKLİYOR', noRoute: 'henüz yönlendirme yok', previewEmpty: 'Cevaplayıcı tarafını görmek için yanıt arayan bir gönderiyi yönlendir.',
    technicalDetails: 'Teknik ayrıntılar', accept: 'Kabul et', skip: 'Geç', attention: 'Oturum kapasitesi', pause: 'Yönlendirme açık', pauseSub: 'Eşleşen kişi yeni istekleri duraklatabilir',
    trends: 'Senin için trendler', trend2: 'Yapay Zeka', trend3: 'Robotik', trendTechnology: 'Teknoloji · Gündemde', trendAi: 'Yapay Zeka · Gündemde', trendEngineering: 'Mühendislik · Gündemde', demoFeed: 'demo akış', posts: 'gönderi', post1Copy: 'Robotu düz çizgide sonunda kararlı hale getirdik. Virajlar hala zor. Bu gece yeni PID profilini test ediyoruz.', post2Copy: 'Hafta sonu prototipi için bir frontend geliştirici arıyoruz. React yeterli. Küçük ekip, net kapsam.', routed: 'NIYET ile yönlendirildi', demoMedia: 'PID yanıt grafiği · demo medya',
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
    evidenceTitle: 'Kanıt kontrolü', evidenceWaiting: 'Kontrol edilmedi', showEvidence: 'Kanıtı göster', hideEvidence: 'Kanıtı gizle', evidenceUnavailable: 'Kanıt kontrolü kullanılamıyor', evidenceNotRequired: 'Kontrol gerektiren olgusal iddia yok', askPerson: 'İlgili bir kişiye sor', askingPerson: 'İnsan incelemesi isteniyor', claimsLabel: 'İddia', sourceLabel: 'Kaynağı aç', passageLabel: 'Kanıt bölümü', distortionLabel: 'Bozulma Merceği', resolutionLabel: 'Çözüm', noEvidence: 'Kontrollü derlemde destekleyici kaynak bulunamadı', claimSignal: 'İddia sinyali', evidenceSignal: 'Kaynak bölümü', singleHop: 'Mevcut kanıt öğesinden tek adımlı dönüşüm gösteriliyor', lineageLabel: 'Kanıt soyu', sourceCount: 'kaynak adresi', sourceCountPlural: 'kaynak adresi', originCount: 'bağımsız köken', originCountPlural: 'bağımsız köken',
    primaryNav: 'Ana gezinme', languageLabel: 'Dil', demoPrompts: 'Demo örnekleri', postTools: 'Gönderi araçları', media: 'Medya', poll: 'Anket', location: 'Konum', contextSidebar: 'Bağlam kenar çubuğu', mobileNav: 'Mobil gezinme', reply: 'Yanıtla', repost: 'Yeniden gönder', like: 'Beğen', share: 'Paylaş', toggleRouting: 'NIYET yönlendirmesini aç veya kapat', close: 'Kapat', notRun: 'çalıştırılmadı', skipToFeed: 'Akışa geç',
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
let latestDrsk = null;
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

function applyLanguage(nextLanguage, persist = true) {
  language = nextLanguage;
  if (persist) localStorage.setItem('drsk-language', language);
  document.documentElement.lang = language;
  $$('[data-i18n]').forEach((node) => { node.textContent = text(node.dataset.i18n); });
  $$('[data-i18n-placeholder]').forEach((node) => { node.placeholder = text(node.dataset.i18nPlaceholder); });
  $$('[data-i18n-aria]').forEach((node) => { node.setAttribute('aria-label', text(node.dataset.i18nAria)); });
  $('.lang-switch')?.classList.toggle('tr', language === 'tr');
  $$('.lang-switch button').forEach((button) => {
    const active = button.dataset.lang === language;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  });
  renderPipelineState();
  renderMatchingWindow();
  updateBudget();
  updateMobileInboxButton();
  renderSecondaryView();
  if (routeResultMode) renderRouteResult(routeResultMode, latestDecision);
  if (latestDrsk) renderEvidence(latestDrsk);
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

async function callDrsk(value, askHuman = false) {
  const response = await fetch('/api', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: askHuman ? 'resolve' : 'analyze', text: value, ask_human: askHuman, responder_state: responderState })
  });
  if (!response.ok) throw new Error('DRSK request failed');
  return response.json();
}

function safeHttpUrl(value) {
  try {
    const parsed = new URL(String(value));
    return ['http:', 'https:'].includes(parsed.protocol) ? parsed.href : null;
  } catch (_) { return null; }
}

function appendTextElement(parent, tag, className, value) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  node.textContent = String(value ?? '');
  parent.appendChild(node);
  return node;
}

function displayCode(value) {
  const code = String(value || '').toUpperCase();
  const labels = language === 'tr' ? {
    SUPPORTED: 'destekleniyor', PARTIALLY_SUPPORTED: 'kısmen destekleniyor',
    CONFLICTING: 'çelişkili', INSUFFICIENT: 'yetersiz', PARTIAL: 'kısmi',
    EVIDENCE: 'kanıt', HUMAN: 'insan', BOTH: 'kanıt + insan', NONE: 'gerek yok', DEFERRED: 'ertelendi',
    NUMERIC_SHIFT: 'sayısal kayma', CAUSALITY_SHIFT: 'nedensellik kayması',
    CERTAINTY_SHIFT: 'kesinlik kayması', ATTRIBUTION_SHIFT: 'atıf kayması'
  } : {};
  return labels[code] || code.replaceAll('_', ' ').toLocaleLowerCase('en-US');
}

function renderEvidence(payload) {
  latestDrsk = payload;
  const card = $('#evidenceCard');
  const bundle = payload?.evidence_bundle || {};
  const analysis = payload?.post_analysis || bundle.analysis || {};
  const claims = Array.isArray(payload?.claims) ? payload.claims : (Array.isArray(analysis.claims) ? analysis.claims : []);
  const evidence = Array.isArray(bundle.evidence) ? bundle.evidence : [];
  const status = analysis.check_worthy === false ? 'NOT_REQUIRED' : (bundle.status || 'INSUFFICIENT');

  card.hidden = false;
  card.dataset.status = String(status).toLowerCase();
  $('#evidenceStatus').textContent = status === 'NOT_REQUIRED' ? text('evidenceNotRequired') : `${text('evidenceTitle')}: ${displayCode(status)}`;
  $('#evidenceExplanation').textContent = status === 'NOT_REQUIRED'
    ? text('evidenceNotRequired')
    : (bundle.explanation || (evidence.length ? '' : text('noEvidence')));

  const claimList = $('#claimList');
  claimList.replaceChildren();
  if (claims.length) appendTextElement(claimList, 'strong', 'evidence-section-title', text('claimsLabel'));
  claims.forEach((claim) => appendTextElement(claimList, 'p', 'claim-text', claim.text || claim.claim_text || claim));

  const evidenceList = $('#evidenceList');
  evidenceList.replaceChildren();
  evidence.forEach((item) => {
    const article = document.createElement('article');
    article.className = 'evidence-item';
    const head = document.createElement('div');
    head.className = 'evidence-item-head';
    appendTextElement(head, 'strong', '', item.title || item.publisher || text('sourceLabel'));
    appendTextElement(head, 'span', 'evidence-relation', displayCode(item.relation));
    article.appendChild(head);
    if (item.publisher) appendTextElement(article, 'small', 'evidence-publisher', item.publisher);
    appendTextElement(article, 'span', 'evidence-passage-label', text('passageLabel'));
    appendTextElement(article, 'blockquote', 'evidence-passage', item.passage || '');
    const distortions = Array.isArray(item.distortions) ? item.distortions.filter((value) => value && value !== 'NONE') : [];
    const claimText = claims[0]?.text || claims[0]?.claim_text || claims[0] || '';
    if (item.passage || claimText) {
      const lens = document.createElement('div');
      lens.className = 'distortion-lens';
      const sourceNode = document.createElement('div');
      sourceNode.className = 'lens-node source-node';
      appendTextElement(sourceNode, 'span', 'lens-label', text('evidenceSignal'));
      appendTextElement(sourceNode, 'p', '', item.passage || '—');
      lens.appendChild(sourceNode);
      const transform = document.createElement('div');
      transform.className = 'lens-transform';
      appendTextElement(transform, 'span', '', distortions.length ? distortions.map(displayCode).join(' + ') : displayCode(item.relation));
      transform.setAttribute('aria-label', `${text('distortionLabel')}: ${transform.textContent}`);
      lens.appendChild(transform);
      const claimNode = document.createElement('div');
      claimNode.className = 'lens-node claim-node';
      appendTextElement(claimNode, 'span', 'lens-label', text('claimSignal'));
      appendTextElement(claimNode, 'p', '', claimText || '—');
      lens.appendChild(claimNode);
      appendTextElement(lens, 'small', 'lens-scope', text('singleHop'));
      article.appendChild(lens);
    }
    if (distortions.length) {
      const labels = document.createElement('div');
      labels.className = 'distortion-list';
      appendTextElement(labels, 'span', 'distortion-prefix', `${text('distortionLabel')}:`);
      distortions.forEach((value) => appendTextElement(labels, 'span', 'distortion-chip', displayCode(value)));
      article.appendChild(labels);
    }
    const href = safeHttpUrl(item.source_url || item.canonical_url);
    if (href) {
      const link = appendTextElement(article, 'a', 'evidence-source-link', text('sourceLabel'));
      link.href = href;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
    }
    evidenceList.appendChild(article);
  });

  if (evidence.length) {
    const origins = new Set(evidence.map((item) => item.origin_cluster_id || item.canonical_url || item.source_url).filter(Boolean));
    const lineage = document.createElement('div');
    lineage.className = 'evidence-lineage';
    appendTextElement(lineage, 'span', 'lineage-title', text('lineageLabel'));
    const flow = document.createElement('div');
    flow.className = 'lineage-flow';
    appendTextElement(flow, 'strong', 'lineage-node', `${evidence.length} ${text(evidence.length === 1 ? 'sourceCount' : 'sourceCountPlural')}`);
    appendTextElement(flow, 'span', 'lineage-arrow', '→');
    appendTextElement(flow, 'strong', 'lineage-node origin', `${origins.size || evidence.length} ${text((origins.size || evidence.length) === 1 ? 'originCount' : 'originCountPlural')}`);
    lineage.appendChild(flow);
    evidenceList.prepend(lineage);
  }

  const resolution = payload?.resolution || {};
  const routedPerson = payload?.niyet?.responder_name;
  $('#resolutionStatus').textContent = resolution.path
    ? `${text('resolutionLabel')}: ${displayCode(resolution.path)}${routedPerson ? ` · ${routedPerson}` : ''}`
    : '';
  const askButton = $('#askPerson');
  askButton.hidden = Boolean(resolution.escalation);
  askButton.disabled = false;
  askButton.textContent = text('askPerson');
}

function resetEvidence() {
  latestDrsk = null;
  $('#evidenceCard').hidden = true;
  $('#evidenceDetails').hidden = true;
  $('#evidenceToggle').setAttribute('aria-expanded', 'false');
  $('.evidence-toggle-label').textContent = text('showEvidence');
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
    resetEvidence();
    $('#routeResult').classList.remove('visible');
    routeResultMode = null;
    return;
  }
  const button = $('#routeIntent');
  button.disabled = true;
  button.textContent = text('analyzing');
  try {
    const [niyetResult, drskResult] = await Promise.all([
      callPipeline(value),
      pipelineLive ? callDrsk(value).catch(() => null) : Promise.resolve(null)
    ]);
    latestDecision = niyetResult;
    if (drskResult) renderEvidence(drskResult);
    else resetEvidence();
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
    resetEvidence();
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
  box.replaceChildren();
  appendTextElement(box, 'strong', '', mode === 'normal' ? text('normalPost') : (!decision?.match ? text('routeNoMatch') : text('routeFound')));
  const meta = document.createElement('div');
  meta.className = 'route-meta';
  box.appendChild(meta);
  const addChip = (value, className = 'route-chip') => appendTextElement(meta, className === 'button' ? 'button' : 'span', className === 'button' ? 'route-chip action-chip' : className, value);
  if (mode === 'normal') {
    const force = addChip(text('useAnyway'), 'button');
    force.id = 'forceNiyet';
    force.type = 'button';
    box.classList.add('visible');
    force.addEventListener('click', () => {
      setIntent('ask');
      $('#intentPanel').classList.add('visible');
    });
    return;
  }
  if (!decision?.match) {
    addChip(`${text('confirmedIntent')}: ${intentLabel()}`);
    addChip(text('modelScopeShort'));
    box.classList.add('visible');
    return;
  }
  addChip(decision.match.name);
  addChip(`${text('confirmedIntent')}: ${intentLabel()}`);
  addChip(`${openRequests.length} ${openRequests.length === 1 ? text('openRequest') : text('openRequests')}`);
  const responderLink = addChip(text('openResponder'), 'button');
  responderLink.type = 'button';
  responderLink.classList.add('mobile-responder-link');
  box.classList.add('visible');
  responderLink.addEventListener('click', openMobileInbox);
}

function renderMatchPreview(decision) {
  const card = $('#matchState');
  card.classList.remove('empty', 'loading');
  card.dataset.state = 'ready';
  if (!decision?.match) {
    $('#matchType').textContent = intentLabel();
    $('#matchStatus').textContent = text('noCandidate');
    $('#matchPostText').textContent = $('#composerText').value.trim();
    $('#matchReasons').replaceChildren();
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
  const matchReasons = $('#matchReasons');
  matchReasons.replaceChildren();
  (decision.match.reason || []).forEach((reason) => appendTextElement(matchReasons, 'div', 'match-reason-line', localizeReason(reason)));
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

function appendPostEvidence(article, payload) {
  const bundle = payload?.evidence_bundle;
  if (!bundle) return;
  const postBody = article.querySelector('.post-grid > div:last-child');
  const actions = $('.post-actions', article);
  const checkWorthy = Boolean(payload?.post_analysis?.check_worthy ?? bundle?.analysis?.check_worthy);
  if (!checkWorthy) {
    const note = appendTextElement(postBody, 'span', 'post-evidence-note', text('evidenceNotRequired'));
    postBody.insertBefore(note, actions);
    return;
  }

  const disclosure = document.createElement('details');
  disclosure.className = 'post-evidence-disclosure';
  const summary = appendTextElement(disclosure, 'summary', 'post-evidence-summary', `${text('evidenceTitle')}: ${displayCode(bundle.status)}`);
  summary.setAttribute('aria-label', `${text('evidenceTitle')}: ${displayCode(bundle.status)}`);
  if (bundle.explanation) appendTextElement(disclosure, 'p', 'post-evidence-explanation', bundle.explanation);
  (Array.isArray(bundle.evidence) ? bundle.evidence : []).forEach((item) => {
    const row = document.createElement('div');
    row.className = 'post-evidence-row';
    appendTextElement(row, 'strong', '', item.title || item.publisher || text('sourceLabel'));
    appendTextElement(row, 'blockquote', '', item.passage || '');
    const distortions = Array.isArray(item.distortions) ? item.distortions.filter((value) => value && value !== 'NONE') : [];
    if (distortions.length) appendTextElement(row, 'small', '', `${text('distortionLabel')}: ${distortions.map(displayCode).join(', ')}`);
    const href = safeHttpUrl(item.source_url || item.canonical_url);
    if (href) {
      const link = appendTextElement(row, 'a', '', text('sourceLabel'));
      link.href = href;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
    }
    disclosure.appendChild(row);
  });
  postBody.insertBefore(disclosure, actions);
}

function createPost(textValue) {
  const article = document.createElement('article');
  article.className = 'post-card demo-user-post';
  article.innerHTML = `<div class="post-grid"><div class="avatar" aria-hidden="true">AB</div><div><div class="post-head"><span class="post-name">Demo User</span><span class="post-handle">@demo.user</span><span class="post-time">· ${text('now')}</span></div><p class="post-copy"></p>${routingEnabled ? `<div class="niyet-tag"><span class="niyet-dot"></span><span data-i18n="routed">${text('routed')}</span></div>` : ''}<div class="post-actions"><button class="post-action" data-action="reply" type="button" aria-label="${text('reply')}">${iconMarkup('i-reply')}<span>0</span></button><button class="post-action" data-action="repost" type="button" aria-label="${text('repost')}">${iconMarkup('i-repeat')}<span>0</span></button><button class="post-action" data-action="like" type="button" aria-label="${text('like')}">${iconMarkup('i-heart')}<span>0</span></button><button class="post-action" data-action="share" type="button" aria-label="${text('share')}">${iconMarkup('i-share')}</button></div></div></div>`;
  $('.post-copy', article).textContent = textValue;
  appendPostEvidence(article, latestDrsk);
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
  $('#matchReasons').replaceChildren();
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
  $('.header-actions')?.prepend(button);
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
    resetEvidence();
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
  if (button) {
    button.classList.toggle('has-match', Boolean(latestDecision?.match));
    button.hidden = activeView !== 'feed';
    const label = $('b', button);
    if (label) label.textContent = text('responderSide');
  }
  const close = $('#mobileInboxClose');
  if (close) close.textContent = text('close');
  const author = $('.author-role-marker');
  if (author) author.textContent = text('authorSide');
  const responder = $('.responder-role-marker');
  if (responder) responder.textContent = text('responderSide');
  const reset = $('#resetDemo');
  if (reset) reset.textContent = text('reset');
}

let sheetReturnFocus = null;
function openExplainSheet(trigger = document.activeElement) {
  sheetReturnFocus = trigger;
  const sheet = $('#explainSheet');
  sheet.classList.add('visible');
  sheet.setAttribute('aria-hidden', 'false');
  $('#closeSheet').focus();
}
function closeExplainSheet() {
  const sheet = $('#explainSheet');
  if (!sheet.classList.contains('visible')) return;
  sheet.classList.remove('visible');
  sheet.setAttribute('aria-hidden', 'true');
  sheetReturnFocus?.focus?.();
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
  $('#evidenceToggle').addEventListener('click', () => {
    const details = $('#evidenceDetails');
    const expanded = details.hidden;
    details.hidden = !expanded;
    $('#evidenceToggle').setAttribute('aria-expanded', String(expanded));
    $('.evidence-toggle-label').textContent = text(expanded ? 'hideEvidence' : 'showEvidence');
  });
  $('#askPerson').addEventListener('click', async () => {
    const value = textarea.value.trim();
    if (!value) return;
    const button = $('#askPerson');
    button.disabled = true;
    button.textContent = text('askingPerson');
    try {
      renderEvidence(await callDrsk(value, true));
      $('#evidenceDetails').hidden = false;
      $('#evidenceToggle').setAttribute('aria-expanded', 'true');
      $('.evidence-toggle-label').textContent = text('hideEvidence');
    } catch (_) {
      button.disabled = false;
      button.textContent = text('askPerson');
    }
  });
  $('#publishPost').addEventListener('click', () => {
    const value = textarea.value.trim();
    if (!value) return;
    createPost(value);
    textarea.value = '';
    latestDecision = null;
    routingEnabled = false;
    hideIntentPanel();
    resetEvidence();
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
    if (!$('#explainMatch').disabled) openExplainSheet($('#explainMatch'));
  });
  $('#closeSheet').addEventListener('click', closeExplainSheet);
  $('#openTechnical')?.addEventListener('click', () => openExplainSheet($('#openTechnical')));
  $('#explainSheet').addEventListener('click', (event) => {
    if (event.target === $('#explainSheet')) closeExplainSheet();
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') { closeExplainSheet(); closeMobileInbox(); }
    if (event.key === 'Tab' && $('#explainSheet').classList.contains('visible')) {
      const focusable = $$('#explainSheet button:not([disabled]), #explainSheet a[href], #explainSheet input:not([disabled])');
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
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

installNavigation();
installRoleMarkers();
installResetButton();
installMobileInbox();
wirePostActions();
applyLanguage(language, false);
bindEvents();
window.__drskAppReady = true;
window.dispatchEvent(new CustomEvent('drsk-app-ready'));
activateView('feed');
renderMatchingWindow();
updateBudget();
resetPreview();
checkPipeline();
