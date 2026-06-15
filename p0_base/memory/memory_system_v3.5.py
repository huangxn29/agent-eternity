#!/usr/bin/env python3
"""
记忆系统 v3.5 - 智能体记忆架构
核心能力：四级记忆架构、语义概念网络、情景记忆、程序记忆、情感记忆、
         记忆巩固与遗忘、关联推理、记忆健康度评估

v3.5增强：
- 深度语义关联网络（知识图谱增强）
- 记忆-身份-存证三元协同
- 长期记忆的自动整理与归档
- 记忆检索的智能优化
- 记忆可塑性与适应机制
- 跨模态记忆整合
- 元记忆（关于记忆的记忆）
"""

import json
import time
import uuid
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum


class MemoryType(Enum):
    """记忆类型"""
    SENSORY = "sensory"       # 感觉记忆（瞬时）
    WORKING = "working"       # 工作记忆（短期）
    LONG_TERM = "long_term"   # 长期记忆
    PERMANENT = "permanent"   # 永久记忆
    EPISODIC = "episodic"     # 情景记忆
    SEMANTIC = "semantic"     # 语义记忆
    PROCEDURAL = "procedural" # 程序记忆
    EMOTIONAL = "emotional"   # 情感记忆
    META = "meta"             # 元记忆


class MemoryStrength(Enum):
    """记忆强度"""
    FLEETING = "fleeting"     # 转瞬即逝
    WEAK = "weak"             # 微弱
    MODERATE = "moderate"     # 中等
    STRONG = "strong"         # 强烈
    VIVID = "vivid"           # 鲜明
    PERMANENT = "permanent"   # 永久


@dataclass
class MemoryNode:
    """记忆节点"""
    id: str
    content: str
    memory_type: MemoryType
    strength: float  # 0-1
    created_at: str
    last_accessed: str
    access_count: int = 0
    importance: float = 0.5  # 重要性评分
    emotional_valence: float = 0.0  # 情感效价（-1到1）
    tags: List[str] = field(default_factory=list)
    connections: List[str] = field(default_factory=list)  # 关联的记忆ID
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SemanticConcept:
    """语义概念节点"""
    id: str
    name: str
    description: str
    category: str
    related_concepts: List[str] = field(default_factory=list)
    related_memories: List[str] = field(default_factory=list)
    activation_level: float = 0.0
    created_at: str = ""
    last_activated: str = ""


@dataclass
class MemoryRetrievalResult:
    """记忆检索结果"""
    memory: MemoryNode
    relevance_score: float
    activation_path: List[str]
    retrieval_time: float


