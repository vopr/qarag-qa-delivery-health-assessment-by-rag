# qarag-common-scoring-and-summary-output-rules

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PURPOSE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This skill standardizes:
1) Scoring + aggregation rules (RAG mapping, denominator rules, group score thresholds)
2) Generation rules for the root-level `"top_items"` (RED/AMBER sections) matching the contract structure and visual standards.
3) Generic standalone output format and dynamic table population rules.

It must be applied consistently across all metric-group assessor agents.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SCORING + AGGREGATION RULES (GENERIC)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# METRIC-LEVEL SCORING (RAG → NUMERIC)
For each metric that is SCORED (final status is GREEN, AMBER, or RED):

- 🟢 GREEN → base_score = 3.0
- 🟠 AMBER → base_score = 2.0
- 🔴 RED   → base_score = 1.0

Weighted score for a metric:
- metric_weighted_score = base_score × metric_weight

Notes:
- metric_weight comes only from the group’s metric catalog (source of truth).
- Do not invent or re-normalize weights.

# DENOMINATOR RULES (INCLUSION / EXCLUSION)
Included in denominator (count toward Σ(weight)):
- Metrics with final status: GREEN, AMBER, RED

Excluded from denominator (do NOT count toward Σ(weight)):
- N/A
- DEFERRED
- SKIPPED

Important:
- Excluded metrics do not contribute to numerator either.

If no metrics are included (Σ(weight) = 0):
- group_score = null
- group_rag = "N/A"

# GROUP SCORE FORMULA
Let S be the set of included metrics (GREEN/AMBER/RED).

Numerator   = Σ(metric_base_score × metric_weight) for metrics in S
Denominator = Σ(metric_weight) for metrics in S

GroupScore = Numerator / Denominator

GroupScore range:
- Minimum = 1.0
- Maximum = 3.0

# GROUP THRESHOLDS (GROUP RAG)
Convert GroupScore to group-level RAG:

- GroupScore >= 2.3  → 🟢 GREEN
- GroupScore >= 1.7  → 🟠 AMBER
- GroupScore <  1.7  → 🔴 RED

If GroupScore is null:
- group_rag = "N/A"

# CONSISTENCY RULES (NON-NEGOTIABLE)
1) Never include N/A, DEFERRED, or SKIPPED metrics in the denominator.
2) Use the same mapping and thresholds for every metric group.
3) Weights come only from the metric catalog; do not override them based on answers.
4) If a metric is not evaluated (deferred/skipped/N/A), it must not affect group score.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GENERATION RULES FOR "TOP_ITEMS" (CONTRACT & VISUAL ALIGNMENT)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
The coordinator and assessors must dynamically extract and format the worst-performing metrics into the root-level `"top_items"` parameter.

### 1) "MUST" Optionality Filtering (CRITICAL)
Only metrics evaluated as `RED` or `AMBER` that have **`MUST` optionality** in the metric catalog are eligible for inclusion in the `"top_items"` list. 
- *Exclude all `SHOULD` or `COULD` metrics from this section entirely (e.g., do not add lower priority metrics here).*

### 2) JSON Structure ("top_items")
The `"top_items"` node must group elements first by Status (`RED` or `AMBER`), then by the metric's parent Group Name, and then contain an array of nested metric item dictionaries.

```json
"top_items": {
  "RED": [
    {
      "group": "Release Readiness Status",
      "metrics": [
        {
          "item": "Manual P1/P2 execution coverage",
          "why": "Finished at 80% — below required threshold",
          "action": "Execute remaining P1/P2 tests or formally de-scope with explicit sign-off"
        }
      ]
    },
    {
      "group": "Testing Delivery Status",
      "metrics": [
        {
          "item": "QA capacity",
          "why": "Dev:QA 15:1 (QA share ~6.3%) — critically undersized",
          "action": "Add QA capacity and/or reduce scope; push shift-left testing"
        }
      ]
    }
  ],
  "AMBER": [
    {
      "group": "Release Readiness Status",
      "metrics": [
        {
          "item": "Automated P1/P2 execution coverage",
          "why": "At 90% — not yet at 100% target",
          "action": "Stabilize and fix missing automation to reach 100%"
        }
      ]
    }
  ]
}