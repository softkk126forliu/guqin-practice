/**
 * 古琴专用实时音高与起音探测器 (YIN Algorithm + Spectral Flux)
 * 专为 55Hz ~ 1200Hz 低频宽域、长余音优化
 */
export class PitchDetector {
  constructor(options = {}) {
    this.audioCtx = null;
    this.analyser = null;
    this.micStream = null;
    this.bufferSize = options.bufferSize || 4096; // 4096 点分析窗，确保 55Hz 低频分辨率
    this.buffer = new Float32Array(this.bufferSize);
    this.isRunning = false;
    this.onPitchResult = options.onPitchResult || null;

    // YIN 算法差分自相关缓冲区
    this.yinBuffer = new Float32Array(this.bufferSize / 2);
    this.yinThreshold = 0.15; // 差分阈值

    // 音量门限 (低于此值视为静音，用于 3 秒静音计时)
    this.silenceRmsThreshold = 0.015;

    // 内部状态跟踪 (用于走手音平稳判定与起音突变)
    this.lastRms = 0;
    this.currentStablePitch = 0;
    this.stablePitchStartTime = 0;
  }

  async startMic() {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    this.audioCtx = new AudioContextClass();
    if (this.audioCtx.state === 'suspended') {
      await this.audioCtx.resume();
    }

    this.micStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: false, // 关闭回声消除，防止古琴泛音和余音被误杀
        noiseSuppression: false, // 关闭降噪，保留原汁原味弦音
        autoGainControl: false
      }
    });

    const micSource = this.audioCtx.createMediaStreamSource(this.micStream);
    this.analyser = this.audioCtx.createAnalyser();
    this.analyser.fftSize = this.bufferSize;
    micSource.connect(this.analyser);

    this.isRunning = true;
    this.loop();
  }

  stop() {
    this.isRunning = false;
    if (this.micStream) {
      this.micStream.getTracks().forEach(track => track.stop());
      this.micStream = null;
    }
    if (this.audioCtx) {
      this.audioCtx.close();
      this.audioCtx = null;
    }
  }

  loop() {
    if (!this.isRunning) return;

    this.analyser.getFloatTimeDomainData(this.buffer);

    // 1. 计算 RMS 能量
    let sum = 0;
    for (let i = 0; i < this.buffer.length; i++) {
      sum += this.buffer[i] * this.buffer[i];
    }
    const rms = Math.sqrt(sum / this.buffer.length);
    const isSilent = rms < this.silenceRmsThreshold;

    let detectedFreq = -1;
    let isOnset = false;
    let isStableGlide = false;
    const now = performance.now();

    if (!isSilent) {
      // 2. 能量突变检测 (Onset)
      const rmsDiff = rms - this.lastRms;
      if (rmsDiff > 0.025) {
        isOnset = true;
      }

      // 3. 执行 YIN 基频提取
      detectedFreq = this.yinPitch(this.buffer, this.audioCtx.sampleRate);

      if (detectedFreq > 0) {
        // 4. 走手音平稳度追踪 (未发生新 Onset，但在目标频段平稳持续 80ms)
        const semitoneDist = Math.abs(12 * Math.log2(detectedFreq / (this.currentStablePitch || detectedFreq)));
        if (semitoneDist < 0.4) {
          if (now - this.stablePitchStartTime >= 80) {
            isStableGlide = true;
          }
        } else {
          this.currentStablePitch = detectedFreq;
          this.stablePitchStartTime = now;
        }
      }
    } else {
      this.currentStablePitch = 0;
    }

    this.lastRms = rms;

    // 回调通知跟谱引擎
    if (this.onPitchResult) {
      this.onPitchResult({
        frequency: detectedFreq,
        rms: rms,
        isSilent: isSilent,
        isOnset: isOnset,
        isStableGlide: isStableGlide,
        timestamp: now
      });
    }

    requestAnimationFrame(() => this.loop());
  }

  /**
   * 经典 YIN 算法：用于高精度提取古琴基频
   */
  yinPitch(buffer, sampleRate) {
    const halfLen = Math.floor(buffer.length / 2);
    const yinBuffer = this.yinBuffer;

    // 差分平方和
    yinBuffer[0] = 1;
    let runningSum = 0;
    for (let tau = 1; tau < halfLen; tau++) {
      let delta = 0;
      for (let i = 0; i < halfLen; i++) {
        const diff = buffer[i] - buffer[i + tau];
        delta += diff * diff;
      }
      runningSum += delta;
      yinBuffer[tau] = delta * tau / (runningSum || 1);
    }

    // 寻找第一个低于阈值的局部极小点
    let tauEstimate = -1;
    for (let tau = 2; tau < halfLen; tau++) {
      if (yinBuffer[tau] < this.yinThreshold) {
        while (tau + 1 < halfLen && yinBuffer[tau + 1] < yinBuffer[tau]) {
          tau++;
        }
        tauEstimate = tau;
        break;
      }
    }

    if (tauEstimate === -1) {
      // 容错：查找全局最低点
      let minVal = 100;
      let minTau = -1;
      for (let tau = 2; tau < halfLen; tau++) {
        if (yinBuffer[tau] < minVal) {
          minVal = yinBuffer[tau];
          minTau = tau;
        }
      }
      if (minVal < 0.35) {
        tauEstimate = minTau;
      }
    }

    if (tauEstimate > 0) {
      // 抛物线插值，提升频率精度至分音（Cents）级别
      const s0 = yinBuffer[tauEstimate - 1];
      const s1 = yinBuffer[tauEstimate];
      const s2 = yinBuffer[tauEstimate + 1];
      const betterTau = tauEstimate + (s2 - s0) / (2 * (2 * s1 - s2 - s0) || 1);
      return sampleRate / betterTau;
    }

    return -1;
  }
}

