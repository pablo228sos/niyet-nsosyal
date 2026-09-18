# UI design rationale

The final prototype is designed as a capability inside a social feed, not as a separate AI dashboard or expert marketplace.

## Host product first

Public NSosyal material presents a conventional social product around feed content, discovery, profiles and real-time interaction. The prototype therefore keeps the host surface visually quiet and familiar: a feed, composer, author identity, post state and responder mode.

We do not claim a pixel-perfect copy of an authenticated NSosyal application. This is an NSosyal-inspired concept integration built from public product patterns.

The final surface intentionally removes decorative navigation and social actions that do not perform a real prototype action. It is better to show fewer real controls than to create the impression of a complete social network through dead UI.

## One product, two roles

DRSK has an author side and a responder side, but both live inside the same feed shell.

The author sees:

- the original post
- bounded evidence when available
- claim-to-passage explanation
- the routed responder when human context is needed
- the returned human answer

The responder sees:

- only requests currently allocated to that responder profile
- the same evidence/provenance available to the author
- remaining capacity and routing availability
- Accept / Skip / Pause / Resume / Answer actions

The role switch exists because capacity-aware routing is part of the product behavior, not a back-office implementation detail.

## Where DRSK becomes visible

DRSK should not dominate an ordinary post. It appears only when the system has something useful to add.

The interaction progresses through four plain states:

1. **Need** — a person posts without depending on follower count for eligibility.
2. **Evidence** — SOURCECHAIN exposes what bounded evidence actually supports.
3. **Human** — NIYET routes the unresolved part to a willing responder with remaining capacity.
4. **Resolved** — human context returns to the same social object.

This is deliberately different from an AI-chat pattern where every interaction ends in a model-generated answer.

## Visual language

The host surface uses neutral whites, grays and one action blue. DRSK uses semantic accents rather than decorative AI effects:

- SOURCECHAIN: restrained evidence blue
- NIYET: restrained routing violet
- resolved human context: green
- warning/conflict: amber or red with explicit text labels

There is no glowing orb, full-page gradient, glassmorphism shell, generic confidence gauge or animated neural-network decoration. The goal is for the feature to look shippable inside a real social product.

## Evidence readability

The key explanatory component is generic and data-driven:

**Post claim ↔ Source passage**

It uses the actual claim text and stored evidence passage returned by the API. It is not hard-coded to the coffee causality example, so numeric and other typed distortions can use the same interaction pattern.

Publisher/title/date and the original source link remain accessible. The responder receives the same provenance context before answering.

## Progressive disclosure

Normal users first see the smallest useful explanation. Exact provenance remains available without turning every post into a research dashboard.

We avoid a generic `trust score` because it compresses a claim/evidence relationship into a number that the current system does not justify. SOURCECHAIN surfaces bounded evidence and explicit relation/distortion states instead.

## Product versus presentation

The public product surface does not contain pitch-only metrics, jury messaging or internal evaluation material. Those belong in the final presentation and defense material, not inside the product UI.

The live product keeps only a small prototype-boundary note because that prevents overclaiming during hands-on use.

## State and persistence

The human-help lifecycle is server-authoritative rather than browser-authoritative. Request state, responder availability and remaining capacity are handled by the HumanHelpService through a storage boundary.

The current code supports:

- process-local memory for local development / single-process demonstrations
- an external durable state backend when configured for multi-instance deployment

The UI must not claim durable production state when the process-local fallback is active.

## Responsive behavior

Desktop uses a three-part workspace: orientation rail, feed, and resolution context.

At tablet widths the orientation rail disappears and the resolution context moves below the feed.

On mobile the interface becomes one feed column. Author and responder modes remain accessible, controls stack without horizontal overflow, long request IDs/passages wrap safely and primary touch targets remain at least 44px high.

## Motion

Motion is intentionally small and functional:

- evidence/routing/answer surfaces reveal with a short fade/translate
- connection checking can pulse subtly
- controls have hover/press feedback
- no decorative background animation runs continuously
- `prefers-reduced-motion` disables nonessential motion

## Accessibility

The final surface includes or requires:

- visible keyboard focus
- semantic form labels and buttons
- live status regions for asynchronous changes
- no critical state communicated by color alone
- minimum 44px primary touch targets
- reduced-motion support
- safe text wrapping at small widths
- source links on author and responder views
- prototype limitations still visible on mobile

## Bilingual surface

English and Turkish share the same product states and dynamic routing data. Language switching changes presentation copy only; it does not imply that every underlying model or benchmark was evaluated bilingually.

## Why this direction

The earlier prototype explored more visibly "AI" design patterns. For the final stage we chose the opposite direction: make DRSK feel like a native social capability and let technical depth appear through behavior, evidence provenance, shared capacity and cross-device resolution.

That makes the product easier to understand in a short live demonstration and harder to dismiss as a styled AI dashboard.

The real-site adapter also separates draft assistance from the social lifecycle. SOURCECHAIN may inspect composer text, but NIYET remains locked until NSosyal's own publish action completes and the exact text appears as a visible post. The extension never presses the host action or claims access to a private platform API.
