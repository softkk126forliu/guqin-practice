#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""标注质量校验器 —— 评审 spec 八度标注的工具。

用途：Antigravity（或人）标完一排后跑一遍，评审者也跑同一遍，
两边数字一致才算通过。避免「凭感觉说对」。

五种校验：

  ① 覆盖率    每排标了多少音，哪些没标（漏标的排出来）
  ② 合法性    字段值是否在允许集合内（dot 只允许 u1/u2/d1，
              oct_shift 只允许 -1/0/1 或等长数组，hui 必须是合法徽位字）
  ③ 内部一致  真实产物（build 出来的 HTML）的发声音高，
              是否落在 spec 标注推出的音区里
              —— 两条独立路径，能抓出「模板没消费该字段」这类实现 bug
  ④ 录音交叉  页面发声 vs 录音基频（aud_base）的八度一致率
              —— 标注对错的客观判据（需 --report，即复测输出的 json）
  ⑤ 谱面对账  spec 标注 vs 谱面行图像素测量（需 --rows，即 crop_rows.py 输出目录）
              —— 用独立连通域 + 逐行墨迹剖面核对每音八度记号，减少只核对模板与脚本的盲区

用法：

  # 青城（无录音）：① ② ③ + ⑤ 谱面对账
  python .agents/skills/guqin-audio-check/scripts/verify_annotations.py \
    --spec "模板/baisuzhen-spec.json" --page "模板/agron模板 · 青城山下白素贞.html" \
    --rows "D:/tmp/gq_rows_bs"

  # 春风（有录音）：加 --report
  python .agents/skills/guqin-audio-check/scripts/verify_annotations.py \
    --spec "春风/chunfeng-p1-spec.json" --page "春风/古琴跟谱 · 春风_agron_my.html" \
    --report "D:/tmp/cf_chk.json"
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

NM = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

VALID_DOT = {"u1", "u2", "d1"}
VALID_SHIFT = {-1, 0, 1}
VALID_HUI = set("一二三四五六七八九十") | {"十一", "十二", "十三"}


