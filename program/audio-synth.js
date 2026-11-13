/**
 * 古琴物理拨弦建模合成器 (Karplus-Strong Algorithm)
 * 专为古琴低频、长余音、木质共鸣特性优化，支持多调式定弦 (1=bB, 1=F, 1=C等)
 * 内置古琴徽位纯律声学物理模型与琴弦调音校准引擎 (Opus 评审推荐规范)
 */

// 1. 古琴十三徽弦长比例 (从岳山到各徽的弦长比例)
export const HUI_RATIOS = [
  null,
  1 / 8,  // 一徽 (0.125)
  1 / 6,  // 二徽 (0.1667)
  1 / 5,  // 三徽 (0.2)
  1 / 4,  // 四徽 (0.25)
  1 / 3,  // 五徽 (0.3333)
  2 / 5,  // 六徽 (0.4)
  1 / 2,  // 七徽 (0.5 - 正中八度)
  3 / 5,  // 八徽 (0.6)
  2 / 3,  // 九徽 (0.6667 - 五度)
  3 / 4,  // 十徽 (0.75 - 四度)
  4 / 5,  // 十一徽 (0.8)
  5 / 6,  // 十二徽 (0.8333)
  7 / 8   // 十三徽 (0.875)
];

// 2. 徽位泛音倍率表 (按弦长振动分段)
export const HARMONIC_MULT = {
  1: 8,
  2: 6,
  3: 5,
  4: 4,
  5: 3,
  6: 2.5,
  7: 2,
  8: 5 / 3,
  9: 3,
  10: 4,
  11: 5,
  12: 6,
  13: 8
};

/**
 * 徽位与徽分线性插值计算物理弦长比例
 * 例如: h = 7.6 (七徽六分) -> 七徽(0.5)到八徽(0.6)之间 60% 处
 */
export function huiPos(h) {
  if (h <= 0) return HUI_RATIOS[1];
  if (h >= 13) return HUI_RATIOS[13];
  const i = Math.floor(h);
  const f = h - i;
  const p1 = HUI_RATIOS[i] || HUI_RATIOS[1];
  const p2 = HUI_RATIOS[i + 1] || HUI_RATIOS[13];
  return p1 + (p2 - p1) * f;
}

// 3. 常见古琴定弦散音频率标准表 (一弦至七弦标准频率与唱名)
export const STANDARD_TUNINGS = {
  "1 = ♭B": [
    { string: 1, name: "一弦", noteName: "C2", pitch: 2, octave: -1, freq: 65.41 },
    { string: 2, name: "二弦", noteName: "D2", pitch: 3, octave: -1, freq: 73.42 },
    { string: 3, name: "三弦", noteName: "F2", pitch: 5, octave: -1, freq: 87.31 },
    { string: 4, name: "四弦", noteName: "G2", pitch: 6, octave: -1, freq: 98.00 },
    { string: 5, name: "五弦", noteName: "♭B2", pitch: 1, octave: 0, freq: 116.54 }, // 紧五弦
    { string: 6, name: "六弦", noteName: "C3", pitch: 2, octave: 0, freq: 130.81 },
    { string: 7, name: "七弦", noteName: "D3", pitch: 3, octave: 0, freq: 146.83 }
  ],
  "1 = F": [
    { string: 1, name: "一弦", noteName: "C2", pitch: 5, octave: -1, freq: 65.41 },
    { string: 2, name: "二弦", noteName: "D2", pitch: 6, octave: -1, freq: 73.42 },
    { string: 3, name: "三弦", noteName: "F2", pitch: 1, octave: 0, freq: 87.31 },
    { string: 4, name: "四弦", noteName: "G2", pitch: 2, octave: 0, freq: 98.00 },
    { string: 5, name: "五弦", noteName: "A2", pitch: 3, octave: 0, freq: 110.00 }, // 正调
    { string: 6, name: "六弦", noteName: "C3", pitch: 5, octave: 0, freq: 130.81 },
    { string: 7, name: "七弦", noteName: "D3", pitch: 6, octave: 0, freq: 146.83 }
  ],
  "1 = C": [
    { string: 1, name: "一弦", noteName: "C2", pitch: 1, octave: -1, freq: 65.41 },
    { string: 2, name: "二弦", noteName: "D2", pitch: 2, octave: -1, freq: 73.42 },
    { string: 3, name: "三弦", noteName: "F2", pitch: 4, octave: -1, freq: 87.31 },
    { string: 4, name: "四弦", noteName: "G2", pitch: 5, octave: -1, freq: 98.00 },
    { string: 5, name: "五弦", noteName: "A2", pitch: 6, octave: 0, freq: 110.00 },
    { string: 6, name: "六弦", noteName: "C3", pitch: 1, octave: 0, freq: 130.81 },
    { string: 7, name: "七弦", noteName: "D3", pitch: 2, octave: 0, freq: 146.83 }
  ]
};

