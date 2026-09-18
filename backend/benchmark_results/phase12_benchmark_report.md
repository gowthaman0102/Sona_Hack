# AURA Phase 12 Benchmark Report

## Benchmark Objective

Evaluate adaptive AURA routing against an Always-HIGH baseline using the same 18 prompts.

The Always-HIGH baseline forces every request to the HIGH tier (`qwen3:8b`).

All models run locally through Ollama, so actual API monetary spend is ?0. The benchmark therefore uses normalized compute cost rather than currency.

## Methodology

- 18 benchmark prompts.
- 6 labelled low difficulty.
- 6 labelled medium difficulty.
- 6 labelled high difficulty.
- Task categories include extraction, classification, transformation, general, explanation, summarization, coding, analysis, and planning.
- Both strategies execute the same prompt set through the existing `/route` pipeline.
- Quality is evaluated deterministically using exact, contains-all, or contains-any checks.
- Production learning history is preserved around every benchmark request so benchmark execution cannot train or contaminate the adaptive router.
- Dataset difficulty labels are benchmark metadata and are distinct from AURA's runtime analyzer tier.

## Aggregate Results

| Metric | Adaptive AURA | Always-HIGH | Adaptive Delta |
|---|---:|---:|---:|
| Pass rate | 88.89% | 100.00% | -11.11 pp |
| Mean quality | 0.8889 | 1.0000 | -0.1111 |
| Total latency | 170.790 s | 90.640 s | +88.43% |
| Mean latency | 9.488 s | 5.036 s | ? |
| Total tokens | 6221 | 4078 | +52.55% |
| Normalized compute | 556.217 | 362.560 | +53.41% |
| Escalations | 0 | 0 | ? |

## Routing Distribution

Adaptive AURA final-tier usage:

- LOW: 6
- MEDIUM: 6
- HIGH: 6

Always-HIGH final-tier usage: HIGH = 18.

## Quality Comparison

- Adaptive quality wins: 0.
- Adaptive quality losses: 2.
- Quality ties: 16.

Always-HIGH corrected these adaptive quality failures:

- `low-classification-negative`
- `low-classification-positive`

## Compute Comparison

- Adaptive used lower normalized compute on 6 cases.
- Adaptive used higher normalized compute on 12 cases.
- Compute ties: 0.

Adaptive AURA matched Always-HIGH quality while using lower normalized compute on:

- `high-planning-backup`
- `high-planning-migration`
- `low-extraction-phone`
- `low-transformation-uppercase`

## Observations

1. Always-HIGH achieved the highest deterministic quality in this benchmark run.
2. Adaptive AURA did not reduce aggregate latency, token generation, or normalized compute in this run.
3. Smaller models sometimes generated substantially longer responses, offsetting their lower per-second compute score.
4. The two adaptive quality failures were both classification tasks routed to the LOW model.
5. Adaptive routing still demonstrated per-case efficiency opportunities: several prompts matched Always-HIGH quality with lower normalized compute.
6. No confidence-based escalation occurred in either saved benchmark run.

## Interpretation

The benchmark does not support a claim that the current adaptive policy is globally more efficient than Always-HIGH on this hardware and prompt set.

Instead, the results identify where the router needs further optimization: stronger classification routing, better output-length control, and routing decisions that account for observed generation efficiency rather than model size alone.

## Limitations

- This is a single saved run of 18 prompts, not a large statistical performance study.
- Local inference latency varies with model warm state, system load, and generated response length.
- The deterministic evaluator checks required answer properties but is not a complete semantic quality judge.
- Normalized compute cost is an internal resource metric, not monetary API cost.
- Actual monetary API spend remains ?0 because all benchmark models execute locally.

## Phase 12 Conclusion

Phase 12 establishes a reproducible benchmarking framework for AURA and provides a measured baseline for future routing improvements.

The current results favor Always-HIGH at the aggregate level, while also revealing specific cases where adaptive routing preserves quality at lower compute.

These findings should be carried into final integration and future policy tuning without altering the saved benchmark evidence.
