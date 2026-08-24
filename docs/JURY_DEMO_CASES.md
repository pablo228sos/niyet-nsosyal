# DRSK jury demo cases

These inputs are frozen for the controlled release. They do not depend on live web search. The only evidence source used by SOURCECHAIN is the stored PubMed demo document.

## Case 1 — Opinion stays outside factual verification

- **INPUT POST:** `I think this movie is terrible.`
- **EXPECTED SOURCECHAIN RESULT:** `OPINION`; no factual evidence required.
- **EXPECTED DISTORTION:** none.
- **EXPECTED RESOLUTION PATH:** `NONE`.
- **EXPECTED NIYET BEHAVIOR:** no automatic SOURCECHAIN escalation.
- **SOURCE USED:** none.
- **FALLBACK ACTION IF NETWORK/UI FAILS:** `python -m pytest tests/sourcechain/test_core.py::test_hostile_language_gate_and_code_switching_cases tests/test_drsk_resolution.py::test_opinion_requires_no_resolution -q`

## Case 2 — Real source, causality and attribution shift

- **INPUT POST:** `According to WHO, drinking coffee causes lower mortality.`
- **EXPECTED SOURCECHAIN RESULT:** `PARTIAL`; the passage remains visible and citation-first.
- **EXPECTED DISTORTION:** `CAUSALITY_SHIFT` and `ATTRIBUTION_SHIFT` (source mismatch).
- **EXPECTED RESOLUTION PATH:** `BOTH`.
- **EXPECTED NIYET BEHAVIOR:** structured human interpretation request is created; an unmatched result is allowed when no responder clears the current relevance threshold.
- **SOURCE USED:** PubMed PMID 26572796, *Association of Coffee Consumption With Total and Cause-Specific Mortality in 3 Large Prospective Cohorts*, Circulation, 2015-12-15. Stored passage: `Higher consumption of total coffee, caffeinated coffee, and decaffeinated coffee was associated with lower risk of total mortality.`
- **FALLBACK ACTION IF NETWORK/UI FAILS:** `python -m pytest tests/sourcechain/test_demo_corpus.py tests/sourcechain/test_distortions.py::test_source_mismatch_is_typed_and_unknown_is_not_reputation -q`

## Case 3 — Distortion Lens strength change

- **INPUT POST:** `Research proves drinking coffee causes lower mortality.`
- **EXPECTED SOURCECHAIN RESULT:** `PARTIAL` against the stored association passage.
- **EXPECTED DISTORTION:** `CAUSALITY_SHIFT`; the UI shows passage → typed distortion → claim. The release does not claim automatic multi-hop repost lineage reconstruction.
- **EXPECTED RESOLUTION PATH:** `BOTH`.
- **EXPECTED NIYET BEHAVIOR:** human interpretation request is produced from the claim, evidence status and distortion type.
- **SOURCE USED:** the same controlled PubMed PMID 26572796 passage as case 2.
- **FALLBACK ACTION IF NETWORK/UI FAILS:** `python -m pytest tests/sourcechain/test_distortions.py::test_distortion_lens_finds_numeric_causality_certainty_and_temporal_shifts tests/test_drsk_resolution.py::test_causality_distortion_requires_evidence_and_human_interpretation -q`

## Case 4 — Insufficient evidence escalates to a relevant human

- **INPUT POST:** `ESP32 sensors always detect obstacles at 50 meters.`
- **EXPECTED SOURCECHAIN RESULT:** `INSUFFICIENT`; no source or quotation is invented.
- **EXPECTED DISTORTION:** none because there is no relevant controlled passage.
- **EXPECTED RESOLUTION PATH:** initial `DEFERRED`; after **Ask a relevant person**, `HUMAN`.
- **EXPECTED NIYET BEHAVIOR:** structured context routes to `r_hardware` / Hardware Builder under the default demo state.
- **SOURCE USED:** none.
- **FALLBACK ACTION IF NETWORK/UI FAILS:** `python -m pytest tests/test_drsk_orchestrator.py::test_real_sourcechain_to_niyet_path_is_executable -q`

## Case 5 — Shared capacity

- **INPUT POST:** first `ESP32 üzerindeki ultrasonik sensör bazen sıfır okuyor. Güç mü bağlantı mı kontrol etmeliyim?`, then `18650 pil paketi motor yükteyken voltajı aniden düşürüyor. Neyi ölçmeliyim?`
- **EXPECTED SOURCECHAIN RESULT:** evidence may be insufficient; this scene demonstrates NIYET allocation rather than a truth verdict.
- **EXPECTED DISTORTION:** none required.
- **EXPECTED RESOLUTION PATH:** human routing path for response-seeking posts.
- **EXPECTED NIYET BEHAVIOR:** requests are allocated in one bounded window; a one-slot responder cannot be assigned twice. Accept consumes the displayed browser-session slot; Pause excludes the responder from later allocation.
- **SOURCE USED:** none.
- **FALLBACK ACTION IF NETWORK/UI FAILS:** `python -m pytest tests/test_runtime.py::test_batch_routing_respects_shared_capacity tests/test_optimizer.py -q`

## Case 6 — Turkish and mobile presentation

- **INPUT POST:** `Araştırma X ile Y arasında ilişki buldu; gönderi X'in Y'ye neden olduğunu söylüyor.`
- **EXPECTED SOURCECHAIN RESULT:** factual/mixed controlled baseline; use case 2 for the source-backed jury claim.
- **EXPECTED DISTORTION:** association→causation rule is covered in Turkish regression tests.
- **EXPECTED RESOLUTION PATH:** depends on retrieved controlled evidence; no evidence means `DEFERRED` until human help is requested.
- **EXPECTED NIYET BEHAVIOR:** Turkish labels remain readable; mobile responder view remains reachable.
- **SOURCE USED:** none unless the controlled coffee passage is retrieved.
- **FALLBACK ACTION IF NETWORK/UI FAILS:** run case 2 in Turkish mode, then `python -m pytest tests/sourcechain/test_distortions.py::test_association_to_causation_is_conflicting_and_flagged_in_english_and_turkish -q`

## 90–120 second order

1. Case 1: show that opinion is not fact-checked.
2. Case 2: open the exact passage and PubMed source; point to both typed shifts and `BOTH`.
3. Case 4: show honest insufficiency, then ask Hardware Builder.
4. Case 5: show shared capacity and the responder side.
5. Switch TR/EN and narrow the viewport to show the same controls without horizontal overflow.
