/**
 * 《捣衣》许健记谱标准琴谱数据 (包含完整第 6 页与第 7 页)
 * 严格按照实体琴谱排印还原：
 * - 减字谱指法 (finger)
 * - 简谱数字 (pitch: 1~7) 与升降号 (accidental: "#" / "b")
 * - 泛音小圆圈 (isHarmonic: true)
 * - 走手音连音线 (isGlide: true)
 * - 减时线下划线 (underline: 0/1/2) 与附点 (hasDot: true)
 * - 延音增时横线 (dashes: 1~3)
 */
export const DAOYI_SCORE = {
  title: "捣    衣",
  subtitle: "古曲 · 钱秀山演奏谱 · 许健记谱",
  key: "1 = ♭B",
  tuning: "紧五慢一定弦: 1: 3: 5: 6. 1. 2. 3.",
  tempo: "♩ = 66",
  pageNumber: "6 - 7",
  measures: [
    // ==========================================
    // 第 6 页 · 第一行：散板引子起音
    // ==========================================
    {
      barNumber: 1,
      isPhraseStart: true,
      notes: [
        { id: "m1-1", pitch: 3, octave: 0, finger: "名九/七", crop: "crops/daoyi/daoyi_m1_1.png", underline: 1, hasDot: true, dashes: 0, isGlide: false, isHarmonic: false },
        { id: "m1-2", pitch: 2, octave: 0, finger: "注十/六", crop: "crops/daoyi/daoyi_m1_2.png", underline: 2, hasDot: false, dashes: 0, isGlide: true,  isHarmonic: false },
        { id: "m1-3", pitch: 1, octave: 0, finger: "勾五",    crop: "crops/daoyi/daoyi_m1_3.png", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false },
        { id: "m1-4", pitch: 2, octave: 0, finger: "挑六",    crop: "crops/daoyi/daoyi_m1_4.png", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false }
      ]
    },
    {
      barNumber: 2,
      isPhraseStart: false,
      notes: [
        { id: "m2-1", pitch: 3, octave: 0, finger: "勾五", crop: "crops/daoyi/daoyi_m2_1.png", underline: 0, hasDot: false, dashes: 3, isGlide: false, isHarmonic: false }
      ]
    },
    {
      barNumber: 3,
      isPhraseStart: false,
      notes: [
        { id: "m3-1", pitch: 6, octave: -1, finger: "名九勾四", crop: "crops/daoyi/daoyi_m3_1.png", underline: 0, hasDot: false, dashes: 1, isGlide: false, isHarmonic: false }
      ]
    },
    {
      barNumber: 4,
      isPhraseStart: false,
      notes: [
        { id: "m4-1", pitch: 5, octave: -1, finger: "夕九勾五", crop: "crops/daoyi/daoyi_m4_1.png", underline: 0, hasDot: false, dashes: 1, isGlide: false, isHarmonic: false }
      ]
    },
    {
      barNumber: 5,
      isPhraseStart: false,
      notes: [
        { id: "m5-1", pitch: 5, octave: -1, finger: "大七勾五", crop: "crops/daoyi/daoyi_m5_1.png", underline: 0, hasDot: false, dashes: 1, isGlide: false, isHarmonic: false },
        { id: "m5-2", pitch: 2, octave: 0,  finger: "七六挑四", crop: "crops/daoyi/daoyi_m5_2.png", underline: 1, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false },
        { id: "m5-3", pitch: 1, octave: 0,  finger: "勾五", underline: 1, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false },
        { id: "m5-4", pitch: 6, octave: -1, finger: "散七", underline: 0, hasDot: false, dashes: 1, isGlide: false, isHarmonic: false }
      ]
    },

    // ==========================================
    // 第 6 页 · 第二行：按音深沉旋律 [一] ♩ = 72
    // ==========================================
    {
      barNumber: 6,
      isPhraseStart: true,
      sectionTitle: "[一] ♩ = 72",
      notes: [
        { id: "m6-1", pitch: 1, octave: 0, finger: "散五", underline: 0, hasDot: false, dashes: 3, isGlide: false, isHarmonic: false }
      ]
    },
    {
      barNumber: 7,
      isPhraseStart: false,
      notes: [
        { id: "m7-1", pitch: 2, octave: 0, finger: "散四", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false },
        { id: "m7-2", pitch: 3, octave: 0, finger: "散三", underline: 0, hasDot: false, dashes: 2, isGlide: false, isHarmonic: false }
      ]
    },
    {
      barNumber: 8,
      isPhraseStart: false,
      notes: [
        { id: "m8-1", pitch: 3, octave: 0, finger: "勾五", underline: 0, hasDot: false, dashes: 3, isGlide: false, isHarmonic: false }
      ]
    },
    {
      barNumber: 9,
      isPhraseStart: false,
      notes: [
        { id: "m9-1", pitch: 3, octave: 0, finger: "散三", underline: 1, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false },
        { id: "m9-2", pitch: 3, octave: 0, finger: "大七", underline: 1, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false },
        { id: "m9-3", pitch: 3, octave: 0, finger: "名九", underline: 0, hasDot: true,  dashes: 0, isGlide: false, isHarmonic: false },
        { id: "m9-4", pitch: 3, octave: 0, finger: "散三", underline: 1, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false }
      ]
    },
    {
      barNumber: 10,
      isPhraseStart: false,
      notes: [
        { id: "m10-1", pitch: 3, octave: 0, finger: "挑六", underline: 1, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false },
        { id: "m10-2", pitch: 2, octave: 0, finger: "大九", underline: 1, hasDot: false, dashes: 0, isGlide: true,  isHarmonic: false },
        { id: "m10-3", pitch: 1, octave: 0, finger: "大十", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false },
        { id: "m10-4", pitch: 2, octave: 0, finger: "挑六", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false },
        { id: "m10-5", pitch: 3, octave: 0, finger: "名九", underline: 0, hasDot: false, dashes: 1, isGlide: false, isHarmonic: false }
      ]
    },

    // ==========================================
    // 第 6 页 · 第三行：灵动泛音段落 (小圆圈 °)
    // ==========================================
    {
      barNumber: 11,
      isPhraseStart: true,
      sectionTitle: "[ 泛 音 ]",
      notes: [
        { id: "m11-1", pitch: 5, octave: 1, finger: "勾四", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: true },
        { id: "m11-2", pitch: 2, octave: 1, finger: "挑五", underline: 1, hasDot: true,  dashes: 0, isGlide: false, isHarmonic: true },
        { id: "m11-3", pitch: 1, octave: 1, finger: "挑六", underline: 2, hasDot: false, dashes: 0, isGlide: true,  isHarmonic: true },
        { id: "m11-4", pitch: 6, octave: 0, finger: "勾五", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: true },
        { id: "m11-5", pitch: 2, octave: 1, finger: "挑四", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: true }
      ]
    },
    {
      barNumber: 12,
      isPhraseStart: false,
      notes: [
        { id: "m12-1", pitch: 2, octave: 1, finger: "挑四", underline: 1, hasDot: true,  dashes: 0, isGlide: false, isHarmonic: true },
        { id: "m12-2", pitch: 1, octave: 1, finger: "挑六", underline: 2, hasDot: false, dashes: 0, isGlide: true,  isHarmonic: true },
        { id: "m12-3", pitch: 6, octave: 0, finger: "勾五", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: true },
        { id: "m12-4", pitch: 1, octave: 1, finger: "挑五", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: true }
      ]
    },
    {
      barNumber: 13,
      isPhraseStart: false,
      notes: [
        { id: "m13-1", pitch: 5, octave: 1, finger: "勾四", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: true },
        { id: "m13-2", pitch: 6, octave: 1, finger: "挑三", underline: 1, hasDot: true,  dashes: 0, isGlide: false, isHarmonic: true },
        { id: "m13-3", pitch: 5, octave: 1, finger: "挑四", underline: 2, hasDot: false, dashes: 0, isGlide: true,  isHarmonic: true },
        { id: "m13-4", pitch: 3, octave: 1, finger: "勾五", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: true },
        { id: "m13-5", pitch: 5, octave: 1, finger: "挑四", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: true }
      ]
    },
    {
      barNumber: 14,
      isPhraseStart: false,
      notes: [
        { id: "m14-1", pitch: 2, octave: 1, finger: "挑四", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: true },
        { id: "m14-2", pitch: 2, octave: 1, finger: "挑四", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: true },
        { id: "m14-3", pitch: 3, octave: 1, finger: "勾三", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: true },
        { id: "m14-4", pitch: 3, octave: 1, finger: "勾三", underline: 0, hasDot: false, dashes: 3, isGlide: false, isHarmonic: true }
      ]
    },

    // ==========================================
    // 第 7 页 · 按音流转与急弄段落 [二] ♩ = 104 & [三] ♩ = 120
    // ==========================================
    {
      barNumber: 15,
      isPhraseStart: true,
      sectionTitle: "第 7 页 · [二] ♩ = 104",
      notes: [
        { id: "m15-1", pitch: 6, octave: 0, finger: "挑六", underline: 1, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false },
        { id: "m15-2", pitch: 1, octave: 0, finger: "勾五", underline: 1, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false },
        { id: "m15-3", pitch: 6, octave: 0, finger: "挑六", underline: 1, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false },
        { id: "m15-4", pitch: 5, octave: 0, finger: "散七", underline: 1, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false },
        { id: "m15-5", pitch: 6, octave: 0, finger: "挑六", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false }
      ]
    },
    {
      barNumber: 16,
      isPhraseStart: false,
      notes: [
        { id: "m16-1", pitch: 5, octave: -1, finger: "散七", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false },
        { id: "m16-2", pitch: 5, octave: -1, finger: "散七", underline: 0, hasDot: false, dashes: 1, isGlide: false, isHarmonic: false }
      ]
    },
    {
      barNumber: 17,
      isPhraseStart: true,
      sectionTitle: "[三] ♩ = 120 (高潮急弄)",
      notes: [
        { id: "m17-1", pitch: 7, octave: 0, finger: "外", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false },
        { id: "m17-2", pitch: 6, octave: 0, finger: "挑六", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false },
        { id: "m17-3", pitch: 7, octave: 0, finger: "外", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false }
      ]
    },
    {
      barNumber: 18,
      isPhraseStart: false,
      notes: [
        { id: "m18-1", pitch: 2, octave: 0, finger: "挑六", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false },
        { id: "m18-2", pitch: 3, octave: 0, finger: "勾五", underline: 0, hasDot: false, dashes: 1, isGlide: false, isHarmonic: false }
      ]
    },
    {
      barNumber: 19,
      isPhraseStart: false,
      notes: [
        { id: "m19-1", pitch: 6, octave: 0, finger: "挑六", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false },
        { id: "m19-2", pitch: 5, octave: 0, accidental: "#", finger: "大九", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false },
        { id: "m19-3", pitch: 3, octave: 0, finger: "名九", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false },
        { id: "m19-4", pitch: 2, octave: 0, finger: "挑六", underline: 0, hasDot: false, dashes: 0, isGlide: false, isHarmonic: false }
      ]
    },
    {
      barNumber: 20,
      isPhraseStart: false,
      notes: [
        { id: "m20-1", pitch: 2, octave: 0, finger: "挑六", underline: 0, hasDot: false, dashes: 1, isGlide: false, isHarmonic: false },
        { id: "m20-2", pitch: 2, octave: -1, finger: "散四", underline: 1, hasDot: true,  dashes: 0, isGlide: false, isHarmonic: false },
        { id: "m20-3", pitch: 1, octave: -1, finger: "散五", underline: 2, hasDot: false, dashes: 0, isGlide: true,  isHarmonic: false }
      ]
    }
  ]
};
