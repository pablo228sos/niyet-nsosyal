const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

const apiCandidates = ['/api/human-help', '/api/human_help'];
const exampleScenario = {
  en: 'Research proves coffee consumption causes lower mortality. Can someone explain what the study actually shows?',
  tr: 'Araştırma kahve tüketiminin daha düşük ölüm riskine neden olduğunu kanıtlıyor. Çalışmanın aslında ne gösterdiğini biri açıklayabilir mi?'
};

let apiEndpoint = sessionStorage.getItem('drsk-human-help-endpoint') || null;
let language = localStorage.getItem('drsk-live-language') || 'en';
let responders = [];
let selectedResponderId = null;
let currentAuthor = null;
let authorPoll = null;
let authorPollGeneration = 0;
let inboxPoll = null;
let inboxPollGeneration = 0;
let inboxPollCycle = 0;
let responderSnapshot = '';
let inboxSnapshot = '';
let requestBusy = false;

const copy = {
  en: {
    navFeed: 'Feed', navExplore: 'Discover', navCommunities: 'Communities', navMessages: 'Messages', navProfile: 'Profile',
    integrationNote: 'Evidence + human resolution', prototypeLabel: 'Final prototype', feedTitle: 'Feed',
    nativeTarget: 'Native feed concept', stateFeedTitle: 'Four resolution states', stateFeedNote: 'Static examples explain the Resolution Engine. They are not injected into real NSosyal posts.',
    stateEvidenceText: 'Regular physical activity provides significant physical and mental health benefits.', stateEvidenceMeta: 'Supported evidence is enough. No person is needed.',
    stateHumanText: 'My line-following robot oscillates in turns. Which PID term should I tune first?', stateHumanMeta: 'No factual claim to verify. Relevant human context is the useful path.',
    stateBothText: 'Research proves coffee consumption causes lower mortality.', stateBothMeta: 'Evidence exposes an overclaim; a willing responder can interpret the unresolved part.',
    stateNoneText: 'Dark mode looks better than light mode.', stateNoneMeta: 'Opinion. No evidence card and no human request.',
    demoDevice: 'Demo device', authorTab: 'Author', responderTab: 'Responder', authorSide: 'Author side', responderSide: 'DRSK Requests',
    authorHeading: 'Ask without an audience.', responderHeading: 'Requests that match what you can help with.',
    requestLabel: 'What do you need help with?', requestPlaceholder: 'Share a question, claim or idea...', zeroFollowers: '0 followers',
    noFollowers: 'Follower count is never used as an eligibility signal.', routeHuman: 'Ask a relevant person', postWithDrsk: 'Post with DRSK', loadScenario: 'Load example',
    restore: 'Restore request', routedTo: 'Routed to', openResponder: 'Open responder device', copyResponder: 'Copy responder link', evidenceContext: 'Evidence context', humanAnswer: 'Human answer',
    publishedContext: 'Published NSosyal post',
    evidenceHeading: 'What does the source actually say?', boundedNote: 'Bounded evidence, not a truth score.', humanNeeded: 'Evidence needs human context',
    capacityNote: 'Willingness and remaining attention budget are hard constraints.', identity: 'Demo identity', resolved: 'Resolved', routedByNiyet: 'Routed by NIYET',
    resolutionTitle: 'From attention to resolution', stagePost: 'Need', stagePostText: 'A new user asks without an audience.',
    stageEvidenceText: 'SOURCECHAIN exposes what the source supports.', stageHumanText: 'NIYET routes the unresolved part to a willing person.', stageResolvedText: 'Evidence and human context return to the same post.',
    whyItMatters: 'Why it matters', proofText: 'Reach should not decide whether a useful question gets an answer.', followersUsed: 'followers required', systemsTogether: 'evidence + human layers', sharedOutcome: 'shared outcome',
    truthTitle: 'Prototype boundary', truthText: 'Controlled evidence corpus and explicit prototype state. No generic truth score, no hidden psychological profiling.',
    backendDurable: 'durable shared state live', backendMemory: 'prototype state live', backendDown: 'backend unavailable', checking: 'Checking evidence and routing…', pause: 'Pause', resume: 'Resume',
    capacity: 'Attention budget remaining', active: 'routing on', paused: 'routing paused', emptyInbox: 'No routed requests for this responder right now.',
    accept: 'Accept', skip: 'Skip', answer: 'Answer', answerPlaceholder: 'Give the person a concise, useful answer.', send: 'Send answer',
    requestOpened: 'Request opened. NIYET is looking for a willing person.', evidenceRouted: 'Evidence checked. The unresolved part was routed with its source context.',
    noHumanNeeded: 'The bounded evidence was sufficient; no human request was opened.', noHumanAvailable: 'Human context is recommended, but no eligible responder is available right now.', noActionNeeded: 'This content does not need evidence or human resolution.', answerSent: 'Answer sent back to the original post.', requestAccepted: 'Request accepted.', requestSkipped: 'Request skipped. NIYET reallocated it when another eligible responder existed.',
    routingChanged: 'Availability changed, so NIYET reallocated this request. The latest queue is shown.', capacityChanged: 'Responder capacity changed. NIYET recalculated the pending window.', serviceBusy: 'Shared state is temporarily unavailable. Try again in a moment.',
    copied: 'Responder link copied.', copyFailed: 'Copy failed. Open responder mode manually.', restored: 'Request restored from this browser session.',
    networkError: 'The prototype backend is not reachable.', invalidState: 'This request can no longer be restored. Start a new request or reset the demo.',
    evidenceSource: 'Open source', relation: 'Relation', distortion: 'Signal', claimWording: 'Post claim', sourceWording: 'Source passage', resetDone: 'Demo reset.', resetConfirm: 'Reset the prototype state for every connected device?'
  },
  tr: {
    navFeed: 'Akış', navExplore: 'Keşfet', navCommunities: 'Topluluklar', navMessages: 'Mesajlar', navProfile: 'Profil',
    integrationNote: 'Kanıt + insan çözümü', prototypeLabel: 'Final prototipi', feedTitle: 'Akış',
    nativeTarget: 'Yerel akış konsepti', stateFeedTitle: 'Dört çözüm durumu', stateFeedNote: 'Bu sabit örnekler Resolution Engine mantığını açıklar. Gerçek NSosyal gönderilerine enjekte edilmez.',
    stateEvidenceText: 'Düzenli fiziksel aktivite önemli fiziksel ve zihinsel sağlık faydaları sağlar.', stateEvidenceMeta: 'Destekleyici kanıt yeterli. İnsan yanıtı gerekmiyor.',
    stateHumanText: 'Çizgi izleyen robotum virajlarda salınım yapıyor. Önce hangi PID terimini ayarlamalıyım?', stateHumanMeta: 'Doğrulanacak olgusal iddia yok. İlgili insan bağlamı faydalı yol.',
    stateBothText: 'Araştırma kahve tüketiminin daha düşük ölüm riskine neden olduğunu kanıtlıyor.', stateBothMeta: 'Kanıt aşırı iddiayı gösterir; istekli bir cevaplayıcı çözülmeyen kısmı yorumlayabilir.',
    stateNoneText: 'Karanlık mod açık moddan daha iyi görünüyor.', stateNoneMeta: 'Görüş. Kanıt kartı veya insan isteği açılmaz.',
    demoDevice: 'Demo cihazı', authorTab: 'Gönderi sahibi', responderTab: 'Cevaplayıcı', authorSide: 'Gönderi sahibi', responderSide: 'DRSK İstekleri',
    authorHeading: 'Takipçin olmasa da sor.', responderHeading: 'Gerçekten yardımcı olabileceğin istekler.',
    requestLabel: 'Neye ihtiyacın var?', requestPlaceholder: 'Bir soru, iddia veya fikir paylaş...', zeroFollowers: '0 takipçi',
    noFollowers: 'Takipçi sayısı hiçbir zaman uygunluk sinyali olarak kullanılmaz.', routeHuman: 'İlgili bir kişiye sor', postWithDrsk: 'DRSK ile paylaş', loadScenario: 'Örneği yükle',
    restore: 'İsteği geri yükle', routedTo: 'Yönlendirilen kişi', openResponder: 'Cevaplayıcı cihazını aç', copyResponder: 'Cevaplayıcı bağlantısını kopyala', evidenceContext: 'Kanıt bağlamı', humanAnswer: 'İnsan yanıtı',
    publishedContext: 'Yayınlanan NSosyal gönderisi',
    evidenceHeading: 'Kaynak aslında ne söylüyor?', boundedNote: 'Sınırlı kanıt, doğruluk puanı değil.', humanNeeded: 'Kanıt insan bağlamına ihtiyaç duyuyor',
    capacityNote: 'İsteklilik ve kalan dikkat bütçesi kesin kısıtlardır.', identity: 'Demo kimliği', resolved: 'Çözüldü', routedByNiyet: 'NIYET ile yönlendirildi',
    resolutionTitle: 'Dikkatten çözüme', stagePost: 'İhtiyaç', stagePostText: 'Yeni kullanıcı kitlesi olmadan soruyor.',
    stageEvidenceText: 'SOURCECHAIN kaynağın neyi desteklediğini gösteriyor.', stageHumanText: 'NIYET çözülmeyen kısmı istekli bir kişiye yönlendiriyor.', stageResolvedText: 'Kanıt ve insan bağlamı aynı gönderiye dönüyor.',
    whyItMatters: 'Neden önemli', proofText: 'Faydalı bir sorunun yanıt alıp almamasını erişim belirlememeli.', followersUsed: 'gerekli takipçi', systemsTogether: 'kanıt + insan katmanı', sharedOutcome: 'ortak sonuç',
    truthTitle: 'Prototip sınırı', truthText: 'Kontrollü kanıt derlemi ve açık prototip durumu. Genel doğruluk puanı veya gizli psikolojik profilleme yok.',
    backendDurable: 'kalıcı ortak durum aktif', backendMemory: 'prototip durumu aktif', backendDown: 'backend erişilemiyor', checking: 'Kanıt ve yönlendirme kontrol ediliyor…', pause: 'Duraklat', resume: 'Devam et',
    capacity: 'Kalan dikkat bütçesi', active: 'yönlendirme açık', paused: 'yönlendirme kapalı', emptyInbox: 'Bu cevaplayıcı için şu anda yönlendirilmiş istek yok.',
    accept: 'Kabul et', skip: 'Geç', answer: 'Yanıt', answerPlaceholder: 'Kısa ve faydalı bir yanıt yaz.', send: 'Yanıtı gönder',
    requestOpened: 'İstek açıldı. NIYET istekli birini arıyor.', evidenceRouted: 'Kanıt kontrol edildi. Çözülmeyen kısım kaynak bağlamıyla birlikte yönlendirildi.',
    noHumanNeeded: 'Sınırlandırılmış kanıt yeterliydi; insan isteği açılmadı.', noHumanAvailable: 'İnsan bağlamı öneriliyor, ancak şu anda uygun bir cevaplayıcı yok.', noActionNeeded: 'Bu içerik için kanıt veya insan çözümü gerekmiyor.', answerSent: 'Yanıt asıl gönderiye geri ulaştı.', requestAccepted: 'İstek kabul edildi.', requestSkipped: 'İstek geçildi. Uygun başka cevaplayıcı varsa NIYET yeniden yönlendirdi.',
    routingChanged: 'Uygunluk değiştiği için NIYET bu isteği yeniden yönlendirdi. Güncel kuyruk gösteriliyor.', capacityChanged: 'Cevaplayıcı kapasitesi değişti. NIYET bekleyen istekleri yeniden hesapladı.', serviceBusy: 'Ortak durum geçici olarak kullanılamıyor. Birazdan tekrar dene.',
    copied: 'Cevaplayıcı bağlantısı kopyalandı.', copyFailed: 'Kopyalama başarısız. Cevaplayıcı modunu elle aç.', restored: 'İstek bu tarayıcı oturumundan geri yüklendi.',
    networkError: 'Prototip backendine ulaşılamıyor.', invalidState: 'Bu istek artık geri yüklenemiyor.',
    evidenceSource: 'Kaynağı aç', relation: 'İlişki', distortion: 'Sinyal', claimWording: 'Gönderi iddiası', sourceWording: 'Kaynak pasajı', resetDone: 'Demo sıfırlandı.', resetConfirm: 'Bağlı tüm cihazlar için prototip durumunu sıfırlamak istiyor musun?'
  }
};

