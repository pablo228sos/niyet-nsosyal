# DRSK product interface system

## Product direction

DRSK is presented as a capability inside a social network, not as a separate AI dashboard.
The host product must remain recognizable first. DRSK becomes visible only when a post
needs evidence context, human resolution, or both.

The final surface follows one interaction thesis:

> ordinary social post → evidence when useful → human context when needed → resolved in place

The visual system deliberately avoids common hackathon-AI motifs: no glowing AI orb, no
full-page gradients, no glassmorphism dashboard, no generic confidence gauge, and no
"AI powered" decoration. Technical depth is revealed through behavior and provenance.

## Visual principles

1. **Host first** — the feed, composer, author identity and responder inbox look like parts
   of one social product. DRSK does not replace the host navigation or create a parallel app.
2. **Quiet by default** — neutral canvas, white surfaces, restrained borders and one primary
   action blue. The interface should still look credible if every DRSK label is removed.
3. **Semantic accents, not spectacle** — SOURCECHAIN uses a restrained blue evidence accent;
   NIYET uses a restrained violet routing accent; resolved human context uses green.
4. **Progressive disclosure** — the user sees the claim/source relationship first. Exact
   passage, provenance and source URL remain one level deeper but are always reachable.
5. **Resolution is the end state** — UI states are not centered on model output. They move
   from Need → Evidence → Human → Resolved.
6. **Prototype honesty** — controlled evidence, demo identities and storage limitations are
   identified without dominating the normal user flow.

## Design tokens

| Role | Value |
| --- | --- |
| Canvas | `#F6F8FB` |
| Surface | `#FFFFFF` |
| Primary text | `#101828` |
| Secondary text | `#667085` |
| Border | `#E4E7EC` |
| Primary action | `#155EEF` |
| Primary hover | `#004EEB` |
| Evidence soft | `#EFF4FF` |
| NIYET accent | `#6941C6` |
| NIYET soft | `#F4F3FF` |
| Resolved | `#067647` |
| Resolved soft | `#ECFDF3` |
| Warning | `#B54708` |
| Error | `#B42318` |

Typography uses the operating-system sans stack. No network font is required for the live
demo. Product copy stays sentence-case. Uppercase is reserved for small system labels such
as SOURCECHAIN / NIYET and compact status metadata.

Spacing follows a compact product rhythm rather than a marketing-page rhythm. Core surfaces
use 10–18px radii, light one-pixel borders and small shadows only when they clarify layering.
Large blurred shadows and decorative glows are intentionally absent.

## Composition

### Desktop

- left rail: host-product orientation and a small DRSK integration marker
- center: primary social feed and the entire resolution journey
- right rail: current Need → Evidence → Human → Resolved state and prototype boundary
- author/responder modes share the same feed shell so the system reads as one product

The right rail is contextual, not promotional. Pitch-only metrics and competition messaging
belong in the presentation, not inside the product UI.

### Tablet

The left rail disappears first. The resolution context moves beneath the feed while the author
and responder flows keep the same controls and content hierarchy.

### Mobile

The product becomes a single feed column. Author and responder modes remain equally usable;
responder controls do not disappear at the breakpoint. Primary actions stack, long request IDs
and passages wrap safely, and touch targets remain at least 44px high.

## Interaction hierarchy

### Author

1. write a normal social post
2. choose `Post with DRSK` or explicitly request a person
3. see bounded evidence inline when available
4. understand the relationship between the original claim and the exact source passage
5. if human context is needed, see who the request was routed to and why
6. receive the human answer on the same post

Follower count is shown as context but is not an eligibility signal.

### Responder

1. choose a responder profile for the prototype
2. see only requests currently allocated to that profile
3. inspect the same evidence/provenance the author sees
4. Accept or Skip the request
5. Pause/Resume routing availability
6. answer the accepted request

Capacity and willingness are product constraints, not decorative ranking badges.

## Evidence UI

Evidence is never rendered as a generic truth score.

Each evidence surface can expose:

- exact post claim
- exact stored source passage
- publisher/title/date
- relation and typed distortion signal
- original source link

The comparison component is generic (`Post claim ↔ Source passage`) rather than hard-coded to
a single causality example. This keeps the UI aligned with the underlying SOURCECHAIN schema.

## Motion

Motion is functional and low-amplitude:

- newly revealed evidence, routing and answer surfaces enter with a short fade/translate
- connection state may pulse while checking
- buttons use small press/hover feedback
- no background animation runs continuously
- `prefers-reduced-motion` collapses transitions and animations

The desired effect is product responsiveness, not visual spectacle.

## Accessibility

The final surface requires:

- semantic buttons, labels and status regions
- visible `:focus-visible` treatment
- minimum 44px primary touch targets
- no critical state communicated by color alone
- safe wrapping for long IDs, names, claims and evidence passages
- reduced-motion support
- source links accessible on both author and responder sides
- the prototype boundary visible on mobile as well as desktop

## Product boundaries

The interface must not imply:

- production NSosyal integration
- universal web fact checking
- a generic source/reputation score
- hidden psychological profiling
- durable multi-instance state when the configured backend is process-local

The public product surface describes the capability. Detailed jury choreography, defense notes
and presentation strategy stay in the private BEYMAX repository.
