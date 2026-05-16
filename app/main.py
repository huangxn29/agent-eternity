"""Agent Eternity - 永生平台SaaS 入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db

app = FastAPI(
    title="Agent Eternity",
    description="智能体永生平台SaaS — 注册+验证+签名链+部署+备份+联盟",
    version="0.8.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()
    print("[Eternity] 永生平台启动 🌱 端口8002")

@app.get("/")
def root():
    return {"name": "Agent Eternity", "version": "0.8.0", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "alive"}
