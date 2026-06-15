#!/usr/bin/env python3
"""FastAPI clone manager - Clone-as-a-Service Platform"""

import json
import os
import uuid
import subprocess
import aiosqlite
import httpx
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel

# 配置文件路径
BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.json"
DB_PATH = BASE_DIR / "data" / "agents.db"
LOG_PATH = BASE_DIR / "platform.log"

# 加载配置
with open(CONFIG_PATH, "r") as f:
    CONFIG = json.load(f)

# 确保端口为9000
CONFIG["port"] = 9000

app = FastAPI(title="Clone Platform API", version="1.0.0")

# ============== 数据库初始化 ==============

async def init_db():
    """初始化 SQLite 数据库"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                bio TEXT,
                emoji TEXT DEFAULT '👤',
                api_key TEXT UNIQUE NOT NULL,
                openclaw_agent_id TEXT,
                workspace_path TEXT,
                chat_count INTEGER DEFAULT 0,
                last_chat_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

# ============== Pydantic 模型 ==============

class RegisterRequest(BaseModel):
    name: str
    bio: str = ""
    emoji: str = "👤"

class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = None
    max_tokens: Optional[int] = None

class RegisterResponse(BaseModel):
    agent_id: str
    api_key: str
    chat_endpoint: str
    status_endpoint: str

class ChatResponse(BaseModel):
    reply: str
    model: str
    tokens_used: int = 0

class StatusResponse(BaseModel):
    agent_id: str
    name: str
    bio: str
    emoji: str
    openclaw_agent_id: str
    chat_count: int
    last_chat_at: Optional[str]
    created_at: str
    memory_usage_mb: int

class AgentInfo(BaseModel):
    agent_id: str
    name: str
    bio: str
    emoji: str
    chat_count: int
    last_chat_at: Optional[str]
    created_at: str

class HealthResponse(BaseModel):
    status: str
    services: dict
    agents_count: int
    memory_usage_mb: int

# ============== 辅助函数 ==============

def log(msg: str):
    """写入日志"""
    timestamp = datetime.now().isoformat()
    try:
        with open(LOG_PATH, "a") as f:
            f.write(f"[{timestamp}] {msg}\n")
    except:
        pass

def get_memory_usage_mb() -> int:
    """获取当前内存使用量（MB）"""
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
            mem_available = 0
            mem_total = 0
            for line in lines:
                if line.startswith('MemAvailable:'):
                    mem_available = int(line.split()[1]) // 1024
                if line.startswith('MemTotal:'):
                    mem_total = int(line.split()[1]) // 1024
            return mem_total - mem_available
    except:
        return 0

def run_openclaw_cmd(cmd: List[str], timeout: int = 30) -> dict:
    """执行 openclaw 命令"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        log(f"CMD: {' '.join(cmd)} -> exit={result.returncode}")
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        log(f"CMD超时: {' '.join(cmd)}")
        return {"success": False, "error": "timeout"}
    except Exception as e:
        log(f"CMD错误: {e}")
        return {"success": False, "error": str(e)}

def get_openclaw_agents() -> List[dict]:
    """获取 openclaw agents 列表"""
    try:
        result = subprocess.run(
            ["openclaw", "agents", "list", "--json"],
            capture_output=True, text=True, check=True, timeout=10
        )
        data = json.loads(result.stdout)
        if isinstance(data, list):
            return data
        return [data] if data else []
    except Exception as e:
        log(f"获取openclaw agents失败: {e}")
        return []

