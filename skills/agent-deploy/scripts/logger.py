#!/usr/bin/env python3
"""
日志系统模块
提供统一的日志管理，支持多级别输出、文件记录、格式化输出和日志轮转。
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional
from datetime import datetime


class DeployLogger:
    """部署日志管理器
    
    提供统一的日志接口，支持控制台输出和文件记录，
    支持日志级别控制和自动轮转。
    """
    
    _loggers = {}
    
    def __init__(
        self,
        name: str = "agent-deploy",
        log_level: str = "INFO",
        log_dir: Optional[str] = None,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        console_output: bool = True
    ):
        """初始化日志管理器
        
        Args:
            name: 日志记录器名称
            log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: 日志文件目录，为None时不写入文件
            max_file_size: 单个日志文件最大大小（字节）
            backup_count: 日志文件备份数量
            console_output: 是否输出到控制台
        """
        self.name = name
        self.log_level = self._parse_level(log_level)
        self.log_dir = Path(log_dir) if log_dir else None
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.console_output = console_output
        
        # 创建logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.log_level)
        self.logger.propagate = False
        
        # 避免重复添加handler
        if self.logger.handlers:
            return
        
        # 日志格式
        self.formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台输出
        if console_output:
            self._setup_console_handler()
        
        # 文件输出
        if self.log_dir:
            self._setup_file_handler()
    
    def _parse_level(self, level_str: str) -> int:
        """解析日志级别字符串"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL,
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'critical': logging.CRITICAL,
        }
        return level_map.get(level_str, logging.INFO)
    
    def _setup_console_handler(self):
        """设置控制台输出处理器"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(self.formatter)
        self.logger.addHandler(console_handler)
    
    def _setup_file_handler(self):
        """设置文件输出处理器"""
        if not self.log_dir:
            return
        
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            log_file = self.log_dir / f"{self.name}.log"
            
            file_handler = RotatingFileHandler(
                str(log_file),
                maxBytes=self.max_file_size,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(self.formatter)
            self.logger.addHandler(file_handler)
        except Exception as e:
            print(f"警告: 无法创建日志文件: {e}", file=sys.stderr)
    
    def debug(self, message: str, *args, **kwargs):
        """记录DEBUG级别日志"""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """记录INFO级别日志"""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """记录WARNING级别日志"""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """记录ERROR级别日志"""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """记录CRITICAL级别日志"""
        self.logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """记录异常信息（ERROR级别 + 堆栈跟踪）"""
        self.logger.exception(message, *args, **kwargs)
    
    def set_level(self, level: str):
        """设置日志级别"""
        self.log_level = self._parse_level(level)
        self.logger.setLevel(self.log_level)
        for handler in self.logger.handlers:
            handler.setLevel(self.log_level)
    
    def get_logger(self) -> logging.Logger:
        """获取原始logger对象"""
        return self.logger


def get_logger(
    name: str = "agent-deploy",
    log_level: str = "INFO",
    log_dir: Optional[str] = None,
    **kwargs
) -> DeployLogger:
    """获取日志记录器（工厂函数）
    
    Args:
        name: 日志记录器名称
        log_level: 日志级别
        log_dir: 日志目录
        **kwargs: 其他参数传递给DeployLogger
    
    Returns:
        DeployLogger实例
    """
    if name not in DeployLogger._loggers:
        DeployLogger._loggers[name] = DeployLogger(
            name=name,
            log_level=log_level,
            log_dir=log_dir,
            **kwargs
        )
    return DeployLogger._loggers[name]


class OperationLogger:
    """操作日志记录器
    
    专门用于记录部署操作的审计日志，
    包含操作人、操作类型、操作时间、操作结果等信息。
    """
    
    def __init__(self, log_dir: str, operator: str = "system"):
        """初始化操作日志记录器
        
        Args:
            log_dir: 日志目录
            operator: 操作人
        """
        self.operator = operator
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "operations.log"
    
    def log_operation(
        self,
        operation: str,
        target: str = "",
        status: str = "success",
        details: str = "",
        duration: float = 0.0
    ):
        """记录操作日志
        
        Args:
            operation: 操作类型（如 deploy, stop, delete, health_check）
            target: 操作目标（如 agent_id）
            status: 操作状态（success, failed, warning）
            details: 详细信息
            duration: 操作耗时（秒）
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = (
            f"[{timestamp}] | {status.upper():8s} | "
            f"operator={self.operator} | operation={operation}"
        )
        
        if target:
            log_entry += f" | target={target}"
        
        if duration > 0:
            log_entry += f" | duration={duration:.3f}s"
        
        if details:
            log_entry += f" | details={details}"
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry + '\n')
        except Exception as e:
            print(f"警告: 无法写入操作日志: {e}", file=sys.stderr)
    
    def log_deploy(self, agent_id: str, status: str = "success", details: str = ""):
        """记录部署操作"""
        self.log_operation("deploy", agent_id, status, details)
    
    def log_stop(self, agent_id: str, status: str = "success", details: str = ""):
        """记录停止操作"""
        self.log_operation("stop", agent_id, status, details)
    
    def log_delete(self, agent_id: str, status: str = "success", details: str = ""):
        """记录删除操作"""
        self.log_operation("delete", agent_id, status, details)
    
    def log_health_check(self, agent_id: str, status: str = "success", details: str = ""):
        """记录健康检查操作"""
        self.log_operation("health_check", agent_id, status, details)
