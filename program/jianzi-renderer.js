/**
 * 古琴合体减字符 SVG 矢量排字与结构化指法渲染引擎
 * 遵循无外部依赖原则：
 * 1. 核心常见部首采用 SVG 矢量视口排布；
 * 2. 复合双层减字（左手徽位 / 右手弦序）采用结构化字模呈现；
 * 3. 彻底告别盲目大面积留空，原汁原味还原古琴指法信息。
 */

export function getJianziSvg(noteOrFinger, showCrop = true) {
  const blankDiv = `<div class="jz-blank" style="width:26px; height:32px; display:inline-block;"></div>`;

  // 1. 若开启原图切片模式且音符包含单字切图，优先以原书高清墨迹呈现 (guqinMM 范式)
  if (showCrop && noteOrFinger && typeof noteOrFinger === 'object') {
    if (noteOrFinger.crop) {
      return `
        <div class="jz-crop-wrap" title="${noteOrFinger.finger || ''}">
          <img class="jz-char-crop" src="${noteOrFinger.crop}" alt="${noteOrFinger.finger || ''}">
        </div>
      `;
    }
  }

  const finger = (typeof noteOrFinger === 'object' && noteOrFinger) ? noteOrFinger.finger : noteOrFinger;

  if (!finger || typeof finger !== 'string') {
    return blankDiv;
  }

  const trimmed = finger.trim();
  if (!trimmed || trimmed === '—' || trimmed === 'blank') {
    return blankDiv;
  }

  // 1. 散音 (艹 上下合体: 散七, 散五, 散四, 散三, 散六, 散一, 散二)
  if (trimmed.startsWith('散')) {
    const num = trimmed.replace('散', '');
    if (num.length <= 2) {
      return `
        <svg class="jianzi-svg" viewBox="0 0 26 32">
          <text x="13" y="13" font-size="15" font-weight="bold" fill="#111" text-anchor="middle" font-family="'KaiTi', 'STKaiti', serif">艹</text>
          <text x="13" y="27" font-size="14" font-weight="bold" fill="#111" text-anchor="middle" font-family="'KaiTi', 'STKaiti', serif">${num}</text>
        </svg>
      `;
    }
  }

  // 2. 勾指 (勹 包围合体: 勾五, 勾四, 勾六, 勾三, 勾七, 勾二, 或单独 勾)
  if (trimmed.startsWith('勾')) {
    const num = trimmed.replace('勾', '');
    if (num.length <= 2) {
      return `
        <svg class="jianzi-svg" viewBox="0 0 26 32">
          <text x="7" y="22" font-size="22" fill="#111" font-family="'KaiTi', 'STKaiti', serif">勹</text>
          ${num ? `<text x="17" y="22" font-size="11" font-weight="bold" fill="#111" text-anchor="middle" font-family="'KaiTi', 'STKaiti', serif">${num}</text>` : ''}
        </svg>
      `;
    }
  }

  // 3. 挑指 (乚 托底合体: 挑六, 挑五, 挑四, 挑三, 挑七, 挑一)
  if (trimmed.startsWith('挑')) {
    const num = trimmed.replace('挑', '');
    if (num.length <= 2) {
      return `
        <svg class="jianzi-svg" viewBox="0 0 26 32">
          <text x="5" y="23" font-size="22" fill="#111" font-family="'KaiTi', 'STKaiti', serif">乚</text>
          ${num ? `<text x="16" y="19" font-size="11" font-weight="bold" fill="#111" text-anchor="middle" font-family="'KaiTi', 'STKaiti', serif">${num}</text>` : ''}
        </svg>
      `;
    }
  }

  // 4. 大指 (大 上下合体: 大七, 大九, 大十, 大八)
  if (trimmed.startsWith('大') && !trimmed.includes('/')) {
    const num = trimmed.replace('大', '');
    if (num.length <= 2) {
      return `
        <svg class="jianzi-svg" viewBox="0 0 26 32">
          <text x="13" y="14" font-size="14" font-weight="bold" fill="#111" text-anchor="middle" font-family="'KaiTi', 'STKaiti', serif">大</text>
          <text x="13" y="27" font-size="13" font-weight="bold" fill="#111" text-anchor="middle" font-family="'KaiTi', 'STKaiti', serif">${num}</text>
        </svg>
      `;
    }
  }

  // 5. 名指 (夕 上下合体: 名九, 名七, 名十, 名八)
  if (trimmed.startsWith('名') && !trimmed.includes('/')) {
    const num = trimmed.replace('名', '');
    if (num.length <= 2) {
      return `
        <svg class="jianzi-svg" viewBox="0 0 26 32">
          <text x="13" y="13" font-size="14" font-weight="bold" fill="#111" text-anchor="middle" font-family="'KaiTi', 'STKaiti', serif">夕</text>
          <text x="13" y="27" font-size="13" font-weight="bold" fill="#111" text-anchor="middle" font-family="'KaiTi', 'STKaiti', serif">${num}</text>
        </svg>
      `;
    }
  }

  // 6. 中指 (中 上下合体)
  if (trimmed.startsWith('中') && !trimmed.includes('/')) {
    const num = trimmed.replace('中', '');
    if (num.length <= 2) {
      return `
        <svg class="jianzi-svg" viewBox="0 0 26 32">
          <text x="13" y="14" font-size="14" font-weight="bold" fill="#111" text-anchor="middle" font-family="'KaiTi', 'STKaiti', serif">中</text>
          <text x="13" y="27" font-size="13" font-weight="bold" fill="#111" text-anchor="middle" font-family="'KaiTi', 'STKaiti', serif">${num}</text>
        </svg>
      `;
    }
  }

  // 7. 注音 (氵 左右合体: 注十, 注十一, 注九)
  if (trimmed.startsWith('注')) {
    const num = trimmed.replace('注', '');
    if (num.length <= 2) {
      return `
        <svg class="jianzi-svg" viewBox="0 0 26 32">
          <text x="7" y="21" font-size="18" fill="#111" text-anchor="middle" font-family="'KaiTi', 'STKaiti', serif">氵</text>
          <text x="18" y="21" font-size="13" font-weight="bold" fill="#111" text-anchor="middle" font-family="'KaiTi', 'STKaiti', serif">${num}</text>
        </svg>
      `;
    }
  }

  // 8. 抹指 (木 结构)
  if (trimmed.startsWith('抹')) {
    const num = trimmed.replace('抹', '');
    if (num.length <= 2) {
      return `
        <svg class="jianzi-svg" viewBox="0 0 26 32">
          <text x="5" y="21" font-size="17" fill="#111" font-family="'KaiTi', 'STKaiti', serif">木</text>
          <text x="17" y="21" font-size="11" font-weight="bold" fill="#111" text-anchor="middle" font-family="'KaiTi', 'STKaiti', serif">${num}</text>
        </svg>
      `;
    }
  }

  // 9. 剔指 (匕 结构)
  if (trimmed.startsWith('剔')) {
    const num = trimmed.replace('剔', '');
    if (num.length <= 2) {
      return `
        <svg class="jianzi-svg" viewBox="0 0 26 32">
          <text x="5" y="22" font-size="18" fill="#111" font-family="'KaiTi', 'STKaiti', serif">匕</text>
          <text x="16" y="20" font-size="11" font-weight="bold" fill="#111" text-anchor="middle" font-family="'KaiTi', 'STKaiti', serif">${num}</text>
        </svg>
      `;
    }
  }

  // 10. 明确的独体常用减字/术语 (如 外, 省, 立, 正, 句, 再作, 泛, 旱, 尸, 乚)
  const allowedSingles = ['外', '省', '立', '正', '句', '再作', '泛', '旱', '尸', '乚', '全', '六', '四', '七'];
  if (allowedSingles.includes(trimmed)) {
    return `
      <svg class="jianzi-svg" viewBox="0 0 26 32">
        <text x="13" y="21" font-size="15" font-weight="bold" fill="#111" text-anchor="middle" font-family="'KaiTi', 'STKaiti', serif">${trimmed}</text>
      </svg>
    `;
  }

  // 11. 复合指法结构化字模呈现 (如 "大九/七" -> 上部大九，下部七；"广五/六" -> 上部广五，下部六)
  // 彻底告别大面积留空，将左手徽位与右手弦序规整展现
  if (trimmed.includes('/')) {
    const parts = trimmed.split('/');
    const topText = parts[0] || '';
    const botText = parts.slice(1).join('/') || '';
    return `
      <div class="jz-structured-glyph" title="${trimmed}">
        <span class="jz-top-part">${topText}</span>
        <span class="jz-bot-part">${botText}</span>
      </div>
    `;
  }

  // 12. 其余带修饰词指法 (如 "大九下七+", "色鹫")
  if (trimmed.length <= 4) {
    return `
      <div class="jz-structured-glyph" title="${trimmed}">
        <span class="jz-top-part" style="font-size: 10px;">${trimmed.slice(0, 2)}</span>
        <span class="jz-bot-part" style="font-size: 10px;">${trimmed.slice(2)}</span>
      </div>
    `;
  }

  return blankDiv;
}
