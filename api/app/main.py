from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import plan, recipes, foods

app = FastAPI(title="吃啥 API", version="0.1.0")

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

@app.get("/api/health")
def health():
    return {"status": "ok"}
