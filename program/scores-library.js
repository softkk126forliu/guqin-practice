import { DAOYI_SCORE } from './daoyi-data.js';
import { CHUNFENG_SCORE } from './chunfeng-data.js';

/**
 * 《仙翁操》标准乐谱数据 (正调，1=F，入门必弹名曲)
 * 正调弦音：C D F G A c d
 */
export const XIANWENG_SCORE = {
  title: "仙  翁  操",
  subtitle: "古曲 · 入门开指必弹开指曲",
  key: "1 = F",
  tuning: "正调 (C D F G A c d)",
  tempo: "♩ = 60",
  pageNumber: "开指",
  measures: [
    {
      barNumber: 1,
      isPhraseStart: true,
      notes: [
        { id: "xw-1-1", pitch: 5, octave: -1, finger: "散七", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false },
        { id: "xw-1-2", pitch: 5, octave: -1, finger: "挑七", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false },
        { id: "xw-1-3", pitch: 5, octave: -1, finger: "散七", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false },
        { id: "xw-1-4", pitch: 6, octave: -1, finger: "勾六", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false }
      ]
    },
    {
      barNumber: 2,
      isPhraseStart: false,
      notes: [
        { id: "xw-2-1", pitch: 1, octave: 0, finger: "挑五", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false },
        { id: "xw-2-2", pitch: 1, octave: 0, finger: "挑五", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false },
        { id: "xw-2-3", pitch: 2, octave: 0, finger: "挑四", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false },
        { id: "xw-2-4", pitch: 1, octave: 0, finger: "挑五", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false }
      ]
    },
    {
      barNumber: 3,
      isPhraseStart: false,
      notes: [
        { id: "xw-3-1", pitch: 3, octave: 0, finger: "名九", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false },
        { id: "xw-3-2", pitch: 2, octave: 0, finger: "名十", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false },
        { id: "xw-3-3", pitch: 1, octave: 0, finger: "注十一", underline: 0, hasDot: false, dashes: 0, isGlide: true,  isHarmonic: false },
        { id: "xw-3-4", pitch: 2, octave: 0, finger: "挑四", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false }
      ]
    },
    {
      barNumber: 4,
      isPhraseStart: false,
      notes: [
        { id: "xw-4-1", pitch: 5, octave: -1, finger: "散七", underline: 0, hasDot: false, dashes: 3, isGlide: false, isHarmonic: false }
      ]
    }
  ]
};

/**
 * 曲目库统一索引
 */
export const SCORES_LIBRARY = {
  "daoyi": DAOYI_SCORE,
  "chunfeng": CHUNFENG_SCORE,
  "xianweng": XIANWENG_SCORE
};

export { DAOYI_SCORE, CHUNFENG_SCORE };
