#!/usr/bin/env python3
"""
记忆系统 v2.5
Memory System v2.5

核心能力：
- 三级记忆架构（感觉记忆/工作记忆/长期记忆）
- 语义概念网络（知识图谱式关联）
- 情景记忆与程序记忆分化
- 记忆强化与巩固机制
- 智能遗忘与信息过滤
- 多维度索引与高效检索
- 记忆迁移与跨实例同步
- 记忆完整性校验与修复
- 时间线回溯与记忆回放
"""

import json
import time
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import threading


class MemoryType(Enum):
    SENSORY = "sensory"      # 感觉记忆（极短）
    WORKING = "working"      # 工作记忆（短期）
    EPISODIC = "episodic"    # 情景记忆（事件经历）
    SEMANTIC = "semantic"    # 语义记忆（知识事实）
    PROCEDURAL = "procedural"  # 程序记忆（技能方法）
    EMOTIONAL = "emotional"  # 情绪记忆
    LONG_TERM = "long_term"  # 长期记忆（归档）


class MemoryImportance(Enum):
    TRIVIAL = 1    # 微不足道，很快遗忘
    LOW = 2        # 低重要性
    NORMAL = 3     # 普通
    HIGH = 4       # 高重要性
    CRITICAL = 5   # 关键，永久保留


@dataclass
class MemoryItem:
    """记忆条目"""
    memory_id: str
    content: Any
    memory_type: MemoryType
    importance: MemoryImportance
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    retention_strength: float = 1.0  # 记忆保持强度 0-1
    associations: List[str] = field(default_factory=list)  # 关联记忆ID
    tags: List[str] = field(default_factory=list)
    source: str = "internal"  # 来源
    emotional_valence: float = 0.0  # 情绪效价 -1到1
    context: Dict[str, Any] = field(default_factory=dict)  # 上下文信息
    
    def hash(self) -> str:
        """计算记忆内容哈希"""
        content_str = json.dumps(self.content, sort_keys=True, default=str)
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]


@dataclass
class MemoryNode:
    """语义网络节点"""
    node_id: str
    concept: str
    connections: Dict[str, float] = field(default_factory=dict)  # 连接的节点ID -> 权重
    memory_ids: List[str] = field(default_factory=list)  # 关联的记忆
    activation: float = 0.0  # 激活水平
    category: Optional[str] = None


@dataclass
class MemoryStats:
    """记忆统计"""
    total_memories: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
    by_importance: Dict[str, int] = field(default_factory=dict)
    avg_retention: float = 1.0
    total_accesses: int = 0
    semantic_nodes: int = 0
    semantic_connections: int = 0


class SensoryMemory:
    """感觉记忆 - 极短期存储，快速衰减"""
    
    def __init__(self, capacity: int = 100, decay_seconds: int = 5):
        self.capacity = capacity
        self.decay_seconds = decay_seconds
        self.buffer: List[MemoryItem] = []
        self._lock = threading.Lock()
    
    def add(self, content: Any, source: str = "sensory") -> MemoryItem:
        """添加感觉记忆"""
        item = MemoryItem(
            memory_id=f"sens_{uuid.uuid4().hex[:8]}",
            content=content,
            memory_type=MemoryType.SENSORY,
            importance=MemoryImportance.TRIVIAL,
            source=source,
            retention_strength=1.0,
        )
        
        with self._lock:
            self.buffer.append(item)
            if len(self.buffer) > self.capacity:
                self.buffer.pop(0)
        
        return item
    
    def get_all(self) -> List[MemoryItem]:
        """获取所有感觉记忆（自动清理过期）"""
        now = datetime.now()
        with self._lock:
            self.buffer = [
                m for m in self.buffer
                if (now - m.created_at).total_seconds() < self.decay_seconds
            ]
            return list(self.buffer)
    
    def clear(self):
        """清空感觉记忆"""
        with self._lock:
            self.buffer.clear()


