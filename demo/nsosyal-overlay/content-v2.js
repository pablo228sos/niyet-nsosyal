(() => {
  if (window.top !== window) return;

  const HOST_ID = 'drsk-concept-overlay-host';
  const AUTHOR_STORAGE_KEY = 'drsk-active-author-v1';
  if (document.getElementById(HOST_ID)) return;

  const EDITABLE_SELECTOR = [
    'textarea',
    'input:not([type])',
    'input[type="text"]',
    '[contenteditable]:not([contenteditable="false"])',
    '[role="textbox"]',
    '[data-lexical-editor]',
    '[data-slate-editor]',
    '.ProseMirror'
  ].join(', ');

  const state = {
    composer: null,
    lastEditable: null,
    author: null,
    inspection: null,
    pollTimer: null,
    publishTimer: null,
    positionFrame: null,
    busy: false,
    dark: false,
    language: 'en'
  };

  const copy = {
    en: {
      title: 'DRSK concept integration',
      subtitle: 'Evidence first. Human context by choice.',
      button: 'DRSK',
      empty: 'Write a post in NSosyal first.',
      checking: 'Checking bounded evidence…',
      routing: 'Finding an available, relevant person…',
      unavailable: 'DRSK backend is not reachable right now.',
      evidence: 'Evidence context',
      human: 'Human context',
      source: 'Open source',
      sourceFallback: 'Source',
      responder: 'Open responder device',
      answered: 'Human context received',
      waiting: 'Waiting for human response',
      accepted: 'Accepted. A response is being prepared.',
      evidenceEnough: 'The bounded evidence is sufficient for this path.',
      noAction: 'No factual claim to verify. No DRSK action is needed for this content.',
      noFactualClaim: 'No factual claim to verify.',
      humanContextNeeded: 'Human context is needed for this question.',
      humanRecommended: 'The evidence leaves an interpretive gap. Human context is recommended.',
      askPerson: 'Ask a relevant person',
      consent: 'Nothing is sent to a person until you press this button.',
      candidate: 'Available now',
      unavailableResponder: 'Human context is recommended, but no eligible responder has capacity right now.',
      activeRequest: 'This post already has an active human request.',
      restoreFailed: 'The previous request is no longer available. You can run a new check.',
      draftStage: 'Private check',
      publishedStage: 'Published',
      routedStage: 'Routed',
      resolvedStage: 'Resolved',
      privateInspect: 'Private draft check only. Nothing has been posted or sent to a person.',
      publishFirst: 'If you want human context, publish this text normally first. Routing unlocks only after the published post is visible.',
      publicationWaiting: 'Waiting for the published post to appear in the feed…',
      publicationMissing: 'The published post is not visible yet. Keep the panel open, then check again.',
      checkPublication: 'Find published post',
      publicationFound: 'Published NSosyal post detected',
      publicationRequired: 'Human routing is available only after the inspected text is visible as a published NSosyal post.',
      publishedContext: 'Published on NSosyal',
      postClaim: 'Post claim',
      sourcePassage: 'Source passage',
      routedTo: 'Routed to',
      resolved: 'Resolved',
      concept: 'Concept overlay · does not post to NSosyal or alter your account.'
    },
    tr: {
      title: 'DRSK kavram entegrasyonu',
      subtitle: 'Önce kanıt. İnsan bağlamı kullanıcının seçimiyle.',
      button: 'DRSK',
      empty: 'Önce NSosyal gönderi alanına bir metin yaz.',
      checking: 'Sınırlandırılmış kanıt kontrol ediliyor…',
      routing: 'Uygun ve ilgili bir kişi aranıyor…',
      unavailable: 'DRSK arka ucuna şu anda ulaşılamıyor.',
      evidence: 'Kanıt bağlamı',
      human: 'İnsan bağlamı',
      source: 'Kaynağı aç',
      sourceFallback: 'Kaynak',
      responder: 'Cevaplayıcı cihazını aç',
      answered: 'İnsan bağlamı geldi',
      waiting: 'İnsan yanıtı bekleniyor',
      accepted: 'Kabul edildi. Yanıt hazırlanıyor.',
      evidenceEnough: 'Sınırlandırılmış kanıt bu yol için yeterli.',
      noAction: 'Doğrulanacak olgusal iddia yok. Bu içerik için ek DRSK adımı gerekmiyor.',
      noFactualClaim: 'Doğrulanacak olgusal iddia yok.',
      humanContextNeeded: 'Bu soru için insan bağlamı gerekiyor.',
      humanRecommended: 'Kanıt yorumlama boşluğu bırakıyor. İnsan bağlamı öneriliyor.',
      askPerson: 'İlgili bir kişiye sor',
      consent: 'Bu düğmeye basılana kadar hiçbir kişiye istek gönderilmez.',
      candidate: 'Şu anda uygun',
      unavailableResponder: 'İnsan bağlamı öneriliyor, ancak şu anda uygun cevaplayıcı kapasitesi yok.',
      activeRequest: 'Bu gönderi için zaten etkin bir insan isteği var.',
      restoreFailed: 'Önceki istek artık kullanılamıyor. Yeni bir kontrol başlatabilirsin.',
      draftStage: 'Özel kontrol',
      publishedStage: 'Yayınlandı',
      routedStage: 'Yönlendirildi',
      resolvedStage: 'Çözüldü',
      privateInspect: 'Bu yalnızca özel taslak kontrolüdür. Hiçbir şey yayınlanmadı veya bir kişiye gönderilmedi.',
      publishFirst: 'İnsan bağlamı istiyorsan bu metni normal şekilde yayınla. Yönlendirme yalnızca yayınlanan gönderi görünür olduktan sonra açılır.',
      publicationWaiting: 'Yayınlanan gönderinin akışta görünmesi bekleniyor…',
      publicationMissing: 'Yayınlanan gönderi henüz görünmüyor. Paneli açık tutup tekrar kontrol et.',
      checkPublication: 'Yayınlanan gönderiyi bul',
      publicationFound: 'Yayınlanan NSosyal gönderisi algılandı',
      publicationRequired: 'İnsan yönlendirmesi, incelenen metin yayınlanmış bir NSosyal gönderisi olarak görünür olduktan sonra kullanılabilir.',
      publishedContext: 'NSosyal’de yayınlandı',
      postClaim: 'Gönderi iddiası',
      sourcePassage: 'Kaynak pasajı',
      routedTo: 'Yönlendirilen kişi',
      resolved: 'Çözüldü',
      concept: 'Kavram katmanı · NSosyal’de paylaşım yapmaz veya hesabını değiştirmez.'
    }
  };

  function detectLanguage() {
    const candidates = [document.documentElement.lang, navigator.language]
      .filter(Boolean)
      .map((value) => String(value).toLowerCase());
    return candidates.some((value) => value.startsWith('tr')) ? 'tr' : 'en';
  }

  state.language = detectLanguage();
  function t(key) { return copy[state.language]?.[key] || copy.en[key] || key; }

  async function api(payload) {
    try {
      const response = await chrome.runtime.sendMessage({ type: 'drsk-api', payload });
      return response || { ok: false, status: 0, error: t('unavailable') };
    } catch (error) {
      return { ok: false, status: 0, error: error?.message || t('unavailable') };
    }
  }

  function visible(node) {
    if (!(node instanceof HTMLElement)) return false;
    const style = getComputedStyle(node);
    if (style.display === 'none' || style.visibility === 'hidden' || Number(style.opacity) === 0) return false;
    const rect = node.getBoundingClientRect();
    return rect.width > 80 && rect.height > 18 && rect.bottom > 0 && rect.top < innerHeight;
  }

  function normalize(value) {
    return String(value || '').replace(/[\u200B-\u200D\uFEFF]/g, '').replace(/\s+/g, ' ').trim();
  }

  function editableText(node) {
    if (!(node instanceof HTMLElement)) return '';
    if (node instanceof HTMLTextAreaElement || node instanceof HTMLInputElement) return normalize(node.value);
    return normalize(node.innerText || node.textContent || node.getAttribute('aria-valuetext'));
  }

  function nodeHints(node) {
    return normalize([
      node.getAttribute('placeholder'),
      node.getAttribute('aria-label'),
      node.getAttribute('data-placeholder'),
      node.getAttribute('title'),
      node.id,
      typeof node.className === 'string' ? node.className : ''
    ].filter(Boolean).join(' ')).toLowerCase();
  }

  function sendLabel(node) {
    return normalize([
      node.textContent,
      node.getAttribute('aria-label'),
      node.getAttribute('title')
    ].filter(Boolean).join(' ')).toLowerCase();
  }

  function isSendAction(node) {
    if (!(node instanceof HTMLElement) || !visible(node)) return false;
    const label = sendLabel(node);
    return ['gönder', 'gonder', 'paylaş', 'paylas', 'send', 'publish', 'post', 'отправ'].some((needle) => label.includes(needle));
  }

  function findSendButtonNear(node) {
    if (!(node instanceof HTMLElement)) return null;
    const editorRect = node.getBoundingClientRect();
    let container = node.parentElement;
    for (let depth = 0; container && depth < 7; depth += 1, container = container.parentElement) {
      const buttons = [...container.querySelectorAll('button, [role="button"]')].filter(isSendAction);
      const close = buttons.find((button) => {
        const rect = button.getBoundingClientRect();
        return Math.abs(rect.top - editorRect.bottom) < 280 && rect.left > editorRect.left - 80;
      });
      if (close) return close;
    }
    return null;
  }

  function candidateFromTarget(target) {
    if (!(target instanceof HTMLElement)) return null;
    if (target.matches(EDITABLE_SELECTOR)) return target;
    const parent = target.closest(EDITABLE_SELECTOR);
    if (parent instanceof HTMLElement) return parent;
    if (target.isContentEditable) {
      let node = target;
      while (node.parentElement?.isContentEditable) node = node.parentElement;
      return node;
    }
    return null;
  }

  function scoreComposer(node) {
    const hints = nodeHints(node);
    const text = editableText(node);
    const rect = node.getBoundingClientRect();
    let score = 0;

    if (node instanceof HTMLTextAreaElement) score += 5;
    if (node instanceof HTMLInputElement) score += 1;
    if (node.isContentEditable || node.hasAttribute('contenteditable')) score += 5;
    if (node.getAttribute('role') === 'textbox') score += 3;
    if (node.matches('[data-lexical-editor], [data-slate-editor], .ProseMirror')) score += 5;
    if (text) score += Math.min(10, 4 + Math.floor(text.length / 30));

    ['post', 'gönderi', 'gonderi', 'paylaş', 'paylas', 'oluştur', 'olustur', 'share', 'create', 'what', 'созда'].forEach((needle) => {
      if (hints.includes(needle)) score += 4;
    });
    ['search', 'arama', 'ara ', 'поиск'].forEach((needle) => {
      if (hints.includes(needle)) score -= 12;
    });

    if (findSendButtonNear(node)) score += 14;
    if (rect.width > 420) score += 3;
    if (rect.top < innerHeight * 0.48) score += 2;
    if (state.lastEditable === node) score += 18;
    return score;
  }

  function editableCandidates() {
    const nodes = [...document.querySelectorAll(EDITABLE_SELECTOR)];
    if (state.lastEditable && document.contains(state.lastEditable)) nodes.unshift(state.lastEditable);
    return [...new Set(nodes)].filter((node) => node instanceof HTMLElement && !node.closest(`#${HOST_ID}`) && visible(node));
  }

  function findComposer() {
    const candidates = editableCandidates()
      .map((node) => ({ node, score: scoreComposer(node) }))
      .sort((a, b) => b.score - a.score);
    if (!candidates.length || candidates[0].score < 7) return null;
    return candidates[0].node;
  }

  function composerText() {
    const remembered = state.lastEditable && document.contains(state.lastEditable) ? state.lastEditable : null;
    const current = state.composer && document.contains(state.composer) ? state.composer : null;
    const nodes = [remembered, current, findComposer()].filter(Boolean);
    for (const node of [...new Set(nodes)]) {
      const text = editableText(node);
      if (text) {
        state.composer = node;
        return text;
      }
    }
    state.composer = findComposer();
    return state.composer ? editableText(state.composer) : '';
  }

  function sameText(left, right) {
    return normalize(left) === normalize(right);
  }

  function publishedCandidates(text) {
    const target = normalize(text);
    if (!target) return [];
    const root = document.querySelector('main') || document.body;
    const selectors = [
      'article',
      '[role="article"]',
      '[data-testid*="post" i]',
      '[class*="post" i]',
      'p',
      'div'
    ].join(', ');

    return [...root.querySelectorAll(selectors)]
      .filter((node) => {
        if (!(node instanceof HTMLElement) || node.closest(`#${HOST_ID}`) || !visible(node)) return false;
        if (node.matches(EDITABLE_SELECTOR) || node.closest(EDITABLE_SELECTOR)) return false;
        if (node.querySelector(EDITABLE_SELECTOR)) return false;
        if (state.composer && (node === state.composer || node.contains(state.composer))) return false;
        return normalize(node.innerText || node.textContent).includes(target);
      })
      .map((node) => {
        const value = normalize(node.innerText || node.textContent);
        const exact = value === target;
        const semanticContainer = node.matches('article, [role="article"], [data-testid*="post" i], [class*="post" i]');
        const excess = Math.max(0, value.length - target.length);
        const score = (exact ? 80 : 0) + (semanticContainer ? 30 : 0) - Math.min(40, excess / 20);
        return { node, score, excess };
      })
      .sort((a, b) => b.score - a.score || a.excess - b.excess);
  }

  function findPublishedPost(text) {
    return publishedCandidates(text)[0]?.node || null;
  }

  function publishedPostUrl() {
    try {
      const url = new URL(location.href);
      if (['nsosyal.com', 'www.nsosyal.com'].includes(url.hostname) && url.protocol === 'https:') {
        return url.href;
      }
    } catch (_) {}
    return null;
  }

  function parseBackground(node) {
    if (!node) return null;
    const match = getComputedStyle(node).backgroundColor.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?/);
    if (!match) return null;
    const alpha = match[4] == null ? 1 : Number(match[4]);
    if (alpha === 0) return null;
    const [r, g, b] = match.slice(1, 4).map(Number);
    return (r * 299 + g * 587 + b * 114) / 1000;
  }

  function detectTheme() {
    const bodyLuma = parseBackground(document.body);
    const rootLuma = parseBackground(document.documentElement);
    const luma = bodyLuma ?? rootLuma;
    return luma == null ? matchMedia('(prefers-color-scheme: dark)').matches : luma < 128;
  }

  function safeUrl(value) {
    try {
      const url = new URL(value);
      return ['http:', 'https:'].includes(url.protocol) ? url.href : null;
    } catch (_) {
      return null;
    }
  }

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
  }

  const host = document.createElement('drsk-concept-overlay');
  host.id = HOST_ID;
  const shadow = host.attachShadow({ mode: 'closed' });

  const stylesheet = document.createElement('link');
  stylesheet.rel = 'stylesheet';
  stylesheet.href = chrome.runtime.getURL('overlay.css');

  const publishedStylesheet = document.createElement('link');
  publishedStylesheet.rel = 'stylesheet';
  publishedStylesheet.href = chrome.runtime.getURL('published-flow.css');

  const trigger = el('button', 'drsk-overlay-trigger', t('button'));
  trigger.type = 'button';
  trigger.setAttribute('aria-label', t('title'));

  const panel = el('aside', 'drsk-overlay-panel');
  panel.setAttribute('aria-live', 'polite');
  panel.hidden = true;

  const head = el('div', 'drsk-overlay-head');
  const headCopy = el('div');
  headCopy.append(el('b', '', t('title')), el('small', '', t('subtitle')));
  const close = el('button', 'drsk-overlay-close', '×');
  close.type = 'button';
  close.setAttribute('aria-label', 'Close DRSK concept integration');
  head.append(headCopy, close);

  const body = el('div', 'drsk-overlay-body');
  const foot = el('div', 'drsk-overlay-foot', t('concept'));
  panel.append(head, body, foot);
  shadow.append(stylesheet, publishedStylesheet, trigger, panel);
  document.body.appendChild(host);

  function applyTheme() {
    state.dark = detectTheme();
    trigger.dataset.theme = state.dark ? 'dark' : 'light';
    panel.dataset.theme = state.dark ? 'dark' : 'light';
  }

  function positionTrigger() {
    applyTheme();
    const composer = findComposer();
    state.composer = composer;
    const narrow = innerWidth <= 760;

    if (!composer) {
      trigger.dataset.fallback = 'true';
      trigger.dataset.entrypoint = 'floating';
      trigger.style.removeProperty('--drsk-trigger-x');
      trigger.style.removeProperty('--drsk-trigger-y');
      trigger.style.setProperty('right', narrow ? 'auto' : '24px');
      return;
    }

    trigger.dataset.fallback = 'false';
    trigger.dataset.entrypoint = 'composer';
    trigger.style.setProperty('right', 'auto');

    const rect = composer.getBoundingClientRect();
    if (narrow) {
      // NSosyal uses a modal composer on narrow screens.  Do not compete with
      // its audience/send toolbar: keep the DRSK entrypoint in the header
      // gutter immediately above the editable field.
      const x = Math.max(12, Math.min(innerWidth - 70, rect.right - 142));
      const y = Math.max(12, Math.min(innerHeight - 48, rect.top - 38));
      trigger.style.setProperty('--drsk-trigger-x', `${Math.round(x)}px`);
      trigger.style.setProperty('--drsk-trigger-y', `${Math.round(y)}px`);
      return;
    }

    const send = findSendButtonNear(composer);
    const sendRect = send?.getBoundingClientRect();
    const x = sendRect
      ? Math.max(16, Math.min(innerWidth - 96, sendRect.left - 82))
      : Math.max(16, Math.min(innerWidth - 96, rect.right - 176));
    const y = sendRect
      ? Math.max(74, Math.min(innerHeight - 64, sendRect.top + (sendRect.height - 36) / 2))
      : Math.max(74, Math.min(innerHeight - 64, rect.bottom - 42));
    trigger.style.setProperty('--drsk-trigger-x', `${Math.round(x)}px`);
    trigger.style.setProperty('--drsk-trigger-y', `${Math.round(y)}px`);
  }

  function schedulePosition() {
    if (state.positionFrame != null) return;
    state.positionFrame = requestAnimationFrame(() => {
      state.positionFrame = null;
      if (!state.busy) positionTrigger();
    });
  }

  function setBusy(message) {
    body.replaceChildren();
    const wrap = el('div', 'drsk-overlay-loading');
    wrap.append(el('span', 'drsk-overlay-spinner'), el('p', '', message));
    body.append(wrap);
  }

  function renderLifecycle({ evidence = false, published = false, request = null } = {}) {
    const answered = Boolean(request?.answer || request?.status === 'ANSWERED');
    const routed = Boolean(request?.assigned_responder);
    const completed = answered ? 4 : routed ? 3 : published ? 2 : evidence ? 1 : 0;
    const labels = [t('draftStage'), t('publishedStage'), t('routedStage'), t('resolvedStage')];
    const wrap = el('ol', 'drsk-overlay-lifecycle');
    labels.forEach((label, index) => {
      const step = el('li', '', label);
      const position = index + 1;
      if (position < completed) step.dataset.state = 'done';
      else if (position === completed) step.dataset.state = answered ? 'done' : 'active';
      wrap.append(step);
    });
    return wrap;
  }

  function renderEvidence(context) {
    const block = el('section', 'drsk-overlay-card');
    const cardHead = el('div', 'drsk-overlay-card-head');
    cardHead.append(el('span', 'drsk-overlay-brand', 'SOURCECHAIN'), el('b', '', t('evidence')));
    block.append(cardHead);

    const items = Array.isArray(context?.evidence) ? context.evidence : [];
    if (!items.length) {
      block.append(el('p', 'drsk-overlay-muted', context?.status || 'No bounded evidence attached.'));
      return block;
    }

    items.slice(0, 2).forEach((item) => {
      const row = el('div', 'drsk-overlay-evidence');
      row.append(el('strong', '', item.source_title || item.publisher || t('sourceFallback')));
      const provenance = [item.publisher, item.publication_date].filter(Boolean).join(' · ');
      if (provenance) row.append(el('small', '', provenance));

      if (item.claim_text && item.passage) {
        const compare = el('div', 'drsk-overlay-compare');
        const claim = el('div');
        claim.append(el('small', '', t('postClaim')), el('b', '', item.claim_text));
        const source = el('div');
        source.append(el('small', '', t('sourcePassage')), el('b', '', item.passage));
        compare.append(claim, el('span', 'drsk-overlay-arrow', '↔'), source);
        row.append(compare);
      } else if (item.passage) {
        row.append(el('blockquote', '', item.passage));
      }

      const distortions = Array.isArray(item.distortions)
        ? item.distortions.filter((value) => value && value !== 'NONE')
        : [];
      const signals = [item.relation, ...distortions].filter(Boolean);
      if (signals.length) row.append(el('small', 'drsk-overlay-signal', signals.join(' · ')));

      const href = safeUrl(item.source_url);
      if (href) {
        const link = el('a', 'drsk-overlay-link', t('source'));
        link.href = href;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        row.append(link);
      }
      block.append(row);
    });
    return block;
  }

  function renderRequest(request) {
    const wrap = el('section', 'drsk-overlay-card');
    const cardHead = el('div', 'drsk-overlay-card-head');
    cardHead.append(el('span', 'drsk-overlay-brand human', 'NIYET'), el('b', '', t('human')));
    if (request?.status) cardHead.append(el('span', 'drsk-overlay-status', request.status));
    wrap.append(cardHead);

    if (request?.social_context?.published_observed) {
      const published = el('a', 'drsk-overlay-published', t('publishedContext'));
      const href = safeUrl(request.social_context.post_url);
      if (href) {
        published.href = href;
        published.target = '_blank';
        published.rel = 'noopener noreferrer';
      }
      wrap.append(published);
    }

    const responder = request?.assigned_responder;
    if (!responder) {
      wrap.append(el('p', 'drsk-overlay-muted', t('unavailableResponder')));
      return wrap;
    }

    wrap.append(el('p', 'drsk-overlay-route', `${t('routedTo')} ${responder.name || responder.id}`));
    const reasons = Array.isArray(responder.reason) ? responder.reason : [];
    if (reasons.length) wrap.append(el('small', 'drsk-overlay-muted', reasons.join(' · ')));

    const button = el('a', 'drsk-overlay-secondary', t('responder'));
    const url = new URL('https://niyet-nsosyal.vercel.app/live');
    url.searchParams.set('role', 'responder');
    url.searchParams.set('responder', responder.id);
    button.href = url.href;
    button.target = '_blank';
    button.rel = 'noopener noreferrer';
    wrap.append(button);
    return wrap;
  }

  function renderAnswer(request) {
    if (!request?.answer) return null;
    const wrap = el('section', 'drsk-overlay-answer');
    wrap.append(el('span', 'drsk-overlay-resolved', t('resolved')), el('b', '', t('answered')), el('p', '', request.answer));
    return wrap;
  }

  function renderHumanRecommendation(result, text, published = false) {
    const wrap = el('section', 'drsk-overlay-card drsk-overlay-recommendation');
    const cardHead = el('div', 'drsk-overlay-card-head');
    cardHead.append(el('span', 'drsk-overlay-brand human', 'NIYET'), el('b', '', t('human')));
    const recommendation = result?.check_worthy === false
      ? t('humanContextNeeded')
      : t('humanRecommended');
    wrap.append(cardHead, el('p', 'drsk-overlay-route', recommendation));

    if (!result?.human_available) {
      wrap.append(el('p', 'drsk-overlay-capacity', t('unavailableResponder')));
      return wrap;
    }

    if (!published) {
      const message = state.inspection?.publishing
        ? t('publicationWaiting')
        : state.inspection?.publicationMissing
          ? t('publicationMissing')
          : t('publishFirst');
      wrap.append(el('p', 'drsk-overlay-publish-gate', message));
      const check = el('button', 'drsk-overlay-secondary', t('checkPublication'));
      check.type = 'button';
      check.addEventListener('click', () => confirmPublishedPost(text, true));
      wrap.append(check);
      return wrap;
    }

    const preview = result.routing_preview;
    if (preview?.name || preview?.id) {
      wrap.append(el('small', 'drsk-overlay-candidate', `${t('candidate')}: ${preview.name || preview.id}`));
    }
    const button = el('button', 'drsk-overlay-primary', t('askPerson'));
    button.type = 'button';
    button.addEventListener('click', () => escalateToHuman(text));
    wrap.append(button, el('small', 'drsk-overlay-consent', t('consent')));
    return wrap;
  }

  function renderResult(result, text = '', options = {}) {
    body.replaceChildren();
    const request = result?.request || null;
    const evidence = result?.evidence_context || request?.evidence_context;
    const published = Boolean(
      options.published
      || request?.social_context?.published_observed
      || (state.inspection && sameText(state.inspection.text, text) && state.inspection.published)
    );
    body.append(renderLifecycle({ evidence: Boolean(evidence), published, request }));
    if (!published && !request) {
      body.append(el('p', 'drsk-overlay-private-note', t('privateInspect')));
    }
    if (evidence) body.append(renderEvidence(evidence));
    else if (result?.check_worthy === false && result?.human_recommended) {
      body.append(el('p', 'drsk-overlay-empty', t('noFactualClaim')));
    }

    if (!request) {
      if (result?.human_recommended) {
        body.append(renderHumanRecommendation(result, text, published));
      } else if (result?.resolution?.path === 'NONE') {
        body.append(el('p', 'drsk-overlay-empty', t('noAction')));
      } else {
        body.append(el('p', 'drsk-overlay-sufficient', t('evidenceEnough')));
      }
      return;
    }

    body.append(renderRequest(request));
    const answer = renderAnswer(request);
    if (answer) body.append(answer);
    else if (request.assigned_responder) {
      const message = request.status === 'ACCEPTED' ? t('accepted') : t('waiting');
      body.append(el('p', 'drsk-overlay-waiting', message));
    }
  }

  function stopPublicationWatch() {
    if (state.publishTimer) clearTimeout(state.publishTimer);
    state.publishTimer = null;
  }

  function confirmPublishedPost(text, manual = false) {
    const inspection = state.inspection;
    if (!inspection || !sameText(inspection.text, text)) return false;
    const post = findPublishedPost(text);
    const postUrl = publishedPostUrl();
    if (!post || !postUrl) {
      if (manual) {
        inspection.publishing = false;
        inspection.publicationMissing = true;
        renderResult(inspection.result, inspection.text, { published: false });
      }
      return false;
    }

    stopPublicationWatch();
    inspection.published = true;
    inspection.publishing = false;
    inspection.publicationMissing = false;
    inspection.postUrl = postUrl;
    inspection.post = post;
    renderResult(inspection.result, inspection.text, { published: true });
    const found = el('p', 'drsk-overlay-published-confirmation', t('publicationFound'));
    body.insertBefore(found, body.children[1] || null);
    return true;
  }

  function watchForPublishedPost(text, attempts = 20) {
    stopPublicationWatch();
    const tick = () => {
      state.publishTimer = null;
      if (confirmPublishedPost(text)) return;
      if (attempts <= 1 || !state.inspection || !sameText(state.inspection.text, text)) {
        if (state.inspection && sameText(state.inspection.text, text)) {
          state.inspection.publishing = false;
          state.inspection.publicationMissing = true;
          renderResult(state.inspection.result, text, { published: false });
        }
        return;
      }
      attempts -= 1;
      state.publishTimer = setTimeout(tick, 650);
    };
    state.publishTimer = setTimeout(tick, 450);
  }

  function stopPoll() {
    if (state.pollTimer) clearTimeout(state.pollTimer);
    state.pollTimer = null;
  }

  async function storeAuthor(request, text = '') {
    const token = request?.author_token || state.author?.author_token;
    if (!request?.request_id || !token) return false;
    const value = {
      request_id: request.request_id,
      author_token: token,
      text: text || state.author?.text || request.text || '',
      status: request.status || state.author?.status || 'OPEN'
    };
    state.author = value;
    await chrome.storage.session.set({ [AUTHOR_STORAGE_KEY]: value });
    return true;
  }

  async function loadAuthor() {
    try {
      const stored = await chrome.storage.session.get(AUTHOR_STORAGE_KEY);
      const value = stored?.[AUTHOR_STORAGE_KEY];
      if (!value?.request_id || !value?.author_token) return null;
      return value;
    } catch (_) {
      return null;
    }
  }

  async function clearAuthor() {
    stopPoll();
    state.author = null;
    try { await chrome.storage.session.remove(AUTHOR_STORAGE_KEY); } catch (_) {}
  }

  async function refreshAuthor() {
    const author = state.author;
    if (!author?.request_id || !author?.author_token) return false;
    const response = await api({
      action: 'status',
      request_id: author.request_id,
      author_token: author.author_token
    });
    if (!response?.ok || !response.data?.request) {
      if ([403, 404].includes(response?.status)) {
        await clearAuthor();
        if (!panel.hidden) body.replaceChildren(el('p', 'drsk-overlay-error', t('restoreFailed')));
      }
      return false;
    }

    const latest = { ...response.data.request, author_token: author.author_token };
    await storeAuthor(latest, author.text);
    renderResult({ request: latest, evidence_context: latest.evidence_context }, author.text);
    return latest.status !== 'ANSWERED';
  }

  async function pollAuthor() {
    state.pollTimer = null;
    const keepPolling = await refreshAuthor();
    if (keepPolling && state.author) {
      state.pollTimer = setTimeout(pollAuthor, 2200);
    }
  }

  async function startPoll(request, text = '') {
    stopPoll();
    if (!(await storeAuthor(request, text))) return;
    if (request.status === 'ANSWERED') return;
    state.pollTimer = setTimeout(pollAuthor, 2200);
  }

  async function escalateToHuman(text) {
    if (state.busy) return;
    const inspection = state.inspection;
    if (!inspection?.published || !sameText(inspection.text, text) || !inspection.postUrl) {
      body.append(el('p', 'drsk-overlay-error', t('publicationRequired')));
      return;
    }
    state.busy = true;
    trigger.disabled = true;
    setBusy(t('routing'));
    const response = await api({ action: 'resolve', text, post_url: inspection.postUrl });
    state.busy = false;
    trigger.disabled = false;

    if (!response?.ok) {
      body.replaceChildren(el('p', 'drsk-overlay-error', response?.error || t('unavailable')));
      return;
    }

    renderResult(response.data || {}, text, { published: true });
    if (response.data?.request) await startPoll(response.data.request, text);
  }

  async function resolveCurrentPost() {
    if (state.busy) return;
    const text = composerText();
    panel.hidden = false;
    if (!text) {
      body.replaceChildren(el('p', 'drsk-overlay-empty', t('empty')));
      return;
    }

    if (state.author) {
      const sameText = normalize(state.author.text) === normalize(text);
      if (state.author.status !== 'ANSWERED' || sameText) {
        const restored = await refreshAuthor();
        if (state.author && state.author.status !== 'ANSWERED') {
          body.prepend(el('p', 'drsk-overlay-active', t('activeRequest')));
          if (restored && !state.pollTimer) state.pollTimer = setTimeout(pollAuthor, 2200);
        }
        return;
      }
      await clearAuthor();
    }

    state.busy = true;
    trigger.disabled = true;
    setBusy(t('checking'));
    const response = await api({ action: 'inspect', text });
    state.busy = false;
    trigger.disabled = false;

    if (!response?.ok) {
      body.replaceChildren(el('p', 'drsk-overlay-error', response?.error || t('unavailable')));
      return;
    }

    state.inspection = {
      text,
      result: response.data || {},
      published: false,
      publishing: false,
      publicationMissing: false,
      postUrl: null,
      post: null
    };
    renderResult(response.data || {}, text, { published: false });
  }

  document.addEventListener('focusin', (event) => {
    const editable = candidateFromTarget(event.target);
    if (editable && !editable.closest(`#${HOST_ID}`)) {
      state.lastEditable = editable;
      state.composer = editable;
      schedulePosition();
    }
  }, true);

  document.addEventListener('input', (event) => {
    const editable = candidateFromTarget(event.target);
    if (editable && !editable.closest(`#${HOST_ID}`)) {
      state.lastEditable = editable;
      state.composer = editable;
    }
    schedulePosition();
  }, true);

  document.addEventListener('click', (event) => {
    const action = event.target instanceof Element
      ? event.target.closest('button, [role="button"]')
      : null;
    if (!action || !isSendAction(action) || !state.inspection) return;
    const text = composerText();
    if (!text || !sameText(state.inspection.text, text)) return;
    state.inspection.publishing = true;
    state.inspection.publicationMissing = false;
    panel.hidden = false;
    renderResult(state.inspection.result, text, { published: false });
    watchForPublishedPost(text);
  }, true);

  trigger.addEventListener('click', resolveCurrentPost);
  close.addEventListener('click', () => {
    panel.hidden = true;
    trigger.focus({ preventScroll: true });
  });

  const observer = new MutationObserver(schedulePosition);
  observer.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ['class', 'style', 'contenteditable', 'placeholder', 'aria-label', 'role']
  });

  addEventListener('resize', schedulePosition, { passive: true });
  addEventListener('scroll', schedulePosition, { passive: true, capture: true });
  matchMedia('(prefers-color-scheme: dark)').addEventListener?.('change', schedulePosition);
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
      schedulePosition();
      if (state.author && !state.pollTimer) pollAuthor();
    }
  });

  async function resumeStoredAuthor() {
    const stored = await loadAuthor();
    if (!stored) return;
    state.author = stored;
    const keepPolling = await refreshAuthor();
    if (keepPolling && state.author) state.pollTimer = setTimeout(pollAuthor, 2200);
  }

  positionTrigger();
  resumeStoredAuthor();
})();
