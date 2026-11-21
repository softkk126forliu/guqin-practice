#!/usr/bin/env python3
"""校验检查脚本的八度规划复刻与页面模板是否一致。

背景
----
`audio_score_check.py` 的 `page_midis()` 是模板 `page.template.html` 中八度规划
逻辑的手工复刻。两者一旦分叉，复测报告里的 `page_sound` 就与页面实际发声不符，
所有基于复测报告的结论都会失真（PR #12 的 HUD 修复、PR #15 的 d1 修正都曾因此
需要反复排查）。

本脚本不再依赖"手工复刻是否写对"，而是**从模板文件里真实提取规划代码块**，
用 node 执行它，再与 `page_midis()` 的输出逐音对账。

用法
----
    python check_sync.py --page "春风/古琴跟谱 · 春风_agron_my.html"
    python check_sync.py --page "模板/agron模板 · 青城山下白素贞.html"

退出码 0 = 一致；1 = 有分歧（打印分歧明细）。
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
# 模板位于同级 skill：guqin-score-page/templates/page.template.html
TEMPLATE = os.path.normpath(os.path.join(
    SKILL_DIR, "..", "guqin-score-page", "templates", "page.template.html"))


def extract_plan_block(tpl_text):
    """从模板里截出 `const MIDI = []; { ... }` 整块（含 dotZone）。"""
    start = tpl_text.find("const MIDI = [];")
    if start < 0:
        sys.exit("模板中找不到 `const MIDI = [];`")
    # 从 start 找到块结束的 `}`（forEach 后的那个）
    depth = 0
    i = start
    begun = False
    while i < len(tpl_text):
        ch = tpl_text[i]
        if ch == "{":
            depth += 1
            begun = True
        elif ch == "}":
            depth -= 1
            if begun and depth == 0:
                return tpl_text[start:i + 1]
        i += 1
    sys.exit("模板中规划块未闭合")


def extract_eff_fn(tpl_text):
    """截出 effMidiOf 函数（模板侧的发声换算）。"""
    m = re.search(r"function\s+effMidiOf\s*\([^)]*\)\s*\{.*?\n\}", tpl_text, re.S)
    if not m:
        sys.exit("模板中找不到 effMidiOf 函数")
    return m.group(0)


def run_template(tpl_text, cells):
    """用 node 执行模板的真实规划代码，返回 (规划值, 发声值) 两组列表。"""
    block = extract_plan_block(tpl_text)
    eff_fn = extract_eff_fn(tpl_text)
    js = (
        "const CELLS = " + json.dumps(cells, ensure_ascii=False) + ";\n"
        + eff_fn + "\n"
        + block + "\n"
        + "const EFF = MIDI.map(ms => ms.map(m => effMidiOf(m, CELLS[ms.__i || 0].harm)));\n"
        + "console.log(JSON.stringify({plan: MIDI, eff: MIDI.map((ms, i) =>"
          " ms.map(m => effMidiOf(m, CELLS[i].harm)))}));"
    )
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                     encoding="utf-8") as f:
        f.write(js)
        path = f.name
    try:
        r = subprocess.run(["node", path], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if r.returncode != 0:
            sys.exit("node 执行模板规划块失败:\n" + (r.stderr or "")[:2000])
        return json.loads(r.stdout.strip())
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def rel(p):
    """显示相对路径（便于把输出贴进 issue / PR）。"""
    try:
        r = os.path.relpath(p, os.getcwd())
    except ValueError:
        return p
    return r.replace("\\", "/")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", required=True, help="跟谱页 HTML 路径")
    ap.add_argument("--template", default=TEMPLATE, help="模板路径（默认用 skill 里的）")
    args = ap.parse_args()

    if not os.path.exists(args.template):
        sys.exit("找不到模板: " + args.template)
    tpl_text = open(args.template, encoding="utf-8").read()

    html = open(args.page, encoding="utf-8").read()
    m = re.search(r"const CELLS\s*=\s*(\[.*?\]);", html, re.S)
    if not m:
        sys.exit("HTML 中找不到 const CELLS = [...]")
    cells = json.loads(m.group(1))

    # 1. 模板真实执行结果
    tpl = run_template(tpl_text, cells)
    tpl_plan = tpl["plan"]
    tpl_eff = tpl["eff"]

    # 2. 检查脚本复刻结果
    sys.path.insert(0, HERE)
    import audio_score_check as asc
    score = asc.load_score(page=args.page)
    rep = asc.page_midis(score)

    if len(tpl_plan) != len(rep):
        print("✗ 长度不一致: 模板 %d  复刻 %d" % (len(tpl_plan), len(rep)))
        return 1

    diffs = []
    for i, (tp, te, r) in enumerate(zip(tpl_plan, tpl_eff, rep)):
        rep_eff = list(r[1])  # eff_m
        if te != rep_eff:
            c = cells[i]
            diffs.append((i, c.get("p"), c.get("dot", ""), tp, te, rep_eff))

    total = len([c for c in cells if not (c.get("rest") or not c.get("pcs"))])
    print("模板: %s" % rel(args.template))
    print("页面: %s" % rel(args.page))
    print("可比音数: %d" % total)
    if not diffs:
        print("✓ 完全一致 —— 检查脚本的复刻与模板逐音相符")
        return 0

    print("✗ 有 %d 个音不一致：" % len(diffs))
    for i, p, dot, tp, te, re_ in diffs[:30]:
        print("   音#%-4d p=%-12s dot=%-4s 模板规划=%-14s 模板发声=%-16s 复刻发声=%s"
              % (i + 1, str(p), dot or "无", tp, te, re_))
    if len(diffs) > 30:
        print("   ... 其余 %d 个省略" % (len(diffs) - 30))
    return 1


if __name__ == "__main__":
    sys.exit(main())
