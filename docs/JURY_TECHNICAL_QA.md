# DRSK technical jury Q&A

## 1. Is SOURCECHAIN a fact checker?

No. It compares bounded claims with supplied passages and reports support, conflict, insufficiency and wording shifts.

## 2. Does DRSK decide what is true?

No. DRSK selects an evidence, human, combined, none or deferred path. It never emits an absolute truth score.

## 3. What is actually innovative?

The evidence relationship is actionable: SOURCECHAIN preserves provenance and distortion, then DRSK converts unresolved interpretation into a structured NIYET request under willingness and capacity constraints.

## 4. Why not just use an LLM with web search?

An LLM answer can blur quotation, inference and source. This prototype stores the exact passage, URL, hash, relation and cited evidence ID before explaining or escalating.

## 5. How do you prevent hallucinated sources?

The release uses only an explicit controlled corpus. EvidenceBundle fields come from stored SourceDocument objects, the API validates public HTTP(S) provenance, and the UI renders text without interpreting HTML.

## 6. Why is SOURCEBENCH-TR only 15 examples?

It is a development regression set created to exercise contracts and edge cases. It is explicitly not presented as a population-scale benchmark.

## 7. What does 3/4 alignment mean?

Three development examples match their labels. The miss is a Turkish paraphrase with lexical score 0.2222; the rule baseline returns partial support where the defensible gold label is support. We retained the miss instead of overfitting one example.

## 8. What is controlled evidence?

Evidence documents are supplied, bounded and stored in advance. The current default corpus contains one verified PubMed demo source and performs no arbitrary network fetch.

## 9. Why is production web retrieval not enabled?

Secure retrieval needs DNS/IP and redirect checks, MIME and byte limits, timeouts, sanitization, persistence and monitoring. Disabling it keeps the prototype's evidence boundary honest and avoids SSRF.

## 10. How does SOURCECHAIN actually connect to NIYET?

The adapter transfers claim text, derived topic, evidence status, distortion types and requested resolution into NIYET retrieval, eligibility, willingness, capacity and allocation.

## 11. Why is NIYET different from a recommender?

It routes explicit response intent to people who declared willingness and still have attention capacity. A relevant but unwilling or exhausted responder is ineligible.

## 12. Why global allocation instead of greedy?

Greedy decisions can consume a scarce responder too early. Global allocation considers the bounded request window together; at floor 0.02 it raised reviewed coverage from 65.62% to 78.12% in the frozen benchmark.

## 13. What happens with conflicting evidence?

Passages remain separate and visible. DRSK chooses `BOTH`, preserving evidence while requesting human interpretation.

## 14. What happens when AI does not know?

SOURCECHAIN returns `INSUFFICIENT`; it does not invent a passage. DRSK defers or routes a structured human request when requested.

## 15. How is responder overload prevented?

Willingness is a hard eligibility rule, capacity creates finite allocation slots, duplicate IDs are rejected, and Accept/Pause update the prototype's browser-session state.

## 16. What is Evidence Lineage?

The current baseline counts supplied independent origin-cluster IDs. Automatic discovery of common origins and repost lineage is planned, not claimed as complete.

## 17. What is Distortion Lens?

It compares a claim with its evidence passage and exposes typed numeric, temporal, scope, certainty, causality and attribution changes. This release is single-hop.

## 18. How do you detect association→causation?

Deterministic multilingual rules detect causal language in the claim and association language without causal language in the passage. Alignment then preserves the relationship as partial/conflicting rather than support.

## 19. What is currently NOT production-ready?

General web retrieval, authentication, durable multi-user capacity, platform rate limiting, automatic lineage discovery, large SOURCEBENCH evaluation and real NSosyal integration.

## 20. What would NSosyal integration require?

Authorized platform APIs, identity and consent, server-side persistence, moderation/privacy review, observability, abuse controls, secure retrieval and measured pilots with representative traffic.

## Evidence discipline

The strongest reproducible claims are indexed in `docs/FINAL_EVIDENCE_PACK.md`. The usability aggregates are team-documented but cannot be independently recomputed because de-identified row-level observations are not in the repository.
