# 贡献指南

感谢你愿意为「吃啥」贡献代码或菜谱！项目刻意保持轻量：**一个 FastAPI 服务（SQLite + 静态前端）**，任何改动请先对齐这个原则。

## 项目结构

```
api/            FastAPI 后端（app/ 源码、tests/ 测试）
web/            Next.js 前端（output: export 纯静态导出 → web/out）
data/recipes/   菜谱源数据（*.json，一行一道菜）
data/raw/       食材营养原始数据（中国食物成分表等）
data/processed/ 构建产物（scripts/build_data.py 生成）
scripts/        数据构建脚本
```

## 本地开发

```bash
python -m venv .venv
.venv/Scripts/pip install -r api/requirements.txt
.venv/Scripts/python -m app.seed --app-dir api          # 首次初始化数据库
.venv/Scripts/python -m uvicorn app.main:app --app-dir api --port 8000
```

前端热更新（可选）：`cd web && NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev`

## 加一道菜谱（最常见贡献）

1. 在 `data/recipes/*.json` 里按现有格式追加一道菜，字段：`id / title / titleEn / cuisine / mealTypes / difficulty / cookTimeMin / servings / summary / coverEmoji / ingredients[{name,ref,amount,unit,note}] / steps[{text,durationMin,heat}] / tips / tags / allergens`
2. `ingredients[].ref` 必须是 `data/processed/foods.json` 里能匹配到的食材（按名称匹配），这样营养才会由「食材 × 克数」自动推导
3. 重新构建并重启：
   ```bash
   python scripts/build_data.py        # 生成 data/processed/*.json
   .venv/Scripts/python -m app.seed --app-dir api
   ```
4. 跑测试确认没破坏：
   ```bash
   .venv/Scripts/python -m pytest api/tests -q
   ```

> 营养匹配不到或引用失败时，`build_data.py` 会报错退出，方便你修。

## 测试

- 30 项测试覆盖：营养计算 / 推荐 / 菜谱 / 认证 / 一周餐单
- 测试用 SQLite 临时库，**不需要 Docker 或 PostgreSQL**
- 提交前请保证 `pytest -q` 全绿

## 代码规范

- 后端：Python，保持现状风格（FastAPI + SQLAlchemy 同步写法）
- 前端：TypeScript，客户端组件为主（SPA 风格），避免引入服务端运行时
- **不新增重型依赖**：能用标准库 / 现有依赖解决就别加包；数据库继续用 SQLite

## 数据版权（重要）

- 《中国食物成分表（第 6 版）》版权归出版社，商用需授权；本项目仅作学习/研究引用，来源见 `data/raw/china-food/`
- 新加入的食材营养数据请注明来源（source 字段）
- 菜谱文字建议原创或注明出处，不要直接搬运受版权保护的菜谱