# DRSK documentation

This directory is the evidence trail behind the public README.

## Start here

1. [DRSK architecture](DRSK_ARCHITECTURE.md) — system contracts and ownership boundaries.
2. [Demo guide](DRSK_DEMO.md) — reproducible EVIDENCE / HUMAN / BOTH / NONE scenarios and the final judge flow.
3. [Product flow](product_flow.md) — author, evidence, consent, NIYET and responder lifecycle.
4. [Engineering journey](ENGINEERING_JOURNEY.md) — how the prototype changed after real browser, retrieval and two-device failures.
5. [Safety and failure modes](safety_and_failure_modes.md) — fail-closed behavior and known production requirements.
6. [SOURCECHAIN model card](SOURCECHAIN_MODEL_CARD.md) — intended use, provider boundary and limitations.
7. [SOURCEBENCH-TR dataset card](SOURCEBENCH_TR_DATASET_CARD.md) — SOURCECHAIN development regression set.
8. [Allocation formulation](allocation_formulation.md) — capacity-aware assignment formulation.
9. [UI design rationale](ui_design_rationale.md) — why DRSK is presented as a social capability rather than an AI dashboard.
10. [Runtime provider setup](runtime_provider_setup.md) — Tavily/Brave evidence providers and Upstash shared state.

## Product proof

Final judge screenshots live in [screenshots/](screenshots/):

- `01_live_coffee_conflict.png` — claim/evidence conflict and causality shift;
- `02_live_routed_research_reviewer.png` — explicit NIYET routing;
- `03_live_responder_accept.png` — responder inbox with shared evidence context;
- `04_live_resolved.png` — answer returned to the original post;
- `05_live_four_states.png` — EVIDENCE / HUMAN / BOTH / NONE in the shared feed.

These are captures of the working `/live` prototype, not design mockups.

## Reproducibility

Use the scripts in [`../experiments/`](../experiments/) and [`../scripts/`](../scripts/) rather than copying numbers out of documentation.

The final stabilization pass completed with 57 targeted tests and 283 full-suite tests, plus JavaScript syntax, site build and extension packaging checks.

Model and retrieval metrics in the documentation remain development/offline measurements. They are not represented as population-level NSosyal performance.