def midi_name(m):
    return "%s%d" % (NM[m % 12], m // 12 - 1)



def expect_zones(note):
    """按 spec 标注推出该音各声部应落的 MIDI 区间。

    返回 (zones, why)：zones 是与音数等长的 [(lo,hi), ...]；无标注时 zones 为 None。

    规则（与 page.template.html 的 dotZone / octZone 一致，但独立实现，
    用于交叉验证模板是否正确消费了字段）：
        dot=u1 → 规划 [60,71]；u2 → [72,83]；d1 → [48,59]
        泛音发声 = 规划 + 12，故泛音的期望区间要相应下移一个八度
        oct_shift=0 → [48,59]；+1 → [60,71]；-1 → [36,47]
        标量 = 各声部同区；数组 = 每声部各自的偏移（异八度撮）
    """
    harm = bool(note.get("harm"))
    dot = (note.get("dot") or "").strip()
    shift = note.get("oct_shift")
    n = len(note.get("pcs") or note.get("p") or []) or 1

    if dot in VALID_DOT:
        if dot.startswith("u"):
            k = max(0, int(dot[1:]) - 1) if harm else int(dot[1:])
        else:                       # d1 与无点音同处低音区
            k = 0
        lo, hi = 48 + k * 12, 59 + k * 12
        return [(lo, hi)] * n, "dot=%s%s" % (dot, "/泛音" if harm else "")
    if shift is None:
        return None, "无标注"
    arr = list(shift) if isinstance(shift, (list, tuple)) else [shift] * n
    if len(arr) != n:
        return None, "oct_shift 长度 %d != 音数 %d" % (len(arr), n)
    try:
        ks = [int(k) for k in arr]
    except (TypeError, ValueError):
        return None, "oct_shift 含非整数值"
    if any(k not in VALID_SHIFT for k in ks):
        return None, "oct_shift 含非法偏移 %s" % ks
    return [(48 + k * 12, 59 + k * 12) for k in ks], "oct_shift=%s" % ks


def page_sounds_from_html(path):
    """从真实产物里取每个音的发声音高（MIDI 列表）"""
    import audio_score_check as asc
    score = asc.load_score(page=path)
    midis = asc.page_midis(score)
    out = []
    for c, (hud, eff) in zip(score, midis):
        out.append(dict(row=c["row"], ni=c["ni"], p=c.get("p", []),
                        pcs=c.get("pcs", []), harm=bool(c.get("harm")),
                        dot=c.get("dot", ""), oct_shift=c.get("oct_shift"),
                        eff=list(eff)))
    return out


def _detect_fused_lower_dot(ink, bbox):
    """检测叠写下排数字底端是否粘连了低音点（逐行墨迹宽度剖面：先收窄再增宽）。

    正常叠写数字高度约 30-36px，h >= 42 且底部出现「颈部收窄 → 底部点状增宽」即判定为粘连低音点。
    返回 (True, 说明) 或 (False, "")。
    """
    x0, y0, x1, y1 = bbox
    h = y1 - y0
    if h < 42:
        return False, ""
    sub = ink[y0:y1, x0:x1]
    widths = [int(sub[r].sum()) for r in range(h)]
    tail = widths[-min(20, h):]
    if len(tail) < 10:
        return False, ""
    best_pinch = None
    for idx in range(2, len(tail) - 4):
        pre_max = max(tail[:idx])
        post_seg = tail[idx + 1:]
        post_max = max(post_seg)
        v = tail[idx]
        if v <= 9 and pre_max - v >= 1 and post_max - v >= 3 and 9 <= post_max <= 16:
            wide_rows = sum(1 for w in post_seg if w >= v + 3)
            if wide_rows >= 3:
                best_pinch = (pre_max, v, post_max)
                break
    if best_pinch:
        return True, "粘连低音点(剖面%d→%d→%d)" % best_pinch
    return False, ""


def _scan_row_image(rows_dir, ri, notes):
    """对单排谱面图做黑色墨迹连通域分析，返回 (ink, digits, points, src_tag, im_w, y_limit)。"""
    import numpy as np
    from PIL import Image
    from scipy import ndimage

    marks_png = os.path.join(rows_dir, "row_%d_marks.png" % ri)
    full_png = os.path.join(rows_dir, "row_%d.png" % ri)
    if not os.path.exists(marks_png) and not os.path.exists(full_png):
        return None

    use_png = marks_png if os.path.exists(marks_png) else full_png
    src_tag = "marks"
    im = Image.open(use_png).convert("RGB")
    # marks 图过浅（如排13 仅 148px）会截断下排数字与点，自动改用整排图
    if use_png == marks_png and im.size[1] < 180 and os.path.exists(full_png):
        use_png = full_png
        src_tag = "整排图"
        im = Image.open(use_png).convert("RGB")

    rgb = np.array(im)
    R, G, B = rgb[:, :, 0].astype(int), rgb[:, :, 1].astype(int), rgb[:, :, 2].astype(int)
    ink = (R < 140) & (G < 140) & (B < 140) & \
          (abs(R - G) < 30) & (abs(G - B) < 30) & (abs(R - B) < 30)
    lab, _ = ndimage.label(ink)

    im_w, im_h = im.size
    raw_comps = []
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        m = (lab[sl] == i)
        area = int(m.sum())
        h, w = y1 - y0, x1 - x0
        hole = int(ndimage.binary_fill_holes(m).sum() - area)
        raw_comps.append({
            "bbox": (x0, y0, x1, y1),
            "cx": (x0 + x1) // 2, "cy": (y0 + y1) // 2,
            "w": w, "h": h, "area": area, "hole": hole,
        })

    # 先按 note 中心附近定位简谱数字，自适应估算该排简谱区下界 y_limit（防不同排 y 偏移漏检）
    note_xcs = [
        (n["x"] + n.get("w", 3.5) / 2.0) / 100.0 * im_w
        for n in notes if n.get("p") and not n.get("rest") and n.get("x") is not None
    ]
    cand_digits = []
    for c in raw_comps:
        x0, y0, x1, y1 = c["bbox"]
        h, w, area = c["h"], c["w"], c["area"]
        if y0 >= min(im_h, 200):
            continue
        if h >= 25 and 12 <= w <= 45 and area >= 150:
            # 排除细长小节线与低填充率倚音斜撇
            if w <= 11 and h >= 65:
                continue
            if area / float(max(w * h, 1)) < 0.36:
                continue
            cand_digits.append(c)

    matched_y1 = [
        d["bbox"][3] for d in cand_digits
        if any(abs(d["cx"] - xc) <= 40 for xc in note_xcs)
    ]
    if matched_y1:
        y_limit = min(im_h, max(matched_y1) + 55, 235)
    else:
        y_limit = min(im_h, 190)

    digits = [d for d in cand_digits if d["bbox"][1] < y_limit]
    points = []
    for c in raw_comps:
        x0, y0, x1, y1 = c["bbox"]
        h, w, area, hole = c["h"], c["w"], c["area"], c["hole"]
        if y0 >= y_limit:
            continue
        if hole == 0 and max(h, w) <= 22 and area >= 40 and not (w >= 15 and h <= 10):
            points.append(c)

    return ink, digits, points, src_tag, im_w, y_limit


def _reconcile_note_with_score(n, ink, digits, points, im_w):
    """将单个非泛音音的 spec oct_shift 与谱面像素测量对账。

    返回 (status, expected_oct, actual_oct, evidence)
      status: 'ok' | 'mismatch' | 'review'
    """
    p = n.get("p") or []
    is_cuo = len(p) == 2
    sh = n.get("oct_shift")
    if is_cuo:
        spec_norm = list(sh) if isinstance(sh, (list, tuple)) else [sh, sh]
    else:
        spec_norm = sh[0] if isinstance(sh, (list, tuple)) else sh

    if n.get("x") is None:
        return "review", None, spec_norm, "缺 note.x"

    xc = (n["x"] + n.get("w", 3.5) / 2.0) / 100.0 * im_w
    near_d = [d for d in digits if abs(d["cx"] - xc) <= 38]
    if not near_d:
        return "review", None, spec_norm, "x=%.0f 附近未定位到数字" % xc

    if not is_cuo:
        # 单音：先排除明显落在下缘减字谱区的构件，再选最上方且水平接近的数字
        top_cy = min(d["cy"] for d in near_d)
        top_band = [d for d in near_d if d["cy"] <= top_cy + 30]
        d = min(top_band, key=lambda t: abs(t["cx"] - xc))
        up_pts = [
            pt for pt in points
            if abs(pt["cx"] - d["cx"]) <= 9 and -45 <= (pt["cy"] - d["cy"]) <= -10
        ]
        dn_pts = [
            pt for pt in points
            if abs(pt["cx"] - d["cx"]) <= 9 and 10 <= (pt["cy"] - d["cy"]) <= 55
        ]
        has_up = bool(up_pts)
        has_dn = bool(dn_pts)
        if has_up and has_dn:
            return "review", None, spec_norm, "数字(%d,%d) 上下同时检出点" % (d["cx"], d["cy"])
        if has_up:
            inferred = 1
            ev = "上方点(%d,%d)" % (up_pts[0]["cx"], up_pts[0]["cy"])
        elif dn_pts:
            inferred = -1
            ev = "下方点(%d,%d)" % (dn_pts[0]["cx"], dn_pts[0]["cy"])
        else:
            inferred = 0
            ev = "无点"
        status = "ok" if inferred == spec_norm else "mismatch"
        return status, inferred, spec_norm, ev

    # 撮（上下叠写两数字）：优先选最上方的简谱叠写对（排除下方减字谱首行）
    best_pair = None
    best_score = (1e9, 1e9)
    for i in range(len(near_d)):
        for j in range(i + 1, len(near_d)):
            a, b = near_d[i], near_d[j]
            dy_ab = abs(a["cy"] - b["cy"])
            if abs(a["cx"] - b["cx"]) <= 12 and 25 <= dy_ab <= 68:
                top_c, bot_c = (a, b) if a["cy"] < b["cy"] else (b, a)
                sc = (top_c["cy"], abs((a["cx"] + b["cx"]) / 2.0 - xc))
                if sc < best_score:
                    best_score = sc
                    best_pair = (top_c, bot_c)
    if not best_pair:
        return "review", None, spec_norm, "撮 x=%.0f 未定位到上下叠写两数字" % xc

    top_d, bot_d = best_pair
    top_up = [
        pt for pt in points
        if abs(pt["cx"] - top_d["cx"]) <= 9 and -45 <= (pt["cy"] - top_d["cy"]) <= -10
    ]
    slant = [
        pt for pt in points
        if 20 <= (pt["cx"] - top_d["cx"]) <= 65
        and (abs(pt["cy"] - top_d["cy"]) <= 40 or abs(pt["cy"] - bot_d["cy"]) <= 40)
    ]
    mid_pts = [
        pt for pt in points
        if abs(pt["cx"] - top_d["cx"]) <= 9
        and (top_d["bbox"][3] - 2) <= pt["cy"] <= (bot_d["bbox"][1] + 2)
    ]
    bot_dn = [
        pt for pt in points
        if abs(pt["cx"] - bot_d["cx"]) <= 9 and 10 <= (pt["cy"] - bot_d["cy"]) <= 55
    ]
    bot_fused, bot_fused_msg = (False, "")
    if not bot_dn:
        bot_fused, bot_fused_msg = _detect_fused_lower_dot(ink, bot_d["bbox"])

    has_top_hi = bool(top_up) or bool(slant)
    has_bot_dn = bool(bot_dn) or bot_fused
    evs = []
    if top_up:
        evs.append("上正点(%d,%d)" % (top_up[0]["cx"], top_up[0]["cy"]))
    if slant:
        evs.append("右上斜点(%d,%d)" % (slant[0]["cx"], slant[0]["cy"]))
    if mid_pts:
        evs.append("字间点(%d,%d)" % (mid_pts[0]["cx"], mid_pts[0]["cy"]))
    if bot_dn:
        evs.append("下正点(%d,%d)" % (bot_dn[0]["cx"], bot_dn[0]["cy"]))
    if bot_fused:
        evs.append(bot_fused_msg)

    if has_top_hi and has_bot_dn:
        inferred = [1, -1]
    elif mid_pts and has_bot_dn:
        inferred = [-1, -1]
    elif has_bot_dn and not has_top_hi and not mid_pts:
        inferred = [-1, -1]
    elif top_up and not has_bot_dn and not mid_pts:
        inferred = [1, 1]
    elif not has_top_hi and not has_bot_dn and not mid_pts:
        inferred = [0, 0]
    else:
        return "review", None, spec_norm, "+".join(evs) or "复杂记号"

    status = "ok" if inferred == spec_norm else "mismatch"
    return status, inferred, spec_norm, "+".join(evs) if evs else "无点"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True, help="spec JSON 路径")
    ap.add_argument("--page", help="build 出来的跟谱页 HTML（用于内部一致性校验）")
    ap.add_argument("--report", help="复测输出的 json（含 aud_base / oct_verdict）")
    ap.add_argument("--rows", help="crop_rows.py 输出目录（启用 ⑤ 谱面对账模式）")
    ap.add_argument("--row", type=int, help="配合 --rows 使用：只对账指定排号（1 起）")
    ap.add_argument("--tonic", help="覆盖调性（默认读 spec 的 tonic）")
    args = ap.parse_args()

    spec = json.load(open(args.spec, encoding="utf-8-sig"))
    rows = spec["rows"]
    tonic_map = {"C": 0, "bB": 10, "bD": 1, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9}
    tonic = tonic_map.get(args.tonic or spec.get("tonic", "C"), 0)

    problems = []

    # ---------- ① 覆盖率 ----------
    print("=" * 68)
    print("① 标注覆盖率")
    print("=" * 68)
    print("%-4s %-6s %-10s %-10s %-8s" % ("排", "音数", "有dot", "有oct_shift", "未标注"))
    cov = []
    for ri, r in enumerate(rows, 1):
        notes = r.get("notes", [])
        nd = ns = un = 0
        for n in notes:
            p = n.get("p")
            if p is None or (isinstance(p, list) and not [x for x in p if str(x).strip()]):
                continue
            has_dot = bool((n.get("dot") or "").strip())
            has_shift = n.get("oct_shift") is not None
            if has_dot:
                nd += 1
            elif has_shift:
                ns += 1
            else:
                un += 1
        cov.append((ri, len(notes), nd, ns, un))
        print("%-4d %-6d %-10d %-10d %-8d" % (ri, len(notes), nd, ns, un))
    total_notes = sum(c[1] for c in cov)
    total_marked = sum(c[2] + c[3] for c in cov)
    total_un = sum(c[4] for c in cov)
    print("-" * 68)
    print("合计 %d 音：已标 %d，未标 %d（%.0f%%）"
          % (total_notes, total_marked, total_un,
             total_marked * 100.0 / max(total_notes, 1)))
    if total_un:
        todo = [c[0] for c in cov if c[4]]
        print("未标完的排：%s" % ", ".join(str(x) for x in todo))

    # ---------- ② 合法性 ----------
    print()
    print("=" * 68)
    print("② 字段合法性 / 待人工确认清单")
    print("=" * 68)
    bad = 0
    pending = []
    for ri, r in enumerate(rows, 1):
        for ni, n in enumerate(r.get("notes", []), 1):
            dot = (n.get("dot") or "").strip()
            if dot and dot not in VALID_DOT:
                print("  ✗ 排%d音%d dot=%r 不在允许集合 %s" % (ri, ni, dot, sorted(VALID_DOT)))
                bad += 1
            sh = n.get("oct_shift")
            if sh is not None:
                npcs = len(n.get("p") or [])
                if isinstance(sh, (list, tuple)):
                    arr = list(sh)
                else:
                    arr = [sh] * max(npcs, 1)   # 标量 = 各声部同区
                if npcs and len(arr) != npcs:
                    print("  ✗ 排%d音%d oct_shift 长度 %d ≠ 音数 %d"
                          % (ri, ni, len(arr), npcs))
                    bad += 1
                for k in arr:
                    try:
                        ki = int(k)
                    except (TypeError, ValueError):
                        print("  ✗ 排%d音%d oct_shift=%r 不是整数" % (ri, ni, k))
                        bad += 1
                        continue
                    if ki not in VALID_SHIFT:
                        print("  ✗ 排%d音%d oct_shift=%d 不在允许集合 %s"
                              % (ri, ni, ki, sorted(VALID_SHIFT)))
                        bad += 1
            hui = n.get("hui")
            if hui not in (None, ""):
                hs = str(hui).strip()
                if hs not in VALID_HUI:
                    print("  ✗ 排%d音%d hui=%r 不是合法徽位字" % (ri, ni, hui))
                    bad += 1
            # 显式标 null = 标注者读不准，转人工
            if ("dot" in n and n["dot"] is None) or ("oct_shift" in n and n["oct_shift"] is None):
                pending.append((ri, ni, "/".join(str(x) for x in (n.get("p") or []))))
    print("  合法性：%s" % ("全部合法" if bad == 0 else "%d 处不合法" % bad))
    if pending:
        print("  待人工确认（显式标 null）：%d 个" % len(pending))
        for row, ni, p in pending[:20]:
            print("    排%d音%-3d %s" % (row, ni, p))
    else:
        print("  待人工确认：0 个")
    if bad:
        problems.append("字段合法性：%d 处不合法" % bad)

    # ---------- ③ 内部一致性 ----------
    print()
    print("=" * 68)
    print("③ 内部一致性（真实产物 vs spec 标注推出的音区）")
    print("=" * 68)
    if not args.page:
        print("  (未提供 --page，跳过)")
    else:
        cells = page_sounds_from_html(args.page)
        checked = mismatch = 0
        mism_list = []
        for c in cells:
            if not c["pcs"]:
                continue
            note = None
            for n in rows[c["row"] - 1]["notes"]:
                if n is None:
                    continue
            # 按 (排, 音序) 取原 note
            raw = rows[c["row"] - 1]["notes"][c["ni"] - 1]
            zs, why = expect_zones(raw)
            if zs is None:
                continue
            checked += 1
            eff = c["eff"]
            if not eff:
                continue
            # 泛音：产物里的 eff 已是发声值；期望区是规划值 → 比较时 +12
            bad_one = False
            for k, (lo, hi) in enumerate(zs):
                cmp_lo, cmp_hi = (lo + 12, hi + 12) if raw.get("harm") else (lo, hi)
                if k >= len(eff):
                    continue
                if not (cmp_lo <= eff[k] <= cmp_hi):
                    bad_one = True
                    mism_list.append((c["row"], c["ni"], "/".join(str(x) for x in c["p"]),
                                      "%s[%d]" % (why, k), cmp_lo, cmp_hi, eff[k]))
            if bad_one:
                mismatch += 1
        print("  可校验 %d 个音，不符 %d 个" % (checked, mismatch))
        for row, ni, p, why, lo, hi, eff in mism_list[:20]:
            print("    排%d音%-3d %-8s [%s] 期望 %d-%d，实际 %s"
                  % (row, ni, p, why, lo, hi, midi_name(eff)))
        if mismatch:
            problems.append("内部一致性：%d 个音不符" % mismatch)

    # ---------- ④ 录音交叉校验 ----------
    print()
    print("=" * 68)
    print("④ 录音交叉校验（页面发声 vs 录音基频）")
    print("=" * 68)
    if not args.report:
        print("  (未提供 --report，跳过 —— 青城无录音，只能用 ①②③)")
    else:
        rep = json.load(open(args.report, encoding="utf-8"))
        notes = rep.get("notes", [])
        if isinstance(notes, dict):
            notes = list(notes.values())
        oct_rows = [n for n in notes if n.get("oct_verdict")]
        ok = sum(n["oct_verdict"] == "八度一致" for n in oct_rows)
        bad = sum(n["oct_verdict"].startswith("页面") for n in oct_rows)
        pcls = sum(n["oct_verdict"] == "音级不符" for n in oct_rows)
        hist = {}
        for n in oct_rows:
            if n["oct_verdict"].startswith("页面"):
                hist[n["oct_verdict"]] = hist.get(n["oct_verdict"], 0) + 1
        print("  可判 %d 个音：八度一致 %d / 偏差 %d / 音级不符 %d"
              % (len(oct_rows), ok, bad, pcls))
        if hist:
            print("  偏差分布：%s" % hist)
        # 按标注类型分组
        grp = {}
        for n in oct_rows:
            key = "泛音" if n.get("harm") else "散按"
            g = grp.setdefault(key, [0, 0])
            g[1] += 1
            if n["oct_verdict"] == "八度一致":
                g[0] += 1
        for k, (o, t) in sorted(grp.items()):
            print("    %s: %d/%d 一致 (%.0f%%)" % (k, o, t, o * 100.0 / max(t, 1)))
        if pcls:
            problems.append("录音交叉：音级不符 %d 个" % pcls)
        print()
        print("  不符明细（前 25）：")
        shown = 0
        for n in oct_rows:
            if n["oct_verdict"] == "八度一致":
                continue
            shown += 1
            if shown > 25:
                break
            print("    排%s音%-3s %-8s 页面=%-10s 录音基频=%-6s %s"
                  % (n.get("row"), n.get("ni"), n.get("jianpu"),
                     n.get("page_sound"), n.get("aud_base"), n.get("oct_verdict")))

    # ---------- ⑤ 谱面对账 ----------
    print()
    print("=" * 68)
    print("⑤ 谱面对账（spec 标注 vs 谱面像素测量 + 粘连剖面）")
    print("=" * 68)
    if not args.rows:
        print("  (未提供 --rows，跳过 —— 传入 crop_rows.py 输出目录可开启谱面对账)")
    else:
        sc_ok = sc_mism = sc_rev = 0
        mism_items = []
        rev_items = []
        row_indices = [args.row] if args.row else list(range(1, len(rows) + 1))
        for ri in row_indices:
            if ri < 1 or ri > len(rows):
                continue
            rnotes = rows[ri - 1].get("notes", [])
            targets = [
                (ni, n) for ni, n in enumerate(rnotes, 1)
                if n.get("p") and not n.get("rest") and not n.get("harm")
                and n.get("oct_shift") is not None
            ]
            if not targets:
                continue
            scanned = _scan_row_image(args.rows, ri, rnotes)
            if scanned is None:
                for ni, n in targets:
                    sc_rev += 1
                    rev_items.append((ri, ni, "/".join(n["p"]), n["oct_shift"], "缺少排图"))
                continue
            ink, digits, points, src_tag, im_w, y_limit = scanned
            for ni, n in targets:
                st, inf, act, ev = _reconcile_note_with_score(n, ink, digits, points, im_w)
                pl = "/".join(str(x) for x in n["p"])
                if st == "ok":
                    sc_ok += 1
                elif st == "mismatch":
                    sc_mism += 1
                    mism_items.append((ri, ni, pl, act, inf, "%s [%s y<%d]" % (ev, src_tag, y_limit)))
                else:
                    sc_rev += 1
                    rev_items.append((ri, ni, pl, act, "%s [%s y<%d]" % (ev, src_tag, y_limit)))
        total_sc = sc_ok + sc_mism + sc_rev
        print("  对账 %d 个已标非泛音音：一致 %d / 冲突 %d / 需人工复核 %d"
              % (total_sc, sc_ok, sc_mism, sc_rev))
        if mism_items:
            print("  ✗ 谱面冲突明细（请重点核查）：")
            for ri, ni, pl, act, inf, ev in mism_items[:30]:
                print("    排%-2d音%-2d %-5s spec=%-8s 谱面=%-8s 依据=%s"
                      % (ri, ni, pl, act, inf, ev))
            problems.append("谱面对账：%d 个音与谱面测量冲突" % sc_mism)
        if rev_items:
            print("  ⚠ 需人工复核明细（未自动定案）：")
            for ri, ni, pl, act, ev in rev_items[:30]:
                print("    排%-2d音%-2d %-5s spec=%-8s 原因=%s"
                      % (ri, ni, pl, act, ev))

    # ---------- 结论 ----------
    print()
    print("=" * 68)
    if problems:
        print("结论：%s" % "；".join(problems))
        print("—— 需要处理后再提交评审")
        return 1
    print("结论：全部检查通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
