# -*- coding: utf-8 -*-
"""《春风》第 1 页 agron_my 单文件 HTML 构建脚本。

直接读取 program/春风/out_cf_agron_my/ 下已生成的 2800px 无损 PNG 缓存，
1 秒内生成 program/春风/古琴跟谱 · 春风_agron_my.html 及对位校验图 all_6_rows_boxes_v2.jpg。
"""
import json, os, sys
sys.dont_write_bytecode = True
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
CF_DIR = os.path.abspath(os.path.join(HERE, "..", "..", "春风"))
OUT_DIR = os.path.join(CF_DIR, "out_cf_agron_my")
PNG_DIR = os.path.join(OUT_DIR, "my_cf_rows")

from make_baisuzhen_agron_my import load_template, fill_template

html_tpl = fill_template(
    load_template(),
    title="春风（第一页）",
    subtitle="许国华、龚一 曲 · 1 = ♭B 紧五弦定弦（2 3 5 6 1 2 3） · 2800px 无损矢量级超清修复版",
    nm=["C", "D♭", "D", "E♭", "E", "F", "G♭", "G", "A♭", "A", "B♭", "B"],
)

SCALE_bB = {"1": 10, "2": 0, "3": 2, "4": 3, "5": 5, "6": 7, "7": 9}

# Refined exact [left%, width%] (x, w) for all 98 notes across 6 rows so every box frames the full Jianpu + Jianzipu
rows_cells_exact = [
    # Row 1 (12 cells, BPM 56)
    [
        {"p": "6", "d": 2, "x": 5.0, "w": 6.2},
        {"p": "3", "d": 2, "x": 15.2, "w": 6.8},
        {"p": "6/3", "d": 1, "x": 28.0, "w": 5.0},
        {"p": "7/3", "d": 3, "x": 35.2, "w": 4.6},
        {"p": "1", "d": 0.5, "x": 48.0, "w": 6.0},
        {"p": "7", "d": 1.5, "x": 55.4, "w": 4.1},
        {"p": "6", "d": 0.5, "x": 60.8, "w": 3.7},
        {"p": "6", "d": 1.5, "x": 65.5, "w": 4.0},
        {"p": "3", "d": 1, "x": 72.8, "w": 6.4},
        {"p": "2", "d": 1, "x": 79.6, "w": 3.9},
        {"p": "1", "d": 1, "x": 84.3, "w": 3.7},
        {"p": "7", "d": 1, "x": 88.6, "w": 4.0},
    ],
    # Row 2 (15 cells, BPM 56)
    [
        {"p": "6", "d": 1, "x": 2.2, "w": 3.3},
        {"p": "3", "d": 1, "x": 7.3, "w": 3.9},
        {"p": "6", "d": 1, "x": 13.4, "w": 3.6},
        {"p": "7", "d": 1, "x": 19.2, "w": 3.8},
        {"p": "3", "d": 0.5, "x": 28.0, "w": 3.4},
        {"p": "2", "d": 0.5, "x": 31.4, "w": 3.0},
        {"p": "1", "d": 0.5, "x": 36.8, "w": 3.2},
        {"p": "7", "d": 0.5, "x": 40.0, "w": 3.8},
        {"p": "6", "d": 0.5, "x": 46.0, "w": 3.0},
        {"p": "3", "d": 0.5, "x": 49.0, "w": 3.2},
        {"p": "6", "d": 0.5, "x": 54.8, "w": 3.0},
        {"p": "7", "d": 0.5, "x": 57.8, "w": 3.4},
        {"p": "1", "d": 1, "x": 66.2, "w": 6.1},
        {"p": "7", "d": 1, "x": 73.0, "w": 9.2},
        {"p": "6", "d": 2, "x": 83.2, "w": 6.4},
    ],
    # Row 3 (13 cells, BPM 56)
    [
        {"p": "5", "d": 0.5, "x": 2.2, "w": 3.3},
        {"p": "6", "d": 0.5, "x": 5.5, "w": 3.5},
        {"p": "6", "d": 0.5, "x": 12.0, "w": 3.0},
        {"p": "5", "d": 0.5, "x": 15.0, "w": 3.6},
        {"p": "3", "d": 1, "x": 22.3, "w": 6.9},
        {"p": "3", "d": 1.5, "x": 32.5, "w": 4.5},
        {"p": "6", "d": 2, "x": 45.8, "w": 7.7},
        {"p": "3", "d": 2, "x": 59.0, "w": 7.0},
        {"p": "1", "d": 0.5, "x": 75.2, "w": 3.1},
        {"p": "2", "d": 0.5, "x": 78.3, "w": 3.7},
        {"p": "6", "d": 0.5, "x": 84.0, "w": 2.8},
        {"p": "5", "d": 0.5, "x": 86.8, "w": 3.0},
        {"p": "2", "d": 1, "x": 91.6, "w": 4.2},
    ],
    # Row 4 (19 cells, BPM 66)
    [
        {"p": "3", "d": 0.5, "x": 3.0, "w": 3.8},
        {"p": "3", "d": 1, "x": 7.3, "w": 6.7},
        {"p": "3/6", "d": 0.5, "x": 14.5, "w": 4.5},
        {"p": "3", "d": 1, "x": 19.8, "w": 3.7},
        {"p": "3/6", "d": 1, "x": 24.4, "w": 4.6},
        {"p": "3", "d": 0.5, "x": 31.5, "w": 3.3},
        {"p": "3", "d": 1, "x": 35.0, "w": 5.2},
        {"p": "3/6", "d": 0.5, "x": 40.8, "w": 3.4},
        {"p": "3", "d": 1, "x": 45.2, "w": 3.3},
        {"p": "3/6", "d": 1, "x": 49.0, "w": 3.4},
        {"p": "2", "d": 0.5, "x": 54.6, "w": 4.5},
        {"p": "2/5", "d": 0.5, "x": 59.3, "w": 4.2},
        {"p": "2/5", "d": 1, "x": 63.6, "w": 3.2},
        {"p": "2", "d": 1, "x": 67.8, "w": 3.8},
        {"p": "2/5", "d": 1, "x": 72.0, "w": 4.2},
        {"p": "3", "d": 0.5, "x": 78.0, "w": 3.6},
        {"p": "3/6", "d": 0.5, "x": 82.0, "w": 4.2},
        {"p": "3/6", "d": 1, "x": 86.5, "w": 3.1},
        {"p": "3/6", "d": 2, "x": 90.0, "w": 3.5},
    ],
    # Row 5 (22 cells, BPM 126)
    [
        {"p": "6", "d": 0.5, "x": 3.1, "w": 4.1},
        {"p": "6", "d": 0.25, "x": 7.2, "w": 3.0},
        {"p": "6", "d": 0.25, "x": 10.2, "w": 3.2},
        {"p": "6", "d": 0.5, "x": 15.4, "w": 2.8},
        {"p": "3", "d": 0.5, "x": 18.2, "w": 3.8},
        {"p": "6", "d": 0.5, "x": 25.8, "w": 3.0},
        {"p": "6", "d": 0.25, "x": 28.8, "w": 3.0},
        {"p": "6", "d": 0.25, "x": 31.8, "w": 3.0},
        {"p": "6", "d": 0.5, "x": 37.0, "w": 3.0},
        {"p": "3", "d": 0.5, "x": 40.0, "w": 3.0},
        {"p": "6", "d": 0.5, "x": 47.5, "w": 3.0},
        {"p": "6", "d": 0.25, "x": 50.5, "w": 2.9},
        {"p": "6", "d": 0.25, "x": 53.4, "w": 3.0},
        {"p": "6", "d": 0.5, "x": 58.2, "w": 2.6},
        {"p": "7", "d": 0.5, "x": 60.8, "w": 3.7},
        {"p": "1", "d": 1, "x": 68.4, "w": 3.8},
        {"p": "7", "d": 0.5, "x": 75.0, "w": 2.8},
        {"p": "6", "d": 0.5, "x": 77.8, "w": 3.4},
        {"p": "7", "d": 0.5, "x": 84.8, "w": 3.2},
        {"p": "6", "d": 0.5, "x": 88.0, "w": 2.8},
        {"p": "7", "d": 0.5, "x": 92.2, "w": 2.6},
        {"p": "5", "d": 0.5, "x": 94.8, "w": 3.6},
    ],
    # Row 6 (17 cells, BPM 126)
    [
        {"p": "6", "d": 2, "x": 1.6, "w": 4.0},
        {"p": "6", "d": 1, "x": 15.8, "w": 3.4},
        {"p": "6/3", "d": 1, "x": 21.6, "w": 4.6},
        {"p": "0", "d": 0.5, "x": 29.6, "w": 2.4},
        {"p": "7", "d": 0.5, "x": 32.0, "w": 3.8},
        {"p": "1", "d": 1, "x": 38.2, "w": 3.8},
        {"p": "1", "d": 0.5, "x": 45.2, "w": 2.8},
        {"p": "2", "d": 0.5, "x": 48.0, "w": 3.2},
        {"p": "2", "d": 0.5, "x": 52.5, "w": 2.7},
        {"p": "3", "d": 0.5, "x": 55.2, "w": 3.2},
        {"p": "3", "d": 2, "x": 60.2, "w": 4.8},
        {"p": "3", "d": 1, "x": 73.0, "w": 3.5},
        {"p": "3", "d": 1, "x": 78.8, "w": 4.2},
        {"p": "4", "d": 0.5, "x": 85.6, "w": 3.9},
        {"p": "3", "d": 0.5, "x": 89.5, "w": 2.4},
        {"p": "3", "d": 0.5, "x": 92.2, "w": 2.8},
        {"p": "2", "d": 0.5, "x": 95.0, "w": 3.4},
    ],
]
row_bpms = [56, 56, 56, 66, 126, 126]

