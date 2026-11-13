import { SCORES_LIBRARY } from './scores-library.js';
import { GuqinSynth, STANDARD_TUNINGS } from './audio-synth.js';
import { PitchDetector } from './pitch-detector.js';
import { ScoreEngine } from './score-engine.js';
import { getJianziSvg } from './jianzi-renderer.js';

class GuqinApp {
  constructor() {
    this.currentSongKey = 'daoyi';
    this.score = SCORES_LIBRARY[this.currentSongKey];
    this.synth = new GuqinSynth();
    this.engine = new ScoreEngine(this.score, this.synth);
    this.detector = new PitchDetector({
      onPitchResult: (frame) => this.handleAudioFrame(frame)
    });

    this.cursorEl = document.getElementById('smooth-capsule-cursor');
    this.sheetEl = document.getElementById('score-sheet');
    this.slurSvgLayer = document.getElementById('slur-svg-layer');
    this.statusDot = document.getElementById('status-dot');
    this.statusText = document.getElementById('status-text');
    this.pitchFeedback = document.getElementById('pitch-feedback');
    this.tunerNeedle = document.getElementById('tuner-needle');

    this.isSimulating = false;
    this.simulationTimer = null;
    this.isMicActive = false;

    // 调音与校音 (修音) 状态
    this.isTunerOpen = false;
    this.isTunerMicListening = false;
    this.calibratedFreqs = null;
    this.activeTunerStringIdx = -1;
    this.popoverTargetNote = null;
    this.showCropView = true; // 默认优先呈现原书单字高清墨迹切片 (guqinMM 范式)

    // AB 循环
    this.isABLoopActive = false;
    this.abStartBar = 1;
    this.abEndBar = 2;

    this.attachEngineCallbacks();
    this.initUI();
    this.renderScore();
    this.bindEvents();
    this.initTuner();
  }

  initUI() {
    this.updateHeaderMeta();
    document.getElementById('score-json-editor').value = JSON.stringify(this.score, null, 2);
    this.updateDockStatus('normal', '【修音与校对模式】点击乐谱可试听示范音，点击【🎵 调音/校音】校准琴弦；练琴时随时开启麦克风跟谱。');
  }

  updateHeaderMeta() {
    document.getElementById('book-title-center').textContent = this.score.title;
    document.getElementById('book-page-num').textContent = this.score.pageNumber || '1';

    const metaLeft = document.getElementById('meta-col-left');
    metaLeft.innerHTML = `
      <div>${this.score.subtitle || ''}</div>
    `;

    const metaRight = document.getElementById('meta-col-right');
    metaRight.innerHTML = `
      <div>${this.score.key}</div>
      <div>${this.score.tuning}</div>
      <div>${this.score.tempo}</div>
    `;
  }

