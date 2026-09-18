# Runtime provider setup

DRSK keeps external services behind server-side provider boundaries. Browser surfaces never receive search-provider or state-store credentials.

## Live web evidence

Actual provider order:

1. strong match from the committed verified corpus — deterministic fast path;
2. `TAVILY_API_KEY` basic search behind the live quality gate;
3. Tavily advanced search only when the basic result is too weak;
4. `BRAVE_SEARCH_API_KEY` — optional secondary fallback when configured;
5. full verified corpus — deterministic final fallback.

The external provider only acquires candidate evidence. SOURCECHAIN still owns passage ranking, relation analysis, distortion checks and the decision to stay `INSUFFICIENT`.

~~~text
TAVILY_API_KEY=...
BRAVE_SEARCH_API_KEY=...   # optional
~~~

No search-provider credential is sent to the client.

## Durable human-help state

For cross-device and multi-instance demo state:

~~~text
UPSTASH_REDIS_REST_URL=...
UPSTASH_REDIS_REST_TOKEN=...
DRSK_STATE_NAMESPACE=jury-demo-v2
DRSK_STATE_TTL_SECONDS=86400
~~~

Vercel integration aliases are also supported:

~~~text
KV_REST_API_URL=...
KV_REST_API_TOKEN=...
~~~

Verify the active state backend with:

~~~text
GET /api/human_help
~~~

A durable configuration reports `state_durable: true` and a Redis-backed `state_backend`. The process-local fallback reports `state_durable: false` and must not be represented as durable cross-device state.

The built-in namespace default separates Vercel Preview (`jury-demo-v2-preview`) from Production (`jury-demo-v2`), so Preview verification cannot consume the jury session.

## Preview extension packaging

For a Preview-specific unpacked extension:

~~~bash
DRSK_OVERLAY_BACKEND_ORIGIN=https://<preview>.vercel.app \
  python scripts/package_nsosyal_overlay.py
~~~

The packager rewrites the service-worker backend URL, Manifest V3 host permission and responder `/live` link together. This prevents Author and Responder from accidentally using different state backends.
