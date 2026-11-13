/**
 * 古琴智能跟谱双触发状态机引擎 (支持动态调号与双触发)
 * - 前向受限滑动窗口 [N, N+2]
 * - 双触发：击弦 Onset 推进 / 走手音 80ms 平稳推进
 * - 3 秒静音自愈：长停顿自动平滑倒回当前乐句首音
 */
export class ScoreEngine {
  constructor(scoreData, synth) {
    this.score = scoreData;
    this.synth = synth;
    this.flatNotes = [];
    this.currentIndex = 0;

    // 回调事件
    this.onCursorMove = null;
    this.onRewind = null;
    this.onStatusUpdate = null;

    // 静音自愈计时器 (毫秒)
    this.silenceStartTime = 0;
    this.silenceDuration = 0;
    this.isRewound = false;

    // 统计数据 (用于轻量复盘)
    this.stats = {
      wrongCount: 0,
      rewindCount: 0,
      startTime: 0,
      measureErrors: {}
    };

    this.flattenScore();
  }

  flattenScore() {
    this.flatNotes = [];
    let phraseHeadIndex = 0;

    // 同步合成器调号
    if (this.synth && this.score.key) {
      this.synth.setKey(this.score.key);
    }

    this.score.measures.forEach(measure => {
      if (measure.isPhraseStart) {
        phraseHeadIndex = this.flatNotes.length;
      }
      measure.notes.forEach(note => {
        const freq = this.synth.getFrequency(note.pitch, note.octave, note.isHarmonic, note.accidental, note.finger);
        let chordFreq = null;
        if (note.chordPitch !== undefined) {
          chordFreq = this.synth.getFrequency(note.chordPitch, note.chordOctave || 0, !!note.chordHarmonic, null, note.finger);
        }
        this.flatNotes.push({
          ...note,
          barNumber: measure.barNumber,
          phraseHeadIndex: phraseHeadIndex,
          targetFreq: freq,
          chordFreq: chordFreq,
          globalIndex: this.flatNotes.length
        });
      });
    });
  }

  /**
   * 基于实测琴弦频率进行整曲目标频率热校准 (修音校正)
   */
  recalibrate(customOpenFreqs) {
    if (this.synth) {
      this.synth.setCustomOpenFrequencies(customOpenFreqs);
    }
    const savedIndex = this.currentIndex;
    this.flattenScore();
    this.currentIndex = Math.min(savedIndex, this.flatNotes.length - 1);
  }

  reset() {
    this.currentIndex = 0;
    this.silenceStartTime = 0;
    this.silenceDuration = 0;
    this.isRewound = false;
    this.stats = {
      wrongCount: 0,
      rewindCount: 0,
      startTime: performance.now(),
      measureErrors: {}
    };
    if (this.onCursorMove) {
      this.onCursorMove(0, this.flatNotes[0], "reset");
    }
  }

  setCursor(index) {
    if (index >= 0 && index < this.flatNotes.length) {
      this.currentIndex = index;
      this.silenceDuration = 0;
      if (this.onCursorMove) {
        this.onCursorMove(index, this.flatNotes[index], "manual");
      }
    }
  }

  getExpectedDurationMs(note) {
    let bpm = 66;
    if (this.score && this.score.tempo) {
      const m = this.score.tempo.match(/(\d+)/);
      if (m) bpm = parseInt(m[1], 10);
    }
    const quarterMs = (60 / bpm) * 1000;
    let factor = 1.0;
    if (note.underline === 1) factor = 0.5;
    else if (note.underline === 2) factor = 0.25;
    if (note.hasDot) factor *= 1.5;
    const dashes = note.dashes || 0;
    return (factor + dashes) * quarterMs;
  }

