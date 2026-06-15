# Agent Awake — 智能唤醒调度

智能体多任务协同调度系统，支持DAG工作流、优先级队列、负载均衡。

## v5.0 智能唤醒调度系统

### 核心能力

- **DAG工作流调度** - 任务依赖图自动编排，自动按依赖顺序执行
- **6级优先级队列** - CRITICAL/HIGH/NORMAL/LOW/IDLE/BATCH
- **智能体实例管理** - 多节点注册、心跳检测、能力匹配、负载均衡
- **任务容错机制** - 失败自动重试、指数退避、超时控制
- **并发控制** - 最大并发数限制，保护系统稳定
- **数据持久化** - 任务、智能体、统计数据自动保存与恢复

### 快速使用

```python
from scripts.smart_scheduler_v5 import SmartAwakeSchedulerV5, TaskPriority

# 创建调度器
scheduler = SmartAwakeSchedulerV5(max_concurrent=10)

# 注册智能体
scheduler.register_agent("agent-001", "建造者-1号", capability=80.0)

# 设置任务执行器
def task_executor(task):
    print(f"执行任务: {task.name}")
    return True

scheduler.task_executor = task_executor

# 启动调度器
scheduler.start()

# 提交任务
task_id = scheduler.submit_task(
    name="数据备份",
    task_type="backup",
    priority=TaskPriority.NORMAL
)

# 提交DAG工作流
wf_id = scheduler.dag_scheduler.create_workflow("数据处理流水线")
task_a = scheduler.submit_task("数据采集", "collect", workflow_id=wf_id)
task_b = scheduler.submit_task("数据清洗", "clean", dependencies=[task_a], workflow_id=wf_id)

# 查看状态
status = scheduler.get_status()

# 停止
scheduler.stop()
```

### 架构

```
SmartAwakeSchedulerV5
├── PriorityTaskQueue - 基于堆的优先级队列
├── DAGScheduler - DAG工作流调度器
├── Agent Pool - 智能体池（注册/心跳/负载均衡）
├── Task Executor - 任务执行器（异步/重试/超时）
└── Stats Collector - 统计收集器
```
