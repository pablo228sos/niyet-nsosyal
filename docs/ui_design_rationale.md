# UI design rationale

The prototype is designed as an integration inside a social feed, not as a separate AI dashboard.

## Host product first

Public NSosyal web and app material shows a conventional social product structure around feed content, search, discovery, communities, profiles and real-time interaction. The public web product has also used left-side navigation and search/trend surfaces. We therefore keep the host interface visually quiet and familiar.

We do not claim that the prototype is a pixel-perfect copy of the current private or authenticated NSosyal application. It is an NSosyal-inspired concept integration built from public product patterns.

## Where NIYET becomes visible

NIYET should appear only when the product has a reason to interrupt the normal feed flow.

The prototype uses a stronger visual language in three places:

1. response-needed suggestion below the composer
2. matched request in the NIYET inbox
3. transparent match explanation sheet

These surfaces use a moving gradient border, a small animated orb and short reveal transitions. The rest of the social interface avoids decorative motion.

## Why we did not use full-page WebGL

We reviewed visual techniques such as WebGL effects, liquid-metal surfaces, animated borders and AI orbs. Full-page effects can create a stronger first impression but do not explain the product and can make a social-network integration look less credible.

For this prototype we use the interaction patterns, not the spectacle:

- Beam-style animated border only on AI surfaces
- panel reveal and state transitions inspired by modern product micro-interactions
- small orb as a persistent NIYET identity
- morphing states after accept, skip and outcome actions

This keeps the visual distinction between normal NSosyal behavior and AI-assisted routing clear.

## Bilingual interface

English is the default prototype language because the technical report and planned pitch are in English. Turkish can be enabled from the header without reloading the page.

The bilingual UI does not imply bilingual model evaluation. The first model evaluation scope remains Turkish.

## Accessibility

The interface includes:

- visible keyboard focus
- semantic buttons and form labels
- an `aria-live` status toast
- Escape and backdrop close behavior for the explanation dialog
- reduced-motion support through `prefers-reduced-motion`
- no critical state communicated by color alone
- responsive mobile navigation

## Demo behavior

The prototype uses clearly marked demo data. The user can test three composer cases:

- a help request
- a collaboration request
- a normal post that should not activate NIYET

This makes the response-needed gate understandable during a short jury demo without pretending to use production NSosyal data.
