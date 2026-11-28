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
    .agents/               生成跟谱页的 skill（已纳入版本管理）
      skills/guqin-score-page/
        SKILL.md
        scripts/guqin_page.py
        templates/page.template.html
    模板/                  《青城山下白素贞》的书页原图、JSON spec、页面变体 HTML
    脚本/                  过程脚本
      sonnet/              多模态转录工具（非页面生成流程，独立保留）
    文档/                  方案与说明文档
```

## 跟谱页 skill

需要新做或重做某首曲的跟谱页时，先阅读并遵循：

`program/.agents/skills/guqin-score-page/SKILL.md`

用它配套的 `scripts/guqin_page.py` 和 `templates/page.template.html`。不要绕过这个 skill 另起一套生成流程，除非用户明确要求。

## 现有跟谱页

《青城山下白素贞》（`模板/`）：

- `页面变体-Gemini-4-Neon-对谱精简版.html` —— **基线**（issue #32 的 Neon 版式，PR #44 收敛为对谱精简版；唯一交付页面）
- `agron模板 · 青城山下白素贞.html` —— 校验脚本的参照页面（非交付物，但**不可删**）

> 含整曲模拟弹奏的旧 Neon 变体及早期对照实验已删除；截图与实测数据保留在
> issue #32 上可查。后续新曲统一由 `page.template.html` 生成，不再复制 HTML 变体。

预览：用系统浏览器直接打开对应 HTML（双击或把文件拖进浏览器即可）。

## 中间产物与过程脚本

`模板/baisuzhen-spec.json` 记录每排的裁切框 `box`、逐音的 `x`（左边缘百分比）、
`w`（宽度百分比）、`d`（时值）、`oct_shift`（谱面八度）等规格。
想微调某个音的位置或宽度，改 spec 后重跑 `guqin_page.py build` 即可重新生成 HTML。

`模板/` 的 build 在内存中完成重建，不产生过程切图。

`脚本/agron_my/` 的早期生成脚本已删除 —— 当前产物一律由 skill 生成，
不要绕过 skill 另起一套生成流程（除非用户明确要求）。

`脚本/sonnet/` 是多模态转录工具（拍照转谱面），与页面生成流程无关，独立保留。

改脚本或重新跑之前，先核对路径是否还指向现在的位置。

## 文档

`文档/` 下有产品方案文档、竞品功能清单、标注任务的底稿与交接索引。
关于模块化页面和本地服务器的旧方案说明已随 `index.html` 一并删除；
目录和实现原则以本文件和当前文件夹为准。

## 工作约定

- 文本文件使用 UTF-8。曲目文件夹和 HTML 文件名含中文，操作时用字面路径，不要改名除非用户要求。
- 不要提交 `.gitignore` 里的内容（`program/模板/out/`、Python 缓存等）。`AGENTS.md` 和 `CLAUDE.md` 在仓库根目录，不在 ignore 范围内；小改动先留本地，等用户说再提交。
- `program/.agents/` 下的 skill 已纳入版本管理，模板与 HTML 产物必须保持版本对应：改了 `page.template.html` 或 `guqin_page.py`，要重跑 `build` 重新生成 HTML 并一起提交，否则会出现模板与产物脱节。
- 不要直接推送到 `main`。功能在分支上改；需要提交到 GitHub 时开正式 Pull Request（不要用 draft），由用户手动添加 Copilot 作为 reviewer，再 Squash and merge。
- 提交前先确认当前分支：`git branch --show-current`。本仓库是个人账户下的私有仓库，`main` 没有分支保护（需 GitHub Pro 才有），直接 push 不会被 GitHub 拦截，但会跳过 PR、跳过 Copilot review，也不留下变更说明。
- 小改动可以先留在本地，不要急着 commit 或开 PR，等用户说再提交。
- 不要安装未要求的扩展、不要改用户未点名的无关文件。