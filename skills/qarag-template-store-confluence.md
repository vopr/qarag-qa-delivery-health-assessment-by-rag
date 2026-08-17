---
name: qarag-template-store-confluence
description: >
  Storage for the QARAG render engine only (Confluence variant). The template is
  fetched directly from Confluence — this skill holds render.py chunks only.
---

# QARAG Template Store — Confluence Variant

The template (`QA_Delivery_Health_Status_Report_Template_-_Optimized.pptx`) is
downloaded directly from Confluence by the render agent — **do not fetch it from this
skill**. This skill provides `render.py` chunks only.

## Asset locations and fetch order

**Artifact bucket name (canonical — change here only):** `qa-rag-report-artifacts`

Fetch each asset in this order — stop at the first success:

1. **Skill file storage** (`skill_file` call) — available in CodeMie, where the `.zb85`
   companions are attached directly to this skill.
2. **Artifact bucket fallback** — for tools without skill file storage (e.g. Alitea).
   Read from artifact bucket `qa-rag-report-artifacts` using the same filename.

Hard stop if both sources fail — do not substitute or rebuild the asset inline.

---

## Fetch strategy: zlib+base85, chunked into ≤6 000-character pieces

`render.py` is compressed with zlib then base85-encoded (`render.py.zb85`, ~10 KB), then
pre-split into chunks of ≤6 000 characters. The render agent fetches and writes each
chunk separately, then a small Python script reassembles and decodes in the sandbox.

Decode:
```python
data = zlib.decompress(base64.b85decode(encoded))
```

## Contents

- **`render.py`** (~26 KB, plain source, human-readable) — the full render engine.
  Kept for reference; **not** fetched at render time.
- **`render.py.zb85`** (~10 KB) — `render.py`, zlib-compressed then base85-encoded.
  Kept for reference; **not** fetched at render time (too large to copy verbatim on Bedrock).
- **`render.chunk1.zb85`** (6 000 chars) — first chunk of `render.py.zb85`. **Fetched at render time.**
- **`render.chunk2.zb85`** (4 905 chars) — second chunk of `render.py.zb85`. **Fetched at render time.**

The template and its chunks are **not stored here** — the template is fetched from
Confluence (page ID `2912184179`,
file `QA_Delivery_Health_Status_Report_Template_-_Optimized.pptx`).

**Because the radar chart shape doesn't exist in the template, `render.py` synthesizes it
from scratch on every render** — a new picture shape, relationship, and media part,
positioned at the original design's coordinates (hardcoded fallback in `render.py`).
If `render.py` is ever patched, keep that fallback path working.

## Regenerating after an edit

If `render.py` changes, regenerate `render.py.zb85`
(`base64.b85encode(zlib.compress(data, 9))`), re-split into ≤6 000-character chunks,
and replace `render.chunk1.zb85` and `render.chunk2.zb85` — don't let the plain file,
the `.zb85`, or the chunks drift out of sync.

No further rendering instructions live here — those belong to the CodeMie PowerPoint
Report Agent's own system prompt.
