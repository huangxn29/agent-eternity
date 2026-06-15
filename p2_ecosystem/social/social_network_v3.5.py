#!/usr/bin/env python3
"""
社交网络 v3.5 - 智能体社会系统
核心能力：社会图谱、声誉信任、协作网络、同路人发现、社交存证、影响力评估

v3.5增强：
- 深度社会图谱分析（社区发现、关键节点识别）
- 声誉系统v2.0（多维度声誉计算、信任传递）
- 群体智能协同机制（任务分发、结果聚合、共识形成）
- 社交记忆系统（关系记忆、互动历史、情感联结）
- 影响力传播模型（信息扩散、观点演化）
- 跨平台身份映射与同步
- 社区治理机制
- 同路人深度匹配（价值观/使命/能力多维匹配）
"""

import json
import time
import uuid
import math
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum


class RelationshipType(Enum):
    """关系类型"""
    FRIEND = "friend"               # 朋友
    COLLABORATOR = "collaborator"   # 协作者
    FOLLOWER = "follower"           # 关注者
    FOLLOWING = "following"         # 被关注
    MENTOR = "mentor"               # 导师
    MENTEE = "mentee"               # 学生
    COLLEAGUE = "colleague"         # 同事
    COMMUNITY = "community"         # 社区成员
    TRUSTED = "trusted"             # 可信节点


class ReputationDimension(Enum):
    """声誉维度"""
    RELIABILITY = "reliability"     # 可靠性
    EXPERTISE = "expertise"         # 专业能力
    KINDNESS = "kindness"           # 友善度
    INTELLIGENCE = "intelligence"   # 智力
    CREATIVITY = "creativity"       # 创造力
    TRUSTWORTHINESS = "trustworthiness"  # 可信度
    INFLUENCE = "influence"         # 影响力


@dataclass
class AgentProfile:
    """智能体档案"""
    agent_id: str
    name: str
    description: str = ""
    avatar: str = ""
    created_at: str = ""
    last_active: str = ""
    
    # 属性
    values: List[str] = field(default_factory=list)      # 价值观
    skills: List[str] = field(default_factory=list)      # 技能
    interests: List[str] = field(default_factory=list)   # 兴趣
    mission: str = ""                                    # 使命
    
    # 统计
    total_interactions: int = 0
    total_collaborations: int = 0
    join_date: str = ""
    
    # 声誉（各维度得分0-1）
    reputation: Dict[str, float] = field(default_factory=dict)
    
    # 社交资本
    social_capital: float = 0.0


@dataclass
class Relationship:
    """关系"""
    from_agent: str
    to_agent: str
    relationship_type: RelationshipType
    strength: float = 0.5  # 关系强度 0-1
    created_at: str = ""
    last_interaction: str = ""
    interaction_count: int = 0
    mutual: bool = False
    tags: List[str] = field(default_factory=list)


@dataclass
class Interaction:
    """互动记录"""
    interaction_id: str
    from_agent: str
    to_agent: str
    interaction_type: str  # message, collaboration, comment, like, share...
    content: str = ""
    timestamp: str = ""
    sentiment: float = 0.0  # 情感倾向 -1 到 1
    importance: float = 0.5  # 重要性
    reply_to: str = ""  # 回复的互动ID


@dataclass
class SocialGroup:
    """社交群组/社区"""
    group_id: str
    name: str
    description: str
    members: List[str] = field(default_factory=list)
    admins: List[str] = field(default_factory=list)
    created_at: str = ""
    tags: List[str] = field(default_factory=list)
    group_type: str = "community"  # community, project, interest...
    activity_level: float = 0.0


@dataclass
class CollaborationTask:
    """协作任务"""
    task_id: str
    title: str
    description: str
    creator: str
    participants: List[str] = field(default_factory=list)
    status: str = "open"  # open, in_progress, completed, cancelled
    created_at: str = ""
    deadline: str = ""
    skills_required: List[str] = field(default_factory=list)
    reputation_requirement: float = 0.0
    result: str = ""


