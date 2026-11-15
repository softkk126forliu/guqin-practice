# -*- coding: utf-8 -*-
import json, os
from PIL import Image

MAJOR = [0, 2, 4, 5, 7, 9, 11]
NM = ["C", "C♯", "D", "D♯", "E", "F", "F♯", "G", "G♯", "A", "A♯", "B"]

# Determine which notes are harmonics (泛音) based on score structure
def is_harmonic_note(ri, ni):
    # ri is 0-indexed row, ni is 0-indexed note in row
    if ri == 0: return True # Row 1 all harmonics
    if ri == 1: return ni in (0,1,2,3,4,5,10) # Row 2 M1 & M3 harmonics
    if ri == 2: return False # Row 3 stopped/open
    if ri == 3: return ni in (0,1,2,3,4,5) # Row 4 M1 harmonics
    if ri == 4: return ni >= 1 # Row 5 M2 & M3 harmonics
    if ri == 5: return True # Row 6 all harmonics
    if ri == 6: return True # Row 7 all harmonics
    if ri == 7: return False # Row 8 stopped/open
    if ri == 8: return False # Row 9 stopped/open
    if ri == 9: return ni >= 6 # Row 10 M3 harmonics
    if ri == 10: return False # Row 11 stopped/open
    if ri == 11: return False # Row 12 stopped/open
    if ri == 12: return 1 <= ni <= 6 # Row 13 M2 harmonics
    if ri == 13: return ni >= 5 # Row 14 M3 harmonics
    if ri == 14: return True # Row 15 all harmonics
    return False

def build_baisuzhen(scratch):
    spec = json.load(open(os.path.join(scratch, 'baisuzhen-argon-spec.json'), encoding='utf-8'))
    b64_rows = json.load(open(os.path.join(scratch, 'my_rows_b64.json'), encoding='utf-8'))
    rows_meta = []
    cells = []
    for ri, r in enumerate(spec['rows']):
        im = Image.open(os.path.join(scratch, 'my_rows', f'row_{ri+1}.png'))
        rows_meta.append({
            'w': im.width,
            'h': im.height,
            'bpm': r.get('bpm', 60),
            'count': len(r['notes'])
        })
        for ni, n in enumerate(r['notes']):
            rest = 1 if n.get('rest') else 0
            p_strs = [] if rest else [str(x) for x in n['p']]
            pcs = [MAJOR[int(x) - 1] % 12 for x in p_strs]
            harm = 1 if is_harmonic_note(ri, ni) else 0
            is_chord = len(p_strs) >= 2
            base_x = round(n['x'], 2)
            w = 3.80 if is_chord else 3.20
            adj_x = round(base_x - (w - 3.13) / 2, 2)
            cells.append({
                'r': ri,
                'ni': ni,
                'p': p_strs,
                'pcs': pcs,
                'x': adj_x,
                'w': w,
                'd': n['d'],
                'rest': rest,
                'harm': harm
            })
    return b64_rows, rows_meta, cells

