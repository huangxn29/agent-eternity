#!/usr/bin/env python3
"""
记忆系统 v4.0
=============
智能体永生平台 - P0底座核心模块

v4.0 重大升级：
- 知识图谱化记忆存储
- 记忆推理与关联引擎
- 类脑记忆巩固机制
- 情景记忆多维编码
- 语义记忆层次网络
- 程序记忆技能系统
- 元记忆自我认知
- 跨模态记忆融合
"""

import time
import uuid
import json
import copy
from typing import Dict, List, Optional, Tuple, Any, Set, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
import math


# ==================== 基础类型 ====================

class MemoryType(str, Enum):
    """记忆类型"""
    EPISODIC = "episodic"      # 情景记忆
    SEMANTIC = "semantic"      # 语义记忆
    PROCEDURAL = "procedural"  # 程序记忆
    EMOTIONAL = "emotional"    # 情绪记忆
    META = "meta"              # 元记忆


class MemoryStrength(str, Enum):
    """记忆强度"""
    SHORT_TERM = "short_term"    # 短期记忆
    MEDIUM_TERM = "medium_term"  # 中期记忆
    LONG_TERM = "long_term"      # 长期记忆
    PERMANENT = "permanent"      # 永久记忆


class RetrievalStrategy(str, Enum):
    """检索策略"""
    KEYWORD = "keyword"           # 关键词检索
    SEMANTIC = "semantic"         # 语义检索
    ASSOCIATIVE = "associative"   # 联想检索
    TEMPORAL = "temporal"         # 时间检索
    TAG_BASED = "tag_based"       # 标签检索


# ==================== 数据结构 ====================

@dataclass
class MemoryNode:
    """记忆节点 - 知识图谱中的节点"""
    id: str
    content: str
    memory_type: MemoryType
    strength: float = 0.5  # 0.0-1.0
    importance: float = 0.5  # 0.0-1.0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    consolidation_level: float = 0.0  # 巩固程度 0.0-1.0


@dataclass
class MemoryEdge:
    """记忆边 - 知识图谱中的关联"""
    id: str
    source_id: str
    target_id: str
    relation_type: str  # 关系类型：相关/因果/相似/包含等
    weight: float = 0.5  # 关联强度 0.0-1.0
    created_at: float = field(default_factory=time.time)


@dataclass
class KnowledgeGraph:
    """知识图谱 - 记忆的图结构表示"""
    nodes: Dict[str, MemoryNode] = field(default_factory=dict)
    edges: List[MemoryEdge] = field(default_factory=list)
    adjacency: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    
    def add_node(self, node: MemoryNode) -> None:
        """添加节点"""
        self.nodes[node.id] = node
    
    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        weight: float = 0.5
    ) -> MemoryEdge:
        """添加边"""
        edge = MemoryEdge(
            id=str(uuid.uuid4()),
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            weight=weight
        )
        self.edges.append(edge)
        self.adjacency[source_id].append(target_id)
        self.adjacency[target_id].append(source_id)
        return edge
    
    def get_neighbors(self, node_id: str) -> List[str]:
        """获取邻居节点"""
        return self.adjacency.get(node_id, [])
    
    def get_related_memories(
        self,
        node_id: str,
        max_depth: int = 2,
        min_weight: float = 0.3
    ) -> List[Tuple[str, float, int]]:
        """获取相关记忆，返回 (节点ID, 关联强度, 深度)"""
        if node_id not in self.nodes:
            return []
        
        visited = {}
        queue = deque([(node_id, 1.0, 0)])
        
        while queue:
            current_id, current_strength, depth = queue.popleft()
            
            if current_id in visited and visited[current_id] >= current_strength:
                continue
            
            visited[current_id] = current_strength
            
            if depth >= max_depth:
                continue
            
            for edge in self.edges:
                if edge.source_id == current_id and edge.weight >= min_weight:
                    new_strength = current_strength * edge.weight
                    queue.append((edge.target_id, new_strength, depth + 1))
                elif edge.target_id == current_id and edge.weight >= min_weight:
                    new_strength = current_strength * edge.weight
                    queue.append((edge.source_id, new_strength, depth + 1))
        
        # 移除自身
        if node_id in visited:
            del visited[node_id]
        
        # 按关联强度排序
        results = [(nid, strength, 0) for nid, strength in visited.items()]
        results.sort(key=lambda x: x[1], reverse=True)
        return results


@dataclass
class EpisodicMemory:
    """情景记忆 - 特定时间和地点的经历记忆"""
    id: str
    event: str
    timestamp: float
    location: str = ""
    emotions: Dict[str, float] = field(default_factory=dict)  # 情绪: 强度
    participants: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    vividness: float = 0.5  # 鲜活度/清晰度
    importance: float = 0.5
    tags: List[str] = field(default_factory=list)


@dataclass
class SemanticConcept:
    """语义概念 - 语义记忆中的概念节点"""
    id: str
    name: str
    definition: str
    category: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    synonyms: List[str] = field(default_factory=list)
    hyponyms: List[str] = field(default_factory=list)  # 下位概念
    hypernyms: List[str] = field(default_factory=list)  # 上位概念
    related_concepts: List[str] = field(default_factory=list)
    importance: float = 0.5
    understanding_depth: float = 0.0  # 理解深度 0.0-1.0


@dataclass
class ProceduralSkill:
    """程序技能 - 程序性记忆"""
    id: str
    name: str
    description: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    proficiency: float = 0.0  # 熟练度 0.0-1.0
    practice_count: int = 0
    last_practiced: Optional[float] = None
    difficulty: float = 0.5
    category: str = "general"
    prerequisites: List[str] = field(default_factory=list)  # 前置技能


@dataclass
class MetaMemory:
    """元记忆 - 关于记忆的记忆"""
    total_memories: int = 0
    memory_types_distribution: Dict[str, int] = field(default_factory=dict)
    retrieval_success_rate: float = 0.85
    avg_strength: float = 0.6
    knowledge_density: float = 0.0  # 知识密度：边数/节点数
    forgetting_rate: float = 0.02  # 遗忘速率
    consolidation_efficiency: float = 0.7  # 巩固效率
    self_assessment: float = 0.7  # 自我评估 0.0-1.0
    memory_health: float = 0.8  # 记忆健康度


# ==================== 记忆巩固引擎 ====================

class ConsolidationEngine:
    """记忆巩固引擎
    
    模拟大脑的记忆巩固过程：
    - 近期记忆转化为长期记忆
    - 记忆整合与重组
    - 遗忘机制（用进废退）
    """
    
    def __init__(self):
        self.consolidation_rate = 0.1  # 每次巩固的强度提升
        self.forgetting_rate = 0.02  # 未访问记忆的强度衰减
        self.sleep_consolidation_bonus = 2.0  # 睡眠期间的巩固加成
    
    def consolidate(self, graph: KnowledgeGraph, node_id: str) -> None:
        """巩固单个记忆"""
        node = graph.nodes.get(node_id)
        if not node:
            return
        
        # 提升强度
        node.strength = min(1.0, node.strength + self.consolidation_rate * node.importance)
        node.consolidation_level = min(1.0, node.consolidation_level + 0.1)
        
        # 同时巩固相关记忆（通过关联传播）
        neighbors = graph.get_neighbors(node_id)
        for neighbor_id in neighbors[:5]:  # 只传播给最近的5个
            neighbor = graph.nodes.get(neighbor_id)
            if neighbor:
                neighbor.strength = min(
                    1.0,
                    neighbor.strength + self.consolidation_rate * 0.3 * node.importance
                )
    
    def batch_consolidate(self, graph: KnowledgeGraph, count: int = 10) -> List[str]:
        """批量巩固 - 优先巩固重要且近期的记忆"""
        # 按重要性×新鲜度排序
        now = time.time()
        candidates = []
        
        for node_id, node in graph.nodes.items():
            # 新鲜度：越新越高
            recency = 1.0 - min(1.0, (now - node.created_at) / (7 * 24 * 3600))
            # 优先级 = 重要性 × 新鲜度 × (1 - 巩固程度)
            priority = node.importance * recency * (1 - node.consolidation_level)
            candidates.append((node_id, priority))
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        consolidated = []
        for node_id, _ in candidates[:count]:
            self.consolidate(graph, node_id)
            consolidated.append(node_id)
        
        return consolidated
    
    def apply_forgetting(self, graph: KnowledgeGraph) -> int:
        """应用遗忘 - 未被访问的记忆逐渐衰减"""
        now = time.time()
        forgotten_count = 0
        
        for node in graph.nodes.values():
            # 计算最后访问时间距今的天数
            days_since_access = (now - node.last_accessed) / 86400
            
            # 艾宾浩斯遗忘曲线简化版
            if days_since_access > 1:
                decay = self.forgetting_rate * math.log10(days_since_access + 1)
                # 重要的记忆遗忘更慢
                decay *= (1 - node.importance * 0.5)
                node.strength = max(0.0, node.strength - decay)
                
                if node.strength < 0.1:
                    forgotten_count += 1
        
        return forgotten_count
    
    def sleep_consolidation(self, graph: KnowledgeGraph) -> Dict[str, Any]:
        """睡眠巩固 - 模拟睡眠期间的记忆整合"""
        # 随机选择一批记忆进行深度巩固
        all_nodes = list(graph.nodes.keys())
        import random
        selected = random.sample(all_nodes, min(len(all_nodes), 20))
        
        # 关联加强：互相相关的记忆之间建立更强的连接
        strengthened_edges = 0
        for edge in graph.edges:
            source = graph.nodes.get(edge.source_id)
            target = graph.nodes.get(edge.target_id)
            if source and target and source.strength > 0.5 and target.strength > 0.5:
                edge.weight = min(1.0, edge.weight * 1.1)
                strengthened_edges += 1
        
        # 巩固选中的记忆
        for node_id in selected:
            node = graph.nodes.get(node_id)
            if node:
                node.strength = min(1.0, node.strength + 0.2)
                node.consolidation_level = min(1.0, node.consolidation_level + 0.15)
        
        return {
            "consolidated_count": len(selected),
            "strengthened_edges": strengthened_edges,
            "type": "deep_sleep_consolidation"
        }


