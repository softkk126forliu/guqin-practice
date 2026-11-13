# 古琴陪练

私有仓库：<https://github.com/softkk126forliu/guqin-practice>

## 本地目录

Git 根目录是 `D:\Works\古琴陪练`。源码和重要文件都在 `program/`。

Antigravity 工作区 `古琴陪练.code-workspace` 会打开 `program/`，以及旁边的 `DeepGuqin-Antigravity-Project`。后者是单独的文件夹，不属于这个 Git 仓库。

## 只留在笔记本上

生成结果和工具输出已写入 `.gitignore`，只留在本机：

- `program/.agents/`
- `program/crops/`
- `program/out_daoyi/`
- `program/out_daoyi_final/`
- `program/out_daoyi_p7/`
- `program/slices_chunfeng/`
- `program/slices_daoyi_p6/`
- `program/slices_daoyi_p7/`

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
