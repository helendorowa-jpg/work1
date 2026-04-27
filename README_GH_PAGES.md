步骤：

- 已把首页复制到 `docs/index.html`，并添加 GitHub Actions 工作流：`.github/workflows/deploy-gh-pages.yml`。
- 推送到 GitHub（主分支名为 `main` 或 `master`）后，Actions 会把 `docs` 发布到 `gh-pages` 分支。

如何查看地址：

- 默认页面地址格式为 `https://<用户名>.github.io/<仓库名>/`。
- 或在仓库 Settings → Pages 中查看并确认来自 `gh-pages` 分支的发布状态。

如果你希望我帮你：

- 帮你把本地改动推到远程（需要你在本地执行 `git push` 或授权）。
- 或改为使用 `gh-pages` 分支直接托管（我可修改 workflow）。
