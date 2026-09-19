# DRSK × NSosyal concept overlay

This folder contains the Chrome/Chromium Manifest V3 extension used to demonstrate how DRSK could live on top of the **real NSosyal interface** without pretending the prototype is an official NSosyal build.

The overlay does **not** publish, edit, or delete NSosyal content. It reads the text currently visible in the user's composer only after the user explicitly presses the DRSK action, sends that text to the fixed public DRSK prototype backend, and renders bounded evidence over the real site. Human routing stays locked while the text is a draft. After the user presses NSosyal's own publish action, the adapter waits until the exact inspected text is visible outside the composer as a published post. Only then can the user explicitly press **Ask a relevant person**. Account cookies are never forwarded to the DRSK backend.

## Why an overlay instead of a cloned NSosyal shell?

The final demo should prove the DRSK interaction model, not our ability to reproduce another product's navigation and icons. The real NSosyal page remains untouched as the host product. The extension contributes only the new resolution layer:

`NSosyal draft → SOURCECHAIN evidence → native publish → published post → NIYET by consent → human answer`

The standalone `/live` prototype remains the deterministic fallback and the inspectable technical surface. An authenticated hardware pass completed the real-host path through responder answer return before the final freeze.

## Authenticated hardware proof

The final real-host pass was captured step by step: private inspect, native publication detection, explicit NIYET opt-in, responder routing and the returned human answer.

![Published NSosyal post detected before explicit human routing](../../docs/screenshots/07_nsosyal_published_optin.webp)

See **[Real NSosyal acceptance](../../docs/REAL_NSOSYAL_ACCEPTANCE.md)** for all four captures and the exact boundary of what this prototype proves.

## Architecture

- A static content script runs only on `nsosyal.com` / `www.nsosyal.com`.
- Composer detection is heuristic and confidence-gated. Desktop may use a compact floating fallback when no composer is available. On narrow screens the fallback is intentionally hidden; DRSK appears only when the native composer is safely detected, avoiding collisions with NSosyal navigation/publish controls.
- Published-post detection requires the exact inspected text to appear in a visible, non-editable NSosyal feed element. A native publish-button click starts the bounded detection window; a manual check remains available if rendering is delayed.
- The injected DRSK UI lives inside a closed **Shadow DOM**, so NSosyal styles do not leak into the overlay and overlay styles do not leak into NSosyal.
- The content script never performs cross-origin fetches. It sends a small, structured message to the Manifest V3 service worker.
- The service worker accepts only `inspect`, `resolve`, and `status`, validates the payload, and calls the configured DRSK HTTPS backend. Preview packaging rewrites the backend origin, Manifest host permission and responder link together so one request cannot split across environments.
- Active and latest-resolved DRSK state is kept in extension storage so answers can return after a NSosyal reload. Current Chromium session storage is explicitly exposed to the content script by the service worker, with a guarded local-storage fallback when session access is unavailable. Tokens are never written into the NSosyal page.
- Dynamic backend values are rendered with DOM APIs / `textContent`, never as backend-supplied HTML.

See `SECURITY.md` for the explicit trust boundary.

## Load locally

1. Open `chrome://extensions`.
2. Enable **Developer mode**.
3. Choose **Load unpacked** and select `demo/nsosyal-overlay`.
4. Open `https://nsosyal.com/home` while logged in.
5. Type a post in the normal NSosyal composer and press the small **DRSK** action.
6. Review the evidence, then publish with NSosyal's native action.
7. After DRSK detects the visible published post, explicitly choose **Ask a relevant person**.

The extension asks only for the NSosyal page access needed by its content script, access to the configured DRSK backend host, and extension storage for the request lifecycle. It does not request broad web access or NSosyal API credentials.

## Demo contract

- Real NSosyal remains the host surface.
- DRSK is explicitly labeled a **concept integration**.
- SOURCECHAIN evidence comes from the same bounded backend used by the standalone prototype.
- NIYET uses the same shared request lifecycle and responder-capacity logic.
- The standalone `/live` prototype remains the fallback if the host site changes or is unavailable.