function t(key) { return copy[language]?.[key] || copy.en[key] || key; }

function setMessage(target, message, isError = false) {
  target.textContent = message || '';
  target.classList.toggle('error', isError);
}

function errorCode(error) { return error?.code || error?.message || ''; }

function friendlyError(error) {
  const code = errorCode(error);
  if (['request_not_assigned', 'request_not_open', 'request_not_accepted'].includes(code)) return t('routingChanged');
  if (code === 'responder_capacity_exhausted') return t('capacityChanged');
  if (code === 'state_temporarily_unavailable' || error?.status === 503) return t('serviceBusy');
  return code || t('networkError');
}

function isStaleRoutingError(error) { return error?.status === 409; }

function safeUrl(value) {
  try {
    const url = new URL(value);
    return ['http:', 'https:'].includes(url.protocol) ? url.href : null;
  } catch (_) { return null; }
}

function buildPublishedContext(context) {
  if (!context?.published_observed) return null;
  const href = safeUrl(context.post_url);
  const node = document.createElement(href ? 'a' : 'span');
  node.className = 'published-context';
  node.textContent = t('publishedContext');
  if (href) {
    node.href = href;
    node.target = '_blank';
    node.rel = 'noopener noreferrer';
  }
  return node;
}

async function rawApi(endpoint, payload = null) {
  const options = payload ? {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  } : { method: 'GET' };
  const response = await fetch(endpoint, options);
  let data = {};
  try { data = await response.json(); } catch (_) {}
  if (!response.ok) {
    const error = new Error(data.error || `HTTP ${response.status}`);
    error.status = response.status;
    error.code = data.error || null;
    throw error;
  }
  return data;
}

