#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""标注质量校验器 —— 评审 spec 八度标注的工具。

用途：Antigravity（或人）标完一排后跑一遍，评审者也跑同一遍，
两边数字一致才算通过。避免「凭感觉说对」。

四种校验：

  ① 覆盖率    每排标了多少音，哪些没标（漏标的排出来）
  ② 合法性    字段值是否在允许集合内（dot 只允许 u1/u2/d1，
              oct_shift 只允许 0/-1/-2，hui 必须是合法徽位字）
  ③ 内部一致  真实产物（build 出来的 HTML）的发声音高，
              是否落在 spec 标注推出的音区里
              —— 两条独立路径，能抓出「模板没消费该字段」这类实现 bug
  ④ 录音交叉  页面发声 vs 录音基频（aud_base）的八度一致率
              —— 标注对错的客观判据（需 --report，即复测输出的 json）

用法：

  # 青城（无录音）：① ② ③
  python .agents/skills/guqin-audio-check/scripts/verify_annotations.py \
    --spec "模板/baisuzhen-spec.json" --page "模板/agron模板 · 青城山下白素贞.html"

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
    n = len(note.get("pcs") or []) or 1

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True, help="spec JSON 路径")
    ap.add_argument("--page", help="build 出来的跟谱页 HTML（用于内部一致性校验）")
    ap.add_argument("--report", help="复测输出的 json（含 aud_base / oct_verdict）")
    ap.add_argument("--tonic", help="覆盖调性（默认读 spec 的 tonic）")
    args = ap.parse_args()

    spec = json.load(open(args.spec, encoding="utf-8"))
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
