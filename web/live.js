import {
  acceptAssignment,
  answerAssignment,
  createRequest,
  currentUser,
  getInbox,
  getMe,
  getRequest,
  isAuthenticated,
  pauseResponder,
  resumeResponder,
  skipAssignment,
  updateResponderProfile
} from './firebase-client.js';

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

const exampleScenario = {
  en: 'Research proves coffee consumption causes lower mortality. Can someone explain what the study actually shows?',
  tr: 'Araştırma kahve tüketiminin daha düşük ölüm riskine neden olduğunu kanıtlıyor. Çalışmanın aslında ne gösterdiğini biri açıklayabilir mi?'
};

let language = localStorage.getItem('drsk-live-language') || 'en';
let responders = [];
let selectedResponderId = null;
let currentProfile = null;
let currentAssignments = [];
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
    authorTab: 'New user', responderTab: 'Responder', authorSide: 'Author side', responderSide: 'Responder side',
    authorHeading: 'Ask without an audience.', responderHeading: 'Requests that match what you can help with.',
    requestLabel: 'What do you need help with?', requestPlaceholder: 'Share a question, claim or idea...', zeroFollowers: '0 followers',
    noFollowers: 'Follower count is never used as an eligibility signal.', routeHuman: 'Ask a person directly', postWithDrsk: 'Post with DRSK', loadScenario: 'Load example',
    restore: 'Restore request', routedTo: 'Routed to', evidenceContext: 'Evidence context', humanAnswer: 'Human answer',
    publishedContext: 'Published NSosyal post',
    evidenceHeading: 'What does the source actually say?', boundedNote: 'Bounded evidence, not a truth score.', humanNeeded: 'Evidence needs human context',
    capacityNote: 'Willingness and remaining capacity are hard constraints.', identity: 'Firebase identity', resolved: 'Resolved', routedByNiyet: 'Routed by NIYET',
    resolutionTitle: 'From attention to resolution', stagePost: 'Need', stagePostText: 'A new user asks without an audience.',
    stageEvidenceText: 'SOURCECHAIN exposes what the source supports.', stageHumanText: 'NIYET routes the unresolved part to a willing person.', stageResolvedText: 'Evidence and human context return to the same post.',
    whyItMatters: 'Why it matters', proofText: 'Reach should not decide whether a useful question gets an answer.', followersUsed: 'followers required', systemsTogether: 'evidence + human layers', sharedOutcome: 'shared outcome',
    truthTitle: 'Production boundary', truthText: 'Authenticated NIYET state is stored in Firestore. Evidence remains bounded and is never presented as a generic truth score.',
    backendDurable: 'authenticated Firestore live', backendMemory: 'invalid non-durable state', backendDown: 'backend unavailable', checking: 'Checking evidence and routing…', pause: 'Pause', resume: 'Resume',
    capacity: 'slots remaining', active: 'routing on', paused: 'routing paused', emptyInbox: 'No routed requests for this responder right now.',
    accept: 'Accept', skip: 'Skip', answer: 'Answer', answerPlaceholder: 'Give the person a concise, useful answer.', send: 'Send answer',
    requestOpened: 'Request opened. NIYET is looking for a willing person.', evidenceRouted: 'Evidence checked. The unresolved part was routed with its source context.',
    noHumanNeeded: 'The bounded evidence was sufficient; no human request was opened.', noHumanAvailable: 'Human context is recommended, but no eligible responder has capacity right now.', noActionNeeded: 'This content does not need evidence or human resolution.', answerSent: 'Answer sent back to the original post.', requestAccepted: 'Request accepted.', requestSkipped: 'Request skipped. NIYET reallocated it when another eligible responder existed.',
    routingChanged: 'Availability changed, so NIYET reallocated this request. The latest queue is shown.', capacityChanged: 'Responder capacity changed. NIYET recalculated the pending window.', serviceBusy: 'Shared state is temporarily unavailable. Try again in a moment.',
    restored: 'Request restored from this browser session.',
    networkError: 'The authenticated backend is not reachable.', invalidState: 'This request can no longer be restored.',
    evidenceSource: 'Open source', relation: 'Relation', distortion: 'Signal', claimWording: 'Post claim', sourceWording: 'Source passage'
  },
  tr: {
    navFeed: 'Akış', navExplore: 'Keşfet', navCommunities: 'Topluluklar', navMessages: 'Mesajlar', navProfile: 'Profil',
    integrationNote: 'Kanıt + insan çözümü', prototypeLabel: 'Final prototipi', feedTitle: 'Akış',
    authorTab: 'Yeni kullanıcı', responderTab: 'Cevaplayıcı', authorSide: 'Gönderi sahibi', responderSide: 'Cevaplayıcı tarafı',
    authorHeading: 'Takipçin olmasa da sor.', responderHeading: 'Gerçekten yardımcı olabileceğin istekler.',
    requestLabel: 'Neye ihtiyacın var?', requestPlaceholder: 'Bir soru, iddia veya fikir paylaş...', zeroFollowers: '0 takipçi',
    noFollowers: 'Takipçi sayısı hiçbir zaman uygunluk sinyali olarak kullanılmaz.', routeHuman: 'Doğrudan birine sor', postWithDrsk: 'DRSK ile paylaş', loadScenario: 'Örneği yükle',
    restore: 'İsteği geri yükle', routedTo: 'Yönlendirilen kişi', evidenceContext: 'Kanıt bağlamı', humanAnswer: 'İnsan yanıtı',
    publishedContext: 'Yayınlanan NSosyal gönderisi',
    evidenceHeading: 'Kaynak aslında ne söylüyor?', boundedNote: 'Sınırlı kanıt, doğruluk puanı değil.', humanNeeded: 'Kanıt insan bağlamına ihtiyaç duyuyor',
    capacityNote: 'İsteklilik ve kalan kapasite kesin kısıtlardır.', identity: 'Firebase kimliği', resolved: 'Çözüldü', routedByNiyet: 'NIYET ile yönlendirildi',
    resolutionTitle: 'Dikkatten çözüme', stagePost: 'İhtiyaç', stagePostText: 'Yeni kullanıcı kitlesi olmadan soruyor.',
    stageEvidenceText: 'SOURCECHAIN kaynağın neyi desteklediğini gösteriyor.', stageHumanText: 'NIYET çözülmeyen kısmı istekli bir kişiye yönlendiriyor.', stageResolvedText: 'Kanıt ve insan bağlamı aynı gönderiye dönüyor.',
    whyItMatters: 'Neden önemli', proofText: 'Faydalı bir sorunun yanıt alıp almamasını erişim belirlememeli.', followersUsed: 'gerekli takipçi', systemsTogether: 'kanıt + insan katmanı', sharedOutcome: 'ortak sonuç',
    truthTitle: 'Production sınırı', truthText: 'Kimliği doğrulanmış NIYET durumu Firestore içinde saklanır. Kanıt sınırlıdır ve genel doğruluk puanı olarak sunulmaz.',
    backendDurable: 'kimlik doğrulamalı Firestore aktif', backendMemory: 'geçersiz kalıcı olmayan durum', backendDown: 'backend erişilemiyor', checking: 'Kanıt ve yönlendirme kontrol ediliyor…', pause: 'Duraklat', resume: 'Devam et',
    capacity: 'slot kaldı', active: 'yönlendirme açık', paused: 'yönlendirme kapalı', emptyInbox: 'Bu cevaplayıcı için şu anda yönlendirilmiş istek yok.',
    accept: 'Kabul et', skip: 'Geç', answer: 'Yanıt', answerPlaceholder: 'Kısa ve faydalı bir yanıt yaz.', send: 'Yanıtı gönder',
    requestOpened: 'İstek açıldı. NIYET istekli birini arıyor.', evidenceRouted: 'Kanıt kontrol edildi. Çözülmeyen kısım kaynak bağlamıyla birlikte yönlendirildi.',
    noHumanNeeded: 'Sınırlandırılmış kanıt yeterliydi; insan isteği açılmadı.', noHumanAvailable: 'İnsan bağlamı öneriliyor, ancak şu anda uygun cevaplayıcı kapasitesi yok.', noActionNeeded: 'Bu içerik için kanıt veya insan çözümü gerekmiyor.', answerSent: 'Yanıt asıl gönderiye geri ulaştı.', requestAccepted: 'İstek kabul edildi.', requestSkipped: 'İstek geçildi. Uygun başka cevaplayıcı varsa NIYET yeniden yönlendirdi.',
    routingChanged: 'Uygunluk değiştiği için NIYET bu isteği yeniden yönlendirdi. Güncel kuyruk gösteriliyor.', capacityChanged: 'Cevaplayıcı kapasitesi değişti. NIYET bekleyen istekleri yeniden hesapladı.', serviceBusy: 'Ortak durum geçici olarak kullanılamıyor. Birazdan tekrar dene.',
    restored: 'İstek bu tarayıcı oturumundan geri yüklendi.',
    networkError: 'Kimliği doğrulanmış backend erişilemiyor.', invalidState: 'Bu istek artık geri yüklenemiyor.',
    evidenceSource: 'Kaynağı aç', relation: 'İlişki', distortion: 'Sinyal', claimWording: 'Gönderi iddiası', sourceWording: 'Kaynak pasajı'
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
  if (code === 'auth_required' || error?.status === 401) return 'Sign in to continue.';
  if (['stale_assignment', 'assignment_expired', 'transaction_conflict'].includes(code)) return t('routingChanged');
  if (['capacity_exhausted', 'responder_paused'].includes(code)) return t('capacityChanged');
  if (code === 'firestore_unavailable' || error?.status === 503) return t('serviceBusy');
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

async function callApi(payload = null) {
  if (!isAuthenticated()) {
    const error = new Error('auth_required');
    error.code = 'auth_required';
    error.status = 401;
    throw error;
  }
  if (!payload) {
    const result = await getMe();
    currentProfile = result.responder_profile || null;
    fillProfileForm(currentProfile);
    const user = currentUser();
    return {
      responders: currentProfile ? [{
        id: user.uid,
        name: user.displayName || user.email || user.uid,
        remaining_slots: currentProfile.capacity_remaining,
        active: !currentProfile.paused
      }] : [],
      state_durable: true,
      state_backend: 'firestore'
    };
  }
  if (payload.action === 'open' || payload.action === 'resolve') {
    return createRequest(payload.text, { mode: payload.action === 'open' ? 'create_request' : 'resolve' });
  }
  if (payload.action === 'status') return getRequest(payload.request_id);
  if (payload.action === 'inbox') {
    const result = await getInbox();
    currentAssignments = result.assignments || [];
    return {
      requests: currentAssignments.map((assignment) => ({
        ...(assignment.request || {}),
        assignment_id: assignment.id || assignment.assignment_id,
        status: assignment.status,
        relevance: assignment.relevance
      }))
    };
  }
  const assignment = currentAssignments.find((item) => item.request_id === payload.request_id);
  const assignmentId = payload.assignment_id || assignment?.id || assignment?.assignment_id;
  if (payload.action === 'accept') return { assignment: await acceptAssignment(assignmentId) };
  if (payload.action === 'skip') return { assignment: await skipAssignment(assignmentId) };
  if (payload.action === 'answer') return { assignment: await answerAssignment(assignmentId, payload.answer) };
  if (payload.action === 'pause') return { responder_profile: await pauseResponder() };
  if (payload.action === 'resume') return { responder_profile: await resumeResponder() };
  throw new Error('invalid_action');
}

function fillProfileForm(profile) {
  if (!profile) return;
  $('#profileTopics').value = (profile.topics || []).join(', ');
  $('#profileLanguages').value = (profile.languages || ['en']).join(', ');
  $('#profileCapacity').value = String(profile.capacity_total || 1);
  $('#profileWilling').checked = Boolean(profile.willing);
  $('#profileActive').checked = Boolean(profile.active);
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
  if (responder && isAuthenticated()) {
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
  const previousResponderId = selectedResponderId;
  selectedResponderId = responders[0]?.id || null;
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
  capacity.textContent = `${record.remaining_slots} ${t('capacity')}`;
  const active = document.createElement('span');
  active.textContent = t(record.active ? 'active' : 'paused');
  target.append(capacity, active);
  $('#availabilityToggle').textContent = t(record.active ? 'pause' : 'resume');
}

function persistAuthor(request) {
  if (!request?.request_id || !currentUser()) return;
  currentAuthor = { request };
  sessionStorage.setItem('drsk-live-author', JSON.stringify({
    request_id: request.request_id,
    author_uid: currentUser().uid,
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
  if (match) {
    $('#matchedResponder').textContent = match.name || match.id;
    renderReasons(match.reason);
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
    $('#routeHuman').disabled = !isAuthenticated();
    $('#resolveEvidence').disabled = !isAuthenticated();
  }
}

async function refreshAuthor(generation = authorPollGeneration) {
  const stored = readStoredAuthor();
  if (!stored?.request_id || stored.author_uid !== currentUser()?.uid) return;
  try {
    const result = await callApi({ action: 'status', request_id: stored.request_id });
    if (generation !== authorPollGeneration) return;
    if (!result.request) return;
    currentAuthor = { request: result.request };
    $('#restoreAuthor').hidden = true;
    renderAuthorRequest(currentAuthor.request);
    if (result.request.status === 'ANSWERED') stopAuthorPoll();
  } catch (error) {
    if (generation !== authorPollGeneration) return;
    const code = errorCode(error);
    if (code === 'request_not_found') {
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
        const result = await callApi({ action: 'accept', request_id: request.request_id });
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
        await callApi({ action: 'skip', request_id: request.request_id });
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
        const result = await callApi({ action: 'answer', request_id: request.request_id, answer });
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
    const result = await callApi({ action: 'inbox' });
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
    await callApi({ action: record.active ? 'pause' : 'resume' });
    await refreshBackendAndInbox();
  } catch (error) {
    setMessage($('#inboxMessage'), friendlyError(error), true);
  } finally { button.disabled = false; }
}

function restoreAuthorButton() {
  const stored = readStoredAuthor();
  const restore = $('#restoreAuthor');
  const owned = stored?.author_uid === currentUser()?.uid;
  if (restore) restore.hidden = !owned;
  if (owned && stored?.text && !$('#requestText').value) $('#requestText').value = stored.text;
  $('#charCount').textContent = `${$('#requestText').value.length} / 1200`;
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
$('#loadScenario').addEventListener('click', () => {
  $('#requestText').value = exampleScenario[language];
  $('#charCount').textContent = `${$('#requestText').value.length} / 1200`;
  $('#requestText').focus();
});
$('#requestText').addEventListener('input', (event) => { $('#charCount').textContent = `${event.target.value.length} / 1200`; });
$('#availabilityToggle').addEventListener('click', toggleAvailability);
$('#responderProfileForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    const result = await updateResponderProfile({
      topics: $('#profileTopics').value.split(',').map((item) => item.trim()).filter(Boolean),
      languages: $('#profileLanguages').value.split(',').map((item) => item.trim()).filter(Boolean),
      capacity_total: Number($('#profileCapacity').value),
      willing: $('#profileWilling').checked,
      active: $('#profileActive').checked
    });
    currentProfile = result.responder_profile;
    fillProfileForm(currentProfile);
    setMessage($('#inboxMessage'), 'Responder profile saved.');
    await refreshBackendAndInbox(true);
  } catch (error) {
    setMessage($('#inboxMessage'), friendlyError(error), true);
  }
});

window.addEventListener('beforeunload', () => { stopAuthorPoll(); stopInboxPoll(); });

function applyAuthenticatedIdentity() {
  const user = currentUser();
  const name = user?.displayName || user?.email || user?.uid || 'Signed-in user';
  const handle = user?.email ? `@${user.email.split('@')[0]}` : '';
  $('#authorDisplayName').textContent = name;
  $('#authorHandle').textContent = handle;
  $('#requestAuthorName').textContent = name;
  $('#requestAuthorHandle').textContent = handle;
  $('#responderIdentity').textContent = name;
}

async function handleAuthChanged() {
  stopAuthorPoll();
  stopInboxPoll();
  responders = [];
  currentAssignments = [];
  selectedResponderId = null;
  responderSnapshot = '';
  inboxSnapshot = '';
  populateResponders();
  const signedIn = isAuthenticated();
  $('#routeHuman').disabled = !signedIn;
  $('#resolveEvidence').disabled = !signedIn;
  $('#responderProfileForm').querySelectorAll('input, button').forEach((node) => { node.disabled = !signedIn; });
  applyAuthenticatedIdentity();
  restoreAuthorButton();
  if (!signedIn) {
    $('#connectionBadge').dataset.state = 'error';
    $('#connectionBadge').textContent = 'authentication required';
    setMessage($('#authorMessage'), 'Sign in to create or view a NIYET request.');
    renderInbox([]);
    return;
  }
  setMessage($('#authorMessage'), '');
  const live = await checkBackend();
  if (!live) {
    setMessage($('#authorMessage'), t('networkError'), true);
    setMessage($('#inboxMessage'), t('networkError'), true);
    return;
  }
  const params = new URL(location.href).searchParams;
  if (params.get('role') === 'responder') startInboxPoll();
  const stored = readStoredAuthor();
  if (stored?.author_uid === currentUser()?.uid && params.get('role') !== 'responder') {
    $('#requestText').value = stored.text || '';
    $('#charCount').textContent = `${$('#requestText').value.length} / 1200`;
    await refreshAuthor();
    if (currentAuthor?.request) startAuthorPoll();
  }
}

(function init() {
  applyLanguage();
  updateStages(null);
  const params = new URL(location.href).searchParams;
  setRole(params.get('role') === 'responder' ? 'responder' : 'author', false);
  $('#routeHuman').disabled = true;
  $('#resolveEvidence').disabled = true;
  $('#responderProfileForm').querySelectorAll('input, button').forEach((node) => { node.disabled = true; });
  window.addEventListener('niyet-auth-changed', () => { handleAuthChanged().catch((error) => setMessage($('#authMessage'), friendlyError(error), true)); });
})();
