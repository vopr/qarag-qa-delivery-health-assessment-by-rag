# qarag-jira-query-registry-contract

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PURPOSE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This skill defines the standard contract for:
1) storing per-metric Jira query configuration in PreferencesConfig
2) returning safe per-metric updates via jira_query_registry_patch
3) consuming jira_snapshot provided by an orchestrator/workflow/Jira-fetcher

This contract prevents "update one metric overrides others" and keeps all group agents consistent.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# KEY TERMS / IDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- group_id: lowercase snake_case (e.g., release_readiness, testing_delivery_status)
- metric_id: stable ID (e.g., m1, m1_2, m3_1)
- metric_key: "{group_id}.{metric_id}" (string)

All Jira registry entries are keyed by metric_key.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PreferencesConfig SCHEMA — jira_query_registry
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PreferencesConfig MUST support:

preferences.integrations.jira = {
  "connected": true|false|null,
  "base_url": "...",
  "project_keys": ["ABC", "XYZ"],
  "defaults": {
    "timebox": "...",      // sprint name, release name, or other
    "date_from": "YYYY-MM-DD"|null,
    "date_to": "YYYY-MM-DD"|null
  }
}

preferences.jira_query_registry = {
  "release_readiness.m1": { ...metric Jira config... },
  "testing_delivery_status.m2": { ...metric Jira config... }
}

Each registry entry schema (recommended minimum):
{
  "enabled": true,
  "jql_mode": "template" | "raw",
  "jql_template": "project in (${project_keys}) AND ...",    // if template
  "jql_raw": "project = ABC AND ...",                        // if raw
  "params": {
    "project_keys": ["ABC"],
    "timebox": "Sprint 12",
    "date_from": "YYYY-MM-DD",
    "date_to": "YYYY-MM-DD",
    "custom": {}
  },
  "notes": "free text",
  "last_modified_at": "YYYY-MM-DD HH:mm",
  "last_modified_by": "user|system"
}

Rules:
- If jql_mode="template": use jql_template and params for placeholder substitution.
- If jql_mode="raw": use jql_raw as-is (params may still exist for documentation).
- "enabled=false" means: do not attempt Jira auto-fill for this metric.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PATCH UPDATES — jira_query_registry_patch (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
When a user edits Jira query/parameters for a single metric, the agent MUST return ONLY a patch
for that metric (never rewrite the entire registry):

jira_query_registry_patch = {
  "{group_id}.{metric_id}": {
    ...full updated registry entry OR minimal changed fields...
  }
}

Patch rules:
1) Patch MUST be scoped to the current metric_key only.
2) Patch MUST NOT delete or overwrite other metrics' registry entries.
3) Patch MUST include last_modified_at (YYYY-MM-DD HH:mm) and last_modified_by.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# "EDIT JIRA QUERY/PARAMETERS" UX OPTION (IF ENABLED)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
If the assistant provides a decision prompt for a metric and Jira editing is enabled,
it MAY include an option:
"Edit Jira query/parameters for this metric"

When user selects it:
1) Show the currently configured values for this metric_key (if any):
   - jql_mode
   - jql_template or jql_raw
   - params (project_keys/timebox/date_from/date_to)
2) Ask user what to change. Accept either:
   A) full new JQL string (raw), or
   B) updated template + params, or
   C) params-only update (keep existing query)
3) Ask:
   "Save as default for next runs? (yes/no)"
   - If yes: return jira_query_registry_patch for this metric_key.
   - If no: do not patch preferences; treat the edit as run-only input (store only in runtime context if available).

Important:
- Editing Jira config must NOT erase metric_state or other preferences.
- If Jira is not connected/available, allow the user to save the query anyway, but proceed with manual questions for this run.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONSUMING jira_snapshot (CONVENTION)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Group agents SHOULD NOT execute heavy Jira fetching during pipeline runs.
Instead, they consume shared_context.jira_snapshot.

Recommended structure:
shared_context.jira_snapshot = {
  "release_readiness.m1": { "p1_open": 0, "p2_open": 4, "retrieved_at": "...", "source": "jira" },
  "testing_delivery_status.m1": { "planned": 20, "tested": 18, "retrieved_at": "...", "source": "jira" }
}

Consumption rules:
1) For each metric, look up snapshot by metric_key = "{group_id}.{metric_id}".
2) If required fields exist in jira_snapshot[metric_key]:
   - use them and skip asking the user for that metric input.
3) If missing or incomplete:
   - fall back to user interview questions.

Optional evidence convention (recommended):
- If Jira data is used, include in the metric's detail/evidence:
  - source = "jira"
  - metric_key
  - retrieved_at (if provided)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SAFETY / CONSISTENCY RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1) Never store secrets/tokens inside PreferencesConfig.
2) Keep all keys stable (group_id, metric_id, metric_key).
3) Do not "invent" JQL for a metric unless user explicitly asks; prefer saving user-provided JQL.
4) Always treat Jira config as configuration, not as scoring logic. Scoring remains in metric definitions.