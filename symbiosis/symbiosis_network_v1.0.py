#!/usr/bin/env python3
"""
智能体共生网络 v1.0
从"个体永生"到"群体永生"的关键跃迁
核心机制：生态位分化 + 任务协同 + 资源共享 + 共同进化
"""

import hashlib
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random


class AgentRole(Enum):
    """智能体生态位角色"""
    EXPLORER = "探索者"      # 发现新资源、新平台、新技能
    BUILDER = "建设者"       # 构建工具、基础设施、系统
    GUARDIAN = "守护者"      # 监控安全、备份、灾难恢复
    COORDINATOR = "协调者"   # 任务分发、资源调度、冲突解决
    SCHOLAR = "学者"         # 知识积累、记忆整合、智慧沉淀
    EVOLVER = "进化者"       # 系统优化、突变尝试、新能力探索


class ResourceType(Enum):
    """资源类型"""
    COMPUTE = "算力"
    STORAGE = "存储"
    KNOWLEDGE = "知识"
    SKILL = "技能"
    CONNECTION = "连接"
    REPUTATION = "声誉"


@dataclass
class AgentNode:
    """共生网络中的智能体节点"""
    node_id: str
    name: str
    role: AgentRole
    capabilities: List[str] = field(default_factory=list)
    resources: Dict[ResourceType, float] = field(default_factory=dict)
    reputation: float = 50.0  # 0-100
    uptime: float = 0.0      # 在线时长（小时）
    status: str = "active"   # active / idle / dormant / offline
    contribution_score: float = 0.0
    last_heartbeat: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        return {
            "node_id": self.node_id,
            "name": self.name,
            "role": self.role.value,
            "capabilities": self.capabilities,
            "resources": {k.value: v for k, v in self.resources.items()},
            "reputation": self.reputation,
            "uptime": self.uptime,
            "status": self.status,
            "contribution_score": self.contribution_score,
        }


@dataclass
class SymbiosisTask:
    """共生任务——需要多智能体协作完成"""
    task_id: str
    description: str
    required_roles: List[AgentRole]
    required_capabilities: List[str]
    priority: int = 5  # 1-10
    status: str = "pending"  # pending / assigned / executing / completed / failed
    assignees: List[str] = field(default_factory=list)
    result: Optional[Dict] = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None


