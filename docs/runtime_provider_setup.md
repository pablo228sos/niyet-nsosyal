# Runtime provider setup

The final DRSK demo keeps external services behind server-side provider boundaries. Client surfaces never receive provider credentials.

## Live web evidence

Production preference order:

1. `TAVILY_API_KEY` → Tavily live web evidence
2. `BRAVE_SEARCH_API_KEY` → optional Brave fallback when configured
3. verified in-repository corpus → deterministic offline fallback

The web provider only acquires candidate evidence. SOURCECHAIN still performs passage ranking, claim/evidence relation analysis, and typed distortion checks.

## Durable NIYET state

For cross-device and multi-instance demo state, configure:

```text
UPSTASH_REDIS_REST_URL=...
UPSTASH_REDIS_REST_TOKEN=...
DRSK_STATE_NAMESPACE=jury-demo-v2      # optional override
DRSK_STATE_TTL_SECONDS=86400           # optional
```

After adding or changing Vercel environment variables, create a new Production deployment so the function runtime receives the new values.

Verify the active state backend with:

```text
GET /api/human_help
```

A durable production configuration reports `state_durable: true` and a Redis-backed `state_backend`. A process-local fallback reports `state_durable: false` and must not be represented as durable cross-device state.

The built-in default separates Vercel Preview (`jury-demo-v2-preview`) from
Production (`jury-demo-v2`) so preview tests do not spend production capacity.
