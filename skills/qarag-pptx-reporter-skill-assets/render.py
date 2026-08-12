#!/usr/bin/env python3
"""
QARAG PowerPoint render engine.

Usage:
    python3 render.py <template.pptx-or-dir> <report_model.json> <output.pptx>

The first argument is either a path to a zipped .pptx, or a path to a
directory already containing a reconstructed template tree — the normal case
when staging the template from individually-fetched parts rather than a
single zip (see build_template_dir_from_parts, and Step 0 of the system
prompt for why: base64-encoding a whole zipped .pptx wastes ~33% on content
that's ~96% plain XML text to begin with, so each internal part is staged
raw instead and reassembled here).

This script is deliberately self-contained and dependency-light (stdlib +
matplotlib only) so it can be fetched once from the qarag-template-store
skill and re-run unmodified for every render, instead of being regenerated
by an LLM turn every time (which both costs tokens and risks reintroducing
bugs already fixed here — raw newlines instead of paragraph breaks, text-
frame-collapse formatting loss, wrap="none" overflow, etc. — see inline
comments for why each rule exists).
"""
import base64
import io
import json
import os
import re
import sys
import zipfile

RAG_COLORS = {"GREEN": "55E66F", "AMBER": "FF7701", "RED": "FF0000", "N/A": "888888"}


# ---------------------------------------------------------------------------
# Step 0 companion: reconstruct the template from individually-fetched parts.
#
# The template is not shipped as a single zipped .pptx to fetch-and-decode —
# base64-encoding the whole zip wastes ~33% on content that's ~96% plain XML
# text to begin with. Instead each internal part is staged as its own small
# file (text parts as-is, the one binary media file as a base64 companion),
# alongside a manifest.json mapping each staged filename back to its real
# path inside the .pptx. This function does the reverse: given a directory
# of staged parts + the manifest, it reconstructs the real ppt/... directory
# tree that render() expects.
# ---------------------------------------------------------------------------
def build_template_dir_from_parts(parts_dir, manifest_path, work_root):
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    if os.path.isdir(work_root):
        for dirpath, dirnames, filenames in os.walk(work_root, topdown=False):
            for fn in filenames:
                os.remove(os.path.join(dirpath, fn))
            for dn in dirnames:
                os.rmdir(os.path.join(dirpath, dn))
    os.makedirs(work_root, exist_ok=True)

    missing = []
    for entry in manifest:
        staged = os.path.join(parts_dir, entry["fetch_as"])
        if not os.path.exists(staged):
            missing.append(entry["fetch_as"])
            continue
        real_path = os.path.join(work_root, entry["path"])
        os.makedirs(os.path.dirname(real_path), exist_ok=True)
        if entry["encoding"] == "base64":
            data = base64.b64decode(open(staged, encoding="ascii").read())
            with open(real_path, "wb") as out:
                out.write(data)
        else:
            with open(staged, encoding="utf-8", newline="") as src, open(real_path, "w", encoding="utf-8", newline="") as out:
                out.write(src.read())

    if missing:
        raise SystemExit(
            f"{len(missing)} template part(s) were not staged before reconstruction: "
            f"{missing[:5]}{'...' if len(missing) > 5 else ''}. Staging (Phase 0a) did "
            "not complete. STOP: do not proceed to build a report from scratch."
        )

    # Sanity check: the reconstructed tree should have the parts a real pptx needs.
    required = ["[Content_Types].xml", "ppt/presentation.xml", "ppt/slides/slide4.xml"]
    for r in required:
        if not os.path.exists(os.path.join(work_root, r)):
            raise SystemExit(
                f"Reconstructed template is missing {r} — manifest or staging is "
                "inconsistent. STOP: do not proceed to build a report from scratch."
            )
    return work_root


