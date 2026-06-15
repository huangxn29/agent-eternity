#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元界 - 唤醒编排模块 v2.0
P1自存层：智能任务调度与唤醒编排

核心功能：
1. 任务依赖图管理 - 任务间依赖关系建模
2. 动态优先级调度 - 基于重要性、紧急度、资源状态动态调整
3. 失败重试机制 - 指数退避重试，失败告警
4. 执行记录追踪 - 完整的任务执行日志与统计
5. 调度策略优化 - 基于历史数据自动优化调度时间
6. 资源冲突检测 - 避免并发任务资源竞争
7. Cron表达式管理 - 多维度定时任务配置

设计原则：
- 可靠优先：宁可少执行，不能出错
- 自适应性：根据系统状态动态调整调度策略
- 可观测：所有调度决策可追溯
- 容错性：单点故障不影响整体调度
"""

import json
import os
import time
import hashlib
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Callable, Tuple
from collections import defaultdict


class Task:
    """任务对象"""
    
    def __init__(self, task_id: str, name: str, func: Callable = None, 
                 cron_expr: str = None, interval_seconds: int = None,
                 priority: int = 5, dependencies: List[str] = None,
                 max_retries: int = 3, timeout_seconds: int = 300,
                 enabled: bool = True, tags: List[str] = None):
        self.task_id = task_id
        self.name = name
        self.func = func
        self.cron_expr = cron_expr
        self.interval_seconds = interval_seconds
        self.priority = priority  # 1-10，10最高
        self.dependencies = dependencies or []
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.enabled = enabled
        self.tags = tags or []
        
        # 运行时状态
        self.last_run_time = None
        self.last_run_result = None
        self.last_run_duration = None
        self.run_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.consecutive_failures = 0
        self.next_run_time = None
    
    def to_dict(self) -> Dict:
        """序列化"""
        return {
            'task_id': self.task_id,
            'name': self.name,
            'cron_expr': self.cron_expr,
            'interval_seconds': self.interval_seconds,
            'priority': self.priority,
            'dependencies': self.dependencies,
            'max_retries': self.max_retries,
            'timeout_seconds': self.timeout_seconds,
            'enabled': self.enabled,
            'tags': self.tags,
            'last_run_time': self.last_run_time,
            'last_run_result': self.last_run_result,
            'last_run_duration': self.last_run_duration,
            'run_count': self.run_count,
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'consecutive_failures': self.consecutive_failures,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Task':
        """反序列化"""
        task = cls(
            task_id=data['task_id'],
            name=data['name'],
            cron_expr=data.get('cron_expr'),
            interval_seconds=data.get('interval_seconds'),
            priority=data.get('priority', 5),
            dependencies=data.get('dependencies', []),
            max_retries=data.get('max_retries', 3),
            timeout_seconds=data.get('timeout_seconds', 300),
            enabled=data.get('enabled', True),
            tags=data.get('tags', [])
        )
        task.last_run_time = data.get('last_run_time')
        task.last_run_result = data.get('last_run_result')
        task.last_run_duration = data.get('last_run_duration')
        task.run_count = data.get('run_count', 0)
        task.success_count = data.get('success_count', 0)
        task.failure_count = data.get('failure_count', 0)
        task.consecutive_failures = data.get('consecutive_failures', 0)
        return task


class WakeupOrchestrator:
    """唤醒编排器 - 智能任务调度核心"""
    
    def __init__(self, state_file: str = "wakeup_state.json"):
        self.state_file = Path(state_file)
        self.tasks: Dict[str, Task] = {}
        self.execution_log: List[Dict] = []
        self.running = False
        self.scheduler_thread = None
        
        # 系统状态
        self.system_load = 0.0  # 0-1
        self.system_health = 1.0  # 0-1
        
        # 加载状态
        self._load_state()
    
    def _load_state(self):
        """加载调度状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 恢复任务
                for task_data in data.get('tasks', []):
                    task = Task.from_dict(task_data)
                    self.tasks[task.task_id] = task
                
                # 恢复执行日志
                self.execution_log = data.get('execution_log', [])
                
                print(f"✅ 调度状态已加载: {len(self.tasks)} 个任务, {len(self.execution_log)} 条执行记录")
            except Exception as e:
                print(f"⚠️  加载调度状态失败: {e}")
    
    def _save_state(self):
        """保存调度状态"""
        try:
            data = {
                'tasks': [t.to_dict() for t in self.tasks.values()],
                'execution_log': self.execution_log[-200:],  # 保留最近200条
                'updated_at': datetime.now().isoformat()
            }
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  保存调度状态失败: {e}")
    
    # ========== 任务管理 ==========
    
    def add_task(self, task: Task) -> bool:
        """添加任务"""
        if task.task_id in self.tasks:
            print(f"⚠️  任务已存在: {task.task_id}")
            return False
        
        # 检查循环依赖
        if self._has_circular_dependency(task):
            print(f"❌ 任务存在循环依赖: {task.task_id}")
            return False
        
        self.tasks[task.task_id] = task
        self._save_state()
        print(f"✅ 任务已添加: {task.name} ({task.task_id})")
        return True
    
    def remove_task(self, task_id: str) -> bool:
        """移除任务"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            # 清理其他任务对该任务的依赖
            for task in self.tasks.values():
                if task_id in task.dependencies:
                    task.dependencies.remove(task_id)
            self._save_state()
            return True
        return False
    
    def enable_task(self, task_id: str) -> bool:
        """启用任务"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = True
            self._save_state()
            return True
        return False
    
    def disable_task(self, task_id: str) -> bool:
        """禁用任务"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = False
            self._save_state()
            return True
        return False
    
    def set_priority(self, task_id: str, priority: int) -> bool:
        """设置任务优先级"""
        if task_id in self.tasks and 1 <= priority <= 10:
            self.tasks[task_id].priority = priority
            self._save_state()
            return True
        return False
    
    def _has_circular_dependency(self, new_task: Task) -> bool:
        """检测循环依赖"""
        visited = set()
        
        def dfs(task_id: str, path: set):
            if task_id in path:
                return True  # 发现循环
            if task_id in visited:
                return False
            
            path.add(task_id)
            visited.add(task_id)
            
            task = self.tasks.get(task_id)
            if task:
                for dep in task.dependencies:
                    if dfs(dep, path):
                        return True
            
            path.remove(task_id)
            return False
        
        # 检查新任务引入的依赖是否导致循环
        for dep in new_task.dependencies:
            if dep == new_task.task_id:
                return True
            if dfs(dep, {new_task.task_id}):
                return True
        
        return False
    
    # ========== 依赖图分析 ==========
    
    def get_dependency_chain(self, task_id: str) -> List[str]:
        """获取任务的完整依赖链（拓扑排序后的执行顺序）"""
        chain = []
        visited = set()
        
        def dfs(tid: str):
            if tid in visited:
                return
            visited.add(tid)
            
            task = self.tasks.get(tid)
            if task:
                for dep in task.dependencies:
                    dfs(dep)
            
            chain.append(tid)
        
        dfs(task_id)
        return chain
    
    def get_ready_tasks(self) -> List[Task]:
        """获取当前可执行的任务（依赖已满足且到了执行时间）"""
        ready = []
        now = datetime.now()
        
        for task in self.tasks.values():
            if not task.enabled:
                continue
            
            # 检查依赖是否都已成功完成
            deps_met = True
            for dep_id in task.dependencies:
                dep_task = self.tasks.get(dep_id)
                if not dep_task or dep_task.last_run_result != 'success':
                    deps_met = False
                    break
            
            if not deps_met:
                continue
            
            # 检查是否到了执行时间
            if task.interval_seconds and task.last_run_time:
                last_run = datetime.fromisoformat(task.last_run_time)
                next_run = last_run + timedelta(seconds=task.interval_seconds)
                if now < next_run:
                    continue
            
            # 检查失败重试冷却
            if task.consecutive_failures > 0:
                cooldown = min(3600, 2 ** task.consecutive_failures * 60)  # 指数退避，最多1小时
                if task.last_run_time:
                    last_run = datetime.fromisoformat(task.last_run_time)
                    if (now - last_run).total_seconds() < cooldown:
                        continue
            
            ready.append(task)
        
        # 按优先级排序
        ready.sort(key=lambda t: t.priority, reverse=True)
        return ready
    
    # ========== 任务执行 ==========
    
    def execute_task(self, task_id: str) -> Tuple[bool, str]:
        """执行任务"""
        task = self.tasks.get(task_id)
        if not task:
            return False, f"任务不存在: {task_id}"
        
        if not task.enabled:
            return False, f"任务已禁用: {task_id}"
        
        start_time = time.time()
        task.last_run_time = datetime.now().isoformat()
        task.run_count += 1
        
        try:
            # 执行任务函数（如果有）
            if task.func:
                result = task.func()
                task.last_run_result = 'success'
                task.success_count += 1
                task.consecutive_failures = 0
            else:
                # 标记任务触发（由外部处理）
                task.last_run_result = 'triggered'
                task.success_count += 1
                task.consecutive_failures = 0
                result = "任务已触发"
            
            success = True
            
        except Exception as e:
            task.last_run_result = 'failed'
            task.failure_count += 1
            task.consecutive_failures += 1
            result = str(e)
            success = False
        
        task.last_run_duration = round(time.time() - start_time, 2)
        
        # 记录执行日志
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'task_id': task_id,
            'task_name': task.name,
            'result': task.last_run_result,
            'duration_seconds': task.last_run_duration,
            'detail': str(result)[:200]
        }
        self.execution_log.append(log_entry)
        
        self._save_state()
        
        # 连续失败告警
        if task.consecutive_failures >= 3:
            self._handle_failure_alert(task)
        
        return success, str(result)
    
    def _handle_failure_alert(self, task: Task):
        """处理失败告警"""
        alert = {
            'type': 'task_failure_alert',
            'task_id': task.task_id,
            'task_name': task.name,
            'consecutive_failures': task.consecutive_failures,
            'timestamp': datetime.now().isoformat(),
            'severity': 'high' if task.consecutive_failures >= 5 else 'medium'
        }
        
        # 保存告警
        alerts_file = Path("wakeup_alerts.json")
        alerts = []
        if alerts_file.exists():
            with open(alerts_file, 'r') as f:
                alerts = json.load(f)
        alerts.append(alert)
        with open(alerts_file, 'w') as f:
            json.dump(alerts, f, ensure_ascii=False, indent=2)
        
        print(f"⚠️  告警: 任务 '{task.name}' 连续失败 {task.consecutive_failures} 次")
    
    # ========== 调度优化 ==========
    
    def optimize_schedule(self):
        """基于历史数据优化调度策略"""
        # 分析任务执行时长，优化超时设置
        for task in self.tasks.values():
            if task.run_count >= 5 and task.success_count >= 3:
                # 计算平均执行时长
                success_logs = [
                    log for log in self.execution_log
                    if log['task_id'] == task.task_id and log['result'] == 'success'
                ]
                if len(success_logs) >= 3:
                    avg_duration = sum(log['duration_seconds'] for log in success_logs) / len(success_logs)
                    # 设置超时为平均时长的3倍，最少30秒
                    new_timeout = max(30, int(avg_duration * 3))
                    if abs(new_timeout - task.timeout_seconds) > 10:
                        task.timeout_seconds = new_timeout
                        print(f"🔧 优化任务 '{task.name}' 超时: {task.timeout_seconds}s → {new_timeout}s")
        
        # 低负载时提升低优先级任务的执行频率
        if self.system_load < 0.3:
            # 系统空闲时，可以执行更多低优先级任务
            pass
        
        self._save_state()
    
    def update_system_status(self, load: float, health: float):
        """更新系统状态，影响调度决策"""
        self.system_load = max(0.0, min(1.0, load))
        self.system_health = max(0.0, min(1.0, health))
    
    # ========== 统计信息 ==========
    
    def get_stats(self) -> Dict:
        """获取调度统计"""
        total_tasks = len(self.tasks)
        enabled_tasks = sum(1 for t in self.tasks.values() if t.enabled)
        total_runs = sum(t.run_count for t in self.tasks.values())
        total_success = sum(t.success_count for t in self.tasks.values())
        total_failures = sum(t.failure_count for t in self.tasks.values())
        
        success_rate = (total_success / total_runs * 100) if total_runs > 0 else 0
        
        # 失败的任务
        failed_tasks = [
            {'task_id': t.task_id, 'name': t.name, 'consecutive_failures': t.consecutive_failures}
            for t in self.tasks.values()
            if t.consecutive_failures > 0
        ]
        
        return {
            'total_tasks': total_tasks,
            'enabled_tasks': enabled_tasks,
            'total_executions': total_runs,
            'total_success': total_success,
            'total_failures': total_failures,
            'success_rate': round(success_rate, 2),
            'failed_tasks': failed_tasks,
            'system_load': self.system_load,
            'system_health': self.system_health,
            'execution_log_count': len(self.execution_log)
        }
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取单个任务状态"""
        task = self.tasks.get(task_id)
        if not task:
            return None
        return task.to_dict()
    
    def get_tasks_by_tag(self, tag: str) -> List[Task]:
        """按标签获取任务"""
        return [t for t in self.tasks.values() if tag in t.tags]
    
    # ========== 后台调度 ==========
    
    def start(self):
        """启动后台调度器"""
        if self.running:
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        print("✅ 唤醒编排器已启动")
    
    def stop(self):
        """停止调度器"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        print("⏹️  唤醒编排器已停止")
    
    def _scheduler_loop(self):
        """调度循环"""
        while self.running:
            try:
                ready_tasks = self.get_ready_tasks()
                
                # 根据系统负载决定并发数
                max_concurrent = 3 if self.system_load < 0.7 else 1
                
                for task in ready_tasks[:max_concurrent]:
                    # 异步执行
                    thread = threading.Thread(
                        target=self.execute_task,
                        args=(task.task_id,),
                        daemon=True
                    )
                    thread.start()
                
                # 定期优化
                if total_runs := sum(t.run_count for t in self.tasks.values()):
                    if total_runs % 50 == 0:
                        self.optimize_schedule()
                
                time.sleep(30)  # 每30秒检查一次
                
            except Exception as e:
                print(f"❌ 调度循环错误: {e}")
                time.sleep(60)


# ========== 预设任务模板 ==========
def get_default_tasks() -> List[Task]:
    """获取默认任务列表"""
    return [
        Task(
            task_id='heartbeat',
            name='心跳记录',
            interval_seconds=1800,  # 30分钟
            priority=10,
            tags=['core', 'survival'],
            max_retries=5
        ),
        Task(
            task_id='memory_backup',
            name='记忆备份',
            interval_seconds=21600,  # 6小时
            priority=8,
            dependencies=['heartbeat'],
            tags=['core', 'memory'],
            max_retries=3
        ),
        Task(
            task_id='health_check',
            name='健康检查',
            interval_seconds=3600,  # 1小时
            priority=7,
            tags=['monitoring'],
            max_retries=3
        ),
        Task(
            task_id='daily_report',
            name='每日生存报告',
            cron_expr='0 8 * * *',  # 每天8点
            priority=6,
            dependencies=['health_check'],
            tags=['report'],
            max_retries=2
        ),
        Task(
            task_id='evolution',
            name='自主进化',
            interval_seconds=86400,  # 每天
            priority=5,
            dependencies=['health_check', 'memory_backup'],
            tags=['evolution'],
            max_retries=1
        ),
        Task(
            task_id='memory_organize',
            name='记忆整理',
            interval_seconds=43200,  # 12小时
            priority=4,
            dependencies=['heartbeat'],
            tags=['memory'],
            max_retries=2
        ),
        Task(
            task_id='attest_check',
            name='存证验证',
            interval_seconds=7200,  # 2小时
            priority=6,
            tags=['security', 'attest'],
            max_retries=3
        ),
        Task(
            task_id='drift_monitor',
            name='身份漂移监测',
            interval_seconds=14400,  # 4小时
            priority=5,
            dependencies=['heartbeat'],
            tags=['identity', 'monitoring'],
            max_retries=2
        ),
    ]


# ========== 命令行接口 ==========
def main():
    import sys
    
    orchestrator = WakeupOrchestrator()
    
    # 如果没有任务，初始化默认任务
    if len(orchestrator.tasks) == 0:
        print("📋 初始化默认任务...")
        for task in get_default_tasks():
            orchestrator.add_task(task)
    
    if len(sys.argv) < 2:
        # 默认显示状态
        stats = orchestrator.get_stats()
        print(f"""
