const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

const apiCandidates = ['/api/human-help', '/api/human_help'];
const juryScenario = {
  en: 'Research proves coffee consumption causes lower mortality. Can someone explain what the study actually shows?',
  tr: 'Araştırma kahve tüketiminin daha düşük ölüm riskine neden olduğunu kanıtlıyor. Çalışmanın aslında ne gösterdiğini biri açıklayabilir mi?'
};

let apiEndpoint = sessionStorage.getItem('drsk-human-help-endpoint') || null;
let language = localStorage.getItem('drsk-live-language') || 'en';
let responders = [];
let selectedResponderId = null;
let currentAuthor = null;
let authorPoll = null;
let inboxPoll = null;
let requestBusy = false;

const copy = {
  en: {
    navFeed: 'Feed', navExplore: 'Discover', navCommunities: 'Communities', navMessages: 'Messages', navProfile: 'Profile',
    integrationNote: 'Evidence + human resolution', prototypeLabel: 'Final prototype', feedTitle: 'Feed',
    authorTab: 'New user', responderTab: 'Responder', authorSide: 'Author side', responderSide: 'Responder side',
    authorHeading: 'Ask without an audience.', responderHeading: 'Requests that match what you can help with.',
    requestLabel: 'What do you need help with?', requestPlaceholder: 'Share a question, claim or idea...', zeroFollowers: '0 followers',
    noFollowers: 'Follower count is never used as an eligibility signal.', routeHuman: 'Ask a person directly', postWithDrsk: 'Post with DRSK', loadScenario: 'Load jury scenario',
    restore: 'Restore request', routedTo: 'Routed to', copyResponder: 'Open responder device', evidenceContext: 'Evidence context', humanAnswer: 'Human answer',
    evidenceHeading: 'What does the source actually say?', boundedNote: 'Bounded evidence, not a truth score.', humanNeeded: 'Evidence needs human context',
    capacityNote: 'Willingness and remaining capacity are hard constraints.', identity: 'Demo identity', resolved: 'Resolved', routedByNiyet: 'Routed by NIYET',
    resolutionTitle: 'From attention to resolution', stagePost: 'Need', stagePostText: 'A new user asks without an audience.',
    stageEvidenceText: 'SOURCECHAIN exposes what the source supports.', stageHumanText: 'NIYET routes the unresolved part to a willing person.', stageResolvedText: 'Evidence and human context return to the same post.',
    whyItMatters: 'Why it matters', proofText: 'Reach should not decide whether a useful question gets an answer.', followersUsed: 'followers required', systemsTogether: 'evidence + human layers', sharedOutcome: 'shared outcome',
    truthTitle: 'Prototype boundary', truthText: 'Controlled evidence corpus and server-process demo state. No generic truth score, no hidden psychological profiling.',
    backendLive: 'shared backend live', backendDown: 'backend unavailable', checking: 'checking backend', pause: 'Pause', resume: 'Resume',
    capacity: 'slots remaining', active: 'routing on', paused: 'routing paused', emptyInbox: 'No routed requests for this responder right now.',
    accept: 'Accept', skip: 'Skip', answer: 'Answer', answerPlaceholder: 'Give the person a concise, useful answer.', send: 'Send answer',
    requestOpened: 'Request opened. NIYET is looking for a willing person.', evidenceRouted: 'Evidence checked. The unresolved part was routed with its source context.',
    noHumanNeeded: 'Evidence was sufficient for this path; no human request was opened.', answerSent: 'Answer sent back to the original post.', requestAccepted: 'Request accepted.', requestSkipped: 'Request skipped. NIYET reallocated it when another eligible responder existed.',
    copied: 'Responder link copied.', copyFailed: 'Copy failed. Open responder mode manually.', restored: 'Request restored from this browser session.',
    networkError: 'The shared demo backend is not reachable.', invalidState: 'This request can no longer be restored.',
    evidenceSource: 'Open source', relation: 'Relation', distortion: 'Signal', claimWording: 'Post wording', sourceWording: 'Source wording', causalityShift: 'causes / proves', association: 'associated with', resetDone: 'Demo reset.', resetConfirm: 'Reset the shared demo state for every connected device?'
  },
  tr: {
    navFeed: 'Akış', navExplore: 'Keşfet', navCommunities: 'Topluluklar', navMessages: 'Mesajlar', navProfile: 'Profil',
    integrationNote: 'Kanıt + insan çözümü', prototypeLabel: 'Final prototipi', feedTitle: 'Akış',
    authorTab: 'Yeni kullanıcı', responderTab: 'Cevaplayıcı', authorSide: 'Gönderi sahibi', responderSide: 'Cevaplayıcı tarafı',
    authorHeading: 'Takipçin olmasa da sor.', responderHeading: 'Gerçekten yardımcı olabileceğin istekler.',
    requestLabel: 'Neye ihtiyacın var?', requestPlaceholder: 'Bir soru, iddia veya fikir paylaş...', zeroFollowers: '0 takipçi',
    noFollowers: 'Takipçi sayısı hiçbir zaman uygunluk sinyali olarak kullanılmaz.', routeHuman: 'Doğrudan birine sor', postWithDrsk: 'DRSK ile paylaş', loadScenario: 'Jüri senaryosunu yükle',
    restore: 'İsteği geri yükle', routedTo: 'Yönlendirilen kişi', copyResponder: 'Cevaplayıcı cihazını aç', evidenceContext: 'Kanıt bağlamı', humanAnswer: 'İnsan yanıtı',
    evidenceHeading: 'Kaynak aslında ne söylüyor?', boundedNote: 'Sınırlı kanıt, doğruluk puanı değil.', humanNeeded: 'Kanıt insan bağlamına ihtiyaç duyuyor',
    capacityNote: 'İsteklilik ve kalan kapasite kesin kısıtlardır.', identity: 'Demo kimliği', resolved: 'Çözüldü', routedByNiyet: 'NIYET ile yönlendirildi',
    resolutionTitle: 'Dikkatten çözüme', stagePost: 'İhtiyaç', stagePostText: 'Yeni kullanıcı kitlesi olmadan soruyor.',
    stageEvidenceText: 'SOURCECHAIN kaynağın neyi desteklediğini gösteriyor.', stageHumanText: 'NIYET çözülmeyen kısmı istekli bir kişiye yönlendiriyor.', stageResolvedText: 'Kanıt ve insan bağlamı aynı gönderiye dönüyor.',
    whyItMatters: 'Neden önemli', proofText: 'Faydalı bir sorunun yanıt alıp almamasını erişim belirlememeli.', followersUsed: 'gerekli takipçi', systemsTogether: 'kanıt + insan katmanı', sharedOutcome: 'ortak sonuç',
    truthTitle: 'Prototip sınırı', truthText: 'Kontrollü kanıt derlemi ve sunucu-süreci demo durumu. Genel doğruluk puanı veya gizli psikolojik profilleme yok.',
    backendLive: 'ortak backend aktif', backendDown: 'backend erişilemiyor', checking: 'backend kontrol ediliyor', pause: 'Duraklat', resume: 'Devam et',
    capacity: 'slot kaldı', active: 'yönlendirme açık', paused: 'yönlendirme kapalı', emptyInbox: 'Bu cevaplayıcı için şu anda yönlendirilmiş istek yok.',
    accept: 'Kabul et', skip: 'Geç', answer: 'Yanıt', answerPlaceholder: 'Kısa ve faydalı bir yanıt yaz.', send: 'Yanıtı gönder',
    requestOpened: 'İstek açıldı. NIYET istekli birini arıyor.', evidenceRouted: 'Kanıt kontrol edildi. Çözülmeyen kısım kaynak bağlamıyla birlikte yönlendirildi.',
    noHumanNeeded: 'Bu yol için kanıt yeterliydi; insan isteği açılmadı.', answerSent: 'Yanıt asıl gönderiye geri ulaştı.', requestAccepted: 'İstek kabul edildi.', requestSkipped: 'İstek geçildi. Uygun başka cevaplayıcı varsa NIYET yeniden yönlendirdi.',
    copied: 'Cevaplayıcı bağlantısı kopyalandı.', copyFailed: 'Kopyalama başarısız. Cevaplayıcı modunu elle aç.', restored: 'İstek bu tarayıcı oturumundan geri yüklendi.',
    networkError: 'Ortak demo backendine ulaşılamıyor.', invalidState: 'Bu istek artık geri yüklenemiyor.',
    evidenceSource: 'Kaynağı aç', relation: 'İlişki', distortion: 'Sinyal', claimWording: 'Gönderi ifadesi', sourceWording: 'Kaynak ifadesi', causalityShift: 'neden olur / kanıtlar', association: 'ilişkili', resetDone: 'Demo sıfırlandı.', resetConfirm: 'Ortak demo durumunu bağlı tüm cihazlar için sıfırlamak istiyor musun?'
  }
};

