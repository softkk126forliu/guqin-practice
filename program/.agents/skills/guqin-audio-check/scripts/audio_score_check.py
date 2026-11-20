# -*- coding: utf-8 -*-
"""
古琴跟谱页 ↔ 示范音频 发音一致性检查（只依赖 numpy / scipy / ffmpeg，不需要 librosa）。

方法（详见同目录 ../SKILL.md）：
  1. 谱面：读跟谱页 HTML 的 `const CELLS`（逐音 pcs 音级 0..11、时值 d）与 `const ROWS`（每排 bpm）；
     或读 spec JSON（rows[].notes[].p 简谱数字 + tonic）。
  2. 音频：ffmpeg 解码成单声道 22050Hz。
  3. 调音：所有显著谱峰相对 A440 的偏差做加权圆均值 → tune（cents）。古琴常不在 A440。
  4. 特征：只保留“音调性谱峰”（压掉拨弦噪声/宽带瞬态）后做谐波求和音高显著度（MIDI 36–96），
     折叠成 12 维“显著度色度”。比普通 chroma 少了泛音（五度、三度）的干扰。
  5. 移调：全曲显著度色度 vs 谱面音级直方图，12 种移调求相关 → 录音是否与页面同调。
  6. 对齐：谱面按各排 bpm 展开成帧序列，与音频帧做子序列 DTW（音频起止自由，
     步长 (1,1)(1,2)(2,1)(1,3)(3,1) 允许 1/3–3 倍局部速度变化，适应“自由地”散板）。
     DTW 天然吸收倚音、滑音、打圆等页面上没画的装饰音，也能跟住“上/下/进/退”这类不重新拨弦的走手音。
  7. 每个谱面音：在 DTW 给出的起点 ±0.2s 内吸附到最近起音（找不到则标“无起音”=多为走手音）；
     取起音后 50–350ms 的显著度色度（减去起音前的余音），看期望音级排第几 → OK / 可疑 / 不一致。
  8. 输出 Markdown 报告 + CSV + JSON（含每个音在录音里的时间，可用于反推节奏/时值）。

用法：
  python audio_score_check.py --page "春风/古琴跟谱 · 春风_agron_my.html" \
      --audio "春风/示范.mp3" --out 春风/audio_check/春风_p1 [--start 0 --end 120] [--transpose auto|0..11]
"""
import argparse
import csv
import json
import os
import re
import subprocess
import sys

import numpy as np
from scipy.ndimage import maximum_filter1d, median_filter
from scipy.signal import stft

SR = 22050
HOP = 512                       # 特征帧移 ≈ 23ms
NM = ["C", "D♭", "D", "E♭", "E", "F", "G♭", "G", "A♭", "A", "B♭", "B"]
DEG = {"1": 0, "2": 2, "3": 4, "4": 5, "5": 7, "6": 9, "7": 11}
TONIC = {"C": 0, "#C": 1, "bD": 1, "D": 2, "#D": 3, "bE": 3, "E": 4, "F": 5, "#F": 6,
         "bG": 6, "G": 7, "#G": 8, "bA": 8, "A": 9, "#A": 10, "bB": 10, "B": 11}
MIDI_LO, MIDI_HI = 36, 96


def midi_name(m):
    return f"{NM[m % 12]}{m // 12 - 1}"


def page_midis(score):
    """复刻跟谱页模板（page.template.html）的八度规划与泛音升八度逻辑。
    返回与 score 等长的 [(hud_m, eff_m), ...]；休止符为 ([], [])。

    注意：这里是模板逻辑的手工复刻，模板改了要同步本函数。
    2026-11-20 起模板的 HUD 改为显示实际发声音高（effMidiOf），
    与合成器一致，因此 hud_m == eff_m。
    """
    out, pv = [], 52
    for c in score:
        if c["rest"] or not c["pcs"]:
            out.append(([], []))
            continue
        tc = 60 if c["harm"] else 52
        min_m, max_m = (48, 74) if c["harm"] else (40, 67)
        best = min(
            (m for m in range(min_m, max_m + 1) if m % 12 == c["pcs"][0]),
            key=lambda m: abs(m - pv) * 0.85 + max(0, abs(m - tc) - 7) * 0.55,
        )
        ms = [best]
        for p in c["pcs"][1:]:
            dd = (c["pcs"][0] - p + 12) % 12 or 12
            ms.append(best - dd)
        pv = best
        eff = [min(79, m + 12) if c["harm"] else m for m in ms]
        # 模板 HUD 现在显示实际发声音高，故 hud 与 eff 相同
        out.append((eff, eff))
    return out