# ---------------------------------------------------------------------------
# XML helpers — run-level text substitution that preserves formatting.
# NEVER use text_frame.text = "..." (python-pptx) or blind <a:t> regex without
# run-concatenation: PowerPoint frequently splits a bracketed placeholder
# token across multiple runs (spellcheck, autocorrect), and naive substitution
# either collapses formatting to a single default run or misses split tokens.
# ---------------------------------------------------------------------------
def replace_first(xml, token, value, count=1):
    return xml.replace(token, value, count)


def set_multi_paragraph(xml, anchor_text, lines):
    """Replace the <a:p> paragraph containing anchor_text with one <a:p> per
    line in `lines`, each reusing the anchor paragraph's <a:pPr>/<a:rPr>.
    This is the fix for the raw-\\n-in-<a:t> bug: OOXML does not treat literal
    newline characters in run text as line breaks. Some renderers (LibreOffice)
    render them leniently, which can hide the bug in your own QA screenshots,
    but real PowerPoint is not guaranteed to."""
    idx = xml.find(anchor_text)
    if idx == -1:
        return xml
    p_start = xml.rfind("<a:p>", 0, idx)
    p_end = xml.find("</a:p>", idx) + len("</a:p>")
    para = xml[p_start:p_end]
    ppr_m = re.search(r"<a:pPr.*?</a:pPr>|<a:pPr[^/]*/>", para, re.DOTALL)
    ppr = ppr_m.group(0) if ppr_m else ""
    rpr_m = re.search(r"<a:rPr[^>]*/>", para)
    rpr = rpr_m.group(0) if rpr_m else "<a:rPr/>"
    if not lines:
        lines = ["\u2014"]
    new_paras = "".join(f"<a:p>{ppr}<a:r>{rpr}<a:t>{l}</a:t></a:r></a:p>" for l in lines)
    return xml[:p_start] + new_paras + xml[p_end:]


def set_run_color(xml, text_after_replace, hex_color):
    """Find the run whose <a:t> equals text_after_replace and set its
    <a:srgbClr val="..."/> to hex_color. Used for RAG-driven text coloring."""
    idx = xml.find(f"<a:t>{text_after_replace}</a:t>")
    if idx == -1:
        return xml
    run_start = xml.rfind("<a:r>", 0, idx)
    run_end = xml.find("</a:r>", idx) + len("</a:r>")
    run = xml[run_start:run_end]
    new_run = re.sub(r'<a:srgbClr val="[0-9A-Fa-f]{6}"/>',
                      f'<a:srgbClr val="{hex_color}"/>', run, count=1)
    return xml[:run_start] + new_run + xml[run_end:]


def set_shape_fill_by_alt_text(xml, alt_text, hex_color):
    """Set a shape's own background fill (not a text run) by locating it via
    its alt text (descr=...) rather than shape index, since index can shift."""
    i = xml.find(f'descr="{alt_text}"')
    if i == -1:
        return xml
    sppr_start = xml.find("<p:spPr>", i)
    sppr_end = xml.find("</p:spPr>", sppr_start) + len("</p:spPr>")
    block = xml[sppr_start:sppr_end]
    new_block = re.sub(
        r"<a:noFill/>|<a:solidFill>.*?</a:solidFill>",
        f'<a:solidFill><a:srgbClr val="{hex_color}"/></a:solidFill>',
        block, count=1, flags=re.DOTALL,
    )
    return xml[:sppr_start] + new_block + xml[sppr_end:]


def fill_header_line(xml, period, run_at, author):
    """The Reporting-period/Assessment/Author line is an independent copy on
    each of slides 1, 2, 3 — must be filled per-slide, not once globally."""
    xml = replace_first(xml, "[Reporting Period]", period)
    xml = xml.replace(
        "[last report time] |   Author: [user.name]",
        f"{run_at} |   Author: {author}", 1,
    )
    return xml


