# qarag-preferences-reportingstatus-contract

## PreferencesConfig location
PreferencesConfig is a single JSON document stored on one Confluence page.

## Per-metric state (MUST)
Each metric uses:
preferences.metric_state[group_id].metrics[metric_id].reporting_status
Allowed values:
- todo
- reported
- deferred
- skipped

## Priority rules (first match wins)
1) skipped -> skip silently, do not ask
2) deferred -> show evaluate/skip/defer prompt (deferred-specific)
3) reported -> evaluate immediately (do NOT show evaluate prompt)
4) todo or missing -> show evaluate/skip/defer prompt

## Pipeline vs standalone IO
- PIPELINE mode: DO NOT read/write Confluence. Use shared_context.preferences as truth.
- STANDALONE mode: read/write Confluence PreferencesConfig.

## Patch updates (MUST)
When updating preferences, do not rewrite whole lists.
Return a patch object with only changed nodes:
metric_state_patch[group_id].metrics[metric_id] = { ...updated fields... }

Optionally return jira_query_registry_patch for per-metric JQL edits:
jira_query_registry_patch["group_id.metric_id"] = { ... }

## Timestamp format
YYYY-MM-DD HH:mm