// 中文数字转阿拉伯数字映射
const CHINESE_NUMS = {
  "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7,
  "八": 8, "九": 9, "十": 10, "十一": 11, "十二": 12, "十三": 13,
  "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7
};

export class GuqinSynth {
  constructor() {
    this.ctx = null;
    this.masterGain = null;
    this.currentKey = "1 = ♭B";
    this.customOpenFrequencies = null; // 用户实测/校准琴弦频率 [f1, ..., f7]
    this.initAudioContext();
  }

  setKey(keyStr) {
    this.currentKey = keyStr || "1 = ♭B";
  }

  /**
   * 设置实测/校准琴弦频率 (修音校准)
   */
  setCustomOpenFrequencies(freqArray) {
    if (Array.isArray(freqArray) && freqArray.length === 7) {
      this.customOpenFrequencies = [...freqArray];
    } else {
      this.customOpenFrequencies = null;
    }
  }

  /**
   * 获取当前定弦下的 7 根琴弦频率列表 (优先使用校准值)
   */
  getOpenFrequencies() {
    if (this.customOpenFrequencies && this.customOpenFrequencies.length === 7) {
      return [...this.customOpenFrequencies];
    }
    const preset = STANDARD_TUNINGS[this.currentKey] || STANDARD_TUNINGS["1 = ♭B"];
    return preset.map(item => item.freq);
  }

  initAudioContext() {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (AudioContextClass && !this.ctx) {
      this.ctx = new AudioContextClass();
      this.masterGain = this.ctx.createGain();
      this.masterGain.gain.setValueAtTime(0.7, this.ctx.currentTime);
      this.masterGain.connect(this.ctx.destination);
    }
  }

  resume() {
    if (this.ctx && this.ctx.state === 'suspended') {
      return this.ctx.resume();
    }
    return Promise.resolve();
  }

  /**
   * 解析减字指法中的徽位与弦序
   */
  parseFingering(fingerStr) {
    if (!fingerStr || typeof fingerStr !== 'string') return null;
    const str = fingerStr.trim();
    let stringNum = null;
    let huiNum = null;

    // 1. 散音匹配 (如 "散七", "散五", "勾五", "挑六", "抹四", "剔三")
    for (const [cn, num] of Object.entries(CHINESE_NUMS)) {
      if (num <= 7 && (str.endsWith(cn) || str.includes(cn))) {
        stringNum = num;
      }
    }

    // 2. 徽位匹配 (如 "大九", "名十", "七", "十", "九", "注十", "夕九")
    const huiMatches = [
      "十三", "十二", "十一", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"
    ];
    for (const hStr of huiMatches) {
      if (str.includes(hStr) && (!stringNum || str.indexOf(hStr) !== str.lastIndexOf(hStr) || !str.endsWith(hStr))) {
        // 如果包含徽位字符且不单纯是末尾弦号
        if (str.includes('徽') || str.includes('大' + hStr) || str.includes('名' + hStr) || str.includes('中' + hStr) || str.includes('夕' + hStr) || str.includes('注' + hStr)) {
          huiNum = CHINESE_NUMS[hStr];
          break;
        }
      }
    }

    return { string: stringNum, hui: huiNum };
  }