# ---------------------------------------------------------------------------
# Step 1: structural duplication
# ---------------------------------------------------------------------------
def duplicate_group_slides(root, n_groups):
    """Slide 4 is the template for every group; duplicate it (n_groups - 1)
    times, registering each copy in [Content_Types].xml and presentation.xml.
    Returns the list of slide XML file paths, one per group, in order."""
    slides_dir = os.path.join(root, "ppt", "slides")
    rels_dir = os.path.join(slides_dir, "_rels")
    slide_paths = [os.path.join(slides_dir, "slide4.xml")]

    if n_groups < 1:
        raise ValueError("n_groups must be >= 1")

    ct_path = os.path.join(root, "[Content_Types].xml")
    ct = open(ct_path, encoding="utf-8").read()
    ct_override_m = re.search(
        r'<Override PartName="/ppt/slides/slide4\.xml"[^/]*ContentType="[^"]*"/>', ct)

    pres_path = os.path.join(root, "ppt", "presentation.xml")
    pres = open(pres_path, encoding="utf-8").read()
    pres_rels_path = os.path.join(root, "ppt", "_rels", "presentation.xml.rels")
    pres_rels = open(pres_rels_path, encoding="utf-8").read()

    existing_rids = set(re.findall(r'Id="(rId\d+)"', pres_rels))
    existing_sldids = [int(x) for x in re.findall(r'<p:sldId id="(\d+)"', pres)]
    next_sldid = max(existing_sldids, default=256) + 1

    def next_free_rid():
        n = 1
        while f"rId{n}" in existing_rids:
            n += 1
        existing_rids.add(f"rId{n}")
        return f"rId{n}"

    slide4_xml = open(slide_paths[0], encoding="utf-8").read()
    slide4_rels = open(os.path.join(rels_dir, "slide4.xml.rels"), encoding="utf-8").read()

    for g in range(2, n_groups + 1):
        new_name = f"slide{3 + g}.xml"  # slide4 is group 1; group 2 -> slide5, etc.
        new_path = os.path.join(slides_dir, new_name)
        open(new_path, "w", encoding="utf-8").write(slide4_xml)
        open(os.path.join(rels_dir, f"{new_name}.rels"), "w", encoding="utf-8").write(slide4_rels)
        slide_paths.append(new_path)

        if ct_override_m:
            ct = ct.replace("</Types>", ct_override_m.group(0).replace("slide4.xml", new_name) + "</Types>")

        new_rid = next_free_rid()
        pres_rels = pres_rels.replace(
            "</Relationships>",
            f'<Relationship Id="{new_rid}" Type="http://schemas.openxmlformats.org/'
            f'officeDocument/2006/relationships/slide" Target="slides/{new_name}"/>'
            "</Relationships>",
        )
        pres = pres.replace(
            "</p:sldIdLst>",
            f'<p:sldId id="{next_sldid}" r:id="{new_rid}"/></p:sldIdLst>',
        )
        next_sldid += 1

    open(ct_path, "w", encoding="utf-8").write(ct)
    open(pres_path, "w", encoding="utf-8").write(pres)
    open(pres_rels_path, "w", encoding="utf-8").write(pres_rels)
    return slide_paths


