const API_URLS = [
  'https://niyet-nsosyal.vercel.app/api/human_help',
  'https://niyet-nsosyal.vercel.app/api/human-help'
];
const ALLOWED_ACTIONS = new Set(['inspect', 'resolve', 'status']);
const NSOSYAL_HOSTS = new Set(['nsosyal.com', 'www.nsosyal.com']);

async function configureSessionStorageAccess() {
  try {
    await chrome.storage.session.setAccessLevel({
      accessLevel: 'TRUSTED_AND_UNTRUSTED_CONTEXTS'
    });
  } catch (_) {
    // Older Chromium builds may not expose setAccessLevel. The overlay still
    // works without persistence in those builds; current Chrome supports it.
  }
}

configureSessionStorageAccess();
chrome.runtime.onInstalled.addListener(configureSessionStorageAccess);
chrome.runtime.onStartup.addListener(configureSessionStorageAccess);

function trustedPostUrl(value) {
  if (value == null) return null;
  if (typeof value !== 'string' || value.length > 2048) return false;
  try {
    const url = new URL(value);
    return url.protocol === 'https:' && NSOSYAL_HOSTS.has(url.hostname) ? url.href : false;
  } catch (_) {
    return false;
  }
}

function trustedSender(sender) {
  try {
    const raw = sender?.url || sender?.tab?.url || '';
    const url = new URL(raw);
    return url.protocol === 'https:' && NSOSYAL_HOSTS.has(url.hostname);
  } catch (_) {
    return false;
  }
}

function errorText(value, fallback = 'DRSK backend request failed') {
  if (!value) return fallback;
  if (typeof value === 'string') return value;
  if (value instanceof Error && value.message) return value.message;
  if (typeof value === 'object') {
    for (const key of ['message', 'detail', 'code', 'error']) {
      const nested = value[key];
      if (typeof nested === 'string' && nested.trim()) return nested.trim();
    }
    try {
      const encoded = JSON.stringify(value);
      if (encoded && encoded !== '{}') return encoded;
    } catch (_) {}
  }
  return String(value);
}

function validatePayload(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return { ok: false, error: 'invalid_payload' };
  }

  const action = value.action;
  if (!ALLOWED_ACTIONS.has(action)) {
    return { ok: false, error: 'unsupported_action' };
  }

  if (action === 'inspect' || action === 'resolve') {
    if (typeof value.text !== 'string') return { ok: false, error: 'text_required' };
    const text = value.text.trim();
    if (!text || text.length > 1200) return { ok: false, error: 'invalid_text_length' };
    const postUrl = trustedPostUrl(value.post_url);
    if (postUrl === false) return { ok: false, error: 'invalid_post_url' };
    return {
      ok: true,
      payload: {
        action,
        text,
        ...(action === 'resolve' && postUrl ? { post_url: postUrl } : {})
      }
    };
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

async function requestOne(url, payload) {
  const response = await fetch(url, {
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

  return { response, data };
}

async function requestApi(payload) {
  let lastFailure = null;

  for (let index = 0; index < API_URLS.length; index += 1) {
    const url = API_URLS[index];
    try {
      const { response, data } = await requestOne(url, payload);
      if (response.ok) {
        return { ok: true, status: response.status, data };
      }

      const failure = {
        ok: false,
        status: response.status,
        error: errorText(data?.error ?? data?.message, `HTTP ${response.status}`)
      };
      lastFailure = failure;

      // Vercel maps Python function filenames to underscore routes. The hyphen
      // alias is retained only as a compatibility fallback, so only retry a
      // route-like failure rather than masking a real application error.
      const domainError = typeof data?.error === 'string' && data.error.trim();
      const routeFailure = [404, 405].includes(response.status) && !domainError;
      if (!routeFailure || index === API_URLS.length - 1) {
        return failure;
      }
    } catch (error) {
      lastFailure = {
        ok: false,
        status: 0,
        error: errorText(error, 'DRSK backend is not reachable right now.')
      };
      if (index === API_URLS.length - 1) return lastFailure;
    }
  }

  return lastFailure || { ok: false, status: 0, error: 'DRSK backend is not reachable right now.' };
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
      error: errorText(error, 'DRSK backend is not reachable right now.')
    }));

  return true;
});