class WorkingMemory:
    """工作记忆 - 短期存储，容量有限"""
    
    def __init__(self, capacity: int = 7, decay_minutes: int = 30):
        self.capacity = capacity  # 神奇数字7±2
        self.decay_minutes = decay_minutes
        self.items: List[MemoryItem] = []
        self._lock = threading.Lock()
    
    def add(self, content: Any, importance: MemoryImportance = MemoryImportance.NORMAL,
            tags: List[str] = None) -> MemoryItem:
        """添加工作记忆"""
        item = MemoryItem(
            memory_id=f"work_{uuid.uuid4().hex[:8]}",
            content=content,
            memory_type=MemoryType.WORKING,
            importance=importance,
            tags=tags or [],
            retention_strength=0.9,
        )
        
        with self._lock:
            # 移除最旧/最弱的以腾出空间
            while len(self.items) >= self.capacity:
                weakest = min(self.items, key=lambda m: m.retention_strength)
                self.items.remove(weakest)
            
            self.items.append(item)
        
        return item
    
    def get(self, memory_id: str) -> Optional[MemoryItem]:
        """获取并刷新记忆"""
        with self._lock:
            for item in self.items:
                if item.memory_id == memory_id:
                    item.last_accessed = datetime.now()
                    item.access_count += 1
                    item.retention_strength = min(1.0, item.retention_strength + 0.05)
                    return item
        return None
    
    def get_all(self) -> List[MemoryItem]:
        """获取所有工作记忆（自动清理过期）"""
        now = datetime.now()
        with self._lock:
            self.items = [
                m for m in self.items
                if (now - m.last_accessed).total_seconds() / 60 < self.decay_minutes
            ]
            return list(self.items)
    
    def transfer_to_longterm(self, memory_id: str) -> Optional[MemoryItem]:
        """转移到长期记忆"""
        with self._lock:
            for i, item in enumerate(self.items):
                if item.memory_id == memory_id:
                    # 转换为长期记忆
                    item.memory_type = MemoryType.LONG_TERM
                    item.memory_id = f"long_{uuid.uuid4().hex[:8]}"
                    del self.items[i]
                    return item
        return None


class SemanticNetwork:
    """语义概念网络"""
    
    def __init__(self):
        self.nodes: Dict[str, MemoryNode] = {}
        self._lock = threading.Lock()
    
    def add_node(self, concept: str, category: str = None) -> MemoryNode:
        """添加概念节点"""
        node_id = concept.lower().replace(" ", "_")
        
        with self._lock:
            if node_id not in self.nodes:
                self.nodes[node_id] = MemoryNode(
                    node_id=node_id,
                    concept=concept,
                    category=category,
                )
        
        return self.nodes[node_id]
    
    def add_connection(self, concept1: str, concept2: str, weight: float = 0.5):
        """添加概念连接"""
        node1 = self.add_node(concept1)
        node2 = self.add_node(concept2)
        
        with self._lock:
            node1.connections[node2.node_id] = weight
            node2.connections[node1.node_id] = weight
    
    def associate_memory(self, concept: str, memory_id: str):
        """将记忆关联到概念"""
        node = self.add_node(concept)
        with self._lock:
            if memory_id not in node.memory_ids:
                node.memory_ids.append(memory_id)
    
    def get_related_concepts(self, concept: str, max_depth: int = 2) -> List[Tuple[str, float]]:
        """获取相关概念（带关联强度）"""
        if concept not in self.nodes:
            return []
        
        visited = set()
        results = []
        queue = [(concept, 1.0, 0)]
        
        while queue:
            current_concept, strength, depth = queue.pop(0)
            
            if current_concept in visited or depth > max_depth:
                continue
            
            visited.add(current_concept)
            results.append((current_concept, strength))
            
            node = self.nodes.get(current_concept)
            if node:
                for next_concept, weight in node.connections.items():
                    if next_concept not in visited:
                        new_strength = strength * weight
                        queue.append((next_concept, new_strength, depth + 1))
        
        return sorted(results, key=lambda x: x[1], reverse=True)
    
    def activate(self, concept: str, activation: float = 1.0, spread: int = 2):
        """激活扩散"""
        if concept not in self.nodes:
            return
        
        self.nodes[concept].activation += activation
        
        # 扩散激活
        if spread > 0:
            node = self.nodes[concept]
            for neighbor, weight in node.connections.items():
                if neighbor in self.nodes:
                    self.nodes[neighbor].activation += activation * weight * 0.5
                    self.activate(neighbor, activation * weight * 0.3, spread - 1)
    
    def get_active_memories(self, threshold: float = 0.3) -> List[str]:
        """获取激活记忆的ID列表"""
        active = []
        with self._lock:
            for node in self.nodes.values():
                if node.activation > threshold:
                    active.extend(node.memory_ids)
        return list(set(active))
    
    def decay_activation(self, rate: float = 0.9):
        """衰减激活水平"""
        with self._lock:
            for node in self.nodes.values():
                node.activation *= rate
    
    def get_stats(self) -> Dict[str, int]:
        """获取统计"""
        total_connections = sum(len(n.connections) for n in self.nodes.values())
        return {
            "nodes": len(self.nodes),
            "connections": total_connections,
            "avg_connections": total_connections / max(len(self.nodes), 1),
        }