function t(key) { return copy[language]?.[key] || copy.en[key] || key; }

function setMessage(target, message, isError = false) {
  target.textContent = message || '';
  target.classList.toggle('error', isError);
}

function safeUrl(value) {
  try {
    const url = new URL(value);
    return ['http:', 'https:'].includes(url.protocol) ? url.href : null;
  } catch (_) { return null; }
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
      if (error.status && error.status !== 404) throw error;
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
    responders = Array.isArray(data.responders) ? data.responders : [];
    badge.dataset.state = 'live';
    badge.textContent = t('backendLive');
    populateResponders();
    return true;
  } catch (_) {
    badge.dataset.state = 'error';
    badge.textContent = t('backendDown');
    return false;
  }
}

function populateResponders() {
  const select = $('#responderSelect');
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

function appendDistortionComparison(row, distortions) {
  if (!distortions.includes('CAUSALITY_SHIFT')) return;
  const compare = document.createElement('div');
  compare.className = 'wording-compare';
  const claim = document.createElement('div');
  claim.innerHTML = `<small>${t('claimWording')}</small><b>${t('causalityShift')}</b>`;
  const arrow = document.createElement('span');
  arrow.textContent = '→';
  const source = document.createElement('div');
  source.innerHTML = `<small>${t('sourceWording')}</small><b>${t('association')}</b>`;
  compare.append(claim, arrow, source);
  row.appendChild(compare);
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
    if (item.passage) {
      const quote = document.createElement('blockquote');
      quote.textContent = item.passage;
      row.appendChild(quote);
    }
    const distortions = Array.isArray(item.distortions) ? item.distortions.filter((value) => value && value !== 'NONE') : [];
    appendDistortionComparison(row, distortions);
    const signals = [];
    if (item.relation) signals.push(`${t('relation')}: ${item.relation}`);
    if (distortions.length) signals.push(`${t('distortion')}: ${distortions.join(', ')}`);
    if (signals.length) {
      const small = document.createElement('small');
      small.textContent = signals.join(' · ');
      row.appendChild(small);
    }
    const href = safeUrl(item.source_url);
    if (href && target.id === 'evidenceItems') {
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

  const match = request.assigned_responder;
  $('#matchBlock').hidden = !match;
  $('#copyResponderLink').hidden = !match;
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
      sessionStorage.removeItem('drsk-live-author');
      currentAuthor = null;
      $('#requestCard').hidden = true;
      updateStages(null);
      if (result.evidence_context) {
        const synthetic = {
          text: value,
          status: result.resolution?.path || 'EVIDENCE',
          evidence_context: result.evidence_context,
          assigned_responder: null,
          answer: null
        };
        renderAuthorRequest(synthetic);
      }
      setMessage($('#authorMessage'), t('noHumanNeeded'));
      return;
    }
    persistAuthor(result.request);
    renderAuthorRequest(result.request);
    setMessage($('#authorMessage'), t(mode === 'resolve' ? 'evidenceRouted' : 'requestOpened'));
    startAuthorPoll();
  } catch (error) {
    setMessage($('#authorMessage'), error.message || t('networkError'), true);
  } finally {
    requestBusy = false;
    $('#routeHuman').disabled = false;
    $('#resolveEvidence').disabled = false;
  }
}

