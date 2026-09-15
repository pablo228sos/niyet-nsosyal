(() => {
  const $ = (selector, root = document) => root.querySelector(selector);

  const pendingCopy = {
    en: {
      resolve: 'Checking available evidence…',
      open: 'Finding someone who can help…',
      accept: 'Accepting request…',
      skip: 'Finding another match…',
      answer: 'Sending answer…',
      availability: 'Updating availability…'
    },
    tr: {
      resolve: 'Mevcut kanıt kontrol ediliyor…',
      open: 'Yardımcı olabilecek biri bulunuyor…',
      accept: 'İstek kabul ediliyor…',
      skip: 'Başka bir eşleşme aranıyor…',
      answer: 'Yanıt gönderiliyor…',
      availability: 'Uygunluk güncelleniyor…'
    }
  };

  function language() {
    return document.documentElement.lang === 'tr' ? 'tr' : 'en';
  }

  function copy(key) {
    return pendingCopy[language()][key] || pendingCopy.en[key] || '';
  }

  function setPendingMessage(target, key) {
    if (!target) return;
    target.textContent = copy(key);
    target.classList.remove('error');
  }

  function clearBusyWhenReady(button, container) {
    if (!button || !container) return;

    button.setAttribute('aria-busy', 'true');
    container.setAttribute('aria-busy', 'true');
    container.classList.add('is-pending');

    const observer = new MutationObserver(() => {
      if (!button.isConnected || !button.disabled) {
        button.removeAttribute('aria-busy');
        container.removeAttribute('aria-busy');
        container.classList.remove('is-pending');
        observer.disconnect();
      }
    });

    observer.observe(button, { attributes: true, attributeFilter: ['disabled'] });

    // Successful inbox actions usually replace the whole card before the
    // triggering button is re-enabled. Remove stale busy semantics then too.
    const parent = container.parentElement;
    if (parent) {
      const removalObserver = new MutationObserver(() => {
        if (!container.isConnected) {
          observer.disconnect();
          removalObserver.disconnect();
        }
      });
      removalObserver.observe(parent, { childList: true });
    }
  }

  function markAuthorPending(button, mode) {
    const view = $('#authorView');
    const message = $('#authorMessage');
    if (!view || !button || !button.disabled) return;
    setPendingMessage(message, mode);
    clearBusyWhenReady(button, view);
  }

  function markInboxPending(button, mode) {
    const card = button?.closest('.inbox-card');
    const message = $('#inboxMessage');
    if (!card || !button.disabled) return;
    setPendingMessage(message, mode);
    clearBusyWhenReady(button, card);
  }

  document.addEventListener('click', (event) => {
    const button = event.target.closest('button');
    if (!button) return;

    if (button.id === 'resolveEvidence') {
      markAuthorPending(button, 'resolve');
      return;
    }
    if (button.id === 'routeHuman') {
      markAuthorPending(button, 'open');
      return;
    }
    if (button.id === 'availabilityToggle') {
      const profile = $('.responder-profile-card');
      if (profile && button.disabled) {
        setPendingMessage($('#inboxMessage'), 'availability');
        clearBusyWhenReady(button, profile);
      }
      return;
    }
    if (button.classList.contains('accept-request')) {
      markInboxPending(button, 'accept');
      return;
    }
    if (button.classList.contains('skip-request')) {
      markInboxPending(button, 'skip');
      return;
    }
    if (button.classList.contains('send-answer')) {
      markInboxPending(button, 'answer');
    }
  });

  const revealTargets = ['requestCard', 'evidenceBlock', 'matchBlock', 'answerBlock'];
  revealTargets.forEach((id) => {
    const node = document.getElementById(id);
    if (!node) return;
    let wasHidden = node.hidden;
    const observer = new MutationObserver(() => {
      if (wasHidden && !node.hidden) {
        node.classList.remove('state-reveal');
        // Force a new animation only when a meaningful product state appears.
        void node.offsetWidth;
        node.classList.add('state-reveal');
      }
      wasHidden = node.hidden;
    });
    observer.observe(node, { attributes: true, attributeFilter: ['hidden'] });
  });
})();
