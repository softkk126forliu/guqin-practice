#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""谱面记号检测：判定每个音的八度偏移建议值。

从 crop_rows.py 生成的标号图（row_N_marks.png）里检测简谱数字上下的记号，
按古琴谱的记号规则给出 oct_shift 建议值：

    数字上方 1 个实心点  → +1（高八度）
    数字下方（横线之下）1 个实心点 → -1（低八度）
    无上述记号            → 0（默认区）

区分要点：
  * 空心小圆圈 = 泛音记号（不参与八度判定）
  * 斜撇（倚音记号）= 不参与八度判定
  * 细长横线且跨度大 = 延音线，**不影响八度**
  * 数字下方的实心小点才是低音标记

用法：
    python detect_marks.py --rows D:/tmp/gq_rows_bs --spec 模板/baisuzhen-spec.json --row 8
    python detect_marks.py --rows D:/tmp/gq_rows_bs --spec 模板/baisuzhen-spec.json --row 3
"""
import argparse
import json
import os

import numpy as np
from PIL import Image
from scipy import ndimage


def load_spec(path):
    return json.load(open(path, encoding="utf-8"))


def analyze(marks_png):
    """返回 (digits, marks, lines)"""
    im = Image.open(marks_png).convert("RGB")
    rgb = np.array(im)
    R, G, B = rgb[:, :, 0].astype(int), rgb[:, :, 1].astype(int), rgb[:, :, 2].astype(int)
    # 只取黑色墨迹，排除红/蓝的序号与音级标注
    ink = (R < 140) & (G < 140) & (B < 140) & \
          (abs(R - G) < 30) & (abs(G - B) < 30) & (abs(R - B) < 30)

    lab, n = ndimage.label(ink)
    digits, marks, lines = [], [], []
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        h, w = y1 - y0, x1 - x0
        m = (lab[sl] == i)
        area = int(m.sum())
        if h <= 8 and w >= 15:                      # 横线
            lines.append((x0, x1, y0, y1)); continue
        if h >= 16 and 5 <= w <= 38 and area >= 80:  # 数字
            digits.append(((x0 + x1) // 2, y0, y1)); continue
        if max(h, w) <= 26 and area >= 25:           # 记号
            hole = int(ndimage.binary_fill_holes(m).sum() - area)
            if hole > 0:
                kind = "o"                        # 空心圈：泛音
            elif h > w * 1.6 or w > h * 1.6:
                kind = "'"                        # 斜撇：倚音
            else:
                kind = "*"                        # 实心点
            marks.append(((x0 + x1) // 2, y0, y1, kind))
    return digits, marks, lines


def suggest(note, digits, marks, lines):
    """给出该音的八度偏移建议：+1 / -1 / 0 / None(上下都有点，需人工判断)

    归属规则：记号按 x 水平位置归属到最近的数字。
    青城的低音标记是「横线之下的小实点」，点可能落在延音线下方，
    离数字底部较远，故下方判定放宽到 70px。
    """
    px = note["x"] * 28
    near = sorted([d for d in digits if abs(d[0] - px) <= 45], key=lambda d: abs(d[0] - px))
    if not near:
        return None, "未定位到数字"
    near = near[:2]                       # 叠写会有两个连通域
    up_pt = dn_pt = 0
    up_oth, dn_oth = [], []
    used = set()                          # 每个记号只归属一个数字，避免重复计数
    for cx, top, bot in near:
        for idx, (mk, y0, y1, k) in enumerate(marks):
            if idx in used or abs(mk - cx) > 20:
                continue
            if y1 <= top + 5 and top - y1 <= 30:            # 数字上方
                used.add(idx)
                if k == "*":
                    up_pt += 1
                else:
                    up_oth.append(k)
            elif y0 >= bot - 5 and y0 - bot <= 70:          # 数字下方（含延音线之下）
                used.add(idx)
                if k == "*":
                    dn_pt += 1
                else:
                    dn_oth.append(k)
    why = []
    if up_pt:
        why.append("上方点×%d" % up_pt)
    if dn_pt:
        why.append("下方点×%d" % dn_pt)
    if up_oth:
        why.append("上方%s" % "".join(up_oth))
    if dn_oth:
        why.append("下方%s" % "".join(dn_oth))
    if up_pt and dn_pt:
        return None, "上下都有点：" + "+".join(why)
    if up_pt:
        return 1, "+".join(why)
    if dn_pt:
        return -1, "+".join(why)
    return 0, "+".join(why) if why else "无记号"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", required=True, help="crop_rows.py 的输出目录")
    ap.add_argument("--spec", required=True)
    ap.add_argument("--row", type=int, required=True, help="排号（1 起）")
    args = ap.parse_args()

    spec = load_spec(args.spec)
    notes = spec["rows"][args.row - 1]["notes"]
    digits, marks, lines = analyze(os.path.join(args.rows, "row_%d_marks.png" % args.row))

    print("=== 排 %d：横线 ===" % args.row)
    for x0, x1, y0, y1 in sorted(lines, key=lambda t: t[0]):
        print("  x %4d-%4d (宽%4d)  %s" % (x0, x1, x1 - x0,
                                        "延音线（不影响八度）" if x1 - x0 > 60 else "短横线"))
    print()
    print("%-4s %-10s %-8s %-8s %s" % ("音", "p", "建议", "依据", "说明"))
    counts = {}
    for ni, n in enumerate(notes, 1):
        s, why = suggest(n, digits, marks, lines)
        counts[s] = counts.get(s, 0) + 1
        p = "/".join(str(x) for x in (n.get("p") or []))
        print("%-4d %-10s %-8s %-8s %s" % (ni, p, str(s), why, ""))
    print()
    print("分布：%s" % {str(k): v for k, v in sorted(counts.items(), key=lambda t: str(t[0]))})


if __name__ == "__main__":
    main()