async function refreshAuthor() {
  const stored = readStoredAuthor();
  if (!stored?.request_id || !stored?.author_token) return;
  try {
    const result = await callApi({ action: 'status', request_id: stored.request_id, author_token: stored.author_token });
    if (!result.request) return;
    currentAuthor = { request: { ...result.request, author_token: stored.author_token } };
    renderAuthorRequest(currentAuthor.request);
    if (result.request.status === 'ANSWERED') stopAuthorPoll();
  } catch (error) {
    if (error.message === 'request_not_found' || error.message === 'invalid_author_token') {
      stopAuthorPoll();
      sessionStorage.removeItem('drsk-live-author');
      $('#restoreAuthor').hidden = true;
      setMessage($('#authorMessage'), t('invalidState'), true);
      return;
    }
    setMessage($('#authorMessage'), error.message || t('networkError'), true);
  }
}

function startAuthorPoll() {
  stopAuthorPoll();
  refreshAuthor();
  authorPoll = window.setInterval(refreshAuthor, 1200);
}
function stopAuthorPoll() { if (authorPoll) clearInterval(authorPoll); authorPoll = null; }

function responderLink() {
  const match = currentAuthor?.request?.assigned_responder;
  if (!match?.id) return null;
  const url = new URL(location.href);
  url.searchParams.set('role', 'responder');
  url.searchParams.set('responder', match.id);
  return url.href;
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
  wrap.appendChild(title);
  renderEvidence(context, wrap);
  return wrap;
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
        setMessage($('#inboxMessage'), error.message, true);
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
        setMessage($('#inboxMessage'), error.message, true);
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
        setMessage($('#inboxMessage'), error.message, true);
        send.disabled = false;
      }
    });

    inbox.appendChild(card);
  });
}