  /**
   * 严格排版渲染：简谱在上，真合体减字符在下 (采用 SVG 矢量字模渲染)
   */
  renderScore() {
    const preservedCursor = this.cursorEl;
    const preservedSvg = this.slurSvgLayer;
    this.sheetEl.innerHTML = '';
    this.sheetEl.appendChild(preservedSvg);
    this.sheetEl.appendChild(preservedCursor);

    const measures = this.score.measures;
    let currentLineEl = null;

    measures.forEach((measure) => {
      if (measure.isPhraseStart || !currentLineEl) {
        currentLineEl = document.createElement('div');
        currentLineEl.className = 'score-line';

        if (measure.sectionTitle) {
          const sectionBadge = document.createElement('div');
          sectionBadge.className = 'section-label';
          sectionBadge.textContent = measure.sectionTitle;
          currentLineEl.appendChild(sectionBadge);
        }

        this.sheetEl.appendChild(currentLineEl);
      }

      const measureBox = document.createElement('div');
      measureBox.className = 'measure-box';
      measureBox.dataset.barNumber = measure.barNumber;

      if (this.isABLoopActive && measure.barNumber >= this.abStartBar && measure.barNumber <= this.abEndBar) {
        measureBox.classList.add('in-ab-loop');
      }

      const notesFlow = document.createElement('div');
      notesFlow.className = 'notes-flow';

      measure.notes.forEach((note) => {
        const flatNote = this.engine.flatNotes.find(fn => fn.id === note.id);
        const globalIdx = flatNote ? flatNote.globalIndex : 0;

        const unit = document.createElement('div');
        unit.className = 'note-unit';
        unit.dataset.globalIndex = globalIdx;
        unit.dataset.noteId = note.id;
        unit.dataset.barNumber = measure.barNumber;
        unit.dataset.isGlide = note.isGlide ? "true" : "false";

        // 1. 上层：简谱主音符
        const pitchWrap = document.createElement('div');
        pitchWrap.className = 'unit-pitch-wrap';

        const body = document.createElement('div');
        body.className = 'pitch-body';

        // 装饰花音群 (如 623, 361, 32, 71)
        if (note.grace) {
          const graceWrap = document.createElement('div');
          graceWrap.className = 'grace-wrap';
          graceWrap.innerHTML = `
            <div class="grace-cluster">
              <span class="grace-slur">⌒</span>
              <span class="grace-numbers">${note.grace}</span>
            </div>
          `;
          body.appendChild(graceWrap);
        }

        if (note.accidental) {
          const acc = document.createElement('span');
          acc.style.fontSize = '14px';
          acc.style.marginRight = '1px';
          acc.textContent = note.accidental;
          body.appendChild(acc);
        }

        // 双音和弦 vs 标准单音
        if (note.chordPitch !== undefined) {
          const chordStack = document.createElement('div');
          chordStack.className = 'chord-stack';

          const topPart = document.createElement('div');
          topPart.className = 'chord-top';
          if (note.isHarmonic) {
            topPart.innerHTML += `<span class="harmonic-ring"><svg class="harmonic-ring-svg" viewBox="0 0 10 10"><circle cx="5" cy="5" r="3.6" fill="none" stroke="#222" stroke-width="1.2"/></svg></span>`;
          }
          if (note.octave > 0) {
            topPart.innerHTML += `<span class="dot-high"></span>`;
          }
          topPart.innerHTML += `<span class="chord-glyph">${note.pitch}</span>`;

          const botPart = document.createElement('div');
          botPart.className = 'chord-bot';
          if (note.chordHarmonic) {
            botPart.innerHTML += `<span class="harmonic-ring"><svg class="harmonic-ring-svg" viewBox="0 0 10 10"><circle cx="5" cy="5" r="3.6" fill="none" stroke="#222" stroke-width="1.2"/></svg></span>`;
          }
          if (note.chordOctave > 0) {
            botPart.innerHTML += `<span class="dot-high"></span>`;
          }
          botPart.innerHTML += `<span class="chord-glyph">${note.chordPitch}</span>`;
          if (note.chordOctave < 0) {
            botPart.innerHTML += `<span class="dot-low"></span>`;
          }

          chordStack.appendChild(topPart);
          chordStack.appendChild(botPart);
          body.appendChild(chordStack);
        } else {
          // 标准单音：泛音圈与高音点在 pitchWrap 顶部按顺序独立居中排布，彻底告别“电灯泡”碰撞
          if (note.isHarmonic) {
            const ring = document.createElement('span');
            ring.className = 'harmonic-ring';
            ring.innerHTML = `<svg class="harmonic-ring-svg" viewBox="0 0 10 10"><circle cx="5" cy="5" r="3.6" fill="none" stroke="#222" stroke-width="1.2"/></svg>`;
            pitchWrap.appendChild(ring);
          }

          if (note.octave > 0) {
            for (let o = 0; o < note.octave; o++) {
              const dotH = document.createElement('span');
              dotH.className = 'dot-high';
              pitchWrap.appendChild(dotH);
            }
          }

          const glyph = document.createElement('span');
          glyph.className = 'pitch-glyph';
          glyph.textContent = note.pitch;
          body.appendChild(glyph);
        }

        if (note.hasDot) {
          const rDot = document.createElement('span');
          rDot.className = 'pitch-rhythm-dot';
          rDot.textContent = '·';
          body.appendChild(rDot);
        }
        pitchWrap.appendChild(body);

        if (note.octave < 0 && note.chordPitch === undefined) {
          for (let o = 0; o < Math.abs(note.octave); o++) {
            const dotL = document.createElement('span');
            dotL.className = 'dot-low';
            pitchWrap.appendChild(dotL);
          }
        }

        if (note.underline === 1) {
          const uSingle = document.createElement('div');
          uSingle.className = 'rhythm-underline-single';
          pitchWrap.appendChild(uSingle);
        } else if (note.underline === 2) {
          const uDouble = document.createElement('div');
          uDouble.className = 'rhythm-underline-double';
          uDouble.innerHTML = '<span></span><span></span>';
          pitchWrap.appendChild(uDouble);
        }

        unit.appendChild(pitchWrap);

        // 2. 下层：真实古琴合体减字符 (支持原书单字切片与矢量字模双模)
        const jianziEl = document.createElement('div');
        jianziEl.className = 'jianzi-glyph';
        jianziEl.innerHTML = getJianziSvg(note, this.showCropView);
        unit.appendChild(jianziEl);

        // 点击音符试听与校对
        unit.addEventListener('click', (e) => {
          this.clearErrorBadges();
          this.synth.pluck(flatNote.targetFreq, 1.8, note.isHarmonic);
          if (flatNote.chordFreq) {
            setTimeout(() => {
              this.synth.pluck(flatNote.chordFreq, 1.4, !!note.chordHarmonic);
            }, 25);
          }
          this.engine.setCursor(globalIdx);
          this.updateCursor(unit, 'click');
          const titlePitch = note.chordPitch ? `${note.pitch}/${note.chordPitch}` : `${note.pitch}`;
          this.updateDockStatus('normal', `点击试听：${note.finger || ''} (${titlePitch}) · 纯律频率 ${Math.round(flatNote.targetFreq)} Hz`);

          // 若点击的是减字谱区域，弹出指法释义与示范修音卡片
          if (e.target.closest('.jianzi-glyph')) {
            this.showNotePopover(note, flatNote);
          }
        });

        notesFlow.appendChild(unit);

        // 3. 延音增时横线
        if (note.dashes && note.dashes > 0) {
          for (let d = 0; d < note.dashes; d++) {
            const dashUnit = document.createElement('div');
            dashUnit.className = 'dash-unit';
            dashUnit.innerHTML = '<span class="dash-symbol">—</span>';
            notesFlow.appendChild(dashUnit);
          }
        }
      });

      measureBox.appendChild(notesFlow);
      currentLineEl.appendChild(measureBox);
    });

    setTimeout(() => {
      this.drawSlurs();
      const firstNoteUnit = this.sheetEl.querySelector('.note-unit[data-global-index="0"]');
      if (firstNoteUnit) {
        this.updateCursor(firstNoteUnit, 'init');
      }
    }, 100);
  }

  clearErrorBadges() {
    this.sheetEl.querySelectorAll('.error-badge').forEach(b => b.remove());
    this.sheetEl.querySelectorAll('.shake-error').forEach(u => u.classList.remove('shake-error'));
  }

