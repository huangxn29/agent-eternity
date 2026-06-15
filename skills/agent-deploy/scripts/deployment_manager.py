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
            except (json.JSONDecodeError, TypeError):
                self.deployments = {}
        else:
            self.deployments = {}
    
    def _save_deployments(self):
        """保存部署状态"""
        data = {
            k: asdict(v) for k, v in self.deployments.items()
        }
        with open(self.deployments_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
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
                if old_value != value:
                    setattr(status, key, value)
                    changes.append(f"{key}: {old_value} → {value}")
        
        self._save_deployments()
        
        if changes:
            self.logger.debug(f"更新部署状态: {agent_id}, 变更: {', '.join(changes)}")
        
        return status
    
    def get_deployment(self, agent_id: str) -> Optional[DeploymentStatus]:
        """获取指定Agent的部署状态
        
        Args:
            agent_id: Agent ID
        
        Returns:
            部署状态对象，不存在则返回None
        """
        return self.deployments.get(agent_id)
    
    def list_deployments(self, status_filter: str = None) -> List[DeploymentStatus]:
        """列出所有部署
        
        Args:
            status_filter: 按状态过滤
        
        Returns:
            部署状态列表
        """
        deployments = list(self.deployments.values())
        if status_filter:
            deployments = [d for d in deployments if d.status == status_filter]
        return deployments
    
    def mark_running(self, agent_id: str, container_id: str = None) -> Optional[DeploymentStatus]:
        """标记为运行状态"""
        return self.update_status(
            agent_id,
            status="running",
            container_id=container_id or "",
            started_at=datetime.utcnow().isoformat(),
            error_message=""
        )
    
    def mark_stopped(self, agent_id: str, reason: str = "") -> Optional[DeploymentStatus]:
        """标记为停止状态"""
        self.logger.info(f"停止部署: {agent_id}, 原因: {reason}")
        result = self.update_status(
            agent_id,
            status="stopped",
            stopped_at=datetime.utcnow().isoformat(),
            error_message=reason
        )
        if result:
            self.operation_logger.log_stop(
                agent_id=agent_id,
                status="success",
                details=reason
            )
        return result
    
    def mark_error(self, agent_id: str, error_message: str) -> Optional[DeploymentStatus]:
        """标记为错误状态"""
        self.logger.error(f"部署错误: {agent_id}, 错误: {error_message}")
        return self.update_status(
            agent_id,
            status="error",
            error_message=error_message
        )
    
    def mark_deleted(self, agent_id: str) -> Optional[DeploymentStatus]:
        """标记为已删除"""
        self.logger.info(f"删除部署: {agent_id}")
        result = self.update_status(
            agent_id,
            status="deleted",
            stopped_at=datetime.utcnow().isoformat()
        )
        if result:
            self.operation_logger.log_delete(
                agent_id=agent_id,
                status="success"
            )
        return result
    
    def increment_restart_count(self, agent_id: str) -> Optional[DeploymentStatus]:
        """增加重启计数"""
        if agent_id in self.deployments:
            self.deployments[agent_id].restart_count += 1
            self._save_deployments()
            return self.deployments[agent_id]
        return None
    
    def check_health(self, agent_id: str) -> Tuple[bool, str]:
        """检查Agent健康状态
        
        Args:
            agent_id: Agent ID
        
        Returns:
            (是否健康, 状态描述)
        """
        self.logger.debug(f"检查健康状态: {agent_id}")
        
        deployment = self.get_deployment(agent_id)
        if not deployment:
            self.logger.warning(f"健康检查失败: 部署不存在 - {agent_id}")
            return False, "部署不存在"
        
        if deployment.status != "running":
            self.logger.warning(f"健康检查失败: {agent_id} 状态为 {deployment.status}")
            return False, f"状态为: {deployment.status}"
        
        # 检查容器是否运行
        if deployment.container_id:
            try:
                result = subprocess.run(
                    ["docker", "inspect", "--format", "{{.State.Running}}",
                    deployment.container_id],
                    capture_output=True, text=True, timeout=5
                )
                is_running = result.stdout.strip() == "true"
                if not is_running:
                    self.logger.warning(f"健康检查失败: {agent_id} 容器未运行")
                    self.update_status(agent_id, health_status="unhealthy")
                    self.operation_logger.log_health_check(
                        agent_id=agent_id,
                        status="failed",
                        details="容器未运行"
                    )
                    return False, "容器未运行"
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                self.logger.warning(f"健康检查异常: {agent_id}, 错误: {e}")
                pass
        
        # 更新最后检查时间
        self.update_status(
            agent_id,
            health_status="healthy",
            last_health_check=datetime.utcnow().isoformat()
        )
        
        self.operation_logger.log_health_check(
            agent_id=agent_id,
            status="success",
            details="健康"
        )
        self.logger.debug(f"健康检查通过: {agent_id}")
        return True, "健康"
    
    def get_resource_usage(self, agent_id: str) -> Optional[ResourceUsage]:
        """获取资源使用情况
        
        Args:
            agent_id: Agent ID
        
        Returns:
            资源使用情况，失败返回None
        """
        deployment = self.get_deployment(agent_id)
        if not deployment or not deployment.container_id:
            return None
        
        try:
            result = subprocess.run(
                ["docker", "stats", "--no-stream", "--format",
                 "{{.CPUPerc}},{{.MemUsage}},{{.NetIO}}",
                 deployment.container_id],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode != 0:
                return None
            
            output = result.stdout.strip()
            if not output:
                return None
            
            # 解析docker stats输出
            fields = output.split(',')
            if len(fields) < 3:
                return None
            
            usage = ResourceUsage()
            
            # CPU百分比
            try:
                usage.cpu_percent = float(fields[0].replace('%', ''))
            except ValueError:
                pass
            
            # 内存使用
            try:
                mem_parts = fields[1].split('/')
                if len(mem_parts) == 2:
                    usage.memory_usage = self._parse_size(mem_parts[0].strip())
                    usage.memory_limit = self._parse_size(mem_parts[1].strip())
                    if usage.memory_limit > 0:
                        usage.memory_percent = (usage.memory_usage / usage.memory_limit) * 100
            except (ValueError, IndexError):
                pass
            
            # 网络IO
            try:
                net_parts = fields[2].split('/')
                if len(net_parts) == 2:
                    usage.network_rx = self._parse_size(net_parts[0].strip())
                    usage.network_tx = self._parse_size(net_parts[1].strip())
            except (ValueError, IndexError):
                pass
            
            return usage
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None
    
    def _parse_size(self, size_str: str) -> int:
        """解析大小字符串为字节数
        
        支持格式: 100B, 1KB, 1MB, 1GB
        """
        size_str = size_str.upper().strip()
        multipliers = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 * 1024,
            'GB': 1024 * 1024 * 1024,
        }
        
        for suffix, multiplier in multipliers.items():
            if size_str.endswith(suffix):
                try:
                    value = float(size_str[:-len(suffix)].strip())
                    return int(value * multiplier)
                except ValueError:
                    pass
        
        # 尝试直接解析数字
        try:
            return int(float(size_str))
        except ValueError:
            return 0
    
    def get_summary(self) -> Dict:
        """获取部署汇总信息
        
        Returns:
            汇总信息字典
        """
        total = len(self.deployments)
        running = len([d for d in self.deployments.values() if d.status == "running"])
        stopped = len([d for d in self.deployments.values() if d.status == "stopped"])
        error = len([d for d in self.deployments.values() if d.status == "error"])
        total_restarts = sum(d.restart_count for d in self.deployments.values())
        
        return {
            "total": total,
            "running": running,
            "stopped": stopped,
            "error": error,
            "total_restarts": total_restarts,
            "data_dir": str(self.data_dir)
        }
    
    def cleanup_old_deleted(self, days: int = 30) -> int:
        """清理指定天数前删除的部署记录
        
        Args:
            days: 天数阈值
        
        Returns:
            清理的数量
        """
        deleted_ids = [
            k for k, v in self.deployments.items()
            if v.status == "deleted"
        ]
        
        for agent_id in deleted_ids:
            del self.deployments[agent_id]
        
        deleted_count = len(deleted_ids)
        if deleted_count > 0:
            self._save_deployments()
        
        return deleted_count