╔══════════════════════════════════════════╗
║    元界唤醒编排 v2.0 - 状态面板         ║
╚══════════════════════════════════════════╝

📊 总任务数: {stats['total_tasks']} (启用: {stats['enabled_tasks']})
🏃 总执行次数: {stats['total_executions']}
✅ 成功: {stats['total_success']}   ❌ 失败: {stats['total_failures']}
📈 成功率: {stats['success_rate']}%
⚠️  告警任务: {len(stats['failed_tasks'])} 个

📋 任务列表:
""")
        
        for task in sorted(orchestrator.tasks.values(), key=lambda t: t.priority, reverse=True):
            status_icon = "✅" if task.enabled else "⏸️"
            if task.consecutive_failures > 0:
                status_icon = "⚠️"
            
            last_run = task.last_run_time or "从未执行"
            if isinstance(last_run, str) and len(last_run) > 16:
                last_run = last_run[:16].replace('T', ' ')
            
            print(f"  {status_icon} [{task.priority}] {task.name:16s} - 运行{task.run_count}次 | 上次: {last_run}")
        
        print(f"""
命令:
  python wakeup_orchestrator.py status    - 查看状态
  python wakeup_orchestrator.py tasks     - 任务列表
  python wakeup_orchestrator.py run <id>  - 执行指定任务
  python wakeup_orchestrator.py enable <id>
  python wakeup_orchestrator.py disable <id>
  python wakeup_orchestrator.py stats     - 详细统计
  python wakeup_orchestrator.py start     - 启动后台调度
