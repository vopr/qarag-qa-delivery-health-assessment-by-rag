---
name: qarag-template-store
description: >
  Storage for the QARAG QA/Delivery Health Status PowerPoint template and its
  render engine. Holds no rendering logic of its own beyond the bundled
  render.py — it exists so the CodeMie PowerPoint Report Agent has a stable
  place to fetch the template and the tested render script from.
---

# QARAG Template Store

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

Binary content can't be fetched raw through `skill_file` — it serializes results in
`encoding="text"` mode, which corrupts arbitrary binary bytes (confirmed in practice:
a direct `.pptx` fetch came back with mangled/replacement characters). Base64 is the
obvious text-safe fix, but it costs ~33% size overhead (3 bytes in -> 4 text chars
out), which pushed the template's companion asset from a 25.6 KB binary to 34 KB of
text — enough to risk `skill_file`'s per-call truncation on a long conversation.

**Compress first, then encode with base85 instead of base64:**
- Base85 costs ~25% overhead instead of base64's ~33% (5 chars per 4 bytes instead of
  4 chars per 3 bytes).
- Running the whole `.pptx` through `zlib` before encoding finds real savings even
  though a `.pptx` is already a ZIP: per-file DEFLATE inside the original ZIP can't
  exploit redundancy *across* files (repeated XML boilerplate between slide1-4,
  slideMaster, etc.), but compressing the whole container as one stream can.

Net result on the current template: 25,584 bytes binary -> 20,356 bytes compressed ->
25,445 bytes base85 text. `render.py` benefits even more, since source code compresses
well: 26,340 bytes -> 10,432 bytes encoded.

Decode is one line each direction:
```python
encoded = base64.b85encode(zlib.compress(data, 9)).decode("ascii")   # encode (already done, see below)
data = zlib.decompress(base64.b85decode(encoded))                     # decode
```

**Assets are pre-split into chunks of ≤6 000 characters.** Even though `skill_file`
can return the full content without truncation, the render agent runs on Bedrock
(claude-sonnet-4-6) which does not support assistant message prefill — meaning the LLM
cannot reliably copy a large opaque string verbatim into a `write_workspace_file` tool
call. Chunks of ≤6 000 characters stay well within what the model can copy in a single
call. The render agent fetches and writes each chunk separately, then a small Python
script reassembles and decodes in the sandbox.

## Contents

- **`render.py`** (~26 KB, plain source, human-readable) — the full render engine.
  Kept for reference; **not** fetched at render time.
- **`render.py.zb85`** (~10 KB) — `render.py`, zlib-compressed then base85-encoded.
  Kept for reference; **not** fetched at render time (too large to copy verbatim on Bedrock).
- **`render.chunk1.zb85`** (6 000 chars) — first chunk of `render.py.zb85`. **Fetched at render time.**
- **`render.chunk2.zb85`** (4 905 chars) — second chunk of `render.py.zb85`. **Fetched at render time.**
- **`QA_Delivery_Health_Status_Report_Template_-_Optimized.pptx`** (~26 KB) — the
  template, kept for reference; **not** fetched at render time (binary, corrupted by text-mode).
- **`QA_Delivery_Health_Status_Report_Template_-_Optimized.pptx.zb85`** (~25 KB) — the
  template, zlib-compressed then base85-encoded. Kept for reference; **not** fetched at
  render time (too large to copy verbatim on Bedrock).
- **`template.chunk1.zb85`** (6 000 chars) — chunk 1 of 5. **Fetched at render time.**
- **`template.chunk2.zb85`** (6 000 chars) — chunk 2 of 5. **Fetched at render time.**
- **`template.chunk3.zb85`** (6 000 chars) — chunk 3 of 5. **Fetched at render time.**
- **`template.chunk4.zb85`** (6 000 chars) — chunk 4 of 5. **Fetched at render time.**
- **`template.chunk5.zb85`** (1 338 chars) — chunk 5 of 5. **Fetched at render time.**

Trimmed hard from the original ~13 MB corporate export: removed 71 unused slide
layouts (the 4 content slides use exactly 1), their orphaned background images, empty
notes slides, PowerPoint's co-authoring metadata, and the cosmetic thumbnail; the logo
was converted from EMF to a compressed PNG; and **the rose/radar chart picture shape
was removed from the template entirely** rather than replaced with a placeholder
image, since it's always regenerated anyway. Verified visually identical to the
pre-trim version, slide-by-slide.

**Because the chart shape doesn't exist in the template, `render.py` synthesizes it
from scratch on every render** — a new picture shape, relationship, and media part,
positioned at the original design's coordinates (hardcoded fallback in `render.py`,
since there's nothing left in the template to read the position from). If `render.py`
is ever patched, keep that fallback path working — don't assume the chart shape
exists.

## Regenerating after an edit

If either file changes, regenerate its `.zb85` companion (`base64.b85encode(zlib.compress(data, 9))`), then re-split into ≤6 000-character chunks and replace all chunk files — don't let the plain file, the `.zb85`, or the chunks drift out of sync. If the template changes structurally (shapes added/removed, alt-text markers renamed), re-run `render.py` against it and confirm
the render still succeeds before redeploying — the chart-shape-synthesis fallback
above is a good example of a structural change that needed a matching code change,
not just a re-encode.

No further rendering instructions live here — those belong to the CodeMie PowerPoint
Report Agent's own system prompt (Step 0, for the exact fetch/stage/decode sequence).
This skill is referenced by that agent purely to retrieve these files.