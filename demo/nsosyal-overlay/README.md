# DRSK × NSosyal concept overlay

This folder contains the Chrome/Chromium Manifest V3 extension used to demonstrate how DRSK could live on top of the **real NSosyal interface** without pretending the prototype is an official NSosyal build.

The overlay does **not** publish, edit, or delete NSosyal content. It reads the text currently visible in the user's composer only after the user explicitly presses the DRSK action, sends that text to the fixed public DRSK prototype backend, and renders bounded evidence over the real site. A human request is opened only after a second explicit **Ask a relevant person** action. Account cookies are never forwarded to the DRSK backend.

## Why an overlay instead of a cloned NSosyal shell?

The final demo should prove the DRSK interaction model, not our ability to reproduce another product's navigation and icons. The real NSosyal page remains untouched as the host product. The extension contributes only the new resolution layer:

`NSosyal composer → DRSK → SOURCECHAIN evidence → Resolution Engine → NIYET when needed → human answer`

The standalone `/live` prototype remains the fallback and the inspectable technical surface.

## Architecture

- A static content script runs only on `nsosyal.com` / `www.nsosyal.com`.
- Composer detection is heuristic and confidence-gated. If no safe composer match exists, the DRSK action becomes a floating fallback rather than attaching to an arbitrary control.
- The injected DRSK UI lives inside a closed **Shadow DOM**, so NSosyal styles do not leak into the overlay and overlay styles do not leak into NSosyal.
- The content script never performs cross-origin fetches. It sends a small, structured message to the Manifest V3 service worker.
- The service worker accepts only `inspect`, `resolve`, and `status`, validates the payload, and calls only `https://niyet-nsosyal.vercel.app/api/human_help` over HTTPS.
- The active DRSK request token is kept in extension session storage so an answer can return after a NSosyal reload. It is never written into the NSosyal page or permanent browser storage.
- Dynamic backend values are rendered with DOM APIs / `textContent`, never as backend-supplied HTML.

See `SECURITY.md` for the explicit trust boundary.

## Load locally

1. Open `chrome://extensions`.
2. Enable **Developer mode**.
3. Choose **Load unpacked** and select `demo/nsosyal-overlay`.
4. Open `https://nsosyal.com/home` while logged in.
5. Type a post in the normal NSosyal composer and press the small **DRSK** action.

The extension asks only for the NSosyal page access needed by its content script, access to the fixed DRSK backend host, and session storage for the active request lifecycle. It does not request broad web access or NSosyal API credentials.

## Demo contract

- Real NSosyal remains the host surface.
- DRSK is explicitly labeled a **concept integration**.
- SOURCECHAIN evidence comes from the same bounded backend used by the standalone prototype.
- NIYET uses the same shared request lifecycle and responder-capacity logic.
- The standalone `/live` prototype remains the fallback if the host site changes or is unavailable.
