# -*- coding: utf-8 -*-
"""谱面八度记号的**像素级测量**工具 —— 输出客观几何证据，不做主观判读。

为什么要有这个：`crop_rows.py` 的标号图只截简谱区（`box` 的上 62%），
记号正好落在裁切边缘时**目视必漏**（排 9 音 1 曾因此被误判为「四处皆无点」）。
本工具对标号图做二值化 + 连通域分析，把每个实心点相对每个数字的
位移量 (dx, dy) 全部列出来，判读依据变成数字而不是印象。

用法：
    python measure_marks.py --spec 模板/baisuzhen-spec.json --rows D:/tmp/gq_rows --row 8
    python measure_marks.py --spec 模板/baisuzhen-spec.json --rows D:/tmp/gq_rows --row 8 --dump

输出（每音一行 + 每点明细）：
    音 | p | 现有oct_shift | 数字数 | 候选点(相对最近数字的 dx,dy 与判读)

判读规则（青城，PR #22 确立 + R23 复审补充）：
    正上方点 (|dx|<=7, -40<=dy<=-10)  → 高八度 +1
    正下方点 (|dx|<=7,  10<=dy<=50)   → 低八度 -1
    撮：两个点 → 异八度撮（数组）；只有一个点 → 各声部同区
    长横线(宽>60) = 延音线，不影响八度
    宽约30px却不紧贴数字下方的短横杠 = 减字谱笔画，不是下加线
    空心圈 = 泛音；斜撇 = 倚音；两者都不参与八度判定
"""
import argparse
import json
import os

import numpy as np
from PIL import Image
from scipy import ndimage

# 几何判据
UP_DX, UP_DY = 7, (-40, -10)
DN_DX, DN_DY = 7, (10, 50)
NEAR_X = 70          # 点与数字的最大水平距离
SLANT_DX = (20, 70)  # 斜置/右侧点的水平区间


def load_spec(path):
    spec = json.load(open(path, encoding="utf-8"))
    spec["_dir"] = os.path.dirname(os.path.abspath(path))
    return spec


def analyze(png, simp_bottom=None):
    """返回 (digits, points, lines, circles, simp_bottom)。

    分类要点（都踩过坑）：
      * 数字「6」「4」「0」**内部有洞**，不能只用「有无洞」区分数字与空心圈；
        数字靠**尺寸**判（h>=25），空心圈靠**小尺寸 + 有洞**判。
      * marks 图只截简谱区，但其下缘仍会带进减字谱第一行；
        减字谱的字同样有洞、尺寸更大，必须按 **y 分层排除**。
    """
    im = Image.open(png).convert("RGB")
    rgb = np.array(im)
    R, G, B = rgb[:, :, 0].astype(int), rgb[:, :, 1].astype(int), rgb[:, :, 2].astype(int)
    # 只取黑色墨迹，排除标号图上的红/蓝序号与音级
    ink = (R < 140) & (G < 140) & (B < 140) & \
          (abs(R - G) < 30) & (abs(G - B) < 30) & (abs(R - B) < 30)
    lab, n = ndimage.label(ink)

    comps = []
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        m = (lab[sl] == i)
        area = int(m.sum())
        h, w = y1 - y0, x1 - x0
        hole = int(ndimage.binary_fill_holes(m).sum() - area)
        comps.append({"bbox": (x0, y0, x1, y1), "cx": (x0 + x1) // 2, "cy": (y0 + y1) // 2,
                      "w": w, "h": h, "area": area, "hole": hole})

    # --- 简谱区下界 ---
    # marks 图虽只截简谱区（box 的上 62%），其下缘仍会带进减字谱第一行。
    # 青城各排实测减字谱首行都在 y>=164（排 3/8/9 验证），故默认取 160；
    # 若该排布局不同，用 --simp-bottom 覆盖。
    if simp_bottom is None:
        simp_bottom = min(160, im.size[1])

    digits, points, lines, circles = [], [], [], []
    for c in comps:
        x0, y0, x1, y1 = c["bbox"]
        h, w, area, hole = c["h"], c["w"], c["area"], c["hole"]
        if y0 >= simp_bottom:            # 减字谱区，不参与八度判定
            continue
        if w >= 15 and h <= 10:
            c["kind"] = "延音线" if w > 60 else "短横杠(需人工判)"
            lines.append(c)
            continue
        if h >= 25 and 6 <= w <= 45 and area >= 150:
            digits.append(c)              # 数字（有洞也算：6/4/0）
            continue
        if hole > 0 and max(h, w) <= 20:
            circles.append(c)              # 小而有洞 = 泛音记号圈
            continue
        if max(h, w) <= 22 and area >= 40:
            points.append(c)              # 实心点
            continue
    return digits, points, lines, circles, simp_bottom


