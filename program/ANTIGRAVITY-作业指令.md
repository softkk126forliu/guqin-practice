# Antigravity 作业指令：古琴谱八度标注

> 这是**操作手册**，知识细节在 `交接-标注任务.md`（遇到具体疑问再查）。
> 本文件只讲「下一步做什么、怎么做、怎么交」。

## 0. 你的工作目录

```
D:/Works/古琴陪练/program
```

⚠️ **必须在 `program/` 下**。设成仓库根会读不到根目录的 `AGENTS.md`（踩过这个坑）。

## 1. 背景（一句话）

古琴谱的绝对音高 = **弦的空弦音高 + 徽位音程**。现在页面靠猜八度（`targetCenter` + 上一音平滑），
错得很厉害。你的任务是：**把谱面的下加线读出来写进 spec，让八度变成确定的**。

## 2. 四条硬规矩

| # | 规矩 | 为什么 |
|---|---|---|
| 1 | **不要用录音一致率评判八度** | `aud_pitch` 取的是同音级**最强**的分音。空弦低音的基频弱、分音强，它必然取到泛音 → 会得出「页面偏低八度」的反向结论。判八度只能用 `aud_base`（基频）|
| 2 | **读不准就标 `null`，不要猜** | 标 `null` 会进入「待人工确认」清单；猜错了会变成确定性的错误。宁可留白 |
| 3 | **每排做完立刻跑验证脚本** | 数字不对就停下来问人，别攒到最后 |
| 4 | **不要直推 main** | 走分支 + PR。仓库 `AGENTS.md` 有此约定 |

## 3. 步骤

### 步骤 1：切分支（从最新 main）

```bash
cd D:/Works/古琴陪练
git fetch origin
git checkout -b feat/annotate-baisuzhen-r5-r6 origin/main
```

分支名规范：`feat/annotate-<曲名简称>-<排号范围>`

### 步骤 2：生成带标号的排图

```bash
cd program
python .agents/skills/guqin-score-page/scripts/crop_rows.py \
  --spec "模板/baisuzhen-spec.json" --out "D:/tmp/gq_rows_bs"
```

产物每排两张：
- `row_N.png` —— 整排（简谱 + 减字谱），2800px
- `row_N_marks.png` —— **简谱区 + 红色音序号 + 蓝色 spec 音级**（标注时用这张）

### 步骤 3：读谱

**必须 ≥3 倍放大**，否则会把叠写的「3/4」读成「4/5」（踩过，导致整排错位）：

```python
from PIL import Image
im = Image.open('D:/tmp/gq_rows_bs/row_5_marks.png')
im.crop((1150, 0, 2200, im.height)).resize((1050*3, im.height*3), Image.LANCZOS).save('D:/tmp/zoom.png')
```

判读要点：

| 看什么 | 含义 |
|---|---|
| 红色数字 | 音序号，对应 spec 里该排 `notes[]` 的下标 |
| 蓝色数字 | spec 的音级，**用它交叉验证你的读数** |
| 紧贴数字下方的**直线** | **下加线**，条数 = 减八度数 |
| 数字上方的 `○○` | 泛音（青城用两个圈）|

⚠️ 三个坑：
1. 相邻数字的下加线**连成一片** —— 按「每个数字下方各有几条」理解，不是数平行线
2. **扫描拖影**会伪装成第二条线 —— 真线笔直平行等宽，拖影有弯曲 → 只算一条
3. 附点（`5.`）是时值记号，不是八度

### 步骤 4：写进 spec

字段写在对应 note 上：

```json
{"p": "6", "oct_shift": -1, "harm": false, "x": 12.5, "w": 3.0, "d": 1}
```

- `oct_shift`：`0` = 中音区 `[48,59]`；`-1` = 低音区 `[36,47]`
- **只用于非泛音音** —— 泛音音高由徽位决定，下加线不适用
- 读不准 → 写 `"oct_shift": null`（显式 null，进待确认清单）

**只改 `oct_shift` / `dot` 字段，不要动 `p` / `x` / `w` / `d` / `harm`**（动了就是抄错谱，要返工）。

### 步骤 5：验证（必须全绿）

```bash
cd program

# ① 重建产物（改 spec 后必须重跑）
cd 模板 && python ../.agents/skills/guqin-score-page/scripts/guqin_page.py build baisuzhen-spec.json && cd ..
# 春风同理：cd 春风 && python ../.agents/skills/guqin-score-page/scripts/guqin_page.py build chunfeng-p1-spec.json && cd ..

# ② 模板 ↔ 检查脚本一致性（必须「完全一致」）
python .agents/skills/guqin-audio-check/scripts/check_sync.py \
  --page "模板/agron模板 · 青城山下白素贞.html"

# ③ 标注质量校验（新增工具，评审的客观依据）
python .agents/skills/guqin-audio-check/scripts/verify_annotations.py \
  --spec "模板/baisuzhen-spec.json" \
  --page "模板/agron模板 · 青城山下白素贞.html"
```

**验收标准**：

| 检查 | 要求 |
|---|---|
| ② `check_sync` | 必须「完全一致」|
| ③ ③ 内部一致性 | 必须「不符 0 个」|
| ③ ② 字段合法性 | 必须「全部合法」|
| ③ ① 覆盖率 | 本次要标的排「未标注」应为 0 |
| 春风复测 | 若改了春风，八度一致数**不得下降**（当前 45/96，音级错 0）|

### 步骤 6：提交

⚠️ **在 Antigravity 里不要点带编辑器的 commit 按钮**（会弹窗卡住）。用命令行：

```bash
cd D:/Works/古琴陪练
git add program/模板/baisuzhen-spec.json program/模板/*.html
git commit -m "标注：青城排 5-6 八度下加线（oct_shift）"
git push -u origin feat/annotate-baisuzhen-r5-r6
```

提交后到 GitHub 上开 PR：**base = `main`**，head = 你的分支。

## 4. 交作业时给用户的汇报（必须包含这几项）

```markdown
## 标注完成：青城排 5-6

### 读数
| 音 | 谱面数字 | 下加线条数 | oct_shift | 页面发声 |
|---|---|---|---|---|
| 5-1 | 6 | 1 条 | -1 | G2 |
| ... | | | | |

### 验证
- check_sync：完全一致（157 音）
- verify_annotations：内部一致 26/26，合法性全通过
- 覆盖率：排 5 未标注 0，排 6 未标注 0

### 待人工确认
（若有显式 null 的音，列出来）
```

**表格里的「页面发声」自己跑一遍模板算法算出来**，别只写 oct_shift ——
评审要靠这列数字交叉验证。

## 5. 从哪排开始

| 顺序 | 排 | 音数 | 泛音 | 理由 |
|---|---|---|---|---|
| 1 | **排 3** | 12 | 0 | 已跑通样板，照着做 |
| 2 | 排 8 | 14 | 0 | 纯散按 |
| 3 | 排 9 | 7 | 0 | 音少，快 |
| 4 | 排 2、5、6 | 11+6+8 | 少量 | — |
| 5 | 排 10-14 | 12+9+11+11+11 | 混合 | — |
| 6 | 排 1、15 | 18+19 | 全泛音 | ⚠️ 泛音排，oct_shift 用不上，做不了 |

**建议一次做 2-3 排就提交一次**，别攒着。

## 6. 什么时候该停下来问人

- 同一排跑了两遍读数不一致
- 下加线条数是 2 条或更多（古琴上不合法，疑似拖影或误读）
- `check_sync` 报不一致（说明模板和检查脚本不同步，不是你的问题，但要报）
- 想知道某个音到底是空弦还是按音（需要减字谱徽位 → 交给人）
