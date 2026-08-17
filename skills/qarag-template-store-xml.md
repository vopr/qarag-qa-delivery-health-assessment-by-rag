---
name: qarag-template-store-xml
description: >
  Storage for the QARAG render engine and PowerPoint template in unpacked form.
  The template is stored as individual XML files (not as a binary PPTX) so the
  render agent can fetch and write plain text without binary encoding.
---

# QARAG Template Store — XML variant

The template is stored unpacked: each internal PPTX file is a separate skill file.
The render agent fetches all files, writes them to workspace, then reconstructs
`template.pptx` with a Python script before rendering.

## Asset locations and fetch order

**Artifact bucket name (canonical — change here only):** `qa-rag-report-artifacts`

Fetch each asset in this order — stop at the first success:

1. **Skill file storage** (`skill_file` call) — available in CodeMie.
2. **Artifact bucket fallback** — bucket `qa-rag-report-artifacts`, same filename.

Hard stop if both sources fail — do not substitute or rebuild inline.

---

## Files to fetch at render time

Fetch all files sequentially (one at a time). All are plain text except `tpl_logo.b64`
(base64-encoded PNG). The Python reconstruction script maps each skill filename back
to its original ZIP path inside the PPTX.

### render.py (2 chunks)
| Skill filename | Size |
|---|---|
| `render.chunk1.zb85` | 6 000 chars |
| `render.chunk2.zb85` | 4 905 chars |

### Template XML files (22 files)
| Skill filename | ZIP path | Size |
|---|---|---|
| `tpl_content_types.xml` | `[Content_Types].xml` | 2 KB |
| `tpl__rels.xml` | `_rels/.rels` | 593 B |
| `tpl_docProps_app.xml` | `docProps/app.xml` | 1.5 KB |
| `tpl_docProps_core.xml` | `docProps/core.xml` | 818 B |
| `tpl_ppt__rels_presentation.xml` | `ppt/_rels/presentation.xml.rels` | 1.3 KB |
| `tpl_ppt_presProps.xml` | `ppt/presProps.xml` | 1.3 KB |
| `tpl_ppt_presentation.xml` | `ppt/presentation.xml` | 3.6 KB |
| `tpl_slideLayouts__rels.xml` | `ppt/slideLayouts/_rels/slideLayout1.xml.rels` | 311 B |
| `tpl_slideLayouts_layout1.xml` | `ppt/slideLayouts/slideLayout1.xml` | 977 B |
| `tpl_slideMasters__rels.xml` | `ppt/slideMasters/_rels/slideMaster1.xml.rels` | 581 B |
| `tpl_slideMaster1.xml` | `ppt/slideMasters/slideMaster1.xml` | 23 KB |
| `tpl_slides__rels_slide1.xml` | `ppt/slides/_rels/slide1.xml.rels` | 311 B |
| `tpl_slides__rels_slide2.xml` | `ppt/slides/_rels/slide2.xml.rels` | 311 B |
| `tpl_slides__rels_slide3.xml` | `ppt/slides/_rels/slide3.xml.rels` | 311 B |
| `tpl_slides__rels_slide4.xml` | `ppt/slides/_rels/slide4.xml.rels` | 311 B |
| `tpl_slide1.xml` | `ppt/slides/slide1.xml` | 14 KB |
| `tpl_slide2.xml` | `ppt/slides/slide2.xml` | 7.4 KB |
| `tpl_slide3.xml` | `ppt/slides/slide3.xml` | 13.6 KB |
| `tpl_slide4.xml` | `ppt/slides/slide4.xml` | 21 KB |
| `tpl_ppt_tableStyles.xml` | `ppt/tableStyles.xml` | 182 B |
| `tpl_ppt_theme1.xml` | `ppt/theme/theme1.xml` | 5.3 KB |
| `tpl_ppt_viewProps.xml` | `ppt/viewProps.xml` | 907 B |
| `tpl_logo.b64` | `ppt/media/image1.png` (binary, b64-encoded) | 3 KB |

**Because the radar chart shape doesn't exist in the template, `render.py` synthesizes it
from scratch on every render.** If `render.py` is ever patched, keep that fallback working.

## Regenerating after an edit

If the template changes:
1. Unpack the new PPTX with `zipfile.ZipFile`
2. Overwrite the affected `tpl_*.xml` files
3. If `render.py` changes, regenerate `render.py.zb85` and re-split into chunks

No rendering instructions live here — those belong to the agent's system prompt.