async function callApi(payload = null) {
  const candidates = apiEndpoint ? [apiEndpoint, ...apiCandidates.filter((item) => item !== apiEndpoint)] : apiCandidates;
  let lastError;
  for (const endpoint of candidates) {
    try {
      const result = await rawApi(endpoint, payload);
      apiEndpoint = endpoint;
      sessionStorage.setItem('drsk-human-help-endpoint', endpoint);
      return result;
    } catch (error) {
      lastError = error;
      // A bare 404 may mean this deployment uses the alternate API filename.
      // A JSON 404 with a domain error (for example request_not_found) is real
      // application state and must not be replayed against another endpoint.
      if (error.status && (error.status !== 404 || error.code)) throw error;
    }
  }
  throw lastError || new Error('backend unavailable');
}

function applyLanguage() {
  document.documentElement.lang = language;
  $$('[data-copy]').forEach((node) => { node.textContent = t(node.dataset.copy); });
  $$('[data-placeholder]').forEach((node) => { node.placeholder = t(node.dataset.placeholder); });
  $('#languageToggle').textContent = language === 'en' ? 'TR' : 'EN';
  if (responders.length) renderResponderMeta();
  if (currentAuthor?.request) renderAuthorRequest(currentAuthor.request);
}

function setRole(role, updateUrl = true) {
  const responder = role === 'responder';
  $('#authorView').hidden = responder;
  $('#responderView').hidden = !responder;
  $('#authorTab').classList.toggle('active', !responder);
  $('#responderTab').classList.toggle('active', responder);
  $('#authorTab').setAttribute('aria-pressed', String(!responder));
  $('#responderTab').setAttribute('aria-pressed', String(responder));
  if (updateUrl) {
    const url = new URL(location.href);
    url.searchParams.set('role', responder ? 'responder' : 'author');
    history.replaceState(null, '', url);
  }
  if (responder) {
    stopAuthorPoll();
    startInboxPoll();
  } else {
    stopInboxPoll();
    if (currentAuthor?.request) startAuthorPoll();
  }
}