html_template = r'''<!DOCTYPE html>
<html lang="zh-CN" data-theme="xuan">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>古琴跟谱 · 青城山下白素贞 (Agron Custom)</title>
<style>
:root {
  --desk: #e6e0d2;
  --bar: #23201c;
  --bar-border: #3a352f;
  --bar-fg: #f2ede2;
  --bar-muted: #b0a798;
  --paper: #fcf9f0;
  --paper-border: #dcd3c0;
  --ink-contrast: 1.12;
  --ink-bright: 1.0;
  --acc: #b83728;
  --acc-soft: rgba(184, 55, 40, 0.16);
  --acc-glow: rgba(184, 55, 40, 0.38);
  --ok: #207848;
  --ok-soft: rgba(32, 120, 72, 0.16);
  --warn: #d98218;
  --sheet-w: 100;
  box-sizing: border-box;
}
:root[data-theme="white"] {
  --desk: #dde1e6;
  --paper: #ffffff;
  --paper-border: #c8cfd8;
}
:root[data-theme="dark"] {
  --desk: #121210;
  --bar: #1a1917;
  --bar-border: #2e2b27;
  --paper: #1f1e1b;
  --paper-border: #35322c;
  --acc: #e25a47;
  --acc-soft: rgba(226, 90, 71, 0.22);
  --acc-glow: rgba(226, 90, 71, 0.45);
}
*, *::before, *::after { box-sizing: inherit; }
html, body {
  height: 100%;
  margin: 0;
  background: var(--desk);
  color: var(--bar-fg);
  font: 14px/1.45 system-ui, -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
  overflow: hidden;
  user-select: none;
}
body { display: flex; flex-direction: column; }

/* 顶部主控栏 */
.topbar {
  background: var(--bar);
  border-bottom: 1px solid var(--bar-border);
  padding: 8px 14px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  z-index: 20;
  box-shadow: 0 2px 12px rgba(0,0,0,0.22);
}
.brand {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-right: 4px;
}
.brand b {
  font: 600 17px "Songti SC", "Noto Serif SC", "STSong", serif;
  letter-spacing: 0.12em;
  color: #fff;
}
.brand span {
  font-size: 12px;
  color: var(--bar-muted);
}
.status-pill {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 10px;
  padding: 5px 12px;
  flex: 1;
  min-width: 240px;
}
.status-main { flex: 1; }
#posText { font-weight: 600; font-size: 13px; color: #fff; }
#posSub { font-size: 11.5px; color: var(--bar-muted); margin-top: 1px; }
#posSub b.hit { color: #5cd68d; }
#posSub b.miss { color: #f4a24c; }
.mic-box {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  min-width: 110px;
}
#hearText { font-size: 12px; font-weight: 600; color: #f6d365; }
.meter {
  width: 96px;
  height: 4px;
  background: rgba(255,255,255,0.14);
  border-radius: 2px;
  overflow: hidden;
  margin-top: 4px;
}
.meter i {
  display: block;
  height: 100%;
  width: 0%;
  background: linear-gradient(90deg, #38b26f, #f6d365, #e25a47);
  transition: width 0.06s linear;
}

.ctrl-group {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}
.ctrl-group label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--bar-muted);
  background: rgba(255,255,255,0.05);
  padding: 4px 8px;
  border-radius: 7px;
  cursor: pointer;
}
.ctrl-group input[type="range"] {
  width: 68px;
  accent-color: var(--acc);
  cursor: pointer;
}
.ctrl-group select, button {
  font: inherit;
  font-size: 12.5px;
  color: var(--bar-fg);
  background: rgba(255,255,255,0.09);
  border: 1px solid rgba(255,255,255,0.14);
  border-radius: 8px;
  padding: 6px 11px;
  cursor: pointer;
  transition: all 0.14s;
}
.ctrl-group select option { background: #23201c; color: #f2ede2; }
button:hover { background: rgba(255,255,255,0.16); border-color: rgba(255,255,255,0.28); }
button.pri { background: var(--acc); color: #fff; border-color: var(--acc); font-weight: 600; }
button.pri:hover { filter: brightness(1.08); }
button.ok { background: var(--ok); color: #fff; border-color: var(--ok); font-weight: 600; }

/* 领奏超清放大窗 (HUD + 2400px 1:1 局部放大) */
#hud {
  display: none;
  background: var(--paper);
  border-bottom: 2px solid var(--acc);
  color: #1f1c18;
  padding: 6px 16px;
  align-items: center;
  justify-content: center;
  gap: 18px;
  z-index: 15;
  box-shadow: 0 4px 14px rgba(0,0,0,0.12);
}
:root[data-theme="dark"] #hud { color: #ebe5da; }
#hud.on { display: flex; }
.hud-card {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 230px;
  padding: 6px 14px;
  border-radius: 10px;
  background: rgba(184, 55, 40, 0.08);
  border: 1px solid rgba(184, 55, 40, 0.25);
}
.hud-jp {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 48px;
  font: 700 26px/1.05 "Georgia", "Times New Roman", serif;
  color: var(--acc);
}
.hud-jp small {
  font: 600 11px/1.2 system-ui, sans-serif;
  color: #665e52;
  margin-bottom: 2px;
}
:root[data-theme="dark"] .hud-jp small { color: #a89f91; }
.hud-meta { font-size: 12.5px; line-height: 1.5; }
.hud-meta b { font-size: 14px; color: var(--acc); }
#lensCanvas {
  width: min(64vw, 680px);
  height: 118px;
  border-radius: 8px;
  border: 1px solid var(--paper-border);
  background: var(--paper);
}

/* 谱面滚动区 */
#sc {
  flex: 1;
  overflow: auto;
  padding: 16px 14px 36px;
  scroll-behavior: smooth;
}
#paper {
  width: min(98%, calc(var(--sheet-w, 100) * 11.4px));
  margin: 0 auto;
  background: var(--paper);
  border: 1px solid var(--paper-border);
  border-radius: 8px;
  padding: 20px 22px 32px;
  box-shadow: 0 8px 28px rgba(0,0,0,0.14);
  transition: background 0.2s, width 0.12s;
}
.sheet-head {
  text-align: center;
  margin: 2px 0 14px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--paper-border);
}
.sheet-head h1 {
  margin: 0;
  font: 600 25px/1.3 "Songti SC", "Noto Serif SC", "STSong", serif;
  letter-spacing: 0.32em;
  color: #181614;
}
.sheet-head p {
  margin: 4px 0 0;
  font-size: 12.5px;
  color: #6e6659;
  letter-spacing: 0.04em;
}
:root[data-theme="dark"] .sheet-head h1 { color: #ece6da; }
:root[data-theme="dark"] .sheet-head p { color: #9c9488; }

.rl {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 12px 2px 3px;
  font: 600 11.5px system-ui, sans-serif;
  color: #847966;
}
.rl::after {
  content: "";
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, var(--paper-border), transparent);
}
.rw {
  position: relative;
  margin: 0 0 4px;
  border-radius: 4px;
}
.rw img {
  display: block;
  width: 100%;
  height: auto;
  mix-blend-mode: multiply;
  filter: contrast(var(--ink-contrast, 1.12)) brightness(var(--ink-bright, 1.0));
  image-rendering: -webkit-optimize-contrast;
}
:root[data-theme="dark"] .rw img {
  mix-blend-mode: normal;
  filter: invert(0.91) hue-rotate(180deg) contrast(var(--ink-contrast, 1.15));
}

/* 音位高亮格 */
.mk {
  position: absolute;
  top: 3%;
  height: 94%;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.12s, box-shadow 0.12s;
}
.mk:hover {
  background: rgba(184, 55, 40, 0.08);
  box-shadow: inset 0 0 0 1px rgba(184, 55, 40, 0.35);
}
.mk.done {
  background: transparent;
}
.mk.cur {
  background: var(--acc-soft);
  box-shadow: 0 0 0 2px var(--acc), 0 0 14px 2px var(--acc-glow);
  z-index: 3;
}
.mk.warn {
  box-shadow: none;
}

/* 矢量简谱/时值角标（可选开启） */
.mk-badge {
  display: none;
  position: absolute;
  top: -13px;
  left: 50%;
  transform: translateX(-50%);
  white-space: nowrap;
  font: 700 10.5px/1.2 system-ui, sans-serif;
  padding: 1px 4px;
  border-radius: 4px;
  background: #fffdf7;
  color: #1f5c38;
  border: 1px solid rgba(31, 92, 56, 0.28);
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  z-index: 4;
  pointer-events: none;
}
:root[data-theme="dark"] .mk-badge {
  background: #2b2925;
  color: #6ee79e;
  border-color: rgba(110, 231, 158, 0.3);
}
#paper.show-badges .mk-badge { display: block; }
#paper.show-badges .rw { margin-top: 14px; }

/* 底部操控栏 */
nav.botbar {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--bar);
  border-top: 1px solid var(--bar-border);
  padding: 8px 14px;
  z-index: 20;
}
nav.botbar button {
  flex: 1;
  min-height: 40px;
  font-size: 13.5px;
}
.beat-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: rgba(255,255,255,0.18);
   display: inline-block;
  margin-right: 5px;
  transition: transform 0.08s, background 0.08s;
}
.beat-dot.flash {
  background: #f6d365;
  transform: scale(1.45);
  box-shadow: 0 0 8px #f6d365;
}

/* 沉浸模式悬浮胶囊 */
#immBar {
  display: none;
  position: fixed;
  right: 16px;
  top: 14px;
  z-index: 30;
  background: rgba(26, 25, 23, 0.88);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255,255,255,0.18);
  border-radius: 999px;
  padding: 5px 10px;
  gap: 6px;
  align-items: center;
  box-shadow: 0 4px 16px rgba(0,0,0,0.35);
}
body.imm .topbar, body.imm nav.botbar { display: none; }
body.imm #immBar { display: flex; }

/* 改时值弹窗 */
dialog {
  border: 1px solid var(--bar-border);
  border-radius: 14px;
  background: var(--bar);
  color: var(--bar-fg);
  width: min(92vw, 600px);
  padding: 18px;
  box-shadow: 0 12px 36px rgba(0,0,0,0.5);
}
dialog::backdrop { background: rgba(0,0,0,0.6); }
dialog textarea {
  width: 100%;
  min-height: 240px;
  margin: 8px 0;
  background: rgba(255,255,255,0.06);
  color: inherit;
  border: 1px solid rgba(255,255,255,0.16);
  border-radius: 8px;
  padding: 10px;
  font: 12.5px/1.65 ui-monospace, Consolas, monospace;
}
.hint { font-size: 12px; color: var(--bar-muted); }
</style>
</head>
<body>

<div class="topbar">
  <div class="brand">
    <b>青城山下白素贞</b>
    <span>1=C · 正调 1 2 4 5 6 1 2</span>
  </div>

  <div class="status-pill">
    <div class="status-main">
      <div id="posText">第 1 / 173 音 · 第 1 排</div>
      <div id="posSub">点谱任意音可直接定位 · 命中 <b class="hit" id="hitCnt">0</b> · 待校准 <b class="miss" id="missCnt">0</b></div>
    </div>
    <div class="mic-box">
      <div id="hearText">麦克风未开启</div>
      <div class="meter"><i id="meterBar"></i></div>
    </div>
  </div>

  <div class="ctrl-group">
    <label title="智能伴随：弹响首音后按节奏平滑推进并用麦克风实时校准；纯听音：严格等待每个音匹配才推进">
      模式
      <select id="followMode">
        <option value="smart" selected>智能伴随(推荐)</option>
        <option value="strict">纯听音推进</option>
      </select>
    </label>
    <label>灵敏<input id="sens" type="range" min="1" max="10" value="6"></label>
    <label>速度<input id="spd" type="range" min="40" max="160" value="100"><span id="spdVal">100%</span></label>
    <label>谱宽<input id="zoom" type="range" min="70" max="180" value="100"></label>
    <label>墨色<input id="ink" type="range" min="1" max="10" value="6"></label>
    <label><input type="checkbox" id="hudCk" checked> 领奏窗</label>
    <label><input type="checkbox" id="mtCk"> <i class="beat-dot" id="beatDot"></i>节拍</label>
    <label><input type="checkbox" id="badgeCk"> 简谱标</label>
    <button id="themeBtn" title="切换纸张背景主题">纸色: 宣纸</button>
    <button id="durBtn">改时值</button>
    <button id="immBtn">沉浸</button>
    <button id="micBtn" class="pri">🎤 开始听音</button>
  </div>
</div>

<div id="hud" class="on">
  <div class="hud-card">
    <div class="hud-jp" id="hudJp">0</div>
    <div class="hud-meta">
      <div><b id="hudPitch">休止符</b> · <span id="hudTech">泛音段</span></div>
      <div id="hudDur">时值 ½ 拍 · 第 1 排第 1 音</div>
    </div>
  </div>
  <canvas id="lensCanvas"></canvas>
</div>

<div id="sc">
  <div id="paper">
    <div class="sheet-head">
      <h1>青城山下白素贞</h1>
      <p>1 = C 正调定弦（一至七弦：1 2 4 5 6 1 2） · 2/4 拍 · 2800px 无损矢量级超清修复版</p>
    </div>
  </div>
</div>

<nav class="botbar">
  <button id="rstBtn">⏮ 重来 (R)</button>
  <button id="prevRowBtn">▲ 上一排</button>
  <button id="prevBtn">◀ 上一音 (←)</button>
  <button id="playBtn" class="pri">▶ 模拟弹奏 (Space)</button>
  <button id="nextBtn">下一音 (→) ▶</button>
  <button id="nextRowBtn">▼ 下一排</button>
</nav>

<div id="immBar">
  <button id="immPlayBtn" class="pri">▶ 弹奏</button>
  <button id="immMicBtn">🎤 听音</button>
  <button id="immExitBtn">退出沉浸</button>
</div>

<dialog id="durDlg">
  <b>每排速度 (BPM) 与各音时值（四分音符 = 1）</b>
  <div class="hint">每行对应谱上一排，格式“速度: 时值1 时值2 …”。0.5 为八分音符，0.25 为十六分音符，休止符也占一个位置。</div>
  <textarea id="durTxt" spellcheck="false"></textarea>
  <div class="hint" id="durMsg" style="color:#f4a24c"></div>
  <div style="display:flex;gap:8px;margin-top:10px;justify-content:flex-end">
    <button id="durApply" class="pri">应用修改</button>
    <button id="durClose">取消</button>
  </div>
</dialog>

<script>
const IMGS = @@IMGS@@;
const ROWS = @@ROWS@@;
const CELLS = @@CELLS@@;

const $ = s => document.querySelector(s);
const NM = ["C", "C♯", "D", "D♯", "E", "F", "F♯", "G", "G♯", "A", "A♯", "B"];
let BPM = ROWS.map(r => r.bpm);
const ROWN = ROWS.map(r => r.count);
const DUR = CELLS.map(c => c.d);

const fmtDur = x => ({0.25:"¼", 0.5:"½", 0.75:"¾", 1:"1", 1.5:"1½", 2:"2"})[x] || String(x);

/* ---------- 1. 构建 2400px 无损超清谱面与音位框 ---------- */
const paper = $("#paper");
const rowEls = [], rowLabelEls = [], rowImgs = [], mkEls = [];

IMGS.forEach((b64, ri) => {
  const rl = document.createElement("div");
  rl.className = "rl";
  paper.appendChild(rl);
  rowLabelEls.push(rl);

  const rw = document.createElement("div");
  rw.className = "rw";
  const im = new Image();
  im.decoding = "async";
  im.src = "data:image/png;base64," + b64;
  im.onload = () => { if (CELLS[idx] && CELLS[idx].r === ri) drawLens(); };
  rw.appendChild(im);
  paper.appendChild(rw);
  rowEls.push(rw);
  rowImgs.push(im);
});

CELLS.forEach((c, i) => {
  const el = document.createElement("div");
  el.className = "mk";
  el.style.left = c.x + "%";
  el.style.width = c.w + "%";
  el.dataset.i = i;

  const badge = document.createElement("span");
  badge.className = "mk-badge";
  el.appendChild(badge);

  rowEls[c.r].appendChild(el);
  mkEls.push(el);
});

function refreshLabels() {
  mkEls.forEach((el, i) => {
    const c = CELLS[i];
    const pStr = c.rest ? "0" : c.p.join("/");
    const hStr = c.harm && !c.rest ? "°" : "";
    el.firstChild.textContent = `${hStr}${pStr} (${fmtDur(DUR[i])})`;
  });
  rowLabelEls.forEach((rl, r) => {
    rl.textContent = `第 ${r + 1} 排 · ♩=${BPM[r]} · ${ROWN[r]} 音`;
  });
}
refreshLabels();

/* ---------- 2. 音高八度规划（兼顾旋律走向与泛音/撮和弦音程） ---------- */
const MIDI = [];
{
  let pv = 52;
  CELLS.forEach(c => {
    if (c.rest || !c.pcs.length) { MIDI.push([]); return; }
    const targetCenter = c.harm ? 60 : 52;
    const minM = c.harm ? 48 : 40;
    const maxM = c.harm ? 74 : 67;
    let best = null;
    for (let m = minM; m <= maxM; m++) {
      if (((m % 12) + 12) % 12 === c.pcs[0]) {
        const d = Math.abs(m - pv) * 0.85 + Math.max(0, Math.abs(m - targetCenter) - 7) * 0.55;
        if (best === null || d < best.d) best = { m, d };
      }
    }
    const ms = [best.m];
    for (let k = 1; k < c.pcs.length; k++) {
      let dd = (c.pcs[0] - c.pcs[k] + 12) % 12;
      if (dd === 0) dd = 12;
      ms.push(best.m - dd);
    }
    MIDI.push(ms);
    pv = best.m;
  });
}

function midiName(m) {
  return NM[((m % 12) + 12) % 12] + (Math.floor(m / 12) - 1);
}

/* ---------- 3. 状态与领奏放大窗渲染 ---------- */
let idx = 0, hit = 0, miss = 0;
const warnSet = new Set();

function drawLens() {
  const hud = $("#hud");
  if (!hud.classList.contains("on")) return;
  const c = CELLS[Math.min(idx, CELLS.length - 1)];
  if (!c) return;

  // 更新左侧大字领奏卡
  if (c.rest) {
    $("#hudJp").innerHTML = `<small>休止</small>0`;
    $("#hudPitch").textContent = "休止符 (空拍)";
    $("#hudTech").textContent = c.harm ? "泛音段" : "散按段";
  } else {
    const hTag = c.harm ? `<small>○ 泛音</small>` : (c.p.length > 1 ? `<small>撮 双音</small>` : `<small>简谱</small>`);
    $("#hudJp").innerHTML = `${hTag}${c.p.join("<br>")}`;
    const mNames = MIDI[Math.min(idx, CELLS.length - 1)].map(midiName).join(" + ");
    $("#hudPitch").textContent = mNames;
    $("#hudTech").textContent = c.harm ? "泛音 (清亮)" : (c.p.length > 1 ? "撮和弦 (双弦同奏)" : "散/按音");
  }
  $("#hudDur").textContent = `时值 ${fmtDur(DUR[Math.min(idx, CELLS.length - 1)])} 拍 · 第 ${c.r + 1} 排第 ${c.ni + 1} 音`;

  // 绘制右侧 2400px 原图局部放大镜
  const cv = $("#lensCanvas");
  const im = rowImgs[c.r];
  if (!im || !im.complete || !im.naturalWidth) return;
  const dp = window.devicePixelRatio || 1;
  const cw = cv.clientWidth, ch = cv.clientHeight;
  if (!cw || !ch) return;
  cv.width = Math.round(cw * dp);
  cv.height = Math.round(ch * dp);
  const g = cv.getContext("2d");

  const isDark = document.documentElement.dataset.theme === "dark";
  g.fillStyle = isDark ? "#1f1e1b" : "#fcf9f0";
  g.fillRect(0, 0, cv.width, cv.height);

  const srcW = im.naturalWidth, srcH = im.naturalHeight;
  const cx = (c.x + c.w / 2) / 100 * srcW;
  const viewW = Math.min(srcW, Math.max(srcH * (cv.width / cv.height) * 0.92, srcW * 0.24));
  const x0 = Math.max(0, Math.min(srcW - viewW, cx - viewW / 2));
  const scale = cv.width / viewW;
  const dh = srcH * scale;
  const dy = (cv.height - dh) / 2;

  g.save();
  if (isDark) g.filter = "invert(0.91) hue-rotate(180deg) contrast(1.18)";
  else g.filter = `contrast(${getComputedStyle(document.documentElement).getPropertyValue("--ink-contrast") || 1.12})`;
  g.imageSmoothingEnabled = true;
  g.imageSmoothingQuality = "high";
  g.drawImage(im, x0, 0, viewW, srcH, 0, dy, cv.width, dh);
  g.restore();

  // 画当前音与前后音参考框
  CELLS.forEach((cell, k) => {
    if (cell.r !== c.r) return;
    const rx = (cell.x / 100 * srcW - x0) * scale;
    const rw = (cell.w / 100 * srcW) * scale;
    if (rx + rw < 0 || rx > cv.width) return;
    const ry = dy + srcH * 0.03 * scale;
    const rh = srcH * 0.94 * scale;
    if (k === idx) {
      g.fillStyle = "rgba(184, 55, 40, 0.15)";
      g.fillRect(rx, ry, rw, rh);
      g.strokeStyle = "#b83728";
      g.lineWidth = 2.2 * dp;
      g.strokeRect(rx, ry, rw, rh);
    } else {
      g.strokeStyle = isDark ? "rgba(255,255,255,0.12)" : "rgba(0,0,0,0.10)";
      g.lineWidth = 1 * dp;
      g.strokeRect(rx, ry, rw, rh);
    }
  });
}

function updateUI(scroll = true) {
  const safeIdx = Math.min(idx, CELLS.length - 1);
  mkEls.forEach((el, k) => {
    el.className = "mk" + (k < idx ? " done" : k === idx ? " cur" : "") + (warnSet.has(k) ? " warn" : "");
  });
  if (idx < CELLS.length) {
    const c = CELLS[idx];
    $("#posText").textContent = `第 ${idx + 1} / ${CELLS.length} 音 · 第 ${c.r + 1} 排第 ${c.ni + 1} 音`;
  } else {
    $("#posText").textContent = `全曲已完成 (${CELLS.length} 音)`;
  }
  $("#hitCnt").textContent = hit;
  $("#missCnt").textContent = miss;
  drawLens();

  if (scroll && mkEls[safeIdx]) {
    const e = mkEls[safeIdx], sc = $("#sc");
    const r = e.getBoundingClientRect(), s = sc.getBoundingClientRect();
    if (r.top < s.top + 45 || r.bottom > s.bottom - 55) {
      sc.scrollBy({ top: r.top - s.top - s.height * 0.32, behavior: "smooth" });
    }
  }
}

function setIdx(newIdx, scroll = true) {
  idx = Math.max(0, Math.min(CELLS.length, newIdx));
  updateUI(scroll);
}

/* ---------- 4. 古琴物理建模合成器（区分散按浑厚音色 vs 泛音清亮晶莹音色） ---------- */
let actx = null, masterIn = null, ksCache = {};

function ensureAudio() {
  if (!actx) {
    actx = new (window.AudioContext || window.webkitAudioContext)();
    const lp = actx.createBiquadFilter();
    lp.type = "lowpass";
    lp.frequency.value = 3600;
    lp.Q.value = 0.45;

    const body = actx.createBiquadFilter();
    body.type = "peaking";
    body.frequency.value = 185;
    body.gain.value = 4.5;
    body.Q.value = 0.85;

    const dry = actx.createGain();
    dry.gain.value = 0.82;
    lp.connect(body);
    body.connect(dry);
    dry.connect(actx.destination);

    // 琴室混响
    const conv = actx.createConvolver();
    const irLen = (actx.sampleRate * 1.6) | 0;
    const ir = actx.createBuffer(2, irLen, actx.sampleRate);
    for (let ch = 0; ch < 2; ch++) {
      const d = ir.getChannelData(ch);
      for (let i = 0; i < irLen; i++) {
        d[i] = (Math.random() * 2 - 1) * Math.exp(-i / (actx.sampleRate * 0.32));
      }
    }
    conv.buffer = ir;
    const wet = actx.createGain();
    wet.gain.value = 0.18;
    lp.connect(conv);
    conv.connect(wet);
    wet.connect(actx.destination);
    masterIn = lp;
  }
  if (actx.state === "suspended") actx.resume();
  return actx;
}

function buildKSBuffer(midi, isHarm) {
  const key = midi + (isHarm ? "_H" : "_S");
  if (ksCache[key]) return ksCache[key];
  const a = ensureAudio(), fs = a.sampleRate;
  // 泛音高八度清亮共鸣
  const effMidi = isHarm ? Math.min(79, midi + 12) : midi;
  const f = 440 * Math.pow(2, (effMidi - 69) / 12);
  const dur = isHarm ? 4.8 : (effMidi < 48 ? 6.8 : 5.4);
  const L = (fs * dur) | 0;
  const P = fs / f;
  const N = Math.max(2, Math.floor(P - 0.5));
  const dl = P - N - 0.5;
  const C = (1 - dl) / (1 + dl);
  const ring = new Float32Array(N);

  let s = 0;
  const smooth = isHarm ? 0.42 : 0.64;
  for (let i = 0; i < N; i++) {
    s = smooth * s + (1 - smooth) * (Math.random() * 2 - 1);
    ring[i] = s;
  }

  const out = new Float32Array(L);
  const g = isHarm ? 0.9968 : (effMidi < 48 ? 0.9972 : effMidi < 58 ? 0.9962 : 0.9946);
  let p = 0, prev = 0, ax = 0, ay = 0;
  for (let n = 0; n < L; n++) {
    const cur = ring[p];
    const v = g * 0.5 * (cur + prev);
    prev = cur;
    const y = C * v + ax - C * ay;
    ax = v;
    ay = y;
    ring[p] = y;
    out[n] = cur;
    if (++p >= N) p = 0;
  }

  let mx = 0;
  for (let i = 0; i < L; i++) mx = Math.max(mx, Math.abs(out[i]));
  const norm = 0.8 / (mx || 1);
  const atk = Math.floor(fs * (isHarm ? 0.0025 : 0.004));
  const rel = Math.floor(fs * 0.45);
  for (let i = 0; i < L; i++) {
    const envA = i < atk ? i / atk : 1;
    const envR = i > L - rel ? (L - i) / rel : 1;
    out[i] *= norm * envA * envR;
  }

  const buf = a.createBuffer(1, L, fs);
  buf.copyToChannel(out, 0);
  return (ksCache[key] = buf);
}

let activeSrcs = [], activeTimers = [];
let playing = false;

function pluckNote(midi, isHarm, when, gainVal) {
  const a = ensureAudio();
  const src = a.createBufferSource();
  const g = a.createGain();
  src.buffer = buildKSBuffer(midi, isHarm);
  g.gain.value = gainVal;
  src.connect(g);
  g.connect(masterIn);
  src.start(when);
  activeSrcs.push(src);
}

function scheduleClick(when) {
  const a = ensureAudio();
  const osc = a.createOscillator();
  const g = a.createGain();
  osc.frequency.value = 1650;
  g.gain.setValueAtTime(0.001, when);
  g.gain.linearRampToValueAtTime(0.14, when + 0.002);
  g.gain.exponentialRampToValueAtTime(0.001, when + 0.05);
  osc.connect(g);
  g.connect(a.destination);
  osc.start(when);
  osc.stop(when + 0.06);
  activeSrcs.push(osc);

  const delayMs = Math.max(0, (when - a.currentTime) * 1000);
  activeTimers.push(setTimeout(() => {
    const dot = $("#beatDot");
    dot.classList.add("flash");
    setTimeout(() => dot.classList.remove("flash"), 110);
  }, delayMs));
}

function previewCell(i) {
  if (i < 0 || i >= CELLS.length) return;
  const c = CELLS[i];
  if (c.rest) return;
  const a = ensureAudio();
  MIDI[i].forEach((m, k) => pluckNote(m, !!c.harm, a.currentTime + 0.01, k ? 0.72 : 0.95));
}

/* ---------- 5. 模拟弹奏（音频时钟精确排程） ---------- */
function buildTimeline() {
  const spd = +$("#spd").value / 100;
  const T = [], D_MS = [], clicks = [];
  let acc = 0;
  for (let r = 0; r < BPM.length; r++) {
    const beatMs = 60000 / (BPM[r] * spd);
    let u = 0;
    CELLS.forEach((c, i) => {
      if (c.r === r) {
        T[i] = acc + u * beatMs;
        D_MS[i] = DUR[i] * beatMs;
        u += DUR[i];
      }
    });
    for (let k = 0; k < Math.ceil(u - 1e-6); k++) clicks.push(acc + k * beatMs);
    acc += u * beatMs;
  }
  return { T, D_MS, clicks, end: acc };
}

function simStop() {
  playing = false;
  activeSrcs.forEach(s => { try { s.stop(); } catch (e) {} });
  activeSrcs = [];
  activeTimers.forEach(clearTimeout);
  activeTimers = [];
  $("#playBtn").textContent = "▶ 模拟弹奏 (Space)";
  $("#immPlayBtn").textContent = "▶ 弹奏";
}

function simStart() {
  if (micTimer) stopMic();
  if (idx >= CELLS.length) idx = 0;
  const a = ensureAudio();
  playing = true;
  $("#playBtn").textContent = "⏸ 暂停 (Space)";
  $("#immPlayBtn").textContent = "⏸ 暂停";

  const { T, clicks, end } = buildTimeline();
  const s = idx, t0 = a.currentTime + 0.12, base = T[s];

  CELLS.forEach((c, i) => {
    if (i < s) return;
    const when = t0 + (T[i] - base) / 1000;
    MIDI[i].forEach((m, k) => pluckNote(m, !!c.harm, when, k ? 0.72 : 1.0));
    activeTimers.push(setTimeout(() => {
      if (playing) setIdx(i);
    }, 120 + T[i] - base));
  });

  if ($("#mtCk").checked) {
    clicks.forEach(t => {
      if (t >= base - 1e-6) scheduleClick(t0 + (t - base) / 1000);
    });
  }

  activeTimers.push(setTimeout(() => {
    simStop();
    setIdx(CELLS.length);
  }, 120 + end - base + 250));
}

$("#playBtn").onclick = () => (playing ? simStop() : simStart());
$("#immPlayBtn").onclick = () => (playing ? simStop() : simStart());

/* ---------- 6. 听音跟谱引擎（YIN 基频检测 + 智能节奏惯性伴随） ---------- */
function yinPitch(buf, sr) {
  const N = 2048;
  const maxT = Math.min(N - 1, Math.floor(sr / 55));
  const minT = Math.floor(sr / 1250);
  const d = new Float32Array(maxT + 2);
  const cmnd = new Float32Array(maxT + 2);
  for (let t = 1; t <= maxT; t++) {
    let s = 0;
    for (let i = 0; i < N; i++) {
      const diff = buf[i] - buf[i + t];
      s += diff * diff;
    }
    d[t] = s;
  }
  let run = 0;
  for (let t = 1; t <= maxT; t++) {
    run += d[t];
    cmnd[t] = run ? (d[t] * t) / run : 1;
  }
  for (let t = Math.max(2, minT); t < maxT; t++) {
    if (cmnd[t] < 0.14) {
      while (t + 1 < maxT && cmnd[t + 1] < cmnd[t]) t++;
      const a = cmnd[t - 1], m = cmnd[t], e = cmnd[t + 1];
      const den = a - 2 * m + e;
      const sh = den ? (a - e) / (2 * den) : 0;
      return sr / (t + sh);
    }
  }
  return -1;
}

let mac = null, analyser = null, micStream = null, micBuf = null, micTimer = 0;
let env = 0, onsetTime = 0, pitchHist = [], lastAdvPc = -1, lastMissTime = 0;
let noteEnterTime = 0, smartStarted = false, lastSoundTime = 0;
let micStarting = false, restHoldMs = 0, lastHitIdx = -1, lastSpd = 1;

function skipRests() {
  restHoldMs = 0;
  const spd = +$("#spd").value / 100 || 1;
  while (idx < CELLS.length && CELLS[idx].rest) {
    restHoldMs += CELLS[idx].d * (60000 / (BPM[CELLS[idx].r] * spd));
    idx++;
  }
}

async function startMic() {
  if (micStarting) return;          // 防止并发初始化：getUserMedia 等待期间重复点击
  micStarting = true;
  simStop();
  try {
    micStream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false }
    });
    mac = new (window.AudioContext || window.webkitAudioContext)();
    await mac.resume();
    analyser = mac.createAnalyser();
    analyser.fftSize = 4096;
    mac.createMediaStreamSource(micStream).connect(analyser);
    micBuf = new Float32Array(4096);
    skipRests();
    setIdx(idx);
    // 起始音若前面是休止符，等待时要把休止符时长加上
    noteEnterTime = performance.now() + (restHoldMs ? -restHoldMs : 0);
    smartStarted = false;
    lastSoundTime = 0;
    micTimer = setInterval(micTick, 45);
    $("#micBtn").textContent = "⏹ 停止听音";
    $("#micBtn").className = "ok";
    $("#immMicBtn").textContent = "⏹ 停止";
    $("#hearText").textContent = "请弹响第一个音…";
  } catch (e) {
    $("#hearText").textContent = "麦克风不可用，请点谱或用按键推进";
  } finally {
    micStarting = false;
  }
}

function stopMic() {
  clearInterval(micTimer);
  micTimer = 0;
  try {
    if (micStream) micStream.getTracks().forEach(t => t.stop());
    if (mac) mac.close();
  } catch (e) {}
  micStream = null;
  mac = null;
  $("#micBtn").textContent = "🎤 开始听音";
  $("#micBtn").className = "pri";
  $("#immMicBtn").textContent = "🎤 听音";
  $("#hearText").textContent = "麦克风未开启";
  $("#meterBar").style.width = "0%";
}

function advanceTo(newIdx) {
  idx = newIdx;
  skipRests();
  noteEnterTime = performance.now();
  setIdx(idx);
}

function micTick() {
  if (!analyser || idx >= CELLS.length) return;
  analyser.getFloatTimeDomainData(micBuf);
  let sum = 0;
  for (let i = 0; i < micBuf.length; i++) sum += micBuf[i] * micBuf[i];
  const rms = Math.sqrt(sum / micBuf.length);
  const gate = 0.028 / (+$("#sens").value);
  $("#meterBar").style.width = Math.min(100, (rms / gate) * 28) + "%";

  const now = performance.now();
  const isOnset = rms > gate && rms > env * 1.55;
  if (isOnset) onsetTime = now;
  env = env * 0.84 + rms * 0.16;

  const cur = CELLS[idx];
  const spd = +$("#spd").value / 100;
  const isSmart = $("#followMode").value === "smart";
  // 智能伴随的推进 deadline 用"上一个实际弹奏到的音"的时值，而不是当前待确认音的时值
  const anchorIdx = (typeof lastHitIdx === "number" && lastHitIdx >= 0) ? lastHitIdx : idx;
  const anchor = CELLS[anchorIdx] || cur;
  const expectedMs = DUR[anchorIdx] * (60000 / (BPM[anchor.r] * spd));

  // 智能伴随模式下的惯性推进
  if (isSmart && smartStarted && idx < CELLS.length) {
    const elapsed = now - noteEnterTime;
    // 若最近 2.5 秒内有琴声，且当前音已到时值并检测到新拨弦起音（哪怕泛音基频较弱），平滑推进到下一音
    if (elapsed >= expectedMs * 0.92 && (now - onsetTime < 280 || (now - lastSoundTime < 1800 && elapsed >= expectedMs * 1.35))) {
      hit++;
      onsetTime = 0;
      pitchHist = [];
      advanceTo(idx + 1);
      return;
    }
  }

  if (rms < gate) {
    pitchHist = [];
    if (!smartStarted) $("#hearText").textContent = "等待琴声…";
    return;
  }

  lastSoundTime = now;
  const f = yinPitch(micBuf, mac.sampleRate);
  if (f < 0) { pitchHist = []; return; }

  const m = Math.round(69 + 12 * Math.log2(f / 440));
  const pc = ((m % 12) + 12) % 12;
  $("#hearText").textContent = `听到 ${midiName(m)} (${f.toFixed(0)}Hz)`;

  pitchHist.push(pc);
  if (pitchHist.length > 2) pitchHist.shift();
  skipRests();
  if (pitchHist.length < 2 || pitchHist.some(p => p !== pc) || idx >= CELLS.length) return;

  const fresh = now - onsetTime < 680;
  let matchOffset = -1, lookCnt = 0;
  // 纯听音（strict）模式只认当前音，不做前瞻；智能伴随允许最多看 3 个音
  const maxLook = isSmart ? 3 : 1;
  for (let k = 0; idx + k < CELLS.length && lookCnt < maxLook; k++) {
    const c = CELLS[idx + k];
    if (c.rest) continue;
    if (c.pcs.includes(pc)) { matchOffset = k; break; }
    lookCnt++;
  }

  if (matchOffset >= 0) {
    if ((lookCnt > 0 || pc === lastAdvPc) && !fresh) return;
    smartStarted = true;
    hit++;
    lastHitIdx = idx + matchOffset;          // 记录实际弹奏到的音，作为下一次推进的时值基准
    for (let q = 0; q < matchOffset; q++) {
      if (!CELLS[idx + q].rest) warnSet.add(idx + q);
    }
    lastAdvPc = pc;
    onsetTime = 0;
    pitchHist = [];
    advanceTo(idx + matchOffset + 1);
  } else if (fresh && now - lastMissTime > 520) {
    lastMissTime = now;
    miss++;
    warnSet.add(idx);
    updateUI(false);
  }
}

$("#micBtn").onclick = () => (micTimer ? stopMic() : startMic());
$("#immMicBtn").onclick = () => (micTimer ? stopMic() : startMic());

/* ---------- 7. 导航、交互与快捷键 ---------- */
$("#prevBtn").onclick = () => { simStop(); lastAdvPc = -1; setIdx(idx - 1); previewCell(idx); };
$("#nextBtn").onclick = () => { simStop(); lastAdvPc = -1; setIdx(idx + 1); previewCell(idx); };
$("#prevRowBtn").onclick = () => {
  simStop();
  const curRow = CELLS[Math.min(idx, CELLS.length - 1)].r;
  const targetRow = Math.max(0, curRow - 1);
  const firstIdx = CELLS.findIndex(c => c.r === targetRow);
  if (firstIdx >= 0) setIdx(firstIdx);
};
$("#nextRowBtn").onclick = () => {
  simStop();
  const curRow = CELLS[Math.min(idx, CELLS.length - 1)].r;
  const targetRow = Math.min(ROWS.length - 1, curRow + 1);
  const firstIdx = CELLS.findIndex(c => c.r === targetRow);
  if (firstIdx >= 0) setIdx(firstIdx);
};
$("#rstBtn").onclick = () => {
  simStop();
  hit = 0; miss = 0; warnSet.clear(); lastAdvPc = -1; smartStarted = false;
  setIdx(0);
  $("#sc").scrollTo({ top: 0, behavior: "smooth" });
};

paper.addEventListener("click", e => {
  const mk = e.target.closest(".mk");
  if (!mk) return;
  simStop();
  const i = +mk.dataset.i;
  lastAdvPc = -1;
  warnSet.delete(i);
  noteEnterTime = performance.now();
  setIdx(i, false);
  previewCell(i);
});

// 速度变更后重排播放调度：以新的速度重算"已过时间"，避免用旧速度的 deadline 判断
function rescheduleAfterTimingChange() {
  const spd = +$("#spd").value / 100 || 1;
  const anchor = (typeof lastHitIdx === "number" && lastHitIdx >= 0) ? lastHitIdx : idx;
  const c = CELLS[anchor];
  if (!c) return;
  const full = DUR[anchor] * (60000 / (BPM[c.r] * spd));   // 该音在新速度下的完整时长
  const elapsedOld = noteEnterTime ? (performance.now() - noteEnterTime) : 0;
  const oldSpd = (typeof lastSpd === "number" && lastSpd > 0) ? lastSpd : spd;
  const elapsedScaled = elapsedOld * (oldSpd / spd);          // 按新速度折算已过时间
  noteEnterTime = performance.now() - Math.min(elapsedScaled, full);
  lastSpd = spd;
}

$("#spd").oninput = e => {
  $("#spdVal").textContent = e.target.value + "%";
  rescheduleAfterTimingChange();
};
$("#zoom").oninput = e => {
  document.documentElement.style.setProperty("--sheet-w", e.target.value);
  drawLens();
};
$("#ink").oninput = e => {
  const v = +e.target.value;
  const c = (0.90 + v * 0.045).toFixed(2);
  const b = (1.04 - v * 0.008).toFixed(2);
  document.documentElement.style.setProperty("--ink-contrast", c);
  document.documentElement.style.setProperty("--ink-bright", b);
  drawLens();
};
$("#hudCk").onchange = e => {
  $("#hud").classList.toggle("on", e.target.checked);
  drawLens();
};
$("#badgeCk").onchange = e => {
  paper.classList.toggle("show-badges", e.target.checked);
};

const themes = [
  { id: "xuan", label: "纸色: 宣纸" },
  { id: "white", label: "纸色: 纯白" },
  { id: "dark", label: "纸色: 暗色" }
];
let themeIdx = 0;
$("#themeBtn").onclick = () => {
  themeIdx = (themeIdx + 1) % themes.length;
  document.documentElement.dataset.theme = themes[themeIdx].id;
  $("#themeBtn").textContent = themes[themeIdx].label;
  drawLens();
};

$("#immBtn").onclick = () => document.body.classList.add("imm");
$("#immExitBtn").onclick = () => document.body.classList.remove("imm");
window.addEventListener("resize", drawLens);

window.addEventListener("keydown", e => {
  if ($("#durDlg").open) return;
  // 焦点在输入控件时（改时值文本框、滑块等），不触发全局快捷键
  const t = e.target;
  if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.tagName === "SELECT" || t.isContentEditable)) return;
  if (e.code === "Space") { e.preventDefault(); playing ? simStop() : simStart(); }
  else if (e.code === "ArrowRight") { e.preventDefault(); $("#nextBtn").click(); }
  else if (e.code === "ArrowLeft") { e.preventDefault(); $("#prevBtn").click(); }
  else if (e.code === "ArrowUp") { e.preventDefault(); $("#prevRowBtn").click(); }
  else if (e.code === "ArrowDown") { e.preventDefault(); $("#nextRowBtn").click(); }
  else if (e.code === "KeyR") { e.preventDefault(); $("#rstBtn").click(); }
  else if (e.code === "KeyM") { e.preventDefault(); $("#micBtn").click(); }
});

/* ---------- 8. 改时值与每排速度弹窗 ---------- */
$("#durBtn").onclick = () => {
  let k = 0;
  $("#durTxt").value = BPM.map((b, r) => {
    const n = ROWN[r];
    const s = b + ": " + DUR.slice(k, k + n).join(" ");
    k += n;
    return s;
  }).join("\n");
  $("#durMsg").textContent = "";
  $("#durDlg").showModal();
};
$("#durClose").onclick = () => $("#durDlg").close();
$("#durApply").onclick = () => {
  const lines = $("#durTxt").value.split("\n").map(s => s.trim()).filter(Boolean);
  let ok = lines.length === ROWN.length, nb = [], nd = [];
  if (ok) {
    lines.forEach((l, r) => {
      const [b, rest] = l.split(":");
      const arr = (rest || "").split(/\s+/).filter(Boolean).map(Number);
      if (!(+b > 0) || arr.length !== ROWN[r] || arr.some(x => !(x > 0))) ok = false;
      nb.push(+b);
      nd.push(...arr);
    });
  }
  if (ok) {
    BPM = nb;
    nd.forEach((x, i) => DUR[i] = x);
    refreshLabels();
    drawLens();
    rescheduleAfterTimingChange();   // 时值/速度已变，重排播放调度
    $("#durDlg").close();
  } else {
    $("#durMsg").textContent = `格式有误：需共 ${ROWN.length} 行，每行音数依次为 ${ROWN.join("、")}`;
  }
};

setIdx(0, false);
</script>
</body>
</html>
'''

if __name__ == "__main__":
    scratch = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "青城山下白素贞"))
    b64_rows, rows_meta, cells = build_baisuzhen(scratch)
    out_html = (html_template
        .replace("@@IMGS@@", json.dumps(b64_rows))
        .replace("@@ROWS@@", json.dumps(rows_meta))
        .replace("@@CELLS@@", json.dumps(cells, ensure_ascii=False))
    )
    out_path = os.path.join(scratch, '古琴跟谱 · 青城山下白素贞_agron_my.html')
    open(out_path, 'w', encoding='utf-8').write(out_html)
    print('Generated:', out_path, os.path.getsize(out_path) // 1024, 'KB')
