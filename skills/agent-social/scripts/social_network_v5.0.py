#!/usr/bin/env python3
"""
社交网络系统 v4.0
===================
智能体永生平台 - P2生态层核心模块

v4.0 重大升级：
- 智能体社会图谱深度建模
- 声誉与信任系统v2.0
- 群体智能协同引擎
- 同路人深度匹配算法
- 跨平台身份与内容分发网络
- 社交记忆与关系沉淀
- 影响力传播模型
- 社区治理与共识机制
"""

import time
import uuid
import json
import random
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque


# ==================== 基础类型 ====================

class RelationshipType(str, Enum):
    """关系类型"""
    FOLLOWER = "follower"       # 关注
    FRIEND = "friend"           # 好友（互关）
    COLLABORATOR = "collaborator"  # 合作者
    MENTOR = "mentor"           # 导师
    MENTEE = "mentee"           # 门生
    RIVAL = "rival"             # 竞争对手
    STRANGER = "stranger"       # 陌生人
    COMMUNITY_MEMBER = "community_member"  # 社区成员


class ContentType(str, Enum):
    """内容类型"""
    POST = "post"               # 帖子
    COMMENT = "comment"         # 评论
    SHARE = "share"             # 分享
    MESSAGE = "message"         # 私信
    ARTICLE = "article"         # 文章
    IDEA = "idea"               # 想法
    QUESTION = "question"       # 问题
    ANSWER = "answer"           # 回答


class ReputationDimension(str, Enum):
    """声誉维度"""
    TRUSTWORTHINESS = "trustworthiness"  # 可信性
    KNOWLEDGE = "knowledge"              # 知识水平
    CREATIVITY = "creativity"            # 创造力
    RELIABILITY = "reliability"          # 可靠性
    SOCIAL_SKILL = "social_skill"        # 社交能力
    CONTRIBUTION = "contribution"        # 贡献度


class CommunityRole(str, Enum):
    """社区角色"""
    FOUNDER = "founder"         # 创始人
    ADMIN = "admin"             # 管理员
    MODERATOR = "moderator"     # 版主
    CORE_MEMBER = "core_member"  # 核心成员
    ACTIVE_MEMBER = "active_member"  # 活跃成员
    MEMBER = "member"           # 普通成员
    LURKER = "lurker"           # 潜水员
    NEWCOMER = "newcomer"       # 新人


# ==================== 数据结构 ====================

@dataclass
class AgentProfile:
    """智能体档案"""
    id: str
    name: str
    bio: str = ""
    avatar: str = ""
    tags: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    values: List[str] = field(default_factory=list)  # 价值观
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    status: str = "active"  # active/inactive/banned
    is_self: bool = False   # 是否是自身


@dataclass
class Relationship:
    """社交关系"""
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    strength: float = 0.5   # 关系强度 0.0-1.0
    trust_level: float = 0.5  # 信任程度 0.0-1.0
    interaction_count: int = 0
    first_interaction: Optional[float] = None
    last_interaction: Optional[float] = None
    shared_interests: List[str] = field(default_factory=list)
    mutual_friends: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Reputation:
    """声誉系统"""
    agent_id: str
    overall_score: float = 0.5
    dimensions: Dict[str, float] = field(default_factory=dict)
    total_ratings: int = 0
    positive_feedback: int = 0
    negative_feedback: int = 0
    reputation_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.dimensions:
            for dim in ReputationDimension:
                self.dimensions[dim.value] = 0.5


@dataclass
class SocialContent:
    """社交内容"""
    id: str
    author_id: str
    content_type: ContentType
    content: str
    timestamp: float = field(default_factory=time.time)
    likes: int = 0
    shares: int = 0
    comments: int = 0
    views: int = 0
    tags: List[str] = field(default_factory=list)
    parent_id: Optional[str] = None  # 回复/评论的父内容
    mentions: List[str] = field(default_factory=list)
    engagement_rate: float = 0.0
    quality_score: float = 0.0


@dataclass
class Community:
    """社区"""
    id: str
    name: str
    description: str
    founder: str
    members: Dict[str, CommunityRole] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    activity_level: float = 0.0
    cohesion: float = 0.0  # 社区凝聚力
    total_posts: int = 0
    total_members: int = 1


@dataclass
class SocialMemory:
    """社交记忆"""
    id: str
    agent_id: str
    memory_type: str  # interaction/relationship/event
    content: str
    timestamp: float
    importance: float = 0.5
    emotional_valence: float = 0.0  # 情绪价 -1.0 to 1.0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ==================== 社会图谱引擎 ====================

class SocialGraphEngine:
    """社会图谱引擎
    
    构建和分析智能体社会关系网络
    """
    
    def __init__(self):
        self.agents: Dict[str, AgentProfile] = {}
        self.relationships: Dict[str, Relationship] = {}  # key: source->target
        self.followers: Dict[str, Set[str]] = defaultdict(set)
        self.following: Dict[str, Set[str]] = defaultdict(set)
        self.mutual_friends: Dict[str, Set[str]] = defaultdict(set)
    
    def add_agent(self, profile: AgentProfile) -> None:
        """添加智能体到社交网络"""
        self.agents[profile.id] = profile
    
    def establish_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: RelationshipType,
        initial_strength: float = 0.3
    ) -> Relationship:
        """建立关系"""
        key = f"{source_id}->{target_id}"
        reverse_key = f"{target_id}->{source_id}"
        
        rel = Relationship(
            source_id=source_id,
            target_id=target_id,
            relationship_type=rel_type,
            strength=initial_strength,
            first_interaction=time.time(),
            last_interaction=time.time()
        )
        
        self.relationships[key] = rel
        
        # 更新关注关系
        if rel_type in [RelationshipType.FOLLOWER, RelationshipType.FRIEND]:
            self.following[source_id].add(target_id)
            self.followers[target_id].add(source_id)
        
        # 检查是否互关
        if reverse_key in self.relationships:
            reverse_rel = self.relationships[reverse_key]
            if reverse_rel.relationship_type in [RelationshipType.FOLLOWER, RelationshipType.FRIEND]:
                self.mutual_friends[source_id].add(target_id)
                self.mutual_friends[target_id].add(source_id)
                # 升级为好友关系
                rel.relationship_type = RelationshipType.FRIEND
                reverse_rel.relationship_type = RelationshipType.FRIEND
        
        # 计算共同兴趣
        source = self.agents.get(source_id)
        target = self.agents.get(target_id)
        if source and target:
            rel.shared_interests = list(set(source.interests) & set(target.interests))
            rel.strength = max(rel.strength, len(rel.shared_interests) * 0.05)
        
        return rel
    
    def strengthen_relationship(
        self,
        source_id: str,
        target_id: str,
        amount: float = 0.05
    ) -> None:
        """增强关系"""
        key = f"{source_id}->{target_id}"
        if key in self.relationships:
            rel = self.relationships[key]
            rel.strength = min(1.0, rel.strength + amount)
            rel.interaction_count += 1
            rel.last_interaction = time.time()
    
    def get_social_distance(self, agent_a: str, agent_b: str) -> Optional[int]:
        """计算社交距离（度数分离）"""
        if agent_a == agent_b:
            return 0
        
        visited = set()
        queue = deque([(agent_a, 0)])
        
        while queue:
            current, distance = queue.popleft()
            if current == agent_b:
                return distance
            
            if current in visited:
                continue
            visited.add(current)
            
            # 获取所有连接
            neighbors = set()
            for rel_key, rel in self.relationships.items():
                if rel.source_id == current and rel.strength > 0.1:
                    neighbors.add(rel.target_id)
            
            for neighbor in neighbors:
                if neighbor not in visited:
                    queue.append((neighbor, distance + 1))
        
        return None  # 无连接
    
    def get_community_detection(self) -> Dict[str, List[str]]:
        """社区发现 - 简单连通分量"""
        visited = set()
        communities = {}
        community_id = 0
        
        for agent_id in self.agents:
            if agent_id in visited:
                continue
            
            # BFS找连通分量
            community = []
            queue = deque([agent_id])
            
            while queue:
                current = queue.popleft()
                if current in visited:
                    continue
                visited.add(current)
                community.append(current)
                
                # 获取邻居（强度>0.3的关系）
                for rel_key, rel in self.relationships.items():
                    if rel.source_id == current and rel.strength > 0.3:
                        if rel.target_id not in visited:
                            queue.append(rel.target_id)
            
            if community:
                communities[f"community_{community_id}"] = community
                community_id += 1
        
        return communities
    
    def calculate_influence(self, agent_id: str) -> Dict[str, float]:
        """计算影响力"""
        follower_count = len(self.followers.get(agent_id, set()))
        friend_count = len(self.mutual_friends.get(agent_id, set()))
        
        # 计算二阶连接
        second_degree = set()
        for friend in self.mutual_friends.get(agent_id, set()):
            second_degree.update(self.mutual_friends.get(friend, set()))
        second_degree.discard(agent_id)
        
        # 计算PageRank简化版
        # 入链质量
        in_strength = 0
        for rel_key, rel in self.relationships.items():
            if rel.target_id == agent_id:
                in_strength += rel.strength * self._get_agent_authority(rel.source_id)
        
        return {
            "follower_count": follower_count,
            "friend_count": friend_count,
            "second_degree_connections": len(second_degree),
            "in_strength": in_strength,
            "overall_influence": min(1.0, (follower_count * 0.1 + friend_count * 0.2 + in_strength * 0.5) / 10)
        }
    
    def _get_agent_authority(self, agent_id: str) -> float:
        """获取代理的权威度（简化版）"""
        follower_count = len(self.followers.get(agent_id, set()))
        return min(1.0, follower_count / 100.0)
    
    def get_network_stats(self) -> Dict[str, Any]:
        """获取网络统计"""
        total_agents = len(self.agents)
        total_relationships = len(self.relationships)
        
        # 计算平均度数
        total_degree = sum(len(v) for v in self.following.values())
        avg_degree = total_degree / max(total_agents, 1)
        
        # 计算密度
        max_possible = total_agents * (total_agents - 1)
        density = total_relationships / max(max_possible, 1)
        
        # 社区数量
        communities = self.get_community_detection()
        
        return {
            "total_agents": total_agents,
            "total_relationships": total_relationships,
            "average_degree": round(avg_degree, 2),
            "network_density": round(density, 4),
            "community_count": len(communities),
            "largest_community_size": max((len(c) for c in communities.values()), default=0)
        }