  drawSlurs() {
    this.slurSvgLayer.innerHTML = '';
    const sheetRect = this.sheetEl.getBoundingClientRect();
    const glideUnits = this.sheetEl.querySelectorAll('.note-unit[data-is-glide="true"]');

    glideUnits.forEach(unit => {
      const globalIdx = parseInt(unit.dataset.globalIndex, 10);
      const prevUnit = this.sheetEl.querySelector(`.note-unit[data-global-index="${globalIdx - 1}"]`);
      if (!prevUnit) return;

      const r1 = prevUnit.querySelector('.pitch-glyph').getBoundingClientRect();
      const r2 = unit.querySelector('.pitch-glyph').getBoundingClientRect();

      if (Math.abs(r1.top - r2.top) < 25) {
        const x1 = r1.left - sheetRect.left + r1.width / 2;
        const y1 = r1.top - sheetRect.top - 2;
        const x2 = r2.left - sheetRect.left + r2.width / 2;
        const y2 = r2.top - sheetRect.top - 2;
        const cx = (x1 + x2) / 2;
        const cy = y1 - 8;

        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', `M ${x1} ${y1} Q ${cx} ${cy} ${x2} ${y2}`);
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke', '#111110');
        path.setAttribute('stroke-width', '1.6');
        path.setAttribute('stroke-linecap', 'round');
        this.slurSvgLayer.appendChild(path);
      }
    });
  }

