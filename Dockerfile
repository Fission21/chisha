# ===== 阶段 1：构建前端静态文件（Next.js） =====
FROM node:22-alpine AS web-builder
WORKDIR /build
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ .
# 菜谱详情页构建时从 data/processed/recipes.json 读取 ID（相对 /build/.. 即 /data）
COPY data/processed /data/processed
RUN npm run build

# ===== 阶段 2：Python 运行时（单服务：API + 前端静态托管） =====
FROM python:3.11-slim
WORKDIR /app

COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/app ./app
COPY api/tests ./tests
COPY data/processed ./data/processed
COPY --from=web-builder /build/out ./web/out

# SQLite 数据库文件持久化目录
ENV DATABASE_URL=sqlite:////app/var/chisha.db
ENV DATA_DIR=/app/data/processed
ENV WEB_DIST=/app/web/out
VOLUME ["/app/var"]

EXPOSE 8000
CMD ["sh", "-c", "python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port 8000"]