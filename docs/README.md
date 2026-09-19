# DRSK documentation

This directory is the evidence trail behind the public README.

## Start here

1. [Final acceptance](FINAL_ACCEPTANCE.md) — exact production status, verification matrix and remaining host-level limitation.
2. [DRSK architecture](DRSK_ARCHITECTURE.md) — system contracts and ownership boundaries.
3. [Demo guide](DRSK_DEMO.md) — reproducible EVIDENCE / HUMAN / BOTH / NONE scenarios and the final judge flow.
4. [Product flow](product_flow.md) — author, evidence, consent, NIYET and responder lifecycle.
5. [Engineering journey](ENGINEERING_JOURNEY.md) — how the prototype changed after real browser, retrieval and two-device failures.
6. [Safety and failure modes](safety_and_failure_modes.md) — fail-closed behavior and known production requirements.
7. [SOURCECHAIN model card](SOURCECHAIN_MODEL_CARD.md) — intended use, provider boundary and limitations.
8. [SOURCEBENCH-TR dataset card](SOURCEBENCH_TR_DATASET_CARD.md) — SOURCECHAIN development regression set.
9. [Allocation formulation](allocation_formulation.md) — capacity-aware assignment formulation.
10. [UI design rationale](ui_design_rationale.md) — why DRSK is presented as a social capability rather than an AI dashboard.
11. [Runtime provider setup](runtime_provider_setup.md) — Tavily/Brave evidence providers and Upstash shared state.

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

The final acceptance pass completed with 73 targeted tests and 284 full-suite tests, plus JavaScript syntax, Python compilation, site build, extension packaging, model/evaluation scripts and browser acceptance.

Model and retrieval metrics in the documentation remain development/offline measurements. They are not represented as population-level NSosyal performance.