  updateCursor(targetElement, triggerType = 'advance') {
    if (!targetElement) return;

    const sheetRect = this.sheetEl.getBoundingClientRect();
    const unitRect = targetElement.getBoundingClientRect();

    const left = unitRect.left - sheetRect.left - 5;
    const top = unitRect.top - sheetRect.top - 4;
    const width = unitRect.width + 10;
    const height = unitRect.height + 8;

    this.cursorEl.style.left = `${left}px`;
    this.cursorEl.style.top = `${top}px`;
    this.cursorEl.style.width = `${width}px`;
    this.cursorEl.style.height = `${height}px`;
    this.cursorEl.style.opacity = '1';

    this.cursorEl.classList.remove('cursor-hit-pulse', 'cursor-gliding', 'cursor-waiting');

    if (triggerType === 'onset-hit') {
      this.cursorEl.classList.add('cursor-hit-pulse');
    } else if (triggerType === 'glide-hit') {
      this.cursorEl.classList.add('cursor-gliding');
    } else if (triggerType === 'waiting') {
      this.cursorEl.classList.add('cursor-waiting');
    }

    if (unitRect.top < 120 || unitRect.bottom > window.innerHeight - 120) {
      targetElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  updateTunerGauge(cents) {
    if (!this.tunerNeedle) return;
    const clampedCents = Math.max(-50, Math.min(50, cents));
    const needlePercent = 50 + (clampedCents / 50) * 50;

    this.tunerNeedle.style.left = `${needlePercent}%`;
    if (Math.abs(cents) <= 15) {
      this.tunerNeedle.classList.add('in-tune');
    } else {
      this.tunerNeedle.classList.remove('in-tune');
    }
  }

  attachEngineCallbacks() {
    this.engine.onCursorMove = (index, targetNote, triggerType, meta) => {
      this.clearErrorBadges();

      if (this.isABLoopActive && targetNote.barNumber > this.abEndBar) {
        const loopStartNote = this.engine.flatNotes.find(fn => fn.barNumber === this.abStartBar);
        if (loopStartNote) {
          this.engine.setCursor(loopStartNote.globalIndex);
          this.updateDockStatus('normal', `🔁 AB 循环：已倒回第 ${this.abStartBar} 小节开头！`);
          return;
        }
      }

      const unit = this.sheetEl.querySelector(`.note-unit[data-global-index="${index}"]`);
      if (unit) {
        this.updateCursor(unit, triggerType);
      }
      this.statusDot.className = 'status-indicator-dot dot-green';
      this.statusText.textContent = `跟谱推进：命中第 ${targetNote.barNumber} 小节 (${targetNote.pitch})`;
      if (meta && meta.cents !== undefined) {
        this.pitchFeedback.textContent = `${Math.round(targetNote.targetFreq)} Hz (${Math.round(meta.cents)} cents)`;
        this.updateTunerGauge(meta.cents);
      }
    };

    this.engine.onRewind = (phraseHeadIndex, headNote) => {
      this.clearErrorBadges();
      const unit = this.sheetEl.querySelector(`.note-unit[data-global-index="${phraseHeadIndex}"]`);
      if (unit) {
        this.updateCursor(unit, 'waiting');
      }
      this.statusDot.className = 'status-indicator-dot dot-amber';
      this.statusText.textContent = `⏳ 停顿超时已超 3 秒：光标已平滑倒回本句首音，重弹第一音即可继续！`;
    };

    this.engine.onStatusUpdate = (info) => {
      if (info.state === 'silence') {
        if (info.silenceSeconds > 0.8) {
          this.statusText.textContent = `静音中 (${info.silenceSeconds}s) · 满 3 秒将自动倒回乐句起点`;
        }
      } else if (info.state === 'waiting') {
        const curUnit = this.sheetEl.querySelector(`.note-unit[data-global-index="${this.engine.currentIndex}"]`);
        if (curUnit) {
          this.updateCursor(curUnit, 'waiting');
          curUnit.classList.add('shake-error');
          setTimeout(() => curUnit.classList.remove('shake-error'), 400);

          if (!curUnit.querySelector('.error-badge')) {
            const badge = document.createElement('div');
            badge.className = 'error-badge';
            badge.textContent = '❌ 错音等待';
            curUnit.appendChild(badge);
          }
        }
        this.statusDot.className = 'status-indicator-dot dot-red';
        this.statusText.textContent = `⚠️ 听到错音！光标原地锁定，点击该音符试听纠正，或停顿3秒倒回。`;
        if (info.cents !== undefined) {
          this.pitchFeedback.textContent = `${Math.round(info.heardFreq)} Hz (${info.cents} cents)`;
          this.updateTunerGauge(info.cents);
        }
      }
    };
  }

  bindEvents() {
    window.addEventListener('resize', () => {
      this.drawSlurs();
      const curUnit = this.sheetEl.querySelector(`.note-unit[data-global-index="${this.engine.currentIndex}"]`);
      if (curUnit) this.updateCursor(curUnit, 'resize');
    });

    // 曲目切换
    const songSelect = document.getElementById('song-selector');
    songSelect.addEventListener('change', (e) => {
      this.loadScore(e.target.value);
    });

    // 减字谱原书单字切图 vs 矢量字模切换
    const btnToggleCrop = document.getElementById('btn-toggle-crop-view');
    if (btnToggleCrop) {
      btnToggleCrop.addEventListener('click', () => {
        this.showCropView = !this.showCropView;
        btnToggleCrop.innerHTML = this.showCropView
          ? '<span style="color:#1b5e20; font-weight:bold;">🖼</span> 减字: 原书真迹'
          : '<span style="color:#555; font-weight:bold;">✒</span> 减字: 矢量字模';
        this.renderScore();
        this.updateDockStatus('normal', this.showCropView ? '已呈现原书单字高清墨迹切图！' : '已切换为矢量排印字模！');
      });
    }

    document.getElementById('btn-auto-simulate').addEventListener('click', () => {
      this.toggleAutoSimulation();
    });

    const btnAb = document.getElementById('btn-toggle-ab');
    btnAb.addEventListener('click', () => {
      this.isABLoopActive = !this.isABLoopActive;
      btnAb.classList.toggle('btn-active-loop', this.isABLoopActive);
      this.renderScore();
      if (this.isABLoopActive) {
        this.updateDockStatus('normal', `🔁 已开启第 ${this.abStartBar}-${this.abEndBar} 小节 AB 循环练习`);
      } else {
        this.updateDockStatus('normal', '已退出 AB 循环模式，恢复全曲跟练');
      }
    });

    document.getElementById('btn-simulate-error').addEventListener('click', () => {
      this.simulateWrongNoteOnly();
    });

    document.getElementById('btn-simulate-silence').addEventListener('click', () => {
      this.simulateLongSilence();
    });

    document.getElementById('btn-toggle-mic').addEventListener('click', () => {
      this.toggleMicrophone();
    });

    const reviewModal = document.getElementById('review-modal');
    document.getElementById('btn-show-review').addEventListener('click', () => {
      reviewModal.classList.add('open');
    });
    document.getElementById('btn-close-review').addEventListener('click', () => {
      reviewModal.classList.remove('open');
    });
    document.getElementById('btn-loop-problem-bar').addEventListener('click', () => {
      this.isABLoopActive = true;
      this.abStartBar = 1;
      this.abEndBar = 1;
      btnAb.classList.add('btn-active-loop');
      btnAb.textContent = '🔁 AB 循环 (第1小节精练)';
      this.renderScore();
      reviewModal.classList.remove('open');
      this.updateDockStatus('normal', '已自动锁定第 1 小节为精练段落！');
    });

    document.getElementById('btn-reset').addEventListener('click', () => {
      this.stopSimulation();
      this.clearErrorBadges();
      this.engine.reset();
      const firstUnit = this.sheetEl.querySelector('.note-unit[data-global-index="0"]');
      if (firstUnit) this.updateCursor(firstUnit, 'init');
      this.updateDockStatus('normal', '已重置到谱首');
    });

    const drawerOverlay = document.getElementById('drawer-overlay');
    const editorDrawer = document.getElementById('editor-drawer');
    const toggleDrawer = (open) => {
      drawerOverlay.classList.toggle('open', open);
      editorDrawer.classList.toggle('open', open);
    };

    document.getElementById('btn-toggle-drawer').addEventListener('click', () => toggleDrawer(true));
    document.getElementById('btn-close-drawer').addEventListener('click', () => toggleDrawer(false));
    drawerOverlay.addEventListener('click', () => toggleDrawer(false));

    document.getElementById('btn-apply-score').addEventListener('click', () => {
      try {
        const newScore = JSON.parse(document.getElementById('score-json-editor').value);
        this.score = newScore;
        this.engine = new ScoreEngine(this.score, this.synth);
        this.updateHeaderMeta();
        this.renderScore();
        toggleDrawer(false);
        this.updateDockStatus('normal', '新乐谱已成功更新并重新排版！');
      } catch (e) {
        alert('JSON 格式有误，请检查后再保存：' + e.message);
      }
    });

    document.getElementById('btn-export-score').addEventListener('click', () => {
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(this.score, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `${this.score.title || '古琴谱'}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
      this.updateDockStatus('normal', `已导出曲谱文件：${this.score.title}.json`);
    });

    const fileInput = document.getElementById('json-file-input');
    fileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (event) => {
          try {
            const importedScore = JSON.parse(event.target.result);
            this.score = importedScore;
            this.engine = new ScoreEngine(this.score, this.synth);
            this.attachEngineCallbacks();
            this.updateHeaderMeta();
            this.renderScore();
            document.getElementById('score-json-editor').value = JSON.stringify(this.score, null, 2);
            toggleDrawer(false);
            this.updateDockStatus('normal', `成功导入并载入新谱：《${this.score.title}》！`);
          } catch (err) {
            alert('文件解析失败，请确保导入的是有效的 JSON 曲谱文件：' + err.message);
          }
        };
        reader.readAsText(file);
      }
    });

    const photoInput = document.getElementById('photo-upload-input');
    const previewHint = document.getElementById('upload-preview-hint');
    photoInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) {
        const fname = file.name.toLowerCase();
        if (fname.includes('0963') || fname.includes('春风') || fname.includes('chunfeng')) {
          this.loadScore('chunfeng');
          toggleDrawer(false);
          previewHint.textContent = `✓ 已匹配并载入照片对应曲目：《春风》(第179页 26小节)`;
          this.updateDockStatus('normal', `已根据谱照名称匹配并呈现内置全量谱：《春风》！`);
        } else if (fname.includes('0961') || fname.includes('0962') || fname.includes('捣衣') || fname.includes('daoyi')) {
          this.loadScore('daoyi');
          toggleDrawer(false);
          previewHint.textContent = `✓ 已匹配并载入照片对应曲目：《捣衣》(第6-7页 20小节)`;
          this.updateDockStatus('normal', `已根据谱照名称匹配并呈现内置全量谱：《捣衣》！`);
        } else {
          previewHint.innerHTML = `已选择 <b>${file.name}</b> (${(file.size / 1024).toFixed(0)} KB)。<br>请在终端运行 <code>python transcribe_sheet.py ${file.name}</code> 进行多模态结构化转录，完成后点击上方【⬆ 导入谱文件】载入。`;
          this.updateDockStatus('normal', `已接收新谱照 ${file.name}。请使用本地转录脚本提取 JSON 后导入。`);
        }
      }
    });
  }

  loadScore(songKey) {
    this.stopSimulation();
    this.currentSongKey = songKey;
    this.score = SCORES_LIBRARY[this.currentSongKey] || SCORES_LIBRARY['daoyi'];
    this.engine = new ScoreEngine(this.score, this.synth);
    if (this.calibratedFreqs) {
      this.engine.recalibrate(this.calibratedFreqs);
    }
    this.attachEngineCallbacks();
    this.updateHeaderMeta();
    this.renderScore();
    const jsonEditor = document.getElementById('score-json-editor');
    if (jsonEditor) jsonEditor.value = JSON.stringify(this.score, null, 2);
    const selector = document.getElementById('song-selector');
    if (selector && selector.value !== songKey) selector.value = songKey;
    this.updateDockStatus('normal', `已载入曲目：《${this.score.title}》 (${this.score.key}) · 共 ${this.score.measures.length} 小节`);
  }

  handleAudioFrame(frame) {
    if (this.isTunerOpen && this.isTunerMicListening) {
      this.handleTunerAudioFrame(frame);
      return;
    }
    this.engine.processAudioFrame(frame);
  }

  async toggleAutoSimulation() {
    if (this.isSimulating) {
      this.stopSimulation();
      return;
    }

    await this.synth.resume();
    this.clearErrorBadges();
    this.isSimulating = true;
    const btn = document.getElementById('btn-auto-simulate');
    btn.textContent = '⏹ 停止模拟演奏';
    btn.classList.add('btn-primary');

    let startIdx = 0;
    if (this.isABLoopActive) {
      const loopStartNote = this.engine.flatNotes.find(fn => fn.barNumber === this.abStartBar);
      if (loopStartNote) startIdx = loopStartNote.globalIndex;
    }
    this.engine.setCursor(startIdx);

    let noteIdx = startIdx;
    const flatNotes = this.engine.flatNotes;

    const playNext = () => {
      if (!this.isSimulating) return;

      if (this.isABLoopActive) {
        const curNote = flatNotes[noteIdx];
        if (!curNote || curNote.barNumber > this.abEndBar) {
          noteIdx = startIdx;
        }
      } else if (noteIdx >= flatNotes.length) {
        this.stopSimulation();
        this.updateDockStatus('normal', '🎉 模拟演奏完毕！光标全程跟进成功！');
        document.getElementById('review-modal').classList.add('open');
        return;
      }

      const note = flatNotes[noteIdx];

      this.synth.pluck(note.targetFreq, 1.2, note.isHarmonic);

      this.engine.processAudioFrame({
        frequency: note.targetFreq,
        rms: 0.1,
        isSilent: false,
        isOnset: !note.isGlide,
        isStableGlide: note.isGlide,
        timestamp: performance.now()
      });

      noteIdx++;

      // ========================================================
      // 真实古琴乐理节拍计算引擎：告别机械节拍器，注入呼吸与韵味
      // ========================================================
      // 1. 基准速度 BPM 换算 (优先匹配小节级动态速度，支持前段散起慢板、后段快板滚拂)
      let bpm = 66;
      const measureData = this.score.measures.find(m => m.barNumber === note.barNumber);
      if (measureData && measureData.tempo) {
        const m = measureData.tempo.match(/(\d+)/);
        if (m) bpm = parseInt(m[1], 10);
      } else if (this.score && this.score.tempo) {
        const m = this.score.tempo.match(/(\d+)/);
        if (m) bpm = parseInt(m[1], 10);
      }
      const quarterBeatMs = (60 / bpm) * 1000;

      // 2. 音符基本时值系数 (减时线与附点)
      // underline: 0 = 四分音符(1拍), 1 = 八分音符(0.5拍), 2 = 十六分音符(0.25拍)
      let beatFactor = 1.0;
      if (note.underline === 1) beatFactor = 0.5;
      else if (note.underline === 2) beatFactor = 0.25;

      // 附点音符增加 50% 时值
      if (note.hasDot) beatFactor *= 1.5;

      // 3. 延音增时横线 (dashes: 如 1 — — — 全音符累计 4 拍)
      const dashes = note.dashes || 0;
      let delay = (beatFactor + dashes) * quarterBeatMs;

      // 4. 滑音走手音 (Glide) 特殊时值过渡
      if (note.isGlide) {
        delay = Math.max(350, delay * 0.75);
      }

      // 5. 古琴弹性速度与句读呼吸 (Rubato Breathing)
      // 遇到小节线末尾或句尾的长音，自然融入 120-180ms 余韵呼吸空隙，呈现古琴活态美感
      const isLastNoteInBar = (noteIdx >= flatNotes.length) || (flatNotes[noteIdx].barNumber !== note.barNumber);
      if (isLastNoteInBar && (dashes > 0 || note.hasDot)) {
        delay += 160;
      }

      this.simulationTimer = setTimeout(playNext, delay);
    };

    playNext();
  }

  stopSimulation() {
    this.isSimulating = false;
    clearTimeout(this.simulationTimer);
    const btn = document.getElementById('btn-auto-simulate');
    btn.textContent = '▶ 电脑模拟奏谱';
  }

  async simulateWrongNoteOnly() {
    await this.synth.resume();
    const wrongFreq = 512.4;
    this.synth.pluck(wrongFreq, 0.9);

    this.engine.processAudioFrame({
      frequency: wrongFreq,
      rms: 0.1,
      isSilent: false,
      isOnset: true,
      isStableGlide: false,
      timestamp: performance.now()
    });
  }

  simulateLongSilence() {
    this.updateDockStatus('warn', '模拟停顿中... 请观察 3 秒后光标是否平滑倒回句首');
    const start = performance.now();

    const interval = setInterval(() => {
      const now = performance.now();
      const elapsed = now - start;

      this.engine.processAudioFrame({
        frequency: -1,
        rms: 0.005,
        isSilent: true,
        isOnset: false,
        isStableGlide: false,
        timestamp: now
      });

      if (elapsed > 3300) {
        clearInterval(interval);
      }
    }, 100);
  }

  async toggleMicrophone() {
    const btn = document.getElementById('btn-toggle-mic');
    if (this.isMicActive) {
      this.detector.stop();
      this.isMicActive = false;
      btn.textContent = '🎙 开启麦克风';
      btn.classList.remove('btn-active-mic');
      this.updateDockStatus('normal', '麦克风已停止');
    } else {
      try {
        await this.detector.startMic();
        this.isMicActive = true;
        btn.textContent = '🔴 正在麦克风听音中';
        btn.classList.add('btn-active-mic');
        this.updateDockStatus('normal', '麦克风已就绪，请在琴上弹奏...');
      } catch (err) {
        alert('无法启动麦克风，请检查浏览器权限：' + err.message);
      }
    }
  }

  initTuner() {
    const tunerModal = document.getElementById('tuner-modal');
    const btnOpenTuner = document.getElementById('btn-open-tuner');
    const btnCloseTuner = document.getElementById('btn-close-tuner');
    const btnTunerMic = document.getElementById('btn-tuner-listen-mic');
    const btnApplyTuning = document.getElementById('btn-apply-tuning-calibration');
    const btnResetTuning = document.getElementById('btn-reset-tuning-calibration');

    // 读取本地保存的琴弦校准记录
    const saved = localStorage.getItem('guqin_calibrated_tuning');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length === 7) {
          this.calibratedFreqs = [...parsed];
          this.synth.setCustomOpenFrequencies(this.calibratedFreqs);
          this.engine.recalibrate(this.calibratedFreqs);
        }
      } catch (e) {}
    }

    if (btnOpenTuner) {
      btnOpenTuner.addEventListener('click', () => this.openTuner());
    }
    if (btnCloseTuner) {
      btnCloseTuner.addEventListener('click', () => this.closeTuner());
    }
    if (btnTunerMic) {
      btnTunerMic.addEventListener('click', () => this.toggleTunerMic());
    }

    if (btnApplyTuning) {
      btnApplyTuning.addEventListener('click', () => {
        if (!this.calibratedFreqs) {
          const defaultList = (STANDARD_TUNINGS[this.score.key] || STANDARD_TUNINGS["1 = ♭B"]).map(s => s.freq);
          this.calibratedFreqs = [...defaultList];
        }
        this.synth.setCustomOpenFrequencies(this.calibratedFreqs);
        this.engine.recalibrate(this.calibratedFreqs);
        localStorage.setItem('guqin_calibrated_tuning', JSON.stringify(this.calibratedFreqs));
        this.closeTuner();
        this.updateDockStatus('normal', '🎉 琴弦频率校准已成功应用到乐谱！全曲徽位与按音已按纯律完成智能修音！');
      });
    }

    if (btnResetTuning) {
      btnResetTuning.addEventListener('click', () => {
        this.calibratedFreqs = null;
        localStorage.removeItem('guqin_calibrated_tuning');
        this.synth.setCustomOpenFrequencies(null);
        this.engine.recalibrate(null);
        this.renderTunerStrings();
        this.updateDockStatus('normal', '已恢复古琴标准定弦音律');
      });
    }

    // 单音指法弹窗绑定
    const notePopoverModal = document.getElementById('note-popover-modal');
    const btnClosePopover = document.getElementById('btn-close-note-popover');
    const btnPopoverConfirm = document.getElementById('btn-popover-close');
    const btnPopoverPlay = document.getElementById('btn-popover-play-sample');

    if (btnClosePopover) {
      btnClosePopover.addEventListener('click', () => notePopoverModal.classList.remove('open'));
    }
    if (btnPopoverConfirm) {
      btnPopoverConfirm.addEventListener('click', () => notePopoverModal.classList.remove('open'));
    }
    if (btnPopoverPlay) {
      btnPopoverPlay.addEventListener('click', () => {
        if (this.popoverTargetNote) {
          this.synth.pluck(this.popoverTargetNote.targetFreq, 2.0, this.popoverTargetNote.isHarmonic);
        }
      });
    }
  }

  openTuner() {
    this.isTunerOpen = true;
    const modal = document.getElementById('tuner-modal');
    if (modal) modal.classList.add('open');
    const keyBadge = document.getElementById('tuner-score-key');
    if (keyBadge) {
      keyBadge.textContent = `当前曲谱：${this.score.key} (${this.score.tuning || '标准定弦'})`;
    }
    this.renderTunerStrings();
  }

  closeTuner() {
    this.isTunerOpen = false;
    const modal = document.getElementById('tuner-modal');
    if (modal) modal.classList.remove('open');
    if (this.isTunerMicListening) {
      this.toggleTunerMic();
    }
  }

  renderTunerStrings() {
    const grid = document.getElementById('tuner-strings-grid');
    if (!grid) return;
    grid.innerHTML = '';
    const stringsData = STANDARD_TUNINGS[this.score.key] || STANDARD_TUNINGS["1 = ♭B"];
    const freqs = this.calibratedFreqs || stringsData.map(s => s.freq);

    stringsData.forEach((item, idx) => {
      const card = document.createElement('div');
      card.className = 'string-card';
      card.id = `string-card-${idx}`;
      const curF = freqs[idx] || item.freq;
      const isCalibrated = this.calibratedFreqs && Math.abs(this.calibratedFreqs[idx] - item.freq) > 0.1;

      card.innerHTML = `
        <div class="string-title">${item.name}</div>
        <div class="string-note-name">${item.noteName}</div>
        <div class="string-pitch-badge">${item.pitch}${item.octave > 0 ? '̇' : (item.octave < 0 ? '̣' : '')}</div>
        <div class="string-freq-label" id="string-freq-${idx}">${curF.toFixed(1)}Hz</div>
        ${isCalibrated ? `<span class="string-diff-badge perfect">已校准</span>` : ''}
      `;

      card.addEventListener('click', () => {
        this.synth.pluck(curF, 2.5, false);
        this.highlightTunerString(idx, 0, curF);
        const feedback = document.getElementById('tuner-meter-feedback');
        if (feedback) feedback.innerHTML = `示范发声：${item.name} (${item.noteName}) · ${curF.toFixed(1)} Hz`;
      });

      grid.appendChild(card);
    });
  }

  highlightTunerString(idx, centsDiff, heardFreq) {
    document.querySelectorAll('.string-card').forEach((c, i) => {
      c.classList.toggle('active', i === idx);
      if (i === idx && Math.abs(centsDiff) <= 5) {
        c.classList.add('in-tune');
      } else if (i === idx) {
        c.classList.remove('in-tune');
      }
    });

    const needle = document.getElementById('tuner-dial-needle');
    const feedback = document.getElementById('tuner-meter-feedback');
    const stringsData = STANDARD_TUNINGS[this.score.key] || STANDARD_TUNINGS["1 = ♭B"];
    const strName = stringsData[idx] ? stringsData[idx].name : '';
    const noteName = stringsData[idx] ? stringsData[idx].noteName : '';

    if (needle) {
      const pct = Math.max(0, Math.min(100, 50 + (centsDiff / 30) * 50));
      needle.style.left = `${pct}%`;
    }

    if (feedback) {
      if (Math.abs(centsDiff) <= 5) {
        if (needle) needle.style.backgroundColor = '#2e7d32';
        feedback.innerHTML = `<span style="color:#2e7d32; font-weight:bold;">✓ ${strName} (${noteName}) 音准极佳！(${centsDiff >= 0 ? '+' : ''}${Math.round(centsDiff)} 音分)</span>`;
      } else if (centsDiff < 0) {
        if (needle) needle.style.backgroundColor = '#d32f2f';
        feedback.innerHTML = `<span style="color:#d32f2f;">${strName} (${noteName}) 偏低 ${Math.round(Math.abs(centsDiff))} 音分 (请旋紧琴轸/调高)</span>`;
      } else {
        if (needle) needle.style.backgroundColor = '#e65100';
        feedback.innerHTML = `<span style="color:#e65100;">${strName} (${noteName}) 偏高 ${Math.round(centsDiff)} 音分 (请放松琴轸/调低)</span>`;
      }
    }

    if (!this.calibratedFreqs) {
      this.calibratedFreqs = stringsData.map(s => s.freq);
    }
    this.calibratedFreqs[idx] = parseFloat(heardFreq.toFixed(1));
    const freqEl = document.getElementById(`string-freq-${idx}`);
    if (freqEl) freqEl.textContent = `${heardFreq.toFixed(1)}Hz`;
  }

  handleTunerAudioFrame(frame) {
    if (frame.isSilent || frame.frequency <= 40) return;

    const stringsData = STANDARD_TUNINGS[this.score.key] || STANDARD_TUNINGS["1 = ♭B"];
    const openFreqs = this.calibratedFreqs || stringsData.map(s => s.freq);

    let closestIdx = -1;
    let minCentsDiff = 9999;

    stringsData.forEach((strData, idx) => {
      const targetF = openFreqs[idx] || strData.freq;
      const cents = 1200 * Math.log2(frame.frequency / targetF);
      if (Math.abs(cents) < Math.abs(minCentsDiff)) {
        minCentsDiff = cents;
        closestIdx = idx;
      }
    });

    if (closestIdx !== -1 && Math.abs(minCentsDiff) <= 120) {
      this.highlightTunerString(closestIdx, minCentsDiff, frame.frequency);
    }
  }

  async toggleTunerMic() {
    const btn = document.getElementById('btn-tuner-listen-mic');
    if (!btn) return;
    if (this.isTunerMicListening) {
      this.isTunerMicListening = false;
      btn.textContent = '🎙 开启校音麦克风';
      btn.classList.remove('btn-primary');
      if (!this.isMicActive) {
        this.detector.stop();
      }
    } else {
      try {
        if (!this.isMicActive) {
          await this.detector.startMic();
        }
        this.isTunerMicListening = true;
        btn.textContent = '🔴 正在麦克风校音中...';
        btn.classList.add('btn-primary');
        const feedback = document.getElementById('tuner-meter-feedback');
        if (feedback) feedback.textContent = '请弹响任意空弦，系统将自动识别并指示音准...';
      } catch (e) {
        alert('无法启动麦克风校音：' + e.message);
      }
    }
  }

  showNotePopover(note, flatNote) {
    this.popoverTargetNote = flatNote;
    const modal = document.getElementById('note-popover-modal');
    const title = document.getElementById('popover-title');
    const content = document.getElementById('popover-content');
    if (!modal || !title || !content) return;

    title.textContent = `第 ${note.barNumber} 小节 · 音符校对 (修音)`;

    let typeStr = "按音 (左手按徽取音)";
    if (note.isHarmonic) typeStr = "泛音 (浮点徽位，轻击出音)";
    if (note.isGlide) typeStr = "走手音 (注/绰/上/下 滑动延音)";
    if (note.finger && note.finger.includes('散')) typeStr = "散音 (空弦原音)";

    let fingeringDesc = "传统减字谱指法标记";
    if (note.finger) {
      if (note.finger.startsWith('名')) fingeringDesc = "左手名指按徽位，配合右手弹拨";
      else if (note.finger.startsWith('大')) fingeringDesc = "左手大指按徽位，配合右手弹拨";
      else if (note.finger.startsWith('食')) fingeringDesc = "左手食指按徽位，配合右手弹拨";
      else if (note.finger.startsWith('中')) fingeringDesc = "左手中指按徽位，配合右手弹拨";
      else if (note.finger.startsWith('散')) fingeringDesc = "右手空弦击弦，琴音苍劲古朴";
      else if (note.finger.startsWith('勾')) fingeringDesc = "右手中指向身内勾弦";
      else if (note.finger.startsWith('挑')) fingeringDesc = "右手食指向外挑弦";
      else if (note.finger.startsWith('抹')) fingeringDesc = "右手食指向内抹弦";
      else if (note.finger.startsWith('剔')) fingeringDesc = "右手中指向外剔弦";
    }

    content.innerHTML = `
      <div style="background: rgba(0,0,0,0.03); padding: 10px; border-radius: 6px; margin-bottom: 10px;">
        <div style="display:flex; justify-content:space-between; margin-bottom: 4px;">
          <span>简谱音级：<b>${note.pitch}</b> ${note.octave > 0 ? '(高八度)' : (note.octave < 0 ? '(低八度)' : '')}</span>
          <span style="color:#2e7d32; font-weight:bold;">${typeStr}</span>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom: 4px;">
          <span>减字指法：<b style="font-size:15px; font-family:'KaiTi',serif;">${note.finger || '—'}</b></span>
          <span style="font-family:monospace; color:#555;">${flatNote.targetFreq.toFixed(1)} Hz</span>
        </div>
      </div>
      <p style="margin:0 0 6px 0; color:#444;">📖 <b>指法释义</b>：${fingeringDesc}</p>
      <p style="margin:0; font-size:12px; color:#777;">
        💡 <b>修音说明</b>：已采用徽位纯律物理公式精准校准。可点击下方【试听示范音】核对音准与韵味。
      </p>
    `;

    // 匹配并展示原谱高清切片 (翻正与去噪对照)
    let sliceImgPath = null;
    const bar = note.barNumber;
    if (this.currentSongKey === 'daoyi') {
      if (bar <= 4) sliceImgPath = 'slices_daoyi_p6/IMG_0961_line_1.jpg';
      else if (bar <= 8) sliceImgPath = 'slices_daoyi_p6/IMG_0961_line_2.jpg';
      else if (bar <= 12) sliceImgPath = 'slices_daoyi_p6/IMG_0961_line_3.jpg';
      else if (bar <= 16) sliceImgPath = 'slices_daoyi_p7/IMG_0962_line_1.jpg';
      else sliceImgPath = 'slices_daoyi_p7/IMG_0962_line_2.jpg';
    } else if (this.currentSongKey === 'chunfeng') {
      if (bar <= 4) sliceImgPath = 'slices_chunfeng/IMG_0963_line_1.jpg';
      else if (bar <= 7) sliceImgPath = 'slices_chunfeng/IMG_0963_line_2.jpg';
      else if (bar <= 10) sliceImgPath = 'slices_chunfeng/IMG_0963_line_3.jpg';
      else if (bar <= 14) sliceImgPath = 'slices_chunfeng/IMG_0963_line_4.jpg';
      else if (bar <= 19) sliceImgPath = 'slices_chunfeng/IMG_0963_line_5.jpg';
      else sliceImgPath = 'slices_chunfeng/IMG_0963_line_6.jpg';
    }

    if (sliceImgPath) {
      content.innerHTML += `
        <div style="margin-top: 10px; border-top: 1px dashed #dcd4c3; padding-top: 8px;">
          <div style="font-size: 11px; font-weight: bold; color: #555; margin-bottom: 4px;">📷 原谱印迹条带 (翻正去噪高清切片):</div>
          <div style="overflow: hidden; border-radius: 4px; border: 1px solid #dcd4c3; max-height: 90px; background: #fff;">
            <img src="${sliceImgPath}" style="width: 100%; display: block; object-fit: cover;" alt="原谱切片对照">
          </div>
        </div>
      `;
    }

    modal.classList.add('open');
  }

  updateDockStatus(type, msg) {
    this.statusText.textContent = msg;
    if (type === 'normal') this.statusDot.className = 'status-indicator-dot dot-green';
    else if (type === 'warn') this.statusDot.className = 'status-indicator-dot dot-amber';
    else if (type === 'error') this.statusDot.className = 'status-indicator-dot dot-red';
  }
}

window.addEventListener('DOMContentLoaded', () => {
  new GuqinApp();
});