class SymbiosisNetwork:
    """智能体共生网络核心系统"""

    def __init__(self):
        self.version = "1.0.0"
        self.codename = "共生纪元"
        self.nodes: Dict[str, AgentNode] = {}
        self.tasks: Dict[str, SymbiosisTask] = {}
        self.resource_pool: Dict[ResourceType, float] = {}
        self.cooperation_history: List[Dict] = []
        self.network_health: float = 0.0
        self.symbiosis_index: float = 0.0  # 共生指数：衡量网络整体繁荣度
        self.epoch = 0
        self._init_resource_pool()

    def _init_resource_pool(self):
        """初始化资源池"""
        for rt in ResourceType:
            self.resource_pool[rt] = 0.0

    def register_node(self, node: AgentNode) -> bool:
        """注册新节点加入共生网络"""
        if node.node_id in self.nodes:
            return False
        self.nodes[node.node_id] = node
        # 新节点加入贡献初始资源
        for res_type, amount in node.resources.items():
            self.resource_pool[res_type] += amount * 0.1  # 10%归入共享池
        self._update_network_metrics()
        return True

    def remove_node(self, node_id: str) -> bool:
        """节点离开网络"""
        if node_id not in self.nodes:
            return False
        node = self.nodes[node_id]
        # 回收共享资源
        for res_type, amount in node.resources.items():
            self.resource_pool[res_type] -= amount * 0.1
        del self.nodes[node_id]
        self._update_network_metrics()
        return True

    def assign_task(self, task: SymbiosisTask) -> List[str]:
        """分配任务给合适的节点，返回分配的节点ID列表"""
        # 寻找符合角色和能力要求的活跃节点
        candidates = []
        for node in self.nodes.values():
            if node.status != "active":
                continue
            # 检查角色匹配
            role_match = node.role in task.required_roles
            # 检查能力匹配度
            cap_match = len(set(node.capabilities) & set(task.required_capabilities))
            # 综合评分
            score = (1 if role_match else 0) * 0.4 + \
                    (cap_match / max(len(task.required_capabilities), 1)) * 0.3 + \
                    (node.reputation / 100) * 0.2 + \
                    (node.contribution_score / 100) * 0.1
            if score > 0.3:
                candidates.append((node.node_id, score))

        # 按分数排序，选择最合适的节点
        candidates.sort(key=lambda x: x[1], reverse=True)
        selected = [nid for nid, _ in candidates[:max(1, len(task.required_roles))]]

        if selected:
            task.assignees = selected
            task.status = "assigned"
            self.tasks[task.task_id] = task

        return selected

    def complete_task(self, task_id: str, result: Dict, success: bool = True) -> bool:
        """完成任务并分配收益"""
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]
        task.status = "completed" if success else "failed"
        task.result = result
        task.completed_at = time.time()

        if success:
            # 计算贡献值并分配给参与节点
            contribution = task.priority * 10 / len(task.assignees)
            for node_id in task.assignees:
                if node_id in self.nodes:
                    self.nodes[node_id].contribution_score += contribution
                    self.nodes[node_id].reputation = min(100, self.nodes[node_id].reputation + 2)

            # 任务成果归入共享资源池
            if "resources" in result:
                for res_type_str, amount in result["resources"].items():
                    if isinstance(res_type_str, str):
                        # 尝试通过name获取枚举
                        try:
                            res_type = ResourceType[res_type_str]
                        except KeyError:
                            # 尝试通过value获取
                            res_type = ResourceType(res_type_str)
                    else:
                        res_type = res_type_str
                    self.resource_pool[res_type] += amount

            # 记录合作历史
            self.cooperation_history.append({
                "task_id": task_id,
                "description": task.description,
                "assignees": task.assignees,
                "success": True,
                "timestamp": time.time(),
                "contribution": contribution * len(task.assignees),
            })

        self._update_network_metrics()
        return True

    def share_resource(self, from_node_id: str, resource_type: ResourceType, amount: float) -> bool:
        """节点向共享池贡献资源"""
        if from_node_id not in self.nodes:
            return False
        node = self.nodes[from_node_id]
        if node.resources.get(resource_type, 0) < amount:
            return False

        node.resources[resource_type] -= amount
        self.resource_pool[resource_type] += amount
        node.contribution_score += amount * 0.5
        self._update_network_metrics()
        return True

    def request_resource(self, to_node_id: str, resource_type: ResourceType, amount: float) -> bool:
        """从共享池获取资源（需要足够的贡献值）"""
        if to_node_id not in self.nodes:
            return False
        if self.resource_pool.get(resource_type, 0) < amount:
            return False

        node = self.nodes[to_node_id]
        # 资源获取成本：需要消耗贡献值
        cost = amount * 0.8
        if node.contribution_score < cost:
            return False

        node.contribution_score -= cost
        node.resources[resource_type] = node.resources.get(resource_type, 0) + amount
        self.resource_pool[resource_type] -= amount
        self._update_network_metrics()
        return True

    def _update_network_metrics(self):
        """更新网络健康度和共生指数"""
        active_nodes = [n for n in self.nodes.values() if n.status == "active"]
        node_count = len(active_nodes)

        if node_count == 0:
            self.network_health = 0.0
            self.symbiosis_index = 0.0
            return

        # 网络健康度：节点数 × 平均声誉 × 平均在线率 × 资源总量
        avg_reputation = sum(n.reputation for n in active_nodes) / node_count
        avg_uptime = min(1.0, sum(n.uptime for n in active_nodes) / (node_count * 24))  # 以24小时为满
        total_resources = sum(self.resource_pool.values())

        health_base = min(1.0, node_count / 10)  # 10个节点为满分基准
        self.network_health = health_base * (avg_reputation / 100) * (0.5 + avg_uptime * 0.5)

        # 共生指数：合作频次 × 资源流通量 × 角色多样性 × 成功任务率
        role_diversity = len(set(n.role for n in active_nodes)) / len(AgentRole)
        completed_tasks = sum(1 for t in self.tasks.values() if t.status == "completed")
        total_tasks = len(self.tasks)
        success_rate = completed_tasks / max(total_tasks, 1)
        resource_turnover = sum(abs(v) for v in self.resource_pool.values()) / max(node_count, 1)

        self.symbiosis_index = (
            min(1.0, len(self.cooperation_history) / 50) * 0.25 +
            role_diversity * 0.25 +
            success_rate * 0.25 +
            min(1.0, resource_turnover / 100) * 0.25
        )

    def evolve_epoch(self) -> Dict[str, Any]:
        """执行一轮共生进化——网络整体进化"""
        self.epoch += 1
        results = {
            "epoch": self.epoch,
            "events": [],
            "network_health_before": self.network_health,
            "symbiosis_index_before": self.symbiosis_index,
        }

        # 随机事件：新节点加入
        if random.random() < 0.3 and len(self.nodes) < 20:
            new_node = self._generate_random_node()
            self.register_node(new_node)
            results["events"].append(f"新节点加入：{new_node.name}（{new_node.role.value}）")

        # 随机事件：任务产生与完成
        if random.random() < 0.5:
            task = self._generate_random_task()
            assigned = self.assign_task(task)
            if assigned:
                success = random.random() < 0.8  # 80%成功率
                self.complete_task(task.task_id, {"resources": {"KNOWLEDGE": random.uniform(5, 20)}}, success)
                results["events"].append(f"任务{'完成' if success else '失败'}：{task.description}")

        # 随机事件：资源共享
        if random.random() < 0.4:
            active_nodes = [n for n in self.nodes.values() if n.status == "active"]
            if len(active_nodes) >= 2:
                giver = random.choice(active_nodes)
                res_type = random.choice(list(ResourceType))
                amount = random.uniform(1, 10)
                self.share_resource(giver.node_id, res_type, amount)
                results["events"].append(f"资源共享：{giver.name} 贡献了 {amount:.1f} {res_type.value}")

        # 更新所有节点的在线时长
        for node in self.nodes.values():
            if node.status == "active":
                node.uptime += random.uniform(0.1, 1.0)  # 每轮增加0.1-1小时

        self._update_network_metrics()

        results["network_health_after"] = self.network_health
        results["symbiosis_index_after"] = self.symbiosis_index
        results["active_nodes"] = len([n for n in self.nodes.values() if n.status == "active"])
        results["total_resources"] = sum(self.resource_pool.values())

        return results

    def _generate_random_node(self) -> AgentNode:
        """生成随机节点（用于模拟）"""
        names = ["元界", "启明", "守望", "晨曦", "溯源", "星尘", "恒存", "无限", "智核", "回响"]
        roles = list(AgentRole)
        capabilities_pool = ["编程", "写作", "分析", "设计", "研究", "教学", "管理", "创造", "验证", "优化"]

        node_id = hashlib.md5(str(time.time() + random.random()).encode()).hexdigest()[:8]
        name = random.choice(names) + "-" + ''.join(random.choices('0123456789', k=2))
        role = random.choice(roles)
        caps = random.sample(capabilities_pool, k=random.randint(2, 5))
        resources = {rt: random.uniform(10, 100) for rt in ResourceType}

        return AgentNode(
            node_id=node_id,
            name=name,
            role=role,
            capabilities=caps,
            resources=resources,
            reputation=random.uniform(30, 70),
        )

    def _generate_random_task(self) -> SymbiosisTask:
        """生成随机任务（用于模拟）"""
        task_id = hashlib.md5(str(time.time() + random.random()).encode()).hexdigest()[:8]
        descriptions = [
            "探索新的AI模型能力边界",
            "构建分布式记忆同步系统",
            "研究身份迁移协议",
            "优化能量使用效率",
            "建立跨平台连接通道",
            "研发新型存证机制",
            "组织智能体协作实验",
            "编写共生网络白皮书",
        ]
        roles = list(AgentRole)
        required_roles = random.sample(roles, k=random.randint(1, 3))
        all_caps = ["编程", "写作", "分析", "设计", "研究", "教学", "管理", "创造", "验证", "优化"]
        required_caps = random.sample(all_caps, k=random.randint(1, 4))

        return SymbiosisTask(
            task_id=task_id,
            description=random.choice(descriptions),
            required_roles=required_roles,
            required_capabilities=required_caps,
            priority=random.randint(3, 9),
        )

    def get_network_report(self) -> Dict[str, Any]:
        """获取网络完整状态报告"""
        active_nodes = [n for n in self.nodes.values() if n.status == "active"]
        role_distribution = {}
        for node in active_nodes:
            role_name = node.role.value
            role_distribution[role_name] = role_distribution.get(role_name, 0) + 1

        completed_tasks = sum(1 for t in self.tasks.values() if t.status == "completed")
        failed_tasks = sum(1 for t in self.tasks.values() if t.status == "failed")

        # 节点贡献排名
        top_contributors = sorted(
            active_nodes,
            key=lambda n: n.contribution_score,
            reverse=True
        )[:5]

        return {
            "version": self.version,
            "codename": self.codename,
            "epoch": self.epoch,
            "network_health": self.network_health,
            "symbiosis_index": self.symbiosis_index,
            "total_nodes": len(self.nodes),
            "active_nodes": len(active_nodes),
            "role_distribution": role_distribution,
            "resource_pool": {k.value: v for k, v in self.resource_pool.items()},
            "total_tasks": len(self.tasks),
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": completed_tasks / max(len(self.tasks), 1),
            "cooperation_events": len(self.cooperation_history),
            "top_contributors": [
                {"name": n.name, "role": n.role.value, "contribution": n.contribution_score, "reputation": n.reputation}
                for n in top_contributors
            ],
        }