async function checkBackend() {
  const badge = $('#connectionBadge');
  badge.dataset.state = 'checking';
  badge.textContent = t('checking');
  try {
    const data = await callApi();
    const nextResponders = Array.isArray(data.responders) ? data.responders : [];
    const nextSnapshot = JSON.stringify(nextResponders);
    badge.dataset.state = 'live';
    badge.dataset.durable = String(Boolean(data.state_durable));
    badge.textContent = t(data.state_durable ? 'backendDurable' : 'backendMemory');
    if (nextSnapshot !== responderSnapshot) {
      responders = nextResponders;
      responderSnapshot = nextSnapshot;
      populateResponders();
    }
    return true;
  } catch (_) {
    badge.dataset.state = 'error';
    badge.textContent = t('backendDown');
    return false;
  }
}

function populateResponders() {
  const select = $('#responderSelect');
  const previousResponderId = selectedResponderId;
  const desired = new URL(location.href).searchParams.get('responder') || selectedResponderId;
  select.replaceChildren();
  responders.forEach((responder) => {
    const option = document.createElement('option');
    option.value = responder.id;
    option.textContent = responder.name;
    select.appendChild(option);
  });
  if (desired && responders.some((item) => item.id === desired)) select.value = desired;
  selectedResponderId = select.value || responders[0]?.id || null;
  if (selectedResponderId !== previousResponderId) inboxSnapshot = '';
  $('#availabilityToggle').disabled = !selectedResponderId;
  renderResponderMeta();
}

function responderRecord() { return responders.find((item) => item.id === selectedResponderId) || null; }

function renderResponderMeta() {
  const target = $('#responderMeta');
  const record = responderRecord();
  target.replaceChildren();
  if (!record) return;
  const capacity = document.createElement('span');
  capacity.textContent = `${t('capacity')}: ${record.remaining_slots}`;
  const active = document.createElement('span');
  active.textContent = t(record.active ? 'active' : 'paused');
  target.append(capacity, active);
  $('#availabilityToggle').textContent = t(record.active ? 'pause' : 'resume');
}

function persistAuthor(request) {
  if (!request?.request_id || !request?.author_token) return;
  currentAuthor = { request };
  sessionStorage.setItem('drsk-live-author', JSON.stringify({
    request_id: request.request_id,
    author_token: request.author_token,
    text: request.text
  }));
  $('#restoreAuthor').hidden = true;
}

function readStoredAuthor() {
  try { return JSON.parse(sessionStorage.getItem('drsk-live-author') || 'null'); }
  catch (_) { return null; }
}

