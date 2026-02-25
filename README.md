# Journal Scout Demo（本地预览）

## 1. 生成数据

先准备 `ShowJCR` 数据源（优先读取其中 `jcr.db`）：

```powershell
git clone --depth 1 https://github.com/hitfyd/ShowJCR.git .\xuankan\data\showjcr_repo
```

然后生成站点数据：

```powershell
python .\build_data.py
```

生成文件：`data/journals.json`、`data/hq_field_stats.json`

## 2. 启动网页（推荐：带 Elsevier 代理）

```powershell
cd .\xuankan\demo_site
$env:ELSEVIER_API_KEY='你的ElsevierKey'
python .\dev_server.py --port 8000
```

浏览器打开：

`http://localhost:8000`

## 3. 当前功能

- 查询入口页：输入期刊名/ISSN/CN号实时联想
- 选择联想项后跳转详情页（`journal.html?id=...`）
- 详情页展示：ISSN/eISSN/CN、IF/JCR最新、中科院最新（含大类/小类）、CSCD、高质量目录、来源轨迹
- 详情页展示 ShowJCR 历年数据：JCR/IF（2022/2023/2024）、中科院分区（2022/2023/2025）、预警（2020/2021/2023/2024/2025）、CCF/CCFT（2022）
- 详情页“期刊概览”支持官网直连与智能补全：本地未命中官网/出版商/OA时自动调用 OpenAlex
- 封面区域优先展示 Wikidata 封面图（P18）/logo（P154），无图时回退为视觉占位并叠加站点 Logo（Clearbit）
- 主视觉右侧支持豆瓣式评分卡：优先显示 Scopus CiteScore（Elsevier API），可展示 CiteScore/SJR/SNIP 及学科层级/分区/排名/百分位，不可用时回退 OpenAlex 代理值
- 详情页提供“相近期刊”快速跳转

## 4. 说明

- 这是可运行演示版，重点用于看页面和数据融合效果。
- 你后续确认后，可以再接后端 API 与增量同步任务。
- IF/JCR、中科院分区、预警、CCF/CCFT 优先来源于 `ShowJCR` 的 `jcr.db`；若无数据库才回退到 CSV。
- 官网链接优先使用本地数据；若识别为目录站/聚合站链接，会改由 OpenAlex 重新解析期刊官网。
- 如需启用官方 Scopus CiteScore：优先使用 `dev_server.py` + `ELSEVIER_API_KEY`（可避免浏览器 CORS）。
- 若仅使用 `python -m http.server` 静态服务，前端直连 Elsevier 可能因 CORS 失败并自动回退到 OpenAlex 代理值。
- 开发临时方式（不推荐长期使用）：`localStorage.setItem('elsevier_api_key', '你的APIKey')`，然后刷新页面。
