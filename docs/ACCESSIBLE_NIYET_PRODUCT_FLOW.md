# Accessible NIYET Product Flow Specification

Resolves issue **#5** (*Build the first accessible NIYET product flow*).

This document establishes the interaction architecture, component contracts, accessibility invariants, and verification suite for the first accessible NIYET product flow.

---

## Product Philosophy: Integration Without Emulation

The product flow intentionally lives **inside** the host social context without pretending to be a separate social network or an AI spectacle:
1. The post composer accepts normal social discourse (status, media, questions, claims).
2. The response-needed gate runs non-intrusively without interrupting the typing flow.
3. When a response is likely needed, an accessible suggestion panel suggests an intent (`ASK`, `FEEDBACK`, `COLLABORATE`, `DISCUSS`).
4. The author retains full agency: they can accept the suggestion, override the intent, or dismiss the panel.
5. The routed request card presents transparent routing reasons and development utility.
6. The responder retains hard attention boundaries with server-authoritative **Accept**, **Skip**, and **Pause/Resume**.
7. Outcome feedback is communicated through accessible live regions and clear visual hierarchy.

---

## 7 Core Interaction Stages

```text
[1. Normal Post Composer]
       │
       ▼ (live text inspection)
[2. Response-Needed Suggestion] ──(Not now)──► [Standard Feed Post]
       │
       ▼ (Author confirms or overrides intent)
[3. Intent Confirmation / Override]
       │
       ▼ (Route with NIYET)
[4. Routed Request Card]
       │
       ▼ (Candidate matching & budget validation)
[5. Responder Lifecycle Controls]
       ├── Accept ──► Consumes 1 slot, opens answer editor
       ├── Skip   ──► Preserves capacity, excludes candidate, reallocates
       └── Pause  ──► Toggles routing eligibility
       │
       ▼
[6. Response Submission & Shared Context]
       │
       ▼
[7. Author Outcome Feedback & Resolution State]
```

### Stage 1: Normal Post Composer
- **Element:** `<textarea id="composerText">`
- **Accessibility:**
  - Semantic label `<label id="composerLabel" for="composerText">`
  - Explicit character limit (`maxlength="1200"`)
  - Live accessible character count via `<output id="characterCount">`
  - Screen reader description via `aria-describedby="composerHelp composerError"`
  - High-contrast visible focus ring adhering to WCAG 2.4.7

### Stage 2: Response-Needed Suggestion
- **Element:** `<div class="intent-panel ai-surface" id="intentPanel">`
- **Accessibility:**
  - Polite live region announcement via `aria-live="polite"`
  - Clear heading: `"This post may need a human response"`
  - Subtext: `"NIYET suggests an intent. You confirm before routing."`
  - Model confidence disclaimer preventing overclaiming

### Stage 3: Author Intent Confirmation / Override
- **Elements:**
  - `<button class="intent-choice" data-intent="ask">ASK</button>`
  - `<button class="intent-choice" data-intent="feedback">FEEDBACK</button>`
  - `<button class="intent-choice" data-intent="collaborate">COLLABORATE</button>`
  - `<button class="intent-choice" data-intent="discuss">DISCUSS</button>`
- **Accessibility:**
  - Interactive toggle buttons with `type="button"` and `aria-pressed="true|false"`
  - Keyboard navigation via Tab / Shift+Tab and Enter / Space
  - Dismiss action `<button id="dismissIntent">` ("Not now")
  - Action confirmation `<button id="routeIntent">` ("Route with NIYET")

### Stage 4: Routed Request Card
- **Element:** `<div class="match-card ai-surface" id="matchState">`
- **Accessibility:**
  - Type indicator `<span class="match-type" id="matchType">`
  - Match status `<span class="match-score status" id="matchStatus">`
  - Post preview `<p id="matchPostText">`
  - Transparent match reasons list `<div class="match-reasons" id="matchReasons">`
  - Technical details modal trigger `<button id="explainMatch">`

### Stage 5: Responder Lifecycle Controls
- **Elements:**
  - `<button class="accept-btn" id="acceptMatch">Accept</button>`
  - `<button class="skip-btn" id="skipMatch">Skip</button>`
  - `<button class="switch" id="routingSwitch" aria-label="Toggle NIYET routing">`
- **Accessibility:**
  - Minimum 44×44px touch targets conforming to WCAG 2.5.5
  - Distinct `:focus-visible` styling preventing keyboard traps
  - Non-color-only state representation (icons, pressed states, text labels)
  - Capacity progress bar with explicit text alternative `<strong class="budget-count" id="budgetCount">`

### Stage 6 & 7: Outcome Feedback & Resolution State
- **Element:** `<div class="route-result" id="routeResult" aria-live="polite">`
- **Accessibility:**
  - Real-time updates delivered to screen readers via `aria-live="polite"`
  - Clear distinction between human answers and verified evidence
  - Persistent state allowing recovery upon page reload

---

## WCAG 2.1 AA Compliance Matrix

| Criterion | Requirement | Implementation in NIYET Flow |
| --- | --- | --- |
| **1.3.1 Info and Relationships** | Semantic markup | `<label>`, `<textarea>`, `<button>`, `<output>`, ARIA landmarks |
| **1.4.3 Contrast (Minimum)** | Contrast $\ge 4.5:1$ text | System colors: `--color-text-main`, `--color-bg-canvas`, dark/light tokens |
| **2.1.1 Keyboard** | Full keyboard operation | All actions reachable via Tab/Shift+Tab and executable with Enter/Space |
| **2.4.7 Focus Visible** | Visible focus indicator | Explicit `:focus-visible` outline rings across all controls in `design-system.css` |
| **2.5.5 Target Size** | Minimum 44×44px | Touch targets conform to `min-height: 44px` across all action buttons |
| **4.1.2 Name, Role, Value** | Accessible states | `aria-live="polite"`, `aria-pressed`, `aria-expanded`, `aria-label` |
| **2.3.3 Animation from Interactions** | Respect user preferences | `@media (prefers-reduced-motion: reduce)` disables non-essential animations |

---

## Verification

The accessible product flow contracts are permanently verified by:

```bash
pytest tests/test_accessible_product_flow.py
pytest tests/test_web_ui_contract.py
```