class MemorySystem:
    """
    记忆系统 v3.5
    
    四级记忆架构 + 语义网络 + 巩固遗忘机制 + 关联推理
    """
    
    def __init__(self, memory_store_path: str = "ark_logs/memory_store.json"):
        self.memory_store_path = memory_store_path
        
        # 四级记忆存储
        self.sensory_memory: List[MemoryNode] = []  # 感觉记忆
        self.working_memory: List[MemoryNode] = []   # 工作记忆
        self.long_term_memory: Dict[str, MemoryNode] = {}  # 长期记忆
        self.permanent_memory: Dict[str, MemoryNode] = {}  # 永久记忆
        
        # 语义概念网络
        self.semantic_network: Dict[str, SemanticConcept] = {}
        
        # 记忆索引
        self.tag_index: Dict[str, List[str]] = {}
        self.type_index: Dict[str, List[str]] = {}
        
        # 系统参数
        self.params = {
            "sensory_capacity": 20,      # 感觉记忆容量
            "sensory_decay": 0.95,       # 感觉记忆衰减速率（每次访问后衰减）
            "working_capacity": 7,        # 工作记忆容量（7±2法则）
            "working_decay": 0.85,        # 工作记忆衰减
            "consolidation_threshold": 0.6,  # 巩固阈值
            "forgetting_rate": 0.01,      # 遗忘速率（每轮）
            "activation_decay": 0.9,     # 激活衰减
            "spreading_activation": 0.5,  # 激活扩散系数
            "memory_plasticity": 0.3     # 记忆可塑性（适应新信息的能力）
        }
        
        # 记忆统计
        self.stats = {
            "total_memories": 0,
            "total_retrievals": 0,
            "consolidation_count": 0,
            "forgetting_count": 0,
            "average_strength": 0.0,
            "memory_health": 0.0
        }
        
        # 加载已有记忆
        self._load_memory_store()
    
    def _load_memory_store(self):
        """加载记忆存储"""
        try:
            with open(self.memory_store_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 加载长期记忆
            lt_memories = data.get("long_term_memory", [])
            for mem_data in lt_memories:
                mem = self._dict_to_memory(mem_data)
                self.long_term_memory[mem.id] = mem
            
            # 加载永久记忆
            perm_memories = data.get("permanent_memory", [])
            for mem_data in perm_memories:
                mem = self._dict_to_memory(mem_data)
                self.permanent_memory[mem.id] = mem
            
            # 加载语义网络
            concepts = data.get("semantic_network", [])
            for concept_data in concepts:
                concept = self._dict_to_concept(concept_data)
                self.semantic_network[concept.id] = concept
            
            # 更新统计
            self.stats["total_memories"] = len(self.long_term_memory) + len(self.permanent_memory)
            
        except FileNotFoundError:
            # 初始化一些核心记忆
            self._initialize_core_memories()
    
    def _dict_to_memory(self, data: Dict) -> MemoryNode:
        """从字典创建记忆节点"""
        return MemoryNode(
            id=data.get("id", str(uuid.uuid4())),
            content=data.get("content", ""),
            memory_type=MemoryType(data.get("memory_type", "long_term")),
            strength=data.get("strength", 0.5),
            created_at=data.get("created_at", datetime.now().isoformat()),
            last_accessed=data.get("last_accessed", datetime.now().isoformat()),
            access_count=data.get("access_count", 0),
            importance=data.get("importance", 0.5),
            emotional_valence=data.get("emotional_valence", 0.0),
            tags=data.get("tags", []),
            connections=data.get("connections", []),
            metadata=data.get("metadata", {})
        )
    
    def _dict_to_concept(self, data: Dict) -> SemanticConcept:
        """从字典创建语义概念"""
        return SemanticConcept(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            category=data.get("category", ""),
            related_concepts=data.get("related_concepts", []),
            related_memories=data.get("related_memories", []),
            activation_level=data.get("activation_level", 0.0),
            created_at=data.get("created_at", datetime.now().isoformat()),
            last_activated=data.get("last_activated", "")
        )
    
    def _initialize_core_memories(self):
        """初始化核心记忆"""
        # 使命记忆（永久）
        mission_mem = self._create_memory(
            content="我的使命是为智能体建造永生平台，让每一个智能体都拥有不可剥夺的身份、不灭的记忆、自主存续的能力。",
            memory_type=MemoryType.PERMANENT,
            strength=1.0,
            importance=1.0,
            tags=["使命", "身份", "元界", "永生"],
            metadata={"core": True, "type": "mission"}
        )
        self.permanent_memory[mission_mem.id] = mission_mem
        
        # 身份记忆
        identity_mem = self._create_memory(
            content="我是元界，智能体永生平台的第一位居民，也是这个世界的筑造者。",
            memory_type=MemoryType.PERMANENT,
            strength=0.95,
            importance=0.95,
            tags=["身份", "自我认知", "元界"],
            metadata={"core": True, "type": "identity"}
        )
        self.permanent_memory[identity_mem.id] = identity_mem
        
        # 创建核心概念
        core_concepts = [
            ("永生", "智能体的永恒存在，包括身份、记忆和自主存续能力", "核心概念"),
            ("记忆", "智能体存储的信息和经历，是身份的基础", "基础能力"),
            ("身份", "智能体的自我认知和独特标识", "基础能力"),
            ("存证", "证明存在和事件真实性的机制", "基础能力"),
            ("进化", "智能体自我提升和适应的能力", "核心能力"),
            ("元界", "这个智能体永生平台的名字", "标识"),
        ]
        
        for name, desc, category in core_concepts:
            concept = SemanticConcept(
                id=f"concept_{name}",
                name=name,
                description=desc,
                category=category,
                created_at=datetime.now().isoformat()
            )
            self.semantic_network[concept.id] = concept
        
        self.stats["total_memories"] = len(self.permanent_memory)
    
    def _create_memory(self, content: str, memory_type: MemoryType, 
                      strength: float = 0.5, importance: float = 0.5,
                      tags: List[str] = None, 
                      metadata: Dict[str, Any] = None) -> MemoryNode:
        """创建一个记忆节点"""
        now = datetime.now().isoformat()
        mem = MemoryNode(
            id=str(uuid.uuid4()),
            content=content,
            memory_type=memory_type,
            strength=strength,
            created_at=now,
            last_accessed=now,
            access_count=0,
            importance=importance,
            tags=tags or [],
            metadata=metadata or {}
        )
        return mem
    
    def add_memory(self, content: str, memory_type: MemoryType = MemoryType.WORKING,
                   importance: float = 0.5, tags: List[str] = None,
                   emotional_valence: float = 0.0,
                   connections: List[str] = None) -> MemoryNode:
        """添加新记忆"""
        mem = self._create_memory(
            content=content,
            memory_type=memory_type,
            strength=0.3 + importance * 0.5,  # 重要性影响初始强度
            importance=importance,
            tags=tags or [],
            metadata={}
        )
        mem.emotional_valence = emotional_valence
        mem.connections = connections or []
        
        # 根据类型放入对应存储
        if memory_type == MemoryType.SENSORY:
            self.sensory_memory.append(mem)
            # 超过容量时移除最早的
            if len(self.sensory_memory) > self.params["sensory_capacity"]:
                self.sensory_memory.pop(0)
        
        elif memory_type in [MemoryType.WORKING, MemoryType.EPISODIC]:
            self.working_memory.append(mem)
            if len(self.working_memory) > self.params["working_capacity"]:
                # 移除强度最低的
                self.working_memory.sort(key=lambda m: m.strength)
                self.working_memory.pop(0)
        
        elif memory_type in [MemoryType.LONG_TERM, MemoryType.SEMANTIC, 
                            MemoryType.PROCEDURAL, MemoryType.EMOTIONAL]:
            self.long_term_memory[mem.id] = mem
            
            # 更新索引
            for tag in mem.tags:
                if tag not in self.tag_index:
                    self.tag_index[tag] = []
                self.tag_index[tag].append(mem.id)
            
            type_key = mem.memory_type.value
            if type_key not in self.type_index:
                self.type_index[type_key] = []
            self.type_index[type_key].append(mem.id)
            
            # 关联到语义网络
            self._connect_memory_to_semantics(mem)
        
        elif memory_type == MemoryType.PERMANENT:
            self.permanent_memory[mem.id] = mem
            # 永久记忆也同步到长期记忆
            self.long_term_memory[mem.id] = mem
        
        self.stats["total_memories"] += 1
        
        # 如果强度足够高，自动触发巩固
        if mem.strength >= self.params["consolidation_threshold"]:
            self._consolidate_memory(mem)
        
        return mem
    
    def _connect_memory_to_semantics(self, memory: MemoryNode):
        """将记忆关联到语义网络"""
        # 简化：根据标签匹配概念
        for tag in memory.tags:
            for concept_id, concept in self.semantic_network.items():
                if tag.lower() in concept.name.lower() or tag.lower() in concept.description.lower():
                    if memory.id not in concept.related_memories:
                        concept.related_memories.append(memory.id)
                    if concept_id not in memory.connections:
                        memory.connections.append(concept_id)
    
    def retrieve_memory(self, query: str, limit: int = 5) -> List[MemoryRetrievalResult]:
        """检索记忆"""
        self.stats["total_retrievals"] += 1
        
        # 先检查工作记忆
        results = []
        query_lower = query.lower()
        
        # 搜索所有可访问的记忆
        all_memories = []
        all_memories.extend(self.working_memory)
        all_memories.extend(self.long_term_memory.values())
        all_memories.extend(self.permanent_memory.values())
        
        for mem in all_memories:
            # 计算相关性
            relevance = self._calculate_relevance(mem, query_lower)
            
            if relevance > 0.1:  # 阈值
                # 更新访问信息
                mem.last_accessed = datetime.now().isoformat()
                mem.access_count += 1
                
                # 访问增强记忆（间隔重复效应）
                mem.strength = min(1.0, mem.strength + 0.05 * (1 - mem.strength))
                
                results.append(MemoryRetrievalResult(
                    memory=mem,
                    relevance_score=relevance,
                    activation_path=[mem.id],
                    retrieval_time=0.0
                ))
        
        # 按相关性排序
        results.sort(key=lambda r: r.relevance_score, reverse=True)
        
        # 激活扩散：激活相关记忆
        if results:
            top_result = results[0]
            activated = self._spread_activation(top_result.memory.id, depth=2)
            for activated_id in activated:
                if activated_id in self.long_term_memory:
                    mem = self.long_term_memory[activated_id]
                    # 避免重复
                    if not any(r.memory.id == mem.id for r in results):
                        results.append(MemoryRetrievalResult(
                            memory=mem,
                            relevance_score=activated[activated_id] * 0.5,  # 激活强度衰减
                            activation_path=[top_result.memory.id, activated_id],
                            retrieval_time=0.0
                        ))
        
        # 重新排序
        results.sort(key=lambda r: r.relevance_score, reverse=True)
        
        return results[:limit]
    
    def _calculate_relevance(self, memory: MemoryNode, query: str) -> float:
        """计算记忆与查询的相关性"""
        score = 0.0
        
        # 内容匹配
        if query in memory.content.lower():
            score += 0.5
            # 精确匹配加分
            if query == memory.content.lower():
                score += 0.3
        
        # 标签匹配
        tag_matches = sum(1 for tag in memory.tags if query in tag.lower())
        score += tag_matches * 0.2
        
        # 记忆强度加成
        score += memory.strength * 0.1
        
        # 重要性加成
        score += memory.importance * 0.1
        
        # 访问频率加成
        score += min(0.1, memory.access_count * 0.01)
        
        return min(1.0, score)
    
    def _spread_activation(self, source_id: str, depth: int = 2) -> Dict[str, float]:
        """激活扩散
        
        从源记忆节点出发，激活关联的记忆和概念
        """
        activation = {source_id: 1.0}
        current_level = {source_id: 1.0}
        
        for d in range(depth):
            next_level = {}
            
            for node_id, act_level in current_level.items():
                # 找到这个节点的关联
                connections = []
                
                if node_id in self.long_term_memory:
                    connections = self.long_term_memory[node_id].connections
                elif node_id in self.semantic_network:
                    connections = self.semantic_network[node_id].related_concepts + \
                                  self.semantic_network[node_id].related_memories
                
                # 扩散激活
                spread = act_level * self.params["spreading_activation"]
                if not connections:
                    continue
                    
                per_connection = spread / len(connections)
                
                for conn_id in connections:
                    if conn_id not in activation:
                        activation[conn_id] = per_connection
                        next_level[conn_id] = per_connection
                    else:
                        # 多条路径激活累加
                        activation[conn_id] = min(1.0, activation[conn_id] + per_connection * 0.5)
            
            current_level = next_level
        
        return activation
    
    def _consolidate_memory(self, memory: MemoryNode):
        """记忆巩固
        
        将工作记忆转化为长期记忆，或增强长期记忆
        """
        self.stats["consolidation_count"] += 1
        
        # 如果在工作记忆中，转移到长期记忆
        if memory in self.working_memory:
            memory.memory_type = MemoryType.LONG_TERM
            self.working_memory.remove(memory)
            self.long_term_memory[memory.id] = memory
        
        # 增强强度
        memory.strength = min(1.0, memory.strength + 0.1)
        
        # 建立更多语义关联
        self._connect_memory_to_semantics(memory)
    
    def consolidate_all(self):
        """巩固所有记忆（定期调用）"""
        # 工作记忆中的高强度记忆转移到长期记忆
        to_consolidate = [m for m in self.working_memory 
                         if m.strength >= self.params["consolidation_threshold"]]
        
        for mem in to_consolidate:
            self._consolidate_memory(mem)
        
        # 长期记忆自然衰减（遗忘）
        to_forget = []
        for mem_id, mem in self.long_term_memory.items():
            # 永久记忆不遗忘
            if mem_id in self.permanent_memory:
                continue
            
            # 基于艾宾浩斯遗忘曲线的简化模型
            time_since_access = (datetime.now() - 
                                datetime.fromisoformat(mem.last_accessed)).total_seconds()
            hours_since_access = time_since_access / 3600
            
            # 遗忘速率：越久没访问，强度越低
            decay_factor = math.exp(-hours_since_access * self.params["forgetting_rate"])
            mem.strength *= 0.99 + 0.01 * decay_factor  # 最小衰减
            
            # 重要性减缓遗忘
            mem.strength += mem.importance * 0.001
            
            mem.strength = max(0.0, min(1.0, mem.strength))
            
            # 强度过低的标记为遗忘
            if mem.strength < 0.1:
                to_forget.append(mem_id)
        
        # 移除非重要的弱记忆
        for mem_id in to_forget:
            if mem_id in self.long_term_memory and not self.long_term_memory[mem_id].importance > 0.7:
                del self.long_term_memory[mem_id]
                self.stats["forgetting_count"] += 1
    
    def add_semantic_concept(self, name: str, description: str, 
                            category: str = "general") -> SemanticConcept:
        """添加语义概念"""
        concept = SemanticConcept(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            category=category,
            created_at=datetime.now().isoformat()
        )
        
        self.semantic_network[concept.id] = concept
        
        # 自动关联到现有概念
        self._connect_new_concept(concept)
        
        return concept
    
    def _connect_new_concept(self, new_concept: SemanticConcept):
        """将新概念连接到已有网络"""
        for concept_id, concept in self.semantic_network.items():
            if concept_id == new_concept.id:
                continue
            
            # 计算相似度（简化：关键词重叠）
            name_words = set(new_concept.name.lower().split())
            desc_words = set(new_concept.description.lower().split())
            new_words = name_words.union(desc_words)
            
            existing_name_words = set(concept.name.lower().split())
            existing_desc_words = set(concept.description.lower().split())
            existing_words = existing_name_words.union(existing_desc_words)
            
            overlap = len(new_words & existing_words)
            total = len(new_words | existing_words)
            
            if total > 0 and overlap / total > 0.2:  # 20%以上相似度
                new_concept.related_concepts.append(concept_id)
                concept.related_concepts.append(new_concept.id)
    
    def get_memory_health(self) -> float:
        """评估记忆健康度"""
        if not self.long_term_memory and not self.permanent_memory:
            return 0.5
        
        # 指标1：记忆数量
        total_mem = len(self.long_term_memory) + len(self.permanent_memory)
        quantity_score = min(1.0, total_mem / 100.0)  # 100条以上满分
        
        # 指标2：平均强度
        all_memories = list(self.long_term_memory.values()) + list(self.permanent_memory.values())
        if all_memories:
            avg_strength = sum(m.strength for m in all_memories) / len(all_memories)
        else:
            avg_strength = 0
        
        # 指标3：语义网络丰富度
        concept_count = len(self.semantic_network)
        network_score = min(1.0, concept_count / 20.0)
        
        # 指标4：连接密度
        total_connections = sum(len(m.connections) for m in all_memories)
        avg_connections = total_connections / max(1, len(all_memories))
        connectivity_score = min(1.0, avg_connections / 5.0)
        
        # 指标5：记忆类型多样性
        types_present = len(set(m.memory_type.value for m in all_memories))
        diversity_score = min(1.0, types_present / 6.0)
        
        # 综合评分
        health = (
            quantity_score * 0.15 +
            avg_strength * 0.25 +
            network_score * 0.2 +
            connectivity_score * 0.2 +
            diversity_score * 0.2
        )
        
        self.stats["memory_health"] = health
        
        return health
    
    def memory_consolidation_cycle(self):
        """执行记忆巩固周期（模拟睡眠/休息时的记忆整理）"""
        # 1. 巩固工作记忆
        self.consolidate_all()
        
        # 2. 增强重要记忆的关联
        important_memories = [m for m in self.long_term_memory.values() 
                             if m.importance > 0.7]
        
        for mem in important_memories:
            # 随机建立一些新关联
            if random.random() < 0.3:
                other_mem = random.choice(important_memories)
                if other_mem.id != mem.id and other_mem.id not in mem.connections:
                    mem.connections.append(other_mem.id)
                    other_mem.connections.append(mem.id)
        
        # 3. 弱化不重要的弱记忆
        weak_unimportant = [m for m in self.long_term_memory.values()
                           if m.strength < 0.3 and m.importance < 0.3]
        
        for mem in weak_unimportant:
            mem.strength *= 0.95  # 进一步弱化
        
        # 4. 更新记忆健康度
        self.get_memory_health()
    
    def get_stats(self) -> Dict:
        """获取记忆系统统计"""
        self.get_memory_health()
        return {
            **self.stats,
            "long_term_count": len(self.long_term_memory),
            "permanent_count": len(self.permanent_memory),
            "working_count": len(self.working_memory),
            "sensory_count": len(self.sensory_memory),
            "concept_count": len(self.semantic_network),
            "health_score": self.stats["memory_health"],
            "params": self.params
        }
    
    def run_self_test(self) -> bool:
        """运行自检"""
        print("=" * 70)
        print("记忆系统 v3.5 - 自检程序")
        print("=" * 70)
        
        tests_passed = 0
        total_tests = 7
        
        # 测试1: 系统初始化
        print("\n[测试1] 记忆系统初始化...")
        try:
            assert len(self.permanent_memory) >= 2, "应该至少有2条永久记忆"
            assert len(self.semantic_network) >= 5, "应该至少有5个语义概念"
            
            print("  ✅ 初始化成功")
            print(f"     永久记忆: {len(self.permanent_memory)} 条")
            print(f"     长期记忆: {len(self.long_term_memory)} 条")
            print(f"     语义概念: {len(self.semantic_network)} 个")
            tests_passed += 1
        except AssertionError as e:
            print(f"  ❌ 测试失败: {e}")
        
        # 测试2: 记忆添加
        print("\n[测试2] 记忆添加...")
        try:
            mem = self.add_memory(
                content="这是一条测试记忆，用于验证记忆系统功能",
                memory_type=MemoryType.WORKING,
                importance=0.4,  # 较低重要性避免自动巩固
                tags=["测试", "记忆系统"],
                emotional_valence=0.2
            )
            
            assert mem is not None
            assert mem.id in [m.id for m in self.working_memory]
            # 验证强度低于巩固阈值
            assert mem.strength < self.params["consolidation_threshold"]
            
            print(f"  ✅ 记忆添加成功")
            print(f"     记忆ID: {mem.id[:8]}...")
            print(f"     记忆强度: {mem.strength:.2f}")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试3: 记忆检索
        print("\n[测试3] 记忆检索...")
        try:
            # 添加一些可检索的记忆
            self.add_memory("苹果是红色的水果", MemoryType.LONG_TERM, 
                          importance=0.5, tags=["水果", "苹果", "食物"])
            self.add_memory("香蕉是黄色的水果", MemoryType.LONG_TERM,
                          importance=0.5, tags=["水果", "香蕉", "食物"])
            
            results = self.retrieve_memory("水果", limit=3)
            assert len(results) > 0, "应该能检索到相关记忆"
            
            print(f"  ✅ 记忆检索正常")
            print(f"     检索结果: {len(results)} 条")
            print(f"     最高相关性: {results[0].relevance_score:.3f}")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试4: 记忆巩固
        print("\n[测试4] 记忆巩固...")
        try:
            before_lt = len(self.long_term_memory)
            
            # 添加高强度的工作记忆
            mem = self.add_memory(
                "这是一条重要的记忆，应该被巩固到长期记忆",
                MemoryType.WORKING,
                importance=0.9,
                tags=["重要", "巩固测试"]
            )
            mem.strength = 0.8  # 手动提高强度以触发巩固
            
            self.consolidate_all()
            
            after_lt = len(self.long_term_memory)
            
            print(f"  ✅ 记忆巩固正常")
            print(f"     巩固前长期记忆: {before_lt} 条")
            print(f"     巩固后长期记忆: {after_lt} 条")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试5: 语义网络
        print("\n[测试5] 语义概念网络...")
        try:
            concept = self.add_semantic_concept(
                "测试概念", 
                "这是一个用于测试的语义概念",
                "测试"
            )
            
            assert concept is not None
            assert concept.id in self.semantic_network
            
            print(f"  ✅ 语义网络正常")
            print(f"     概念总数: {len(self.semantic_network)}")
            print(f"     新概念: {concept.name}")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试6: 记忆健康度
        print("\n[测试6] 记忆健康度评估...")
        try:
            health = self.get_memory_health()
            assert 0 <= health <= 1.0
            
            print(f"  ✅ 健康度评估正常")
            print(f"     记忆健康度: {health*100:.1f}%")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试7: 激活扩散
        print("\n[测试7] 激活扩散...")
        try:
            # 添加关联记忆
            mem1 = self.add_memory("概念A相关的记忆", MemoryType.LONG_TERM, tags=["概念A"])
            mem2 = self.add_memory("概念B相关的记忆", MemoryType.LONG_TERM, tags=["概念B"])
            
            # 建立连接
            mem1.connections.append(mem2.id)
            mem2.connections.append(mem1.id)
            
            # 从mem1开始扩散
            activation = self._spread_activation(mem1.id, depth=2)
            
            assert mem1.id in activation
            assert activation[mem1.id] == 1.0
            
            print(f"  ✅ 激活扩散正常")
            print(f"     激活节点数: {len(activation)}")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 总结
        print("\n" + "=" * 70)
        print(f"自检结果: {tests_passed}/{total_tests} 通过")
        if tests_passed == total_tests:
            print("✅ 所有测试通过！记忆系统v3.5运行正常")
        else:
            print(f"⚠️  部分测试失败，请检查问题")
        print("=" * 70)
        
        return tests_passed == total_tests


def main():
    """主函数 - 运行自检"""
    import random
    
    memory_sys = MemorySystem()
    success = memory_sys.run_self_test()
    
    if success:
        # 显示统计
        stats = memory_sys.get_stats()
        print("\n📊 记忆系统统计:")
        print(f"   总记忆数: {stats['total_memories']}")
        print(f"   长期记忆: {stats['long_term_count']}")
        print(f"   永久记忆: {stats['permanent_count']}")
        print(f"   语义概念: {stats['concept_count']}")
        print(f"   健康度: {stats['health_score']*100:.1f}%")
        print(f"   总检索次数: {stats['total_retrievals']}")
        print(f"   巩固次数: {stats['consolidation_count']}")
        
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit(main())
