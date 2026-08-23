# UI design rationale

The prototype is designed as an integration inside a social feed, not as a separate AI dashboard.

## Host product first

Public NSosyal web and app material shows a conventional social product structure around feed content, search, discovery, communities, profiles and real-time interaction. We therefore keep the host interface visually quiet and familiar.

We do not claim that the prototype is a pixel-perfect copy of the current private or authenticated NSosyal application. It is an NSosyal-inspired concept integration built from public product patterns.

The primary navigation is functional in the prototype. Feed returns to the real NIYET composer and interaction flow; Explore, Communities, Messages and Profile open lightweight concept surfaces. This avoids presenting decorative controls as working product navigation.

## Two sides of the interaction

NIYET has an author side and a responder side. Both need to be visible because routing quality and responder capacity are part of the same product decision.

On desktop the responder inbox is kept in the right rail. On mobile that rail becomes an explicit responder drawer rather than disappearing at the responsive breakpoint. The main route result also provides a direct action to open the responder view.

A short role label distinguishes Author side from Responder side so Accept, Skip, Pause and capacity do not look like controls belonging to the person who wrote the request.

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
- state changes after Accept, Skip and routing actions

This keeps the visual distinction between normal NSosyal behavior and AI-assisted routing clear.

## Bilingual interface

English is the default prototype language because the technical report and planned pitch are in English. Turkish can be enabled from the header without reloading the page.

Static labels and dynamic routing states use the same translation source. Match reasons returned by the Python API are localized at the presentation layer so switching language does not leave mixed English/Turkish result cards.

The bilingual UI does not imply bilingual model evaluation. The first model evaluation scope remains Turkish.

## Feed actions

Posts created inside the prototype use the same reply, repost, like and share icon system as the static feed examples. These actions are intentionally lightweight demo interactions, but they behave consistently instead of leaving a user-created post visually incomplete.

## Accessibility

The interface includes:

- visible keyboard focus
- semantic buttons and form labels
- accessible live status regions
- Escape and backdrop close behavior for the explanation dialog
- reduced-motion support through `prefers-reduced-motion`
- no critical state communicated by color alone
- responsive mobile navigation
- a mobile responder drawer so responder controls remain reachable on small screens

## Demo state

The browser stores a small amount of session state to demonstrate open requests and remaining responder capacity. A versioned reset prevents old prototype sessions from carrying stale queues or exhausted capacity into a later release. A visible Reset demo action is also available on desktop.

This is prototype state, not production persistence.

## Demo behavior

The prototype uses clearly marked demo data. The user can test three composer cases:

- a help request
- a collaboration request
- a normal post that should not activate NIYET

The user can also manually activate NIYET after a response-gate miss. This makes both false-positive and false-negative recovery visible without pretending to use production NSosyal data.
