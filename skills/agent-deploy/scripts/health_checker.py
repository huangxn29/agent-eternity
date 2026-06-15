#!/usr/bin/env python3
"""
健康检查模块
提供多种健康检查方式，确保Agent正常运行。
支持端口检查、进程检查、API响应检查等。
"""

import os
import time
import socket
import subprocess
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from logger import get_logger


class HealthStatus(str, Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    check_name: str
    status: HealthStatus
    message: str = ""
    response_time_ms: float = 0.0
    details: Dict = field(default_factory=dict)
    checked_at: str = ""


@dataclass
class HealthReport:
    """综合健康报告"""
    overall_status: HealthStatus
    checks: List[HealthCheckResult] = field(default_factory=list)
    generated_at: str = ""
    agent_id: str = ""
    
    def add_check(self, check: HealthCheckResult):
        """添加检查结果"""
        self.checks.append(check)
        self._update_overall_status()
    
    def _update_overall_status(self):
        """更新整体状态"""
        if not self.checks:
            self.overall_status = HealthStatus.UNKNOWN
            return
        
        statuses = [c.status for c in self.checks]
        
        if all(s == HealthStatus.HEALTHY for s in statuses):
            self.overall_status = HealthStatus.HEALTHY
        elif HealthStatus.UNHEALTHY in statuses:
            self.overall_status = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            self.overall_status = HealthStatus.DEGRADED
        else:
            self.overall_status = HealthStatus.UNKNOWN


class HealthChecker:
    """健康检查器
    
    提供多种健康检查方法，用于监控Agent运行状态。
    """
    
    def __init__(self, agent_id: str = "", timeout: int = 5, log_level: str = "INFO"):
        """初始化健康检查器
        
        Args:
            agent_id: Agent ID
            timeout: 超时时间（秒）
            log_level: 日志级别
        """
        self.agent_id = agent_id
        self.timeout = timeout
        self.logger = get_logger(
            name=f"health-checker-{agent_id or 'default'}",
            log_level=log_level
        )
    
    def check_port(self, host: str, port: int, service_name: str = "") -> HealthCheckResult:
        """检查端口是否可访问
        
        Args:
            host: 主机地址
            port: 端口号
            service_name: 服务名称
        
        Returns:
            健康检查结果
        """
        start_time = time.time()
        name = service_name or f"port_{port}"
        self.logger.debug(f"开始端口检查: {host}:{port} ({name})")
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            
            elapsed = (time.time() - start_time) * 1000
            
            if result == 0:
                self.logger.debug(f"端口检查通过: {host}:{port} ({elapsed:.1f}ms)")
                return HealthCheckResult(
                    check_name=name,
                    status=HealthStatus.HEALTHY,
                    message=f"端口 {port} 可访问",
                    response_time_ms=elapsed,
                    checked_at=datetime.utcnow().isoformat()
                )
            else:
                self.logger.warning(f"端口检查失败: {host}:{port} 不可访问")
                return HealthCheckResult(
                    check_name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"端口 {port} 不可访问",
                    response_time_ms=elapsed,
                    checked_at=datetime.utcnow().isoformat()
                )
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            self.logger.error(f"端口检查异常: {host}:{port}, 错误: {e}")
            return HealthCheckResult(
                check_name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"端口检查异常: {str(e)}",
                response_time_ms=elapsed,
                checked_at=datetime.utcnow().isoformat()
            )
    
    def check_process(self, container_name: str = "", process_name: str = "") -> HealthCheckResult:
        """检查进程是否运行
        
        Args:
            container_name: 容器名称
            process_name: 进程名称
        
        Returns:
            健康检查结果
        """
        start_time = time.time()
        
        try:
            if container_name:
                # 检查容器是否运行
                result = subprocess.run(
                    ["docker", "inspect", "--format", "{{.State.Running}}", container_name],
                    capture_output=True, text=True, timeout=self.timeout
                )
                
                elapsed = (time.time() - start_time) * 1000
                is_running = result.stdout.strip() == "true"
                
                if is_running:
                    return HealthCheckResult(
                        check_name=f"container_{container_name}",
                        status=HealthStatus.HEALTHY,
                        message=f"容器 {container_name} 正在运行",
                        response_time_ms=elapsed,
                        checked_at=datetime.utcnow().isoformat()
                    )
                else:
                    return HealthCheckResult(
                        check_name=f"container_{container_name}",
                        status=HealthStatus.UNHEALTHY,
                        message=f"容器 {container_name} 未运行",
                        response_time_ms=elapsed,
                        checked_at=datetime.utcnow().isoformat()
                    )
            elif process_name:
                # 检查宿主机进程
                result = subprocess.run(
                    ["pgrep", "-f", process_name],
                    capture_output=True, text=True, timeout=self.timeout
                )
                
                elapsed = (time.time() - start_time) * 1000
                
                if result.returncode == 0:
                    pids = result.stdout.strip().split('\n')
                    return HealthCheckResult(
                        check_name=f"process_{process_name}",
                        status=HealthStatus.HEALTHY,
                        message=f"进程 {process_name} 正在运行，PID数: {len(pids)}",
                        response_time_ms=elapsed,
                        details={"pid_count": len(pids)},
                        checked_at=datetime.utcnow().isoformat()
                    )
                else:
                    return HealthCheckResult(
                        check_name=f"process_{process_name}",
                        status=HealthStatus.UNHEALTHY,
                        message=f"进程 {process_name} 未运行",
                        response_time_ms=elapsed,
                        checked_at=datetime.utcnow().isoformat()
                    )
            
            elapsed = (time.time() - start_time) * 1000
            return HealthCheckResult(
                check_name="process",
                status=HealthStatus.UNKNOWN,
                message="未指定检查目标",
                response_time_ms=elapsed,
                checked_at=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            return HealthCheckResult(
                check_name=f"process_{container_name or process_name}",
                status=HealthStatus.UNHEALTHY,
                message=f"进程检查异常: {str(e)}",
                response_time_ms=elapsed,
                checked_at=datetime.utcnow().isoformat()
            )
    
    def check_http_endpoint(self, url: str, method: str = "GET", 
                           expected_status: int = 200) -> HealthCheckResult:
        """检查HTTP端点响应
        
        Args:
            url: URL地址
            method: HTTP方法
            expected_status: 期望的状态码
        
        Returns:
            健康检查结果
        """
        start_time = time.time()
        
        try:
            import urllib.request
            req = urllib.request.Request(url, method=method)
            
            try:
                response = urllib.request.urlopen(req, timeout=self.timeout)
                elapsed = (time.time() - start_time) * 1000
                
                if response.status == expected_status:
                    return HealthCheckResult(
                        check_name=f"http_{url[:50]}",
                        status=HealthStatus.HEALTHY,
                        message=f"HTTP {method} {url} 返回 {response.status}",
                        response_time_ms=elapsed,
                        details={"status_code": response.status},
                        checked_at=datetime.utcnow().isoformat()
                    )
                else:
                    return HealthCheckResult(
                        check_name=f"http_{url[:50]}",
                        status=HealthStatus.DEGRADED,
                        message=f"HTTP {method} {url} 返回 {response.status}，期望 {expected_status}",
                        response_time_ms=elapsed,
                        details={"status_code": response.status},
                        checked_at=datetime.utcnow().isoformat()
                    )
            except Exception as e:
                elapsed = (time.time() - start_time) * 1000
                return HealthCheckResult(
                    check_name=f"http_{url[:50]}",
                    status=HealthStatus.UNHEALTHY,
                    message=f"HTTP请求失败: {str(e)}",
                    response_time_ms=elapsed,
                    checked_at=datetime.utcnow().isoformat()
                )
        except ImportError:
            elapsed = (time.time() - start_time) * 1000
            return HealthCheckResult(
                check_name=f"http_{url[:50]}",
                status=HealthStatus.UNKNOWN,
                message="无法导入urllib",
                response_time_ms=elapsed,
                checked_at=datetime.utcnow().isoformat()
            )
    
    def check_disk_space(self, path: str = "/", min_free_gb: float = 1.0) -> HealthCheckResult:
        """检查磁盘空间
        
        Args:
            path: 检查路径
            min_free_gb: 最小可用空间（GB）
        
        Returns:
            健康检查结果
        """
        start_time = time.time()
        
        try:
            stat = os.statvfs(path)
            free_bytes = stat.f_frsize * stat.f_bavail
            free_gb = free_bytes / (1024 ** 3)
            total_gb = (stat.f_frsize * stat.f_blocks) / (1024 ** 3)
            
            elapsed = (time.time() - start_time) * 1000
            
            if free_gb >= min_free_gb:
                return HealthCheckResult(
                    check_name=f"disk_{path}",
                    status=HealthStatus.HEALTHY,
                    message=f"磁盘空间充足: {free_gb:.2f}GB / {total_gb:.2f}GB",
                    response_time_ms=elapsed,
                    details={
                        "free_gb": round(free_gb, 2),
                        "total_gb": round(total_gb, 2),
                        "free_percent": round(free_gb / total_gb * 100, 2) if total_gb > 0 else 0
                    },
                    checked_at=datetime.utcnow().isoformat()
                )
            else:
                return HealthCheckResult(
                    check_name=f"disk_{path}",
                    status=HealthStatus.UNHEALTHY,
                    message=f"磁盘空间不足: {free_gb:.2f}GB，至少需要 {min_free_gb}GB",
                    response_time_ms=elapsed,
                    details={
                        "free_gb": round(free_gb, 2),
                        "total_gb": round(total_gb, 2),
                        "min_required_gb": min_free_gb
                    },
                    checked_at=datetime.utcnow().isoformat()
                )
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            return HealthCheckResult(
                check_name=f"disk_{path}",
                status=HealthStatus.UNKNOWN,
                message=f"磁盘检查异常: {str(e)}",
                response_time_ms=elapsed,
                checked_at=datetime.utcnow().isoformat()
            )
    
    def check_file_exists(self, file_path: str, description: str = "") -> HealthCheckResult:
        """检查文件是否存在
        
        Args:
            file_path: 文件路径
            description: 文件描述
        
        Returns:
            健康检查结果
        """
        start_time = time.time()
        
        try:
            exists = os.path.exists(file_path)
            elapsed = (time.time() - start_time) * 1000
            
            if exists:
                file_size = os.path.getsize(file_path) if os.path.isfile(file_path) else 0
                return HealthCheckResult(
                    check_name=description or f"file_{os.path.basename(file_path)}",
                    status=HealthStatus.HEALTHY,
                    message=f"文件存在: {file_path}",
                    response_time_ms=elapsed,
                    details={"size_bytes": file_size},
                    checked_at=datetime.utcnow().isoformat()
                )
            else:
                return HealthCheckResult(
                    check_name=description or f"file_{os.path.basename(file_path)}",
                    status=HealthStatus.UNHEALTHY,
                    message=f"文件不存在: {file_path}",
                    response_time_ms=elapsed,
                    checked_at=datetime.utcnow().isoformat()
                )
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            return HealthCheckResult(
                check_name=description or f"file_{file_path}",
                status=HealthStatus.UNKNOWN,
                message=f"文件检查异常: {str(e)}",
                response_time_ms=elapsed,
                checked_at=datetime.utcnow().isoformat()
            )
    
    def run_full_check(self, checks: List[dict]) -> HealthReport:
        """运行完整的健康检查
        
        Args:
            checks: 检查配置列表，每项包含type和对应的参数
        
        Returns:
            综合健康报告
        """
        report = HealthReport(
            overall_status=HealthStatus.UNKNOWN,
            agent_id=self.agent_id,
            generated_at=datetime.utcnow().isoformat()
        )
        
        for check_config in checks:
            check_type = check_config.get("type", "")
            
            if check_type == "port":
                result = self.check_port(
                    host=check_config.get("host", "localhost"),
                    port=check_config.get("port", 0),
                    service_name=check_config.get("name", "")
                )
            elif check_type == "process":
                result = self.check_process(
                    container_name=check_config.get("container", ""),
                    process_name=check_config.get("process", "")
                )
            elif check_type == "http":
                result = self.check_http_endpoint(
                    url=check_config.get("url", ""),
                    method=check_config.get("method", "GET"),
                    expected_status=check_config.get("expected_status", 200)
                )
            elif check_type == "disk":
                result = self.check_disk_space(
                    path=check_config.get("path", "/"),
                    min_free_gb=check_config.get("min_free_gb", 1.0)
                )
            elif check_type == "file":
                result = self.check_file_exists(
                    file_path=check_config.get("path", ""),
                    description=check_config.get("name", "")
                )
            else:
                result = HealthCheckResult(
                    check_name=f"unknown_{check_type}",
                    status=HealthStatus.UNKNOWN,
                    message=f"未知的检查类型: {check_type}",
                    checked_at=datetime.utcnow().isoformat()
                )
            
            report.add_check(result)
        
        return report
