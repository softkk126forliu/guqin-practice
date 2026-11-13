/**
 * 《春风》许国华、龚一 曲 标准琴谱数据 (第 179 页完整 26 小节)
 * 严格按照原谱真实版面切分行，并注入小节级动态速度 (tempo) 与拍号 (meter)：
 * - 第 1 行：第 1~4 小节 (4/4 拍，自由抒情 ♩=66，泛音起势，带装饰花音群与和弦叠音)
 * - 第 2 行：第 5~7 小节 (4/4 拍，泛音平稳行进)
 * - 第 3 行：第 8~10 小节 (4/4 拍 -> 3/4 拍，高音泛音)
 * - 第 4 行：第 11~14 小节 (4/4 拍，泛音双弹 -> 稍渐快散起按音 ♩=84)
 * - 第 5 行：第 15~19 小节 (2/4 拍，入拍 ♩=126 快板滚拂，纯正按音，无泛音圈)
 * - 第 6 行：第 20~23 小节 (2/4 拍，走手音与如歌行进)
 * - 第 7 行：第 24~26 小节 (2/4 拍，大滑音与第 179 页收句)
 */
export const CHUNFENG_SCORE = {
  title: "春    风",
  subtitle: "许国华、龚一 曲 · 紧五弦定弦 (1=♭B)",
  key: "1 = ♭B",
  tuning: "紧五弦定弦: 2: 3: 5: 6. 1 2 3",
  tempo: "♩ = 66",
  pageNumber: "179",
  measures: [
    // ====================================================
    // 第 1 行：自由地 抒情地 (4/4 拍) 泛音起势
    // ====================================================
    {
      barNumber: 1,
      isPhraseStart: true,
      sectionTitle: "自由地 抒情地",
      tempo: "♩ = 66",
      meter: "4/4",
      notes: [
        { id: "cf-1-1", pitch: 6, octave: 1, isHarmonic: true, underline: 0, hasDot: false, dashes: 1, isGlide: false, grace: "623", finger: "色鹫 (1)" },
        { id: "cf-1-2", pitch: 3, octave: 1, isHarmonic: true, underline: 0, hasDot: false, dashes: 1, isGlide: false, grace: "361", finger: "鹫 (2)" }
      ]
    },
    {
      barNumber: 2,
      isPhraseStart: false,
      tempo: "♩ = 66",
      meter: "4/4",
      notes: [
        { id: "cf-2-1", pitch: 6, octave: 1, isHarmonic: true, chordPitch: 3, chordOctave: 0, chordHarmonic: true, underline: 0, hasDot: false, dashes: 0, isGlide: false, finger: "夕九/旱" },
        { id: "cf-2-2", pitch: 7, octave: 1, isHarmonic: true, chordPitch: 3, chordOctave: 0, chordHarmonic: true, underline: 0, hasDot: false, dashes: 2, isGlide: false, finger: "旱四" }
      ]
    },
    {
      barNumber: 3,
      isPhraseStart: false,
      tempo: "♩ = 66",
      meter: "4/4",
      notes: [
        { id: "cf-3-1", pitch: 1, octave: 1, isHarmonic: true, underline: 1, hasDot: false, dashes: 0, isGlide: false, grace: "32", finger: "广五/六" },
        { id: "cf-3-2", pitch: 7, octave: 1, isHarmonic: true, underline: 1, hasDot: true,  dashes: 0, isGlide: false, finger: "大九/七" },
        { id: "cf-3-3", pitch: 6, octave: 1, isHarmonic: true, underline: 2, hasDot: false, dashes: 0, isGlide: false, finger: "萄/六" },
        { id: "cf-3-4", pitch: 6, octave: 1, isHarmonic: true, underline: 0, hasDot: true,  dashes: 0, isGlide: false, finger: "大九/六" }
      ]
    },
    {
      barNumber: 4,
      isPhraseStart: false,
      tempo: "♩ = 66",
      meter: "4/4",
      notes: [
        { id: "cf-4-1", pitch: 3, octave: 1, isHarmonic: true, underline: 0, hasDot: false, dashes: 0, isGlide: false, grace: "361", finger: "鹫" },
        { id: "cf-4-2", pitch: 2, octave: 1, isHarmonic: true, underline: 0, hasDot: false, dashes: 0, isGlide: false, finger: "剔六" },
        { id: "cf-4-3", pitch: 1, octave: 1, isHarmonic: true, underline: 0, hasDot: false, dashes: 0, isGlide: false, finger: "勾" },
        { id: "cf-4-4", pitch: 7, octave: 1, isHarmonic: true, underline: 0, hasDot: false, dashes: 0, isGlide: false, finger: "大九/七" }
      ]
    },

    // ====================================================
    // 第 2 行：泛音平稳行进 (4/4 拍)
    // ====================================================
    {
      barNumber: 5,
      isPhraseStart: true,
      tempo: "♩ = 66",
      meter: "4/4",
      notes: [
        { id: "cf-5-1", pitch: 6, octave: 1, isHarmonic: true, underline: 0, hasDot: false, dashes: 0, isGlide: false, finger: "六" },
        { id: "cf-5-2", pitch: 3, octave: 1, isHarmonic: true, underline: 0, hasDot: false, dashes: 0, isGlide: false, finger: "勾" },
        { id: "cf-5-3", pitch: 6, octave: 1, isHarmonic: true, underline: 0, hasDot: false, dashes: 0, isGlide: false, finger: "六" },
        { id: "cf-5-4", pitch: 7, octave: 1, isHarmonic: true, underline: 0, hasDot: false, dashes: 0, isGlide: false, finger: "大九/七" }
      ]
    },
    {
      barNumber: 6,
      isPhraseStart: false,
      tempo: "♩ = 66",
      meter: "4/4",
      notes: [
        { id: "cf-6-1", pitch: 3, octave: 1, isHarmonic: true, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "广/六" },
        { id: "cf-6-2", pitch: 2, octave: 1, isHarmonic: true, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "剔六" },
        { id: "cf-6-3", pitch: 1, octave: 1, isHarmonic: true, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "勾" },
        { id: "cf-6-4", pitch: 7, octave: 1, isHarmonic: true, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "大九/七" },
        { id: "cf-6-5", pitch: 6, octave: 1, isHarmonic: true, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "大九/六" },
        { id: "cf-6-6", pitch: 3, octave: 1, isHarmonic: true, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "勾" },
        { id: "cf-6-7", pitch: 6, octave: 1, isHarmonic: true, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "六" },
        { id: "cf-6-8", pitch: 7, octave: 1, isHarmonic: true, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "大九/七" }
      ]
    },
    {
      barNumber: 7,
      isPhraseStart: false,
      tempo: "♩ = 66",
      meter: "4/4",
      notes: [
        { id: "cf-7-1", pitch: 1, octave: 1, isHarmonic: true, underline: 0, hasDot: false, dashes: 0, isGlide: false, grace: "32", finger: "广五/六" },
        { id: "cf-7-2", pitch: 7, octave: 1, isHarmonic: true, underline: 2, hasDot: false, dashes: 0, isGlide: false, grace: "71", finger: "大九/七" },
        { id: "cf-7-3", pitch: 6, octave: 1, isHarmonic: true, underline: 2, hasDot: false, dashes: 0, isGlide: false, finger: "萄/六" },
        { id: "cf-7-4", pitch: 7, octave: 1, isHarmonic: true, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "大九/七" },
        { id: "cf-7-5", pitch: 6, octave: 1, isHarmonic: true, underline: 0, hasDot: false, dashes: 1, isGlide: false, finger: "大九/六" }
      ]
    },

    // ====================================================
    // 第 3 行：泛音转拍 (4/4 -> 3/4)
    // ====================================================
    {
      barNumber: 8,
      isPhraseStart: true,
      tempo: "♩ = 66",
      meter: "4/4",
      notes: [
        { id: "cf-8-1", pitch: 5, octave: 1, isHarmonic: true, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "萄/六" },
        { id: "cf-8-2", pitch: 6, octave: 1, isHarmonic: true, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "大九/七" },
        { id: "cf-8-3", pitch: 6, octave: 1, isHarmonic: true, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "勾" },
        { id: "cf-8-4", pitch: 5, octave: 1, isHarmonic: true, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "广五/四" },
        { id: "cf-8-5", pitch: 3, octave: 1, isHarmonic: true, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "大九/七" },
        { id: "cf-8-6", pitch: 3, octave: 1, isHarmonic: true, underline: 0, hasDot: true,  dashes: 0, isGlide: false, finger: "大九/七" }
      ]
    },
    {
      barNumber: 9,
      isPhraseStart: false,
      tempo: "♩ = 66",
      meter: "4/4",
      notes: [
        { id: "cf-9-1", pitch: 6, octave: 1, isHarmonic: true, underline: 0, hasDot: false, dashes: 1, isGlide: false, grace: "623", finger: "鹫" },
        { id: "cf-9-2", pitch: 3, octave: 1, isHarmonic: true, underline: 0, hasDot: false, dashes: 1, isGlide: false, grace: "361", finger: "鹫" }
      ]
    },
    {
      barNumber: 10,
      isPhraseStart: false,
      tempo: "♩ = 66",
      meter: "3/4",
      sectionTitle: "3/4 拍",
      notes: [
        { id: "cf-10-1", pitch: 1, octave: 2, isHarmonic: true, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "勾六" },
        { id: "cf-10-2", pitch: 2, octave: 2, isHarmonic: true, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "四三" },
        { id: "cf-10-3", pitch: 6, octave: 1, isHarmonic: true, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "勾" },
        { id: "cf-10-4", pitch: 5, octave: 1, isHarmonic: true, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "四" },
        { id: "cf-10-5", pitch: 2, octave: 1, isHarmonic: true, underline: 0, hasDot: false, dashes: 0, isGlide: false, finger: "勾" }
      ]
    },

    // ====================================================
    // 第 4 行：泛音双弹 -> 稍渐快散起按音 (4/4 拍)
    // ====================================================
    {
      barNumber: 11,
      isPhraseStart: true,
      tempo: "♩ = 66",
      meter: "4/4",
      notes: [
        { id: "cf-11-1", pitch: 3, octave: 1, isHarmonic: true, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "勾" },
        { id: "cf-11-2", pitch: 3, octave: 1, isHarmonic: true, underline: 1, hasDot: false, dashes: 0, isGlide: false, grace: "61", finger: "木七/七" },
        { id: "cf-11-3", pitch: 3, octave: 1, chordPitch: 6, chordOctave: 1, isHarmonic: true, chordHarmonic: true, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "旱四" },
        { id: "cf-11-4", pitch: 3, octave: 1, isHarmonic: true, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "勾" },
        { id: "cf-11-5", pitch: 3, octave: 1, chordPitch: 6, chordOctave: 1, isHarmonic: true, chordHarmonic: true, underline: 0, hasDot: false, dashes: 1, isGlide: false, finger: "旱四" }
      ]
    },
    {
      barNumber: 12,
      isPhraseStart: false,
      tempo: "♩ = 66",
      meter: "4/4",
      notes: [
        { id: "cf-12-1", pitch: 3, octave: 1, isHarmonic: true, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "勾" },
        { id: "cf-12-2", pitch: 3, octave: 1, isHarmonic: true, underline: 1, hasDot: false, dashes: 0, isGlide: false, grace: "61", finger: "木七/七" },
        { id: "cf-12-3", pitch: 3, octave: 1, chordPitch: 6, chordOctave: 1, isHarmonic: true, chordHarmonic: true, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "旱四" },
        { id: "cf-12-4", pitch: 3, octave: 1, isHarmonic: true, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "勾" },
        { id: "cf-12-5", pitch: 3, octave: 1, chordPitch: 6, chordOctave: 1, isHarmonic: true, chordHarmonic: true, underline: 0, hasDot: false, dashes: 1, isGlide: false, finger: "旱四" }
      ]
    },
    {
      barNumber: 13,
      isPhraseStart: false,
      sectionTitle: "稍渐快 ♩=84",
      tempo: "♩ = 84",
      meter: "4/4",
      notes: [
        { id: "cf-13-1", pitch: 2, octave: -1, isHarmonic: false, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "勾" },
        { id: "cf-13-2", pitch: 5, octave: -1, isHarmonic: false, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "旱" },
        { id: "cf-13-3", pitch: 2, octave: -1, isHarmonic: false, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "勾" },
        { id: "cf-13-4", pitch: 5, octave: -1, isHarmonic: false, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "旱" },
        { id: "cf-13-5", pitch: 2, octave: -1, isHarmonic: false, underline: 0, hasDot: false, dashes: 0, isGlide: false, finger: "勾" },
        { id: "cf-13-6", pitch: 5, octave: -1, isHarmonic: false, underline: 0, hasDot: false, dashes: 0, isGlide: false, finger: "旱" }
      ]
    },
    {
      barNumber: 14,
      isPhraseStart: false,
      tempo: "♩ = 84",
      meter: "4/4",
      notes: [
        { id: "cf-14-1", pitch: 3, octave: -1, isHarmonic: false, underline: 0, hasDot: false, dashes: 0, isGlide: false, finger: "勾" },
        { id: "cf-14-2", pitch: 6, octave: -1, isHarmonic: false, underline: 0, hasDot: false, dashes: 0, isGlide: false, finger: "旱" },
        { id: "cf-14-3", pitch: 3, octave: -1, isHarmonic: false, underline: 0, hasDot: false, dashes: 0, isGlide: false, finger: "勾" },
        { id: "cf-14-4", pitch: 6, octave: -1, isHarmonic: false, underline: 0, hasDot: false, dashes: 1, isGlide: false, finger: "旱" }
      ]
    },

    // ====================================================
    // 第 5 行：入拍 ♩ = 126 (2/4 拍) 滚拂与快板按音
    // ====================================================
    {
      barNumber: 15,
      isPhraseStart: true,
      sectionTitle: "入拍 ♩=126 (2/4拍)",
      tempo: "♩ = 126",
      meter: "2/4",
      notes: [
        { id: "cf-15-1", pitch: 6, octave: 0, isHarmonic: false, underline: 2, hasDot: false, dashes: 0, isGlide: false, finger: "大九/六" },
        { id: "cf-15-2", pitch: 6, octave: 0, isHarmonic: false, underline: 2, hasDot: false, dashes: 0, isGlide: false, finger: "乚" },
        { id: "cf-15-3", pitch: 6, octave: 0, isHarmonic: false, underline: 2, hasDot: false, dashes: 0, isGlide: false, finger: "尸" },
        { id: "cf-15-4", pitch: 6, octave: 0, isHarmonic: false, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "乚" },
        { id: "cf-15-5", pitch: 3, octave: 0, isHarmonic: false, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "勾" }
      ]
    },
    {
      barNumber: 16,
      isPhraseStart: false,
      tempo: "♩ = 126",
      meter: "2/4",
      notes: [
        { id: "cf-16-1", pitch: 6, octave: 0, isHarmonic: false, underline: 2, hasDot: false, dashes: 0, isGlide: false, finger: "大九/六" },
        { id: "cf-16-2", pitch: 6, octave: 0, isHarmonic: false, underline: 2, hasDot: false, dashes: 0, isGlide: false, finger: "乚" },
        { id: "cf-16-3", pitch: 6, octave: 0, isHarmonic: false, underline: 2, hasDot: false, dashes: 0, isGlide: false, finger: "尸" },
        { id: "cf-16-4", pitch: 6, octave: 0, isHarmonic: false, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "乚" },
        { id: "cf-16-5", pitch: 3, octave: 0, isHarmonic: false, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "勾" }
      ]
    },
    {
      barNumber: 17,
      isPhraseStart: false,
      tempo: "♩ = 126",
      meter: "2/4",
      notes: [
        { id: "cf-17-1", pitch: 6, octave: 0, isHarmonic: false, underline: 2, hasDot: false, dashes: 0, isGlide: false, finger: "大九/六" },
        { id: "cf-17-2", pitch: 6, octave: 0, isHarmonic: false, underline: 2, hasDot: false, dashes: 0, isGlide: false, finger: "乚" },
        { id: "cf-17-3", pitch: 6, octave: 0, isHarmonic: false, underline: 2, hasDot: false, dashes: 0, isGlide: false, finger: "尸" },
        { id: "cf-17-4", pitch: 6, octave: 0, isHarmonic: false, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "乚" },
        { id: "cf-17-5", pitch: 7, octave: 0, isHarmonic: false, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "大九/七" }
      ]
    },
    {
      barNumber: 18,
      isPhraseStart: false,
      tempo: "♩ = 126",
      meter: "2/4",
      notes: [
        { id: "cf-18-1", pitch: 1, octave: 1, isHarmonic: false, underline: 0, hasDot: false, dashes: 0, isGlide: false, finger: "全/七" },
        { id: "cf-18-2", pitch: 7, octave: 0, isHarmonic: false, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "大九/七" },
        { id: "cf-18-3", pitch: 6, octave: 0, isHarmonic: false, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "大九/六" }
      ]
    },
    {
      barNumber: 19,
      isPhraseStart: false,
      tempo: "♩ = 126",
      meter: "2/4",
      notes: [
        { id: "cf-19-1", pitch: 7, octave: 0, isHarmonic: false, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "大九下/七" },
        { id: "cf-19-2", pitch: 6, octave: 0, isHarmonic: false, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "外/能六" },
        { id: "cf-19-3", pitch: 7, octave: 0, isHarmonic: false, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "大九下/七" },
        { id: "cf-19-4", pitch: 5, octave: 0, isHarmonic: false, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "外/能六" }
      ]
    },

    // ====================================================
    // 第 6 行：走手音与如歌行进 (2/4 拍)
    // ====================================================
    {
      barNumber: 20,
      isPhraseStart: true,
      tempo: "♩ = 126",
      meter: "2/4",
      notes: [
        { id: "cf-20-1", pitch: 6, octave: 0, isHarmonic: false, underline: 0, hasDot: false, dashes: 1, isGlide: true, finger: "大九/六" }
      ]
    },
    {
      barNumber: 21,
      isPhraseStart: false,
      tempo: "♩ = 126",
      meter: "2/4",
      notes: [
        { id: "cf-21-1", pitch: 6, octave: 0, isHarmonic: false, underline: 0, hasDot: false, dashes: 0, isGlide: false, finger: "六" },
        { id: "cf-21-2", pitch: 6, octave: 0, chordPitch: 3, chordOctave: 0, isHarmonic: false, underline: 0, hasDot: true,  dashes: 0, isGlide: false, finger: "旱四" }
      ]
    },
    {
      barNumber: 22,
      isPhraseStart: false,
      tempo: "♩ = 126",
      meter: "2/4",
      notes: [
        { id: "cf-22-1", pitch: 7, octave: 0, isHarmonic: false, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "大九/七" },
        { id: "cf-22-2", pitch: 1, octave: 1, isHarmonic: false, underline: 0, hasDot: false, dashes: 0, isGlide: false, finger: "全" }
      ]
    },
    {
      barNumber: 23,
      isPhraseStart: false,
      tempo: "♩ = 126",
      meter: "2/4",
      notes: [
        { id: "cf-23-1", pitch: 1, octave: 1, isHarmonic: false, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "木上七/六" },
        { id: "cf-23-2", pitch: 2, octave: 1, isHarmonic: false, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "乚上七" },
        { id: "cf-23-3", pitch: 2, octave: 1, isHarmonic: false, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "乚上七" },
        { id: "cf-23-4", pitch: 3, octave: 1, isHarmonic: false, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "乚" }
      ]
    },

    // ====================================================
    // 第 7 行：大滑音与第 179 页收句 (2/4 拍)
    // ====================================================
    {
      barNumber: 24,
      isPhraseStart: true,
      tempo: "♩ = 126",
      meter: "2/4",
      notes: [
        { id: "cf-24-1", pitch: 3, octave: 1, isHarmonic: false, underline: 0, hasDot: false, dashes: 1, isGlide: true, finger: "乚" }
      ]
    },
    {
      barNumber: 25,
      isPhraseStart: false,
      tempo: "♩ = 126",
      meter: "2/4",
      notes: [
        { id: "cf-25-1", pitch: 3, octave: 1, isHarmonic: false, underline: 0, hasDot: false, dashes: 0, isGlide: false, finger: "勾" },
        { id: "cf-25-2", pitch: 3, octave: 1, isHarmonic: false, underline: 0, hasDot: false, dashes: 0, isGlide: false, finger: "勾" }
      ]
    },
    {
      barNumber: 26,
      isPhraseStart: false,
      tempo: "♩ = 126",
      meter: "2/4",
      notes: [
        { id: "cf-26-1", pitch: 4, octave: 1, isHarmonic: false, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "大九下/七" },
        { id: "cf-26-2", pitch: 3, octave: 1, isHarmonic: false, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "乚下七/六" },
        { id: "cf-26-3", pitch: 3, octave: 1, isHarmonic: false, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "乚下七/六" },
        { id: "cf-26-4", pitch: 2, octave: 1, isHarmonic: false, underline: 1, hasDot: false, dashes: 0, isGlide: false, finger: "乚下七/六" }
      ]
    }
  ]
};
