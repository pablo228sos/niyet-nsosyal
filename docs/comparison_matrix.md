# Prior-work comparison matrix

This table is for report preparation. A blank or `not established` entry is safer than guessing what another system does internally.

| Capability | Standard social feed | CrowdSTAR | Reciprocal recommender systems | NIYET prototype |
| --- | --- | --- | --- | --- |
| Main object | content | task/question to user | person-to-person match | response-seeking intent to responder |
| Topic/expertise relevance | common ranking signal, platform-specific | yes | model-specific | yes |
| Mutual/willing interaction | not required for a view | availability is considered | core requirement | explicit willing intent + opt-in |
| Temporary availability | platform-specific | yes, social availability | model-specific | active state + attention budget |
| Hard responder capacity | not established | not established in cited paper | model-specific | yes |
| Batch allocation across competing requests | not established | not established in cited paper | not a defining property of RRS | yes, current core experiment |
| Can leave weak request unmatched | platform-specific | routing threshold/details system-specific | model-specific | yes, minimum score + dummy assignment |
| Outcome target | usually engagement/relevance, platform-specific | task routing quality | successful reciprocal match | useful/resolved interaction is planned product signal |
| Load concentration metric | platform-specific | not established in cited paper | research challenge dependent | load Gini + overload count |

Sources:
- CrowdSTAR: Nushi et al., ICWE 2015, DOI 10.1007/978-3-319-19890-3_15
- Reciprocal recommender systems: Palomares et al., Information Fusion 69 (2021), DOI 10.1016/j.inffus.2020.12.001

## Novelty statement we can defend

NIYET does not claim to invent expert routing, reciprocal recommendation, availability modeling or fairness research.

The project tests a narrower system design: after response-seeking detection and candidate retrieval, several open requests compete for limited responder capacity in one allocation step. The optimizer tries to avoid locally good choices that reduce the total quality of the remaining assignments.

That claim is only valuable if the final benchmark shows a measurable difference from greedy routing under realistic capacity conflicts. Until then, it is a technical hypothesis with a working implementation.