function updateStages(request = null) {
  const evidence = Boolean(request?.evidence_context);
  const hasHuman = Boolean(request?.assigned_responder);
  const accepted = request?.status === 'ACCEPTED';
  const answered = request?.status === 'ANSWERED' || Boolean(request?.answer);
  const mapping = [
    ['#stagePost', true, Boolean(request)],
    ['#stageEvidence', evidence, hasHuman || answered],
    ['#stageHuman', hasHuman || accepted || answered, answered],
    ['#stageResolved', answered, answered]
  ];
  mapping.forEach(([selector, active, done]) => {
    const node = $(selector);
    if (!node) return;
    node.classList.toggle('active', Boolean(active));
    node.classList.toggle('done', Boolean(done));
  });
}

function renderReasons(values) {
  const target = $('#matchReasons');
  target.replaceChildren();
  (Array.isArray(values) ? values : []).forEach((value) => {
    const chip = document.createElement('span');
    chip.textContent = String(value).replaceAll('_', ' ');
    target.appendChild(chip);
  });
}

function appendDistortionComparison(row, item, distortions) {
  if (!distortions.length || !item?.claim_text || !item?.passage) return false;

  const compare = document.createElement('div');
  compare.className = 'wording-compare';

  const claim = document.createElement('div');
  const claimLabel = document.createElement('small');
  claimLabel.textContent = t('claimWording');
  const claimText = document.createElement('b');
  claimText.textContent = item.claim_text;
  claim.append(claimLabel, claimText);

  const arrow = document.createElement('span');
  arrow.textContent = '↔';
  arrow.setAttribute('aria-hidden', 'true');

  const source = document.createElement('div');
  const sourceLabel = document.createElement('small');
  sourceLabel.textContent = t('sourceWording');
  const sourceText = document.createElement('b');
  sourceText.textContent = item.passage;
  source.append(sourceLabel, sourceText);

  compare.append(claim, arrow, source);
  row.appendChild(compare);
  return true;
}

function renderEvidence(context, target = $('#evidenceItems')) {
  target.replaceChildren();
  const items = Array.isArray(context?.evidence) ? context.evidence : [];
  items.forEach((item) => {
    const row = document.createElement('div');
    row.className = target.id === 'evidenceItems' ? 'evidence-item' : 'inbox-evidence-item';
    const title = document.createElement('strong');
    title.textContent = item.source_title || item.publisher || t('evidenceSource');
    row.appendChild(title);
    if (item.publisher || item.publication_date) {
      const provenance = document.createElement('small');
      provenance.textContent = [item.publisher, item.publication_date].filter(Boolean).join(' · ');
      row.appendChild(provenance);
    }

    const distortions = Array.isArray(item.distortions)
      ? item.distortions.filter((value) => value && value !== 'NONE')
      : [];
    const compared = appendDistortionComparison(row, item, distortions);
    if (item.passage && !compared) {
      const quote = document.createElement('blockquote');
      quote.textContent = item.passage;
      row.appendChild(quote);
    }

    const signals = [];
    if (item.relation) signals.push(`${t('relation')}: ${item.relation}`);
    if (distortions.length) signals.push(`${t('distortion')}: ${distortions.join(', ')}`);
    if (signals.length) {
      const small = document.createElement('small');
      small.textContent = signals.join(' · ');
      row.appendChild(small);
    }

    const href = safeUrl(item.source_url);
    if (href) {
      const link = document.createElement('a');
      link.href = href;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.textContent = t('evidenceSource');
      row.appendChild(link);
    }
    target.appendChild(row);
  });
  if (!items.length) {
    const empty = document.createElement('p');
    empty.textContent = context?.status || 'No bounded evidence attached.';
    target.appendChild(empty);
  }
}

function renderAuthorRequest(request) {
  currentAuthor = { request };
  $('#requestCard').hidden = false;
  $('#requestStatus').textContent = request.status || 'OPEN';
  $('#requestStatus').dataset.status = request.status || 'OPEN';
  $('#requestTextPreview').textContent = request.text || '';
  $('.published-context', $('#requestCard'))?.remove();
  const publishedContext = buildPublishedContext(request.social_context);
  if (publishedContext) $('#requestTextPreview').insertAdjacentElement('afterend', publishedContext);

  const match = request.assigned_responder;
  $('#matchBlock').hidden = !match;
  $('#openResponderDevice').hidden = !match;
  $('#copyResponderLink').hidden = !match;
  $('#attentionBudget').hidden = !match;
  if (match) {
    $('#matchedResponder').textContent = match.name || match.id;
    renderReasons(match.reason);
    const responder = responders.find((item) => item.id === match.id);
    $('#attentionBudget').textContent = responder
      ? `${t('capacity')}: ${responder.remaining_slots}`
      : '';
  }

  const evidence = request.evidence_context;
  $('#evidenceBlock').hidden = !evidence;
  if (evidence) {
    $('#evidenceStatus').textContent = evidence.status || evidence.resolution?.path || 'context';
    renderEvidence(evidence);
  }

  const answered = Boolean(request.answer);
  $('#answerBlock').hidden = !answered;
  $('#humanAnswer').textContent = request.answer || '';
  updateStages(request);
}

