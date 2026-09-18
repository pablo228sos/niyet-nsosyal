# DRSK × NSosyal overlay security model

The overlay is a presentation/demo integration layer, not an official NSosyal client and not a replacement for a production NSosyal integration.

## Boundaries

- The content script runs only on `nsosyal.com` / `www.nsosyal.com`.
- It reads composer text only after the user explicitly presses the DRSK action.
- It never calls NSosyal publish/edit/delete actions and never reads or forwards NSosyal cookies.
- Cross-origin DRSK requests are made only by the extension service worker to the configured DRSK HTTPS backend. Production defaults to `https://niyet-nsosyal.vercel.app`; Preview packaging rewrites the allowed backend origin and host permission together.
- The service worker accepts only the DRSK `inspect`, `resolve`, and `status` actions and validates payload sizes before forwarding them.
- Evidence inspection never creates a human request. Human routing requires a separate explicit confirmation in the overlay.
- Request credentials live in extension storage, never in the NSosyal DOM. The service worker explicitly enables Manifest V3 session-storage access for the content script; the content script falls back to extension local storage only when session storage is unavailable. NSosyal page scripts cannot read either extension storage area.
- The injected UI is isolated in a closed Shadow DOM. Dynamic backend values are rendered through DOM APIs / `textContent`, not backend-provided HTML.
- If the NSosyal composer cannot be identified with sufficient confidence, DRSK does not attach to an arbitrary page element. Desktop can use the compact fallback; narrow-screen fallback is deliberately suppressed to avoid covering native controls.

## Demo claim

The overlay demonstrates the integration boundary and interaction model on top of the real NSosyal interface. It does not claim official or production deployment inside NSosyal.
