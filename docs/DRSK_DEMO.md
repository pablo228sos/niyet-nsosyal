# DRSK demo and regression scenarios

The final judge surface supports repeated private checks and a separate explicit human-routing action. The goal is not to force every input into a strong answer. `NONE`, `INSUFFICIENT` and an unmatched human request are valid safe outcomes.

## Clean judge start

Open the final `/live` surface and press **Prepare demo** once.

This restores the canonical coffee text, clears stale author state and restores the demo responder budgets. Normal checks after that do not require another reset.

## 1 — BOTH: canonical coffee causality shift

~~~text
Research proves coffee consumption causes lower mortality. Can someone explain what the study actually shows?
~~~

Expected after **Check with DRSK**:

- no human request is created;
- SOURCECHAIN keeps the exact coffee cohort source passage visible;
- post wording says `proves / causes`;
- source wording says `associated with`;
- relation is `CONFLICTING`;
- typed signal includes `CAUSALITY_SHIFT`;
- resolution path is `BOTH`;
- responder attention remains unchanged.

Only after **Ask a relevant person**:

- NIYET creates the request;
- final demo routing selects `Research Reviewer`;
- the author card shows routing reason and remaining attention budget.

## 2 — HUMAN: practical PID question

~~~text
What will happen to a control system if you increase the Derivative coefficient (Kd) too much, while keeping the Proportional (Kp) and Integral (Ki) coefficients the same?
~~~

Expected:

- path is `HUMAN`;
- the UI does not manufacture a SOURCECHAIN `INSUFFICIENT` evidence card for a pure contextual question;
- Check opens no request and spends no capacity;
- explicit human routing remains separate.

## 3 — NONE: opinion stays ordinary

~~~text
Dark mode looks better than light mode.
~~~

Expected:

- statement is subjective/non-checkable;
- no evidence card is rendered;
- no human request is opened;
- path is `NONE`.

## 4 — EVIDENCE: supported official statement

~~~text
Regular physical activity provides significant physical and mental health benefits.
~~~

Verified fallback source: World Health Organization, `Physical activity`.

Expected on a clean controlled run:

- exact provenance is preserved;
- a supported passage can resolve through `EVIDENCE`;
- no person is needed.

Live web acquisition may produce additional candidates. The relation must remain bounded by the actual retrieved passages rather than being forced to match this expected demonstration path.

## 5 — arbitrary factual claim

Ask the judge for an unprepared factual statement and press **Check with DRSK**.

Legitimate outcomes include `SUPPORTED`, `PARTIALLY_SUPPORTED`, `CONFLICTING` and `INSUFFICIENT`.

The success criterion is coherent evidence/provenance and safe failure, not a visually convenient label. Repeated arbitrary checks must not consume responder capacity.

## 6 — full same-page human round trip

Starting from the coffee result:

1. **Ask a relevant person**.
2. Confirm routing to `Research Reviewer`.
3. Switch `Demo device` to **Responder**.
4. The responder selector follows the assigned `Research Reviewer`.
5. The coffee request is visible immediately.
6. Press **Accept**.
7. Enter an answer.
8. Send the answer.
9. Switch back to **Author**.
10. The same request refreshes to `Resolved`.
11. The exact human answer is visible.

The final acceptance pass verified this path in separate browser contexts and rechecked the responder budget after status transitions.

## 7 — separate responder device

Use **Open responder device** or **Copy responder link** after routing and open the link in a genuinely separate browser context/session.

Expected:

- explicit responder URL selects the same assigned responder;
- request and evidence context match the Author view;
- Accept / Answer works;
- the Author request reaches `Resolved`.

## 8 — real NSosyal concept adapter

Manual presentation-hardware flow:

1. open real NSosyal while logged in;
2. type a draft;
3. press DRSK for a private inspect;
4. verify no human request exists;
5. publish with NSosyal's native control;
6. wait for the exact text to be detected as a visible published post;
7. press **Ask a relevant person** only after publication;
8. open the responder device;
9. Accept and answer;
10. verify the returned answer can be restored in the extension.

On narrow/mobile widths:

- no unsafe standalone floating DRSK fallback while the composer is closed;
- composer DRSK must not cover NSosyal publish/navigation controls;
- the result uses the narrow-screen sheet/full-width treatment.

An authenticated presentation-hardware pass subsequently reached the human answer on the real NSosyal host. That pass exposed one resolved-state persistence edge case, fixed in PR #34 and covered by the final regression suite. `/live` remains the deterministic full fallback if the external host becomes unstable.

## Verification

~~~bash
python -m pip install -c constraints.txt -e . pytest
node --check web/live.js
node --check demo/nsosyal-overlay/background.js
node --check demo/nsosyal-overlay/content-v2.js
python scripts/build_site.py
python scripts/package_nsosyal_overlay.py
pytest -q
python experiments/evaluate_matching_draft.py
python experiments/evaluate_sourcechain_v0.py
python scripts/validate_annotations.py data/intent_seed_v1.csv
python scripts/validate_annotations.py data/response_gate_seed_v1.csv
python scripts/validate_sourcebench.py data/sourcebench_tr
~~~

Final acceptance result: **75 targeted tests passed** and **286 full-suite tests passed**. Runtime acceptance CI run #601 passed; later documentation-only main changes did not alter the verified runtime contracts, and current Production remains READY.