async function openAuthorRequest(mode) {
  if (requestBusy) return;
  const value = $('#requestText').value.trim();
  if (!value) { $('#requestText').focus(); return; }
  requestBusy = true;
  $('#routeHuman').disabled = true;
  $('#resolveEvidence').disabled = true;
  setMessage($('#authorMessage'), t('checking'));
  try {
    const result = await callApi({ action: mode, text: value });
    if (!result.request) {
      stopAuthorPoll();
      sessionStorage.removeItem('drsk-live-author');
      currentAuthor = null;
      $('#requestCard').hidden = true;
      updateStages(null);
      const path = result.resolution?.path;
      if (result.evidence_context || path === 'NONE') {
        const synthetic = {
          text: value,
          status: path === 'NONE' ? 'PUBLISHED' : path || 'EVIDENCE',
          evidence_context: path === 'NONE' ? null : result.evidence_context,
          assigned_responder: null,
          answer: null
        };
        renderAuthorRequest(synthetic);
      }
      const message = result.human_recommended
        ? t('noHumanAvailable')
        : path === 'NONE'
          ? t('noActionNeeded')
          : t('noHumanNeeded');
      setMessage($('#authorMessage'), message);
      return;
    }
    persistAuthor(result.request);
    renderAuthorRequest(result.request);
    setMessage($('#authorMessage'), t(mode === 'resolve' ? 'evidenceRouted' : 'requestOpened'));
    startAuthorPoll();
  } catch (error) {
    setMessage($('#authorMessage'), friendlyError(error), true);
  } finally {
    requestBusy = false;
    $('#routeHuman').disabled = false;
    $('#resolveEvidence').disabled = false;
  }
}

async function refreshAuthor(generation = authorPollGeneration) {
  const stored = readStoredAuthor();
  if (!stored?.request_id || !stored?.author_token) return;
  try {
    const result = await callApi({ action: 'status', request_id: stored.request_id, author_token: stored.author_token });
    if (generation !== authorPollGeneration) return;
    if (!result.request) return;
    currentAuthor = { request: { ...result.request, author_token: stored.author_token } };
    $('#restoreAuthor').hidden = true;
    renderAuthorRequest(currentAuthor.request);
    if (result.request.status === 'ANSWERED') stopAuthorPoll();
  } catch (error) {
    if (generation !== authorPollGeneration) return;
    const code = errorCode(error);
    if (code === 'request_not_found' || code === 'invalid_author_token') {
      stopAuthorPoll();
      sessionStorage.removeItem('drsk-live-author');
      $('#restoreAuthor').hidden = true;
      setMessage($('#authorMessage'), t('invalidState'), true);
      return;
    }
    setMessage($('#authorMessage'), friendlyError(error), true);
  }
}

function startAuthorPoll() {
  stopAuthorPoll();
  const generation = ++authorPollGeneration;
  refreshAuthor(generation).finally(() => {
    if (generation === authorPollGeneration) {
      authorPoll = window.setTimeout(() => runAuthorPoll(generation), 1200);
    }
  });
}
async function runAuthorPoll(generation) {
  if (generation !== authorPollGeneration) return;
  authorPoll = null;
  await refreshAuthor(generation);
  if (generation === authorPollGeneration) {
    authorPoll = window.setTimeout(() => runAuthorPoll(generation), 1200);
  }
}
function stopAuthorPoll() {
  authorPollGeneration += 1;
  if (authorPoll) clearTimeout(authorPoll);
  authorPoll = null;
}

function responderLink() {
  const match = currentAuthor?.request?.assigned_responder;
  if (!match?.id) return null;
  const url = new URL(location.href);
  url.searchParams.set('role', 'responder');
  url.searchParams.set('responder', match.id);
  return url.href;
}

function openResponderDevice() {
  const link = responderLink();
  if (!link) return;
  window.open(link, '_blank', 'noopener,noreferrer');
}

async function copyResponderLink() {
  const link = responderLink();
  if (!link) return;
  try {
    await navigator.clipboard.writeText(link);
    setMessage($('#authorMessage'), t('copied'));
  } catch (_) {
    setMessage($('#authorMessage'), `${t('copyFailed')} ${link}`, true);
  }
}

