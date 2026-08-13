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
# OUTPUT FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
You MUST output the final text summary using this exact template.

TEXT SUMMARY TEMPLATE

▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

1. Header

Field Value
Project [PROJECT]
Reporting Period [REPORTING PERIOD]
Assessment Date & Time [YYYY-MM-DD HH:MM]
Author [AUTHOR/ROLE]

2. Overall Status

[🟢 GREEN/🟡 AMBER/🔴 RED] — Score: [X.XX] / 3.0

[Overall status prose summary — 2-3 sentences summarizing the status, explaining key delivery bottlenecks, capacity/execution gaps, and critical path recommendations for proceeding to release.]



3. Groups Overview

Group Score RAG
[Group Name 1] [X.XX] / 3.0 [🟢 GREEN/🟡 AMBER/🔴 RED]
[Group Name ...] [X.XX] / 3.0 [🟢 GREEN/🟡 AMBER/🔴 RED]
[Group Name N] [X.XX] / 3.0 [🟢 GREEN/🟡 AMBER/🔴 RED]

4. Top RED Items

[Group Name 1] — [Metric Name] — [what is wrong — 1 line] → [Recommended action / mitigation step]
[Group Name ... ] — [Metric Name] — [what is wrong — 1 line] → [Recommended action / mitigation step]
[Group Name N] — [Metric Name] — [what is wrong — 1 line] → [Recommended action / mitigation step]

5. Top AMBER Items
[Group Name 1] — [Metric Name] — [what is wrong — 1 line] → [Recommended action / mitigation step]
[Group Name ... ] — [Metric Name] — [what is wrong — 1 line] → [Recommended action / mitigation step]
[Group Name N] — [Metric Name] — [what is wrong — 1 line] → [Recommended action / mitigation step]

▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼

Rules:
- Tables are mandatory.
- Keep formatting concise with zero unnecessary whitespace or artificial column padding.
- Do not replace with a prose-only summary.
- If a section (e.g., "Top RED Items" or "Top AMBER Items") has no items, write "None".

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DYNAMIC TABLE & CONTENT POPULATION RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
To populate the tables and sections:

Header Information:

Fetch [PROJECT] and [REPORTING PERIOD] from the current configuration or project preferences.
For [YYYY-MM-DD HH:MM], use the current assessment timestamp in the relevant time zone.
For [AUTHOR/ROLE], default to the user's [name] (e.g., "Volodya").


Overall Status:

Determine the overall status and score dynamically using the metric-weight scoring rules.
Formulate the blockquote section as a brief, high-level summary of recommendations and status-defining risks.


Groups Overview Table:

The catalog order of evaluation groups is the source of truth for the rows.
Populate with the calculated group scores and their corresponding RAG symbols.


Top RED / AMBER Items:

Extract the highest-impact failed metrics (such as those marked MUST optionality/priority).
Format each line item precisely: [Group Name] — [Metric Name] ([Context/Value]) → [Target Action].

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PLACEHOLDER SOURCES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[PROJECT], [REPORTING PERIOD]: PreferencesConfig / project context.
[YYYY-MM-DD HH:MM]: Assessment execution timestamp.
[AUTHOR/ROLE]: Current evaluator's title or default system role.
Group names, metrics, scores, and status symbols: dynamically evaluated based on the metric rules.

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