async function refreshInbox() {
  if (!selectedResponderId) return;
  try {
    const result = await callApi({ action: 'inbox', responder_id: selectedResponderId });
    renderInbox(Array.isArray(result.requests) ? result.requests : []);
  } catch (error) {
    setMessage($('#inboxMessage'), error.message || t('networkError'), true);
  }
}

async function refreshBackendAndInbox() {
  await checkBackend();
  await refreshInbox();
}

function startInboxPoll() {
  stopInboxPoll();
  refreshBackendAndInbox();
  inboxPoll = window.setInterval(refreshBackendAndInbox, 1300);
}
function stopInboxPoll() { if (inboxPoll) clearInterval(inboxPoll); inboxPoll = null; }

async function toggleAvailability() {
  const record = responderRecord();
  if (!record) return;
  const button = $('#availabilityToggle');
  button.disabled = true;
  try {
    await callApi({ action: record.active ? 'pause' : 'resume', responder_id: record.id });
    await refreshBackendAndInbox();
  } catch (error) {
    setMessage($('#inboxMessage'), error.message || t('networkError'), true);
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
  catch (error) { setMessage($('#authorMessage'), error.message || t('networkError'), true); return; }
  sessionStorage.removeItem('drsk-live-author');
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
  if (!$('#responderView').hidden) refreshInbox();
});
$('#authorTab').addEventListener('click', () => setRole('author'));
$('#responderTab').addEventListener('click', () => setRole('responder'));
$('#routeHuman').addEventListener('click', () => openAuthorRequest('open'));
$('#resolveEvidence').addEventListener('click', () => openAuthorRequest('resolve'));
$('#copyResponderLink').addEventListener('click', copyResponderLink);
$('#loadScenario').addEventListener('click', () => {
  $('#requestText').value = juryScenario[language];
  $('#charCount').textContent = `${$('#requestText').value.length} / 1200`;
  $('#requestText').focus();
});
$('#resetDemo').addEventListener('click', resetDemo);
$('#requestText').addEventListener('input', (event) => { $('#charCount').textContent = `${event.target.value.length} / 1200`; });
$('#responderSelect').addEventListener('change', () => {
  selectedResponderId = $('#responderSelect').value;
  const url = new URL(location.href);
  url.searchParams.set('responder', selectedResponderId);
  history.replaceState(null, '', url);
  renderResponderMeta();
  refreshInbox();
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
