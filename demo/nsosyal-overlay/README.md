# DRSK × NSosyal concept overlay

This folder contains a small Chrome/Chromium Manifest V3 extension used to demonstrate how DRSK could live on top of the real NSosyal surface without pretending the prototype is an official NSosyal build.

The overlay does **not** publish, edit, or delete NSosyal content. It only reads the text currently visible in the user's composer after the user explicitly presses the DRSK button, sends that text to the public DRSK prototype backend, and renders bounded evidence / human-routing context over the real site. Account cookies are not forwarded to the DRSK backend.

## Load locally

1. Open `chrome://extensions`.
2. Enable **Developer mode**.
3. Choose **Load unpacked** and select `demo/nsosyal-overlay`.
4. Open `https://nsosyal.com/home` while logged in.
5. Type a post in the normal NSosyal composer and press the small **DRSK** action.

The extension tries to anchor the DRSK action close to the current composer. If the site DOM changes and a composer cannot be identified safely, it falls back to a floating DRSK action instead of mutating unknown page structure.

## Demo contract

- Real NSosyal remains the host surface.
- DRSK is explicitly labeled a **concept integration**.
- SOURCECHAIN evidence comes from the same bounded backend used by the standalone prototype.
- NIYET uses the same shared request lifecycle and responder capacity logic.
- The standalone `/live` prototype remains the fallback if the host site changes or is unavailable.
