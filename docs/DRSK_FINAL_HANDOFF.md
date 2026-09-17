# DRSK MVP final handoff

Status: core frozen in production, 2026-09-17.

## Product contract

DRSK is the resolution layer for NSosyal. SOURCECHAIN provides bounded evidence intelligence. NIYET provides capacity-aware human interaction intelligence. The Resolution Engine selects exactly one path: `EVIDENCE`, `HUMAN`, `BOTH`, or `NONE`.

The operating rule is: when evidence is enough, show the evidence; when it is not, find the right willing human. Weak, ambiguous, deictic, or irrelevant evidence must fail closed as `INSUFFICIENT`.

The backend is the source of truth. `/live`, the NSosyal overlay, and the responder surface are thin clients. The overlay is a concept integration adapter, not the product and not a replacement for NSosyal.

## Release state

- Production: <https://niyet-nsosyal.vercel.app>
- PR #29 was merged into PR #28; PR #28 was merged into `main`.
- Frozen core merge commit: `fc7f056af74eb0ba7d69d494014d2505969c53d0`.
- Production deployment: `dpl_Fh2r6gYHw9P1S3Yi9zUvupKAQhdb` (`READY`).
- Final release-candidate Preview: `dpl_4QJJDHQbdhZU9ptmLoKTLmk5Syfd` (`READY`).
- Upstash Redis REST is the durable shared state backend in deployed environments.
- `TAVILY_API_KEY` is configured in Vercel. Live acquisition uses a cheap-to-expensive cascade: basic search, quality gate, advanced only when needed, then `INSUFFICIENT`.
- `experiment/tavily-depth-audit` remains isolated and must not be merged into the core.

## What is proved

- Arbitrary Turkish and English inputs are not limited to fixed audit cases.
- `EVIDENCE`, `HUMAN`, `BOTH`, and `NONE` paths have regression coverage and deployed API checks.
- Live evidence requires lexical relevance, textual anchors, and entity/date/number compatibility. Numeric coincidence alone is rejected.
- Only `SUPPORTED` is sufficient. `PARTIAL`, `CONFLICTING`, and `INSUFFICIENT` remain visibly bounded and can route the unresolved part to NIYET.
- Draft inspection never creates a human request. The extension unlocks NIYET only after detecting the same text as a visible published NSosyal post and after explicit user action.
- Published post URL and evidence context survive routing, accept, answer, and resolved states.
- Responder willingness and remaining capacity are hard constraints. Stale polling, stale assignment, empty queue, pause/resume, capacity exhaustion, and shared-state conflicts have guarded states.
- The latest local suite passed: 253 tests. GitHub Actions run #450 passed. Latest Preview was `READY`; runtime error query returned no errors.

## Deliberate boundaries

- SOURCEBENCH alignment stays at 3/4. The remaining Turkish semantic paraphrase has low lexical overlap. Fixing it safely needs a general semantic mechanism; a synonym rule tailored to one benchmark case would reduce trust.
- Reader-side SOURCECHAIN for arbitrary existing feed posts is not in the frozen core. Reliable post selection, anchoring, and consent are not a small change; adding it now would raise demo risk.
- ModernBERT-TR remains an offline evaluation signal, not a production dependency.
- No truth score, hidden psychological profile, reputation score, blockchain, agent layer, chatbot, or generated summary is part of the MVP.

## Manual checks still required

Run these on the actual presentation hardware after installing the packaged extension:

1. Real NSosyal composer on device A: enter a new claim/question and verify private SOURCECHAIN inspection.
2. Confirm no NIYET request exists before publication.
3. Publish the same text, let the overlay detect the post, then press the explicit human-help action.
4. Open the copied responder link on device B, accept, answer, and verify the author reaches `Resolved`.
5. Repeat once at a narrow/mobile viewport and once with a long Turkish post and long source title.
6. Verify the presentation network allows NSosyal, Vercel, Tavily, and Upstash. Keep the controlled example as fallback if live web acquisition is slow.

Cloud-browser tabs are useful integration verification, but they are not physical two-device or human usability testing.

## Judge demo flow

1. Ask the judge for an unknown post.
2. Show draft evidence inspection without creating a human request.
3. Publish it on real NSosyal.
4. Let the Resolution Engine choose the path and explain why.
5. If evidence is sufficient, stop at SOURCECHAIN. If not, request human context explicitly.
6. On the responder device, show matching reason and capacity, accept, answer, and return to the same published post as `Resolved`.

## Freeze rule

Do not add features to the core before the final. Accept only a reproduced blocker with a minimal fix, a regression test, green CI, Preview verification, and Technical Report alignment.