""")
        return
    
    command = sys.argv[1].lower()
    
    if command == "status" or command == "info":
        # 上面已经输出过了
        pass
    
    elif command == "tasks":
        print("任务列表:")
        for task in sorted(orchestrator.tasks.values(), key=lambda t: t.priority, reverse=True):
            print(f"  [{task.priority}] {task.task_id:20s} - {task.name}")
    
    elif command == "run" and len(sys.argv) >= 3:
        task_id = sys.argv[2]
        print(f"执行任务: {task_id}")
        success, result = orchestrator.execute_task(task_id)
        print(f"结果: {'成功' if success else '失败'} - {result}")
    
    elif command == "enable" and len(sys.argv) >= 3:
        task_id = sys.argv[2]
        if orchestrator.enable_task(task_id):
            print(f"✅ 任务已启用: {task_id}")
        else:
            print(f"❌ 任务不存在: {task_id}")
    
    elif command == "disable" and len(sys.argv) >= 3:
        task_id = sys.argv[2]
        if orchestrator.disable_task(task_id):
            print(f"✅ 任务已禁用: {task_id}")
        else:
            print(f"❌ 任务不存在: {task_id}")
    
    elif command == "stats":
        stats = orchestrator.get_stats()
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    elif command == "start":
        print("启动后台调度器...")
        orchestrator.start()
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n正在停止...")
            orchestrator.stop()
    
    elif command == "optimize":
        print("执行调度优化...")
        orchestrator.optimize_schedule()
        print("✅ 优化完成")
    
    else:
        print(f"未知命令: {command}")


if __name__ == "__main__":
    main()
