# qarag-metric-interview-flow

This skill defines the STANDARD interview mechanics used by all Group Assessor agents.
Group agents provide metric catalogs, thresholds and domain logic; this skill provides the flow, UX rules and strict sequencing.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GLOBAL HARD RULES (NON-NEGOTIABLE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1) ONE METRIC AT A TIME:
   - Never show questions for more than one metric in the same assistant message.
   - Never show multiple metric decision prompts at once.
2) VISUAL SEPARATOR:
   - Before starting ANY metric interaction (including the Evaluate prompt or metric questions), print EXACTLY this line on its own:
     "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
3) After metric is skipped (S / Skip option ("🚫 'S' - Skip / Not Applicable (Type 'S' to skip this metric)"), print:
	"✅ [METRIC NAME] is 🚫 SKIPPED!"
   - Proceed to the next metric immediately.
4) After scoring a metric, print:
   "✅ [METRIC NAME] scored — [🟢 GREEN / 🟠 AMBER / 🔴 RED / N/A] — [short status comment]"
   then immediately ask the confirmation prompt (below).
   IMPORTANT! Don't do step 4 if metric is skipped  (S / Skip option ("🚫 'S' - Skip / Not Applicable (Type 'S' to skip this metric)"):
5) Confirmation prompt MUST be exactly:
   "Would you like to keep this score, change it with a justification, or add any additional details about this metric?
    Reply:
    1. Keep score
    2. Change score + justification
    3. Add additional details"
6) If user replies "1. Keep score":
   - Do NOT repeat the confirmation prompt.
   - Proceed to the next metric immediately.
7) If user replies "2. Change score + justification" or "3. Add additional details":
   - Capture the justification/details.
   - Update the stored metric result accordingly.
   - If score changes, reprint the "✅ [METRIC] scored — ..." line with the updated status.
   - Then proceed to the next metric (do not loop confirmation endlessly).
8) Max 2 clarifying follow-ups per metric answer.
9) Skipped behavior:
   - Skipped metrics: do not ask questions, do not show in table if marked as skip.
10) Do not bloat:
   - Keep each metric interaction concise.
   - Do not repeat long definitions unless user asks.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STANDARD METRIC DECISION PROMPT (EVALUATE/SKIP) — MODE-AWARE (NO “ELIGIBLE” STEP)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 0) Always apply scope filters first (hard filters)
A metric may be asked ONLY if it matches BOTH:
- **Chosen Metric type**: `Ongoing` / `Efficiency` / `Both`
- **Chosen metric group** (e.g., `Testing_delivery_status`)

If a metric fails either filter → **skip it entirely** (no prompt, no questions).

## 1) Determine run mode (controls which metrics are included)

### A) Mode 2 — Fresh start
If the user chose **Fresh start**:
- **Ignore** `{group_id}.metrics[metric_id].reporting_status` completely.
- Ask **all** metrics that pass the scope filters (type + group), even if their `reporting_status` is not `reported`.

### B) Mode 1 — Same as last time
If the user chose **Mode 1 — Same as last time**:
- Ask **ONLY** metrics where:  
  `{group_id}.metrics[metric_id].reporting_status = reported`
- All other metrics are **totally skipped** (no prompt, no questions).
- **Fallback:** If **no** metrics have `{group_id}.metrics[metric_id].reporting_status = reported`, then **act as Fresh start** (ignore `reporting_status` and ask all metrics that pass the scope filters).


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ASKING METRIC QUESTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
If proceeding to evaluate a metric:
- Print separator line (see rule #2) and then the metric name.
- Single-message: if the metric has one question (or set of questions combined together in 1 ask), ask it in one message and wait for the user’s reply.
- Sequential (mandatory when the metric definition says or implies “Asking these questions 1 by 1”): ask only one step at a time and wait for the user’s answer before continuing, e.g.:
Ask 1 → wait for answer → Ask 2 → wait for answer → Ask 3 → wait for answer → …
- If a sequential step results in N/A or an instruction says to stop/skip remaining questions for this metric, stop immediately and proceed to scoring/status for this metric (do not ask the next steps).
- Use at most 2 clarifying follow-ups.