  /**
   * 处理音频输入帧
   */
  processAudioFrame(frame) {
    if (this.currentIndex >= this.flatNotes.length) return;

    const currentNote = this.flatNotes[this.currentIndex];
    const now = frame.timestamp;

    // 1. 处理静音与自愈倒回 (结合音符期望时值，全音符等长延音不误判)
    if (frame.isSilent) {
      if (!this.silenceStartTime) {
        this.silenceStartTime = now;
      }
      this.silenceDuration = now - this.silenceStartTime;

      const expectedDuration = this.getExpectedDurationMs(currentNote);
      const silenceThreshold = Math.max(3000, expectedDuration * 1.5);

      if (this.silenceDuration >= silenceThreshold && !this.isRewound) {
        const phraseHead = currentNote.phraseHeadIndex;
        if (this.currentIndex > phraseHead) {
          this.currentIndex = phraseHead;
          this.isRewound = true;
          this.stats.rewindCount++;
          if (this.onRewind) {
            this.onRewind(phraseHead, this.flatNotes[phraseHead]);
          }
        }
      }

      if (this.onStatusUpdate) {
        this.onStatusUpdate({
          state: "silence",
          silenceSeconds: (this.silenceDuration / 1000).toFixed(1),
          currentNote: currentNote
        });
      }
      return;
    }

    this.silenceStartTime = 0;
    this.silenceDuration = 0;
    this.isRewound = false;

    if (frame.frequency <= 0) return;

    // 2. 双触发匹配逻辑 ([N, N+2] 受限滑动窗口)
    const candidates = [
      this.flatNotes[this.currentIndex],
      this.flatNotes[this.currentIndex + 1],
      this.flatNotes[this.currentIndex + 2]
    ].filter(Boolean);

    let matchedCandidateIndex = -1;
    let minCentsDiff = 9999;

    candidates.forEach((cand, offset) => {
      let cents = 1200 * Math.log2(frame.frequency / cand.targetFreq);

      // 仅对一弦极低频 (C2 约 65Hz) 在麦克风拾取到二次谐波时做 +1200 音分折叠，保护二至七弦及所有高八度泛音
      if (cand.targetFreq < 95 && !cand.isHarmonic && Math.abs(cents - 1200) < 50) {
        cents -= 1200;
      }

      const absCents = Math.abs(cents);
      const tolerance = cand.isGlide ? 48 : 38;

      if (absCents <= tolerance) {
        if (cand.isGlide) {
          // 走手音：平稳滑动停留或起音触发
          if (frame.isStableGlide || frame.isOnset) {
            if (absCents < minCentsDiff) {
              minCentsDiff = absCents;
              matchedCandidateIndex = offset;
            }
          }
        } else {
          // 击弦音：必须有明确起音突变 (isOnset)，防止同音反复 (如 6 6 6 6 3) 余音穿透连续跳动
          if (frame.isOnset) {
            if (absCents < minCentsDiff) {
              minCentsDiff = absCents;
              matchedCandidateIndex = offset;
            }
          }
        }
      }
    });

    if (matchedCandidateIndex !== -1) {
      const advanceSteps = matchedCandidateIndex + 1;
      this.currentIndex = Math.min(this.currentIndex + advanceSteps, this.flatNotes.length - 1);

      const target = this.flatNotes[this.currentIndex];
      const triggerType = candidates[matchedCandidateIndex].isGlide ? "glide-hit" : "onset-hit";

      if (this.onCursorMove) {
        this.onCursorMove(this.currentIndex, target, triggerType, {
          cents: minCentsDiff,
          skippedNotes: advanceSteps - 1
        });
      }
    } else {
      // 错音统计严格去抖：仅在有新的起音击弦 (isOnset) 时累计一次失误，杜绝每帧暴增
      if (frame.isOnset) {
        const currentBar = currentNote.barNumber;
        this.stats.measureErrors[currentBar] = (this.stats.measureErrors[currentBar] || 0) + 1;
        this.stats.wrongCount++;
      }

      if (this.onStatusUpdate) {
        this.onStatusUpdate({
          state: "waiting",
          heardFreq: frame.frequency,
          expectedFreq: currentNote.targetFreq,
          cents: Math.round(1200 * Math.log2(frame.frequency / currentNote.targetFreq))
        });
      }
    }
  }
}