# ---------------------------------------------------------------- 谱面
def load_score(page=None, spec=None, tonic=None):
    """返回 [{'row','ni','p','pcs','d','rest','harm','bpm'}...]"""
    if page:
        txt = open(page, encoding="utf-8").read()
        m = re.search(r"const CELLS\s*=\s*(\[.*?\]);", txt, re.S)
        if not m:
            sys.exit("HTML 中找不到 const CELLS = [...]")
        cells = json.loads(m.group(1))
        mr = re.search(r"const ROWS\s*=\s*(\[.*?\]);", txt, re.S)
        bpms = [r.get("bpm", 60) for r in json.loads(mr.group(1))] if mr else []
        return [dict(row=c["r"] + 1, ni=c["ni"] + 1, p=c.get("p", []), pcs=c.get("pcs", []),
                     d=c.get("d", 1), rest=bool(c.get("rest")), harm=bool(c.get("harm")),
                     bpm=bpms[c["r"]] if c["r"] < len(bpms) else 60) for c in cells]
    sp = json.load(open(spec, encoding="utf-8"))
    t = TONIC[tonic or sp.get("tonic", "C")]
    out = []
    for ri, r in enumerate(sp["rows"]):
        for ni, n in enumerate(r["notes"]):
            p = n.get("p", [])
            pcs = [] if n.get("rest") else [
                (t + DEG[x[-1]] + (1 if x.startswith("#") else -1 if x.startswith("b") else 0)) % 12 for x in p]
            out.append(dict(row=ri + 1, ni=ni + 1, p=p, pcs=pcs, d=n.get("d", 1),
                            rest=bool(n.get("rest")), harm=bool(n.get("harm")), bpm=r.get("bpm", 60)))
    return out


