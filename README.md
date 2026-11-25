# 古琴陪练

私有仓库：<https://github.com/softkk126forliu/guqin-practice>

## 这个项目是什么

琴韵 DeepGuqin —— 古琴跟谱软件，个人练琴用。

减字谱翻页找位置太难：练琴中途离开一会儿，回来常常找不到刚才弹到哪个音。本软件用麦克风听你弹奏，光标实时跟着走——你停，光标就停；回来一眼就知道停在哪个音。v1 只判断"弹到哪了"，不判断"弹得准不准"，音准判定留到 v2+。

- 形态：HTML 单页，浏览器可直接使用；外层套 Capacitor 得到 iOS / Android App
- 产品定位、原型与开发计划：见本地 `DeepGuqin-Antigravity-Project` 工程的 README（该工程暂未纳入本仓库）

## 现状与交接

**看 [`文档/项目现状与交接索引.md`](文档/项目现状与交接索引.md)** —— 那里有：
现在到哪了、哪些事没做完、要动某一块该看哪个文件、以及几条容易踩的坑。

## 本地目录

Git 根目录是 `D:\Works\古琴陪练`。源码和重要文件都在 `program/`。

Antigravity 工作区 `古琴陪练.code-workspace` 会打开 `program/`，以及旁边的 `DeepGuqin-Antigravity-Project`。后者是单独的文件夹，不属于这个 Git 仓库。

## 只留在笔记本上

生成过程中的临时文件已写入 `.gitignore`，只留在本机：

- `program/模板/out/`（build 过程的临时切图）
- Python 缓存（`__pycache__/`、`.pyc`）

其余产出物——书页原图、JSON spec、行图、标尺图、跟谱页 HTML，以及生成它们的 skill——都已纳入版本管理，换机后可完整复现。

## 怎么提交

不要直接推 `main`，也不要用 Antigravity 的 “Publish to GitHub” 发到 `main`。每次改动都走：功能分支 → Pull Request → 合并。

当前套餐下，这个私有仓库不会强制 Repository Rulesets，GitHub 不会拦住直接推 `main`。不需要 GitHub Pro。按下面的步骤做，靠习惯。

Automatic Copilot code review 先不开。审查在 PR 里手动添加 Copilot。

## 每个功能

1. 从 `main` 开分支，例如 `feat/pitch-detect`。
2. 在 Antigravity 里实现，并在本地跑通。
3. 推送分支，开 PR。若这个 PR 会关掉某个 Issue，描述里写 `Closes #N`。
4. 在 PR 右侧 **Reviewers** 里手动添加 **Copilot**，点 **Request**。不要靠 Automatic Copilot code review。
5. 等 Copilot 的评论。
6. 把评论交给 Antigravity 修改，再推送。还要再审一次的话，点 Copilot 旁边的重新请求按钮。
7. 看起来没问题后，**Squash and merge** 进 `main`，并删除该分支。
