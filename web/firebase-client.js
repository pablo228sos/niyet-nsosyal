import { initializeApp } from 'https://www.gstatic.com/firebasejs/12.19.0/firebase-app.js';
import {
  GoogleAuthProvider,
  browserLocalPersistence,
  createUserWithEmailAndPassword,
  getAuth,
  onAuthStateChanged,
  setPersistence,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
  updateProfile
} from 'https://www.gstatic.com/firebasejs/12.19.0/firebase-auth.js';

const state = { auth: null, user: null, ready: false };

function element(id) {
  return document.getElementById(id);
}

function authMessage(value, error = false) {
  const target = element('authMessage');
  if (!target) return;
  target.textContent = value || '';
  target.classList.toggle('error', error);
}

function errorCode(error) {
  return error?.code || error?.message || 'request_failed';
}

export function isAuthenticated() {
  return Boolean(state.user);
}

export function currentUser() {
  return state.user;
}

export async function apiRequest(action = 'me', options = {}) {
  if (!state.user) {
    const error = new Error('auth_required');
    error.code = 'auth_required';
    error.status = 401;
    throw error;
  }
  const token = await state.user.getIdToken();
  const method = options.method || (options.body ? 'POST' : 'GET');
  let url = '/api/niyet';
  const headers = { ...(options.headers || {}), Authorization: `Bearer ${token}` };
  const request = { method, headers, cache: 'no-store' };
  if (method === 'GET') {
    const query = new URLSearchParams({ action, ...(options.query || {}) });
    url += `?${query.toString()}`;
  } else {
    headers['Content-Type'] = 'application/json';
    request.body = JSON.stringify({ action, ...(options.body || {}) });
  }
  const response = await fetch(url, request);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(payload?.error?.code || `HTTP ${response.status}`);
    error.code = payload?.error?.code || null;
    error.status = response.status;
    throw error;
  }
  return payload;
}

export function newIdempotencyKey() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
  const bytes = new Uint8Array(24);
  globalThis.crypto.getRandomValues(bytes);
  return Array.from(bytes, (value) => value.toString(16).padStart(2, '0')).join('');
}

export async function createRequest(text, { mode = 'create_request', intent = 'ask', postUrl = null } = {}) {
  let stored = null;
  try { stored = JSON.parse(sessionStorage.getItem('niyet-pending-create') || 'null'); } catch (_) {}
  const idempotencyKey = stored?.text === text && stored?.mode === mode
    ? stored.key
    : newIdempotencyKey();
  sessionStorage.setItem('niyet-pending-create', JSON.stringify({ text, mode, key: idempotencyKey }));
  const body = {
    text,
    intent,
    idempotency_key: idempotencyKey
  };
  if (postUrl) body.post_url = postUrl;
  try {
    const result = await apiRequest(mode, { method: 'POST', body });
    sessionStorage.removeItem('niyet-pending-create');
    return result;
  } catch (error) {
    if (error.status && error.status < 500) sessionStorage.removeItem('niyet-pending-create');
    throw error;
  }
}

export const getMe = () => apiRequest('me');
export const getInbox = () => apiRequest('inbox');
export const getRequest = (requestId) => apiRequest('request', { query: { request_id: requestId } });
export const updateResponderProfile = (profile) => apiRequest('update_profile', { method: 'POST', body: profile });
export const acceptAssignment = (assignmentId) => apiRequest('accept', { method: 'POST', body: { assignment_id: assignmentId } });
export const skipAssignment = (assignmentId) => apiRequest('skip', { method: 'POST', body: { assignment_id: assignmentId } });
export const answerAssignment = (assignmentId, answer) => apiRequest('answer', { method: 'POST', body: { assignment_id: assignmentId, answer } });
export const pauseResponder = () => apiRequest('pause', { method: 'POST' });
export const resumeResponder = () => apiRequest('resume', { method: 'POST' });

function setSignedInState(user) {
  const signedOut = element('authSignedOut');
  const signedIn = element('authSignedIn');
  if (signedOut) signedOut.hidden = Boolean(user);
  if (signedIn) signedIn.hidden = !user;
  if (element('currentUser')) {
    element('currentUser').textContent = user ? (user.displayName || user.email || user.uid) : '';
  }
  if (element('accountStatus')) {
    element('accountStatus').textContent = user
      ? `Signed in as ${user.email || user.uid}`
      : 'Sign in to use NIYET';
  }
}

function bind(id, event, callback) {
  const target = element(id);
  if (target) target.addEventListener(event, callback);
}

async function initializeAuth() {
  try {
    const response = await fetch('/api/niyet?action=config', { cache: 'no-store' });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload?.error?.code || 'firebase_config_unavailable');
    const app = initializeApp(payload.firebase);
    state.auth = getAuth(app);
    await setPersistence(state.auth, browserLocalPersistence);
  } catch (error) {
    state.ready = true;
    setSignedInState(null);
    authMessage(errorCode(error), true);
    window.dispatchEvent(new CustomEvent('niyet-auth-changed', { detail: { user: null, error } }));
    return;
  }

  bind('signUpEmail', 'click', async () => {
    try {
      authMessage('');
      const credential = await createUserWithEmailAndPassword(
        state.auth,
        element('authEmail').value.trim(),
        element('authPassword').value
      );
      const displayName = element('authDisplayName')?.value.trim();
      if (displayName) await updateProfile(credential.user, { displayName });
      await credential.user.getIdToken(true);
    } catch (error) {
      authMessage(errorCode(error), true);
    }
  });
  bind('signInEmail', 'click', async () => {
    try {
      authMessage('');
      await signInWithEmailAndPassword(
        state.auth,
        element('authEmail').value.trim(),
        element('authPassword').value
      );
    } catch (error) {
      authMessage(errorCode(error), true);
    }
  });
  bind('signInGoogle', 'click', async () => {
    try {
      authMessage('');
      await signInWithPopup(state.auth, new GoogleAuthProvider());
    } catch (error) {
      authMessage(errorCode(error), true);
    }
  });
  bind('signOutUser', 'click', () => signOut(state.auth));

  onAuthStateChanged(state.auth, async (user) => {
    state.user = user;
    state.ready = true;
    setSignedInState(user);
    if (user) {
      try {
        await apiRequest('sync_user', { method: 'POST' });
        authMessage('');
      } catch (error) {
        authMessage(errorCode(error), true);
      }
    }
    window.dispatchEvent(new CustomEvent('niyet-auth-changed', { detail: { user } }));
  });
}

initializeAuth();
