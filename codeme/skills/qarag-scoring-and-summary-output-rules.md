# qarag-scoring-and-summary-output-rules

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PURPOSE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This skill standardizes:
1) Scoring + aggregation rules (RAG mapping, denominator rules, group score thresholds)
2) Generic standalone output format and dynamic table population rules

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
- SKIPPED (permanent skip)

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
# OUTPUT FORMAT (GENERIC — STANDALONE MODE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
When in STANDALONE MODE, you MUST output the final group report using this exact template.

## STANDALONE MODE

▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

📊 [METRIC GROUP NAME] — [PROJECT] | [REPORTING PERIOD] | [date & time in your time zone]

Overall: [🟢 GREEN/🟠 AMBER/🔴RED], Score: [X.X]/3.0

| Metric | Weighted Score | Status |
| :--- | :---: | :---: |
| Metric 1 | X.X | 🟢 |
| Metric ...| X.X | 🟠 |
| Metric N| X.X | 🟢 |
| Metric N+ 1| X.X | 🔴 |

🔴 NEEDS IMMEDIATE ATTENTION
▸ **[Metric]**: [what is wrong — 1 line]
  → [Delivery impact — 1 line]
  🎯 Fix: [concrete action + effort]

🟠 NEEDS ATTENTION
▸ **[Metric]**: [gap — 1 line]
  → [impact]

✅ HEALTHY: **[metric]** | **[metric]**

▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼


Rules:
- Table is mandatory.
- All metrics must appear EXCEPT permanently skipped metrics (reporting_status="skipped").
- Concise Formatting: Ensure zero unnecessary whitespace or artificial column padding to keep the table compact.
- Deferred metrics show as DEFERRED in Score, 🔘 in Status.
- Do not replace with prose-only summary.
- If a section has no items, write "None".

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DYNAMIC TABLE POPULATION RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
To populate the table and sections:

1) Use the group’s metric catalog/order as the source of truth for which metrics exist.
2) Exclude permanently skipped metrics (reporting_status="skipped") from the table.
3) Include deferred metrics in the table with:
   - Weighted Score = "DEFERRED"
   - Status = "🔘"
4) For N/A metrics:
   - Keep the row (unless permanently skipped)
   - Weighted Score can be "N/A"
   - Status icon can be "⚪" (or keep blank), but be consistent within the report.
5) Fill "NEEDS IMMEDIATE ATTENTION" with RED metrics; include gaps + delivery impact + fix (1–2 lines each).
6) Fill "NEEDS ATTENTION" with AMBER metrics; include gap + impact (1–2 lines each).
7) Fill "HEALTHY" with GREEN metrics (names only).
8) If a section has no items, write "None".

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PLACEHOLDER SOURCES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- {METRIC GROUP NAME]: use the group display name (e.g., "Testing Delivery Status").
- [PROJECT], [REPORTING PERIOD]: use PreferencesConfig / project context.
- [date & time]: current timestamp.
- Overall score/status: compute from evaluated non-N/A, non-skipped, non-deferred metrics per scoring rules above.