# Install checklist

This extension is intended for the competition demo machine, not for Chrome Web Store distribution.

1. Check out the final tested branch/commit, or build the packaged extension with `python scripts/package_nsosyal_overlay.py`.
2. Open `chrome://extensions` in Chrome or Chromium.
3. Enable **Developer mode**.
4. Select **Load unpacked** and choose `demo/nsosyal-overlay`.
5. Confirm the extension requests access only to NSosyal pages, the fixed DRSK backend host, and extension session storage.
6. Open `https://nsosyal.com/home`, sign in normally, and type text in the normal NSosyal composer.
7. Press **DRSK**. Verify that evidence appears before any human request is opened.
8. Publish with NSosyal's own control. After the exact text is detected as a published post, press **Ask a relevant person** only when the demo calls for NIYET routing. The extension must never press NSosyal's publish button or modify the account.

Before a jury session, verify both fallbacks:

- Standalone DRSK surface: `https://niyet-nsosyal.vercel.app/live`
- Local single-process fallback: `python scripts/serve_local.py --host 0.0.0.0 --port 8765`

Do not update Chrome, the extension, or the repository on the jury machine after the final rehearsal unless a blocking bug requires it.
