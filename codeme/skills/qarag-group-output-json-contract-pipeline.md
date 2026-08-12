# qarag-group-output-json-contract-pipeline

Return ONLY JSON with fields:
{
  "general_project_info": {
    "user_name": "Volodya",
    "project_name": "Test project",
    "project_timezone": "UTC",
    "reporting_period": "Release 1.0",
    "cadence": "Quarterly",
    "staffing": {
      "dev_count": 15,
      "qa_count": 1
    },
    "integrations": {
      "jira": {
        "connected": false
      }
    },
    "last_run_at": "2026-08-04T17:46:49Z"
  },
  "selection_defaults": {
    "metric_type": "both",
    "selected_group_ids": [],
    "metrics_priorities": "MUST"
  },
  "common_score": {
    "rag": "RED",
    "score": 1.0,
    "general_conclusion": "Open defects: P1=1, P2=10.",
    "gaps": "...",
    "fix": "..."
  },
  "top_items": {
    "RED": [
      {
        "group": "Testing Delivery Status",
        "metrics": [
          {
            "item": "P1 defects very high (P1=10)",
            "why": "Direct release blocker risk",
            "action": "Daily triage, assign owners, burn down to 0"
          }
        ]
      },
      {
        "group": "Release Readiness Status",
        "metrics": [
          {
            "item": "Manual P1/P2 execution only 50% (Finished)",
            "why": "Not enough validation for release confidence",
            "action": "Re-run missing P1/P2 cases to \u226590% (target 100%)"
          },
          {
            "item": "High-impact risk: \"slow AI\" (medium prob)",
            "why": "Can impact release outcomes/quality",
            "action": "Define mitigation + contingency, set go/no-go criteria"
          }
        ]
      }
    ],
    "AMBER": [
      {
        "group": "Release Readiness Status",
        "metrics": [
          {
            "item": "Automated P1/P2 coverage 90%",
            "why": "Critical automation not fully executed",
            "action": "Push to 100%, stabilize flaky tests"
          }
        ]
      },
      {
        "group": "Testing Delivery Status",
        "metrics": [
          {
            "item": "P3+/untriaged = 12",
            "why": "Backlog moderate",
            "action": "Triage, close duplicates, keep \u226410"
          },
          {
            "item": "P3+ trend widening (stored \"C\")",
            "why": "Backlog accumulation risk",
            "action": "Increase resolution throughput, weekly burn-down targets"
          }
        ]
      }
    ]
  },
  "group_metrics": [
    {
      "group_key": 1,
      "group_id": "release_readiness",
      "group": "Release Readiness",
      "weight": 1.0,
      "group_score": 2.2,
      "group_status": "RED",
      "group_conclusion": "...",
      "metric_results": [
        {
          "metric_id": "m1",
          "name": "Metric display name",
          "type": "ongoing",
          "optionality": "MUST",
          "status": "RED",
          "score": 3.0,
          "weight": 1.0,
          "detail": "...",
          "gaps": "...",
          "fix": "...",
          "key_facts": "..."
        }
      ],
      "metric_state_patch": {},
      "jira_query_registry_patch": {}
    }
  ]
}
Notes:
- group_score excludes N/A and SKIPPED from denominator.
- DEFERRED metrics should appear in metric_results with status=DEFERRED and score=0 and excluded from denominator.