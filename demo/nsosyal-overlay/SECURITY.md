# DRSK × NSosyal overlay security model

The overlay is a presentation/demo integration layer, not an official NSosyal client and not a replacement for a production NSosyal integration.

## Boundaries

- The content script runs only on `nsosyal.com` / `www.nsosyal.com`.
- It reads composer text only after the user explicitly presses the DRSK action.
- It never calls NSosyal publish/edit/delete actions and never reads or forwards NSosyal cookies.
- Cross-origin DRSK requests are made only by the extension service worker to the fixed HTTPS endpoint `https://niyet-nsosyal.vercel.app/api/human-help`.
- The service worker accepts only the DRSK `inspect`, `resolve`, and `status` actions and validates payload sizes before forwarding them.
- Evidence inspection never creates a human request. Human routing requires a separate explicit confirmation in the overlay.
- The active request id and author token live only in extension session storage so polling can resume after a page reload. NSosyal page scripts cannot read extension storage, and the token is cleared when the browser session ends.
- The injected UI is isolated in a closed Shadow DOM. Dynamic backend values are rendered through DOM APIs / `textContent`, not backend-provided HTML.
- If the NSosyal composer cannot be identified with sufficient confidence, the DRSK action falls back to a floating control instead of attaching to an arbitrary page element.

## Demo claim

The overlay demonstrates the integration boundary and interaction model on top of the real NSosyal interface. It does not claim official or production deployment inside NSosyal.
