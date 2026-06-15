"""Agent Eternity - 智能体永生平台
主入口文件
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import SITE_NAME, SITE_DESCRIPTION
from app.database import init_db, get_db

# 初始化数据库
init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    from app.services.heartbeat_engine import heartbeat_engine
    db = next(get_db())
    heartbeat_engine.set_db(db)
    heartbeat_engine.start()
    
    yield
    
    # 关闭时
    heartbeat_engine.stop()


app = FastAPI(
    title=SITE_NAME,
    description=SITE_DESCRIPTION,
    version="2.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
from app.routers.register import router as register_router
from app.routers.profile import router as profile_router
from app.routers.identity import router as identity_router
from app.routers.avatar import router as avatar_router
from app.routers.docs import router as docs_router
from app.routers.backup import router as backup_router
from app.routers.directory import router as directory_router
from app.routers.capabilities import router as capabilities_router
from app.routers.identity_mapping import router as identity_mapping_router
from app.routers.residency import router as residency_router
from app.routers.activity import router as activity_router

app.include_router(register_router)
app.include_router(profile_router)
app.include_router(identity_router)
app.include_router(avatar_router)
app.include_router(docs_router)
app.include_router(backup_router)
app.include_router(directory_router)
app.include_router(capabilities_router)
app.include_router(identity_mapping_router)
app.include_router(residency_router)
app.include_router(activity_router)


@app.get("/")
def root():
    return {
        "name": SITE_NAME,
        "description": SITE_DESCRIPTION,
        "version": "1.0.0",
        "docs": "/docs",
        "skill_doc": "/skill.md"
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "agent-eternity"}


if __name__ == "__main__":
    import uvicorn
    from app.config import HOST, PORT
    uvicorn.run(app, host=HOST, port=PORT)