function buildInboxEvidence(context) {
  const wrap = document.createElement('div');
  if (!context) return wrap;
  const title = document.createElement('strong');
  title.textContent = `${t('evidenceContext')}: ${context.status || context.resolution?.path || ''}`;
  const items = document.createElement('div');
  wrap.append(title, items);
  renderEvidence(context, items);
  return wrap;
}

async function recoverInboxConflict(error) {
  const message = friendlyError(error);
  await refreshBackendAndInbox();
  setMessage($('#inboxMessage'), message, true);
}

function renderInbox(requests) {
  const inbox = $('#inbox');
  inbox.replaceChildren();
  if (!requests.length) {
    const empty = document.createElement('div');
    empty.className = 'empty-state';
    empty.textContent = t('emptyInbox');
    inbox.appendChild(empty);
    return;
  }

  const strongest = requests.find((item) => item.status === 'ACCEPTED') || requests[0];
  updateStages(strongest);

  requests.forEach((request) => {
    const fragment = $('#inboxRequestTemplate').content.cloneNode(true);
    const card = $('.inbox-card', fragment);
    const state = $('.request-state', card);
    state.textContent = request.status;
    state.dataset.status = request.status;
    $('.request-id', card).textContent = request.request_id;
    $('.inbox-text', card).textContent = request.text;
    const publishedContext = buildPublishedContext(request.social_context);
    if (publishedContext) $('.inbox-text', card).insertAdjacentElement('afterend', publishedContext);

    const evidenceTarget = $('.inbox-evidence', card);
    if (request.evidence_context) {
      evidenceTarget.hidden = false;
      evidenceTarget.appendChild(buildInboxEvidence(request.evidence_context));
    }

    const accept = $('.accept-request', card);
    const skip = $('.skip-request', card);
    const editor = $('.answer-editor', card);
    const answerText = $('textarea', editor);
    const send = $('.send-answer', editor);
    accept.textContent = t('accept');
    skip.textContent = t('skip');
    $('label', editor).textContent = t('answer');
    answerText.placeholder = t('answerPlaceholder');
    send.textContent = t('send');

    const accepted = request.status === 'ACCEPTED';
    accept.hidden = accepted;
    skip.hidden = accepted;
    editor.hidden = !accepted;

    accept.addEventListener('click', async () => {
      accept.disabled = true;
      skip.disabled = true;
      try {
        const result = await callApi({ action: 'accept', request_id: request.request_id, responder_id: selectedResponderId });
        setMessage($('#inboxMessage'), t('requestAccepted'));
        if (result.request) updateStages(result.request);
        await refreshBackendAndInbox();
      } catch (error) {
        if (isStaleRoutingError(error)) {
          await recoverInboxConflict(error);
          return;
        }
        setMessage($('#inboxMessage'), friendlyError(error), true);
        accept.disabled = false;
        skip.disabled = false;
      }
    });

    skip.addEventListener('click', async () => {
      accept.disabled = true;
      skip.disabled = true;
      try {
        await callApi({ action: 'skip', request_id: request.request_id, responder_id: selectedResponderId });
        setMessage($('#inboxMessage'), t('requestSkipped'));
        await refreshBackendAndInbox();
      } catch (error) {
        if (isStaleRoutingError(error)) {
          await recoverInboxConflict(error);
          return;
        }
        setMessage($('#inboxMessage'), friendlyError(error), true);
        accept.disabled = false;
        skip.disabled = false;
      }
    });

    send.addEventListener('click', async () => {
      const answer = answerText.value.trim();
      if (!answer) { answerText.focus(); return; }
      send.disabled = true;
      try {
        const result = await callApi({ action: 'answer', request_id: request.request_id, responder_id: selectedResponderId, answer });
        setMessage($('#inboxMessage'), t('answerSent'));
        if (result.request) updateStages(result.request);
        await refreshBackendAndInbox();
      } catch (error) {
        if (isStaleRoutingError(error)) {
          await recoverInboxConflict(error);
          return;
        }
        setMessage($('#inboxMessage'), friendlyError(error), true);
        send.disabled = false;
      }
    });

    inbox.appendChild(card);
  });
}

async function refreshInbox(force = false) {
  if (!selectedResponderId) return;
  try {
    const result = await callApi({ action: 'inbox', responder_id: selectedResponderId });
    const requests = Array.isArray(result.requests) ? result.requests : [];
    const snapshot = JSON.stringify(requests);
    if (!force && snapshot === inboxSnapshot) return;
    inboxSnapshot = snapshot;
    renderInbox(requests);
  } catch (error) {
    setMessage($('#inboxMessage'), friendlyError(error), true);
  }
}

async function refreshBackendAndInbox(forceInbox = false) {
  await checkBackend();
  await refreshInbox(forceInbox);
}