# ---------------------------------------------------------------- 音频
def load_audio(path, start=0.0, end=None):
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", str(start)]
    if end:
        cmd += ["-to", str(end)]
    cmd += ["-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def spectrogram(y, n_fft, hop):
    f, t, Z = stft(y, fs=SR, nperseg=n_fft, noverlap=n_fft - hop, boundary=None, padded=False)
    return f, t, np.abs(Z)


def estimate_tuning(f, S):
    """显著谱峰相对 A440 的偏差（cents），抛物线插值 + 幅度加权圆均值。"""
    band = (f > 80) & (f < 1500)
    fb, Sb = f[band], S[band]
    pk = (Sb[1:-1] > Sb[:-2]) & (Sb[1:-1] > Sb[2:])
    thr = np.percentile(Sb, 99)
    k, j = np.where(pk & (Sb[1:-1] > thr))
    k = k + 1
    a, b, c = (np.log(Sb[k + d, j] + 1e-9) for d in (-1, 0, 1))
    off = 0.5 * (a - c) / (a - 2 * b + c + 1e-12)
    freq = fb[k] + off * (fb[1] - fb[0])
    cents = 1200 * np.log2(freq / 440.0)
    mean = np.angle(np.sum(Sb[k, j] * np.exp(2j * np.pi * cents / 100.0)))
    return float(mean / (2 * np.pi) * 100.0)


def salience(y, tune):
    """音调性谱峰 → 谐波求和音高显著度 P (61×T) 与 12 维色度 C (12×T)。"""
    f, t, S = spectrogram(y, 4096, HOP)
    L = np.log1p(300 * S / (np.percentile(S, 99.9) + 1e-9))
    # 只留局部峰且明显高出邻域中值的谱线（压宽带噪声/拨弦瞬态）
    loc_max = L == maximum_filter1d(L, size=5, axis=0)
    loc_med = median_filter(L, size=(31, 1))
    T = np.where(loc_max & (L > loc_med + 0.35), L - loc_med, 0.0)
    mids = np.arange(MIDI_LO, MIDI_HI + 1)
    df = f[1] - f[0]
    P = np.zeros((len(mids), T.shape[1]))
    for mi, m in enumerate(mids):
        f0 = 440 * 2 ** ((m - 69 + tune / 100) / 12)
        for h, w in zip(range(1, 7), (1.0, 0.75, 0.55, 0.4, 0.3, 0.22)):
            fr = f0 * h
            if fr > 5500:
                break
            k = int(round(fr / df))
            r = max(1, int(round(fr * 0.025 / df)))   # ±~40 cents
            P[mi] += w * T[max(0, k - r):k + r + 1].max(0)
    C = np.zeros((12, P.shape[1]))
    for mi, m in enumerate(mids):
        C[m % 12] += P[mi]
    energy = C.sum(0)
    return t, P, C, energy


def onsets(y):
    n_fft, hop = 2048, 256
    f, t, S = spectrogram(y, n_fft, hop)
    L = np.log1p(1000 * S / (S.max() + 1e-9))
    band = (f > 60) & (f < 4000)
    flux = np.concatenate([[0], np.maximum(0, np.diff(L[band], axis=1)).sum(0)])
    flux = flux / (np.percentile(flux, 99.5) + 1e-9)
    thr = median_filter(flux, size=int(1.0 * SR / hop)) + 0.12
    peaks = (flux == maximum_filter1d(flux, size=int(0.07 * SR / hop) | 1)) & (flux > thr)
    times, strength = t[peaks], flux[peaks]
    keep, last = [], -1.0
    for i, tt in enumerate(times):
        if tt - last >= 0.06:
            keep.append(i)
            last = tt
    return times[keep], strength[keep]


# ---------------------------------------------------------------- 匹配
def template(pcs):
    v = np.zeros(12)
    for p in pcs:
        v[p % 12] += 1.0
        v[(p + 7) % 12] += 0.15   # 谐波求和的残余：上五度
        v[(p + 5) % 12] += 0.15   # 以及下五度“鬼影”
    n = np.linalg.norm(v)
    return v / n if n else v


def key_shift(score, chroma_sum):
    hist = np.zeros(12)
    for c in score:
        for p in c["pcs"]:
            hist[p] += c["d"]
    cs = chroma_sum / (np.linalg.norm(chroma_sum) + 1e-9)
    h = hist / (np.linalg.norm(hist) + 1e-9)
    scores = [float(np.dot(np.roll(h, k), cs)) for k in range(12)]
    return int(np.argmax(scores)), scores


def pitch_change_events(ft, C, energy, ot, min_gap=0.10):
    """没有拨弦起音、但主音级发生稳定变化的时刻（上/下/进/退/绰/注等走手音）。"""
    act = energy > 0.08 * np.percentile(energy, 95)
    dom = np.where(act, np.argmax(C, axis=0), -1)
    ev, st = [], []
    run = 4  # 新音级至少稳定 4 帧（≈90ms）
    for k in range(run, len(dom) - run):
        a, b = dom[k - run:k], dom[k:k + run]
        if b[0] < 0 or not np.all(b == b[0]) or np.any(a == b[0]):
            continue
        if len(ot) and np.min(np.abs(ot - ft[k])) < min_gap:
            continue
        if ev and ft[k] - ev[-1] < 0.15:
            continue
        ev.append(ft[k])
        st.append(0.25)
    return np.array(ev), np.array(st)


def event_feature(ft, C, t_on, t_end):
    """起音后 50–350ms 的显著度色度，减去起音前 150ms 的余音（正部分），再混入少量绝对量。"""
    win_end = min(t_on + 0.35, max(t_end, t_on + 0.12))
    post = (ft >= t_on + 0.04) & (ft <= win_end)
    if not post.any():
        post = np.arange(len(ft)) == np.argmin(np.abs(ft - t_on - 0.1))
    pre = (ft >= t_on - 0.15) & (ft < t_on - 0.01)
    vpost = C[:, post].mean(1)
    vpre = C[:, pre].mean(1) if pre.any() else np.zeros(12)
    return np.maximum(0, vpost - 0.6 * vpre) + 0.3 * vpost, post


def align(score_vecs, pos, ev_vecs, et, estr, speed=1.0,
          ins_w=0.12, del_cost=1.2, lam=0.35, max_skip=2, max_gap=8.0):
    """带节奏约束的事件级动态规划。
    谱面音 i（按序，可跳过 ≤max_skip 个，每个 del_cost）↔ 音频事件 j（单调递增，起止自由）。
    步代价 = (1-cos) + ins_w*被跳过事件强度和 + lam*|log(实际间隔/期望间隔)|（裁剪到 log3）。
    pos[i] 为谱面标称起始秒（各排 bpm），speed 为录音/标称 的整体时间倍率。"""
    N, M = len(score_vecs), len(ev_vecs)
    sim = score_vecs @ ev_vecs.T
    cum = np.concatenate([[0], np.cumsum(estr)])
    INF = 1e18
    D = np.full((N, M), INF)
    Pi = np.full((N, M), -1, dtype=np.int32)
    Pj = np.full((N, M), -1, dtype=np.int32)
    for i in range(min(N, max_skip + 1)):
        D[i] = (1 - sim[i]) + i * del_cost
    for i in range(1, N):
        for j in range(1, M):
            lo = int(np.searchsorted(et, et[j] - max_gap))
            if lo >= j:
                continue
            jp = np.arange(lo, j)
            dt = np.maximum(et[j] - et[jp], 1e-3)
            skip = ins_w * (cum[j] - cum[jp + 1])
            best, bi, bj = INF, -1, -1
            for k in range(1, max_skip + 2):
                ip = i - k
                if ip < 0:
                    break
                exp = max((pos[i] - pos[ip]) * speed, 1e-3)
                c = D[ip, lo:j] + lam * np.minimum(np.abs(np.log(dt / exp)), np.log(3.0)) + skip + (k - 1) * del_cost
                q = int(np.argmin(c))
                if c[q] < best:
                    best, bi, bj = c[q], ip, lo + q
            val = best + (1 - sim[i, j])
            if bi >= 0 and val < D[i, j]:
                D[i, j], Pi[i, j], Pj[i, j] = val, bi, bj
    best = (INF, -1, -1)
    for k in range(max_skip + 1):
        i = N - 1 - k
        j = int(np.argmin(D[i]))
        if D[i, j] + k * del_cost < best[0]:
            best = (D[i, j] + k * del_cost, i, j)
    _, i, j = best
    path = {}
    while i >= 0 and j >= 0:
        path[i] = j
        i, j = Pi[i, j], Pj[i, j]
    return path, sim



def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", help="跟谱页 HTML（读取 const CELLS / ROWS）")
    ap.add_argument("--spec", help="或 spec JSON")
    ap.add_argument("--tonic", help="spec 模式下覆盖 1=? 调，如 bB")
    ap.add_argument("--audio", required=True)
    ap.add_argument("--start", type=float, default=0.0, help="音频分析起点（秒）")
    ap.add_argument("--end", type=float, default=None, help="音频分析终点（秒）；整首录音只对应部分页面时建议给")
    ap.add_argument("--transpose", default="auto", help="录音相对页面的半音移调；auto=自动估计")
    ap.add_argument("--tune", type=float, default=None, help="手动指定调音偏差 cents（默认自动）")
    ap.add_argument("--out", required=True, help="输出前缀（不含扩展名）")
    a = ap.parse_args()

    score = load_score(a.page, a.spec, a.tonic)
    y = load_audio(a.audio, a.start, a.end)
    print(f"谱面 {len(score)} 格，音频 {len(y) / SR:.1f}s")

    if a.tune is None:
        f8, _, S8 = spectrogram(y, 8192, 512)
        tune = estimate_tuning(f8, S8)
    else:
        tune = a.tune
    print(f"调音偏差 {tune:+.1f} cents（A4≈{440 * 2 ** (tune / 1200):.1f}Hz）")

    ft, P, C, energy = salience(y, tune)
    ot, ostr = onsets(y)
    print(f"特征帧 {C.shape[1]}，起音 {len(ot)} 个")

    k_best, kscores = key_shift(score, C.sum(1))
    shift = k_best if a.transpose == "auto" else int(a.transpose)
    print(f"移调估计：录音比页面高 {k_best} 半音（相关 {kscores[k_best]:.3f}；同调相关 {kscores[0]:.3f}）；采用 {shift}")

    # ---- 音频事件 = 拨弦起音 ∪ 走手音级变化点
    pe, pst = pitch_change_events(ft, C, energy, ot)
    et = np.concatenate([ot, pe])
    estr = np.concatenate([ostr, pst])
    is_on = np.concatenate([np.ones(len(ot), bool), np.zeros(len(pe), bool)])
    o = np.argsort(et)
    et, estr, is_on = et[o], estr[o], is_on[o]
    print(f"走手音级变化点 {len(pe)} 个，事件合计 {len(et)}")
    feats = []
    for q in range(len(et)):
        t_end = et[q + 1] if q + 1 < len(et) else et[q] + 0.35
        v, _ = event_feature(ft, C, et[q], max(t_end, et[q] + 0.15))
        feats.append(v / (np.linalg.norm(v) + 1e-9))
    EV = np.array(feats)

    # ---- 谱面标称时间轴（含休止符）
    tpos, acc = [], 0.0
    for c in score:
        tpos.append(acc)
        acc += c["d"] * 60.0 / c["bpm"]
    playable = [i for i, c in enumerate(score) if not c["rest"] and c["pcs"]]
    pos = np.array([tpos[i] for i in playable])
    SV = np.array([template([(p + shift) % 12 for p in score[i]["pcs"]]) for i in playable])

    speed = 1.0
    for _ in range(2):   # 第二遍用第一遍估出的整体速度
        path, sim = align(SV, pos, EV, et, estr, speed=speed)
        ks = sorted(path)
        ratios = [(et[path[b]] - et[path[a_]]) / (pos[b] - pos[a_]) for a_, b in zip(ks, ks[1:]) if pos[b] > pos[a_]]
        if ratios:
            speed = float(np.median(ratios))
    print(f"录音/页面 时间倍率 ≈ {speed:.2f}（>1 表示录音比页面 bpm 慢）")

    midis = page_midis(score)
    rows = []
    for k, ci in enumerate(playable):
        c = score[ci]
        exp = [(p + shift) % 12 for p in c["pcs"]]
        hud_m, eff_m = midis[ci]
        base = dict(idx=ci + 1, row=c["row"], ni=c["ni"], jianpu="+".join(c["p"]), harm=c["harm"], d=c["d"],
                    expect="+".join(NM[p] for p in exp),
                    page_sound="+".join(midi_name(m) for m in eff_m),
                    page_hud="+".join(midi_name(m) for m in hud_m))
        j = path.get(k)
        if j is None:
            rows.append(dict(base, time="", onset="", heard="", pitch="", aud_pitch="",
                             sim="", rank="", verdict="缺失", extra=""))
            continue
        nxt = [path[q] for q in range(k + 1, len(playable)) if q in path]
        t_on = float(et[j])
        t_next = float(et[nxt[0]]) if nxt else t_on + 1.0
        v, post = event_feature(ft, C, t_on, t_next)
        order = list(np.argsort(-v))
        rank = max(order.index(p) for p in exp) + 1
        s = float(np.dot(template(exp), v / (np.linalg.norm(v) + 1e-9)))
        if rank <= len(exp) or (rank == len(exp) + 1 and s >= 0.75):
            verdict = "OK"
        elif rank <= len(exp) + 2:
            verdict = "可疑"
        else:
            verdict = "不一致"
        Pm = P[:, post].mean(1)
        top_m = MIDI_LO + int(np.argmax(Pm))
        aud_cands = [m for m in range(48 if c["harm"] else 36, 80) if m % 12 == exp[0]]
        aud_m = max(aud_cands, key=lambda m: Pm[m - MIDI_LO])
        extra = [f"{et[q] + a.start:.2f}:{NM[int(np.argmax(EV[q]))]}"
                 for q in range(j + 1, nxt[0] if nxt else j + 1) if is_on[q] and estr[q] >= 0.45]
        rows.append(dict(base, time=round(t_on + a.start, 2), onset="拨" if is_on[j] else "走",
                         heard="/".join(NM[p] for p in order[:3]), pitch=midi_name(top_m),
                         aud_pitch=midi_name(aud_m), sim=round(s, 3), rank=rank, verdict=verdict,
                         extra=" ".join(extra)))
    rows_t = [r for r in rows if r["time"] != ""]


    n_ok = sum(r["verdict"] == "OK" for r in rows)
    n_sus = sum(r["verdict"] == "可疑" for r in rows)
    n_bad = sum(r["verdict"] in ("不一致", "缺失") for r in rows)
    # 每排小结与录音实际速度
    row_sum = []
    for rn in sorted({r["row"] for r in rows_t}):
        rr = [r for r in rows_t if r["row"] == rn]
        beats = sum(c["d"] for c in score if c["row"] == rn)
        nxt = [r["time"] for r in rows_t if r["row"] == rn + 1]
        span = (nxt[0] if nxt else rr[-1]["time"] + rr[-1]["d"] * 60 / score[rr[-1]["idx"] - 1]["bpm"] * speed) - rr[0]["time"]
        row_sum.append(dict(row=rn, start=rr[0]["time"], seconds=round(span, 2),
                            bpm_page=score[rr[0]["idx"] - 1]["bpm"],
                            bpm_audio=round(beats * 60 / span, 1) if span > 0 else None,
                            ok=sum(r["verdict"] == "OK" for r in rows if r["row"] == rn),
                            n=sum(1 for r in rows if r["row"] == rn)))
    summary = dict(page=a.page or a.spec, audio=os.path.basename(a.audio), window=[a.start, a.end],
                   tuning_cents=round(tune, 1), transpose=shift, key_scores=[round(x, 3) for x in kscores],
                   speed=round(speed, 3), span=[rows_t[0]["time"], rows_t[-1]["time"]], notes=len(rows),
                   ok=n_ok, suspicious=n_sus, mismatch=n_bad, rows=row_sum)

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out + ".csv", "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    json.dump(dict(summary=summary, notes=rows), open(a.out + ".json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    L = [f"# 发音一致性检查：{os.path.basename(summary['page'])}", "",
         f"- 音频：{summary['audio']}（分析区间 {a.start}s – {a.end or '结尾'}）",
         f"- 调音偏差：{summary['tuning_cents']:+} cents（A4≈{440 * 2 ** (tune / 1200):.1f}Hz）；"
         f"移调：{shift} 半音（0 = 与页面同调；12 种移调相关最高 {kscores[k_best]:.3f}，同调 {kscores[0]:.3f}）",
         f"- 页面在录音中的区间：{summary['span'][0]}s – {summary['span'][1]}s；录音/页面时间倍率 ≈ {speed:.2f}",
         f"- 结果：OK {n_ok} / 可疑 {n_sus} / 不一致或缺失 {n_bad}（共 {len(rows)} 个可发音格）", "",
         "## 每排小结", "", "| 排 | 录音起点s | 时长s | 页面bpm | 录音约bpm | OK/总 |", "|---|---|---|---|---|---|"]
    for r in row_sum:
        L.append(f"| {r['row']} | {r['start']} | {r['seconds']} | {r['bpm_page']} | {r['bpm_audio']} | {r['ok']}/{r['n']} |")
    L += ["", "## 逐音", "",
          "| # | 排-音 | 简谱 | 泛 | 期望 | 页面发声 | 时间s | 拨/走 | 听到(前3) | 最强音高 | 录音同音级八度 | 相似 | 名次 | 判定 | 之后多出的拨弦 |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        vd = r["verdict"] if r["verdict"] == "OK" else f"**{r['verdict']}**"
        L.append(f"| {r['idx']} | {r['row']}-{r['ni']} | {r['jianpu']} | {'○' if r['harm'] else ''} | {r['expect']} | "
                 f"{r['page_sound']} | {r['time']} | {r['onset']} | {r['heard']} | {r['pitch']} | {r['aud_pitch']} | "
                 f"{r['sim']} | {r['rank']} | {vd} | {r['extra']} |")
    open(a.out + ".md", "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "rows"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
