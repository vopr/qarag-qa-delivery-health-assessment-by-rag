---
name: qarag-template-store
description: >
  Binary storage for the QARAG QA/Delivery Health Status PowerPoint template.
  Holds no logic of its own — it exists only so the CodeMie PowerPoint Report
  Agent has a stable place to fetch the template .pptx from, since binary
  files can't live inline in the agent's own system prompt.
---

# QARAG Template Store

This skill stores two companion files, kept in sync — regenerate the `.b64.txt` file
any time the `.pptx` changes:

- `assets/QA_Delivery_Health_Status_Report_Template_-_Optimized.pptx` — the template
  itself (~120 KB). Trimmed to only the slide layout, master, and media actually used
  by its 4 content slides — the original export carried 71 unused corporate slide
  layouts and ~13 MB of orphaned background images that were never reachable from any
  real slide; removing them cut the file from ~13 MB to ~120 KB with zero visual
  change (verified against the untrimmed version, slide-by-slide).
- `assets/QA_Delivery_Health_Status_Report_Template_-_Optimized.pptx.b64.txt` — the
  same file, base64-encoded as plain ASCII text (~163 KB). **Fetch this one, not the
  raw `.pptx`, via `skill_file`.** `skill_file` serializes binary content in
  `encoding="text"` mode, which corrupts arbitrary binary bytes (confirmed: raw PPTX
  fetches came back with mangled/replacement characters, not just truncated). Base64
  text has no bytes outside the printable ASCII range, so it survives that mode
  intact — decode it client-side instead.

No rendering instructions live here — those belong to the CodeMie PowerPoint Report
Agent's own system prompt. This skill is referenced by that agent purely to retrieve
the file.