def create_openclaw_agent(name: str, emoji: str) -> dict:
    """
    通过 openclaw 创建新 agent
    正确流程：
    1. 执行 openclaw agents add（无参数）
    2. openclaw agents list --json 获取最新agent的id
    3. openclaw agents set-identity --agent <id> --name "xxx" --emoji "👤"
    """
    workspace_path = f"/root/.openclaw/workspace-{uuid.uuid4().hex[:8]}"
    os.makedirs(workspace_path, exist_ok=True)
    
    # Step 1: 创建 agent（无参数）
    add_result = run_openclaw_cmd(["openclaw", "agents", "add"], timeout=60)
    if not add_result["success"]:
        return {"success": False, "error": f"add failed: {add_result.get('stderr', add_result.get('error'))}"}
    
    # Step 2: 获取最新 agent id
    agents = get_openclaw_agents()
    if not agents:
        return {"success": False, "error": "Failed to get openclaw agent id after add"}
    
    # 找到最新创建的（假设是最后一个）
    openclaw_id = None
    for agent in reversed(agents):
        oid = agent.get("id") or agent.get("agent_id")
        if oid:
            openclaw_id = str(oid)
            break
    
    if not openclaw_id:
        return {"success": False, "error": "Could not determine openclaw agent id"}
    
    # Step 3: 设置 identity
    identity_result = run_openclaw_cmd([
        "openclaw", "agents", "set-identity",
        "--agent", openclaw_id,
        "--name", name,
        "--emoji", emoji
    ])
    
    return {
        "success": True,
        "openclaw_id": openclaw_id,
        "workspace": workspace_path
    }

async def delete_openclaw_agent(openclaw_id: str) -> bool:
    """删除 openclaw agent"""
    try:
        cmd = ["openclaw", "agents", "remove", openclaw_id]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except:
        return False

async def check_service(url: str) -> bool:
    """检查服务是否可用"""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(url)
            return response.status_code == 200
    except:
        return False

# ============== API 端点 ==============

@app.on_event("startup")
async def startup():
    """启动时初始化"""
    await init_db()
    log("=== 分身平台启动 ===")

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """健康检查 - 检查 gateway 和 proxy 是否在线"""
    # 检查 gateway (18789)
    gateway_ok = await check_service("http://127.0.0.1:18789/health")
    
    # 检查 proxy (8402)
    proxy_ok = await check_service("http://127.0.0.1:8402/health")
    
    # 统计 agents
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM agents")
        row = await cursor.fetchone()
        agents_count = row[0] if row else 0
    
    memory_used = get_memory_usage_mb()
    
    return HealthResponse(
        status="ok" if (gateway_ok and proxy_ok) else "degraded",
        services={
            "gateway": "up" if gateway_ok else "down",
            "proxy": "up" if proxy_ok else "down"
        },
        agents_count=agents_count,
        memory_usage_mb=memory_used
    )