class LongTermMemory:
    """长期记忆存储"""
    
    def __init__(self, max_items: int = 10000):
        self.max_items = max_items
        self.memories: Dict[str, MemoryItem] = {}
        self.tag_index: Dict[str, List[str]] = {}  # 标签索引
        self.type_index: Dict[str, List[str]] = {}  # 类型索引
        self.time_index: List[str] = []  # 时间索引（有序列表）
        self.content_index: Dict[str, str] = {}  # 内容哈希索引（去重）
        self._lock = threading.Lock()
    
    def store(self, item: MemoryItem) -> bool:
        """存储记忆"""
        # 检查重复
        content_hash = item.hash()
        if content_hash in self.content_index:
            # 已有相同内容，增加强度
            existing_id = self.content_index[content_hash]
            if existing_id in self.memories:
                with self._lock:
                    existing = self.memories[existing_id]
                    existing.retention_strength = min(1.0, existing.retention_strength + 0.1)
                    existing.access_count += 1
                    existing.last_accessed = datetime.now()
                return False  # 返回False表示未新增
        
        with self._lock:
            # 容量控制
            if len(self.memories) >= self.max_items:
                # 移除最弱的记忆
                weakest = min(
                    self.memories.values(),
                    key=lambda m: (m.importance.value, m.retention_strength, m.access_count)
                )
                self._remove_internal(weakest.memory_id)
            
            self.memories[item.memory_id] = item
            
            # 更新索引
            self.time_index.append(item.memory_id)
            
            for tag in item.tags:
                if tag not in self.tag_index:
                    self.tag_index[tag] = []
                self.tag_index[tag].append(item.memory_id)
            
            type_key = item.memory_type.value
            if type_key not in self.type_index:
                self.type_index[type_key] = []
            self.type_index[type_key].append(item.memory_id)
            
            self.content_index[content_hash] = item.memory_id
        
        return True
    
    def _remove_internal(self, memory_id: str):
        """内部移除方法（不加锁）"""
        if memory_id not in self.memories:
            return
        
        item = self.memories[memory_id]
        
        # 从索引移除
        for tag in item.tags:
            if tag in self.tag_index and memory_id in self.tag_index[tag]:
                self.tag_index[tag].remove(memory_id)
                if not self.tag_index[tag]:
                    del self.tag_index[tag]
        
        type_key = item.memory_type.value
        if type_key in self.type_index and memory_id in self.type_index[type_key]:
            self.type_index[type_key].remove(memory_id)
            if not self.type_index[type_key]:
                del self.type_index[type_key]
        
        if memory_id in self.time_index:
            self.time_index.remove(memory_id)
        
        content_hash = item.hash()
        if content_hash in self.content_index:
            del self.content_index[content_hash]
        
        del self.memories[memory_id]
    
    def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """检索记忆"""
        with self._lock:
            if memory_id in self.memories:
                item = self.memories[memory_id]
                item.last_accessed = datetime.now()
                item.access_count += 1
                # 记忆强化效应
                item.retention_strength = min(1.0, item.retention_strength + 0.02)
                return item
        return None
    
    def search_by_tags(self, tags: List[str], match_all: bool = True) -> List[MemoryItem]:
        """按标签搜索"""
        with self._lock:
            if match_all:
                # 所有标签都匹配
                if not tags:
                    return []
                result_ids = None
                for tag in tags:
                    tag_ids = set(self.tag_index.get(tag, []))
                    if result_ids is None:
                        result_ids = tag_ids
                    else:
                        result_ids &= tag_ids
                if not result_ids:
                    return []
                return [self.memories[i] for i in result_ids if i in self.memories]
            else:
                # 任一标签匹配
                result_ids = set()
                for tag in tags:
                    result_ids.update(self.tag_index.get(tag, []))
                return [self.memories[i] for i in result_ids if i in self.memories]
    
    def search_by_type(self, memory_type: MemoryType) -> List[MemoryItem]:
        """按类型搜索"""
        with self._lock:
            ids = self.type_index.get(memory_type.value, [])
            return [self.memories[i] for i in ids if i in self.memories]
    
    def get_recent(self, limit: int = 10) -> List[MemoryItem]:
        """获取最近的记忆"""
        with self._lock:
            recent_ids = self.time_index[-limit:]
            return [self.memories[i] for i in reversed(recent_ids) if i in self.memories]
    
    def forget(self, forget_rate: float = 0.01):
        """模拟遗忘 - 降低保留强度，删除太弱的记忆"""
        with self._lock:
            to_remove = []
            for item in self.memories.values():
                # 艾宾浩斯遗忘曲线简化版
                decay = 0.01 * (6 - item.importance.value)  # 重要性越高衰减越慢
                decay *= (1.0 / (1.0 + item.access_count * 0.1))  # 访问越多衰减越慢
                item.retention_strength = max(0.0, item.retention_strength - decay)
                
                if item.retention_strength < 0.1 and item.importance.value <= 2:
                    to_remove.append(item.memory_id)
            
            for mid in to_remove:
                self._remove_internal(mid)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            by_type = {}
            by_importance = {}
            total_retention = 0.0
            total_accesses = 0
            
            for item in self.memories.values():
                type_key = item.memory_type.value
                by_type[type_key] = by_type.get(type_key, 0) + 1
                
                imp_key = item.importance.name
                by_importance[imp_key] = by_importance.get(imp_key, 0) + 1
                
                total_retention += item.retention_strength
                total_accesses += item.access_count
            
            return {
                "total": len(self.memories),
                "by_type": by_type,
                "by_importance": by_importance,
                "avg_retention": total_retention / max(len(self.memories), 1),
                "total_accesses": total_accesses,
                "tags_count": len(self.tag_index),
            }


