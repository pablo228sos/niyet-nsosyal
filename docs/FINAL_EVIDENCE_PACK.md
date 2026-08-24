# DRSK final evidence pack

This is the jury-facing index for the release-frozen controlled prototype. Run commands from the repository root after installing the pinned project dependencies.

| Claim / criterion | Evidence artifact | Reproduction command |
| --- | --- | --- |
| NIYET response-needed gate | `src/niyet/runtime.py`, `tests/test_runtime.py`, controlled gate data | `python -m pytest tests/test_runtime.py::test_normal_post_does_not_enter_routing -q` |
| NIYET intent classification/confirmation | `src/niyet/classifier.py`, `tests/test_runtime.py` | `python -m pytest tests/test_runtime.py::test_manual_intent_can_override_false_negative_gate -q` |
| Reviewed retrieval benchmark | `data/matching_benchmark_v1_reviewed.json`, `results/niyet_retrieval_reviewed.json` | `python -m pytest tests/test_reviewed_benchmark_metrics.py -q` |
| Global allocation result | `src/niyet/optimizer.py`, `results/niyet_allocation_reviewed.json` | `python experiments/evaluate_matching_draft.py` |
| Capacity safety | `src/niyet/runtime.py`, `tests/test_runtime.py` | `python -m pytest tests/test_runtime.py::test_batch_routing_respects_shared_capacity -q` |
| Duplicate request protection | `src/niyet/runtime.py`, `api/index.py` | `python -m pytest tests/test_runtime.py::test_batch_routing_rejects_duplicate_request_ids tests/test_api.py::test_api_rejects_duplicate_batch_ids_after_normalization -q` |
| SOURCECHAIN statement gate | `src/sourcechain/statement_classifier.py`, SOURCEBENCH statement rows | `python -m pytest tests/sourcechain/test_core.py::test_statement_gate_excludes_question_opinion_and_experience -q` |
| Atomic claim extraction | `src/sourcechain/claim_extractor.py` | `python -m pytest tests/sourcechain/test_core.py::test_claim_extraction_is_bounded_and_preserves_exact_offsets -q` |
| Evidence provenance | `src/sourcechain/schemas.py`, `src/sourcechain/evidence.py` | `python -m pytest tests/sourcechain/test_demo_corpus.py -q` |
| Claim/evidence alignment | `src/sourcechain/alignment.py`, `data/sourcebench_tr/alignment.jsonl` | `python experiments/evaluate_sourcechain_v0.py` |
| Source mismatch | `src/sourcechain/mismatch.py` | `python -m pytest tests/sourcechain/test_distortions.py::test_source_mismatch_is_typed_and_unknown_is_not_reputation -q` |
| Numeric distortion | `src/sourcechain/structured_checks.py` | `python -m pytest tests/sourcechain/test_distortions.py::test_numeric_change_and_negation_are_conflicts -q` |
| Causality distortion | `src/sourcechain/structured_checks.py` | `python -m pytest tests/sourcechain/test_distortions.py::test_association_to_causation_is_conflicting_and_flagged_in_english_and_turkish -q` |
| Certainty distortion | `src/sourcechain/structured_checks.py` | `python -m pytest tests/sourcechain/test_distortions.py::test_hedged_increase_to_unqualified_increase_is_certainty_shift -q` |
| Distortion Lens | `src/sourcechain/distortion.py`, typed badges in `web/app.js` | `python -m pytest tests/sourcechain/test_distortions.py::test_distortion_lens_finds_numeric_causality_certainty_and_temporal_shifts -q` |
| Evidence Lineage baseline | `src/sourcechain/lineage.py`; supplied origin clusters, not inferred lineage | `python -m pytest tests/sourcechain/test_core.py::test_bundle_is_citation_first_and_counts_independent_origins -q` |
| DRSK Resolution Engine | `src/drsk/resolution.py` | `python -m pytest tests/test_drsk_resolution.py -q` |
| Structured SOURCECHAIN→NIYET escalation | `src/drsk/adapter.py`, `src/drsk/orchestrator.py` | `python -m pytest tests/test_drsk_orchestrator.py -q` |
| Context changes human routing | robotics→`r_control`, NLP→`r_ml` regression | `python -m pytest tests/test_drsk_orchestrator.py::test_structured_claim_context_changes_real_niyet_routing -q` |
| UI progressive disclosure and ARIA | `web/index.html`, `web/app.js`; evidence toggle, labelled regions and mobile navigation | Follow `docs/JURY_DEMO_CASES.md` cases 1–4 in the live demo |
| English/Turkish flow | bilingual copy and status mapping in `web/app.js` | Open the live demo, switch `EN`/`TR`, then run cases 1 and 2 |
| Mobile behavior | responsive rules in `web/styles.css` and `web/app.js` | Run case 5 at 390×844; verify no horizontal overflow and open responder view |
| Security controls | bounded API parsing/state, safe provenance URLs, response headers | `python -m pytest tests/test_api.py -q` |
| SOURCEBENCH-TR v0 | 15 development-only JSONL examples, dataset card and generated result | `python scripts/validate_sourcebench.py data/sourcebench_tr && python experiments/evaluate_sourcechain_v0.py` |
| Reproducible result pack | `scripts/generate_results.py`, four JSON files in `results/` | `python scripts/generate_results.py` |
| Compact acceptance proof | `scripts/competition_check.py` | `python scripts/competition_check.py` |
| Live deployed prototype | existing Vercel project | Open `https://niyet-nsosyal.vercel.app/` and follow `docs/JURY_DEMO_CASES.md` |

## Boundaries the evidence pack does not claim

- SOURCEBENCH-TR v0 is 15 development examples, not a production benchmark.
- Distortion Lens is a typed single-hop evidence-to-claim comparison, not automatic multi-hop repost lineage reconstruction.
- Evidence Lineage counts supplied origin clusters; it does not discover common origins automatically.
- Usability aggregates are team-documented but not independently reproducible because row-level observations are not public.
- Authentication, durable capacity, rate limiting and arbitrary web retrieval are not production features of this release.