def duplicate_category_cards(slide2_xml, groups):
    """Slide 2 ships with 2 example card <p:sp> shapes. Duplicate/trim to
    exactly len(groups) cards, laid out in an even grid."""
    CARD_W, CARD_H, GAP = 5053523, 3032113, 505353
    TOP_Y = 2162009
    SLIDE_W = 12192000

    start = slide2_xml.find('<p:sp><p:nvSpPr><p:cNvPr id="101"')
    end = slide2_xml.find("</p:sp>", slide2_xml.find(
        '<p:sp><p:nvSpPr><p:cNvPr id="102"')) + len("</p:sp>")
    if start == -1 or end == -1:
        raise RuntimeError("Could not locate template category cards on slide 2")
    before, after = slide2_xml[:start], slide2_xml[end:]

    n = max(len(groups), 1)
    total_w = n * CARD_W + (n - 1) * GAP
    left_margin = max((SLIDE_W - total_w) // 2, 300000)
    card_w = CARD_W
    if total_w > SLIDE_W - 600000:
        card_w = (SLIDE_W - 600000 - (n - 1) * GAP) // n
        left_margin = 300000

    def card_shape(shape_id, off_x, title_text, body_text):
        return (
            f'<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="Category Card" '
            f'descr="Category Card"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr>'
            f'<a:xfrm><a:off x="{off_x}" y="{TOP_Y}"/>'
            f'<a:ext cx="{card_w}" cy="{CARD_H}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            f'<a:solidFill><a:srgbClr val="161616"/></a:solidFill>'
            f'<a:ln w="12700" cap="flat" cmpd="sng" algn="ctr">'
            f'<a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>'
            f'<a:prstDash val="solid"/><a:miter lim="800000"/></a:ln></p:spPr>'
            f'<p:txBody><a:bodyPr spcFirstLastPara="0" vert="horz" wrap="square" '
            f'lIns="129540" tIns="129540" rIns="129540" bIns="129540" numCol="1" '
            f'spcCol="1270" anchor="ctr" anchorCtr="0">'
            f'<a:normAutofit fontScale="70000" lnSpcReduction="10000"/></a:bodyPr>'
            f'<a:lstStyle/>'
            f'<a:p><a:pPr marL="0" lvl="0" indent="0" algn="ctr" defTabSz="1511300">'
            f'<a:lnSpc><a:spcPct val="90000"/></a:lnSpc><a:spcBef><a:spcPct val="0"/>'
            f'</a:spcBef><a:spcAft><a:spcPct val="35000"/></a:spcAft><a:buNone/></a:pPr>'
            f'<a:r><a:rPr lang="en-US" sz="3400" b="1" kern="1200" dirty="0">'
            f'<a:solidFill><a:srgbClr val="55E66F"/></a:solidFill></a:rPr>'
            f'<a:t>{title_text}</a:t></a:r></a:p>'
            f'<a:p><a:pPr marL="0" lvl="0" indent="0" algn="ctr" defTabSz="1511300">'
            f'<a:lnSpc><a:spcPct val="90000"/></a:lnSpc><a:spcBef><a:spcPct val="0"/>'
            f'</a:spcBef><a:spcAft><a:spcPct val="35000"/></a:spcAft><a:buNone/></a:pPr>'
            f'<a:r><a:rPr lang="en-US" sz="2400" kern="1200" dirty="0">'
            f'<a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill></a:rPr>'
            f'<a:t>{body_text}</a:t></a:r></a:p></p:txBody></p:sp>'
        )

    cards = []
    for i, g in enumerate(groups[:10]):
        off_x = left_margin + i * (card_w + GAP)
        title = f"{g['group']}  ({g['group_score']:.2f}/3, {g['rag']})"
        cards.append(card_shape(200 + i, off_x, title, g["group_conclussion"]))
    new_xml = before + "".join(cards) + after

    # Recolor each card's title run to its RAG color.
    for g in groups[:10]:
        title = f"{g['group']}  ({g['group_score']:.2f}/3, {g['rag']})"
        new_xml = set_run_color(new_xml, title, RAG_COLORS.get(g["rag"], "888888"))
    return new_xml


# ---------------------------------------------------------------------------
# Radar chart (Slide 1) — overwrite the same media file the relationship
# already points to if the picture shape exists; if the template ships
# without one (a minimal template may omit it entirely, since it's always
# regenerated anyway), synthesize the shape from a known-good fallback
# geometry that matches the original design.
# ---------------------------------------------------------------------------
CHART_ALT_TEXT = "[Rose Chart for Project Group Metrics Statuses]"
# Fallback geometry (EMU) — the original template's rose chart position/size,
# used only when no existing picture shape is found to read geometry from.
FALLBACK_CHART_OFF = (7246213, 1788098)
FALLBACK_CHART_EXT = (4424169, 4424169)


def _next_media_filename(root):
    media_dir = os.path.join(root, "ppt", "media")
    os.makedirs(media_dir, exist_ok=True)
    existing = [f for f in os.listdir(media_dir) if f.startswith("image")]
    nums = []
    for f in existing:
        m = re.match(r"image(\d+)\.", f)
        if m:
            nums.append(int(m.group(1)))
    return f"image{max(nums, default=0) + 1}.png"


def _next_rid(rels_xml):
    used = {int(n) for n in re.findall(r'Id="rId(\d+)"', rels_xml)}
    n = 1
    while n in used:
        n += 1
    return f"rId{n}"


def _next_shape_id(slide_xml):
    used = {int(n) for n in re.findall(r'<p:cNvPr id="(\d+)"', slide_xml)}
    return max(used, default=0) + 1


def render_radar_chart(root, groups):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    slide1_path = os.path.join(root, "ppt", "slides", "slide1.xml")
    rels_path = os.path.join(root, "ppt", "slides", "_rels", "slide1.xml.rels")
    slide1_xml = open(slide1_path, encoding="utf-8").read()
    rels_xml = open(rels_path, encoding="utf-8").read()

    i = slide1_xml.find(f'descr="{CHART_ALT_TEXT}"')

    if i != -1:
        # Existing picture shape found — read its real geometry and target,
        # overwrite that same media file in place. This path never touches
        # the shape's XML at all, so its position/border/etc. are untouched.
        xfrm_m = re.search(r'<a:off x="(\d+)" y="(\d+)"/><a:ext cx="(\d+)" cy="(\d+)"/>',
                            slide1_xml[i:i + 600])
        cx, cy = int(xfrm_m.group(3)), int(xfrm_m.group(4))
        embed_m = re.search(r'<a:blip r:embed="(rId\d+)"/>', slide1_xml[i:i + 400])
        rid = embed_m.group(1)
        target_m = re.search(rf'Id="{rid}"[^>]*Target="([^"]+)"', rels_xml)
        media_rel = target_m.group(1)  # e.g. ../media/image14.png
        media_path = os.path.normpath(os.path.join(root, "ppt", "slides", media_rel))
    else:
        # No picture shape in the template at all — synthesize one. This is
        # expected for a minimal template that omits the chart placeholder
        # entirely (it's always regenerated, so shipping a real or even a
        # placeholder image in the stored template is just dead weight).
        cx, cy = FALLBACK_CHART_EXT
        off_x, off_y = FALLBACK_CHART_OFF
        media_filename = _next_media_filename(root)
        media_path = os.path.join(root, "ppt", "media", media_filename)
        rid = _next_rid(rels_xml)
        shape_id = _next_shape_id(slide1_xml)

        rels_xml = rels_xml.replace(
            "</Relationships>",
            f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/'
            f'officeDocument/2006/relationships/image" Target="../media/{media_filename}"/>'
            "</Relationships>",
        )
        open(rels_path, "w", encoding="utf-8").write(rels_xml)

        pic_xml = (
            f'<p:pic><p:nvPicPr><p:cNvPr id="{shape_id}" name="Picture {shape_id}" '
            f'descr="{CHART_ALT_TEXT}"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/>'
            f'</p:cNvPicPr><p:nvPr/></p:nvPicPr><p:blipFill><a:blip r:embed="{rid}"/>'
            f'<a:stretch><a:fillRect/></a:stretch></p:blipFill><p:spPr>'
            f'<a:xfrm><a:off x="{off_x}" y="{off_y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>'
        )
        slide1_xml = slide1_xml.replace("</p:spTree>", pic_xml + "</p:spTree>")
        open(slide1_path, "w", encoding="utf-8").write(slide1_xml)

    size_in = cx / 914400
    groups = groups[:10]
    labels = [g["group"] for g in groups]
    scores = [g["group_score"] for g in groups]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    scores_c, angles_c = scores + scores[:1], angles + angles[:1]

    fig = plt.figure(figsize=(size_in, size_in), dpi=200)
    fig.patch.set_alpha(0)
    ax = fig.add_subplot(111, polar=True)
    ax.patch.set_alpha(0)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 3)
    ax.set_yticks([1, 2, 3])
    ax.set_yticklabels(["1", "2", "3"], color="#AAAAAA", fontsize=7)
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, color="#FFFFFF", fontsize=9)
    ax.tick_params(axis="x", pad=12)
    ax.spines["polar"].set_color("#666666")
    ax.grid(color="#444444", linewidth=0.6)
    ax.plot(angles_c, scores_c, color="#00F6FF", linewidth=2)
    ax.fill(angles_c, scores_c, color="#00F6FF", alpha=0.15)
    plt.tight_layout(pad=0.6)
    plt.savefig(media_path, transparent=True, dpi=200)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------