def is_harmonic_cf(ri, ni):
    if ri in (0, 1, 2):
        return True
    if ri == 3:
        return ni < 10
    return False

b64_rows = json.load(open(os.path.join(OUT_DIR, "my_cf_rows_b64.json"), encoding="utf-8"))

# 谱面八度点标记（dot）取自 spec，与主路径 guqin_page.py 保持一致。
# 行/音序号与 rows_cells_exact 一一对应。
_spec = json.load(open(os.path.join(CF_DIR, "chunfeng-p1-spec.json"), encoding="utf-8"))
_dots = [[n.get("dot", "") or "" for n in r["notes"]] for r in _spec["rows"]]

# 两份数据（spec 与本脚本硬编码的 rows_cells_exact）必须逐排等长，
# 否则按 (排, 音) 取 dot 会错位。错位是静默的音高错误，必须 fail fast。
if len(_dots) != len(rows_cells_exact):
    raise SystemExit(
        "spec 排数 %d 与 rows_cells_exact 排数 %d 不一致，无法按 (排,音) 对应 dot"
        % (len(_dots), len(rows_cells_exact))
    )
for _ri, (_row_dots, _row_notes) in enumerate(zip(_dots, rows_cells_exact)):
    if len(_row_dots) != len(_row_notes):
        raise SystemExit(
            "第 %d 排音数不一致: spec %d 个, rows_cells_exact %d 个。"
            " 两份数据已分叉，dot 不能按序号对应。"
            % (_ri + 1, len(_row_dots), len(_row_notes))
        )

