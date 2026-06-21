# 10,000次心跳的采样

基于 Spotify 全球 Top 10,000 热门歌曲数据集，以 Tableau 工作簿为视觉基准，复刻 10 组交互图表，讲述从**流派王权交替**到**情绪象限**、从**黄金公式**到**文化反叛**的完整数据叙事。

## 在线预览

### GitHub Pages

部署完成后访问：

- **演示稿（推荐）**：https://asbaniaworld-ui.github.io/10-000-/deck/
- **Web 滚动版**：https://asbaniaworld-ui.github.io/10-000-/web/

> 首次推送后需在仓库 **Settings → Pages** 中将 Source 设为 **GitHub Actions**（workflow 已包含在 `.github/workflows/pages.yml`）。若首次 workflow 失败，启用 Pages 后进入 **Actions** 页重新运行即可。

### 本地预览

```bash
python -m http.server 8770
```

- **Deck 演示稿**：http://localhost:8770/deck/
- **Web 滚动页**：http://localhost:8770/web/

## 项目结构

```
├── deck/              # 12 页交互演示稿（主交付）
├── web/               # 单页滚动版 + 图表数据
│   ├── data/          # charts.json、故事文案、配色等
│   ├── js/            # ECharts 图表渲染
│   └── scripts/       # 数据处理（tableau_logic.py 等）
├── scripts/           # build_deck.py 等构建脚本
├── materials/         # 故事线源文档
└── *.twb              # Tableau 工作簿
```

## 构建

```bash
# 重新生成 deck/index.html
python scripts/build_deck.py
```

## 数据说明

- 图表数据已导出至 `web/data/charts.json`，可直接运行，无需原始 Excel。
- 若需从源数据重新生成，将 `副top-10k-spotify-songs-2025-07-detailed-genre.xlsx` 置于项目根目录后执行：

```bash
python web/scripts/prepare_data.py
python web/scripts/validate_data.py
```

## 技术栈

- **Tableau** — 视觉基准与数据分析
- **ECharts 5** — 网页交互图表
- **Python / pandas** — 数据聚合与构建脚本

## License

课程期末项目，数据来源于 Spotify Top 10,000 公开数据集。