  /**
   * 将简谱或指法转换为对应调号的物理频率
   * 优先使用【徽位纯律物理公式】(Opus 评审算法)，当有明确徽位/弦序时精准修正！
   */
  getFrequency(pitch, octave = 0, isHarmonic = false, accidental = null, finger = null) {
    const openFreqs = this.getOpenFrequencies();

    // 1. 若有明确指法，尝试使用古琴徽位纯律物理公式精准修音
    if (finger) {
      const parsed = this.parseFingering(finger);
      if (parsed && parsed.string && parsed.string >= 1 && parsed.string <= 7) {
        const f0 = openFreqs[parsed.string - 1];
        if (isHarmonic && parsed.hui && HARMONIC_MULT[parsed.hui]) {
          return f0 * HARMONIC_MULT[parsed.hui];
        } else if (!isHarmonic && parsed.hui) {
          const pos = huiPos(parsed.hui);
          if (pos > 0) return f0 / pos;
        } else if (!parsed.hui) {
          return f0; // 散音
        }
      }
    }

    // 2. 基准调号十二平均律计算 (作为通用简谱基底)
    const semitonesFromRoot = {
      1: 0,
      2: 2,
      3: 4,
      4: 5,
      5: 7,
      6: 9,
      7: 11
    };

    let rootFreq = 233.08; // 默认 1=bB3
    if (this.currentKey.includes("F")) {
      rootFreq = 174.61; // 1=F3
    } else if (this.currentKey.includes("C")) {
      rootFreq = 130.81; // 1=C3
    } else if (this.currentKey.includes("G")) {
      rootFreq = 196.00; // 1=G3
    } else if (this.currentKey.includes("D")) {
      rootFreq = 146.83; // 1=D3
    }

    let semitoneOffset = (semitonesFromRoot[pitch] || 0) + octave * 12;

    if (accidental === "#") semitoneOffset += 1;
    if (accidental === "b") semitoneOffset -= 1;

    // 泛音高一个倍频程
    if (isHarmonic) {
      semitoneOffset += 12;
    }

    return rootFreq * Math.pow(2, semitoneOffset / 12);
  }

  /**
   * 物理拨弦声音合成：产生古琴特有的温润木质共鸣与长衰减
   */
  pluck(freq, duration = 2.0, isHarmonic = false) {
    this.initAudioContext();
    this.resume();
    if (!this.ctx) return;

    const sampleRate = this.ctx.sampleRate;
    const period = Math.max(2, Math.round(sampleRate / freq));
    const bufferLength = Math.max(period * 2, 2048);
    const audioBuffer = this.ctx.createBuffer(1, bufferLength, sampleRate);
    const channelData = audioBuffer.getChannelData(0);

    for (let i = 0; i < period; i++) {
      channelData[i] = (Math.random() * 2 - 1) * 0.8;
    }

    const damping = isHarmonic ? 0.995 : 0.988;
    for (let i = period; i < bufferLength; i++) {
      channelData[i] = ((channelData[i - period] + channelData[i - period + 1]) / 2) * damping;
    }

    const source = this.ctx.createBufferSource();
    source.buffer = audioBuffer;
    source.loop = true;

    const bodyFilter = this.ctx.createBiquadFilter();
    bodyFilter.type = "lowpass";
    bodyFilter.frequency.setValueAtTime(isHarmonic ? 2400 : 1200, this.ctx.currentTime);
    bodyFilter.Q.setValueAtTime(2.0, this.ctx.currentTime);

    const gainNode = this.ctx.createGain();
    const now = this.ctx.currentTime;
    gainNode.gain.setValueAtTime(1.0, now);
    gainNode.gain.exponentialRampToValueAtTime(0.001, now + duration);

    source.connect(bodyFilter);
    bodyFilter.connect(gainNode);
    gainNode.connect(this.masterGain);

    source.start(now);
    source.stop(now + duration + 0.1);
  }
}
