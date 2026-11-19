# -*- coding: utf-8 -*-
"""
逐帧音高显著度打印（人工复核“可疑/不一致”用）。

用法：
  python pitch_track.py --audio 春风/示范.mp3 --from 36.4 --to 39.2 [--tune -32] [--step 2]
每行：时间  能量  前三个候选音高:显著度（已按调音偏差校正，带八度）。
看法：
  - 一个音持续多帧占第一 = 真实发音；起音帧出现 D3/E♭3/E3 等相邻半音一起冒头 = 拨弦/走手的宽带噪声，忽略。
  - 低音撮（如 C3+F2、D3+G2）的低音基频常很弱，要看它的 3/5 次泛音（上五度、两个八度+大三度）是否出现。
  - 走手音（上/下/进/退/绰/注）没有新起音，只看音高在持续帧里如何移动。
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio_score_check as A  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", required=True)
    ap.add_argument("--from", dest="t0", type=float, required=True)
    ap.add_argument("--to", dest="t1", type=float, required=True)
    ap.add_argument("--tune", type=float, default=None, help="调音偏差 cents；默认按该片段自动估计")
    ap.add_argument("--step", type=int, default=2, help="每隔几帧打印一次（帧移 ≈23ms）")
    a = ap.parse_args()
    y = A.load_audio(a.audio, a.t0, a.t1)
    if a.tune is None:
        f8, _, S8 = A.spectrogram(y, 8192, 512)
        tune = A.estimate_tuning(f8, S8)
    else:
        tune = a.tune
    ft, P, C, energy = A.salience(y, tune)
    print(f"# tune {tune:+.1f} cents")
    for k in range(0, P.shape[1], a.step):
        o = np.argsort(-P[:, k])[:3]
        cand = " ".join(f"{A.midi_name(A.MIDI_LO + i)}:{P[i, k]:.1f}" for i in o)
        print(f"{a.t0 + ft[k]:7.2f}  e={energy[k]:7.1f}  {cand}")


if __name__ == "__main__":
    main()
