(() => {
  if (window.top !== window || document.documentElement.dataset.drskOverlayMounted === '1') return;
  document.documentElement.dataset.drskOverlayMounted = '1';

  const state = {
    composer: null,
    author: null,
    pollTimer: null,
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
    concept: 'Concept overlay · does not post to NSosyal or alter your account.'
  };

  function api(payload = null) {
    return new Promise((resolve) => chrome.runtime.sendMessage({ type: 'drsk-api', payload }, resolve));
  }

  function visible(node) {
    if (!(node instanceof HTMLElement)) return false;
    const style = getComputedStyle(node);
    if (style.display === 'none' || style.visibility === 'hidden' || Number(style.opacity) === 0) return false;
    const rect = node.getBoundingClientRect();
    return rect.width > 120 && rect.height > 20 && rect.bottom > 0 && rect.top < innerHeight;
  }

  function scoreComposer(node) {
    const text = [
      node.getAttribute('placeholder'),
      node.getAttribute('aria-label'),
      node.getAttribute('data-placeholder'),
      node.textContent
    ].filter(Boolean).join(' ').toLowerCase();
    let score = node.matches('textarea') ? 4 : 1;
    if (node.matches('[contenteditable="true"]')) score += 3;
    ['post', 'gönder', 'paylaş', 'созда', 'share', 'what'].forEach((needle) => {
      if (text.includes(needle)) score += 5;
    });
    const rect = node.getBoundingClientRect();
    if (rect.width > 350) score += 2;
    if (rect.top < innerHeight * 0.55) score += 2;
    return score;
  }

  function findComposer() {
    const candidates = [...document.querySelectorAll('textarea, [contenteditable="true"], [role="textbox"]')]
      .filter(visible)
      .map((node) => ({ node, score: scoreComposer(node) }))
      .sort((a, b) => b.score - a.score);
    return candidates[0]?.node || null;
  }

  function composerText() {
    const node = state.composer && document.contains(state.composer) ? state.composer : findComposer();
    state.composer = node;
    if (!node) return '';
    return ('value' in node ? node.value : node.innerText || node.textContent || '').trim();
  }

  function detectTheme() {
    const bg = getComputedStyle(document.body).backgroundColor;
    const match = bg.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
    if (!match) return matchMedia('(prefers-color-scheme: dark)').matches;
    const [r, g, b] = match.slice(1).map(Number);
    return ((r * 299 + g * 587 + b * 114) / 1000) < 128;
  }

  function safeUrl(value) {
    try {
      const url = new URL(value);
      return ['http:', 'https:'].includes(url.protocol) ? url.href : null;
    } catch (_) { return null; }
  }

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
  }

  const trigger = el('button', 'drsk-overlay-trigger', strings.button);
  trigger.type = 'button';
  trigger.setAttribute('aria-label', 'Open DRSK concept integration');

  const panel = el('aside', 'drsk-overlay-panel');
  panel.setAttribute('aria-live', 'polite');
  panel.hidden = true;
  panel.innerHTML = `
    <div class="drsk-overlay-head">
      <div><b>${strings.title}</b><small>${strings.subtitle}</small></div>
      <button class="drsk-overlay-close" type="button" aria-label="Close">×</button>
    </div>
    <div class="drsk-overlay-body"></div>
    <div class="drsk-overlay-foot">${strings.concept}</div>
  `;

  document.documentElement.append(trigger, panel);
  const body = panel.querySelector('.drsk-overlay-body');
  const close = panel.querySelector('.drsk-overlay-close');

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
      return;
    }
    trigger.dataset.fallback = 'false';
    const rect = composer.getBoundingClientRect();
    const x = Math.max(16, Math.min(innerWidth - 96, rect.right - 86));
    const y = Math.max(82, Math.min(innerHeight - 64, rect.bottom - 44));
    trigger.style.setProperty('--drsk-trigger-x', `${x}px`);
    trigger.style.setProperty('--drsk-trigger-y', `${y}px`);
  }

  function setBusy(message) {
    body.replaceChildren();
    const wrap = el('div', 'drsk-overlay-loading');
    wrap.append(el('span', 'drsk-overlay-spinner'), el('p', '', message));
    body.append(wrap);
  }

  function renderEvidence(context) {
    const block = el('section', 'drsk-overlay-card');
    const head = el('div', 'drsk-overlay-card-head');
    head.append(el('span', 'drsk-overlay-brand', 'SOURCECHAIN'), el('b', '', strings.evidence));
    block.append(head);

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

      const signals = [item.relation, ...(Array.isArray(item.distortions) ? item.distortions.filter((x) => x && x !== 'NONE') : [])];
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
    const head = el('div', 'drsk-overlay-card-head');
    head.append(el('span', 'drsk-overlay-brand human', 'NIYET'), el('b', '', strings.human));
    wrap.append(head);

    const responder = request.assigned_responder;
    if (responder) {
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
    } else {
      wrap.append(el('p', 'drsk-overlay-muted', 'No eligible responder is available right now.'));
    }
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
    const evidence = result.evidence_context || result.request?.evidence_context;
    if (evidence) body.append(renderEvidence(evidence));
    if (result.request) {
      body.append(renderRequest(result.request));
      const answer = renderAnswer(result.request);
      if (answer) body.append(answer);
      else body.append(el('p', 'drsk-overlay-waiting', strings.waiting));
    } else {
      body.append(el('p', 'drsk-overlay-sufficient', strings.sufficient));
    }
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
      renderResult({ request: response.data.request, evidence_context: response.data.request.evidence_context });
      if (response.data.request.status === 'ANSWERED') stopPoll();
    }, 2500);
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
    setBusy(strings.checking);
    const response = await api({ action: 'resolve', text });
    state.busy = false;
    if (!response?.ok) {
      body.replaceChildren(el('p', 'drsk-overlay-error', response?.error || strings.unavailable));
      return;
    }
    renderResult(response.data || {});
    if (response.data?.request) startPoll(response.data.request);
  }

  trigger.addEventListener('click', resolveCurrentPost);
  close.addEventListener('click', () => { panel.hidden = true; });

  const observer = new MutationObserver(() => {
    if (!state.busy) positionTrigger();
  });
  observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['class', 'style'] });

  addEventListener('resize', positionTrigger, { passive: true });
  addEventListener('scroll', positionTrigger, { passive: true, capture: true });
  matchMedia('(prefers-color-scheme: dark)').addEventListener?.('change', applyTheme);
  positionTrigger();
})();
