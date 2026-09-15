const API_URL = 'https://niyet-nsosyal.vercel.app/api/human-help';

async function requestApi(payload = null) {
  const response = await fetch(API_URL, payload ? {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    credentials: 'omit',
    redirect: 'error'
  } : {
    method: 'GET',
    credentials: 'omit',
    redirect: 'error'
  });

  let data = {};
  try { data = await response.json(); } catch (_) {}
  if (!response.ok) {
    return { ok: false, status: response.status, error: data.error || `HTTP ${response.status}` };
  }
  return { ok: true, status: response.status, data };
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type !== 'drsk-api') return false;
  requestApi(message.payload || null)
    .then(sendResponse)
    .catch((error) => sendResponse({ ok: false, status: 0, error: error?.message || 'backend unavailable' }));
  return true;
});
