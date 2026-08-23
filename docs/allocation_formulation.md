# Allocation formulation

NIYET does not claim a new optimization algorithm. The prototype uses a standard linear assignment solver after retrieval and eligibility filtering. Our contribution is the social-product formulation around competing response-seeking requests and limited willing responder capacity.

## Inputs

For one bounded matching window:

- open response-seeking requests `i`
- responder candidates `j`
- remaining responder capacity `c_j`
- candidate edge utility `u_ij`

An edge exists only when:

1. the request is activated in NIYET, either by the response-needed gate plus author confirmation or by manual user activation
2. the responder is active
3. the responder has remaining capacity
4. the responder accepts the confirmed interaction type
5. topic relevance clears the retrieval-quality floor

Invalid edges are removed before optimization.

## Development edge utility

Willingness is a hard eligibility condition in the current implementation. All candidates that reach scoring are already willing to receive that intent type, so willingness is not useful as a ranking feature today.

The current utility is:

```text
u_ij = (topic_relevance + availability) / 2
```

where:

- `topic_relevance` is the current retrieval similarity
- `availability` is remaining responder slots divided by the configured budget

Both values are normalized to 0-1.

This is a development utility, not a calibrated response probability. Equal weights are used because the prototype does not yet have enough real Accepted, Skipped, Useful or Resolved outcomes to justify learned weights.

## Assignment objective

The allocator chooses binary assignments `x_ij`:

```text
maximize sum(u_ij * x_ij)
```

subject to:

```text
sum_j x_ij <= 1       for each open request i
sum_i x_ij <= c_j     for each responder j
x_ij = 0              for invalid or below-threshold edges
x_ij in {0, 1}
```

Responder capacity is represented as repeated assignment slots. Dummy columns with zero utility allow a request to remain unmatched.

## Why batch allocation matters

A greedy method can make the best local choice and still reduce the total utility of the window.

| | R1 | R2 |
| --- | ---: | ---: |
| I1 | 0.99 | 0.98 |
| I2 | 0.97 | 0.10 |

Both responders have capacity 1.

Greedy can assign R1 to I1 and leave I2 with R2. Batch assignment can give R2 to I1 and reserve R1 for I2.

This table is a unit-test example. It explains the optimization problem but is not a real-world effect-size claim.

## Threshold rule

Minimum-quality rules are applied before optimization.

If a weak edge is allowed to influence the assignment and removed only after the solver runs, it can block a different valid solution. `tests/test_optimizer.py` contains a regression case for this failure mode.

The runtime also applies a topic-relevance floor before creating allocation edges. Our first matching benchmark draft showed why this matters: a global optimizer can increase coverage by distributing weak matches when retrieval is too permissive.

## Stateful prototype capacity

The main web prototype keeps open requests and responder state in browser session storage. Each API call includes the current responder state.

Accept reduces remaining capacity. Pause disables that responder. Skip excludes a responder for the current request and reallocates the open window.

This makes capacity persistent across sequential actions within one demo session. It is intentionally not described as production persistence.

## Scaling boundary

The dense assignment solver is not intended to run over the complete NSosyal network.

```text
retrieval -> bounded candidate graph -> allocation
```

The current implementation is appropriate for small matching windows after retrieval. Larger production windows can use sparse min-cost flow or smaller topic/time buckets without changing the product-level constraints.
