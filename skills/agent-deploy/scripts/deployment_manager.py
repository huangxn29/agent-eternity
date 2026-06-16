#!/usr/bin/env python3
"""
部署管理器模块
提供Agent部署的状态跟踪、生命周期管理和资源监控功能。
"""

import os
import json
import time
import subprocess
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Tuple
from datetime import datetime

from utils import retry, ConfigManager
from logger import get_logger, OperationLogger


@dataclass
class DeploymentStatus:
    """部署状态信息"""
    agent_id: str
    agent_name: str = ""
    status: str = "pending"  # pending, running, stopped, error, deleted
    container_id: str = ""
    container_name: str = ""
    gateway_port: int = 0
    clawrouter_port: int = 0
    cpu_quota: str = "1.0"
    memory_quota: str = "1536M"
    created_at: str = ""
    started_at: str = ""
    stopped_at: str = ""
    last_health_check: str = ""
    health_status: str = "unknown"  # healthy, unhealthy, unknown
    error_message: str = ""
    restart_count: int = 0
    labels: Dict[str, str] = field(default_factory=dict)

    def to_dict(self):
        """转换为字典"""
        return asdict(self)


@dataclass
class ResourceUsage:
    """资源使用情况"""
    cpu_percent: float = 0.0
    memory_usage: int = 0  # bytes
    memory_limit: int = 0  # bytes
    memory_percent: float = 0.0
    network_rx: int = 0  # bytes
    network_tx: int = 0  # bytes


class DeploymentManager:
    """Agent部署管理器
    
    负责管理Agent的部署生命周期，包括创建、启动、停止、删除、状态查询等。
    """
    
    def __init__(self, data_dir: str = None, config_file: str = None):
        """初始化部署管理器
        
        Args:
            data_dir: 数据目录路径
            config_file: 配置文件路径
        """
        if data_dir:
            self.data_dir = Path(data_dir).resolve()
        else:
            self.data_dir = Path(__file__).parent.parent / "agent-deploy-data"
        
        self.state_dir = self.data_dir / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置管理
        self.config = ConfigManager(config_file)
        
        # 日志系统
        log_level = self.config.get('logging.level', 'INFO')
        log_dir = self.data_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger(
            name="deployment-manager",
            log_level=log_level,
            log_dir=str(log_dir)
        )
        self.operation_logger = OperationLogger(
            log_dir=str(log_dir),
            operator="deployment-manager"
        )
        
        # 部署状态文件
        self.deployments_file = self.state_dir / "deployments.json"
        self.deployments = {}
        self._load_deployments()
        self.logger.info("部署管理器初始化完成")
    
    def _load_deployments(self):
        """加载部署状态"""
        if self.deployments_file.exists():
            try:
                with open(self.deployments_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.deployments = {
                    k: DeploymentStatus(**v) 
                    for k, v in data.items()
                }
            except (json.JSONDecodeError, TypeError) as e:
                self.logger.error(f"加载部署状态失败: {e}")
                self.deployments = {}
        else:
            self.deployments = {}
    
    def _save_deployments(self):
        """保存部署状态"""
        data = {
            k: v.to_dict() for k, v in self.deployments.items()
        }
        try:
            with open(self.deployments_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存部署状态失败: {e}")
    
    def register_deployment(self, agent_id: str, agent_name: str = "",
                           container_id: str = "", container_name: str = "",
                           gateway_port: int = 0, clawrouter_port: int = 0,
                           cpu_quota: str = "1.0", memory_quota: str = "1536M",
                           labels: Dict[str, str] = None) -> DeploymentStatus:
        """注册一个新的部署
        
        Args:
            agent_id: Agent唯一标识符
            agent_name: Agent名称
            container_id: 容器ID
            container_name: 容器名称
            gateway_port: Gateway端口
            clawrouter_port: ClawRouter端口
            cpu_quota: CPU配额
            memory_quota: 内存配额
            labels: 标签
        
        Returns:
            部署状态对象
        """
        self.logger.info(f"注册部署: agent_id={agent_id}, name={agent_name}")
        
        if agent_id in self.deployments:
            self.logger.warning(f"部署已存在: {agent_id}")
            return self.deployments[agent_id]
        
        now = datetime.utcnow().isoformat()
        
        status = DeploymentStatus(
            agent_id=agent_id,
            agent_name=agent_name or agent_id,
            status="running" if container_id else "pending",
            container_id=container_id,
            container_name=container_name,
            gateway_port=gateway_port,
            clawrouter_port=clawrouter_port,
            cpu_quota=cpu_quota,
            memory_quota=memory_quota,
            created_at=now,
            started_at=now if container_id else "",
            labels=labels or {}
        )
        
        self.deployments[agent_id] = status
        self._save_deployments()
        
        self.operation_logger.log_deploy(
            agent_id=agent_id,
            status="success",
            details=f"name={agent_name}, status={status.status}"
        )
        self.logger.info(f"部署注册成功: {agent_id}")
        
        return status
    
    def update_status(self, agent_id: str, **kwargs) -> Optional[DeploymentStatus]:
        """更新部署状态
        
        Args:
            agent_id: Agent ID
            **kwargs: 要更新的字段
        
        Returns:
            更新后的部署状态，不存在则返回None
        """
        if agent_id not in self.deployments:
            self.logger.warning(f"更新状态失败: 部署不存在 - {agent_id}")
            return None
        
        status = self.deployments[agent_id]
        changes = []
        for key, value in kwargs.items():
            if hasattr(status, key):
                old_value = getattr(status, key)
                setattr(status, key, value)
                changes.append(f"{key}: {old_value} -> {value}")
        
        if changes:
            self._save_deployments()
            self.logger.info(f"更新部署状态: {agent_id}, 变更项: {', '.join(changes)}")
        
        return status
    
    def get_deployment(self, agent_id: str) -> Optional[DeploymentStatus]:
        """获取部署状态
        
        Args:
            agent_id: Agent ID
        
        Returns:
            部署状态对象，不存在则返回None
        """
        return self.deployments.get(agent_id)
    
    def list_deployments(self) -> List[DeploymentStatus]:
        """获取所有部署状态
        
        Returns:
            部署状态列表
        """
        return list(self.deployments.values())
    
    def remove_deployment(self, agent_id: str) -> bool:
        """移除部署记录
        
        Args:
            agent_id: Agent ID
        
        Returns:
            是否成功移除
        """
        if agent_id in self.deployments:
            del self.deployments[agent_id]
            self._save_deployments()
            self.logger.info(f"移除部署记录: {agent_id}")
            return True
        return False


def main():
    # 测试代码
    manager = DeploymentManager()
    status = manager.register_deployment(
        agent_id="test-agent",
        agent_name="测试Agent",
        gateway_port=8080,
        clawrouter_port=8081
    )
    print(status)
    
    updated_status = manager.update_status(
        "test-agent",
        status="running",
        container_id="container-123"
    )
    print(updated_status)
    
    deployment = manager.get_deployment("test-agent")
    print(deployment)
    
    deployments = manager.list_deployments()
    for deploy in deployments:
        print(deploy)
    
    manager.remove_deployment("test-agent")


if __name__ == "__main__":
    main()
