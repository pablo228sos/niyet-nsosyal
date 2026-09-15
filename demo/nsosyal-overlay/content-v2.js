(() => {
  if (window.top !== window) return;

  const HOST_ID = 'drsk-concept-overlay-host';
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
    pollTimer: null,
    positionFrame: null,
    busy: false,
    dark: false
  };

  const strings = {
    title: 'DRSK concept integration',
    subtitle: 'Evidence when enough. Human context when needed.',
    button: 'DRSK',
    empty: 'Write a post in NSosyal first.',
    checking: 'Checking bounded evidence…',
    unavailable: 'DRSK backend is not reachable right now.',
    evidence: 'Evidence context',
    human: 'Human routing',
    source: 'Open source',
    responder: 'Open responder device',
    answered: 'Human context received',
    waiting: 'Waiting for human response',
    sufficient: 'Evidence was sufficient for this path.',
    unavailableResponder: 'No eligible responder is available right now.',
    concept: 'Concept overlay · does not post to NSosyal or alter your account.'
  };

  async function api(payload) {
    try {
      const response = await chrome.runtime.sendMessage({ type: 'drsk-api', payload });
      return response || { ok: false, status: 0, error: strings.unavailable };
    } catch (error) {
      return { ok: false, status: 0, error: error?.message || strings.unavailable };
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

  const trigger = el('button', 'drsk-overlay-trigger', strings.button);
  trigger.type = 'button';
  trigger.setAttribute('aria-label', 'Open DRSK concept integration');

  const panel = el('aside', 'drsk-overlay-panel');
  panel.setAttribute('aria-live', 'polite');
  panel.hidden = true;

  const head = el('div', 'drsk-overlay-head');
  const headCopy = el('div');
  headCopy.append(el('b', '', strings.title), el('small', '', strings.subtitle));
  const close = el('button', 'drsk-overlay-close', '×');
  close.type = 'button';
  close.setAttribute('aria-label', 'Close DRSK concept integration');
  head.append(headCopy, close);

  const body = el('div', 'drsk-overlay-body');
  const foot = el('div', 'drsk-overlay-foot', strings.concept);
  panel.append(head, body, foot);
  shadow.append(stylesheet, trigger, panel);
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

    if (!composer) {
      trigger.dataset.fallback = 'true';
      trigger.style.removeProperty('--drsk-trigger-x');
      trigger.style.removeProperty('--drsk-trigger-y');
      trigger.style.setProperty('right', '24px');
      return;
    }

    trigger.dataset.fallback = 'false';
    trigger.style.setProperty('right', 'auto');
    const send = findSendButtonNear(composer);
    const rect = composer.getBoundingClientRect();
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

  function renderEvidence(context) {
    const block = el('section', 'drsk-overlay-card');
    const cardHead = el('div', 'drsk-overlay-card-head');
    cardHead.append(el('span', 'drsk-overlay-brand', 'SOURCECHAIN'), el('b', '', strings.evidence));
    block.append(cardHead);

    const items = Array.isArray(context?.evidence) ? context.evidence : [];
    if (!items.length) {
      block.append(el('p', 'drsk-overlay-muted', context?.status || 'No bounded evidence attached.'));
      return block;
    }

    items.slice(0, 2).forEach((item) => {
      const row = el('div', 'drsk-overlay-evidence');
      row.append(el('strong', '', item.source_title || item.publisher || 'Source'));
      const provenance = [item.publisher, item.publication_date].filter(Boolean).join(' · ');
      if (provenance) row.append(el('small', '', provenance));

      if (item.claim_text && item.passage) {
        const compare = el('div', 'drsk-overlay-compare');
        const claim = el('div');
        claim.append(el('small', '', 'Post claim'), el('b', '', item.claim_text));
        const source = el('div');
        source.append(el('small', '', 'Source passage'), el('b', '', item.passage));
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
        const link = el('a', 'drsk-overlay-link', strings.source);
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
    cardHead.append(el('span', 'drsk-overlay-brand human', 'NIYET'), el('b', '', strings.human));
    if (request?.status) cardHead.append(el('span', 'drsk-overlay-status', request.status));
    wrap.append(cardHead);

    const responder = request?.assigned_responder;
    if (!responder) {
      wrap.append(el('p', 'drsk-overlay-muted', strings.unavailableResponder));
      return wrap;
    }

    wrap.append(el('p', 'drsk-overlay-route', `Routed to ${responder.name || responder.id}`));
    const reasons = Array.isArray(responder.reason) ? responder.reason : [];
    if (reasons.length) wrap.append(el('small', 'drsk-overlay-muted', reasons.join(' · ')));

    const button = el('a', 'drsk-overlay-secondary', strings.responder);
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
    wrap.append(el('span', 'drsk-overlay-resolved', 'Resolved'), el('b', '', strings.answered), el('p', '', request.answer));
    return wrap;
  }

  function renderResult(result) {
    body.replaceChildren();
    const request = result?.request || null;
    const evidence = result?.evidence_context || request?.evidence_context;
    if (evidence) body.append(renderEvidence(evidence));

    if (!request) {
      body.append(el('p', 'drsk-overlay-sufficient', strings.sufficient));
      return;
    }

    body.append(renderRequest(request));
    const answer = renderAnswer(request);
    if (answer) body.append(answer);
    else if (request.assigned_responder) body.append(el('p', 'drsk-overlay-waiting', strings.waiting));
  }

  function stopPoll() {
    if (state.pollTimer) clearInterval(state.pollTimer);
    state.pollTimer = null;
  }

  function startPoll(request) {
    stopPoll();
    const requestId = request?.request_id;
    const token = request?.author_token;
    if (!requestId || !token) return;

    state.author = { request_id: requestId, author_token: token };
    state.pollTimer = setInterval(async () => {
      const response = await api({ action: 'status', request_id: requestId, author_token: token });
      if (!response?.ok || !response.data?.request) return;
      const latest = response.data.request;
      renderResult({ request: latest, evidence_context: latest.evidence_context });
      if (latest.status === 'ANSWERED') stopPoll();
    }, 2200);
  }

  async function resolveCurrentPost() {
    if (state.busy) return;
    const text = composerText();
    panel.hidden = false;
    if (!text) {
      body.replaceChildren(el('p', 'drsk-overlay-empty', strings.empty));
      return;
    }

    state.busy = true;
    trigger.disabled = true;
    setBusy(strings.checking);
    const response = await api({ action: 'resolve', text });
    state.busy = false;
    trigger.disabled = false;

    if (!response?.ok) {
      body.replaceChildren(el('p', 'drsk-overlay-error', response?.error || strings.unavailable));
      return;
    }

    renderResult(response.data || {});
    if (response.data?.request) startPoll(response.data.request);
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
    if (!document.hidden) schedulePosition();
  });

  positionTrigger();
})();
