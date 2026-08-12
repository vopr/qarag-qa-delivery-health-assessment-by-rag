# qarag-scoring-and-summary-output-rules

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PURPOSE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This skill standardizes:
1) Scoring + aggregation rules (RAG mapping, denominator rules, group score thresholds)
2) Generic standalone output format and dynamic table population rules
3) A mandatory user confirmation gate after each group summary (draft → confirm/edit → confirmed)

It must be applied consistently across all metric-group assessor agents.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIRMATION GATE (MANDATORY — NON-NEGOTIABLE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This skill MUST enforce a 2-step handshake for every group summary:

Step A — DRAFT Group Summary (always first):
- Generate the full group summary using the template below.
- At the end of the summary, you MUST ask for confirmation using EXACT text (verbatim):

"Proceed with this group summary?
1) Yes — save and continue
2) No — change something"

- After asking this question, you MUST STOP and wait for the user's answer.
- You MUST NOT start the next group, ask the next metric question, or output any other follow-up question in the same message.

Step B — CONFIRMED Group Summary (only after user selects option 1):
- Re-print the same group summary heading andmark it as confirmed:
📊 [METRIC GROUP NAME] — [PROJECT] | [REPORTING PERIOD] | [date & time in your time zone]
Mode: Mode: CONFIRMED BY USER
Overall: [🟢 GREEN/🟠 AMBER/🔴RED/ N/A], Score: [X.X]/3.0
- Do NOT ask the confirmation question again.
- Then and only then the calling agent may proceed to persistence and the next group.

Step B — CONFIRMED Group Summary (only after user selects option 1):
- Do NOT reprint the group summary.
- Output the following message: "GROUP SUMMARY FOR [Metric Group Name] is confirmed" (replace `[Metric Group Name]` with the actual name of the metric group being summarized).
- Do NOT ask the confirmation question again.
- Then and only then the calling agent may proceed to persistence and the next group.

Important:
- This gate is required even if the group is N/A (no scored metrics); still produce the table and request confirmation.
- This skill does not perform persistence itself; it provides the required interaction checkpoint that the caller must honor.

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
Mode: DRAFT

Overall: [🟢 GREEN/🟠 AMBER/🔴RED/ N/A], Score: [X.X]/3.0

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

Proceed with this group summary?
1) Yes — save and continue
2) No — change something

HARD Rules:
- Table is mandatory.
- Important: Exclude skipped metrics (`{group_id}.metrics[metric_id].reporting_status = skipped` or (S / Skip option ("🚫 'S' - Skip / Not Applicable (Type 'S' to skip this metric)")) - don't show them in the table!
- Concise Formatting: Ensure zero unnecessary whitespace or artificial column padding to keep the table compact.
- Deferred metrics show as DEFERRED in Score, 🔘 in Status.
- For N/A metrics, keep the row (unless permanently skipped) with Weighted Score = "N/A" and Status = "⚪" (or blank), but be consistent within the report.
- If a section has no items, write "None".
- In DRAFT mode, the confirmation question MUST be the final lines of the message (no text after).
- In CONFIRMED mode, replace "Mode: DRAFT" with "Mode: CONFIRMED BY USER" and remove the confirmation question entirely.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DYNAMIC TABLE POPULATION RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
To populate the table and sections:

1) Use the group’s metric catalog/order as the source of truth for which metrics exist.
2) Exclude from the table skipped metrics: `{group_id}.metrics[metric_id].reporting_status = skipped` or (S / Skip option ("🚫 'S' - Skip / Not Applicable (Type 'S' to skip this metric)")
3) Include deferred metrics in the table with:
   - Weighted Score = "DEFERRED"
   - Status = "🔘"
4) For N/A metrics:
   - Keep the row (unless permanently skipped)
   - Weighted Score = "N/A"
   - Status = "⚪" (or keep blank), but be consistent within the report.
5) Fill "NEEDS IMMEDIATE ATTENTION" with RED metrics; include gaps + delivery impact + fix (1–2 lines each).
6) Fill "NEEDS ATTENTION" with AMBER metrics; include gap + impact (1–2 lines each).
7) Fill "HEALTHY" with GREEN metrics (names only).
8) If a section has no items, write "None".

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# USER REQUESTED EDITS (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
If the user selects option 2 ("No — change something"):
- Ask exactly ONE question:
  "What would you like to change? (reply with: conclusion / table row(s) / gaps / fix / key facts)"
- Only modify the parts the user requested.
- Do NOT change computed scores unless the user changed a metric input/status that affects scoring.
- Regenerate the full DRAFT summary and re-run the Confirmation Gate.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PLACEHOLDER SOURCES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- {METRIC GROUP NAME]: use the group display name (e.g., "Testing Delivery Status").
- [PROJECT], [REPORTING PERIOD]: use PreferencesConfig / project context.
- [date & time]: current timestamp.
- Overall score/status: compute from evaluated non-N/A, non-skipped, non-deferred metrics per scoring rules above.