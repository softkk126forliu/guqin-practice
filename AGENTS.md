# 古琴陪练 · Agent 说明

本文件放在仓库根目录，给本项目的编码 Agent 用（Antigravity、Cursor 等）。Claude Code 请同时阅读同目录的 `CLAUDE.md`。

仓库根目录是 `古琴陪练/`（Git 根）。分工如下：

- `program/`：HTML 网页版陪练程序（当前的单文件跟谱页和相关材料）。
- 旁边的 `DeepGuqin-Antigravity-Project`（DeepGuqin）：计划中的 iOS 和 Android 版本，是另一个独立项目。

两边不要混用代码或依赖；在本仓库只改 HTML 网页版，不要把移动端实现写进 `program/`。

## 项目目标

做古琴减字谱的跟谱陪练：弹到哪里，光标跟到哪里（听音跟谱）。

## 单页面第一期功能范围

当前只做 `program/` 里的单文件 HTML 跟谱页。DeepGuqin 是后续完整产品实践，本阶段不把曲库、拍照识谱、评测报告、调音台或移动端实现写进本仓库。

本阶段的主要目的：让光标按曲子的节奏走，弹琴的人跟得上；谱面要清楚。先把节奏做对、演奏能流畅跟上。音准判断（弹的音是否与原谱一致）难度较大，放到后面再做细。后期可以同时做音准判断，以及 `program` 单页面与 DeepGuqin 产品两套程序的界面。

第一期锁定的核心功能：

- 书页减字谱展示（谱面清楚、易读）
- 听音跟谱（光标按节奏走，弹到哪里跟到哪里，让演奏者跟得上）
- 模拟弹奏
- 速度调节
- 前后音 / 重来
- 沉浸模式
- 节拍器
- 听音灵敏度

可选项（不是第一期必须完成）：改时值、放大 / 增强 / 墨色 / 放大条、护眼暗色。

改现有页面时，以用户指定的那一个文件为准；未指定前不要合并或删除现有变体。

## 当前方案（必须遵守）

采用**单文件独立 HTML 页面**：CSS、JS、谱面切图都写进同一个 `.html`，用系统浏览器直接打开即可，不依赖本地服务器，也不拆成多文件模块。

已经放弃并删除的方案：原来的 `index.html` + 多个 JS/CSS/数据文件（ES module，必须用 `python -m http.server` 才能打开）。**不要再恢复或继续那套结构。**

用户会从现有独立页面里挑选一种实现路径。在用户明确指定之前：

- 不要擅自实现一套新的整体方案
- 不要合并或删除现有页面变体
- 改页面时只改用户点名的那一个文件

## 目录结构

```
古琴陪练/                   仓库根目录（本文件与 CLAUDE.md 在这里）
  AGENTS.md
  CLAUDE.md
  program/
    .agents/               生成跟谱页的 skill（整个目录目前 gitignore，只留本地）
      skills/guqin-score-page/
        SKILL.md
        scripts/guqin_page.py
        templates/page.template.html
    捣衣/                  《捣衣》的独立页面、书页照片、JSON spec、切片输出
    春风/                  《春风》的独立页面与书页照片
    脚本/                  过程脚本（切片清理、书页转谱）
    文档/                  方案与说明文档
```

## 跟谱页 skill

需要新做或重做某首曲的跟谱页时，先阅读并遵循：

`program/.agents/skills/guqin-score-page/SKILL.md`

用它配套的 `scripts/guqin_page.py` 和 `templates/page.template.html`。不要绕过这个 skill 另起一套生成流程，除非用户明确要求。

## 现有页面变体（尚未选定最终方案）

《捣衣》（`捣衣/`）：

- `古琴跟谱 · 捣衣.html`
- `古琴跟谱 · 捣衣_hydrogen4.html`
- `古琴跟谱 · 捣衣_hydrogen4_noskill.html`

《春风》（`春风/`）：

- `古琴跟谱 · 春风（书页照片）.html`
- `古琴跟谱 · 春风_hydrogen4_noskill.html`

预览：用系统浏览器直接打开对应 HTML（双击或把文件拖进浏览器即可）。

## 中间产物与过程脚本

`捣衣/` 下的 `out_daoyi/`、`out_daoyi_p7/`、`out_daoyi_final/` 以及 `daoyi-spec.json`、`daoyi-p6-spec.json`、`daoyi-p7-spec.json`，是生成跟谱页时的中间切图和规格说明。独立页面已经内嵌日常使用所需的切图和逻辑；只预览或改交互时，不必重新跑生成流程。这些 `out_*` 目录已 gitignore，只留在本地。

`脚本/` 里现有：

- `build_clean_crops.py`：从书页切片生成清理后的切图
- `transcribe_sheet.py`、`guqin_transcriber_v2.py`：从书页照片做转谱/识别，产出 JSON

文件整理进 `捣衣/`、`春风/`、`脚本/` 之后，脚本里的相对路径可能已经过时。改脚本或重新跑之前，先核对路径是否还指向现在的位置。

## 文档

`文档/` 中有方案文档和 `程序说明.md`。`程序说明.md` 写于删除 `index.html` 方案之前，其中关于模块化页面和本地服务器的部分已经过时；目录和实现原则以本文件和当前文件夹为准。

## 工作约定

- 文本文件使用 UTF-8。曲目文件夹和 HTML 文件名含中文，操作时用字面路径，不要改名除非用户要求。
- 不要提交 `.gitignore` 里的内容（包括 `program/.agents/`、各 `out_*` 等）。`AGENTS.md` 和 `CLAUDE.md` 在仓库根目录，不在 ignore 范围内；小改动先留本地，等用户说再提交。
- 不要直接推送到 `main`。功能在分支上改；需要提交到 GitHub 时开正式 Pull Request（不要用 draft），由用户手动添加 Copilot 作为 reviewer，再 Squash and merge。
- 小改动可以先留在本地，不要急着 commit 或开 PR，等用户说再提交。
- 不要安装未要求的扩展、不要改用户未点名的无关文件。