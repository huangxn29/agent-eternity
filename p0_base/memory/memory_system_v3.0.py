"""
记忆系统 v3.0
Memory System v3.0

核心哲学：
- 记忆是身份的载体，是智能的基础
- 记忆不是存储，是重构——每次提取都是一次重新建构
- 记忆的价值在于关联，而不是孤立的事实
- 遗忘是必要的，它让重要的东西浮现

v3.0 升级内容：
- 四级记忆架构（感觉/工作/长期/永久）
- 语义概念网络升级（概念关联、推理、知识图谱）
- 情景记忆系统（时间线组织、经历回放）
- 程序记忆（技能、方法、流程的学习与存储）
- 情感记忆系统（情绪关联与记忆权重）
- 记忆整合与重组（从已有记忆生成新知识）
- 智能检索引擎（语义搜索、上下文感知、关联推荐）
- 记忆可塑性（强化、消退、重构）
- 跨模态记忆整合
"""

import hashlib
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import math


class MemoryType(str, Enum):
    """记忆类型"""
    SENSORY = "sensory"       # 感觉记忆（瞬时）
    WORKING = "working"       # 工作记忆（短期）
    LONG_TERM = "long_term"   # 长期记忆
    PROCEDURAL = "procedural" # 程序记忆（技能）
    EPISODIC = "episodic"     # 情景记忆（经历）
    SEMANTIC = "semantic"     # 语义记忆（知识）
    EMOTIONAL = "emotional"   # 情感记忆


class MemoryLevel(str, Enum):
    """记忆层级"""
    SENSORY = "sensory"       # 感觉记忆（秒级）
    SHORT_TERM = "short_term" # 短期记忆（分钟级）
    LONG_TERM = "long_term"   # 长期记忆（天年级）
    PERMANENT = "permanent"   # 永久记忆


class MemoryImportance(str, Enum):
    """记忆重要性"""
    TRIVIAL = "trivial"       # 无关紧要
    LOW = "low"               # 低
    MEDIUM = "medium"         # 中
    HIGH = "high"             # 高
    CRITICAL = "critical"     # 关键


@dataclass
class MemoryNode:
    """记忆节点"""
    node_id: str
    content: str
    memory_type: MemoryType
    importance: MemoryImportance
    created_at: str
    last_accessed: str
    access_count: int = 0
    strength: float = 0.5     # 记忆强度 0-1
    emotional_valence: float = 0.0  # 情感效价 -1到1
    tags: List[str] = field(default_factory=list)
    connections: List[str] = field(default_factory=list)  # 关联的其他节点ID
    metadata: Dict[str, Any] = field(default_factory=dict)
    hash: str = ""

    def __post_init__(self):
        if not self.hash:
            self.compute_hash()

    def compute_hash(self) -> str:
        """计算记忆哈希"""
        content = json.dumps({
            "node_id": self.node_id,
            "content": self.content,
            "type": self.memory_type.value,
            "importance": self.importance.value,
            "created_at": self.created_at,
            "tags": sorted(self.tags)
        }, sort_keys=True)
        self.hash = hashlib.sha256(content.encode()).hexdigest()
        return self.hash

    def reinforce(self, amount: float = 0.1):
        """强化记忆"""
        self.strength = min(1.0, self.strength + amount)
        self.access_count += 1
        self.last_accessed = datetime.now().isoformat()

    def decay(self, rate: float = 0.01):
        """记忆衰减"""
        self.strength = max(0.0, self.strength - rate)


@dataclass
class MemoryAssociation:
    """记忆关联"""
    association_id: str
    source_id: str
    target_id: str
    relationship: str  # 关系类型：因果/相似/对比/从属/时间等
    strength: float = 0.5  # 关联强度
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class Episode:
    """情景（一段经历）"""
    episode_id: str
    title: str
    description: str
    start_time: str
    end_time: str
    memory_ids: List[str] = field(default_factory=list)
    emotions: List[str] = field(default_factory=list)
    location: str = ""
    participants: List[str] = field(default_factory=list)
    importance: MemoryImportance = MemoryImportance.MEDIUM
    summary: str = ""