def render(template_source, report_model_path, output_path):
    """template_source may be either a path to a zipped .pptx, or a path to a
    directory already containing a reconstructed template tree (see
    build_template_dir_from_parts) — the normal path when staging from
    individually-fetched parts rather than a single zip."""
    with open(report_model_path, encoding="utf-8") as f:
        R = json.load(f)

    work_root = "unpacked"
    if os.path.isdir(template_source):
        # Already-reconstructed tree (e.g. from build_template_dir_from_parts).
        # If it's not already named "unpacked", treat it as work_root directly.
        work_root = template_source
    else:
        if os.path.isdir(work_root):
            for dirpath, dirnames, filenames in os.walk(work_root, topdown=False):
                for fn in filenames:
                    os.remove(os.path.join(dirpath, fn))
                for dn in dirnames:
                    os.rmdir(os.path.join(dirpath, dn))
        with zipfile.ZipFile(template_source) as z:
            z.extractall(work_root)

    groups = R["groups"]
    project = R["project"]
    period = project["reporting_period"]
    run_at = R["last_run_at"]
    author = R["user"]["name"]
    common = R["common"]
    facts = R["facts"]

    # --- Slide 1 ---
    p = os.path.join(work_root, "ppt", "slides", "slide1.xml")
    xml = open(p, encoding="utf-8").read()
    xml = fill_header_line(xml, period, run_at, author)
    xml = replace_first(xml, "[Project Name]", project["name"])
    xml = replace_first(xml, "[Project entry information]", R.get("entryinfo", ""))
    xml = replace_first(xml, "[Metrics types in scope]", facts.get("metrics_types_in_scope", ""))
    xml = replace_first(xml, "[RAG STATUS]", common["rag"])
    score_txt = f'{common["score"]:.2f}' if isinstance(common["score"], (int, float)) else str(common["score"])
    xml = replace_first(xml, "Score: [n.nn] / 3", f"Score: {score_txt} / 3")
    concl = common["conclusion"]
    concl_lines = concl if isinstance(concl, list) else [concl]
    xml = set_multi_paragraph(xml, "[General conclusions about project status]", concl_lines)
    xml = set_shape_fill_by_alt_text(xml, "Overall RAG Status", RAG_COLORS.get(common["rag"], "888888"))
    open(p, "w", encoding="utf-8").write(xml)

    # --- Slide 2 ---
    p = os.path.join(work_root, "ppt", "slides", "slide2.xml")
    xml = open(p, encoding="utf-8").read()
    xml = fill_header_line(xml, period, run_at, author)
    xml = duplicate_category_cards(xml, groups)
    open(p, "w", encoding="utf-8").write(xml)

    # --- Slide 3 ---
    p = os.path.join(work_root, "ppt", "slides", "slide3.xml")
    xml = open(p, encoding="utf-8").read()
    xml = fill_header_line(xml, period, run_at, author)
    top = R.get("top_items", {"red": [], "amber": []})
    for prefix, items in (("RED", top.get("red", [])), ("AMBER", top.get("amber", []))):
        for i in range(1, 6):
            g_tok, i_tok = f"[TOP_{prefix}_{i}_GROUP]", f"[TOP_{prefix}_{i}_ITEM]"
            w_tok, a_tok = f"[TOP_{prefix}_{i}_WHY]", f"[TOP_{prefix}_{i}_ACTION]"
            if i <= len(items):
                it = items[i - 1]
                xml = xml.replace(g_tok, it["group"], 1).replace(i_tok, it["item"], 1)
                xml = xml.replace(w_tok, it["why"], 1).replace(a_tok, it["action"], 1)
            else:
                l1 = re.search(rf"<a:p>(?:(?!</a:p>).)*{i}\. {re.escape(g_tok)}.*?</a:p>", xml, re.DOTALL)
                l2 = re.search(rf"<a:p>(?:(?!</a:p>).)*Action: {re.escape(a_tok)}.*?</a:p>", xml, re.DOTALL)
                if l1: xml = xml.replace(l1.group(0), "")
                if l2: xml = xml.replace(l2.group(0), "")
    open(p, "w", encoding="utf-8").write(xml)

    # --- Slides 4..N (one per group) ---
    slide_paths = duplicate_group_slides(work_root, len(groups))
    for path, g in zip(slide_paths, groups):
        xml = open(path, encoding="utf-8").read()
        xml = replace_first(xml, "G[N]", g["group_key"])
        xml = replace_first(xml, "[Group Metric name N]", g["group"])
        score_txt = f'{g["group_score"]:.2f}' if isinstance(g["group_score"], (int, float)) else str(g["group_score"])
        xml = replace_first(xml, "Score: [n.nn] / 3   |   RAG: [RAG STATUS]",
                             f'Score: {score_txt} / 3   |   RAG: {g["rag"]}')
        badge_idx = xml.find('descr="RAG Status Box"')
        t_idx = xml.find("[RAG Status]", badge_idx)
        xml = xml[:t_idx] + g["rag"] + xml[t_idx + len("[RAG Status]"):]
        xml = set_shape_fill_by_alt_text(xml, "RAG Status Box", RAG_COLORS.get(g["rag"], "888888"))
        xml = replace_first(xml, "[General Conclusion on this metrics category and key recommendations] ",
                             g["group_conclussion"])
        xml = replace_first(xml, "[General Conclusion on this metrics category and key recommendations]",
                             g["group_conclussion"])

        detail = g.get("metric_results", {}).get("detail", []) or g.get("metric_results", {}).get("gaps", [])
        labels_tok = ["[Key data name 1]", "[Key data name N]", "[Key data name N+1]", "[Key data name N+2]"]
        for idx, tok in enumerate(labels_tok):
            if idx < len(detail):
                row = detail[idx]
                label = row.get("label", "") if isinstance(row, dict) else str(row)
                value = row.get("value", "") if isinstance(row, dict) else ""
                xml = xml.replace(tok, label, 1)
                xml = xml.replace(tok, value, 1)
            else:
                xml = xml.replace(tok, "\u2014", 1)
                xml = xml.replace(tok, "\u2014", 1)

        findings = g.get("findings", {})
        xml = xml.replace("[List of RED Findings with some recommendations]", "\x00CRIT\x00", 1)
        xml = xml.replace("[List of AMBER Findings with some recommendations]", "\x00AMBER\x00", 1)
        xml = set_multi_paragraph(xml, "\x00CRIT\x00", findings.get("critical", []))
        xml = set_multi_paragraph(xml, "\x00AMBER\x00", findings.get("amber", []))
        open(path, "w", encoding="utf-8").write(xml)

    # --- Radar chart ---
    render_radar_chart(work_root, groups)

    # --- Repack (pure Python, no shell — see Execution Environment Constraints) ---
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zout:
        for root_dir, dirs, files in os.walk(work_root):
            for file in files:
                abs_path = os.path.join(root_dir, file)
                arc_name = os.path.relpath(abs_path, work_root)
                zout.write(abs_path, arc_name)

    return output_path


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 render.py <template.pptx> <report_model.json> <output.pptx>")
        sys.exit(1)
    out = render(sys.argv[1], sys.argv[2], sys.argv[3])
    print(f"Wrote {out}")
