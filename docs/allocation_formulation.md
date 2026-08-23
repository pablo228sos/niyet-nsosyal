# Allocation formulation

NIYET does not claim a new optimization algorithm. The current prototype uses a standard linear assignment solver after candidate retrieval. Our contribution is the product formulation around limited responder capacity and the way this step is connected to response-seeking social posts.

## Inputs

For one bounded allocation window:

- open response-seeking intents `i`
- eligible responders `j`
- responder capacity `c_j`
- candidate edge utility `u_ij`

An edge is created only after:

1. the post passes the response-needed gate
2. the user confirms the interaction intent
3. the responder has opted into that intent type
4. the responder has remaining attention capacity
5. topic relevance clears the retrieval quality floor

An invalid edge is not passed to the optimizer.

## Development edge utility

The current transparent baseline uses three normalized signals:

`u_ij = (topic_relevance + willingness + availability) / 3`

This is a development utility, not a calibrated probability.

In the current prototype:

- `topic_relevance` comes from the deployed lexical retrieval baseline
- `willingness` is explicit compatibility with the requested interaction type
- `availability` is remaining attention slots divided by the daily budget

The equal weights are intentional. We do not have outcome data that would justify learned weights yet. A later production version can calibrate the utility from accepted, skipped, useful and resolved outcomes.

## Assignment objective

The allocator chooses binary assignments `x_ij`:

`maximize sum(u_ij * x_ij)`

subject to:

`sum_j x_ij <= 1` for each open intent

`sum_i x_ij <= c_j` for each responder

`x_ij = 0` for any edge that failed eligibility or the quality threshold

`x_ij in {0, 1}`

The current implementation represents responder capacity as repeated assignment slots and uses SciPy's linear assignment solver. Dummy columns with zero utility allow an intent to remain unmatched.

## Why batch allocation can matter

A greedy method can make the best local choice and still reduce the total quality of the batch.

Example:

| | R1 | R2 |
| --- | ---: | ---: |
| I1 | 0.99 | 0.98 |
| I2 | 0.97 | 0.10 |

Both responders have capacity 1.

A greedy choice can spend R1 on I1 and leave I2 with R2. Global assignment instead gives R2 to I1 and R1 to I2.

This example is a unit test of the allocation logic. It is not evidence that real social interaction improves by the same amount.

## Threshold rule

Quality thresholds must be applied before optimization.

If a below-threshold edge is allowed to influence the assignment and removed only afterwards, it can block a different valid solution. The regression test in `tests/test_optimizer.py` covers this case.

The runtime also applies a topic-relevance floor before allocation. This was added after the first matching benchmark draft showed that a global optimizer can increase coverage by spreading weak candidates if retrieval is too permissive.

## Scaling boundary

The dense assignment solver is not intended to run over the complete NSosyal network.

The production sequence is:

`retrieval -> small eligible candidate graph -> allocation`

The current dense implementation is suitable for bounded batches. Larger windows can use a sparse min-cost-flow formulation without changing the product-level constraints.