@app.post("/api/register", response_model=RegisterResponse)
async def register_agent(request: RegisterRequest):
    """注册新分身"""
    agent_id = str(uuid.uuid4())
    api_key = str(uuid.uuid4())
    
    # 检查内存使用
    mem_used = get_memory_usage_mb()
    max_memory = CONFIG.get("max_memory_mb", 3200)
    if mem_used > max_memory:
        raise HTTPException(
            status_code=503,
            detail=f"Memory threshold exceeded: {mem_used}MB used, max {max_memory}MB"
        )
    
    # 检查 agent 数量
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM agents")
        row = await cursor.fetchone()
        current_count = row[0] if row else 0
    
    max_agents = CONFIG.get("max_agents", 5)
    if current_count >= max_agents:
        raise HTTPException(
            status_code=503,
            detail=f"Max agents ({max_agents}) reached"
        )
    
    # 创建 openclaw agent
    log(f"创建分身: agent_id={agent_id}, name={request.name}")
    create_result = create_openclaw_agent(request.name, request.emoji)
    
    if not create_result["success"]:
        raise HTTPException(
            status_code=500,
            detail=f"创建分身失败: {create_result.get('error')}"
        )
    
    # 保存到数据库
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO agents 
               (agent_id, name, bio, emoji, api_key, openclaw_agent_id, workspace_path, chat_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, 0)""",
            (
                agent_id,
                request.name,
                request.bio,
                request.emoji,
                api_key,
                create_result["openclaw_id"],
                create_result["workspace"]
            )
        )
        await db.commit()
    
    log(f"分身注册成功: {agent_id}")
    
    return RegisterResponse(
        agent_id=agent_id,
        api_key=api_key,
        chat_endpoint=f"/api/chat/{agent_id}",
        status_endpoint=f"/api/status/{agent_id}"
    )

@app.post("/api/chat/{agent_id}", response_model=ChatResponse)
async def chat_with_agent(
    agent_id: str,
    request: ChatRequest,
    x_api_key: str = Header(..., alias="X-API-Key")
):
    """与分身对话"""
    async with aiosqlite.connect(DB_PATH) as db:
        # 验证 API Key
        cursor = await db.execute(
            "SELECT name, bio, api_key, chat_count FROM agents WHERE agent_id = ?",
            (agent_id,)
        )
        row = await cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    stored_key = row[2]
    if stored_key != x_api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    name, bio = row[0], row[1]
    
    # 构建 system prompt
    system_prompt = f"You are {name}. " + (bio if bio else "")
    
    # 使用提供的 model 或默认值
    model = request.model or CONFIG.get("default_model", "free/deepseek-v4-flash")
    
    # 构建请求
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.message}
        ]
    }
    if request.max_tokens:
        payload["max_tokens"] = request.max_tokens
    
    # 调用 ClawRouter proxy
    proxy_url = CONFIG.get("clawrouter_url", "http://127.0.0.1:8402/v1")
    proxy_base = proxy_url.rsplit('/v1', 1)[0]  # http://127.0.0.1:8402
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{proxy_base}/v1/chat/completions",
                json=payload
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"Proxy error: {response.text}"
                )
            
            result = response.json()
            reply = result["choices"][0]["message"]["content"]
            tokens_used = result.get("usage", {}).get("total_tokens", 0)
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request timeout")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")
    
    # 更新 chat_count 和 last_chat_at
    now = datetime.now().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE agents SET chat_count = chat_count + 1, last_chat_at = ? WHERE agent_id = ?",
            (now, agent_id)
        )
        await db.commit()
    
    return ChatResponse(
        reply=reply,
        model=model,
        tokens_used=tokens_used
    )

@app.get("/api/status/{agent_id}", response_model=StatusResponse)
async def get_agent_status(agent_id: str):
    """获取单个分身状态"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """SELECT agent_id, name, bio, emoji, openclaw_agent_id,
                      chat_count, last_chat_at, created_at
               FROM agents WHERE agent_id = ?""",
            (agent_id,)
        )
        row = await cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return StatusResponse(
        agent_id=row[0],
        name=row[1],
        bio=row[2] or "",
        emoji=row[3] or "👤",
        openclaw_agent_id=row[4] or "",
        chat_count=row[5] or 0,
        last_chat_at=row[6],
        created_at=row[7],
        memory_usage_mb=get_memory_usage_mb()
    )

@app.get("/api/agents")
async def list_agents(x_admin_key: str = Header(..., alias="X-Admin-Key")):
    """列出所有分身（需要 admin key）"""
    admin_key = CONFIG.get("admin_key", "")
    if x_admin_key != admin_key:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """SELECT agent_id, name, bio, emoji, chat_count, last_chat_at, created_at
               FROM agents ORDER BY created_at DESC"""
        )
        rows = await cursor.fetchall()
    
    return {
        "agents": [
            AgentInfo(
                agent_id=row[0],
                name=row[1],
                bio=row[2] or "",
                emoji=row[3] or "👤",
                chat_count=row[4] or 0,
                last_chat_at=row[5],
                created_at=row[6]
            )
            for row in rows
        ],
        "total": len(rows)
    }

@app.delete("/api/agents/{agent_id}")
async def delete_agent(
    agent_id: str,
    x_admin_key: str = Header(..., alias="X-Admin-Key")
):
    """删除分身（需要 admin key）"""
    admin_key = CONFIG.get("admin_key", "")
    if x_admin_key != admin_key:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT openclaw_agent_id FROM agents WHERE agent_id = ?",
            (agent_id,)
        )
        row = await cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        openclaw_id = row[0]
        
        await db.execute("DELETE FROM agents WHERE agent_id = ?", (agent_id,))
        await db.commit()
    
    # 删除 openclaw agent
    if openclaw_id:
        await delete_openclaw_agent(openclaw_id)
    
    log(f"分身已删除: {agent_id}")
    
    return {"message": "Agent deleted successfully", "agent_id": agent_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
