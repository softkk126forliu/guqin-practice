# 跟谱页音高与八度规划不准确（音频对照实测 43% 八度偏差）

> 本文档是 GitHub issue #10 的完整分析底稿。
> Issue: https://github.com/softkk126forliu/guqin-practice/issues/10
> 相关 PR: `feat/guqin-audio-check`（新增检查 skill 与示范素材）

## 问题

用 `guqin-audio-check` skill 对照《春风》跟谱页与示范录音实测，发现页面"模拟弹奏"发出的音高与录音存在系统性偏差：

| 指标 | 实测值 |
|---|---|
| 参与判定的音 | 97 个（第 1–6 排） |
| 音级一致（OK） | 71 |
| 可疑 | 17 |
| 不一致 | 9 |
| **八度不一致** | **32 / 74（有八度数据的音中占 43%）** |
| 调音偏差 | −32.2 cents（A4 ≈ 431.9 Hz） |
| 移调 | 0（与页面同调） |
| 时间倍率 | 0.93（录音比页面 bpm 慢约 7%） |

音级（pitch class）基本是对的，问题集中在**八度**。

## 根因定位

跟谱页的八度由 `page.template.html` 的 `MIDI[]` 规划算法决定（`program/.agents/skills/guqin-score-page/templates/page.template.html`）。已定位三个缺陷：

### 缺陷 1：泛音 HUD 与实际发声系统性差八度（确定性）

`page.template.html:735`
```javascript
const effMidi = isHarm ? Math.min(79, midi + 12) : midi;
```
合成器对泛音统一 `+12`，但 HUD（`page.template.html:604`）显示的是原始 `MIDI[i]`。

实测：**39 个泛音音中 39 个 `page_sound − page_hud == 12`（100%）**。
即泛音段 HUD 永远比实际发声低一个八度。这是纯代码缺陷，与 spec 无关。

### 缺陷 2：双音撮八度折叠

`page.template.html:573-576`
```javascript
let dd = (c.pcs[0] - c.pcs[k] + 12) % 12;
if (dd === 0) dd = 12;
ms.push(best.m - dd);
```
第二音固定按半音数距离放在第一音下方。遇到十度大撮（如 `6/3̣` = G3 + D2）时，
低音会被抬高一个八度（变成 G3 + D3）。

### 缺陷 3：散按音下限截断 + 贪心八度平滑

`page.template.html:558-562`
```javascript
let pv = 52;
const minM = c.harm ? 48 : 40;   // E2 = 40
```
- `minM = 40` 排除了古琴一弦 C2（36）、二弦 D2（38）
- `pv` 贪心平滑只依据"上一个音"猜八度，没有全局约束

实测偏差分布（页面发声 vs 录音同音级八度）：
- 排 4：简谱 `3` × 6 个连续音，页面 D5 / 录音 D4（页面**高**八度）
- 排 5、6：简谱 `6`、`7` 共 19 个音，页面 G3、A3 / 录音 G4、A4（页面**低**八度）
- 排 6 有一个音页面 G3 / 录音 G5（差两个八度）
- 排 1：简谱 `2`，页面 C4 / 录音 C5（页面低八度）

### 缺陷 4：spec 不携带高低音点信息（数据层根因）

`spec.json` 的 `p` 只存裸数字（如 `"3"`），不含简谱的高低音点（`·` / `:` / `.`）。
模板因此完全依赖 `pv` 贪心推断八度，无法知道原谱写的是 `3̇`（高音）还是 `3̣`（低音）。

**这一条是其它三条的根因**：只要 spec 补上高低音点，很多八度猜测就不需要猜了。

## 验收标准

- [ ] 泛音段 HUD 显示的音高与页面实际发声**一致**（消除 `midi + 12` 的显示差）
- [ ] 八度不一致率显著下降；剩余偏差须逐个在 issue 中说明原因（谱面版本差异 / 录音版本差异）
- [ ] 改动后重跑 `guqin_page.py build`，青城与春风两个页面产物同步更新
- [ ] 用 `audio_score_check.py` 复测，输出新的 OK / 可疑 / 不一致 统计
- [ ] "可疑"与"不一致"的音须用 `pitch_track.py` 人工复核后再下结论（见 skill 的两层检查要求）

