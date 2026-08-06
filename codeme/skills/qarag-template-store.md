---
name: qarag-template-store
description: >
  Binary storage for the QARAG QA/Delivery Health Status PowerPoint template.
  Holds no logic of its own — it exists only so the CodeMie PowerPoint Report
  Agent has a stable place to fetch the template .pptx from, since binary
  files can't live inline in the agent's own system prompt.
---

# QARAG Template Store

This skill has exactly one purpose: storing the template binary at

`assets/QA_Delivery_Health_Status_Report_Template_-_Optimized.pptx`

No rendering instructions live here — those belong to the CodeMie PowerPoint Report
Agent's own system prompt. This skill is referenced by that agent purely to retrieve
the file.
