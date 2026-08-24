# DRSK report-to-code traceability

Source reviewed: `DRSK_Technical_Report_2026.docx` (126 paragraphs, 13 tables).

This matrix is deliberately time-aware. The report describes the state at submission; this repository contains later implementation work. A report item marked “planned” is therefore not silently rewritten as a historical implementation claim.

Status definitions:

- **VERIFIED** — present and executable in the repository, or accurately described as historical/report-time state.
- **PARTIAL** — a bounded baseline exists, but not the full capability described.
- **PLANNED** — the report explicitly presents future work that remains unimplemented.
- **NOT VERIFIED** — the repository does not contain enough evidence to reproduce the claim.

| Report location | Report claim | Status | Repository evidence / boundary |
| --- | --- | --- | --- |
| ¶21–31, Table 0 | DRSK combines SOURCECHAIN, NIYET and a Resolution layer; SOURCECHAIN and Resolution were targets at submission | VERIFIED | `src/sourcechain/`, `src/niyet/`, `src/drsk/`; report-time “planned” wording is historically accurate and the components were implemented later |
| ¶42 | Distortion Lens covers numeric, causality, certainty and attribution shifts | PARTIAL | `src/sourcechain/structured_checks.py` and tests implement typed single-hop checks; the product does not yet infer or visualize arbitrary multi-hop mutation chains |
| ¶43 | Source mismatch and provenance should remain visible | VERIFIED | `src/sourcechain/mismatch.py`, immutable `EvidenceItem` URL/passage/hash fields, and provenance rendering in `web/app.js` |
| ¶44 | Evidence Lineage is an engineering hypothesis to validate | PARTIAL | `src/sourcechain/lineage.py` counts supplied `origin_cluster_id` values; automatic origin discovery/clustering and lineage reconstruction are not implemented |
| ¶50 | Cached evidence bundles and later re-evaluation are planned | PLANNED | Bundles are deterministic and versioned in memory, but durable cache/re-evaluation jobs do not exist |
| ¶52, Table 0 | SOURCECHAIN modules would be added after report preparation | VERIFIED | The statement is accurate for the report snapshot; the later baseline now lives in `src/sourcechain/` |
| ¶53 | Production queue and persistence are planned | PLANNED | Current API execution is synchronous and browser capacity is session-local |
| ¶54 | Secure arbitrary-URL ingestion is future work | PLANNED | Live arbitrary fetching remains disabled; controlled corpus only |
| ¶60 | SOURCEBENCH v1 target is at least 300 statement, 300 alignment, 100 mismatch and 120 mutation examples | PLANNED | `data/sourcebench_tr/` is a 15-example development regression set, not SOURCEBENCH v1 |
| ¶62, Table 7 | The report makes no measured SOURCECHAIN performance claim | VERIFIED | Historically accurate. `experiments/evaluate_sourcechain_v0.py` now measures the later 15-example development baseline and labels it development-only |
| ¶64 | UI Level 3 includes a Distortion Lens | PARTIAL | The feed renders evidence relation and typed distortion badges; a full transformation-chain visualization is not present |
| ¶69 | A user pilot was planned and no result was claimed in the report | NOT VERIFIED | The repository documents a later eight-participant study and five-session retest, but contains templates/protocols rather than de-identified row-level study records sufficient for independent reproduction |
| Table 3 | SOURCECHAIN model and hybrid retrieval are planned | PARTIAL | Deterministic statement rules, lexical controlled retrieval and structured checks are implemented; no trained SOURCECHAIN model or hybrid production retriever is shipped |
| Table 4 | Historical NIYET controlled-data metrics are reported | VERIFIED | `scripts/train_intent_baseline.py`, pinned constraints and tests reproduce the controlled evaluation path |
| Table 7 | SOURCECHAIN metrics were planned | VERIFIED | Accurate at report time; a small development-only evaluator now exists and does not claim benchmark-grade validity |
| Table 11 | Timing/scale checks were planned after the report | VERIFIED | `experiments/benchmark_scaling.py`, `experiments/scaling_results_v1.md` and allocation benchmarks provide later engineering measurements |
| Table 0 | Resolution Engine was planned | VERIFIED | `src/drsk/resolution.py` implements explicit EVIDENCE/HUMAN/BOTH/NONE/DEFERRED policy with tests |
| Table 0 | Transparency tools were planned | PARTIAL | Citation-first bundles, explanations and distortion badges exist; full lineage and multi-hop lens tooling remain incomplete |

## Audit totals

- VERIFIED: 8
- PARTIAL: 5
- PLANNED: 4
- NOT VERIFIED: 1
- Direct report/code contradictions: 0
- Report-time planned items whose implementation state later changed: 6
- Repository evidence gaps affecting an empirical claim: 1 (later usability study raw records)

The principal risk is not a contradiction in the report. It is reading time-stamped “planned” statements as if they described the current repository, or reading small deterministic regression results as mature SOURCECHAIN model validation.
