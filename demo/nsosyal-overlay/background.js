const API_URL = 'https://niyet-nsosyal.vercel.app/api/human-help';
const ALLOWED_ACTIONS = new Set(['resolve', 'status']);
const NSOSYAL_HOSTS = new Set(['nsosyal.com', 'www.nsosyal.com']);

function trustedSender(sender) {
  try {
    const raw = sender?.url || sender?.tab?.url || '';
    const url = new URL(raw);
    return url.protocol === 'https:' && NSOSYAL_HOSTS.has(url.hostname);
  } catch (_) {
    return false;
  }
}

function validatePayload(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return { ok: false, error: 'invalid_payload' };
  }

  const action = value.action;
  if (!ALLOWED_ACTIONS.has(action)) {
    return { ok: false, error: 'unsupported_action' };
  }

  if (action === 'resolve') {
    if (typeof value.text !== 'string') return { ok: false, error: 'text_required' };
    const text = value.text.trim();
    if (!text || text.length > 1200) return { ok: false, error: 'invalid_text_length' };
    return { ok: true, payload: { action, text } };
  }

  if (action === 'status') {
    if (typeof value.request_id !== 'string' || !value.request_id || value.request_id.length > 128) {
      return { ok: false, error: 'invalid_request_id' };
    }
    if (typeof value.author_token !== 'string' || !value.author_token || value.author_token.length > 256) {
      return { ok: false, error: 'invalid_author_token' };
    }
    return {
      ok: true,
      payload: {
        action,
        request_id: value.request_id,
        author_token: value.author_token
      }
    };
  }

  return { ok: false, error: 'unsupported_action' };
}

async function requestApi(payload) {
  const response = await fetch(API_URL, {
    method: 'POST',
    headers: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload),
    credentials: 'omit',
    cache: 'no-store',
    redirect: 'error'
  });

  let data = {};
  try { data = await response.json(); } catch (_) {}

  if (!response.ok) {
    return {
      ok: false,
      status: response.status,
      error: data.error || `HTTP ${response.status}`
    };
  }

  return { ok: true, status: response.status, data };
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type !== 'drsk-api') return false;

  if (!trustedSender(sender)) {
    sendResponse({ ok: false, status: 403, error: 'untrusted_sender' });
    return false;
  }

  const validated = validatePayload(message.payload);
  if (!validated.ok) {
    sendResponse({ ok: false, status: 400, error: validated.error });
    return false;
  }

  requestApi(validated.payload)
    .then(sendResponse)
    .catch((error) => sendResponse({
      ok: false,
      status: 0,
      error: error?.message || 'backend unavailable'
    }));

  return true;
});