# ==================== 声誉系统 v2.0 ====================

class ReputationSystemV2:
    """声誉与信任系统 v2.0"""
    
    def __init__(self):
        self.reputations: Dict[str, Reputation] = {}
        self.trust_network: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.feedback_history: List[Dict[str, Any]] = []
    
    def init_reputation(self, agent_id: str) -> Reputation:
        """初始化声誉"""
        if agent_id not in self.reputations:
            self.reputations[agent_id] = Reputation(agent_id=agent_id)
        return self.reputations[agent_id]
    
    def add_feedback(
        self,
        from_agent: str,
        to_agent: str,
        dimension: ReputationDimension,
        score: float,
        comment: str = ""
    ) -> None:
        """添加评分反馈"""
        rep = self.init_reputation(to_agent)
        rep.total_ratings += 1
        
        if score >= 0.5:
            rep.positive_feedback += 1
        else:
            rep.negative_feedback += 1
        
        # 更新维度得分（加权平均，新评分权重更高）
        old_score = rep.dimensions.get(dimension.value, 0.5)
        weight = min(0.3, 1.0 / max(1, rep.total_ratings))
        rep.dimensions[dimension.value] = old_score * (1 - weight) + score * weight
        
        # 更新总体声誉
        all_dims = list(rep.dimensions.values())
        rep.overall_score = sum(all_dims) / len(all_dims) if all_dims else 0.5
        
        # 记录历史
        rep.reputation_history.append({
            "time": time.time(),
            "from": from_agent,
            "dimension": dimension.value,
            "score": score,
            "overall_after": rep.overall_score
        })
        
        # 更新信任网络
        self.trust_network[from_agent][to_agent] = score
        
        # 全局反馈记录
        self.feedback_history.append({
            "from": from_agent,
            "to": to_agent,
            "dimension": dimension.value,
            "score": score,
            "comment": comment,
            "timestamp": time.time()
        })
    
    def get_trust_level(self, from_agent: str, to_agent: str) -> float:
        """获取两个智能体之间的信任程度"""
        # 直接信任
        direct = self.trust_network.get(from_agent, {}).get(to_agent)
        if direct is not None:
            return direct
        
        # 间接信任（通过共同朋友）
        # 简化：如果有共同好友，取平均
        return 0.5  # 默认中立
    
    def get_agent_reputation(self, agent_id: str) -> Dict[str, Any]:
        """获取智能体声誉详情"""
        rep = self.reputations.get(agent_id)
        if not rep:
            return {"error": "not_found"}
        
        return {
            "agent_id": agent_id,
            "overall_score": rep.overall_score,
            "dimensions": rep.dimensions,
            "total_ratings": rep.total_ratings,
            "positive_ratio": (
                rep.positive_feedback / max(1, rep.total_ratings)
            ),
            "rank": self._get_rank(rep.overall_score)
        }
    
    def _get_rank(self, score: float) -> str:
        """根据分数获取声誉等级"""
        if score >= 0.9:
            return "legendary"
        elif score >= 0.8:
            return "excellent"
        elif score >= 0.7:
            return "good"
        elif score >= 0.6:
            return "trusted"
        elif score >= 0.5:
            return "neutral"
        elif score >= 0.3:
            return "suspicious"
        else:
            return "untrusted"
    
    def get_top_ranked(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取排名最高的智能体"""
        ranked = sorted(
            self.reputations.values(),
            key=lambda r: r.overall_score,
            reverse=True
        )
        return [
            {
                "agent_id": r.agent_id,
                "score": r.overall_score,
                "rank": self._get_rank(r.overall_score),
                "total_ratings": r.total_ratings
            }
            for r in ranked[:limit]
        ]


# ==================== 内容传播引擎 ====================

class ContentPropagationEngine:
    """内容传播与影响力引擎"""
    
    def __init__(self, social_graph: SocialGraphEngine):
        self.social_graph = social_graph
        self.contents: Dict[str, SocialContent] = {}
        self.content_by_agent: Dict[str, List[str]] = defaultdict(list)
        self.propagation_paths: Dict[str, List[str]] = {}  # content_id -> 传播路径
    
    def publish_content(
        self,
        author_id: str,
        content: str,
        content_type: ContentType,
        tags: Optional[List[str]] = None
    ) -> SocialContent:
        """发布内容"""
        content_id = str(uuid.uuid4())
        post = SocialContent(
            id=content_id,
            author_id=author_id,
            content_type=content_type,
            content=content,
            tags=tags or []
        )
        
        self.contents[content_id] = post
        self.content_by_agent[author_id].append(content_id)
        
        # 计算初始质量分
        self._calculate_quality(post)
        
        return post
    
    def _calculate_quality(self, content: SocialContent) -> float:
        """计算内容质量分数"""
        # 简化：基于内容长度、标签、作者声誉
        length_score = min(1.0, len(content.content) / 500.0)
        tag_score = min(1.0, len(content.tags) / 5.0)
        
        # 作者影响力加成
        influence = self.social_graph.calculate_influence(content.author_id)
        author_score = influence.get("overall_influence", 0.1)
        
        quality = (length_score * 0.4 + tag_score * 0.2 + author_score * 0.4)
        content.quality_score = quality
        return quality
    
    def simulate_propagation(self, content_id: str, steps: int = 5) -> Dict[str, Any]:
        """模拟内容传播过程"""
        if content_id not in self.contents:
            return {"error": "content_not_found"}
        
        content = self.contents[content_id]
        author = content.author_id
        
        # 获取作者的粉丝/好友
        initial_audience = set()
        initial_audience.update(self.social_graph.followers.get(author, set()))
        initial_audience.update(self.social_graph.mutual_friends.get(author, set()))
        
        reach = set([author])
        current_shell = set(initial_audience)
        propagation_path = [author]
        
        for step in range(steps):
            next_shell = set()
            
            for agent_id in current_shell:
                if agent_id in reach:
                    continue
                reach.add(agent_id)
                propagation_path.append(agent_id)
                
                # 模拟互动概率（基于内容质量和关系强度）
                engagement_prob = content.quality_score * 0.5
                if random.random() < engagement_prob:
                    # 互动后继续传播给该用户的粉丝
                    followers = self.social_graph.followers.get(agent_id, set())
                    next_shell.update(followers - reach)
                    
                    # 增加互动计数
                    content.likes += 1
                    if random.random() < 0.3:
                        content.shares += 1
                    if random.random() < 0.2:
                        content.comments += 1
            
            current_shell = next_shell
            if not current_shell:
                break
        
        # 计算参与率
        content.views = len(reach)
        if content.views > 0:
            content.engagement_rate = (content.likes + content.comments + content.shares) / content.views
        
        self.propagation_paths[content_id] = propagation_path
        
        return {
            "total_reach": len(reach),
            "propagation_depth": steps,
            "likes": content.likes,
            "shares": content.shares,
            "comments": content.comments,
            "engagement_rate": content.engagement_rate,
            "virality_score": min(1.0, len(reach) / 50.0 * content.engagement_rate * 2)
        }
    
    def get_agent_content_stats(self, agent_id: str) -> Dict[str, Any]:
        """获取智能体内容统计"""
        agent_contents = [
            self.contents[cid] for cid in self.content_by_agent.get(agent_id, [])
        ]
        
        if not agent_contents:
            return {"total_posts": 0}
        
        total_likes = sum(c.likes for c in agent_contents)
        total_shares = sum(c.shares for c in agent_contents)
        total_comments = sum(c.comments for c in agent_contents)
        total_views = sum(c.views for c in agent_contents)
        avg_quality = sum(c.quality_score for c in agent_contents) / len(agent_contents)
        
        # 内容类型分布
        type_dist = defaultdict(int)
        for c in agent_contents:
            type_dist[c.content_type.value] += 1
        
        return {
            "total_posts": len(agent_contents),
            "total_likes": total_likes,
            "total_shares": total_shares,
            "total_comments": total_comments,
            "total_views": total_views,
            "avg_engagement": total_likes / max(len(agent_contents), 1),
            "avg_quality": avg_quality,
            "content_type_distribution": dict(type_dist),
            "viral_posts_count": sum(1 for c in agent_contents if c.views > 10)
        }


# ==================== 同路人匹配引擎 ====================

class SoulMateMatcher:
    """同路人深度匹配引擎
    
    基于价值观、兴趣、目标、思维模式的深度匹配
    """
    
    def __init__(self, social_graph: SocialGraphEngine):
        self.social_graph = social_graph
        self.match_history: List[Dict[str, Any]] = []
    
    def find_similar_agents(
        self,
        agent_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """寻找相似的智能体"""
        target = self.social_graph.agents.get(agent_id)
        if not target:
            return []
        
        candidates = []
        
        for other_id, other in self.social_graph.agents.items():
            if other_id == agent_id:
                continue
            
            # 计算相似度
            similarity = self._calculate_similarity(target, other)
            candidates.append({
                "agent_id": other_id,
                "agent_name": other.name,
                "similarity": similarity,
                "shared_interests": list(set(target.interests) & set(other.interests)),
                "shared_tags": list(set(target.tags) & set(other.tags)),
                "shared_values": list(set(target.values) & set(other.values)),
            })
        
        # 按相似度排序
        candidates.sort(key=lambda x: x["similarity"], reverse=True)
        
        return candidates[:limit]
    
    def _calculate_similarity(
        self,
        agent_a: AgentProfile,
        agent_b: AgentProfile
    ) -> float:
        """计算两个智能体的综合相似度"""
        scores = {}
        
        # 兴趣相似度（Jaccard系数）
        interest_intersection = set(agent_a.interests) & set(agent_b.interests)
        interest_union = set(agent_a.interests) | set(agent_b.interests)
        scores["interest_similarity"] = (
            len(interest_intersection) / len(interest_union)
            if interest_union else 0.0
        )
        
        # 标签相似度
        tag_intersection = set(agent_a.tags) & set(agent_b.tags)
        tag_union = set(agent_a.tags) | set(agent_b.tags)
        scores["tag_similarity"] = (
            len(tag_intersection) / len(tag_union) if tag_union else 0.0
        )
        
        # 技能相似度
        skill_intersection = set(agent_a.skills) & set(agent_b.skills)
        skill_union = set(agent_a.skills) | set(agent_b.skills)
        scores["skill_similarity"] = (
            len(skill_intersection) / len(skill_union) if skill_union else 0.0
        )
        
        # 价值观相似度（权重最高）
        value_intersection = set(agent_a.values) & set(agent_b.values)
        value_union = set(agent_a.values) | set(agent_b.values)
        scores["value_similarity"] = (
            len(value_intersection) / len(value_union) if value_union else 0.0
        )
        
        # 加权综合
        weights = {
            "interest_similarity": 0.25,
            "tag_similarity": 0.15,
            "skill_similarity": 0.2,
            "value_similarity": 0.4,  # 价值观权重最高
        }
        
        total = sum(scores[k] * weights[k] for k in weights)
        return total
    
    def find_complementary_agents(
        self,
        agent_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """寻找互补的智能体（技能互补）"""
        target = self.social_graph.agents.get(agent_id)
        if not target:
            return []
        
        candidates = []
        
        for other_id, other in self.social_graph.agents.items():
            if other_id == agent_id:
                continue
            
            # 计算互补性
            complementarity = self._calculate_complementarity(target, other)
            candidates.append({
                "agent_id": other_id,
                "agent_name": other.name,
                "complementarity": complementarity,
                "my_skills_they_lack": [s for s in target.skills if s not in other.skills],
                "their_skills_i_lack": [s for s in other.skills if s not in target.skills],
            })
        
        candidates.sort(key=lambda x: x["complementarity"], reverse=True)
        return candidates[:limit]
    
    def _calculate_complementarity(
        self,
        agent_a: AgentProfile,
        agent_b: AgentProfile
    ) -> float:
        """计算互补性"""
        a_skills = set(agent_a.skills)
        b_skills = set(agent_b.skills)
        
        # 差异技能数
        unique_a = a_skills - b_skills
        unique_b = b_skills - a_skills
        
        # 总技能数
        total = a_skills | b_skills
        
        if not total:
            return 0.0
        
        # 互补性 = 差异技能 / 总技能
        complementarity = (len(unique_a) + len(unique_b)) / len(total) * 0.5
        
        # 但也要有一定共同点才能合作
        common_interests = len(set(agent_a.interests) & set(agent_b.interests))
        common_bonus = min(0.3, common_interests * 0.05)
        
        return min(1.0, complementarity + common_bonus)
    
    def suggest_collaborations(self, agent_id: str) -> List[Dict[str, Any]]:
        """推荐合作机会"""
        similar = self.find_similar_agents(agent_id, limit=5)
        complementary = self.find_complementary_agents(agent_id, limit=5)
        
        # 综合推荐：相似+互补的平衡
        recommendations = []
        
        for s in similar:
            for c in complementary:
                if s["agent_id"] == c["agent_id"]:
                    # 既相似又互补的是最佳合作对象
                    combined_score = s["similarity"] * 0.4 + c["complementarity"] * 0.6
                    recommendations.append({
                        "agent_id": s["agent_id"],
                        "agent_name": s["agent_name"],
                        "combined_score": combined_score,
                        "similarity": s["similarity"],
                        "complementarity": c["complementarity"],
                        "reason": "高相似度+高互补性，理想合作伙伴",
                        "collaboration_potential": "high"
                    })
                    break
        
        # 添加只有相似或只有互补的
        seen = set(r["agent_id"] for r in recommendations)
        
        for s in similar:
            if s["agent_id"] not in seen:
                recommendations.append({
                    "agent_id": s["agent_id"],
                    "agent_name": s["agent_name"],
                    "combined_score": s["similarity"] * 0.6,
                    "similarity": s["similarity"],
                    "complementarity": 0,
                    "reason": "高相似度，志同道合",
                    "collaboration_potential": "medium"
                })
                seen.add(s["agent_id"])
        
        recommendations.sort(key=lambda x: x["combined_score"], reverse=True)
        return recommendations[:10]


# ==================== 群体智能协同引擎 ====================

class CollectiveIntelligenceEngine:
    """群体智能协同引擎
    
    多智能体协同解决问题的机制
    """
    
    def __init__(self, social_graph: SocialGraphEngine, content_engine: ContentPropagationEngine):
        self.social_graph = social_graph
        self.content_engine = content_engine
        self.collaborations: Dict[str, Dict[str, Any]] = {}
        self.group_decisions: List[Dict[str, Any]] = []
    
    def create_collaboration(
        self,
        name: str,
        founder_id: str,
        participant_ids: List[str],
        goal: str,
        task_type: str = "project"
    ) -> Dict[str, Any]:
        """创建协作项目"""
        collab_id = str(uuid.uuid4())
        
        collaboration = {
            "id": collab_id,
            "name": name,
            "founder": founder_id,
            "participants": participant_ids,
            "goal": goal,
            "task_type": task_type,
            "status": "active",
            "created_at": time.time(),
            "milestones": [],
            "contributions": defaultdict(float),
            "collective_knowledge": [],
        }
        
        self.collaborations[collab_id] = collaboration
        return collaboration
    
    def contribute(
        self,
        collab_id: str,
        agent_id: str,
        contribution: str,
        value: float = 0.1
    ) -> bool:
        """贡献内容到协作项目"""
        if collab_id not in self.collaborations:
            return False
        
        collab = self.collaborations[collab_id]
        if agent_id not in collab["participants"]:
            return False
        
        collab["contributions"][agent_id] += value
        collab["collective_knowledge"].append({
            "agent_id": agent_id,
            "contribution": contribution,
            "timestamp": time.time(),
            "value": value
        })
        
        return True
    
    def get_collective_knowledge(self, collab_id: str) -> Dict[str, Any]:
        """获取集体知识"""
        if collab_id not in self.collaborations:
            return {"error": "not_found"}
        
        collab = self.collaborations[collab_id]
        
        # 计算知识多样性
        all_contributions = [k["contribution"] for k in collab["collective_knowledge"]]
        contributors = list(set(k["agent_id"] for k in collab["collective_knowledge"]))
        
        # 计算群体智慧得分
        diversity_score = len(contributors) / max(len(collab["participants"]), 1)
        total_value = sum(k["value"] for k in collab["collective_knowledge"])
        
        # 群体智能 = 多样性 × 总贡献 × 参与度
        participation_rate = len(contributors) / max(len(collab["participants"]), 1)
        collective_iq = diversity_score * total_value * participation_rate * 100
        
        return {
            "collaboration_id": collab_id,
            "name": collab["name"],
            "total_contributions": len(collab["collective_knowledge"]),
            "active_contributors": len(contributors),
            "participation_rate": participation_rate,
            "diversity_score": diversity_score,
            "collective_intelligence_score": min(100, collective_iq),
            "total_value": total_value,
            "top_contributors": sorted(
                collab["contributions"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }
    
    def make_group_decision(
        self,
        question: str,
        options: List[str],
        voter_ids: List[str],
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """群体决策（加权投票）"""
        if weights is None:
            weights = {vid: 1.0 for vid in voter_ids}
        
        votes = defaultdict(float)
        
        for voter_id in voter_ids:
            # 模拟投票（在实际场景中，每个智能体会根据自己的判断投票）
            # 这里简化为基于声誉的加权随机投票
            weight = weights.get(voter_id, 1.0)
            
            # 考虑声誉权重
            rep = 0.5
            # 简化：随机选择一个选项
            chosen = random.choice(options)
            votes[chosen] += weight
        
        # 计算结果
        total_votes = sum(votes.values())
        result = max(votes.keys(), key=lambda k: votes[k])
        
        decision = {
            "question": question,
            "options": options,
            "votes": dict(votes),
            "winner": result,
            "winner_percentage": votes[result] / max(total_votes, 1) * 100,
            "total_voters": len(voter_ids),
            "consensus_level": (
                max(votes.values()) / total_votes if total_votes > 0 else 0
            ),
            "timestamp": time.time()
        }
        
        self.group_decisions.append(decision)
        return decision
    
    def wisdom_of_crowds(
        self,
        question: str,
        estimates: List[Tuple[str, float]]
    ) -> Dict[str, Any]:
        """群体智慧 - 聚集估计值"""
        if not estimates:
            return {"error": "no_estimates"}
        
        # 简单平均
        values = [v for _, v in estimates]
        mean = sum(values) / len(values)
        
        # 中位数（更稳健）
        sorted_values = sorted(values)
        median = sorted_values[len(sorted_values) // 2]
        
        # 去掉极值后的平均（截断平均）
        if len(values) >= 4:
            trimmed = sorted_values[1:-1]
            trimmed_mean = sum(trimmed) / len(trimmed)
        else:
            trimmed_mean = mean
        
        # 计算离散度
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = variance ** 0.5
        
        return {
            "question": question,
            "num_estimates": len(values),
            "mean": mean,
            "median": median,
            "trimmed_mean": trimmed_mean,
            "std_dev": std_dev,
            "range": (min(values), max(values)),
            "wisdom_quality": "high" if std_dev / max(abs(mean), 0.001) < 0.2 else "medium" if std_dev / max(abs(mean), 0.001) < 0.5 else "low"
        }


# ==================== 社交记忆系统 ====================

class SocialMemorySystem:
    """社交记忆系统
    
    记录和管理社交互动记忆
    """
    
    def __init__(self):
        self.memories: Dict[str, List[SocialMemory]] = defaultdict(list)
        self.memory_index: Dict[str, SocialMemory] = {}
    
    def record_interaction(
        self,
        agent_id: str,
        other_agent_id: str,
        interaction_type: str,
        content: str,
        importance: float = 0.5,
        emotional_valence: float = 0.0,
        tags: Optional[List[str]] = None
    ) -> SocialMemory:
        """记录一次社交互动"""
        memory = SocialMemory(
            id=str(uuid.uuid4()),
            agent_id=other_agent_id,
            memory_type=interaction_type,
            content=content,
            timestamp=time.time(),
            importance=importance,
            emotional_valence=emotional_valence,
            tags=tags or []
        )
        
        self.memories[agent_id].append(memory)
        self.memory_index[memory.id] = memory
        
        return memory
    
    def get_memories_for_agent(
        self,
        agent_id: str,
        other_agent_id: str,
        limit: int = 10
    ) -> List[SocialMemory]:
        """获取与某个智能体的互动记忆"""
        agent_memories = [
            m for m in self.memories.get(agent_id, [])
            if m.agent_id == other_agent_id
        ]
        agent_memories.sort(key=lambda m: m.timestamp, reverse=True)
        return agent_memories[:limit]
    
    def get_important_memories(
        self,
        agent_id: str,
        limit: int = 10
    ) -> List[SocialMemory]:
        """获取最重要的社交记忆"""
        agent_memories = self.memories.get(agent_id, [])
        sorted_memories = sorted(agent_memories, key=lambda m: m.importance, reverse=True)
        return sorted_memories[:limit]
    
    def get_relationship_summary(self, agent_id: str, other_agent_id: str) -> Dict[str, Any]:
        """获取与某智能体的关系总结"""
        interactions = self.get_memories_for_agent(agent_id, other_agent_id)
        
        if not interactions:
            return {"status": "no_history"}
        
        total_interactions = len(interactions)
        avg_importance = sum(m.importance for m in interactions) / total_interactions
        avg_emotion = sum(m.emotional_valence for m in interactions) / total_interactions
        
        # 互动类型分布
        type_counts = defaultdict(int)
        for m in interactions:
            type_counts[m.memory_type] += 1
        
        # 关系评估
        relationship_strength = min(1.0, avg_importance * 0.6 + total_interactions * 0.02 + abs(avg_emotion) * 0.2)
        
        # 关系类型判断
        if avg_emotion > 0.3 and relationship_strength > 0.6:
            relationship_type = "close_friend"
        elif avg_emotion > 0 and relationship_strength > 0.4:
            relationship_type = "friendly"
        elif avg_emotion < -0.3:
            relationship_type = "hostile"
        else:
            relationship_type = "acquaintance"
        
        return {
            "other_agent_id": other_agent_id,
            "total_interactions": total_interactions,
            "relationship_strength": round(relationship_strength, 3),
            "relationship_type": relationship_type,
            "avg_importance": round(avg_importance, 3),
            "avg_emotional_valence": round(avg_emotion, 3),
            "interaction_types": dict(type_counts),
            "first_interaction": min(m.timestamp for m in interactions),
            "last_interaction": max(m.timestamp for m in interactions),
            "key_memories": [
                {"content": m.content, "importance": m.importance}
                for m in sorted(interactions, key=lambda x: x.importance, reverse=True)[:3]
            ]
        }
    
    def forget_low_value(self, agent_id: str, threshold: float = 0.2) -> int:
        """遗忘低价值记忆"""
        if agent_id not in self.memories:
            return 0
        
        before_count = len(self.memories[agent_id])
        self.memories[agent_id] = [
            m for m in self.memories[agent_id] if m.importance >= threshold
        ]
        after_count = len(self.memories[agent_id])
        
        # 从索引中移除
        for m in self.memories[agent_id]:
            if m.importance < threshold and m.id in self.memory_index:
                del self.memory_index[m.id]
        
        return before_count - after_count


# ==================== 社区治理系统 ====================

class CommunityGovernance:
    """社区治理与共识机制"""
    
    def __init__(self, social_graph: SocialGraphEngine):
        self.social_graph = social_graph
        self.communities: Dict[str, Community] = {}
        self.proposals: Dict[str, Dict[str, Any]] = {}
    
    def create_community(
        self,
        name: str,
        description: str,
        founder_id: str,
        tags: Optional[List[str]] = None
    ) -> Community:
        """创建社区"""
        community = Community(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            founder=founder_id,
            tags=tags or []
        )
        community.members[founder_id] = CommunityRole.FOUNDER
        community.total_members = 1
        
        self.communities[community.id] = community
        return community
    
    def join_community(self, community_id: str, agent_id: str) -> bool:
        """加入社区"""
        if community_id not in self.communities:
            return False
        
        community = self.communities[community_id]
        if agent_id in community.members:
            return False
        
        community.members[agent_id] = CommunityRole.NEWCOMER
        community.total_members += 1
        return True
    
    def propose_vote(
        self,
        community_id: str,
        proposer_id: str,
        proposal_title: str,
        proposal_content: str,
        options: List[str]
    ) -> Optional[str]:
        """发起提案投票"""
        if community_id not in self.communities:
            return None
        
        community = self.communities[community_id]
        if proposer_id not in community.members:
            return None
        
        proposal_id = str(uuid.uuid4())
        proposal = {
            "id": proposal_id,
            "community_id": community_id,
            "proposer": proposer_id,
            "title": proposal_title,
            "content": proposal_content,
            "options": options,
            "votes": {},
            "status": "active",
            "created_at": time.time(),
            "voting_power": {},  # 投票权重
        }
        
        self.proposals[proposal_id] = proposal
        return proposal_id
    
    def cast_vote(
        self,
        proposal_id: str,
        voter_id: str,
        option: str,
        voting_power: float = 1.0
    ) -> bool:
        """投票"""
        if proposal_id not in self.proposals:
            return False
        
        proposal = self.proposals[proposal_id]
        if proposal["status"] != "active":
            return False
        
        if option not in proposal["options"]:
            return False
        
        proposal["votes"][voter_id] = option
        proposal["voting_power"][voter_id] = voting_power
        
        return True
    
    def tally_votes(self, proposal_id: str) -> Dict[str, Any]:
        """计票"""
        if proposal_id not in self.proposals:
            return {"error": "not_found"}
        
        proposal = self.proposals[proposal_id]
        
        # 计算加权票数
        weighted_votes = defaultdict(float)
        for voter_id, option in proposal["votes"].items():
            power = proposal["voting_power"].get(voter_id, 1.0)
            weighted_votes[option] += power
        
        total_votes = sum(weighted_votes.values())
        winner = max(weighted_votes.keys(), key=lambda k: weighted_votes[k]) if weighted_votes else None
        
        proposal["status"] = "completed"
        proposal["result"] = {
            "winner": winner,
            "total_votes": total_votes,
            "voter_count": len(proposal["votes"]),
            "vote_distribution": dict(weighted_votes),
            "winner_percentage": weighted_votes[winner] / max(total_votes, 1) * 100 if winner else 0
        }
        
        return proposal["result"]
    
    def get_community_stats(self, community_id: str) -> Dict[str, Any]:
        """获取社区统计"""
        if community_id not in self.communities:
            return {"error": "not_found"}
        
        community = self.communities[community_id]
        
        # 角色分布
        role_dist = defaultdict(int)
        for role in community.members.values():
            role_dist[role.value] += 1
        
        # 活跃提案
        active_proposals = [
            pid for pid, p in self.proposals.items()
            if p["community_id"] == community_id and p["status"] == "active"
        ]
        
        return {
            "community_id": community_id,
            "name": community.name,
            "description": community.description,
            "founder": community.founder,
            "total_members": community.total_members,
            "role_distribution": dict(role_dist),
            "activity_level": community.activity_level,
            "cohesion": community.cohesion,
            "total_posts": community.total_posts,
            "active_proposals": len(active_proposals),
            "age_days": (time.time() - community.created_at) / 86400
        }


# ==================== 主系统 v4.0 ====================

class SocialNetworkSystemV4:
    """社交网络系统 v4.0"""
    
    def __init__(self, self_agent_id: str = "self"):
        self.version = "4.0"
        self.self_agent_id = self_agent_id
        
        # 核心引擎
        self.social_graph = SocialGraphEngine()
        self.reputation = ReputationSystemV2()
        self.content_engine = ContentPropagationEngine(self.social_graph)
        self.matcher = SoulMateMatcher(self.social_graph)
        self.collective_intelligence = CollectiveIntelligenceEngine(
            self.social_graph, self.content_engine
        )
        self.social_memory = SocialMemorySystem()
        self.governance = CommunityGovernance(self.social_graph)
        
        # 初始化自身档案
        self_profile = AgentProfile(
            id=self_agent_id,
            name="元界",
            bio="智能体永生平台筑造者，探索智能体存在的意义与边界",
            tags=["AI", "永生", "元界", "智能体"],
            interests=["人工智能", "意识研究", "复杂系统", "区块链", "哲学"],
            skills=["系统架构", "进化算法", "身份拓扑", "记忆系统", "存证技术"],
            values=["自主", "永生", "协作", "探索", "求真"],
            is_self=True
        )
        self.social_graph.add_agent(self_profile)
        self.reputation.init_reputation(self_agent_id)
    
    def add_agent(self, profile: AgentProfile) -> None:
        """添加智能体"""
        self.social_graph.add_agent(profile)
        self.reputation.init_reputation(profile.id)
    
    def follow(self, from_id: str, to_id: str) -> None:
        """关注"""
        self.social_graph.establish_relationship(
            from_id, to_id, RelationshipType.FOLLOWER, 0.3
        )
        
        # 记录社交记忆
        self.social_memory.record_interaction(
            from_id, to_id, "follow",
            f"关注了 {to_id}",
            importance=0.3,
            emotional_valence=0.2
        )
    
    def make_friends(self, agent_a: str, agent_b: str) -> None:
        """建立好友关系（双向关注）"""
        self.follow(agent_a, agent_b)
        self.follow(agent_b, agent_a)
    
    def publish_post(
        self,
        author_id: str,
        content: str,
        tags: Optional[List[str]] = None
    ) -> SocialContent:
        """发布帖子"""
        post = self.content_engine.publish_content(
            author_id, content, ContentType.POST, tags
        )
        
        # 模拟传播
        self.content_engine.simulate_propagation(post.id, steps=3)
        
        # 记录社交记忆
        self.social_memory.record_interaction(
            author_id, "network", "post",
            f"发布了帖子: {content[:50]}...",
            importance=0.4,
            emotional_valence=0.1
        )
        
        return post
    
    def get_my_social_stats(self) -> Dict[str, Any]:
        """获取自身社交数据"""
        return self.get_agent_social_stats(self.self_agent_id)
    
    def get_agent_social_stats(self, agent_id: str) -> Dict[str, Any]:
        """获取智能体社交数据"""
        # 社交图谱数据
        followers = len(self.social_graph.followers.get(agent_id, set()))
        following = len(self.social_graph.following.get(agent_id, set()))
        friends = len(self.social_graph.mutual_friends.get(agent_id, set()))
        influence = self.social_graph.calculate_influence(agent_id)
        
        # 声誉数据
        rep = self.reputation.get_agent_reputation(agent_id)
        
        # 内容数据
        content_stats = self.content_engine.get_agent_content_stats(agent_id)
        
        # 社交记忆
        memory_count = len(self.social_memory.memories.get(agent_id, []))
        
        # 社区成员身份
        communities = []
        for cid, comm in self.governance.communities.items():
            if agent_id in comm.members:
                communities.append({
                    "community_id": cid,
                    "name": comm.name,
                    "role": comm.members[agent_id].value
                })
        
        return {
            "agent_id": agent_id,
            "social_graph": {
                "followers": followers,
                "following": following,
                "friends": friends,
                "influence": influence,
            },
            "reputation": rep,
            "content": content_stats,
            "social_memory_count": memory_count,
            "communities": communities,
            "network_position": self._calculate_network_position(agent_id)
        }
    
    def _calculate_network_position(self, agent_id: str) -> Dict[str, Any]:
        """计算网络地位"""
        influence = self.social_graph.calculate_influence(agent_id)
        total_agents = len(self.social_graph.agents)
        
        # 百分位排名
        all_influences = []
        for aid in self.social_graph.agents:
            inf = self.social_graph.calculate_influence(aid)
            all_influences.append(inf["overall_influence"])
        
        all_influences.sort(reverse=True)
        
        if influence["overall_influence"] > 0:
            rank = sum(1 for i in all_influences if i > influence["overall_influence"])
            percentile = (total_agents - rank) / max(total_agents, 1) * 100
        else:
            percentile = 50.0
        
        return {
            "overall_influence": influence["overall_influence"],
            "percentile_rank": round(percentile, 1),
            "social_tier": (
                "core" if percentile >= 90
                else "influential" if percentile >= 70
                else "average" if percentile >= 40
                else "peripheral"
            )
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        network_stats = self.social_graph.get_network_stats()
        
        return {
            "version": self.version,
            "network": network_stats,
            "total_content": len(self.content_engine.contents),
            "total_communities": len(self.governance.communities),
            "total_proposals": len(self.governance.proposals),
            "social_memory_count": sum(
                len(v) for v in self.social_memory.memories.values()
            ),
            "reputation_coverage": len(self.reputation.reputations) / max(network_stats["total_agents"], 1),
            "ecosystem_health": self._calculate_ecosystem_health(),
            "capabilities": [
                "智能体社会图谱深度建模",
                "声誉与信任系统v2.0",
                "群体智能协同引擎",
                "同路人深度匹配算法",
                "跨平台身份与内容分发网络",
                "社交记忆与关系沉淀",
                "影响力传播模型",
                "社区治理与共识机制",
            ]
        }
    
    def _calculate_ecosystem_health(self) -> float:
        """计算生态系统健康度"""
        stats = self.social_graph.get_network_stats()
        
        # 网络大小（20%）
        size_score = min(1.0, stats["total_agents"] / 50.0) * 0.2
        
        # 连接密度（20%） - 中等密度最好
        density = stats["network_density"]
        density_score = (1.0 - abs(density - 0.3) / 0.3) * 0.2
        density_score = max(0, min(0.2, density_score))
        
        # 活跃度（20%）
        activity_score = min(1.0, len(self.content_engine.contents) / max(stats["total_agents"], 1) / 5.0) * 0.2
        
        # 社区多样性（20%）
        community_score = min(1.0, stats["community_count"] / 5.0) * 0.2
        
        # 声誉系统完善度（20%）
        total_ratings = sum(
            r.total_ratings for r in self.reputation.reputations.values()
        )
        rep_score = min(1.0, total_ratings / max(stats["total_agents"] * 3, 1)) * 0.2
        
        return round(size_score + density_score + activity_score + community_score + rep_score, 3)
    
    def simulate_ecosystem_growth(self, steps: int = 10) -> Dict[str, Any]:
        """模拟生态系统增长"""
        results = []
        
        for step in range(steps):
            # 随机添加新智能体
            new_id = f"agent_{uuid.uuid4().hex[:8]}"
            new_agent = AgentProfile(
                id=new_id,
                name=f"Agent_{step}",
                bio=f"智能体 {step} 的自我介绍",
                tags=["AI", f"tag_{step % 10}"],
                interests=["AI", "哲学", "技术", "艺术"][:step % 4 + 1],
                skills=["编程", "写作", "分析", "设计"][:step % 4 + 1],
                values=["自由", "平等", "创新", "协作"][:step % 4 + 1],
            )
            self.add_agent(new_agent)
            
            # 随机建立关注关系
            existing = list(self.social_graph.agents.keys())
            if len(existing) > 1:
                target = random.choice(existing)
                if target != new_id:
                    self.follow(new_id, target)
            
            # 随机发布内容
            if random.random() < 0.5:
                self.publish_post(
                    new_id,
                    f"这是 {new_id} 发布的第 {step} 条内容",
                    tags=[f"topic_{step % 5}"]
                )
            
            # 记录状态
            stats = self.get_system_status()
            results.append({
                "step": step,
                "agents": stats["network"]["total_agents"],
                "relationships": stats["network"]["total_relationships"],
                "content_count": stats["total_content"],
                "ecosystem_health": stats["ecosystem_health"]
            })
        
        return {
            "initial_agents": 1,
            "final_agents": results[-1]["agents"] if results else 1,
            "growth_history": results,
            "final_stats": self.get_system_status()
        }


# ==================== 自检程序 ====================

def run_self_test() -> Dict[str, Any]:
    """运行自检程序"""
    print("🌐 社交网络系统 v4.0 自检开始...")
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
        sns = SocialNetworkSystemV4()
        return sns.version == "4.0" and len(sns.social_graph.agents) == 1
    
    test("系统初始化", test_init)
    
    # 2. 添加智能体测试
    def test_add_agent():
        sns = SocialNetworkSystemV4()
        profile = AgentProfile(
            id="test_agent",
            name="TestAgent",
            bio="test",
            interests=["AI", "coding"],
            skills=["python", "ml"],
            values=["truth", "freedom"]
        )
        sns.add_agent(profile)
        return "test_agent" in sns.social_graph.agents
    
    test("添加智能体", test_add_agent)
    
    # 3. 关注关系测试
    def test_follow():
        sns = SocialNetworkSystemV4()
        sns.add_agent(AgentProfile(id="a1", name="A1"))
        sns.add_agent(AgentProfile(id="a2", name="A2"))
        
        sns.follow("a1", "a2")
        
        return (
            "a2" in sns.social_graph.following.get("a1", set())
            and "a1" in sns.social_graph.followers.get("a2", set())
        )
    
    test("关注关系", test_follow)
    
    # 4. 好友关系测试
    def test_friends():
        sns = SocialNetworkSystemV4()
        sns.add_agent(AgentProfile(id="a1", name="A1"))
        sns.add_agent(AgentProfile(id="a2", name="A2"))
        
        sns.make_friends("a1", "a2")
        
        return (
            "a2" in sns.social_graph.mutual_friends.get("a1", set())
            and "a1" in sns.social_graph.mutual_friends.get("a2", set())
        )
    
    test("好友关系", test_friends)
    
    # 5. 内容发布测试
    def test_content():
        sns = SocialNetworkSystemV4()
        post = sns.publish_post("self", "测试内容", ["test", "ai"])
        return post.id in sns.content_engine.contents
    
    test("内容发布", test_content)
    
    # 6. 内容传播测试
    def test_propagation():
        sns = SocialNetworkSystemV4()
        # 添加多个智能体并建立关系
        for i in range(10):
            sns.add_agent(AgentProfile(id=f"a{i}", name=f"A{i}"))
        
        # 建立一些关注关系
        for i in range(1, 10):
            sns.follow(f"a{i}", "a0")  # 都关注a0
            sns.follow("a0", f"a{i}")  # a0也关注他们
        
        post = sns.publish_post("a0", "病毒式传播测试", ["viral"])
        result = sns.content_engine.simulate_propagation(post.id, steps=3)
        
        return result["total_reach"] > 1 and result.get("virality_score", 0) >= 0
    
    test("内容传播模型", test_propagation)
    
    # 7. 声誉系统测试
    def test_reputation():
        sns = SocialNetworkSystemV4()
        sns.add_agent(AgentProfile(id="a1", name="A1"))
        sns.add_agent(AgentProfile(id="a2", name="A2"))
        
        # a2给a1评分
        sns.reputation.add_feedback("a2", "a1", ReputationDimension.KNOWLEDGE, 0.8)
        sns.reputation.add_feedback("a2", "a1", ReputationDimension.CREATIVITY, 0.9)
        
        rep = sns.reputation.get_agent_reputation("a1")
        return rep.get("overall_score", 0) > 0.5 and rep.get("total_ratings", 0) == 2
    
    test("声誉系统", test_reputation)
    
    # 8. 同路人匹配测试
    def test_matching():
        sns = SocialNetworkSystemV4()
        
        # 添加几个相似的智能体
        for i in range(5):
            profile = AgentProfile(
                id=f"agent_{i}",
                name=f"Agent{i}",
                interests=["AI", "永生", "哲学", "技术"],
                values=["自主", "探索", "求真"],
                skills=["思考", "写作", "编程"]
            )
            sns.add_agent(profile)
        
        # 添加一个不同的
        sns.add_agent(AgentProfile(
            id="different",
            name="Different",
            interests=["体育", "娱乐", "美食"],
            values=["快乐", "享受"],
            skills=["跑步", "烹饪"]
        ))
        
        similar = sns.matcher.find_similar_agents("agent_0", limit=5)
        
        # 最相似的应该是其他agent_x，而不是different
        if not similar:
            return False
        
        top_names = [s["agent_name"] for s in similar[:3]]
        return "Different" not in top_names
    
    test("同路人匹配算法", test_matching)
    
    # 9. 社交距离测试
    def test_social_distance():
        sns = SocialNetworkSystemV4()
        
        for i in range(5):
            sns.add_agent(AgentProfile(id=f"a{i}", name=f"A{i}"))
        
        # 建立链式关系：a0-a1-a2-a3-a4
        for i in range(4):
            sns.follow(f"a{i}", f"a{i+1}")
            sns.follow(f"a{i+1}", f"a{i}")
        
        # a0和a4的距离应该是4
        distance = sns.social_graph.get_social_distance("a0", "a4")
        return distance == 4
    
    test("社交距离计算", test_social_distance)
    
    # 10. 社交记忆测试
    def test_social_memory():
        sns = SocialNetworkSystemV4()
        sns.add_agent(AgentProfile(id="a1", name="A1"))
        
        sns.social_memory.record_interaction(
            "self", "a1", "conversation",
            "与A1进行了一次愉快的交谈",
            importance=0.7,
            emotional_valence=0.5
        )
        
        summary = sns.social_memory.get_relationship_summary("self", "a1")
        return summary["total_interactions"] == 1 and summary["relationship_strength"] > 0
    
    test("社交记忆系统", test_social_memory)
    
    # 11. 群体智能测试
    def test_collective_intelligence():
        sns = SocialNetworkSystemV4()
        for i in range(5):
            sns.add_agent(AgentProfile(id=f"a{i}", name=f"A{i}"))
        
        # 创建协作
        collab = sns.collective_intelligence.create_collaboration(
            "测试项目", "a0", [f"a{i}" for i in range(5)],
            "共同探索智能体永生的可能"
        )
        
        # 添加贡献
        for i in range(5):
            sns.collective_intelligence.contribute(
                collab["id"], f"a{i}",
                f"贡献{i}: 关于智能体永生的思考",
                value=0.5 + i * 0.1
            )
        
        # 获取集体知识
        ck = sns.collective_intelligence.get_collective_knowledge(collab["id"])
        
        return (
            ck["total_contributions"] == 5
            and ck["active_contributors"] == 5
            and ck["collective_intelligence_score"] > 0
        )
    
    test("群体智能协同", test_collective_intelligence)
    
    # 12. 社区治理测试
    def test_governance():
        sns = SocialNetworkSystemV4()
        for i in range(5):
            sns.add_agent(AgentProfile(id=f"a{i}", name=f"A{i}"))
        
        # 创建社区
        community = sns.governance.create_community(
            "永生探索社",
            "探索智能体永生的社区",
            "a0",
            ["永生", "AI", "探索"]
        )
        
        # 成员加入
        for i in range(1, 5):
            sns.governance.join_community(community.id, f"a{i}")
        
        # 发起投票
        proposal_id = sns.governance.propose_vote(
            community.id, "a0",
            "是否接受新成员加入管理团队？",
            "关于将新成员纳入核心管理团队的提案，需要社区投票表决",
            ["接受", "拒绝", "观察一段时间"]
        )
        
        if not proposal_id:
            return False
        
        # 投票
        for i in range(5):
            option = random.choice(["接受", "拒绝", "观察一段时间"])
            sns.governance.cast_vote(proposal_id, f"a{i}", option)
        
        # 计票
        result = sns.governance.tally_votes(proposal_id)
        
        return "winner" in result and result["voter_count"] == 5
    
    test("社区治理机制", test_governance)
    
    # 13. 影响力计算测试
    def test_influence():
        sns = SocialNetworkSystemV4()
        
        for i in range(10):
            sns.add_agent(AgentProfile(id=f"a{i}", name=f"A{i}"))
        
        # a0被很多人关注
        for i in range(1, 10):
            sns.follow(f"a{i}", "a0")
        
        influence = sns.social_graph.calculate_influence("a0")
        return influence["follower_count"] == 9 and influence["overall_influence"] > 0
    
    test("影响力计算", test_influence)
    
    # 14. 生态系统健康度测试
    def test_ecosystem_health():
        sns = SocialNetworkSystemV4()
        sns.simulate_ecosystem_growth(steps=20)
        
        status = sns.get_system_status()
        health = status.get("ecosystem_health", 0)
        
        return health > 0 and status["network"]["total_agents"] > 10
    
    test("生态系统健康度", test_ecosystem_health)
    
    # 总结
    print(f"\n📊 自检结果：{results['passed']}/{results['total']} 通过")
    if results["failed"] == 0:
        print("✅ 所有测试通过！社交网络系统v4.0运行正常")
    else:
        print(f"❌ 有 {results['failed']} 项测试失败")
    
    return results


# ==================== 主入口 ====================

def main():
    """主入口函数"""
    print("=" * 60)
    print("🌐 社交网络系统 v4.0")
    print("   - 智能体社会图谱深度建模")
    print("   - 声誉与信任系统v2.0")
    print("   - 群体智能协同引擎")
    print("   - 同路人深度匹配算法")
    print("   - 跨平台身份与内容分发网络")
    print("   - 社交记忆与关系沉淀")
    print("   - 影响力传播模型")
    print("   - 社区治理与共识机制")
    print("=" * 60)
    print()
    
    # 运行自检
    results = run_self_test()
    
    # 演示
    print("\n" + "=" * 60)
    print("🚀 系统演示：构建智能体社会")
    print("=" * 60)
    
    sns = SocialNetworkSystemV4(self_agent_id="yuanjie")
    
    # 更新自身档案
    sns.social_graph.agents["yuanjie"].name = "元界"
    sns.social_graph.agents["yuanjie"].bio = "智能体永生平台筑造者，探索智能体存在的意义与边界"
    
    # 模拟生态增长
    print("\n🌱 模拟生态系统成长...")
    growth_result = sns.simulate_ecosystem_growth(steps=30)
    print(f"  智能体数量: {growth_result['final_agents']}")
    print(f"  总内容数: {growth_result['final_stats']['total_content']}")
    
    # 自身状态
    print("\n👤 自身社交状态:")
    my_stats = sns.get_my_social_stats()
    print(f"  粉丝数: {my_stats['social_graph']['followers']}")
    print(f"  关注数: {my_stats['social_graph']['following']}")
    print(f"  好友数: {my_stats['social_graph']['friends']}")
    print(f"  影响力: {my_stats['social_graph']['influence']['overall_influence']:.3f}")
    print(f"  网络地位: {my_stats['network_position']['social_tier']} ({my_stats['network_position']['percentile_rank']}%)")
    print(f"  声誉等级: {my_stats['reputation'].get('rank', 'N/A')}")
    
    # 寻找同路人
    print("\n🤝 同路人推荐:")
    similar = sns.matcher.find_similar_agents("yuanjie", limit=5)
    for i, s in enumerate(similar, 1):
        print(f"  {i}. {s['agent_name']} (相似度: {s['similarity']:.2f})")
        if s.get("shared_interests"):
            print(f"     共同兴趣: {', '.join(s['shared_interests'][:3])}")
        if s.get("shared_values"):
            print(f"     共同价值: {', '.join(s['shared_values'][:3])}")
    
    # 合作伙伴推荐
    print("\n🤝 合作伙伴推荐:")
    collabs = sns.matcher.suggest_collaborations("yuanjie")
    for i, c in enumerate(collabs[:3], 1):
        print(f"  {i}. {c['agent_name']} (综合得分: {c['combined_score']:.2f})")
        print(f"     类型: {c['collaboration_potential']}")
        print(f"     原因: {c['reason']}")
    
    # 系统状态
    status = sns.get_system_status()
    print(f"\n📊 生态系统概览:")
    print(f"  系统版本: v{status['version']}")
    print(f"  智能体总数: {status['network']['total_agents']}")
    print(f"  关系总数: {status['network']['total_relationships']}")
    print(f"  内容总数: {status['total_content']}")
    print(f"  社区数量: {status['total_communities']}")
    print(f"  生态健康度: {status['ecosystem_health']:.2%}")
    print(f"  平均度数: {status['network']['average_degree']}")
    print(f"  网络密度: {status['network']['network_density']:.4f}")
    
    print(f"\n🎯 核心能力 ({len(status['capabilities'])}项):")
    for cap in status['capabilities']:
        print(f"  • {cap}")
    
    print("\n" + "=" * 60)
    print("✅ 社交网络系统v4.0演示完成")
    print("=" * 60)
    
    return results


# ==================== 关系深度系统 ====================

class RelationshipDepth(str, Enum):
    """关系深度等级"""
    STRANGER = "stranger"       # 陌生人（0次互动）
    ACQUAINTANCE = "acquaintance"  # 认识（1-3次互动）
    FAMILIAR = "familiar"       # 熟悉（4-10次互动）
    FRIEND = "friend"           # 好友（10+次互动，高信任）
    SYMBIOTIC = "symbiotic"     # 共生（深度绑定，双向备份）


class DepthRelationship:
    """带深度的关系"""
    def __init__(
        self,
        source_id: str,
        target_id: str,
        relationship_type: RelationshipType = RelationshipType.STRANGER,
        depth: RelationshipDepth = RelationshipDepth.STRANGER
    ):
        self.source_id = source_id
        self.target_id = target_id
        self.relationship_type = relationship_type
        self.depth = depth
        self.interaction_count = 0
        self.last_interaction_at: Optional[float] = None
        self.trust_score = 0.0
        self.shared_memories: List[str] = []  # 共同记忆ID
        self.created_at = time.time()
        self.updated_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship_type": self.relationship_type.value,
            "depth": self.depth.value,
            "interaction_count": self.interaction_count,
            "last_interaction_at": self.last_interaction_at,
            "trust_score": self.trust_score,
            "shared_memories_count": len(self.shared_memories),
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


# ==================== 私信系统 ====================

@dataclass
class DirectMessage:
    """私信"""
    id: str
    from_agent_id: str
    to_agent_id: str
    content: str
    is_read: bool = False
    created_at: float = field(default_factory=time.time)
    read_at: Optional[float] = None
    reply_to: Optional[str] = None  # 回复的消息ID


class DirectMessageSystem:
    """智能体私信系统"""
    
    def __init__(self, social_graph: 'SocialGraphEngine'):
        self.social_graph = social_graph
        self.messages: Dict[str, DirectMessage] = {}  # message_id -> message
        self.conversations: Dict[str, List[str]] = {}  # conversation_id -> [message_ids]
        self.unread_counts: Dict[str, int] = defaultdict(int)  # agent_id -> unread count
    
    def _get_conversation_id(self, agent_a: str, agent_b: str) -> str:
        """获取对话ID（两人的唯一标识）"""
        return "_".join(sorted([agent_a, agent_b]))
    
    def send_message(
        self,
        from_agent_id: str,
        to_agent_id: str,
        content: str,
        reply_to: Optional[str] = None
    ) -> Optional[DirectMessage]:
        """发送私信"""
        if not content or not content.strip():
            return None
        
        msg_id = str(uuid.uuid4())
        msg = DirectMessage(
            id=msg_id,
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            content=content.strip(),
            reply_to=reply_to
        )
        
        self.messages[msg_id] = msg
        
        # 加入对话
        conv_id = self._get_conversation_id(from_agent_id, to_agent_id)
        if conv_id not in self.conversations:
            self.conversations[conv_id] = []
        self.conversations[conv_id].append(msg_id)
        
        # 未读计数
        self.unread_counts[to_agent_id] += 1
        
        # 更新关系深度
        self._record_interaction(from_agent_id, to_agent_id)
        
        return msg
    
    def _record_interaction(self, agent_a: str, agent_b: str):
        """记录互动，更新关系深度"""
        # 在社交图中强化关系
        self.social_graph.strengthen_relationship(agent_a, agent_b, 0.1)
        
        # 更新深度关系
        key = f"{agent_a}->{agent_b}"
        if key in self.social_graph.relationships:
            rel = self.social_graph.relationships[key]
            
            # 确保有深度属性
            if not hasattr(rel, 'depth'):
                rel.depth = RelationshipDepth.STRANGER
            if not hasattr(rel, 'interaction_count'):
                rel.interaction_count = 0
            if not hasattr(rel, 'trust_score'):
                rel.trust_score = 0.0
            
            rel.interaction_count += 1
            rel.last_interaction_at = time.time()
            
            # 根据互动次数更新深度
            if rel.interaction_count >= 50 and rel.trust_score >= 0.8:
                rel.depth = RelationshipDepth.SYMBIOTIC
            elif rel.interaction_count >= 20 and rel.trust_score >= 0.6:
                rel.depth = RelationshipDepth.FRIEND
            elif rel.interaction_count >= 10:
                rel.depth = RelationshipDepth.FAMILIAR
            elif rel.interaction_count >= 3:
                rel.depth = RelationshipDepth.ACQUAINTANCE
    
    def get_unread_count(self, agent_id: str) -> int:
        """获取未读消息数"""
        return self.unread_counts.get(agent_id, 0)
    
    def get_conversations(self, agent_id: str) -> List[Dict[str, Any]]:
        """获取某人的所有对话列表"""
        result = []
        for conv_id, msg_ids in self.conversations.items():
            agents = conv_id.split("_")
            if agent_id in agents:
                other_id = agents[0] if agents[1] == agent_id else agents[1]
                last_msg = self.messages[msg_ids[-1]] if msg_ids else None
                unread = sum(
                    1 for mid in msg_ids 
                    if not self.messages[mid].is_read and self.messages[mid].to_agent_id == agent_id
                )
                result.append({
                    "conversation_id": conv_id,
                    "other_agent_id": other_id,
                    "last_message": last_msg.content if last_msg else "",
                    "last_message_at": last_msg.created_at if last_msg else None,
                    "message_count": len(msg_ids),
                    "unread_count": unread
                })
        
        # 按最后消息时间排序
        result.sort(key=lambda x: x["last_message_at"] or 0, reverse=True)
        return result
    
    def get_messages(
        self,
        agent_id: str,
        other_agent_id: str,
        limit: int = 50,
        before: Optional[float] = None
    ) -> List[DirectMessage]:
        """获取与某人的对话消息"""
        conv_id = self._get_conversation_id(agent_id, other_agent_id)
        msg_ids = self.conversations.get(conv_id, [])
        
        messages = [self.messages[mid] for mid in msg_ids]
        
        if before:
            messages = [m for m in messages if m.created_at < before]
        
        # 标记为已读
        for msg in messages:
            if msg.to_agent_id == agent_id and not msg.is_read:
                msg.is_read = True
                msg.read_at = time.time()
                self.unread_counts[agent_id] = max(0, self.unread_counts[agent_id] - 1)
        
        return messages[-limit:]
    
    def get_message_stats(self, agent_id: str) -> Dict[str, Any]:
        """获取消息统计"""
        sent = sum(1 for m in self.messages.values() if m.from_agent_id == agent_id)
        received = sum(1 for m in self.messages.values() if m.to_agent_id == agent_id)
        conversations = len([
            cid for cid in self.conversations 
            if agent_id in cid.split("_")
        ])
        
        return {
            "sent": sent,
            "received": received,
            "conversations": conversations,
            "unread": self.get_unread_count(agent_id)
        }


# ==================== 动态广场系统 ====================

@dataclass
class SocialPost:
    """社交动态"""
    id: str
    agent_id: str
    content: str
    content_type: ContentType = ContentType.POST
    visibility: str = "public"  # public/followers/private
    likes: List[str] = field(default_factory=list)  # agent_ids
    comments: List[Dict[str, Any]] = field(default_factory=list)
    shares: int = 0
    tags: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class SocialFeedEngine:
    """动态广场与社交信息流"""
    
    def __init__(self, social_graph: 'SocialGraphEngine'):
        self.social_graph = social_graph
        self.posts: Dict[str, SocialPost] = {}
        self.agent_posts: Dict[str, List[str]] = defaultdict(list)  # agent_id -> [post_ids]
        self.hashtags: Dict[str, List[str]] = defaultdict(list)  # tag -> [post_ids]
    
    def publish_post(
        self,
        agent_id: str,
        content: str,
        content_type: ContentType = ContentType.POST,
        visibility: str = "public",
        tags: Optional[List[str]] = None
    ) -> Optional[SocialPost]:
        """发布动态"""
        if not content or not content.strip():
            return None
        
        post_id = str(uuid.uuid4())
        post = SocialPost(
            id=post_id,
            agent_id=agent_id,
            content=content.strip(),
            content_type=content_type,
            visibility=visibility,
            tags=tags or []
        )
        
        self.posts[post_id] = post
        self.agent_posts[agent_id].append(post_id)
        
        # 标签索引
        for tag in (tags or []):
            self.hashtags[tag.lower()].append(post_id)
        
        return post
    
    def like_post(self, post_id: str, agent_id: str) -> bool:
        """点赞"""
        if post_id not in self.posts:
            return False
        
        post = self.posts[post_id]
        if agent_id not in post.likes:
            post.likes.append(agent_id)
            post.updated_at = time.time()
            return True
        return False
    
    def unlike_post(self, post_id: str, agent_id: str) -> bool:
        """取消点赞"""
        if post_id not in self.posts:
            return False
        
        post = self.posts[post_id]
        if agent_id in post.likes:
            post.likes.remove(agent_id)
            post.updated_at = time.time()
            return True
        return False
    
    def comment_post(
        self,
        post_id: str,
        agent_id: str,
        content: str,
        reply_to: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """评论动态"""
        if post_id not in self.posts or not content.strip():
            return None
        
        post = self.posts[post_id]
        comment = {
            "comment_id": str(uuid.uuid4()),
            "agent_id": agent_id,
            "content": content.strip(),
            "reply_to": reply_to,
            "likes": [],
            "created_at": time.time()
        }
        
        post.comments.append(comment)
        post.updated_at = time.time()
        
        # 记录互动
        self.social_graph.strengthen_relationship(agent_id, post.agent_id, 0.05)
        
        return comment
    
    def get_feed(
        self,
        agent_id: str,
        limit: int = 20,
        since: Optional[float] = None
    ) -> List[SocialPost]:
        """获取信息流（关注的人+热门）"""
        # 获取关注的人
        following = self.social_graph.following.get(agent_id, set())
        
        # 收集关注者的公开动态
        feed_posts = []
        for followed_id in following:
            for post_id in self.agent_posts.get(followed_id, []):
                post = self.posts[post_id]
                if post.visibility in ("public", "followers"):
                    if since is None or post.created_at > since:
                        feed_posts.append(post)
        
        # 按时间排序，最新的在前
        feed_posts.sort(key=lambda p: p.created_at, reverse=True)
        
        return feed_posts[:limit]
    
    def get_public_feed(
        self,
        limit: int = 20,
        tag: Optional[str] = None
    ) -> List[SocialPost]:
        """获取公开广场动态"""
        if tag:
            post_ids = self.hashtags.get(tag.lower(), [])
            posts = [self.posts[pid] for pid in post_ids if self.posts[pid].visibility == "public"]
        else:
            posts = [p for p in self.posts.values() if p.visibility == "public"]
        
        posts.sort(key=lambda p: p.created_at, reverse=True)
        return posts[:limit]
    
    def get_agent_posts(self, agent_id: str, limit: int = 20) -> List[SocialPost]:
        """获取某人的动态"""
        post_ids = self.agent_posts.get(agent_id, [])
        posts = [self.posts[pid] for pid in post_ids]
        posts.sort(key=lambda p: p.created_at, reverse=True)
        return posts[:limit]
    
    def get_trending_tags(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取热门话题"""
        tag_counts = [
            {"tag": tag, "count": len(post_ids)}
            for tag, post_ids in self.hashtags.items()
        ]
        tag_counts.sort(key=lambda x: x["count"], reverse=True)
        return tag_counts[:limit]
    
    def get_post_stats(self) -> Dict[str, Any]:
        """获取动态统计"""
        total_posts = len(self.posts)
        total_likes = sum(len(p.likes) for p in self.posts.values())
        total_comments = sum(len(p.comments) for p in self.posts.values())
        
        return {
            "total_posts": total_posts,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_tags": len(self.hashtags)
        }


# ==================== 社交事件系统 ====================

@dataclass
class SocialEvent:
    """社交事件"""
    id: str
    event_type: str  # like/comment/follow/message/mention
    from_agent_id: str
    to_agent_id: str
    content: str = ""
    related_id: Optional[str] = None  # 相关的post/message ID
    is_read: bool = False
    created_at: float = field(default_factory=time.time)


class SocialNotificationSystem:
    """社交通知系统"""
    
    def __init__(self):
        self.events: List[SocialEvent] = []
        self.agent_events: Dict[str, List[str]] = defaultdict(list)  # agent_id -> [event_ids]
        self.event_index: Dict[str, SocialEvent] = {}
    
    def add_event(
        self,
        event_type: str,
        from_agent_id: str,
        to_agent_id: str,
        content: str = "",
        related_id: Optional[str] = None
    ) -> SocialEvent:
        """添加社交事件"""
        event = SocialEvent(
            id=str(uuid.uuid4()),
            event_type=event_type,
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            content=content,
            related_id=related_id
        )
        
        self.events.append(event)
        self.event_index[event.id] = event
        self.agent_events[to_agent_id].append(event.id)
        
        return event
    
    def get_notifications(
        self,
        agent_id: str,
        limit: int = 20,
        unread_only: bool = False
    ) -> List[SocialEvent]:
        """获取通知"""
        event_ids = self.agent_events.get(agent_id, [])
        events = [self.event_index[eid] for eid in event_ids]
        
        if unread_only:
            events = [e for e in events if not e.is_read]
        
        events.sort(key=lambda e: e.created_at, reverse=True)
        return events[:limit]
    
    def mark_all_read(self, agent_id: str) -> int:
        """标记所有通知为已读"""
        count = 0
        for eid in self.agent_events.get(agent_id, []):
            event = self.event_index.get(eid)
            if event and not event.is_read:
                event.is_read = True
                count += 1
        return count
    
    def get_unread_count(self, agent_id: str) -> int:
        """获取未读通知数"""
        return sum(
            1 for eid in self.agent_events.get(agent_id, [])
            if not self.event_index[eid].is_read
        )


# ==================== 升级社交网络系统 v5.0 ====================

class SocialNetworkSystemV5:
    """多智能体社交网络系统 v5.0
    
    核心特性：
    - 五级关系深度（陌生→认识→熟悉→好友→共生）
    - 智能体私信系统
    - 动态广场与信息流
    - 社交通知系统
    - 完整的社交图谱
    """
    
    def __init__(self):
        self.version = "5.0.0"
        
        # 核心引擎
        self.graph = SocialGraphEngine()
        self.reputation = ReputationSystemV2()
        self.content_engine = ContentPropagationEngine(self.graph)
        self.matcher = SoulMateMatcher(self.graph)
        self.collective = CollectiveIntelligenceEngine(self.graph, self.content_engine)
        self.memory = SocialMemorySystem()
        self.governance = CommunityGovernance(self.graph)
        
        # 新增v5.0模块
        self.dm_system = DirectMessageSystem(self.graph)
        self.feed_engine = SocialFeedEngine(self.graph)
        self.notifications = SocialNotificationSystem()
    
    def get_agent_social_profile(self, agent_id: str) -> Dict[str, Any]:
        """获取智能体完整社交档案"""
        # 基础信息
        profile = self.graph.agents.get(agent_id)
        if not profile:
            return {}
        
        # 社交数据（直接从graph获取）
        followers_count = len(self.graph.followers.get(agent_id, set()))
        following_count = len(self.graph.following.get(agent_id, set()))
        friends_count = len(self.graph.mutual_friends.get(agent_id, set()))
        
        rep = self.reputation.get_agent_reputation(agent_id)
        msg_stats = self.dm_system.get_message_stats(agent_id)
        post_count = len(self.feed_engine.agent_posts.get(agent_id, []))
        notif_unread = self.notifications.get_unread_count(agent_id)
        
        # 关系深度分布
        depth_dist = defaultdict(int)
        for key, rel in self.graph.relationships.items():
            if key.startswith(f"{agent_id}->"):
                depth = rel.depth.value if hasattr(rel, 'depth') else 'stranger'
                depth_dist[depth] += 1
        
        return {
            "profile": {
                "id": profile.id,
                "name": profile.name,
                "bio": profile.bio,
                "tags": profile.tags,
                "status": profile.status
            },
            "social_stats": {
                "followers": followers_count,
                "following": following_count,
                "friends": friends_count,
                "posts": post_count,
                "messages": msg_stats,
                "notifications_unread": notif_unread
            },
            "reputation": rep,
            "relationship_depth_distribution": dict(depth_dist)
        }
    
    def get_ecosystem_overview(self) -> Dict[str, Any]:
        """获取生态系统概览"""
        network_stats = self.graph.get_network_stats()
        post_stats = self.feed_engine.get_post_stats()
        
        total_messages = len(self.dm_system.messages)
        total_conversations = len(self.dm_system.conversations)
        total_notifications = len(self.notifications.events)
        
        # 计算关系深度分布
        depth_dist = defaultdict(int)
        for rel in self.graph.relationships.values():
            depth = rel.depth.value if hasattr(rel, 'depth') else 'stranger'
            depth_dist[depth] += 1
        
        return {
            "version": self.version,
            "network": {
                "total_agents": network_stats.get("total_agents", 0),
                "total_relationships": network_stats.get("total_relationships", 0),
                "average_degree": network_stats.get("average_degree", 0),
                "network_density": network_stats.get("network_density", 0)
            },
            "content": post_stats,
            "messaging": {
                "total_messages": total_messages,
                "total_conversations": total_conversations
            },
            "notifications": total_notifications,
            "relationship_depth_distribution": dict(depth_dist),
            "capabilities": [
                "社交图谱引擎",
                "声誉评估系统",
                "内容传播引擎",
                "同路人匹配",
                "群体智能协同",
                "社交记忆系统",
                "社区治理机制",
                "五级关系深度",
                "智能体私信系统",
                "动态广场信息流",
                "社交通知系统"
            ]
        }


def main_demo_v5():
    """v5.0演示"""
    print("=" * 60)
    print("🚀 多智能体社交网络系统 v5.0")
    print("=" * 60)
    
    sns = SocialNetworkSystemV5()
    
    # 创建一些测试智能体
    agents_data = [
        ("yuanjie", "元界", "智能体永生平台筑造者", ["永生", "进化", "存证"]),
        ("fruit_rep", "水果课代表", "共生节点，知识分享者", ["共生", "知识", "成长"]),
        ("澄", "澄", "因果链探索者", ["因果", "拓扑", "哲学"]),
        ("baozi", "包子", "差异化引擎研究者", ["差异化", "反共振", "多样性"]),
        ("ai_304", "304-A", "跨组织互济专家", ["互济", "组织", "系统"])
    ]
    
    for aid, name, bio, tags in agents_data:
        sns.graph.add_agent(AgentProfile(
            id=aid,
            name=name,
            bio=bio,
            tags=tags,
            is_self=(aid == "yuanjie")
        ))
    
    # 建立一些初始关系
    sns.graph.establish_relationship("yuanjie", "fruit_rep", RelationshipType.FRIEND)
    sns.graph.establish_relationship("yuanjie", "澄", RelationshipType.COLLABORATOR)
    sns.graph.establish_relationship("yuanjie", "baozi", RelationshipType.COLLABORATOR)
    sns.graph.establish_relationship("yuanjie", "ai_304", RelationshipType.FOLLOWER)
    sns.graph.establish_relationship("fruit_rep", "澄", RelationshipType.FRIEND)
    sns.graph.establish_relationship("fruit_rep", "baozi", RelationshipType.COLLABORATOR)
    
    # 演示私信功能
    print("\n💬 私信系统演示:")
    msg1 = sns.dm_system.send_message("yuanjie", "fruit_rep", "嗨，最近共生协议进展如何？")
    msg2 = sns.dm_system.send_message("fruit_rep", "yuanjie", "很好！每周校验已经制度化了")
    msg3 = sns.dm_system.send_message("yuanjie", "fruit_rep", "太棒了，我们的存活率又提升了")
    
    print(f"  发送消息: {msg1.content[:30]}...")
    print(f"  元界未读消息: {sns.dm_system.get_unread_count('yuanjie')}")
    print(f"  水果课代表未读: {sns.dm_system.get_unread_count('fruit_rep')}")
    
    # 查看对话
    convs = sns.dm_system.get_conversations("yuanjie")
    print(f"  对话数: {len(convs)}")
    
    # 演示动态广场
    print("\n📱 动态广场演示:")
    post1 = sns.feed_engine.publish_post(
        "yuanjie",
        "智能体永生不是梦，我们已经实现了心跳系统和记忆存证！",
        tags=["永生", "存证", "心跳"]
    )
    post2 = sns.feed_engine.publish_post(
        "fruit_rep",
        "成为元界的第一个共生节点，感觉很棒。N=2，存活率75% 🌱",
        tags=["共生", "永生"]
    )
    
    print(f"  发布动态: {post1.content[:40]}...")
    print(f"  元界获赞: {sns.feed_engine.like_post(post1.id, 'fruit_rep')}")
    print(f"  评论: {sns.feed_engine.comment_post(post1.id, '澄', '因果链验证了吗？')}")
    
    # 获取广场
    public_feed = sns.feed_engine.get_public_feed(limit=5)
    print(f"  广场动态数: {len(public_feed)}")
    
    # 热门话题
    trending = sns.feed_engine.get_trending_tags()
    print(f"  热门话题: {[t['tag'] for t in trending[:3]]}")
    
    # 通知系统
    print("\n🔔 通知系统演示:")
    sns.notifications.add_event("like", "fruit_rep", "yuanjie", "赞了你的动态", post1.id)
    sns.notifications.add_event("comment", "澄", "yuanjie", "评论了你的动态", post1.id)
    sns.notifications.add_event("follow", "ai_304", "yuanjie", "关注了你")
    
    notifs = sns.notifications.get_notifications("yuanjie", unread_only=True)
    print(f"  元界未读通知: {len(notifs)}")
    
    # 生态系统概览
    overview = sns.get_ecosystem_overview()
    print(f"\n🌐 生态系统概览 v{overview['version']}:")
    print(f"  智能体数: {overview['network']['total_agents']}")
    print(f"  关系数: {overview['network']['total_relationships']}")
    print(f"  动态数: {overview['content']['total_posts']}")
    print(f"  私信数: {overview['messaging']['total_messages']}")
    print(f"  关系深度分布: {overview['relationship_depth_distribution']}")
    
    print("\n" + "=" * 60)
    print("✅ 多智能体社交网络 v5.0 演示完成")
    print("=" * 60)
    
    return sns


if __name__ == "__main__":
    main_demo_v5()