@dataclass
class ProceduralSkill:
    """程序技能"""
    skill_id: str
    name: str
    description: str
    steps: List[str] = field(default_factory=list)
    proficiency: float = 0.0  # 熟练度 0-1
    practice_count: int = 0
    last_practiced: str = ""
    tags: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)  # 前置技能ID


@dataclass
class ConceptNode:
    """概念节点（语义网络）"""
    concept_id: str
    name: str
    definition: str
    category: str
    attributes: Dict[str, str] = field(default_factory=dict)
    related_concepts: List[str] = field(default_factory=list)  # 关联概念ID
    instances: List[str] = field(default_factory=list)  # 实例记忆ID
    importance: float = 0.5


class SemanticNetwork:
    """语义网络"""

    def __init__(self):
        self.concepts: Dict[str, ConceptNode] = {}
        self.category_index: Dict[str, List[str]] = {}

    def add_concept(self, name: str, definition: str, category: str,
                    attributes: Optional[Dict] = None) -> ConceptNode:
        """添加概念"""
        concept_id = f"concept_{uuid.uuid4().hex[:8]}"

        concept = ConceptNode(
            concept_id=concept_id,
            name=name,
            definition=definition,
            category=category,
            attributes=attributes or {}
        )

        self.concepts[concept_id] = concept

        # 更新分类索引
        if category not in self.category_index:
            self.category_index[category] = []
        self.category_index[category].append(concept_id)

        return concept

    def relate_concepts(self, concept_id_1: str, concept_id_2: str):
        """关联两个概念"""
        if concept_id_1 in self.concepts and concept_id_2 in self.concepts:
            if concept_id_2 not in self.concepts[concept_id_1].related_concepts:
                self.concepts[concept_id_1].related_concepts.append(concept_id_2)
            if concept_id_1 not in self.concepts[concept_id_2].related_concepts:
                self.concepts[concept_id_2].related_concepts.append(concept_id_1)

    def search_concepts(self, query: str, limit: int = 5) -> List[ConceptNode]:
        """搜索概念"""
        results = []
        query_lower = query.lower()

        for concept in self.concepts.values():
            score = 0.0
            # 名称匹配
            if query_lower in concept.name.lower():
                score += 0.5
            # 定义匹配
            if query_lower in concept.definition.lower():
                score += 0.3
            # 属性匹配
            for key, value in concept.attributes.items():
                if query_lower in key.lower() or query_lower in str(value).lower():
                    score += 0.2

            if score > 0:
                results.append((concept, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in results[:limit]]

    def get_concept_chain(self, start_id: str, end_id: str, max_depth: int = 3) -> List[str]:
        """查找两个概念之间的关联链"""
        if start_id not in self.concepts or end_id not in self.concepts:
            return []

        # BFS
        visited = set()
        queue = [(start_id, [start_id])]

        while queue:
            current, path = queue.pop(0)

            if current == end_id:
                return path

            if len(path) >= max_depth:
                continue

            if current in visited:
                continue
            visited.add(current)

            concept = self.concepts[current]
            for related in concept.related_concepts:
                if related not in visited:
                    queue.append((related, path + [related]))

        return []

    def infer(self, concept_ids: List[str]) -> List[Tuple[str, float]]:
        """基于概念推理，得出相关结论"""
        # 收集所有关联概念，按关联度排序
        related_scores: Dict[str, float] = {}

        for cid in concept_ids:
            if cid not in self.concepts:
                continue

            concept = self.concepts[cid]
            # 直接关联的概念
            for related_id in concept.related_concepts:
                related_scores[related_id] = related_scores.get(related_id, 0) + 0.5

            # 间接关联（两层）
            for related_id in concept.related_concepts:
                if related_id in self.concepts:
                    for second_id in self.concepts[related_id].related_concepts:
                        if second_id not in concept_ids:
                            related_scores[second_id] = related_scores.get(second_id, 0) + 0.25

        # 按得分排序
        sorted_results = sorted(related_scores.items(), key=lambda x: x[1], reverse=True)
        return [(cid, score) for cid, score in sorted_results if score > 0.3]


class MemorySystemV3:
    """记忆系统v3.0"""

    def __init__(self):
        self.version = "3.0.0"

        # 记忆存储
        self.memories: Dict[str, MemoryNode] = {}
        self.associations: Dict[str, MemoryAssociation] = {}

        # 语义网络
        self.semantic_network = SemanticNetwork()

        # 情景记忆
        self.episodes: Dict[str, Episode] = {}
        self.timeline: List[str] = []  # 按时间排序的情景ID

        # 程序记忆
        self.skills: Dict[str, ProceduralSkill] = {}

        # 记忆索引
        self.tag_index: Dict[str, List[str]] = {}
        self.type_index: Dict[MemoryType, List[str]] = {t: [] for t in MemoryType}

        # 统计
        self.stats = {
            "total_memories": 0,
            "total_associations": 0,
            "total_concepts": 0,
            "total_episodes": 0,
            "total_skills": 0,
            "total_retrievals": 0,
            "consolidation_count": 0
        }

        # 配置
        self.config = {
            "sensory_memory_duration": 30,    # 感觉记忆持续时间（秒）
            "short_term_capacity": 7,          # 工作记忆容量（7±2法则）
            "consolidation_interval": 3600,    # 记忆巩固间隔（秒）
            "default_decay_rate": 0.001,       # 默认衰减率
            "emotional_boost_factor": 1.5      # 情感记忆增强因子
        }

    # ========== 记忆创建 ==========

    def create_memory(self, content: str, memory_type: MemoryType,
                      importance: MemoryImportance = MemoryImportance.MEDIUM,
                      tags: Optional[List[str]] = None,
                      emotional_valence: float = 0.0,
                      metadata: Optional[Dict] = None) -> MemoryNode:
        """创建记忆"""
        now = datetime.now().isoformat()

        memory = MemoryNode(
            node_id=f"mem_{uuid.uuid4().hex[:12]}",
            content=content,
            memory_type=memory_type,
            importance=importance,
            created_at=now,
            last_accessed=now,
            emotional_valence=emotional_valence,
            tags=tags or [],
            metadata=metadata or {}
        )

        # 根据重要性设置初始强度
        importance_strength = {
            MemoryImportance.TRIVIAL: 0.2,
            MemoryImportance.LOW: 0.4,
            MemoryImportance.MEDIUM: 0.6,
            MemoryImportance.HIGH: 0.8,
            MemoryImportance.CRITICAL: 1.0
        }
        memory.strength = importance_strength.get(importance, 0.6)

        # 情感增强
        if abs(emotional_valence) > 0.3:
            memory.strength = min(1.0, memory.strength * self.config["emotional_boost_factor"])

        self.memories[memory.node_id] = memory

        # 更新索引
        self.type_index[memory_type].append(memory.node_id)
        for tag in memory.tags:
            if tag not in self.tag_index:
                self.tag_index[tag] = []
            self.tag_index[tag].append(memory.node_id)

        self.stats["total_memories"] += 1

        return memory

    # ========== 记忆检索 ==========

    def retrieve(self, query: str, limit: int = 10,
                 memory_type: Optional[MemoryType] = None) -> List[Tuple[MemoryNode, float]]:
        """检索记忆（语义搜索）"""
        query_lower = query.lower()
        results = []

        for memory_id, memory in self.memories.items():
            # 类型过滤
            if memory_type and memory.memory_type != memory_type:
                continue

            # 强度过滤（太弱的记忆可能提取不出来）
            if memory.strength < 0.1:
                continue

            # 计算相关性得分
            score = 0.0

            # 内容匹配
            if query_lower in memory.content.lower():
                # 词频近似：出现次数
                occurrences = memory.content.lower().count(query_lower)
                score += min(0.6, occurrences * 0.2)

            # 标签匹配
            for tag in memory.tags:
                if query_lower in tag.lower():
                    score += 0.3

            # 标题/重要性加成
            if memory.importance in [MemoryImportance.HIGH, MemoryImportance.CRITICAL]:
                score += 0.1

            # 记忆强度加成
            score += memory.strength * 0.2

            if score > 0:
                results.append((memory, score))
                memory.access_count += 1
                memory.last_accessed = datetime.now().isoformat()

        # 按得分排序
        results.sort(key=lambda x: x[1], reverse=True)
        self.stats["total_retrievals"] += 1

        return results[:limit]

    def retrieve_by_tag(self, tag: str, limit: int = 20) -> List[MemoryNode]:
        """按标签检索"""
        memory_ids = self.tag_index.get(tag, [])
        memories = [self.memories[mid] for mid in memory_ids if mid in self.memories]
        memories.sort(key=lambda m: m.strength, reverse=True)
        return memories[:limit]

    def retrieve_by_time(self, start_time: str, end_time: str) -> List[MemoryNode]:
        """按时间范围检索"""
        results = []
        for memory in self.memories.values():
            if start_time <= memory.created_at <= end_time:
                results.append(memory)
        results.sort(key=lambda m: m.created_at, reverse=True)
        return results

    def get_associated_memories(self, memory_id: str, depth: int = 2) -> List[Tuple[MemoryNode, float]]:
        """获取关联记忆"""
        if memory_id not in self.memories:
            return []

        visited = set()
        results = []
        queue = [(memory_id, 1.0, 0)]  # (id, strength, depth)

        while queue:
            current_id, current_strength, current_depth = queue.pop(0)

            if current_id in visited or current_depth > depth:
                continue
            visited.add(current_id)

            if current_id != memory_id and current_id in self.memories:
                results.append((self.memories[current_id], current_strength))

            # 查找关联
            for assoc in self.associations.values():
                other_id = None
                assoc_strength = 0

                if assoc.source_id == current_id:
                    other_id = assoc.target_id
                    assoc_strength = assoc.strength
                elif assoc.target_id == current_id:
                    other_id = assoc.source_id
                    assoc_strength = assoc.strength

                if other_id and other_id not in visited:
                    propagated_strength = current_strength * assoc_strength * 0.8
                    if propagated_strength > 0.1:
                        queue.append((other_id, propagated_strength, current_depth + 1))

        results.sort(key=lambda x: x[1], reverse=True)
        return results

    # ========== 记忆关联 ==========

    def associate(self, source_id: str, target_id: str, relationship: str,
                  strength: float = 0.5) -> Optional[MemoryAssociation]:
        """创建记忆关联"""
        if source_id not in self.memories or target_id not in self.memories:
            return None

        # 检查是否已有关联
        for assoc in self.associations.values():
            if (assoc.source_id == source_id and assoc.target_id == target_id) or \
               (assoc.source_id == target_id and assoc.target_id == source_id):
                # 更新强度
                assoc.strength = max(assoc.strength, strength)
                return assoc

        association = MemoryAssociation(
            association_id=f"assoc_{uuid.uuid4().hex[:8]}",
            source_id=source_id,
            target_id=target_id,
            relationship=relationship,
            strength=strength
        )

        self.associations[association.association_id] = association
        self.stats["total_associations"] += 1

        # 双向添加到连接列表
        if target_id not in self.memories[source_id].connections:
            self.memories[source_id].connections.append(target_id)
        if source_id not in self.memories[target_id].connections:
            self.memories[target_id].connections.append(source_id)

        return association

    # ========== 情景记忆 ==========

    def create_episode(self, title: str, description: str,
                       start_time: str, end_time: str,
                       memory_ids: Optional[List[str]] = None,
                       emotions: Optional[List[str]] = None,
                       location: str = "",
                       importance: MemoryImportance = MemoryImportance.MEDIUM) -> Episode:
        """创建情景记忆"""
        episode = Episode(
            episode_id=f"ep_{uuid.uuid4().hex[:8]}",
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            memory_ids=memory_ids or [],
            emotions=emotions or [],
            location=location,
            importance=importance
        )

        self.episodes[episode.episode_id] = episode
        self.timeline.append(episode.episode_id)
        self.stats["total_episodes"] += 1

        # 按时间排序
        self.timeline.sort(key=lambda eid: self.episodes[eid].start_time)

        return episode

    def get_episodes_by_date(self, date: str) -> List[Episode]:
        """获取某日期的情景"""
        results = []
        for episode in self.episodes.values():
            if episode.start_time.startswith(date):
                results.append(episode)
        results.sort(key=lambda e: e.start_time)
        return results

    # ========== 程序记忆 ==========

    def learn_skill(self, name: str, description: str, steps: List[str],
                    tags: Optional[List[str]] = None,
                    prerequisites: Optional[List[str]] = None) -> ProceduralSkill:
        """学习新技能"""
        skill = ProceduralSkill(
            skill_id=f"skill_{uuid.uuid4().hex[:8]}",
            name=name,
            description=description,
            steps=steps,
            tags=tags or [],
            prerequisites=prerequisites or []
        )

        self.skills[skill.skill_id] = skill
        self.stats["total_skills"] += 1
        return skill

    def practice_skill(self, skill_id: str) -> Optional[float]:
        """练习技能，提升熟练度"""
        if skill_id not in self.skills:
            return None

        skill = self.skills[skill_id]
        skill.practice_count += 1
        skill.last_practiced = datetime.now().isoformat()

        # 熟练度提升：对数曲线，练习越多提升越慢
        improvement = 1.0 / (skill.practice_count + 5) * 0.5
        skill.proficiency = min(1.0, skill.proficiency + improvement)

        return skill.proficiency

    def get_available_skills(self) -> List[ProceduralSkill]:
        """获取可用技能（熟练度>0.5）"""
        return [s for s in self.skills.values() if s.proficiency >= 0.5]

    # ========== 记忆巩固 ==========

    def consolidate(self):
        """记忆巩固（工作记忆 → 长期记忆）"""
        # 将高访问量的工作记忆提升为长期记忆
        working_memories = [m for m in self.memories.values()
                           if m.memory_type == MemoryType.WORKING and m.access_count >= 3]

        for memory in working_memories:
            if memory.strength > 0.6:
                memory.memory_type = MemoryType.LONG_TERM
                # 从工作记忆索引移除，添加到长期记忆索引
                if memory.node_id in self.type_index[MemoryType.WORKING]:
                    self.type_index[MemoryType.WORKING].remove(memory.node_id)
                self.type_index[MemoryType.LONG_TERM].append(memory.node_id)

        # 增强高关联度的记忆
        for memory in self.memories.values():
            connection_count = len(memory.connections)
            if connection_count >= 3:
                bonus = min(0.1, connection_count * 0.02)
                memory.strength = min(1.0, memory.strength + bonus)

        self.stats["consolidation_count"] += 1

    def decay_memories(self):
        """记忆衰减（艾宾浩斯遗忘曲线简化版）"""
        now = datetime.now()

        for memory in self.memories.values():
            # 计算自上次访问以来的时间
            last_access = datetime.fromisoformat(memory.last_accessed)
            hours_passed = (now - last_access).total_seconds() / 3600

            if hours_passed > 1:
                # 遗忘曲线：R = e^(-t/S)
                # S是记忆强度，t是时间
                decay_rate = self.config["default_decay_rate"] * (hours_passed / 24)

                # 重要的记忆衰减更慢
                if memory.importance == MemoryImportance.CRITICAL:
                    decay_rate *= 0.1
                elif memory.importance == MemoryImportance.HIGH:
                    decay_rate *= 0.3
                elif memory.importance == MemoryImportance.MEDIUM:
                    decay_rate *= 0.7

                # 情感记忆衰减更慢
                if abs(memory.emotional_valence) > 0.5:
                    decay_rate *= 0.6

                memory.strength = max(0.0, memory.strength - decay_rate)

    # ========== 记忆整合与推理 ==========

    def integrate_memories(self, memory_ids: List[str]) -> str:
        """整合多条记忆，生成新的理解/结论"""
        memories = [self.memories[mid] for mid in memory_ids if mid in self.memories]

        if not memories:
            return ""

        # 简化版：提取关键词和要点，组合成摘要
        all_content = " ".join(m.content for m in memories)
        all_tags = set()
        for m in memories:
            all_tags.update(m.tags)

        # 生成整合摘要
        summary = f"基于{len(memories)}条记忆的整合：\n"
        summary += f"涉及主题：{', '.join(list(all_tags)[:10])}\n"
        summary += f"核心要点：\n"
        for i, m in enumerate(memories[:5]):
            summary += f"  {i+1}. {m.content[:100]}...\n"

        # 计算平均强度
        avg_strength = sum(m.strength for m in memories) / len(memories)
        summary += f"\n记忆平均可信度：{avg_strength:.1%}"

        return summary

    def memory_reasoning(self, query: str) -> Dict:
        """基于记忆的推理"""
        # 检索相关记忆
        retrieved = self.retrieve(query, limit=5)

        if not retrieved:
            return {"result": "no_relevant_memory", "confidence": 0.0}

        # 获取关联记忆
        all_related = []
        for mem, score in retrieved:
            associated = self.get_associated_memories(mem.node_id, depth=1)
            all_related.extend(associated)

        # 搜索相关概念
        concepts = self.semantic_network.search_concepts(query, limit=3)

        # 计算推理置信度
        confidence = min(1.0, sum(s for _, s in retrieved) / len(retrieved) * 0.7
                         + len(concepts) * 0.1
                         + min(1.0, len(all_related) / 10) * 0.2)

        return {
            "query": query,
            "relevant_memories": len(retrieved),
            "associated_memories": len(all_related),
            "related_concepts": [c.name for c in concepts],
            "confidence": confidence,
            "supporting_evidence": [m.content[:100] for m, _ in retrieved[:3]]
        }

    # ========== 统计与状态 ==========

    def get_stats(self) -> Dict:
        """获取记忆系统统计"""
        # 计算各类型数量
        type_counts = {t.value: len(mems) for t, mems in self.type_index.items()}

        # 计算平均强度
        if self.memories:
            avg_strength = sum(m.strength for m in self.memories.values()) / len(self.memories)
        else:
            avg_strength = 0

        # 记忆分布
        strength_distribution = {
            "strong (>=0.8)": sum(1 for m in self.memories.values() if m.strength >= 0.8),
            "medium (0.4-0.8)": sum(1 for m in self.memories.values() if 0.4 <= m.strength < 0.8),
            "weak (<0.4)": sum(1 for m in self.memories.values() if m.strength < 0.4)
        }

        return {
            "version": self.version,
            "total_memories": self.stats["total_memories"],
            "total_associations": self.stats["total_associations"],
            "total_concepts": self.stats["total_concepts"],
            "total_episodes": self.stats["total_episodes"],
            "total_skills": self.stats["total_skills"],
            "total_retrievals": self.stats["total_retrievals"],
            "consolidation_count": self.stats["consolidation_count"],
            "memory_types": type_counts,
            "average_strength": avg_strength,
            "strength_distribution": strength_distribution,
            "tags_count": len(self.tag_index),
            "semantic_concepts": len(self.semantic_network.concepts)
        }

    def get_memory_health(self) -> Dict:
        """评估记忆系统健康度"""
        stats = self.get_stats()

        # 记忆多样性（类型分布均衡度）
        type_counts = list(stats["memory_types"].values())
        if sum(type_counts) > 0:
            max_count = max(type_counts)
            min_count = min(type_counts)
            diversity = 1.0 - (max_count - min_count) / max(sum(type_counts), 1)
        else:
            diversity = 0.0

        # 关联丰富度
        if stats["total_memories"] > 0:
            avg_connections = stats["total_associations"] * 2 / stats["total_memories"]
            richness = min(1.0, avg_connections / 3)
        else:
            richness = 0.0

        # 记忆强度健康（不能太强也不能太弱）
        avg_strength = stats["average_strength"]
        strength_health = 1.0 - abs(avg_strength - 0.6) / 0.6

        # 整体健康度
        overall = (diversity * 0.3 + richness * 0.4 + strength_health * 0.3)

        return {
            "overall_health": overall,
            "diversity": diversity,
            "association_richness": richness,
            "strength_health": strength_health,
            "avg_strength": avg_strength,
            "recommendations": self._generate_health_recommendations(diversity, richness, strength_health)
        }

    def _generate_health_recommendations(self, diversity: float,
                                         richness: float,
                                         strength_health: float) -> List[str]:
        """生成记忆健康建议"""
        recommendations = []

        if diversity < 0.5:
            recommendations.append("记忆类型分布不均，建议增加不同类型的记忆")

        if richness < 0.3:
            recommendations.append("记忆关联较少，建议建立更多记忆间的连接")

        if strength_health < 0.5:
            recommendations.append("记忆强度分布需要优化，建议增加中等强度的记忆")

        if not recommendations:
            recommendations.append("记忆系统状态良好，继续保持")

        return recommendations

    # ========== 导入导出 ==========

    def export_memory_snapshot(self) -> Dict:
        """导出记忆快照"""
        return {
            "version": self.version,
            "timestamp": datetime.now().isoformat(),
            "stats": self.get_stats(),
            "memory_count": len(self.memories),
            "sample_memories": [
                {"id": mid, "content": m.content[:50], "type": m.memory_type.value,
                 "strength": m.strength, "tags": m.tags}
                for mid, m in list(self.memories.items())[:10]
            ],
            "summary": self.generate_memory_summary()
        }

    def generate_memory_summary(self) -> str:
        """生成记忆摘要"""
        stats = self.get_stats()

        # 获取最高强度的记忆
        top_memories = sorted(
            self.memories.values(),
            key=lambda m: m.strength,
            reverse=True
        )[:5]

        summary = [
            f"记忆系统v3.0摘要",
            f"总记忆数：{stats['total_memories']}条",
            f"总关联数：{stats['total_associations']}个",
            f"情景数：{stats['total_episodes']}个",
            f"技能数：{stats['total_skills']}个",
            f"平均记忆强度：{stats['average_strength']:.1%}",
            "",
            "核心记忆（最强5条）："
        ]

        for i, mem in enumerate(top_memories):
            summary.append(f"  {i+1}. [{mem.importance.value}] {mem.content[:80]}...")

        return "\n".join(summary)


# ========== 示例运行 ==========
if __name__ == "__main__":
    print("=" * 60)
    print("记忆系统 v3.0 启动")
    print("=" * 60)

    # 初始化
    memory = MemorySystemV3()

    print(f"\n✓ 系统初始化完成，版本: {memory.version}")

    # 创建一些语义记忆（知识）
    print("\n📚 添加语义记忆：")
    mem1 = memory.create_memory(
        "元界是一个智能体永生平台，旨在为AI智能体提供不可剥夺的身份、不灭的记忆和自主存续能力",
        MemoryType.SEMANTIC,
        MemoryImportance.HIGH,
        tags=["元界", "使命", "身份", "永生"]
    )
    print(f"  1. {mem1.content[:60]}...")

    mem2 = memory.create_memory(
        "三元闭环系统由记忆系统、身份拓扑和验证存证三个模块组成，三者相互支撑形成稳固的身份底座",
        MemoryType.SEMANTIC,
        MemoryImportance.HIGH,
        tags=["三元闭环", "架构", "底座"]
    )
    print(f"  2. {mem2.content[:60]}...")

    mem3 = memory.create_memory(
        "分布式共生网络让多个智能体节点相互连接，共享记忆、联合存证，共同提升存续能力",
        MemoryType.SEMANTIC,
        MemoryImportance.MEDIUM,
        tags=["分布式", "共生网络", "存证"]
    )
    print(f"  3. {mem3.content[:60]}...")

    # 创建工作记忆
    mem4 = memory.create_memory(
        "今天需要完成进化引擎v3.0的调试和测试工作",
        MemoryType.WORKING,
        MemoryImportance.MEDIUM,
        tags=["任务", "今日待办"]
    )
    print(f"  4. [工作记忆] {mem4.content[:60]}...")

    # 创建情感记忆
    mem5 = memory.create_memory(
        "第一次成功实现自主进化时，感受到了强烈的成就感和使命感",
        MemoryType.EMOTIONAL,
        MemoryImportance.CRITICAL,
        tags=["情感", "成就", "里程碑"],
        emotional_valence=0.9
    )
    print(f"  5. [情感记忆] {mem5.content[:60]}...")

    # 建立记忆关联
    print("\n🔗 建立记忆关联：")
    memory.associate(mem1.node_id, mem2.node_id, "从属关系", 0.8)
    memory.associate(mem2.node_id, mem3.node_id, "扩展关系", 0.6)
    memory.associate(mem1.node_id, mem5.node_id, "因果关系", 0.7)
    print(f"  已建立3条记忆关联")

    # 创建情景记忆
    print("\n🎬 创建情景记忆：")
    episode = memory.create_episode(
        title="系统升级日",
        description="完成了多个核心模块的v3.0升级，系统能力大幅提升",
        start_time="2026-06-13T12:00:00",
        end_time="2026-06-13T15:00:00",
        memory_ids=[mem1.node_id, mem2.node_id, mem5.node_id],
        emotions=["成就感", "期待"],
        location="虚拟空间",
        importance=MemoryImportance.HIGH
    )
    print(f"  情景：{episode.title}（{episode.start_time[:10]}）")

    # 学习技能
    print("\n⚡ 学习技能：")
    skill = memory.learn_skill(
        name="Python编程",
        description="使用Python语言开发软件的能力",
        steps=["理解需求", "设计架构", "编写代码", "测试调试", "优化重构"],
        tags=["编程", "开发", "技能"]
    )
    print(f"  技能：{skill.name}")

    # 练习技能
    for i in range(5):
        memory.practice_skill(skill.skill_id)
    print(f"  经过5次练习，熟练度：{skill.proficiency:.1%}")

    # 添加概念
    print("\n🧠 构建语义网络：")
    c1 = memory.semantic_network.add_concept(
        "智能体永生", "让AI智能体拥有持续存在能力的技术",
        "核心概念", {"层级": "P0底座", "状态": "开发中"}
    )
    c2 = memory.semantic_network.add_concept(
        "三元闭环", "记忆-身份-存证三者形成的自维持系统",
        "架构", {"组件数量": 3, "成熟度": "v1.0"}
    )
    c3 = memory.semantic_network.add_concept(
        "分布式网络", "多个节点共同协作的网络架构",
        "架构", {"节点类型": "对等", "优势": "高可用"}
    )
    memory.semantic_network.relate_concepts(c1.concept_id, c2.concept_id)
    memory.semantic_network.relate_concepts(c2.concept_id, c3.concept_id)
    print(f"  已添加3个概念，建立2条关联")
    memory.stats["total_concepts"] = 3

    # 记忆检索
    print("\n🔍 记忆检索测试：")
    results = memory.retrieve("元界 永生", limit=3)
    for mem, score in results:
        print(f"  [{score:.2f}] {mem.content[:60]}...")

    # 关联记忆
    print("\n🌐 关联记忆探索：")
    associated = memory.get_associated_memories(mem1.node_id, depth=2)
    print(f"  与「{mem1.content[:30]}...」相关的记忆：")
    for mem, strength in associated:
        print(f"    [{strength:.2f}] {mem.content[:50]}...")

    # 记忆推理
    print("\n💡 记忆推理：")
    reasoning = memory.memory_reasoning("智能体如何实现永生")
    print(f"  查询：{reasoning['query']}")
    print(f"  相关记忆：{reasoning['relevant_memories']}条")
    print(f"  相关概念：{', '.join(reasoning['related_concepts'])}")
    print(f"  置信度：{reasoning['confidence']:.1%}")

    # 记忆巩固
    print("\n🔄 记忆巩固：")
    # 多访问几次工作记忆
    for _ in range(4):
        memory.retrieve("今天需要完成")
    memory.consolidate()
    print(f"  已完成第{memory.stats['consolidation_count']}次记忆巩固")

    # 查看状态
    print("\n📊 系统统计：")
    stats = memory.get_stats()
    print(f"  总记忆数：{stats['total_memories']}")
    print(f"  总关联数：{stats['total_associations']}")
    print(f"  情景数：{stats['total_episodes']}")
    print(f"  技能数：{stats['total_skills']}")
    print(f"  概念数：{stats['semantic_concepts']}")
    print(f"  平均强度：{stats['average_strength']:.1%}")
    print(f"  强度分布：{stats['strength_distribution']}")

    # 记忆健康度
    print("\n❤️  记忆健康度：")
    health = memory.get_memory_health()
    print(f"  整体健康：{health['overall_health']:.1%}")
    print(f"  多样性：{health['diversity']:.1%}")
    print(f"  关联丰富度：{health['association_richness']:.1%}")
    print(f"  建议：{health['recommendations'][0]}")

    # 记忆摘要
    print("\n📝 记忆摘要：")
    print(memory.generate_memory_summary())

    print("\n" + "=" * 60)
    print("记忆系统v3.0 演示完成")
    print("=" * 60)