rows_meta = []
cells = []
for ri, r_notes in enumerate(rows_cells_exact):
    im = Image.open(os.path.join(PNG_DIR, f"row_{ri+1}.png"))
    rows_meta.append({
        "w": im.width,
        "h": im.height,
        "bpm": row_bpms[ri],
        "count": len(r_notes),
    })
    for ni, n in enumerate(r_notes):
        p_raw = str(n["p"]).strip()
        rest = 1 if p_raw in ("0", "-", "") else 0
        p_strs = [] if rest else p_raw.split("/")
        pcs = [SCALE_bB[x] for x in p_strs]
        harm = 1 if (not rest and is_harmonic_cf(ri, ni)) else 0
        cells.append({
            "r": ri,
            "ni": ni,
            "p": p_strs,
            "pcs": pcs,
            "x": round(n["x"], 2),
            "w": round(n["w"], 2),
            "d": n["d"],
            "rest": rest,
            "harm": harm,
            "dot": ("" if rest else _dots[ri][ni]),
        })

out_html = (html_tpl
    .replace("@@IMGS@@", json.dumps(b64_rows))
    .replace("@@ROWS@@", json.dumps(rows_meta))
    .replace("@@CELLS@@", json.dumps(cells, ensure_ascii=False))
)

out_path = os.path.join(CF_DIR, "古琴跟谱 · 春风_agron_my.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(out_html)

print("Generated:", out_path, f"{os.path.getsize(out_path)//1024} KB, {len(cells)} cells, {len(rows_meta)} rows")

# Render check preview of all 6 rows with the refined boxes
ims = [Image.open(os.path.join(PNG_DIR, f"row_{r}.png")).convert("RGB") for r in range(1, 7)]
for c in cells:
    im = ims[c["r"]]
    dr = ImageDraw.Draw(im, "RGBA")
    x0 = c["x"] / 100.0 * im.width
    x1 = (c["x"] + c["w"]) / 100.0 * im.width
    y0 = 0.015 * im.height
    y1 = 0.985 * im.height
    dr.rectangle([x0, y0, x1, y1], outline=(184, 55, 40, 220), fill=(184, 55, 40, 35), width=4)

out_prev = Image.new("RGB", (2800, sum(im.height for im in ims)), (252, 249, 240))
for i, im in enumerate(ims):
    out_prev.paste(im, (0, sum(x.height for x in ims[:i])))
out_prev.resize((1600, int(out_prev.height * 1600 / 2800))).save(os.path.join(OUT_DIR, "all_6_rows_boxes_v2.jpg"), quality=90)
print("Saved all_6_rows_boxes_v2.jpg in", OUT_DIR)
