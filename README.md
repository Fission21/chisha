# 吃啥 🍳⚡

> 解决健身人士「今天吃什么、怎么做好吃」的网站。

**一句话定位**：输入身体信息和目标（增肌 / 减脂 / 维持），自动算出每日热量与三大营养素目标，推荐搭配的菜谱（中餐 + 全球做法），并给出专业、可执行、好吃的菜谱（食材克数、步骤、火候、营养、技巧）。

## 快速开始（Docker，推荐）

```bash
docker compose up -d --build
# 打开 http://localhost:8000
```

首次启动会自动导入数据（1741 条食材营养 + 77 道菜谱），之后数据保存在 `chisha-data` 卷里，重启不丢失。

## 本地开发（不用 Docker）

```bash
# 1. 后端（Python 3.11+）
python -m venv .venv
.venv/Scripts/pip install -r api/requirements.txt   # Windows
# venv/bin/pip install -r api/requirements.txt       # macOS / Linux

# 2. 初始化数据库（首次运行）
.venv/Scripts/python -m app.seed --app-dir api       # 或先 cd api

# 3. 启动后端（API + 前端静态托管）
.venv/Scripts/python -m uvicorn app.main:app --app-dir api --port 8000

# 4. （可选）前端开发模式，热更新
cd web
NEXT_PUBLIC_API_URL=http://localhost:8000 npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev  # http://localhost:3000
```

前端是纯静态导出（`web/out`），由后端直接托管，所以日常使用只需跑后端一个进程。

## 架构（刻意保持简单）

```
[ 单个 FastAPI 服务 :8000 ]
   ├── /api/*         营养计算 / 推荐 / 菜谱 / 用户 API
   └── /*             前端静态文件（next build 产物，无 Node 运行时）
   └── SQLite         单文件数据库（var/chisha.db，零配置）
```

- 原来 Postgres + 3 容器，现为 **SQLite + 1 容器**：部署、备份、开源都更轻。
- 前端 Next.js 用 `output: export` 纯静态导出，菜谱详情页在构建时读取 `data/processed/recipes.json` 生成。
- 如需 PostgreSQL，仍可通过环境变量 `DATABASE_URL` 切回（模型用通用 JSON 类型，兼容两者）。

## 核心功能

1. **身体档案**：身高 / 体重 / 年龄 / 性别 / 体脂率（选填）、活动量 / 目标
2. **营养计算**：Mifflin-St Jeor → BMR → TDEE → 每日热量 + 蛋白 / 碳水 / 脂肪
3. **吃什么**：按营养目标 + 过敏忌口 + 偏好菜系，分早餐 / 午餐 / 晚餐 / 加餐推荐，任选其一即可达标
4. **怎么做**：专业菜谱——食材克数、步骤与火候、每份营养、过敏原、师傅小贴士
5. **一周餐单 + 购物清单**：一键生成 7 天不重样的餐单，并自动汇总采购清单
6. **饮食记录**：按食材/菜谱记录每天吃了什么，实时对照热量与三大营养素目标
7. **收藏**：把喜欢的菜谱收进收藏夹，菜谱库可一键筛选
8. **记住档案**：身体信息自动保存，下次直接继续
9. **账号同步**：注册 / 登录后，档案、收藏、饮食记录云端保存，换设备不丢

## 数据管道

```bash
python scripts/build_data.py   # 中国食物成分表 + 全球食材 → data/processed/*.json
```

- 数据源：`data/raw/china-food/`（中国食物成分表第 6 版 OCR，来源见下方）、`data/global_foods.json`（USDA 近似值）
- 新菜谱放 `data/recipes/*.json`（格式见 `data/recipes/chinese.json`），重新 build + 重启即可
- 菜谱营养由「食材 × 克数」推导，随食材库自动更新

## 测试

```bash
.venv/Scripts/python -m pytest api/tests -q   # 30 项，用 SQLite，无需 Docker
```

## 数据来源与版权

- 《中国食物成分表（第 6 版）》1657 条（[Sanotsu/china-food-composition-data](https://github.com/Sanotsu/china-food-composition-data)，OCR 识别，版权归出版社，商用需授权）
- 全球食材补充（USDA 近似值，`data/global_foods.json` 标注 source）
- 菜谱（自建，营养由食材推导）

## 技术栈

- 前端：Next.js 15（App Router，静态导出）+ TypeScript + 自绘 SVG 图标 + 纯 CSS 设计系统（见 `DESIGN.md`）
- 后端：FastAPI（SQLAlchemy + SQLite）
- 设计规范：已安装 [impeccable](https://github.com/pbakaus/impeccable)（本地开发工具，不入库），视觉世界「菜市场 · 价签」

## 文档

- [01-调研报告](docs/01-调研报告.md)：GitHub 同类项目与数据源调研
- [02-产品设计](docs/02-产品设计.md)：用户流程、页面、功能优先级
- [03-数据方案](docs/03-数据方案.md)：数据源选型与数据结构
- [04-技术方案](docs/04-技术方案.md)：架构与技术栈
- [05-路线图](docs/05-路线图.md)：从 MVP 到正式版
- [开源菜谱数据源调研](docs/recipe-sources-research.md)
- `PRODUCT.md`：产品事实记录（impeccable）
- `DESIGN.md`：视觉世界与设计系统（impeccable）
## 参与贡献

加菜谱、跑测试、代码规范见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 开源许可

- 代码：MIT License（见 [LICENSE](LICENSE)）
- 数据：来源见上文「数据来源与版权」，部分数据版权归原作者 / 出版社，仅供学习研究