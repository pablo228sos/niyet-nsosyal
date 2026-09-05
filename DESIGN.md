# DRSK interface system

## Direction

A working social surface for NSosyal readers, authors and willing responders.
The 2026 redesign opens directly on the feed. Evidence and human routing remain
the product; there is no marketing gate. Variance 4, motion 2, density 5.

The visual reference uses a quiet three-column layout: navigation, conversation,
response space. The code adopts its 24px rhythm, readable sans hierarchy, flat
surfaces and evidence edge. It does not adopt the reference's invented source text.

## Tokens

| Role | Light | Dark |
| --- | --- | --- |
| Canvas | #f5f7fb | #121926 |
| Surface | #ffffff | #192233 |
| Text | #17233e | #e9eef8 |
| Secondary text | #58657b | #b4bfd1 |
| Border | #d8deea | #39465c |
| Action | #2855d9 | #94b4ff |
| Evidence | #087b7b | #74d6cc |

Primary filled buttons keep white text on #2855d9 in both themes. Semantic
statuses always include words. System preference selects light/dark consistently.

Typography: Segoe UI/system sans for readable native rendering without network
fonts; Consolas for technical values. Body 16px, controls 14–16px, secondary
metadata 12–13px. Display 28–38px; lab heading up to 48px. No dot-matrix body copy.

Use 8px control/surface corners, 12px avatars/dialogs and fully rounded switches.
Spacing follows 8/12/16/20/24/28/32px roles. Shadows are reserved for overlays.

## Composition and state

- Desktop: 200px navigation, flexible feed up to 650px, 310px response space.
- Tablet: response space becomes an accessible drawer.
- Mobile: one column, bottom navigation and a labeled responder action.
- Source details reveal progressively and retain verbatim passages and URLs.
- Unavailable evidence is not false; empty allocation is not fabricated success.
- Technical diagnostics stay behind a keyboard-accessible dialog.
- Lab pairs the same real query batch and capacity in both methods.
- Session-only data and unconnected social surfaces are explicitly identified.

## References applied

- Vercel Web Interface Guidelines: semantics, focus, forms, URLs, reduced motion,
  overflow, errors and async state audit.
- Taste Skill: audit-first redesign, restrained surfaces, coherent type and tokens.
  Its marketing-only layout rules do not replace operational product requirements.
- Image-to-Code: generated working-screen reference, then composition analysis.
- Awesome Design MD / Intercom analysis: conversational clarity and friendly blue
  action emphasis, adapted to DRSK rather than copying an unrelated product.

Sources: https://github.com/vercel-labs/web-interface-guidelines,
https://www.tasteskill.dev/, https://github.com/voltagent/awesome-design-md,
https://getdesign.md/intercom/design-md.
