import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers import plan, recipes, foods, auth, me

app = FastAPI(title="吃啥 API", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(plan.router)
app.include_router(recipes.router)
app.include_router(foods.router)
app.include_router(auth.router)
app.include_router(me.router)

@app.get("/api/health")
def health():
    return {"status": "ok"}


# 前端静态文件（web/out 由 next build 生成）；未构建时仅提供 API
WEB_DIST = Path(os.environ.get("WEB_DIST", "web/out"))
if WEB_DIST.is_dir():
    app.mount("/", StaticFiles(directory=WEB_DIST, html=True), name="web")