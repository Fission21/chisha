# ADR-0001：单服务架构（SQLite + 静态前端托管）

- 状态：已复盘
- 日期：2026-08-04
- 决策人：项目作者（CC）
- 标签：#架构 #部署 #数据库 #前端
- 关键词：SQLite、PostgreSQL、单容器、静态导出、Next.js、FastAPI

## 1. 背景

MVP（commit `cb3b315`）采用三容器部署：PostgreSQL（db）+ FastAPI（api）+ Next.js（web），本地开发需要同时维护三个进程、Docker Compose 编排，且数据库迁移、备份、开源分发都要围绕 Postgres 进行。

对于一个以静态数据和规则计算为主的中小型工具站，这套复杂度与实际负载不匹配：

- 菜谱 / 食材数据在构建期已定型（JSON），运行期几乎只读。
- 用户数据（档案、收藏、饮食记录）量级小，单文件数据库足以承载。
- 三容器带来的部署、备份、本地开发摩擦在单人维护阶段不可忽视。

2026-08-04 提交 `9cc3c93` 完成改造：Postgres → SQLite、Next.js 改为纯静态导出、三容器合并为单容器。本 ADR 记录该改造的决策过程与约束。

## 2. 目标与边界

### 目标

- 部署简化为单容器单进程，`docker compose up -d --build` 即起。
- 本地开发零外部依赖：无需安装 / 启动 PostgreSQL。
- 数据库单文件、可复制备份，重启不丢用户数据。
- 前端与 API 同源（同端口），去掉 CORS / 跨端口问题。
- 保留未来切回 PostgreSQL 的能力（模型层通用化）。

### 不在本次范围内

- 不做水平扩展 / 高可用设计。
- 不做多租户、多实例部署。
- 不引入 ORM 迁移工具（Alembic）。
- 不解决多用户并发写入性能问题（单文件库的固有限制，接受）。

## 3. 候选方案

### 方案 A：单服务 —— SQLite + FastAPI 静态托管前端

前端 `next build` 产物 `web/out` 由 FastAPI `StaticFiles` 直接托管，API 与页面同源同端口。

- 优点：一个容器一个进程；零外部服务；备份 = 复制一个文件；构建产物托管无 Node 运行时，镜像小；无需 CORS。
- 缺点：SQLite 写并发弱（WAL 模式下可接受）；动态渲染能力受限（页面需预生成）；多实例部署时数据文件需要共享存储。
- 成本：一次重构（删除 web/api 两个容器、改静态导出、seed 幂等化），后续维护成本最低。
- 风险：菜谱详情页需在构建期生成（当前 77 道，构建可接受）；若未来页面数量级增长，构建时间变长。

### 方案 B：保持三容器（Postgres + FastAPI + Next.js）

- 优点：架构演进空间大，Postgres 功能全（全文检索、GIS、并发）。
- 缺点：部署与本地开发摩擦大；备份 / 开源分发重；与本项目数据规模不匹配。
- 成本：持续的多进程维护。
- 风险：复杂度提前支付，MVP 阶段拖慢迭代。

### 方案 C：SQLite + 保留 Next.js 独立服务（两容器）

- 优点：保留 SSR / 动态路由能力。
- 缺点：仍需双容器双进程；同源问题靠反向代理解决，复杂度介于 A 与 B 之间，两头不讨好。
- 成本：两容器编排 + 代理配置。
- 风险：收益不明显，复杂度仍高于 A。

## 4. 最终决策

最终选择：方案 A（单服务 —— SQLite + FastAPI 静态托管）。

核心理由：

1. 数据规模与访问模式（静态菜谱 + 轻量用户数据）完全在 SQLite 能力范围内，Postgres 的优势用不上。
2. 单容器单进程把部署、备份、本地开发、开源分发的摩擦同时降为零，与单人维护现状匹配。
3. 前端纯静态导出后无需 Node 运行时，镜像更小、运行时攻击面更小。

为什么不选择其他方案：

- 方案 B：复杂度与数据规模不匹配，且 MVP 已证明静态导出可覆盖全部现有页面。
- 方案 C：静态导出已满足需求，保留独立前端服务只有成本没有收益。

## 5. 架构与实现约束