def classify(pt, digits):
    """给一个点找出所有可能的归属，并给出几何判读。"""
    out = []
    for d in digits:
        dx = pt["cx"] - d["cx"]
        dy = pt["cy"] - d["cy"]
        if abs(dx) > NEAR_X:
            continue
        if abs(dx) <= UP_DX and UP_DY[0] <= dy <= UP_DY[1]:
            verdict = "正上方点→高八度(+1)"
        elif abs(dx) <= DN_DX and DN_DY[0] <= dy <= DN_DY[1]:
            verdict = "正下方点→低八度(-1)"
        elif SLANT_DX[0] <= dx <= SLANT_DX[1] and abs(dy) <= 45:
            verdict = "斜置/右侧点→需人工判归属"
        else:
            verdict = "无归属"
        out.append({"digit": d, "dx": dx, "dy": dy, "verdict": verdict})
    out.sort(key=lambda r: abs(r["dx"]) + abs(r["dy"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--rows", required=True, help="crop_rows.py 的输出目录")
    ap.add_argument("--row", type=int, required=True, help="排号（1 起）")
    ap.add_argument("--dump", action="store_true", help="额外输出全部数字与点的坐标")
    ap.add_argument("--simp-bottom", type=int, default=None,
                    help="简谱区下界 y（默认自动推断，用于排除减字谱行）")
    a = ap.parse_args()

    spec = load_spec(a.spec)
    notes = spec["rows"][a.row - 1]["notes"]
    png = os.path.join(a.rows, "row_%d_marks.png" % a.row)
    if not os.path.exists(png):
        sys_exit("找不到 %s —— 先跑 crop_rows.py" % png)
    digits, points, lines, circles, sb = analyze(png, a.simp_bottom)

    # --- 越界检查：下界之外若还有点状构件，可能是被裁掉的记号 ---
    # 简谱区下界在不同排并不统一（实测：排3/4/8/9 用 160 即可，排2 的记号落在 y=188），
    # 所以这里不自动放宽，而是主动报出来 —— 宁可多提示，也不要静默漏检。
    warn = []
    if a.simp_bottom is None:
        im0 = Image.open(png).convert("RGB")
        rgb0 = np.array(im0)
        R0, G0, B0 = rgb0[:, :, 0].astype(int), rgb0[:, :, 1].astype(int), rgb0[:, :, 2].astype(int)
        ink0 = (R0 < 140) & (G0 < 140) & (B0 < 140) & \
               (abs(R0 - G0) < 30) & (abs(G0 - B0) < 30) & (abs(R0 - B0) < 30)
        lab0, n0 = ndimage.label(ink0)
        for i, sl in enumerate(ndimage.find_objects(lab0), 1):
            y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
            if y0 < sb:
                continue
            m = (lab0[sl] == i)
            area = int(m.sum())
            h, w = y1 - y0, x1 - x0
            if int(ndimage.binary_fill_holes(m).sum() - area) > 0:
                continue
            if max(h, w) <= 24 and area >= 35:
                warn.append((x0, y0, w, h, area))

    print("=== 排 %d  简谱区 y<%d | 数字 %d / 实心点 %d / 横线 %d / 空心圈 %d ===" % (
        a.row, sb, len(digits), len(points), len(lines), len(circles)))
    if warn:
        print()
        print("⚠ 下界之外还检出 %d 个点状构件，可能有记号被裁掉：" % len(warn))
        for x0, y0, w, h, area in sorted(warn, key=lambda t: t[0])[:12]:
            print("    (%d,%d) %dx%d 面积=%d" % (x0, y0, w, h, area))
        print("  若这些是数字上下的八度记号，请调大 --simp-bottom 重跑本排（勿凭印象判读）。")
    print()
    print("--- 记号全局序列（按 x 排序）---")
    stream = []
    for d in digits:
        stream.append((d["cx"], "数字", d))
    for p in points:
        stream.append((p["cx"], "点  ", p))
    for l in lines:
        stream.append((l["cx"], "线  ", l))
    for c in circles:
        stream.append((c["cx"], "圈  ", c))
    for cx, kind, o in sorted(stream, key=lambda t: t[0]):
        extra = ""
        if kind == "点  ":
            cands = classify(o, digits)
            if cands:
                extra = "   → " + " ; ".join(
                    "%s (dx=%+d,dy=%+d)" % (c["verdict"], c["dx"], c["dy"]) for c in cands[:2])
            else:
                extra = "   → 附近无数字"
        elif kind == "线  ":
            extra = "   （%s）" % o["kind"]
        elif kind == "圈  ":
            extra = "   （泛音记号，不参与八度）"
        print("  x=%-5d %s 中心=(%d,%d) %dx%d 面积=%d%s" % (
            cx, kind, o["cx"], o["cy"], o["w"], o["h"], o["area"], extra))

    print()
    print("%-4s %-10s %-12s %s" % ("音", "p", "现有oct_shift", "该音 x 邻域内的记号"))
    print("  ⚠ 按音分组仅供导航：note.x 与实际数字位置有 45–70px 偏差，邻音的记号会串组；")
    print("    判读以「记号全局序列」为准（那里按 x 严格排序，不依赖 note.x）。")
    print("-" * 96)
    for ni, n in enumerate(notes, 1):
        p = n.get("p")
        pl = "/".join(str(x) for x in p) if isinstance(p, list) else str(p)
        octv = n.get("oct_shift")
        octs = json.dumps(octv, ensure_ascii=False) if isinstance(octv, list) else str(octv)
        if n.get("rest"):
            print("%-4d %-10s %-12s (休止符)" % (ni, pl, octs))
            continue
        if n.get("harm"):
            print("%-4d %-10s %-12s (泛音：八度由徽位决定，oct_shift 不适用)" % (ni, pl, octs))
            continue
        nx = n.get("x")
        items = []
        if nx is not None:
            px = nx / 100.0 * 2800
            win = [o for _, k, o in stream if k.strip() in ("数字", "点") and abs(o["cx"] - px) <= 95]
            win.sort(key=lambda o: o["cx"])
            for o in win:
                if k_is_point(o, points):
                    cands = classify(o, digits)
                    d0 = cands[0] if cands else None
                    items.append("点(%d,%d)%s" % (
                        o["cx"], o["cy"],
                        ("→%s" % d0["verdict"]) if d0 else ""))
                else:
                    items.append("数字(%d,%d)" % (o["cx"], o["cy"]))
        print("%-4d %-10s %-12s %s" % (ni, pl, octs, "  ".join(items)))

    if a.dump:
        print()
        print("--- 全部数字 ---")
        for d in sorted(digits, key=lambda x: x["cx"]):
            print("   数字 bbox=%s 中心=(%d,%d) 面积=%d" % (str(d["bbox"]), d["cx"], d["cy"], d["area"]))
        print("--- 全部实心点 ---")
        for p in sorted(points, key=lambda x: x["cx"]):
            print("   点   bbox=%s 中心=(%d,%d) 面积=%d" % (str(p["bbox"]), p["cx"], p["cy"], p["area"]))
        print("--- 全部横线 ---")
        for l in sorted(lines, key=lambda x: x["cx"]):
            print("   线   bbox=%s 宽=%d %s" % (str(l["bbox"]), l["w"], l["kind"]))
        print("--- 全部空心圈（泛音记号）---")
        for c in sorted(circles, key=lambda x: x["cx"]):
            print("   圈   bbox=%s" % str(c["bbox"]))


def sys_exit(msg):
    import sys
    print(msg)
    sys.exit(1)


def k_is_point(o, points):
    """判断一个记号对象是否属于「实心点」集合。"""
    return any(o is p for p in points)


if __name__ == "__main__":
    main()