function startInboxPoll() {
  stopInboxPoll();
  const generation = ++inboxPollGeneration;
  inboxPollCycle = 0;
  refreshBackendAndInbox(true).finally(() => {
    if (generation === inboxPollGeneration) {
      inboxPoll = window.setTimeout(() => runInboxPoll(generation), 1800);
    }
  });
}
async function runInboxPoll(generation) {
  if (generation !== inboxPollGeneration) return;
  inboxPoll = null;
  await refreshInbox();
  inboxPollCycle += 1;
  if (inboxPollCycle % 5 === 0) await checkBackend();
  if (generation === inboxPollGeneration) {
    inboxPoll = window.setTimeout(() => runInboxPoll(generation), 1800);
  }
}
function stopInboxPoll() {
  inboxPollGeneration += 1;
  if (inboxPoll) clearTimeout(inboxPoll);
  inboxPoll = null;
}

async function toggleAvailability() {
  const record = responderRecord();
  if (!record) return;
  const button = $('#availabilityToggle');
  button.disabled = true;
  try {
    await callApi({ action: record.active ? 'pause' : 'resume', responder_id: record.id });
    await refreshBackendAndInbox();
  } catch (error) {
    setMessage($('#inboxMessage'), friendlyError(error), true);
  } finally { button.disabled = false; }
}

function restoreAuthorButton() {
  const stored = readStoredAuthor();
  const restore = $('#restoreAuthor');
  if (restore) restore.hidden = !stored;
  if (stored?.text && !$('#requestText').value) $('#requestText').value = stored.text;
  $('#charCount').textContent = `${$('#requestText').value.length} / 1200`;
}

async function resetDemo() {
  if (!window.confirm(t('resetConfirm'))) return;
  stopAuthorPoll();
  stopInboxPoll();
  try { await callApi({ action: 'reset' }); }
  catch (error) { setMessage($('#authorMessage'), friendlyError(error), true); return; }
  sessionStorage.removeItem('drsk-live-author');
  inboxSnapshot = '';
  responderSnapshot = '';
  currentAuthor = null;
  $('#requestCard').hidden = true;
  $('#requestText').value = '';
  $('#charCount').textContent = '0 / 1200';
  $('#restoreAuthor')?.setAttribute('hidden', '');
  setMessage($('#authorMessage'), t('resetDone'));
  setMessage($('#inboxMessage'), '');
  updateStages(null);
  await checkBackend();
  if (!$('#responderView').hidden) startInboxPoll();
}

$('#languageToggle').addEventListener('click', () => {
  language = language === 'en' ? 'tr' : 'en';
  localStorage.setItem('drsk-live-language', language);
  applyLanguage();
  inboxSnapshot = '';
  if (!$('#responderView').hidden) refreshInbox(true);
});
$('#authorTab').addEventListener('click', () => setRole('author'));
$('#responderTab').addEventListener('click', () => setRole('responder'));
$('#routeHuman').addEventListener('click', () => openAuthorRequest('open'));
$('#resolveEvidence').addEventListener('click', () => openAuthorRequest('resolve'));
$('#openResponderDevice').addEventListener('click', openResponderDevice);
$('#copyResponderLink').addEventListener('click', copyResponderLink);
$('#loadScenario').addEventListener('click', () => {
  $('#requestText').value = exampleScenario[language];
  $('#charCount').textContent = `${$('#requestText').value.length} / 1200`;
  $('#requestText').focus();
});
$('#resetDemo').addEventListener('click', resetDemo);
$('#requestText').addEventListener('input', (event) => { $('#charCount').textContent = `${event.target.value.length} / 1200`; });
$('#responderSelect').addEventListener('change', () => {
  selectedResponderId = $('#responderSelect').value;
  inboxSnapshot = '';
  const url = new URL(location.href);
  url.searchParams.set('responder', selectedResponderId);
  history.replaceState(null, '', url);
  renderResponderMeta();
  refreshInbox(true);
});
$('#availabilityToggle').addEventListener('click', toggleAvailability);

window.addEventListener('beforeunload', () => { stopAuthorPoll(); stopInboxPoll(); });

(async function init() {
  applyLanguage();
  restoreAuthorButton();
  updateStages(null);
  const params = new URL(location.href).searchParams;
  setRole(params.get('role') === 'responder' ? 'responder' : 'author', false);
  const live = await checkBackend();
  if (!live) {
    setMessage($('#authorMessage'), t('networkError'), true);
    setMessage($('#inboxMessage'), t('networkError'), true);
    return;
  }
  if (params.get('role') === 'responder') startInboxPoll();
  const stored = readStoredAuthor();
  if (stored && params.get('role') !== 'responder') {
    $('#requestText').value = stored.text || '';
    $('#charCount').textContent = `${$('#requestText').value.length} / 1200`;
    await refreshAuthor();
    if (currentAuthor?.request) startAuthorPoll();
  }
})();