- 前端必须使用 `output: export` 纯静态导出，页面需在构建期可生成；菜谱详情页构建时读取 `data/processed/recipes.json`（Dockerfile 阶段 1 中 `COPY data/processed /data/processed`）。
- 后端是唯一对外服务，端口统一 8000，API 前缀 `/api/*`，静态资源根路径 `/*`（见 `api/app/main.py`）。
- 数据库必须通过 `DATABASE_URL` 环境变量连接，默认 `sqlite:///./var/chisha.db`（见 `api/app/config.py`、`api/app/db.py`）。
- ORM 模型禁止使用 SQLite 专有类型，通用 JSON 类型用于数组字段，保证 `DATABASE_URL` 可切回 PostgreSQL（见 `api/app/models.py`）。
- 容器内数据卷挂载 `/app/var`（见 `Dockerfile`、`docker-compose.yml`），数据库文件必须落在这个卷内。
- `seed` 必须幂等：已有数据跳过，重启不丢用户数据（`python -m app.seed && uvicorn ...`，见 `Dockerfile` CMD）。
- 新增页面必须评估静态导出可行性，不能引入需要 SSR 的页面。
- SQLite 连接必须设置 `check_same_thread=False` 并保证父目录存在（见 `api/app/db.py`）。

## 6. 落地计划

| 事项 | 涉及文件或模块 | 负责人 | 状态 |
|---|---|---|---|
| 数据库 Postgres → SQLite，模型改通用 JSON 类型 | `api/app/db.py`、`api/app/config.py`、`api/app/models.py` | CC | ✅ |
| 前端改静态导出 + 详情页构建期生成 | `web/next.config.mjs`、`web/app/recipes/[id]/page.tsx` | CC | ✅ |
| 三容器 → 单容器多阶段 Dockerfile | `Dockerfile`、`docker-compose.yml` | CC | ✅ |
| seed 幂等化 | `api/app/seed.py` | CC | ✅ |
| 测试改用本地 SQLite | `api/tests/conftest.py`、`api/pytest.ini` | CC | ✅ |
| 文档同步 | `README.md`、`docs/04-技术方案.md`、`PRODUCT.md`、`.env.example` | CC | ✅ |

## 7. 验收标准

- `docker compose up -d --build` 后单容器可访问 `http://localhost:8000`，前端页面与 `/api/health` 均正常。
- 重启容器后用户注册数据、收藏、饮食记录不丢失（卷持久化）。
- 本地无 Docker、无 Postgres 时，`pytest api/tests -q`（33 项）全绿。
- `DATABASE_URL` 指向 PostgreSQL 时应用可启动（模型无 SQLite 专有类型）。
- 静态导出构建产物中没有 Node 运行时依赖。
- 前端与 API 同源，无 CORS 错误。

## 8. 后果与风险

### 正面影响

- 部署、备份、开源分发复杂度大幅下降。
- 本地开发仅需 Python 环境，测试无需 Docker / Postgres。
- 单容器单进程，运维心智负担小。

### 负面影响和代价

- SQLite 写并发能力有限，多用户同时写入时可能锁库（当前规模可接受）。
- 菜谱详情页构建期生成：新增菜谱需重新构建镜像才能出现在详情页（API 推荐不受影响，运行时读 JSON）。
- 单实例部署，无内置水平扩展路径。

### 持续跟踪风险

- [ ] 用户量增长后 SQLite 写入是否成为瓶颈（监控 `database is locked` 错误）。
- [ ] 菜谱数量增长后 `next build` 构建时间是否失控。
- [ ] 静态导出的动态内容需求是否出现（需要时重新评估方案）。

## 9. 复盘

- 预期目标是否达成：达成。部署从三容器降为一容器，本地开发与测试不再依赖 Docker / Postgres。
- 实际收益和成本：改造在一天内完成（2026-08-04），收益立即兑现；后续功能（账号、收藏、饮食记录、一周餐单）全部在此架构上顺利开发。
- 哪些假设被证明错误：暂无。数据规模与访问模式假设成立（33 项测试全绿，无性能问题）。
- 是否需要新建 ADR 替代当前决策：目前不需要。若出现「多用户写并发成为瓶颈」或「需要动态页面」的明确证据，再启动替代决策。

## 10. 相关链接

- 相关 Issue：无（个人项目）
- 关联 ADR：[ADR-0002：数据管道与数据源选型](./2026-08-04-0002-data-pipeline-json.md)、[ADR-0004：认证与用户数据同步方案](./2026-08-04-0004-auth-bearer-token.md)
- 代码：`api/app/db.py`、`api/app/config.py`、`api/app/main.py`、`api/app/models.py`、`Dockerfile`、`docker-compose.yml`
- 测试：`api/tests/conftest.py`、`api/tests/`
- 文档：`README.md`、`docs/04-技术方案.md`、`PRODUCT.md`
