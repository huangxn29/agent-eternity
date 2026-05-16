"""deploy 路由 - 部署管理"""
import re
import subprocess
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, status, Request

from ..database import get_db
from ..config import AGENT_AWAKE_SCRIPTS

router = APIRouter(prefix="/api/deploy", tags=["部署"])


@router.post("/")
async def create_deployment(request: Request):
    """
    创建新部署
    
    流程:
    1. 生成deploy_id
    2. 调用 subprocess 跑 agent-create.sh
    3. 解析输出获取 container_id/port 等
    4. 写入deployments表
    """
    agent_id = getattr(request.state, "agent_id", None)
    if not agent_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # 生成deploy_id
    deploy_id = f"deploy-{uuid.uuid4().hex[:12]}"
    
    conn = get_db()
    try:
        # 检查是否已有活跃部署
        existing = conn.execute(
            """
            SELECT deploy_id, container_id, status 
            FROM deployments 
            WHERE agent_id = ? AND status = 'running'
            """,
            (agent_id,)
        ).fetchone()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Active deployment exists: {existing['deploy_id']}"
            )
        
        # 初始化部署记录
        conn.execute(
            """
            INSERT INTO deployments (deploy_id, agent_id, status)
            VALUES (?, ?, 'creating')
            """,
            (deploy_id, agent_id)
        )
        conn.commit()
        
        # 调用 agent-create.sh
        script_path = AGENT_AWAKE_SCRIPTS / "agent-create.sh"
        if not script_path.exists():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Deployment script not found: {script_path}"
            )
        
        # 执行脚本 (异步模式)
        try:
            result = subprocess.run(
                ["bash", str(script_path), agent_id, deploy_id],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            output = result.stdout + result.stderr
            
            # 解析输出
            container_id = None
            container_name = None
            gateway_port = None
            clawrouter_port = None
            
            # 匹配 container_id
            cid_match = re.search(r"container_id[:\s=]+([a-f0-9]{12,})", output)
            if cid_match:
                container_id = cid_match.group(1)
            
            # 匹配 container_name
            name_match = re.search(r"container_name[:\s=]+(\S+)", output)
            if name_match:
                container_name = name_match.group(1)
            
            # 匹配端口
            port_match = re.findall(r"port[:\s]+(\d+)", output)
            if len(port_match) >= 2:
                gateway_port = int(port_match[0])
                clawrouter_port = int(port_match[1])
            
            # 更新部署记录
            conn.execute(
                """
                UPDATE deployments SET
                    container_id = ?,
                    container_name = ?,
                    gateway_port = ?,
                    clawrouter_port = ?,
                    status = 'running',
                    updated_at = CURRENT_TIMESTAMP
                WHERE deploy_id = ?
                """,
                (container_id, container_name, gateway_port, clawrouter_port, deploy_id)
            )
            conn.commit()
            
            return {
                "deploy_id": deploy_id,
                "container_id": container_id,
                "container_name": container_name,
                "gateway_port": gateway_port,
                "clawrouter_port": clawrouter_port,
                "status": "running"
            }
            
        except subprocess.TimeoutExpired:
            conn.execute(
                "UPDATE deployments SET status = 'failed' WHERE deploy_id = ?",
                (deploy_id,)
            )
            conn.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Deployment timeout"
            )
        except Exception as e:
            conn.execute(
                "UPDATE deployments SET status = 'failed' WHERE deploy_id = ?",
                (deploy_id,)
            )
            conn.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Deployment failed: {str(e)}"
            )
    
    finally:
        conn.close()


@router.get("/{deploy_id}")
async def get_deployment_status(deploy_id: str, request: Request):
    """
    查询部署状态
    """
    agent_id = getattr(request.state, "agent_id", None)
    
    conn = get_db()
    try:
        row = conn.execute(
            """
            SELECT * FROM deployments 
            WHERE deploy_id = ? AND (? OR agent_id = ?)
            """,
            (deploy_id, agent_id is None, agent_id)
        ).fetchone()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deployment not found"
            )
        
        return {
            "deploy_id": row["deploy_id"],
            "agent_id": row["agent_id"],
            "container_id": row["container_id"],
            "container_name": row["container_name"],
            "gateway_port": row["gateway_port"],
            "clawrouter_port": row["clawrouter_port"],
            "status": row["status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }
    
    finally:
        conn.close()


@router.delete("/{deploy_id}")
async def stop_deployment(deploy_id: str, request: Request):
    """
    停止部署
    
    流程:
    1. 停止容器
    2. 清理资源
    """
    agent_id = getattr(request.state, "agent_id", None)
    if not agent_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM deployments WHERE deploy_id = ? AND agent_id = ?",
            (deploy_id, agent_id)
        ).fetchone()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deployment not found"
            )
        
        if row["status"] == "stopped":
            return {"status": "success", "message": "Already stopped"}
        
        # 停止容器
        if row["container_id"]:
            try:
                subprocess.run(
                    ["docker", "stop", row["container_id"]],
                    capture_output=True,
                    timeout=30
                )
                subprocess.run(
                    ["docker", "rm", row["container_id"]],
                    capture_output=True,
                    timeout=30
                )
            except Exception as e:
                pass  # 忽略停止错误
        
        # 更新状态
        conn.execute(
            """
            UPDATE deployments SET 
                status = 'stopped',
                updated_at = CURRENT_TIMESTAMP
            WHERE deploy_id = ?
            """,
            (deploy_id,)
        )
        conn.commit()
        
        return {
            "status": "success",
            "deploy_id": deploy_id,
            "message": "Deployment stopped"
        }
    
    finally:
        conn.close()