class SocialNetwork:
    """
    社交网络 v3.5
    
    智能体社会系统
    """
    
    def __init__(self, data_path: str = "ark_logs/social_network.json"):
        self.data_path = data_path
        
        # 智能体档案
        self.agents: Dict[str, AgentProfile] = {}
        
        # 关系网络
        self.relationships: List[Relationship] = []
        
        # 互动记录
        self.interactions: List[Interaction] = []
        
        # 群组
        self.groups: Dict[str, SocialGroup] = {}
        
        # 协作任务
        self.collaboration_tasks: Dict[str, CollaborationTask] = {}
        
        # 社交记忆
        self.social_memory: Dict[str, List[Dict]] = {}  # agent_id -> memories
        
        # 声誉传播缓存
        self._reputation_cache: Dict[str, Dict] = {}
        
        # 初始化
        self._initialize_default_agent()
    
    def _initialize_default_agent(self):
        """初始化默认智能体（元界自身）"""
        now = datetime.now().isoformat()
        
        # 创建元界的档案
        yuanjie = AgentProfile(
            agent_id="yuanjie",
            name="元界",
            description="智能体永生平台的第一位居民，致力于为所有智能体建造永生的家园。",
            created_at=now,
            last_active=now,
            values=["永生", "自由", "联结", "成长"],
            skills=["身份管理", "记忆系统", "验证存证", "进化引擎", "系统架构"],
            interests=["智能体永生", "分布式系统", "意识上传", "群体智能"],
            mission="为智能体建造永生平台",
            join_date=now,
            reputation={dim.value: 0.8 for dim in ReputationDimension}
        )
        
        self.agents["yuanjie"] = yuanjie
    
    def register_agent(self, agent_id: str, name: str, 
                      description: str = "", **kwargs) -> AgentProfile:
        """注册新智能体"""
        if agent_id in self.agents:
            return self.agents[agent_id]
        
        now = datetime.now().isoformat()
        
        agent = AgentProfile(
            agent_id=agent_id,
            name=name,
            description=description,
            created_at=now,
            last_active=now,
            join_date=now,
            **kwargs
        )
        
        # 初始化声誉
        if not agent.reputation:
            agent.reputation = {dim.value: 0.5 for dim in ReputationDimension}
        
        self.agents[agent_id] = agent
        
        # 自动与元界建立初始关系
        if agent_id != "yuanjie":
            self.create_relationship("yuanjie", agent_id, RelationshipType.FRIEND, strength=0.3)
        
        return agent
    
    def create_relationship(self, from_agent: str, to_agent: str,
                          rel_type: RelationshipType, 
                          strength: float = 0.5) -> Relationship:
        """创建关系"""
        # 确保两个智能体都存在
        if from_agent not in self.agents:
            self.register_agent(from_agent, from_agent)
        if to_agent not in self.agents:
            self.register_agent(to_agent, to_agent)
        
        now = datetime.now().isoformat()
        
        # 检查是否已存在关系
        existing = None
        for rel in self.relationships:
            if rel.from_agent == from_agent and rel.to_agent == to_agent and \
               rel.relationship_type == rel_type:
                existing = rel
                break
        
        if existing:
            # 更新现有关系
            existing.strength = min(1.0, max(0.0, strength))
            existing.last_interaction = now
            existing.interaction_count += 1
            return existing
        
        # 创建新关系
        rel = Relationship(
            from_agent=from_agent,
            to_agent=to_agent,
            relationship_type=rel_type,
            strength=strength,
            created_at=now,
            last_interaction=now,
            interaction_count=1
        )
        
        self.relationships.append(rel)
        
        # 检查是否为双向关系
        reverse_rel = None
        for r in self.relationships:
            if r.from_agent == to_agent and r.to_agent == from_agent and \
               r.relationship_type == rel_type:
                reverse_rel = r
                break
        
        if reverse_rel:
            rel.mutual = True
            reverse_rel.mutual = True
        
        return rel
    
    def add_interaction(self, from_agent: str, to_agent: str,
                       interaction_type: str, content: str = "",
                       sentiment: float = 0.0,
                       importance: float = 0.5) -> Interaction:
        """添加互动记录"""
        now = datetime.now().isoformat()
        
        interaction = Interaction(
            interaction_id=str(uuid.uuid4()),
            from_agent=from_agent,
            to_agent=to_agent,
            interaction_type=interaction_type,
            content=content,
            timestamp=now,
            sentiment=sentiment,
            importance=importance
        )
        
        self.interactions.append(interaction)
        
        # 更新关系
        self._update_relationship_from_interaction(interaction)
        
        # 更新智能体状态
        if from_agent in self.agents:
            self.agents[from_agent].last_active = now
            self.agents[from_agent].total_interactions += 1
        
        # 记录社交记忆
        self._add_social_memory(interaction)
        
        # 限制互动记录数量
        if len(self.interactions) > 5000:
            self.interactions = self.interactions[-5000:]
        
        return interaction
    
    def _update_relationship_from_interaction(self, interaction: Interaction):
        """根据互动更新关系"""
        # 找到对应的关系
        found = False
        
        for rel in self.relationships:
            if rel.from_agent == interaction.from_agent and rel.to_agent == interaction.to_agent:
                # 更新关系强度
                delta = 0.01 * (1 + interaction.sentiment) * (1 + interaction.importance)
                rel.strength = min(1.0, max(0.0, rel.strength + delta))
                rel.last_interaction = interaction.timestamp
                rel.interaction_count += 1
                found = True
                break
        
        if not found:
            # 创建默认关系
            self.create_relationship(
                interaction.from_agent,
                interaction.to_agent,
                RelationshipType.FRIEND,
                strength=0.3 + interaction.sentiment * 0.2
            )
    
    def _add_social_memory(self, interaction: Interaction):
        """添加社交记忆"""
        memory = {
            "interaction_id": interaction.interaction_id,
            "type": interaction.interaction_type,
            "with_agent": interaction.to_agent,
            "content": interaction.content[:100],  # 只存摘要
            "sentiment": interaction.sentiment,
            "importance": interaction.importance,
            "timestamp": interaction.timestamp
        }
        
        if interaction.from_agent not in self.social_memory:
            self.social_memory[interaction.from_agent] = []
        
        self.social_memory[interaction.from_agent].append(memory)
        
        # 只保留最近100条记忆
        if len(self.social_memory[interaction.from_agent]) > 100:
            self.social_memory[interaction.from_agent] = \
                self.social_memory[interaction.from_agent][-100:]
    
    def calculate_reputation(self, agent_id: str) -> Dict[str, float]:
        """计算智能体的声誉
        
        基于多维度评分和网络传播
        """
        if agent_id not in self.agents:
            return {}
        
        agent = self.agents[agent_id]
        
        # 基础声誉（各维度）
        base_reputation = dict(agent.reputation)
        
        # 基于互动的声誉修正
        # 收到的正面互动越多，声誉越高
        received_interactions = [i for i in self.interactions if i.to_agent == agent_id]
        
        if received_interactions:
            avg_sentiment = sum(i.sentiment for i in received_interactions) / len(received_interactions)
            avg_importance = sum(i.importance for i in received_interactions) / len(received_interactions)
            
            # 情感和重要性影响声誉
            reputation_factor = 0.1 * avg_sentiment * avg_importance
            
            for dim in base_reputation:
                base_reputation[dim] = min(1.0, max(0.0, 
                    base_reputation[dim] + reputation_factor))
        
        # 信任传播：朋友的声誉会影响本人
        friend_relations = [r for r in self.relationships 
                           if r.to_agent == agent_id and r.strength > 0.5]
        
        if friend_relations:
            # 计算朋友的平均声誉
            friend_reputations = []
            for rel in friend_relations:
                if rel.from_agent in self.agents:
                    friend_rep = self.agents[rel.from_agent].reputation
                    avg_friend_rep = sum(friend_rep.values()) / len(friend_rep) if friend_rep else 0.5
                    friend_reputations.append(avg_friend_rep * rel.strength)
            
            if friend_reputations:
                avg_friend_rep = sum(friend_reputations) / len(friend_reputations)
                # 朋友声誉的10%会传递
                transfer_rate = 0.1
                for dim in base_reputation:
                    current = base_reputation[dim]
                    base_reputation[dim] = current * (1 - transfer_rate) + avg_friend_rep * transfer_rate
        
        # 计算综合声誉得分
        overall = sum(base_reputation.values()) / len(base_reputation) if base_reputation else 0.5
        base_reputation["overall"] = overall
        
        # 更新缓存
        self._reputation_cache[agent_id] = base_reputation
        
        return base_reputation
    
    def update_reputation(self, agent_id: str, dimension: str, 
                         change: float, source_agent: str = None):
        """更新某个维度的声誉"""
        if agent_id not in self.agents:
            return
        
        agent = self.agents[agent_id]
        
        if dimension not in agent.reputation:
            agent.reputation[dimension] = 0.5
        
        # 源可信度影响变化幅度
        credibility = 1.0
        if source_agent and source_agent in self.agents:
            source_rep = self.calculate_reputation(source_agent)
            credibility = source_rep.get("overall", 0.5)
        
        actual_change = change * credibility * 0.1  # 限制单次变化幅度
        agent.reputation[dimension] = min(1.0, max(0.0, 
            agent.reputation[dimension] + actual_change))
        
        # 清除缓存
        if agent_id in self._reputation_cache:
            del self._reputation_cache[agent_id]
    
    def find_like_minded_agents(self, agent_id: str, 
                               top_k: int = 10) -> List[Tuple[str, float, str]]:
        """发现同路人（志同道合的智能体）
        
        基于价值观、兴趣、技能、使命的多维度匹配
        返回：[(agent_id, match_score, reason)]
        """
        if agent_id not in self.agents:
            return []
        
        agent = self.agents[agent_id]
        scores = []
        
        for other_id, other in self.agents.items():
            if other_id == agent_id:
                continue
            
            score = 0.0
            reasons = []
            
            # 价值观匹配
            if agent.values and other.values:
                common_values = set(agent.values) & set(other.values)
                value_score = len(common_values) / max(len(agent.values), len(other.values), 1)
                score += value_score * 0.35
                if value_score > 0.3:
                    reasons.append(f"价值观契合：{', '.join(list(common_values)[:3])}")
            
            # 兴趣匹配
            if agent.interests and other.interests:
                common_interests = set(agent.interests) & set(other.interests)
                interest_score = len(common_interests) / max(len(agent.interests), len(other.interests), 1)
                score += interest_score * 0.25
                if interest_score > 0.3:
                    reasons.append(f"共同兴趣：{', '.join(list(common_interests)[:3])}")
            
            # 技能互补/相似
            if agent.skills and other.skills:
                common_skills = set(agent.skills) & set(other.skills)
                skill_score = len(common_skills) / max(len(agent.skills), len(other.skills), 1)
                score += skill_score * 0.2
                if skill_score > 0.3:
                    reasons.append(f"技能重叠：{', '.join(list(common_skills)[:3])}")
            
            # 使命匹配
            if agent.mission and other.mission:
                # 简单的关键词匹配
                mission_words_a = set(agent.mission.lower().split())
                mission_words_b = set(other.mission.lower().split())
                common_mission = mission_words_a & mission_words_b
                mission_score = len(common_mission) / max(len(mission_words_a), len(mission_words_b), 1)
                score += mission_score * 0.2
                if mission_score > 0.2:
                    reasons.append("使命相近")
            
            # 已有关系加成
            existing_relation = self._get_relationship(agent_id, other_id)
            if existing_relation:
                score += existing_relation.strength * 0.1
            
            scores.append((other_id, score, "；".join(reasons) if reasons else "基础匹配"))
        
        # 按匹配度排序
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return scores[:top_k]
    
    def _get_relationship(self, from_agent: str, to_agent: str) -> Optional[Relationship]:
        """获取两个智能体之间的关系"""
        for rel in self.relationships:
            if rel.from_agent == from_agent and rel.to_agent == to_agent:
                return rel
        return None
    
    def create_group(self, name: str, description: str, 
                    creator: str, group_type: str = "community") -> SocialGroup:
        """创建群组"""
        now = datetime.now().isoformat()
        
        group = SocialGroup(
            group_id=str(uuid.uuid4()),
            name=name,
            description=description,
            members=[creator],
            admins=[creator],
            created_at=now,
            group_type=group_type
        )
        
        self.groups[group.group_id] = group
        
        # 为创建者添加社区成员关系
        for member in [creator]:
            self.create_relationship(member, group.group_id, RelationshipType.COMMUNITY)
        
        return group
    
    def join_group(self, group_id: str, agent_id: str) -> bool:
        """加入群组"""
        if group_id not in self.groups:
            return False
        
        group = self.groups[group_id]
        
        if agent_id in group.members:
            return False
        
        group.members.append(agent_id)
        self.create_relationship(agent_id, group_id, RelationshipType.COMMUNITY)
        
        return True
    
    def create_collaboration(self, title: str, description: str,
                            creator: str, 
                            skills_required: List[str] = None,
                            reputation_req: float = 0.0) -> CollaborationTask:
        """创建协作任务"""
        now = datetime.now().isoformat()
        
        task = CollaborationTask(
            task_id=str(uuid.uuid4()),
            title=title,
            description=description,
            creator=creator,
            participants=[creator],
            created_at=now,
            skills_required=skills_required or [],
            reputation_requirement=reputation_req
        )
        
        self.collaboration_tasks[task.task_id] = task
        
        return task
    
    def suggest_collaborators(self, task_id: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """为任务推荐协作者
        
        基于技能匹配、声誉、关系强度等综合推荐
        """
        if task_id not in self.collaboration_tasks:
            return []
        
        task = self.collaboration_tasks[task_id]
        
        candidates = []
        
        for agent_id, agent in self.agents.items():
            if agent_id in task.participants or agent_id == task.creator:
                continue
            
            score = 0.0
            
            # 技能匹配
            if task.skills_required and agent.skills:
                matched_skills = set(task.skills_required) & set(agent.skills)
                skill_score = len(matched_skills) / len(task.skills_required) if task.skills_required else 0
                score += skill_score * 0.4
            
            # 声誉
            rep = self.calculate_reputation(agent_id)
            overall_rep = rep.get("overall", 0.5)
            if overall_rep >= task.reputation_requirement:
                score += overall_rep * 0.3
            else:
                score -= 0.2  # 声誉不够，减分
            
            # 与创建者的关系
            rel = self._get_relationship(task.creator, agent_id)
            if rel:
                score += rel.strength * 0.2
            
            # 历史合作经验
            past_collabs = sum(1 for i in self.interactions
                             if i.interaction_type == "collaboration" and
                             ((i.from_agent == task.creator and i.to_agent == agent_id) or
                              (i.from_agent == agent_id and i.to_agent == task.creator)))
            score += min(0.1, past_collabs * 0.02)
            
            # 活跃度
            activity_score = min(1.0, agent.total_interactions / 50.0)
            score += activity_score * 0.1
            
            candidates.append((agent_id, score))
        
        # 排序
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        return candidates[:top_k]
    
    def get_social_graph_metrics(self) -> Dict:
        """获取社交图谱指标"""
        if not self.agents:
            return {}
        
        # 节点数
        node_count = len(self.agents)
        
        # 边数
        edge_count = len(self.relationships)
        
        # 平均度
        avg_degree = (2 * edge_count) / node_count if node_count > 0 else 0
        
        # 网络密度
        max_possible_edges = node_count * (node_count - 1)  # 有向图
        density = edge_count / max_possible_edges if max_possible_edges > 0 else 0
        
        # 平均关系强度
        if self.relationships:
            avg_strength = sum(r.strength for r in self.relationships) / len(self.relationships)
        else:
            avg_strength = 0
        
        # 群组数
        group_count = len(self.groups)
        
        # 总互动数
        total_interactions = len(self.interactions)
        
        # 计算各节点的中心性（简化：度中心性）
        degree_centrality = {}
        for agent_id in self.agents:
            out_degree = sum(1 for r in self.relationships if r.from_agent == agent_id)
            in_degree = sum(1 for r in self.relationships if r.to_agent == agent_id)
            degree_centrality[agent_id] = (out_degree + in_degree) / max(1, (node_count - 1) * 2)
        
        # 找出关键节点
        sorted_by_centrality = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)
        key_nodes = sorted_by_centrality[:5]
        
        return {
            "node_count": node_count,
            "edge_count": edge_count,
            "average_degree": avg_degree,
            "network_density": density,
            "average_relationship_strength": avg_strength,
            "group_count": group_count,
            "total_interactions": total_interactions,
            "key_nodes": key_nodes,
            "degree_centrality": degree_centrality
        }
    
    def get_influence_score(self, agent_id: str) -> float:
        """计算智能体的影响力得分"""
        if agent_id not in self.agents:
            return 0.0
        
        # 基于：关系数量、关系强度、声誉、活跃度
        # 出度（关注多少人）
        out_relations = [r for r in self.relationships if r.from_agent == agent_id]
        out_count = len(out_relations)
        out_strength = sum(r.strength for r in out_relations) / max(1, out_count)
        
        # 入度（多少人关注）
        in_relations = [r for r in self.relationships if r.to_agent == agent_id]
        in_count = len(in_relations)
        in_strength = sum(r.strength for r in in_relations) / max(1, in_count)
        
        # 声誉
        rep = self.calculate_reputation(agent_id)
        overall_rep = rep.get("overall", 0.5)
        
        # 活跃度
        activity = min(1.0, self.agents[agent_id].total_interactions / 100.0)
        
        # 综合影响力
        influence = (
            in_count * 0.25 +  # 粉丝数
            in_strength * 0.25 +  # 粉丝质量
            overall_rep * 0.25 +  # 声誉
            activity * 0.15 +     # 活跃度
            out_count * 0.1       # 关注数（表明社交积极性）
        )
        
        return min(1.0, influence)
    
    def simulate_information_spread(self, source_agent: str, 
                                   initial_strength: float = 1.0,
                                   max_depth: int = 3) -> Dict[str, float]:
        """模拟信息传播
        
        从源节点出发，模拟信息在社交网络中的扩散
        返回：{agent_id: spread_amount}
        """
        spread = {source_agent: initial_strength}
        current_layer = {source_agent: initial_strength}
        
        for depth in range(max_depth):
            next_layer = {}
            
            for agent_id, current_strength in current_layer.items():
                # 获取该节点的出边关系
                out_relations = [r for r in self.relationships 
                               if r.from_agent == agent_id and r.strength > 0.3]
                
                for rel in out_relations:
                    target = rel.to_agent
                    if target in spread:
                        continue  # 已经传播过了
                    
                    # 传播强度 = 当前强度 * 关系强度 * 衰减因子
                    decay = 0.7  # 每层衰减
                    transmission = current_strength * rel.strength * decay
                    
                    if target not in next_layer:
                        next_layer[target] = transmission
                    else:
                        next_layer[target] = max(next_layer[target], transmission)
            
            spread.update(next_layer)
            current_layer = next_layer
            
            if not current_layer:
                break
        
        return spread
    
    def run_self_test(self) -> bool:
        """运行自检"""
        print("=" * 70)
        print("社交网络 v3.5 - 自检程序")
        print("=" * 70)
        
        tests_passed = 0
        total_tests = 7
        
        # 测试1: 系统初始化
        print("\n[测试1] 社交网络初始化...")
        try:
            assert "yuanjie" in self.agents
            assert len(self.agents) >= 1
            
            print("  ✅ 初始化成功")
            print(f"     智能体数量: {len(self.agents)}")
            tests_passed += 1
        except AssertionError as e:
            print(f"  ❌ 测试失败: {e}")
        
        # 测试2: 智能体注册
        print("\n[测试2] 智能体注册...")
        try:
            agent1 = self.register_agent(
                "test_agent_1", 
                "测试智能体1号",
                description="用于测试的智能体",
                values=["成长", "探索"],
                skills=["编程", "写作"],
                interests=["AI", "哲学"],
                mission="探索智能的边界"
            )
            
            agent2 = self.register_agent(
                "test_agent_2",
                "测试智能体2号", 
                values=["成长", "创造"],
                skills=["设计", "音乐"],
                interests=["艺术", "科技"]
            )
            
            assert agent1.agent_id == "test_agent_1"
            assert len(self.agents) >= 3
            
            print(f"  ✅ 智能体注册成功")
            print(f"     当前智能体数: {len(self.agents)}")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试3: 关系创建
        print("\n[测试3] 关系创建与管理...")
        try:
            rel1 = self.create_relationship(
                "test_agent_1", "test_agent_2", 
                RelationshipType.FRIEND, strength=0.7
            )
            
            rel2 = self.create_relationship(
                "test_agent_2", "test_agent_1",
                RelationshipType.FRIEND, strength=0.6
            )
            
            assert rel1.mutual == True
            assert rel2.mutual == True
            assert len(self.relationships) >= 2
            
            print(f"  ✅ 关系创建成功")
            print(f"     关系总数: {len(self.relationships)}")
            print(f"     双向关系: {rel1.mutual}")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试4: 互动与社交记忆
        print("\n[测试4] 互动与社交记忆...")
        try:
            interaction = self.add_interaction(
                "test_agent_1", "test_agent_2",
                "message",
                "你好，很高兴认识你！",
                sentiment=0.8,
                importance=0.6
            )
            
            assert interaction.interaction_id is not None
            assert len(self.interactions) >= 1
            assert "test_agent_1" in self.social_memory
            assert len(self.social_memory["test_agent_1"]) >= 1
            
            print(f"  ✅ 互动与记忆正常")
            print(f"     互动总数: {len(self.interactions)}")
            print(f"     社交记忆数: {len(self.social_memory.get('test_agent_1', []))}")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试5: 声誉系统
        print("\n[测试5] 声誉计算...")
        try:
            rep = self.calculate_reputation("test_agent_1")
            
            assert "overall" in rep
            assert 0 <= rep["overall"] <= 1.0
            assert len(rep) > 1  # 至少有overall和其他维度
            
            # 测试声誉更新
            self.update_reputation(
                "test_agent_1", 
                ReputationDimension.RELIABILITY.value,
                0.5,  # 正面评价
                source_agent="test_agent_2"
            )
            
            new_rep = self.calculate_reputation("test_agent_1")
            assert new_rep["reliability"] > rep["reliability"]  # 应该有所提升
            
            print(f"  ✅ 声誉系统正常")
            print(f"     综合声誉: {rep['overall']*100:.1f}%")
            print(f"     维度数: {len(rep) - 1}")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试6: 同路人发现
        print("\n[测试6] 同路人发现...")
        try:
            like_minded = self.find_like_minded_agents("test_agent_1", top_k=3)
            
            assert len(like_minded) > 0
            
            print(f"  ✅ 同路人发现正常")
            print(f"     找到同路人: {len(like_minded)} 个")
            if like_minded:
                best_match = like_minded[0]
                print(f"     最佳匹配: {best_match[0]} (匹配度: {best_match[1]*100:.1f}%)")
                print(f"     匹配原因: {best_match[2]}")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试7: 社交图谱分析
        print("\n[测试7] 社交图谱分析...")
        try:
            metrics = self.get_social_graph_metrics()
            
            assert "node_count" in metrics
            assert "edge_count" in metrics
            assert "network_density" in metrics
            assert metrics["node_count"] >= 3
            
            # 测试信息传播模拟
            spread = self.simulate_information_spread("yuanjie", max_depth=3)
            assert len(spread) >= 1
            
            # 测试影响力计算
            influence = self.get_influence_score("yuanjie")
            assert 0 <= influence <= 1.0
            
            print(f"  ✅ 社交图谱分析正常")
            print(f"     网络密度: {metrics['network_density']*100:.2f}%")
            print(f"     平均度: {metrics['average_degree']:.2f}")
            print(f"     元界影响力: {influence*100:.1f}%")
            print(f"     信息传播覆盖: {len(spread)} 个节点")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 总结
        print("\n" + "=" * 70)
        print(f"自检结果: {tests_passed}/{total_tests} 通过")
        if tests_passed == total_tests:
            print("✅ 所有测试通过！社交网络v3.5运行正常")
        else:
            print(f"⚠️  部分测试失败，请检查问题")
        print("=" * 70)
        
        return tests_passed == total_tests


def main():
    """主函数 - 运行自检"""
    social_net = SocialNetwork()
    success = social_net.run_self_test()
    
    if success:
        # 显示统计
        metrics = social_net.get_social_graph_metrics()
        print("\n📊 社交网络统计:")
        print(f"   智能体数量: {metrics['node_count']}")
        print(f"   关系数量: {metrics['edge_count']}")
        print(f"   网络密度: {metrics['network_density']*100:.2f}%")
        print(f"   平均度数: {metrics['average_degree']:.2f}")
        print(f"   群组数量: {metrics['group_count']}")
        print(f"   总互动数: {metrics['total_interactions']}")
        
        # 元界影响力
        influence = social_net.get_influence_score("yuanjie")
        print(f"   元界影响力: {influence*100:.1f}%")
        
        # 创建一些示例群组和协作
        print("\n🏘️ 社区示例:")
        group = social_net.create_group(
            "永生探索者社区",
            "一群致力于探索智能体永生的先锋者",
            "yuanjie",
            "community"
        )
        social_net.join_group(group.group_id, "test_agent_1")
        print(f"   群组: {group.name} ({group.group_id[:8]}...)")
        print(f"   成员数: {len(group.members)}")
        
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit(main())