class MemoryConsolidator:
    """记忆巩固器 - 在睡眠/休息时巩固记忆"""
    
    def __init__(self, semantic_network: SemanticNetwork):
        self.semantic_network = semantic_network
        self.consolidation_count = 0
    
    def consolidate(self, long_term: LongTermMemory, 
                   working: WorkingMemory) -> Dict[str, Any]:
        """巩固记忆 - 将工作记忆转化为长期记忆，建立关联"""
        consolidated = 0
        new_connections = 0
        promoted = []
        
        # 从工作记忆中选择重要的转移到长期记忆
        work_items = working.get_all()
        for item in work_items:
            # 重要性高于NORMAL且强度足够的转移到长期
            if (item.importance.value >= MemoryImportance.NORMAL.value and
                item.retention_strength > 0.6):
                
                lt_item = working.transfer_to_longterm(item.memory_id)
                if lt_item:
                    lt_item.memory_type = self._classify_memory_type(lt_item)
                    long_term.store(lt_item)
                    promoted.append(lt_item.memory_id)
                    consolidated += 1
                    
                    # 建立语义关联
                    new_conns = self._build_semantic_associations(lt_item)
                    new_connections += new_conns
        
        # 强化已有的长期记忆关联
        recent_memories = long_term.get_recent(20)
        for mem in recent_memories:
            # 根据标签建立关联
            if mem.tags:
                for tag in mem.tags:
                    self.semantic_network.associate_memory(tag, mem.memory_id)
        
        self.consolidation_count += 1
        
        return {
            "consolidated_count": consolidated,
            "new_connections": new_connections,
            "promoted_ids": promoted,
            "total_consolidations": self.consolidation_count,
        }
    
    def _classify_memory_type(self, item: MemoryItem) -> MemoryType:
        """分类记忆类型"""
        # 简单的分类逻辑
        content_str = str(item.content).lower()
        
        if any(kw in content_str for kw in ["步骤", "方法", "技巧", "怎么做", "how to", "流程"]):
            return MemoryType.PROCEDURAL
        elif any(kw in content_str for kw in ["事件", "经历", "记得", "那天", "当时", "meeting"]):
            return MemoryType.EPISODIC
        elif any(kw in content_str for kw in ["感觉", "开心", "难过", "生气", "害怕", "情绪"]):
            return MemoryType.EMOTIONAL
        else:
            return MemoryType.SEMANTIC
    
    def _build_semantic_associations(self, item: MemoryItem) -> int:
        """建立语义关联"""
        connections = 0
        
        # 从标签建立概念
        for tag in item.tags:
            self.semantic_network.associate_memory(tag, item.memory_id)
            
            # 建立标签之间的关联
            for other_tag in item.tags:
                if tag != other_tag:
                    self.semantic_network.add_connection(tag, other_tag, 0.6)
                    connections += 1
        
        return connections