## 候选方案（待对比后选定）

### 方案 A：spec 补高低音点（数据层）

在 `spec.json` 的音符上增加高低音点标记（如 `"p": "3̇"` 或独立的 `"dot"` 字段），
模板优先使用 spec 指定八度，推断只作兜底。

- 优点：从根上解决；`guqin-score-page` skill 已支持 `p` 兼容简谱字符串
- 代价：所有 spec 需重新标注；需确认 `guqin_page.py` 与 `make_cf_agron_my.py` 两条生成路径都能透传
- 风险：标注工作量大，且标注本身可能出错

### 方案 B：改进模板八度规划算法（逻辑层）

在 `MIDI[]` 规划中加入全局约束，替换当前的贪心平滑：
- 用整排/整曲的音高走向做动态规划，而非逐音独立贪心
- 按古琴实际音域与弦位关系约束双音撮的八度
- 放宽或修正 `minM`，允许一弦、二弦低音

- 优点：改动集中在一处，所有曲子受益；不用重录 spec
- 代价：算法复杂度上升；需要用本 issue 的 97 个音做回归验证不引入新的错八度
- 风险：可能过度拟合春风这一首

### 方案 C：只修 HUD 显示（表现层）

`page.template.html:604` 显示时加上与合成器一致的 `+12` 偏移。

- 优点：最小改动，立刻消除 39/39 的确定性缺陷
- 代价：只解决"显示"问题，实际发声的八度仍然偏高/偏低
- 定位：这是**必须做但远不够**的一项

### 方案 D：组合

先做 C（消除确定性缺陷），再在 A 与 B 之间选其一处理真正的八度规划问题。

## 相关文件

- `program/.agents/skills/guqin-score-page/templates/page.template.html` — 八度规划与合成器
  - `558-580`：MIDI[] 八度规划
  - `604`：HUD 显示
  - `735`：泛音 `+12`
- `program/.agents/skills/guqin-audio-check/` — 检查工具
  - `scripts/audio_score_check.py`：主程序
  - `scripts/pitch_track.py`：人工复核
- `program/春风/chunfeng-p1-spec.json` — 春风 spec
- `program/春风/古琴跟谱 · 春风_agron_my.html` — 春风跟谱页
- `program/春风/春风.pdf` — 琴谱 PDF（人工复核用）
- `program/春风/春风_最贴切示范_Chinese_Guqin_music_春风_古琴.mp3` — 示范录音

## 复现方式

```powershell
cd program
python .agents/skills/guqin-audio-check/scripts/audio_score_check.py `
  --page "春风/古琴跟谱 · 春风_agron_my.html" `
  --audio "春风/春风_最贴切示范_Chinese_Guqin_music_春风_古琴.mp3" `
  --end 120 --out <输出前缀>
```

预期复现结果：调音偏差约 −32 cents、移调 0、时间倍率约 0.93、
OK 71 / 可疑 17 / 不一致 9，八度不一致 32 个。

## 人工复核提示

「可疑」与「不一致」中有一部分是**假不一致**，复核时注意（详见 skill 第 4 节）：

- 泛音音色里另一个分音很强 → 期望音在持续帧稳定存在即算一致
- 低音撮（2+5、3+6）基频弱，靠 3 次/5 次泛音 → 看是否出现对应泛音
- 滑音弧线下的第二音没有新起音，音高是滑过去的 → 看持续帧是否停在期望音
- 页面音前多出的密拨弦是 PDF 上的倚音，页面按设计省略
- 同音快速反复（666）中某个音缺失不算发音错误

能下"真不一致"结论的条件：期望音在整个音的持续帧里都不出现，
录音里稳定出现的是另一个音级，且 PDF 上写的也是录音那个音
（说明 spec 抄错了），或 PDF 与页面一致但演奏者确实改了音（版本差异）。
