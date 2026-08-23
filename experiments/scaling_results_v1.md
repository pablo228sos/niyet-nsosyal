# Dense global allocator scaling check

This is a development benchmark for the current dense assignment prototype. It is not a production NSosyal load test.

Setup:
- synthetic candidate graph
- 8 candidate responders per intent
- responder attention budget: 2
- responders: about half the number of intents, with a minimum of 10
- SciPy `linear_sum_assignment`
- dummy columns allow intents to remain unmatched
- median of 7 runs for sizes up to 400
- larger sizes were checked with 3 runs

Development environment:
- Linux x86_64
- Python process saw 5 CPUs
- SciPy 1.17.0

Results:

| Open intents | Responders | Candidate edges | Dense matrix | Median runtime |
| ---: | ---: | ---: | ---: | ---: |
| 25 | 12 | 200 | 0.009 MB | 0.177 ms |
| 50 | 25 | 400 | 0.038 MB | 0.194 ms |
| 100 | 50 | 800 | 0.153 MB | 0.648 ms |
| 200 | 100 | 1,600 | 0.610 MB | 1.882 ms |
| 400 | 200 | 3,200 | 2.441 MB | 8.390 ms |
| 800 | 400 | 6,400 | 9.766 MB | 47.887 ms |
| 1,200 | 600 | 9,600 | 21.973 MB | 176.833 ms |
| 1,600 | 800 | 12,800 | 39.063 MB | 546.314 ms |

## What this means

The current dense solver is fast enough for small candidate batches in the prototype, but its memory and runtime grow quickly as the batch gets large. We should not run one global assignment across an entire social network.

The intended production shape is two-stage:

1. semantic retrieval narrows every open intent to a small candidate set
2. allocation runs inside a bounded queue, topic/community bucket or short time window

For larger deployments we should also test a sparse min-cost flow formulation instead of creating a dense utility matrix.

This result is useful for the report because it defines a real operating boundary. It is not evidence that the current implementation can handle millions of users without further engineering.