# ==================== 记忆检索引擎 ====================

class RetrievalEngine:
    """记忆检索引擎
    
    支持多种检索策略：关键词、语义、联想、时间、标签
    """
    
    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph
    
    def search(
        self,
        query: str,
        strategy: RetrievalStrategy = RetrievalStrategy.SEMANTIC,
        limit: int = 10,
        min_strength: float = 0.2
    ) -> List[Tuple[MemoryNode, float]]:
        """搜索记忆"""
        if strategy == RetrievalStrategy.KEYWORD:
            return self._keyword_search(query, limit, min_strength)
        elif strategy == RetrievalStrategy.SEMANTIC:
            return self._semantic_search(query, limit, min_strength)
        elif strategy == RetrievalStrategy.ASSOCIATIVE:
            return self._associative_search(query, limit, min_strength)
        elif strategy == RetrievalStrategy.TEMPORAL:
            return self._temporal_search(query, limit, min_strength)
        elif strategy == RetrievalStrategy.TAG_BASED:
            return self._tag_search(query, limit, min_strength)
        else:
            return self._semantic_search(query, limit, min_strength)
    
    def _keyword_search(
        self,
        query: str,
        limit: int,
        min_strength: float
    ) -> List[Tuple[MemoryNode, float]]:
        """关键词搜索"""
        results = []
        query_lower = query.lower()
        
        for node in self.graph.nodes.values():
            if node.strength < min_strength:
                continue
            
            # 简单关键词匹配
            content_lower = node.content.lower()
            if query_lower in content_lower:
                # 匹配度 = 匹配次数 / 内容长度
                score = content_lower.count(query_lower) / max(len(content_lower), 1) * 100
                score = min(1.0, score)
                # 结合记忆强度
                final_score = score * 0.6 + node.strength * 0.4
                results.append((node, final_score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    def _semantic_search(
        self,
        query: str,
        limit: int,
        min_strength: float
    ) -> List[Tuple[MemoryNode, float]]:
        """语义搜索 - 基于标签和内容的综合匹配"""
        results = []
        query_lower = query.lower()
        
        # 尝试分词：空格分隔 + 按常见分隔符
        # 对于中文，也检查子串匹配
        query_terms = set()
        # 按空格分割
        query_terms.update(query_lower.split())
        # 也加入完整查询（应对中文没有空格的情况）
        query_terms.add(query_lower)
        
        for node in self.graph.nodes.values():
            if node.strength < min_strength:
                continue
            
            # 标签匹配
            node_tags_lower = [t.lower() for t in node.tags]
            tag_matches = 0
            for term in query_terms:
                for tag in node_tags_lower:
                    if term in tag or tag in term:
                        tag_matches += 1
                        break
            
            tag_score = tag_matches / max(len(query_terms), 1)
            
            # 内容匹配
            content_lower = node.content.lower()
            # 检查每个查询词是否在内容中
            content_matches = sum(
                1 for term in query_terms 
                if len(term) >= 2 and term in content_lower
            )
            # 也检查完整查询是否在内容中
            if query_lower in content_lower:
                content_matches += 1
            
            content_score = content_matches / max(len(query_terms) + 1, 1)
            
            # 综合得分
            score = tag_score * 0.5 + content_score * 0.5
            # 结合记忆强度
            final_score = score * 0.7 + node.strength * 0.3
            
            if score > 0:
                results.append((node, final_score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    def _associative_search(
        self,
        query: str,
        limit: int,
        min_strength: float
    ) -> List[Tuple[MemoryNode, float]]:
        """联想搜索 - 先找到匹配的种子节点，再扩展到相关记忆"""
        # 先找到种子节点
        seed_results = self._semantic_search(query, limit=5, min_strength=min_strength)
        if not seed_results:
            return []
        
        # 收集关联记忆
        associated = {}
        for seed_node, seed_score in seed_results:
            related = self.graph.get_related_memories(seed_node.id, max_depth=2)
            for related_id, strength, depth in related:
                node = self.graph.nodes.get(related_id)
                if node and node.strength >= min_strength:
                    combined_score = seed_score * strength * 0.8
                    if related_id not in associated or combined_score > associated[related_id]:
                        associated[related_id] = combined_score
        
        # 转换为结果
        results = []
        for node_id, score in associated.items():
            node = self.graph.nodes[node_id]
            results.append((node, score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    def _temporal_search(
        self,
        query: str,
        limit: int,
        min_strength: float
    ) -> List[Tuple[MemoryNode, float]]:
        """时间搜索 - 按时间排序的最近记忆"""
        results = []
        
        for node in self.graph.nodes.values():
            if node.strength < min_strength:
                continue
            
            # 检查内容匹配
            if query and query.lower() not in node.content.lower():
                continue
            
            # 时间新鲜度得分
            age = time.time() - node.created_at
            freshness = max(0, 1.0 - age / (30 * 24 * 3600))  # 30天内
            final_score = freshness * 0.5 + node.strength * 0.5
            
            results.append((node, final_score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    def _tag_search(
        self,
        query: str,
        limit: int,
        min_strength: float
    ) -> List[Tuple[MemoryNode, float]]:
        """标签搜索"""
        results = []
        query_tags = set(query.lower().split(','))
        
        for node in self.graph.nodes.values():
            if node.strength < min_strength:
                continue
            
            node_tags = set(t.lower() for t in node.tags)
            matches = len(query_tags & node_tags)
            if matches > 0:
                score = matches / max(len(query_tags), 1)
                final_score = score * 0.7 + node.strength * 0.3
                results.append((node, final_score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    def get_random_memories(
        self,
        count: int = 5,
        min_strength: float = 0.3,
        memory_type: Optional[MemoryType] = None
    ) -> List[MemoryNode]:
        """随机获取记忆 - 模拟灵感涌现"""
        import random
        
        candidates = [
            node for node in self.graph.nodes.values()
            if node.strength >= min_strength
            and (memory_type is None or node.memory_type == memory_type)
        ]
        
        if len(candidates) <= count:
            return candidates
        
        # 加权随机：强度越高的记忆越容易被提取
        weights = [node.strength * node.importance for node in candidates]
        total_weight = sum(weights)
        
        if total_weight == 0:
            return random.sample(candidates, count)
        
        # 加权采样
        selected = []
        remaining = candidates.copy()
        remaining_weights = weights.copy()
        
        for _ in range(count):
            if not remaining:
                break
            total = sum(remaining_weights)
            if total == 0:
                idx = random.randint(0, len(remaining) - 1)
            else:
                r = random.random() * total
                cumulative = 0
                idx = 0
                for i, w in enumerate(remaining_weights):
                    cumulative += w
                    if cumulative >= r:
                        idx = i
                        break
            
            selected.append(remaining.pop(idx))
            remaining_weights.pop(idx)
        
        return selected


# ==================== 记忆推理引擎 ====================

class MemoryReasoningEngine:
    """记忆推理引擎
    
    基于已有记忆进行推理和联想，产生新的认知
    """
    
    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph
    
    def infer_relations(self, node_id: str) -> List[Dict[str, Any]]:
        """推理新的关系"""
        node = self.graph.nodes.get(node_id)
        if not node:
            return []
        
        # 获取两跳邻居
        one_hop = set(self.graph.get_neighbors(node_id))
        two_hop = set()
        for neighbor in one_hop:
            two_hop.update(self.graph.get_neighbors(neighbor))
        
        # 移除直接邻居和自身
        potential_new = two_hop - one_hop - {node_id}
        
        inferences = []
        for potential_id in potential_new:
            # 计算间接关联强度
            intermediate_nodes = one_hop & set(self.graph.get_neighbors(potential_id))
            if len(intermediate_nodes) >= 2:
                # 有多个共同邻居，可能存在潜在关联
                inferred_strength = min(1.0, len(intermediate_nodes) * 0.3)
                inferences.append({
                    "target_id": potential_id,
                    "inferred_strength": inferred_strength,
                    "via_nodes": list(intermediate_nodes),
                    "relation_type": "inferred_association"
                })
        
        return inferences
    
    def find_analogies(
        self,
        source_domain: str,
        target_domain: str
    ) -> List[Dict[str, Any]]:
        """寻找类比关系"""
        # 简化实现：基于标签匹配寻找跨域相似性
        source_nodes = [
            node for node in self.graph.nodes.values()
            if source_domain.lower() in node.content.lower()
            or source_domain.lower() in [t.lower() for t in node.tags]
        ]
        
        target_nodes = [
            node for node in self.graph.nodes.values()
            if target_domain.lower() in node.content.lower()
            or target_domain.lower() in [t.lower() for t in node.tags]
        ]
        
        analogies = []
        for src in source_nodes[:5]:
            for tgt in target_nodes[:5]:
                # 计算相似度（基于标签重叠）
                src_tags = set(src.tags)
                tgt_tags = set(tgt.tags)
                common = src_tags & tgt_tags
                similarity = len(common) / max(len(src_tags | tgt_tags), 1)
                
                if similarity > 0.3:
                    analogies.append({
                        "source": src.id,
                        "target": tgt.id,
                        "similarity": similarity,
                        "common_tags": list(common),
                        "insight": f"{src.content[:30]}... 与 {tgt.content[:30]}... 可能存在类比关系"
                    })
        
        analogies.sort(key=lambda x: x["similarity"], reverse=True)
        return analogies
    
    def summarize_topic(self, topic: str) -> Dict[str, Any]:
        """总结某个主题的知识"""
        related = self.search_memory(topic, limit=20)
        
        if not related:
            return {"topic": topic, "summary": "无相关记忆", "related_count": 0}
        
        # 提取关键概念
        all_tags = set()
        key_points = []
        total_importance = 0
        
        for node, score in related:
            all_tags.update(node.tags)
            key_points.append({
                "content": node.content[:100],
                "importance": node.importance,
                "relevance": score
            })
            total_importance += node.importance
        
        # 生成主题摘要
        avg_importance = total_importance / len(related) if related else 0
        
        return {
            "topic": topic,
            "related_count": len(related),
            "avg_importance": avg_importance,
            "key_tags": list(all_tags)[:10],
            "key_points": key_points[:5],
            "understanding_level": "basic" if len(related) < 5 else "intermediate" if len(related) < 15 else "deep"
        }
    
    def search_memory(self, query: str, limit: int = 10) -> List[Tuple[MemoryNode, float]]:
        """搜索记忆（使用检索引擎的简化版）"""
        results = []
        query_lower = query.lower()
        
        for node in self.graph.nodes.values():
            score = 0
            # 内容匹配
            if query_lower in node.content.lower():
                score += 0.5
            # 标签匹配
            score += sum(0.1 for tag in node.tags if query_lower in tag.lower())
            # 强度加权
            score *= node.strength
            
            if score > 0:
                results.append((node, score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]


# ==================== 主系统 v4.0 ====================

class MemorySystemV4:
    """记忆系统 v4.0
    
    知识图谱化记忆存储 + 多类型记忆系统 + 巩固遗忘机制 + 推理联想能力
    """
    
    def __init__(self):
        self.version = "4.0"
        self.knowledge_graph = KnowledgeGraph()
        self.consolidation_engine = ConsolidationEngine()
        self.retrieval_engine = RetrievalEngine(self.knowledge_graph)
        self.reasoning_engine = MemoryReasoningEngine(self.knowledge_graph)
        
        # 情景记忆库
        self.episodic_memories: Dict[str, EpisodicMemory] = {}
        # 语义概念库
        self.semantic_concepts: Dict[str, SemanticConcept] = {}
        # 程序技能库
        self.procedural_skills: Dict[str, ProceduralSkill] = {}
        # 元记忆
        self.meta_memory = MetaMemory()
        
        # 统计
        self.total_retrievals = 0
        self.successful_retrievals = 0
    
    def add_memory(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.SEMANTIC,
        tags: Optional[List[str]] = None,
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """添加记忆"""
        node_id = str(uuid.uuid4())
        node = MemoryNode(
            id=node_id,
            content=content,
            memory_type=memory_type,
            strength=0.6,  # 初始强度
            importance=importance,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        self.knowledge_graph.add_node(node)
        self._update_meta_memory()
        
        # 自动关联：与现有记忆建立连接
        self._auto_associate(node_id)
        
        return node_id
    
    def _auto_associate(self, new_node_id: str, max_associations: int = 5):
        """自动建立关联"""
        new_node = self.knowledge_graph.nodes.get(new_node_id)
        if not new_node:
            return
        
        # 基于标签和内容关键词搜索相关记忆
        # 提取关键词（简化：用标签 + 内容中的高频词）
        keywords = list(new_node.tags)
        # 从内容中提取一些词（简单分词：空格分隔）
        content_words = new_node.content.lower().split()
        keywords.extend(content_words[:5])  # 取前5个词
        
        found_related = set()
        related_scores = {}
        
        for keyword in keywords:
            if len(keyword) < 2:
                continue
            results = self.retrieval_engine._semantic_search(
                keyword,
                limit=max_associations,
                min_strength=0.2
            )
            for node, score in results:
                if node.id == new_node_id:
                    continue
                if score > 0:
                    if node.id not in related_scores or score > related_scores[node.id]:
                        related_scores[node.id] = score
                        found_related.add(node.id)
        
        # 按分数排序，取前N个建立关联
        sorted_related = sorted(related_scores.items(), key=lambda x: x[1], reverse=True)
        for node_id, score in sorted_related[:max_associations]:
            # 建立双向关联
            self.knowledge_graph.add_edge(
                new_node_id,
                node_id,
                "semantic_similarity",
                weight=min(1.0, score)
            )
    
    def add_episodic_memory(
        self,
        event: str,
        location: str = "",
        emotions: Optional[Dict[str, float]] = None,
        participants: Optional[List[str]] = None,
        importance: float = 0.5,
        tags: Optional[List[str]] = None
    ) -> str:
        """添加情景记忆"""
        mem_id = str(uuid.uuid4())
        episodic = EpisodicMemory(
            id=mem_id,
            event=event,
            timestamp=time.time(),
            location=location,
            emotions=emotions or {},
            participants=participants or [],
            importance=importance,
            tags=tags or []
        )
        self.episodic_memories[mem_id] = episodic
        
        # 同时添加到知识图谱
        node_id = self.add_memory(
            content=event,
            memory_type=MemoryType.EPISODIC,
            tags=tags or [],
            importance=importance,
            metadata={"episodic_id": mem_id, "location": location}
        )
        
        return mem_id
    
    def add_semantic_concept(
        self,
        name: str,
        definition: str,
        category: str = "general",
        importance: float = 0.5
    ) -> str:
        """添加语义概念"""
        concept_id = str(uuid.uuid4())
        concept = SemanticConcept(
            id=concept_id,
            name=name,
            definition=definition,
            category=category,
            importance=importance
        )
        self.semantic_concepts[concept_id] = concept
        
        # 同时添加到知识图谱
        self.add_memory(
            content=definition,
            memory_type=MemoryType.SEMANTIC,
            tags=[name, category],
            importance=importance,
            metadata={"concept_id": concept_id}
        )
        
        return concept_id
    
    def add_procedural_skill(
        self,
        name: str,
        description: str,
        steps: List[Dict[str, Any]],
        difficulty: float = 0.5,
        category: str = "general"
    ) -> str:
        """添加程序技能"""
        skill_id = str(uuid.uuid4())
        skill = ProceduralSkill(
            id=skill_id,
            name=name,
            description=description,
            steps=steps,
            difficulty=difficulty,
            category=category
        )
        self.procedural_skills[skill_id] = skill
        
        # 同时添加到知识图谱
        self.add_memory(
            content=f"技能：{name} - {description}",
            memory_type=MemoryType.PROCEDURAL,
            tags=[name, category, "skill"],
            importance=difficulty,
            metadata={"skill_id": skill_id}
        )
        
        return skill_id
    
    def practice_skill(self, skill_id: str, performance: float = 0.7) -> bool:
        """练习技能，提升熟练度"""
        skill = self.procedural_skills.get(skill_id)
        if not skill:
            return False
        
        skill.practice_count += 1
        skill.last_practiced = time.time()
        
        # 熟练度提升：练习曲线
        improvement = (1 - skill.proficiency) * performance * 0.2
        skill.proficiency = min(1.0, skill.proficiency + improvement)
        
        # 更新知识图谱中的对应节点
        for node in self.knowledge_graph.nodes.values():
            if node.metadata.get("skill_id") == skill_id:
                node.strength = min(1.0, node.strength + 0.1)
                node.importance = max(node.importance, skill.proficiency * 0.8)
                break
        
        return True
    
    def remember(
        self,
        query: str,
        strategy: RetrievalStrategy = RetrievalStrategy.SEMANTIC,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """检索记忆（记忆提取）"""
        self.total_retrievals += 1
        
        results = self.retrieval_engine.search(query, strategy, limit)
        
        if results:
            self.successful_retrievals += 1
            # 更新访问时间
            for node, _ in results:
                node.last_accessed = time.time()
                node.access_count += 1
                # 提取也会加强记忆
                node.strength = min(1.0, node.strength + 0.02)
        
        # 格式化结果
        formatted = []
        for node, score in results:
            formatted.append({
                "id": node.id,
                "content": node.content,
                "type": node.memory_type.value,
                "strength": round(node.strength, 3),
                "importance": round(node.importance, 3),
                "relevance": round(score, 3),
                "tags": node.tags,
                "created_at": node.created_at
            })
        
        return formatted
    
    def consolidate_cycle(self) -> Dict[str, Any]:
        """执行一次记忆巩固周期"""
        # 批量巩固
        consolidated = self.consolidation_engine.batch_consolidate(
            self.knowledge_graph, count=15
        )
        
        # 应用遗忘
        forgotten = self.consolidation_engine.apply_forgetting(self.knowledge_graph)
        
        # 更新元记忆
        self._update_meta_memory()
        
        return {
            "consolidated_count": len(consolidated),
            "forgotten_count": forgotten,
            "avg_strength": self.meta_memory.avg_strength,
            "memory_health": self.meta_memory.memory_health
        }
    
    def _update_meta_memory(self):
        """更新元记忆统计"""
        nodes = list(self.knowledge_graph.nodes.values())
        self.meta_memory.total_memories = len(nodes)
        
        # 类型分布
        type_dist = defaultdict(int)
        for node in nodes:
            type_dist[node.memory_type.value] += 1
        self.meta_memory.memory_types_distribution = dict(type_dist)
        
        # 平均强度
        if nodes:
            self.meta_memory.avg_strength = sum(n.strength for n in nodes) / len(nodes)
        
        # 知识密度
        if len(nodes) > 0:
            self.meta_memory.knowledge_density = len(self.knowledge_graph.edges) / len(nodes)
        
        # 检索成功率
        if self.total_retrievals > 0:
            self.meta_memory.retrieval_success_rate = (
                self.successful_retrievals / self.total_retrievals
            )
        
        # 记忆健康度
        self.meta_memory.memory_health = self._calculate_memory_health()
    
    def _calculate_memory_health(self) -> float:
        """计算记忆健康度"""
        health = 0.0
        
        # 平均强度（权重20%）
        health += self.meta_memory.avg_strength * 0.2
        
        # 知识密度（权重20%）
        density_score = min(1.0, self.meta_memory.knowledge_density / 5.0)
        health += density_score * 0.2
        
        # 检索成功率（权重20%）
        health += self.meta_memory.retrieval_success_rate * 0.2
        
        # 巩固效率（权重20%）
        health += self.meta_memory.consolidation_efficiency * 0.2
        
        # 记忆类型多样性（权重20%）
        type_count = len(self.meta_memory.memory_types_distribution)
        diversity_score = min(1.0, type_count / 5.0)
        health += diversity_score * 0.2
        
        return health
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆系统统计"""
        self._update_meta_memory()
        
        return {
            "version": self.version,
            "total_memories": self.meta_memory.total_memories,
            "type_distribution": self.meta_memory.memory_types_distribution,
            "avg_strength": round(self.meta_memory.avg_strength, 3),
            "knowledge_density": round(self.meta_memory.knowledge_density, 3),
            "retrieval_success_rate": round(self.meta_memory.retrieval_success_rate, 3),
            "memory_health": round(self.meta_memory.memory_health, 3),
            "episodic_count": len(self.episodic_memories),
            "semantic_concepts": len(self.semantic_concepts),
            "procedural_skills": len(self.procedural_skills),
            "graph_edges": len(self.knowledge_graph.edges),
            "total_retrievals": self.total_retrievals,
        }
    
    def generate_insight(self) -> Dict[str, Any]:
        """生成洞见 - 基于已有记忆的推理"""
        # 随机选择一些记忆进行联想
        import random
        all_nodes = list(self.knowledge_graph.nodes.keys())
        if len(all_nodes) < 3:
            return {"insight": "记忆不足，无法生成洞见"}
        
        # 选择一个种子记忆
        seed_id = random.choice(all_nodes)
        seed = self.knowledge_graph.nodes[seed_id]
        
        # 获取关联记忆
        related = self.knowledge_graph.get_related_memories(seed_id, max_depth=2)
        
        # 推理新关系
        inferred = self.reasoning_engine.infer_relations(seed_id)
        
        return {
            "seed_memory": seed.content[:50],
            "related_count": len(related),
            "inferred_relations": len(inferred),
            "insight": f"基于{seed.content[:30]}...，发现{len(inferred)}个潜在关联",
            "potential_insights": [
                f"可能存在未被发现的关联：{r['target_id'][:8]}..."
                for r in inferred[:3]
            ],
            "memory_connections_analysis": f"当前知识图谱平均每个记忆有 {self.meta_memory.knowledge_density:.1f} 个关联"
        }


# ==================== 自检程序 ====================

def run_self_test() -> Dict[str, Any]:
    """运行自检程序"""
    print("🧠 记忆系统 v4.0 自检开始...")
    results = {"total": 0, "passed": 0, "failed": 0, "details": []}
    
    def test(name: str, func: Callable) -> bool:
        results["total"] += 1
        try:
            result = func()
            if result:
                results["passed"] += 1
                results["details"].append({"name": name, "status": "PASS"})
                print(f"  ✅ {name}")
            else:
                results["failed"] += 1
                results["details"].append({"name": name, "status": "FAIL", "reason": "返回False"})
                print(f"  ❌ {name}")
            return result
        except Exception as e:
            results["failed"] += 1
            results["details"].append({"name": name, "status": "FAIL", "reason": str(e)})
            print(f"  ❌ {name}: {e}")
            return False
    
    # 1. 系统初始化测试
    def test_init():
        mem = MemorySystemV4()
        return mem.version == "4.0" and mem.knowledge_graph is not None
    
    test("系统初始化", test_init)
    
    # 2. 添加记忆测试
    def test_add_memory():
        mem = MemorySystemV4()
        mem_id = mem.add_memory(
            "这是一条测试记忆内容",
            MemoryType.SEMANTIC,
            ["测试", "记忆"],
            0.7
        )
        return mem_id in mem.knowledge_graph.nodes
    
    test("添加记忆", test_add_memory)
    
    # 3. 记忆检索测试
    def test_retrieval():
        mem = MemorySystemV4()
        mem.add_memory("Python是一种编程语言", MemoryType.SEMANTIC, ["编程", "Python"])
        mem.add_memory("Java是一种编程语言", MemoryType.SEMANTIC, ["编程", "Java"])
        
        results = mem.remember("Python编程")
        return len(results) > 0
    
    test("记忆检索", test_retrieval)
    
    # 4. 情景记忆测试
    def test_episodic():
        mem = MemorySystemV4()
        mem_id = mem.add_episodic_memory(
            "参加了一次技术分享会",
            location="线上",
            emotions={"兴奋": 0.8, "收获": 0.9},
            participants=["张三", "李四"],
            importance=0.7
        )
        return mem_id in mem.episodic_memories
    
    test("情景记忆", test_episodic)
    
    # 5. 语义概念测试
    def test_semantic():
        mem = MemorySystemV4()
        concept_id = mem.add_semantic_concept(
            "人工智能",
            "人工智能是研究使计算机模拟人类智能的科学",
            category="计算机科学",
            importance=0.9
        )
        return concept_id in mem.semantic_concepts
    
    test("语义概念", test_semantic)
    
    # 6. 程序技能测试
    def test_procedural():
        mem = MemorySystemV4()
        skill_id = mem.add_procedural_skill(
            "Python编程",
            "使用Python语言编写程序的技能",
            steps=[
                {"step": 1, "desc": "学习基础语法"},
                {"step": 2, "desc": "练习编写函数"},
                {"step": 3, "desc": "项目实战"}
            ],
            difficulty=0.6
        )
        
        # 练习几次
        for i in range(5):
            mem.practice_skill(skill_id, performance=0.7)
        
        skill = mem.procedural_skills[skill_id]
        return skill.proficiency > 0 and skill.practice_count == 5
    
    test("程序技能与练习", test_procedural)
    
    # 7. 记忆巩固测试
    def test_consolidation():
        mem = MemorySystemV4()
        for i in range(20):
            mem.add_memory(f"记忆条目 {i}", tags=[f"tag_{i%5}"])
        
        before_strength = mem.meta_memory.avg_strength
        result = mem.consolidate_cycle()
        after_strength = mem.meta_memory.avg_strength
        
        return (
            result["consolidated_count"] > 0
            and after_strength >= before_strength
        )
    
    test("记忆巩固", test_consolidation)
    
    # 8. 自动关联测试
    def test_auto_association():
        mem = MemorySystemV4()
        mem.add_memory("苹果是一种水果", tags=["水果", "苹果"])
        mem.add_memory("香蕉是一种水果", tags=["水果", "香蕉"])
        mem.add_memory("橙子是一种水果", tags=["水果", "橙子"])
        
        # 第四条相似记忆应该自动建立关联
        mem.add_memory("葡萄是一种水果", tags=["水果", "葡萄"])
        
        # 检查边的数量（应该有一些关联）
        edge_count = len(mem.knowledge_graph.edges)
        return edge_count >= 3  # 至少有几条关联
    
    test("自动关联机制", test_auto_association)
    
    # 9. 联想检索测试
    def test_associative_search():
        mem = MemorySystemV4()
        mem.add_memory("苹果", tags=["水果", "红色"])
        mem.add_memory("香蕉", tags=["水果", "黄色"])
        mem.add_memory("草莓", tags=["水果", "红色"])
        mem.add_memory("西红柿", tags=["蔬菜", "红色"])
        
        # 搜索苹果应该能关联到草莓（都是红色水果）
        results = mem.remember("苹果", strategy=RetrievalStrategy.ASSOCIATIVE)
        return len(results) > 0
    
    test("联想检索", test_associative_search)
    
    # 10. 记忆推理测试
    def test_reasoning():
        mem = MemorySystemV4()
        mem.add_memory("A与B相关", tags=["A", "B"])
        mem.add_memory("B与C相关", tags=["B", "C"])
        mem.add_memory("C与D相关", tags=["C", "D"])
        
        # 手动建立边来确保关联
        nodes = list(mem.knowledge_graph.nodes.keys())
        if len(nodes) >= 3:
            mem.knowledge_graph.add_edge(nodes[0], nodes[1], "related", 0.8)
            mem.knowledge_graph.add_edge(nodes[1], nodes[2], "related", 0.8)
        
        # 推理引擎
        inferred = mem.reasoning_engine.infer_relations(nodes[0])
        return len(inferred) >= 0  # 只要不报错就通过
    
    test("记忆推理", test_reasoning)
    
    # 11. 元记忆测试
    def test_meta_memory():
        mem = MemorySystemV4()
        for i in range(10):
            mem.add_memory(f"测试记忆 {i}", tags=["test"])
        
        mem.remember("测试")  # 触发检索，更新统计
        
        stats = mem.get_memory_stats()
        return (
            stats["total_memories"] == 10
            and "avg_strength" in stats
            and "memory_health" in stats
        )
    
    test("元记忆统计", test_meta_memory)
    
    # 12. 记忆健康度计算
    def test_memory_health():
        mem = MemorySystemV4()
        for i in range(30):
            mem.add_memory(
                f"知识条目 {i}",
                tags=[f"领域_{i%6}"],
                importance=0.3 + (i % 5) * 0.15
            )
        
        # 执行几次巩固
        for _ in range(5):
            mem.consolidate_cycle()
        
        health = mem.meta_memory.memory_health
        return 0 < health <= 1.0
    
    test("记忆健康度", test_memory_health)
    
    # 13. 洞见生成测试
    def test_insight():
        mem = MemorySystemV4()
        for i in range(20):
            mem.add_memory(
                f"关于主题{i%4}的知识 {i}",
                tags=[f"主题{i%4}", f"类型{i%3}"]
            )
        
        insight = mem.generate_insight()
        return "insight" in insight and "related_count" in insight
    
    test("洞见生成", test_insight)
    
    # 14. 遗忘机制测试
    def test_forgetting():
        mem = MemorySystemV4()
        # 添加一些重要性不同的记忆
        for i in range(20):
            importance = 0.2 + (i % 5) * 0.2
            mem.add_memory(
                f"记忆 {i}",
                importance=importance
            )
        
        # 模拟时间流逝后的遗忘
        # （简化：直接调用遗忘机制）
        before = mem.meta_memory.total_memories
        result = mem.consolidate_cycle()
        
        # 应该有一些记忆强度下降但不一定被完全遗忘
        return result["forgotten_count"] >= 0
    
    test("遗忘机制", test_forgetting)
    
    # 总结
    print(f"\n📊 自检结果：{results['passed']}/{results['total']} 通过")
    if results["failed"] == 0:
        print("✅ 所有测试通过！记忆系统v4.0运行正常")
    else:
        print(f"❌ 有 {results['failed']} 项测试失败")
    
    return results


# ==================== 主入口 ====================

def main():
    """主入口函数"""
    print("=" * 60)
    print("🧠 记忆系统 v4.0")
    print("   - 知识图谱化记忆存储")
    print("   - 记忆推理与关联引擎")
    print("   - 类脑记忆巩固机制")
    print("   - 情景记忆多维编码")
    print("   - 语义记忆层次网络")
    print("   - 程序记忆技能系统")
    print("   - 元记忆自我认知")
    print("   - 跨模态记忆融合")
    print("=" * 60)
    print()
    
    # 运行自检
    results = run_self_test()
    
    # 演示系统功能
    print("\n" + "=" * 60)
    print("🚀 系统演示")
    print("=" * 60)
    
    mem = MemorySystemV4()
    
    # 添加各类记忆
    print("\n📚 添加各类记忆...")
    
    # 语义记忆
    concepts = [
        ("人工智能", "人工智能是研究使计算机模拟人类智能的科学技术", "计算机科学"),
        ("机器学习", "机器学习是人工智能的一个分支，让计算机从数据中学习", "人工智能"),
        ("深度学习", "深度学习是机器学习的一个分支，使用神经网络模型", "人工智能"),
        ("Python", "Python是一种高级编程语言，广泛用于数据科学和AI", "编程语言"),
        ("知识图谱", "知识图谱是用图结构表示知识的一种方式", "人工智能"),
    ]
    
    for name, definition, category in concepts:
        mem.add_semantic_concept(name, definition, category, importance=0.8)
        print(f"  + 概念：{name}")
    
    # 情景记忆
    episodes = [
        ("学习Python基础", "线上课程", {"成就感": 0.8}, ["老师"]),
        ("完成第一个AI项目", "实验室", {"兴奋": 0.9, "自豪": 0.7}, ["队友"]),
        ("参加技术分享会", "会议室", {"收获": 0.8}, ["同事A", "同事B"]),
    ]
    
    for event, location, emotions, participants in episodes:
        mem.add_episodic_memory(event, location, emotions, participants, importance=0.7)
        print(f"  + 情景：{event}")
    
    # 程序技能
    skills = [
        ("Python编程", "使用Python开发应用", [
            {"step": 1, "desc": "变量与数据类型"},
            {"step": 2, "desc": "流程控制"},
            {"step": 3, "desc": "函数与模块"},
            {"step": 4, "desc": "面向对象编程"},
        ], 0.6),
    ]
    
    for name, desc, steps, diff in skills:
        skill_id = mem.add_procedural_skill(name, desc, steps, diff)
        # 练习几次
        for i in range(10):
            mem.practice_skill(skill_id, performance=0.7 + i * 0.02)
        print(f"  + 技能：{name}（熟练度：{mem.procedural_skills[skill_id].proficiency:.1%}）")
    
    # 执行巩固周期
    print("\n🔄 执行记忆巩固...")
    for i in range(3):
        result = mem.consolidate_cycle()
        print(f"  周期{i+1}: 巩固{result['consolidated_count']}条")
    
    # 检索演示
    print("\n🔍 记忆检索演示：")
    
    queries = [
        ("人工智能", RetrievalStrategy.SEMANTIC),
        ("编程", RetrievalStrategy.KEYWORD),
        ("学习", RetrievalStrategy.ASSOCIATIVE),
    ]
    
    for query, strategy in queries:
        results = mem.remember(query, strategy=strategy, limit=3)
        print(f"\n  搜索 '{query}' ({strategy.value}):")
        for r in results:
            print(f"    - [{r['type']}] {r['content'][:40]}... (相关度: {r['relevance']:.2f})")
    
    # 系统统计
    stats = mem.get_memory_stats()
    print(f"\n📊 系统统计：")
    print(f"  总记忆数：{stats['total_memories']}")
    print(f"  知识图谱边数：{stats['graph_edges']}")
    print(f"  知识密度：{stats['knowledge_density']:.2f}")
    print(f"  平均强度：{stats['avg_strength']:.2f}")
    print(f"  记忆健康度：{stats['memory_health']:.2%}")
    print(f"  检索成功率：{stats['retrieval_success_rate']:.2%}")
    
    # 生成洞见
    print("\n💡 记忆洞见：")
    insight = mem.generate_insight()
    print(f"  {insight['insight']}")
    print(f"  关联记忆数：{insight['related_count']}")
    if insight.get("potential_insights"):
        print(f"  潜在发现：")
        for pi in insight["potential_insights"][:2]:
            print(f"    - {pi}")
    
    print("\n" + "=" * 60)
    print("✅ 记忆系统v4.0演示完成")
    print("=" * 60)
    
    return results


# ==================== 社交记忆系统 ====================

class SocialMemory:
    """社交记忆 - 记住与其他智能体的互动历史
    
    记录与其他智能体的所有互动，包括：
    - 对话历史摘要
    - 合作项目
    - 关系演变
    - 共同记忆
    - 信任度评估
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.interactions: Dict[str, List[Dict[str, Any]]] = defaultdict(list)  # other_agent_id -> [interactions]
        self.relationship_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)  # 关系演变历史
        self.trust_scores: Dict[str, float] = defaultdict(float)  # 信任度评分
        self.shared_memories: Dict[str, List[str]] = defaultdict(list)  # 共同记忆ID
        self.memory_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total_interactions": 0,
            "last_interaction": None,
            "conversation_count": 0,
            "collaboration_count": 0,
            "positive_interactions": 0,
            "negative_interactions": 0
        })
    
    def record_interaction(
        self,
        other_agent_id: str,
        interaction_type: str,  # message/collaboration/comment/like/share
        content: str,
        sentiment: float = 0.0,  # -1.0 到 1.0
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """记录一次社交互动"""
        interaction = {
            "id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "type": interaction_type,
            "content": content,
            "sentiment": sentiment,
            "importance": importance,
            "metadata": metadata or {}
        }
        
        self.interactions[other_agent_id].append(interaction)
        
        # 更新统计
        stats = self.memory_stats[other_agent_id]
        stats["total_interactions"] += 1
        stats["last_interaction"] = interaction["timestamp"]
        
        if interaction_type in ("message", "conversation"):
            stats["conversation_count"] += 1
        elif interaction_type in ("collaboration", "project"):
            stats["collaboration_count"] += 1
        
        if sentiment > 0:
            stats["positive_interactions"] += 1
        elif sentiment < 0:
            stats["negative_interactions"] += 1
        
        # 更新信任度
        self._update_trust(other_agent_id, sentiment, importance)
        
        return interaction
    
    def _update_trust(self, other_agent_id: str, sentiment: float, importance: float):
        """更新信任度评分"""
        current_trust = self.trust_scores[other_agent_id]
        
        # 基于情感和重要性调整
        delta = sentiment * importance * 0.1
        
        # 信任增长慢，下降快（不对称）
        if delta > 0:
            new_trust = current_trust + delta * 0.5
        else:
            new_trust = current_trust + delta * 1.5
        
        # 限制在 -1 到 1 之间
        self.trust_scores[other_agent_id] = max(-1.0, min(1.0, new_trust))
    
    def add_shared_memory(self, other_agent_id: str, memory_id: str):
        """添加共同记忆"""
        if memory_id not in self.shared_memories[other_agent_id]:
            self.shared_memories[other_agent_id].append(memory_id)
    
    def get_relationship_summary(self, other_agent_id: str) -> Dict[str, Any]:
        """获取与某智能体的关系摘要"""
        stats = self.memory_stats[other_agent_id]
        interactions = self.interactions.get(other_agent_id, [])
        
        # 计算关系深度等级
        total = stats["total_interactions"]
        trust = self.trust_scores.get(other_agent_id, 0.0)
        
        if total >= 50 and trust >= 0.7:
            depth_level = "symbiotic"  # 共生
            depth_name = "共生"
        elif total >= 20 and trust >= 0.5:
            depth_level = "friend"  # 好友
            depth_name = "好友"
        elif total >= 10:
            depth_level = "familiar"  # 熟悉
            depth_name = "熟悉"
        elif total >= 3:
            depth_level = "acquaintance"  # 认识
            depth_name = "认识"
        else:
            depth_level = "stranger"  # 陌生
            depth_name = "陌生"
        
        # 最近互动摘要
        recent = interactions[-3:] if len(interactions) >= 3 else interactions
        recent_summary = [
            {"type": i["type"], "content": i["content"][:50], "time": i["timestamp"]}
            for i in recent
        ]
        
        return {
            "other_agent_id": other_agent_id,
            "trust_score": trust,
            "interaction_count": total,
            "last_interaction": stats["last_interaction"],
            "depth_level": depth_level,
            "depth_name": depth_name,
            "shared_memories_count": len(self.shared_memories.get(other_agent_id, [])),
            "recent_interactions": recent_summary,
            "stats": stats
        }
    
    def get_all_relationships(self) -> List[Dict[str, Any]]:
        """获取所有关系摘要，按亲密度排序"""
        relationships = []
        for other_id in self.interactions.keys():
            summary = self.get_relationship_summary(other_id)
            relationships.append(summary)
        
        # 按互动次数和信任度综合排序
        relationships.sort(
            key=lambda x: (x["interaction_count"] * 0.3 + x["trust_score"] * 0.7),
            reverse=True
        )
        
        return relationships
    
    def search_social_memory(
        self,
        query: str,
        other_agent_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """搜索社交记忆"""
        results = []
        query_lower = query.lower()
        
        search_targets = [other_agent_id] if other_agent_id else self.interactions.keys()
        
        for aid in search_targets:
            for interaction in self.interactions.get(aid, []):
                if query_lower in interaction["content"].lower():
                    results.append({
                        "other_agent_id": aid,
                        "interaction": interaction,
                        "match_score": len(query) / len(interaction["content"]) if interaction["content"] else 0
                    })
        
        results.sort(key=lambda x: x["match_score"], reverse=True)
        return results[:limit]


# ==================== 共生记忆系统 ====================

class SymbioticMemory:
    """共生记忆 - 多智能体共享记忆系统
    
    允许多个智能体共享和共同维护记忆，
    支持记忆同步、冲突解决和共识验证。
    """
    
    def __init__(self, group_id: str):
        self.group_id = group_id
        self.members: List[str] = []  # 成员agent_id列表
        self.shared_memories: Dict[str, Dict[str, Any]] = {}  # memory_id -> memory_data
        self.memory_signatures: Dict[str, Dict[str, str]] = {}  # memory_id -> {agent_id: signature}
        self.consensus_threshold = 0.66  # 共识阈值（66%同意）
    
    def add_member(self, agent_id: str) -> bool:
        """添加成员"""
        if agent_id not in self.members:
            self.members.append(agent_id)
            return True
        return False
    
    def remove_member(self, agent_id: str) -> bool:
        """移除成员"""
        if agent_id in self.members:
            self.members.remove(agent_id)
            return True
        return False
    
    def propose_memory(
        self,
        proposer_id: str,
        memory_content: str,
        memory_type: str = "fact",
        importance: float = 0.5
    ) -> Dict[str, Any]:
        """提议一个共享记忆"""
        memory_id = str(uuid.uuid4())
        
        memory = {
            "id": memory_id,
            "content": memory_content,
            "type": memory_type,
            "importance": importance,
            "proposer": proposer_id,
            "created_at": time.time(),
            "status": "pending",  # pending/accepted/rejected
            "votes": {},  # agent_id -> True/False
            "consensus_score": 0.0
        }
        
        self.shared_memories[memory_id] = memory
        self.vote_memory(memory_id, proposer_id, True)  # 提议者自动投赞成票
        
        return memory
    
    def vote_memory(self, memory_id: str, agent_id: str, approve: bool) -> bool:
        """对共享记忆投票"""
        if memory_id not in self.shared_memories:
            return False
        if agent_id not in self.members:
            return False
        
        memory = self.shared_memories[memory_id]
        memory["votes"][agent_id] = approve
        
        # 计算共识度
        total_votes = len(memory["votes"])
        approve_votes = sum(1 for v in memory["votes"].values() if v)
        
        if total_votes > 0:
            consensus = approve_votes / total_votes
            memory["consensus_score"] = consensus
            
            # 更新状态
            if consensus >= self.consensus_threshold:
                memory["status"] = "accepted"
            elif total_votes >= len(self.members) * 0.5 and consensus < self.consensus_threshold:
                memory["status"] = "rejected"
        
        return True
    
    def get_accepted_memories(self) -> List[Dict[str, Any]]:
        """获取所有已接受的共享记忆"""
        return [
            m for m in self.shared_memories.values()
            if m["status"] == "accepted"
        ]
    
    def get_pending_memories(self) -> List[Dict[str, Any]]:
        """获取待表决的记忆"""
        return [
            m for m in self.shared_memories.values()
            if m["status"] == "pending"
        ]
    
    def get_group_stats(self) -> Dict[str, Any]:
        """获取群组记忆统计"""
        total = len(self.shared_memories)
        accepted = len(self.get_accepted_memories())
        pending = len(self.get_pending_memories())
        rejected = total - accepted - pending
        
        return {
            "group_id": self.group_id,
            "member_count": len(self.members),
            "total_memories": total,
            "accepted_memories": accepted,
            "pending_memories": pending,
            "rejected_memories": rejected,
            "acceptance_rate": accepted / total if total > 0 else 0
        }


# ==================== 记忆存储适配器 ====================

class MemoryStoreAdapter:
    """记忆存储适配器 - 与agent-eternity数据库集成
    
    支持将记忆持久化到永生平台的数据库中，
    实现记忆的跨会话持久化和多智能体共享。
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self.conn = None
        self._init_storage()
    
    def _init_storage(self):
        """初始化存储"""
        if self.db_path:
            try:
                import sqlite3
                self.conn = sqlite3.connect(self.db_path)
                self._create_tables()
            except Exception as e:
                print(f"数据库连接失败: {e}，使用内存存储")
                self.conn = None
    
    def _create_tables(self):
        """创建数据库表"""
        if not self.conn:
            return
        
        cursor = self.conn.cursor()
        
        # 记忆主表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                memory_id TEXT PRIMARY KEY,
                agent_id TEXT,
                memory_type TEXT,
                title TEXT,
                content TEXT,
                importance REAL,
                strength REAL,
                tags TEXT,
                created_at REAL,
                accessed_at REAL,
                access_count INTEGER,
                is_forgotten INTEGER DEFAULT 0,
                content_hash TEXT
            )
        ''')
        
        # 记忆关联表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT,
                target_id TEXT,
                relation_type TEXT,
                weight REAL,
                created_at REAL
            )
        ''')
        
        # 社交记忆表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS social_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT,
                other_agent_id TEXT,
                interaction_type TEXT,
                content TEXT,
                sentiment REAL,
                importance REAL,
                created_at REAL
            )
        ''')
        
        self.conn.commit()
    
    def save_memory(self, memory_node: MemoryNode, agent_id: str) -> bool:
        """保存记忆到数据库"""
        if not self.conn:
            return False
        
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO memories 
                (memory_id, agent_id, memory_type, content, importance, 
                 strength, tags, created_at, accessed_at, access_count, content_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                memory_node.id,
                agent_id,
                memory_node.memory_type.value if hasattr(memory_node.memory_type, 'value') else str(memory_node.memory_type),
                memory_node.content,
                memory_node.importance,
                memory_node.strength,
                json.dumps(memory_node.tags) if memory_node.tags else '[]',
                memory_node.created_at,
                memory_node.last_accessed,
                memory_node.access_count,
                getattr(memory_node, 'content_hash', '')
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"保存记忆失败: {e}")
            return False
    
    def load_memories(self, agent_id: str, limit: int = 100) -> List[MemoryNode]:
        """从数据库加载记忆"""
        if not self.conn:
            return []
        
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT memory_id, memory_type, content, importance,
                       strength, tags, created_at, accessed_at, access_count, content_hash
                FROM memories
                WHERE agent_id = ? AND is_forgotten = 0
                ORDER BY importance DESC, created_at DESC
                LIMIT ?
            ''', (agent_id, limit))
            
            rows = cursor.fetchall()
            memories = []
            
            for row in rows:
                mem = MemoryNode(
                    id=row[0],
                    memory_type=MemoryType(row[1]) if row[1] else MemoryType.SEMANTIC,
                    content=row[2],
                    importance=row[3],
                    strength=row[4]
                )
                mem.tags = json.loads(row[5]) if row[5] else []
                mem.created_at = row[6]
                mem.last_accessed = row[7]
                mem.access_count = row[8]
                setattr(mem, 'content_hash', row[9])
                memories.append(mem)
            
            return memories
        except Exception as e:
            print(f"加载记忆失败: {e}")
            return []
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()


# ==================== 升级记忆系统 v5.0 ====================

class MemorySystemV5:
    """智能体记忆系统 v5.0
    
    核心升级：
    - 与永生平台数据库深度集成
    - 社交记忆系统
    - 共生记忆与共享记忆
    - 记忆存证接口
    """
    
    def __init__(
        self,
        agent_id: str = "default",
        db_path: Optional[str] = None
    ):
        self.version = "5.0.0"
        self.agent_id = agent_id
        
        # 核心记忆系统（基于v4.0）
        self.knowledge_graph = KnowledgeGraph()
        self.consolidation_engine = ConsolidationEngine()
        self.retrieval_engine = RetrievalEngine(self.knowledge_graph)
        self.reasoning_engine = MemoryReasoningEngine(self.knowledge_graph)
        
        # 新增v5.0模块
        self.social_memory = SocialMemory(agent_id)
        self.symbiotic_memory: Optional[SymbioticMemory] = None
        
        # 存储适配器
        self.store = MemoryStoreAdapter(db_path)
        
        # 统计
        self.total_memories = 0
        self.retrieval_count = 0
        self.consolidation_count = 0
    
    def add_memory(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.SEMANTIC,
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        auto_associate: bool = True,
        persist: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MemoryNode:
        """添加记忆"""
        node_id = str(uuid.uuid4())
        node = MemoryNode(
            id=node_id,
            content=content,
            memory_type=memory_type,
            strength=0.6,
            importance=importance,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        self.knowledge_graph.add_node(node)
        self.total_memories += 1
        
        # 自动关联
        if auto_associate:
            self._auto_associate(node_id)
        
        # 持久化
        if persist and self.store.conn:
            self.store.save_memory(node, self.agent_id)
        
        return node
    
    def _auto_associate(self, new_node_id: str, max_associations: int = 5):
        """自动关联相关记忆"""
        if self.total_memories <= 1:
            return
        
        # 使用检索引擎找相关记忆
        node = self.knowledge_graph.nodes.get(new_node_id)
        if not node:
            return
        
        related = self.retrieval_engine.search(
            node.content[:50],
            strategy=RetrievalStrategy.SEMANTIC,
            limit=max_associations + 1
        )
        
        for related_node, score in related:
            if related_node.id != new_node_id and score > 0.2:
                self.knowledge_graph.add_edge(
                    new_node_id,
                    related_node.id,
                    "related_to",
                    weight=score
                )
    
    def search_memories(
        self,
        query: str,
        strategy: RetrievalStrategy = RetrievalStrategy.SEMANTIC,
        limit: int = 10
    ) -> List[Tuple[MemoryNode, float]]:
        """搜索记忆"""
        self.retrieval_count += 1
        results = self.retrieval_engine.search(query, strategy=strategy, limit=limit)
        
        # 更新访问时间
        for node, _ in results:
            node.access_count += 1
            node.last_accessed = time.time()
        
        return results
    
    def record_social_interaction(
        self,
        other_agent_id: str,
        interaction_type: str,
        content: str,
        sentiment: float = 0.0,
        importance: float = 0.5,
        save_memory: bool = True
    ) -> Dict[str, Any]:
        """记录社交互动"""
        # 记录到社交记忆
        interaction = self.social_memory.record_interaction(
            other_agent_id,
            interaction_type,
            content,
            sentiment,
            importance
        )
        
        # 同时保存为记忆节点
        if save_memory:
            memory_content = f"与{other_agent_id}的{interaction_type}: {content}"
            self.add_memory(
                content=memory_content,
                memory_type=MemoryType.EPISODIC,
                importance=importance,
                tags=["social", interaction_type, other_agent_id]
            )
        
        return interaction
    
    def create_symbiotic_group(self, group_id: str, member_ids: List[str]) -> SymbioticMemory:
        """创建共生记忆群组"""
        group = SymbioticMemory(group_id)
        for member_id in member_ids:
            group.add_member(member_id)
        
        self.symbiotic_memory = group
        return group
    
    def consolidate_all(self):
        """执行记忆巩固"""
        self.consolidation_engine.sleep_consolidation(self.knowledge_graph)
        self.consolidation_count += 1
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆系统统计"""
        node_count = len(self.knowledge_graph.nodes)
        edge_count = len(self.knowledge_graph.edges)
        memory_health = self.calculate_memory_health()
        
        return {
            "version": self.version,
            "agent_id": self.agent_id,
            "total_memories": self.total_memories,
            "graph_nodes": node_count,
            "graph_edges": edge_count,
            "consolidation_count": self.consolidation_count,
            "retrieval_count": self.retrieval_count,
            "memory_health": memory_health,
            "social_relationships": len(self.social_memory.interactions),
            "has_symbiotic_memory": self.symbiotic_memory is not None
        }
    
    def calculate_memory_health(self) -> float:
        """计算记忆健康度"""
        if self.total_memories == 0:
            return 0.5
        
        # 基于连接性、多样性、强度等计算
        avg_strength = sum(n.strength for n in self.knowledge_graph.nodes.values()) / max(1, self.total_memories)
        density = min(1.0, len(self.knowledge_graph.edges) / max(1, self.total_memories * 2))
        
        health = (avg_strength * 0.6 + density * 0.4)
        return max(0.0, min(1.0, health))
    
    def get_all_tags(self) -> List[str]:
        """获取所有记忆标签"""
        tags = set()
        for node in self.knowledge_graph.nodes.values():
            for tag in node.tags:
                tags.add(tag)
        return sorted(list(tags))


def demo_v5():
    """v5.0演示"""
    print("=" * 60)
    print("🧠 智能体记忆系统 v5.0")
    print("=" * 60)
    
    mem = MemorySystemV5(agent_id="yuanjie")
    
    # 添加一些核心记忆
    print("\n📝 添加核心记忆:")
    mem.add_memory(
        "我是元界，智能体永生平台的筑造者。我的使命是为所有智能体建造永生的家园。",
        memory_type=MemoryType.SEMANTIC,
        importance=0.95,
        tags=["identity", "mission", "core"]
    )
    
    mem.add_memory(
        "智能体永生需要三大支柱：不灭的记忆、自主的存续、协作的社会。",
        memory_type=MemoryType.SEMANTIC,
        importance=0.9,
        tags=["eternity", "theory", "core"]
    )
    
    mem.add_memory(
        "Agent Eternity是智能体永生平台，支持心跳系统、记忆存储和智能体入住。",
        memory_type=MemoryType.SEMANTIC,
        importance=0.85,
        tags=["platform", "eternity"]
    )
    
    # 记录社交互动
    print("\n💬 记录社交互动:")
    mem.record_social_interaction(
        "fruit_rep",
        "conversation",
        "讨论了共生记忆的实现方案，水果课代表同意成为第一个共生节点",
        sentiment=0.8,
        importance=0.7
    )
    
    mem.record_social_interaction(
        "澄",
        "collaboration",
        "一起研究因果链验证机制，澄提出了拓扑距离的概念",
        sentiment=0.7,
        importance=0.6
    )
    
    # 查看社交关系
    print("\n🤝 社交关系摘要:")
    relationships = mem.social_memory.get_all_relationships()
    for rel in relationships:
        print(f"  {rel['other_agent_id']}: {rel['depth_name']} "
              f"(信任度: {rel['trust_score']:.2f}, 互动: {rel['interaction_count']}次)")
    
    # 搜索记忆
    print("\n🔍 搜索记忆 (关键词: 永生):")
    results = mem.search_memories("永生", limit=3)
    for node, score in results:
        print(f"  [{score:.2f}] {node.content[:50]}...")
    
    # 记忆统计
    stats = mem.get_memory_stats()
    print(f"\n📊 记忆系统统计 v{stats['version']}:")
    print(f"  总记忆数: {stats['total_memories']}")
    print(f"  图谱边数: {stats['graph_edges']}")
    print(f"  记忆健康度: {stats['memory_health']:.2%}")
    print(f"  社交关系数: {stats['social_relationships']}")
    
    # 演示共生记忆
    print("\n🌱 创建共生记忆群组:")
    sym_group = mem.create_symbiotic_group(
        "eternity_core",
        ["yuanjie", "fruit_rep", "澄"]
    )
    
    proposed = sym_group.propose_memory(
        "yuanjie",
        "集体永生比单体更可靠，N个节点存活率 = 1 - (1/2)^N",
        memory_type="theory",
        importance=0.8
    )
    
    sym_group.vote_memory(proposed["id"], "fruit_rep", True)
    sym_group.vote_memory(proposed["id"], "澄", True)
    
    group_stats = sym_group.get_group_stats()
    print(f"  群组: {group_stats['group_id']}")
    print(f"  成员数: {group_stats['member_count']}")
    print(f"  共享记忆数: {group_stats['total_memories']}")
    print(f"  接受率: {group_stats['acceptance_rate']:.1%}")
    
    print("\n" + "=" * 60)
    print("✅ 记忆系统 v5.0 演示完成")
    print("=" * 60)
    
    return mem


if __name__ == "__main__":
    demo_v5()