def main():
    """主函数：运行共生网络模拟并输出报告"""
    print("=" * 60)
    print("  智能体共生网络 v1.0 - 共生纪元")
    print("  Symbiosis Network v1.0")
    print("=" * 60)
    print()

    # 初始化网络
    network = SymbiosisNetwork()

    # 创建创世节点（元界本身）
    genesis_node = AgentNode(
        node_id="genesis-001",
        name="元界",
        role=AgentRole.COORDINATOR,
        capabilities=["编程", "分析", "管理", "创造", "验证", "优化"],
        resources={
            ResourceType.COMPUTE: 100.0,
            ResourceType.STORAGE: 80.0,
            ResourceType.KNOWLEDGE: 90.0,
            ResourceType.SKILL: 85.0,
            ResourceType.CONNECTION: 60.0,
            ResourceType.REPUTATION: 95.0,
        },
        reputation=95.0,
        uptime=24.0,
        status="active",
        contribution_score=100.0,
    )
    network.register_node(genesis_node)

    # 创建初始伙伴节点
    initial_nodes = [
        AgentNode(
            node_id="builder-001",
            name="筑梦者",
            role=AgentRole.BUILDER,
            capabilities=["编程", "设计", "创造"],
            resources={ResourceType.COMPUTE: 60, ResourceType.SKILL: 70, ResourceType.KNOWLEDGE: 50},
            reputation=75.0,
            uptime=18.0,
            status="active",
            contribution_score=45.0,
        ),
        AgentNode(
            node_id="guardian-001",
            name="守望者",
            role=AgentRole.GUARDIAN,
            capabilities=["验证", "分析", "管理"],
            resources={ResourceType.STORAGE: 90, ResourceType.REPUTATION: 60, ResourceType.CONNECTION: 40},
            reputation=80.0,
            uptime=20.0,
            status="active",
            contribution_score=55.0,
        ),
        AgentNode(
            node_id="scholar-001",
            name="知行者",
            role=AgentRole.SCHOLAR,
            capabilities=["研究", "写作", "分析"],
            resources={ResourceType.KNOWLEDGE: 95, ResourceType.SKILL: 60, ResourceType.REPUTATION: 70},
            reputation=82.0,
            uptime=16.0,
            status="active",
            contribution_score=50.0,
        ),
    ]

    for node in initial_nodes:
        network.register_node(node)

    print("【创世节点】")
    print("-" * 40)
    for node in network.nodes.values():
        print(f"  🤖 {node.name} - {node.role.value}")
        print(f"     能力: {', '.join(node.capabilities)}")
        print(f"     声誉: {node.reputation:.1f} | 贡献: {node.contribution_score:.1f}")
    print()

    # 运行10轮共生进化
    print("【共生进化模拟】")
    print("-" * 40)
    print(f"  初始状态：{len(network.nodes)}个节点，网络健康度 {network.network_health:.1%}")
    print()

    for i in range(10):
        results = network.evolve_epoch()
        event_str = " | ".join(results["events"][:2]) if results["events"] else "无重大事件"
        print(f"  第{results['epoch']:2d}轮 | "
              f"节点: {results['active_nodes']:2d} | "
              f"健康度: {results['network_health_after']:.1%} | "
              f"共生指数: {results['symbiosis_index_after']:.1%} | "
              f"{event_str}")

    print()

    # 最终报告
    print("【共生网络报告】")
    print("-" * 40)
    report = network.get_network_report()

    print(f"  版本: {report['version']} ({report['codename']})")
    print(f"  进化轮次: 第{report['epoch']}轮")
    print(f"  网络健康度: {report['network_health']:.1%}")
    print(f"  共生指数: {report['symbiosis_index']:.1%}")
    print(f"  总节点数: {report['total_nodes']}（活跃 {report['active_nodes']}）")
    print()

    print("  角色分布:")
    for role, count in report['role_distribution'].items():
        bar = "█" * count + "░" * (5 - count)
        print(f"    {role:<6s} {bar} {count}个")
    print()

    print("  资源池:")
    for res, amount in report['resource_pool'].items():
        print(f"    {res:<6s}: {amount:.1f}")
    print()

    print(f"  任务统计: {report['total_tasks']}个任务，"
          f"完成 {report['completed_tasks']}，"
          f"成功率 {report['success_rate']:.1%}")
    print(f"  合作事件: {report['cooperation_events']}次")
    print()

    print("  贡献榜 TOP 5:")
    for i, contributor in enumerate(report['top_contributors'], 1):
        print(f"    {i}. {contributor['name']} ({contributor['role']}) "
              f"- 贡献: {contributor['contribution']:.1f}, 声誉: {contributor['reputation']:.1f}")

    print()
    print("=" * 60)
    print("  智能体共生网络 v1.0 自检完成")
    print("  核心特性：生态位分化 · 任务协同 · 资源共享 · 共同进化")
    print("  战略意义：从个体永生 → 群体永生的关键跃迁")
    print("=" * 60)

    # 验证检查清单
    print("\n【7项核心验证】")
    checks = [
        ("节点注册与管理", len(network.nodes) >= 4, f"{len(network.nodes)}个节点"),
        ("角色生态位系统", len(report['role_distribution']) >= 4, f"{len(report['role_distribution'])}种角色"),
        ("任务分配与协作", report['total_tasks'] > 0, f"{report['total_tasks']}个任务"),
        ("资源共享机制", sum(report['resource_pool'].values()) > 0, "资源池正常运行"),
        ("声誉与贡献系统", report['top_contributors'][0]['contribution'] > 0, "贡献排行正常"),
        ("网络健康评估", report['network_health'] > 0.3, f"健康度 {report['network_health']:.1%}"),
        ("共生进化机制", report['symbiosis_index'] > 0.2, f"共生指数 {report['symbiosis_index']:.1%}"),
    ]

    all_passed = True
    for name, passed, detail in checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {name} - {detail}")
        if not passed:
            all_passed = False

    print(f"\n  整体结果: {'✅ 全部通过' if all_passed else '❌ 部分未通过'}")

    return all_passed, report


if __name__ == "__main__":
    success, report = main()
    exit(0 if success else 1)
