# NIYET interface system

## Direction

A working social surface for NSosyal readers, authors and willing responders.
The 2026 redesign opens directly on the feed. Evidence and human routing remain
the product; there is no marketing gate. Variance 4, motion 2, density 5.

The supplied NIYET UI Assets Pack is the primary visual source. Dark research
surfaces, blue/violet illumination limited to introductions, and a quiet
three-column workspace preserve operational clarity. Every supplied file is
accounted for in `docs/ASSET_INVENTORY.md`. References are never rendered as UI.

## Tokens

| Role | Light | Dark |
| --- | --- | --- |
| Canvas | #f4f6fa | #090d16 |
| Surface | #ffffff | #101623 |
| Text | #18233b | #eef2ff |
| Secondary text | #54627a | #a1aec7 |
| Border | #d3dce9 | #29354b |
| Action text | #3e50b4 | #a6b8ff |
| Evidence | #167163 | #86daca |

Filled actions use white text on #5668de (dark) or #4457cb (light). Semantic
statuses always include a label, icon and explanation. Dark is the brand default;
the shared appearance toggle persists an explicit light/dark choice.

Typography: Segoe UI/system sans for readable native rendering without network
fonts; Consolas for technical values. Body 16px, controls 14–16px, secondary
metadata 12–13px. Display 28–38px; lab heading up to 48px. No dot-matrix body copy.

Use 8px control/surface corners, 12px avatars/dialogs and fully rounded switches.
Spacing follows 8/12/16/20/24/28/32px roles. Shadows are reserved for overlays.

## Composition and state

- Desktop: 184px navigation, flexible feed up to 720px, 300px response space.
- Tablet: response space becomes an accessible drawer.
- Mobile: one column, bottom navigation and a labeled responder action.
- Source details reveal progressively and retain verbatim passages and URLs.
- Unavailable evidence is not false; empty allocation is not fabricated success.
- Technical diagnostics stay behind a keyboard-accessible dialog.
- Lab pairs the same real query batch and capacity in both methods.
- Session-only data and unconnected social surfaces are explicitly identified.
- SOURCECHAIN has a five-step explanatory path and a payload-driven evidence trail.
- EVIDENCE / HUMAN / BOTH / NONE / DEFERRED retain engine semantics with plain labels.
- Long comparisons, full provenance and original analysis notes expand independently.
- Loading, cancellation, retry and empty-search recovery are visible and keyboard usable.

## References applied

- Vercel Web Interface Guidelines: semantics, focus, forms, URLs, reduced motion,
  overflow, errors and async state audit.
- Taste Skill: audit-first redesign, restrained surfaces, coherent type and tokens.
  Its marketing-only layout rules do not replace operational product requirements.
- Image-to-Code: supplied desktop/mobile composition references are the visual source
  for this pass; no new generated assets replace the user's pack.
- Awesome Design MD / Intercom analysis: conversational clarity and friendly blue
  action emphasis, adapted to DRSK rather than copying an unrelated product.

Sources: https://github.com/vercel-labs/web-interface-guidelines,
https://www.tasteskill.dev/, https://github.com/voltagent/awesome-design-md,
https://getdesign.md/intercom/design-md.