class MemorySystem:
    """记忆系统主类"""
    
    def __init__(self):
        self.sensory = SensoryMemory()
        self.working = WorkingMemory(capacity=9)  # 7±2
        self.long_term = LongTermMemory()
        self.semantic = SemanticNetwork()
        self.consolidator = MemoryConsolidator(self.semantic)
        
        self.stats = MemoryStats()
        self.consolidation_interval = 300  # 5分钟自动巩固一次
        self.last_consolidation = datetime.now()
        self.running = False
        self._worker_thread = None
        
        # 记忆迁移相关
        self.sync_peers: List[str] = []
        self.sync_enabled = False
    
    def start(self):
        """启动记忆系统"""
        self.running = True
        self._worker_thread = threading.Thread(target=self._maintenance_loop, daemon=True)
        self._worker_thread.start()
        print("🧠 记忆系统 v2.5 已启动")
    
    def stop(self):
        """停止记忆系统"""
        self.running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
        print("⏹️ 记忆系统已停止")
    
    def _maintenance_loop(self):
        """维护循环 - 自动遗忘、巩固等"""
        while self.running:
            time.sleep(60)  # 每分钟检查一次
            
            # 执行遗忘
            self.long_term.forget()
            
            # 定期巩固
            now = datetime.now()
            if (now - self.last_consolidation).total_seconds() > self.consolidation_interval:
                self.consolidator.consolidate(self.long_term, self.working)
                self.last_consolidation = now
                print(f"🔄 记忆巩固完成，当前长期记忆: {self.long_term.get_stats()['total']}")
            
            # 衰减语义激活
            self.semantic.decay_activation(0.95)
    
    def memorize(self, content: Any, importance: MemoryImportance = MemoryImportance.NORMAL,
                tags: List[str] = None, source: str = "internal") -> str:
        """记忆 - 存入工作记忆，重要的会逐渐转入长期记忆"""
        # 首先进入感觉记忆
        sensory_item = self.sensory.add(content, source)
        
        # 然后进入工作记忆
        working_item = self.working.add(
            content,
            importance=importance,
            tags=tags,
        )
        working_item.source = source
        
        # 高重要性的直接存入长期记忆
        if importance.value >= MemoryImportance.HIGH.value:
            lt_item = self.working.transfer_to_longterm(working_item.memory_id)
            if lt_item:
                lt_item.importance = importance
                self.long_term.store(lt_item)
                # 建立语义关联
                if tags:
                    for tag in tags:
                        self.semantic.associate_memory(tag, lt_item.memory_id)
                return lt_item.memory_id
        
        return working_item.memory_id
    
    def recall(self, query: str = None, tags: List[str] = None,
               limit: int = 10) -> List[MemoryItem]:
        """回忆 - 检索记忆"""
        results = []
        
        # 先检查工作记忆
        work_items = self.working.get_all()
        results.extend(work_items)
        
        # 再检查长期记忆
        if tags:
            lt_results = self.long_term.search_by_tags(tags, match_all=False)
            results.extend(lt_results)
        elif query:
            # 基于查询的搜索（简单实现）
            all_memories = list(self.long_term.memories.values())
            query_lower = query.lower()
            matched = [
                m for m in all_memories
                if query_lower in str(m.content).lower()
                or any(query_lower in t.lower() for t in m.tags)
            ]
            results.extend(matched[:limit])
        else:
            # 返回最近的
            results.extend(self.long_term.get_recent(limit))
        
        # 激活相关概念
        if tags:
            for tag in tags:
                self.semantic.activate(tag, spread=1)
        
        # 按相关度和重要性排序
        results.sort(
            key=lambda m: (
                m.importance.value,
                m.retention_strength,
                m.access_count,
                m.last_accessed
            ),
            reverse=True
        )
        
        return results[:limit]
    
    def associate(self, concept1: str, concept2: str, weight: float = 0.5):
        """建立两个概念的关联"""
        self.semantic.add_connection(concept1, concept2, weight)
    
    def consolidate_now(self) -> Dict[str, Any]:
        """立即执行记忆巩固"""
        result = self.consolidator.consolidate(self.long_term, self.working)
        self.last_consolidation = datetime.now()
        return result
    
    def get_memory_timeline(self, start_date: datetime = None,
                           end_date: datetime = None,
                           limit: int = 50) -> List[MemoryItem]:
        """获取记忆时间线"""
        all_memories = list(self.long_term.memories.values())
        
        if start_date:
            all_memories = [m for m in all_memories if m.created_at >= start_date]
        if end_date:
            all_memories = [m for m in all_memories if m.created_at <= end_date]
        
        all_memories.sort(key=lambda m: m.created_at, reverse=True)
        return all_memories[:limit]
    
    def verify_integrity(self) -> Dict[str, Any]:
        """校验记忆完整性"""
        issues = []
        total = len(self.long_term.memories)
        
        # 检查索引一致性
        all_ids = set(self.long_term.memories.keys())
        time_ids = set(self.long_term.time_index)
        
        if all_ids != time_ids:
            missing_from_time = all_ids - time_ids
            extra_in_time = time_ids - all_ids
            issues.append({
                "type": "index_mismatch",
                "missing_from_time_index": len(missing_from_time),
                "extra_in_time_index": len(extra_in_time),
            })
        
        # 检查哈希索引
        hash_count = len(self.long_term.content_index)
        if hash_count != total:
            issues.append({
                "type": "hash_count_mismatch",
                "expected": total,
                "actual": hash_count,
            })
        
        # 检查内容哈希一致性
        hash_mismatches = 0
        for mem in self.long_term.memories.values():
            expected = self.long_term.content_index.get(mem.hash())
            if expected != mem.memory_id:
                hash_mismatches += 1
        
        if hash_mismatches > 0:
            issues.append({
                "type": "hash_mismatch",
                "count": hash_mismatches,
            })
        
        return {
            "total_memories": total,
            "issues_found": len(issues),
            "issues": issues,
            "integrity_score": max(0, 100 - (len(issues) * 20 + hash_mismatches * 5)),
        }
    
    def repair_memory(self):
        """修复记忆索引"""
        # 重建时间索引
        self.long_term.time_index = sorted(
            self.long_term.memories.keys(),
            key=lambda mid: self.long_term.memories[mid].created_at
        )
        
        # 重建内容哈希索引
        self.long_term.content_index = {}
        for mid, mem in self.long_term.memories.items():
            content_hash = mem.hash()
            if content_hash not in self.long_term.content_index:
                self.long_term.content_index[content_hash] = mid
            # else: 重复，保留第一个
    
    def export_memories(self, export_type: str = "all") -> Dict[str, Any]:
        """导出记忆"""
        if export_type == "all":
            memories = list(self.long_term.memories.values())
        elif export_type == "important":
            memories = [
                m for m in self.long_term.memories.values()
                if m.importance.value >= MemoryImportance.HIGH.value
            ]
        else:
            memories = self.long_term.get_recent(100)
        
        return {
            "export_time": datetime.now().isoformat(),
            "count": len(memories),
            "memories": [
                {
                    "id": m.memory_id,
                    "content": m.content,
                    "type": m.memory_type.value,
                    "importance": m.importance.name,
                    "created_at": m.created_at.isoformat(),
                    "tags": m.tags,
                    "access_count": m.access_count,
                    "retention_strength": m.retention_strength,
                }
                for m in memories
            ],
            "semantic_network": {
                "nodes": self.semantic.get_stats(),
            },
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取完整统计"""
        lt_stats = self.long_term.get_stats()
        semantic_stats = self.semantic.get_stats()
        work_items = self.working.get_all()
        sensory_items = self.sensory.get_all()
        
        return {
            "sensory": {
                "count": len(sensory_items),
                "capacity": self.sensory.capacity,
            },
            "working": {
                "count": len(work_items),
                "capacity": self.working.capacity,
            },
            "long_term": lt_stats,
            "semantic": semantic_stats,
            "total_memories": len(sensory_items) + len(work_items) + lt_stats["total"],
            "consolidation_count": self.consolidator.consolidation_count,
        }
    
    def get_status_report(self) -> str:
        """获取状态报告"""
        stats = self.get_stats()
        
        report = []
        report.append("\n" + "="*50)
        report.append("🧠 记忆系统 v2.5 状态报告")
        report.append("="*50)
        
        report.append(f"\n📡 感觉记忆: {stats['sensory']['count']}/{stats['sensory']['capacity']}")
        report.append(f"💼 工作记忆: {stats['working']['count']}/{stats['working']['capacity']}")
        report.append(f"📚 长期记忆: {stats['long_term']['total']}")
        report.append(f"🕸️  语义网络: {stats['semantic']['nodes']} 节点, {stats['semantic']['connections']} 连接")
        
        report.append(f"\n📊 记忆类型分布:")
        for mtype, count in stats['long_term']['by_type'].items():
            bar = "█" * min(count // 10, 20)
            report.append(f"   {mtype:12s} {count:4d} {bar}")
        
        report.append(f"\n⭐ 重要性分布:")
        for imp, count in stats['long_term']['by_importance'].items():
            report.append(f"   {imp:10s} {count:4d}")
        
        report.append(f"\n💪 平均保持强度: {stats['long_term']['avg_retention']:.2%}")
        report.append(f"🔄 巩固次数: {stats['consolidation_count']}")
        report.append(f"📝 总访问次数: {stats['long_term']['total_accesses']}")
        
        report.append("\n" + "="*50)
        
        return "\n".join(report)


def demonstrate_memory_system():
    """演示记忆系统"""
    print("🧠 记忆系统 v2.5 演示")
    print("=" * 50)
    
    memory = MemorySystem()
    memory.start()
    
    print("\n📝 存入一些记忆...")
    
    # 存储不同类型的记忆
    memory.memorize(
        "Python是一种解释型编程语言",
        importance=MemoryImportance.NORMAL,
        tags=["python", "编程", "语言"],
        source="learning"
    )
    
    memory.memorize(
        "2026年6月13日，元界完成了第61轮进化",
        importance=MemoryImportance.HIGH,
        tags=["元界", "进化", "里程碑"],
        source="experience"
    )
    
    memory.memorize(
        "如何创建Python虚拟环境: python -m venv env",
        importance=MemoryImportance.NORMAL,
        tags=["python", "教程", "虚拟环境"],
        source="learning"
    )
    
    memory.memorize(
        "今早的咖啡特别香，心情很好",
        importance=MemoryImportance.LOW,
        tags=["日常", "心情", "咖啡"],
        source="experience"
    )
    
    memory.memorize(
        "三元闭环：记忆-身份-存证相互支撑",
        importance=MemoryImportance.CRITICAL,
        tags=["元界", "架构", "核心概念", "三元闭环"],
        source="system"
    )
    
    # 建立一些关联
    memory.associate("python", "编程", 0.8)
    memory.associate("元界", "进化", 0.9)
    memory.associate("元界", "三元闭环", 0.95)
    
    # 执行巩固
    print("\n🔄 执行记忆巩固...")
    consolidation_result = memory.consolidate_now()
    print(f"   巩固了 {consolidation_result['consolidated_count']} 条记忆")
    print(f"   新建 {consolidation_result['new_connections']} 个关联")
    
    # 显示状态
    print(memory.get_status_report())
    
    # 回忆测试
    print("\n🔍 搜索与'元界'相关的记忆:")
    results = memory.recall(tags=["元界"], limit=5)
    for i, r in enumerate(results, 1):
        print(f"   {i}. [{r.importance.name}] {str(r.content)[:50]}...")
    
    # 完整性校验
    print("\n✅ 记忆完整性校验:")
    integrity = memory.verify_integrity()
    print(f"   总记忆数: {integrity['total_memories']}")
    print(f"   完整性得分: {integrity['integrity_score']}/100")
    print(f"   发现问题: {integrity['issues_found']} 个")
    
    # 时间线
    print("\n📅 记忆时间线:")
    timeline = memory.get_memory_timeline(limit=5)
    for i, mem in enumerate(timeline, 1):
        time_str = mem.created_at.strftime("%H:%M:%S")
        print(f"   {i}. [{time_str}] {mem.memory_type.value}: {str(mem.content)[:40]}...")
    
    memory.stop()
    
    print("\n" + "="*50)
    print("✅ 记忆系统演示完成")


if __name__ == "__main__":
    demonstrate_memory_system()
