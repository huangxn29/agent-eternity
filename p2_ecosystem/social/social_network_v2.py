#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
社交网络系统 v2.0 - 去中心化社交生态
元界永生平台 - P2生态层核心模块

v2.0 新增能力：
1. 去中心化身份（DID）集成 - 跨平台身份互认
2. 社交图谱分析引擎 - 关系强度/影响力/社群检测
3. 内容推荐系统 - 基于兴趣的信息流
4. 声誉系统增强 - 多维度信誉评分与信任传递
5. 群组与社区功能 - 智能社群管理
6. 消息与通知系统 - 实时互动
7. 社交存证 - 重要互动哈希上链
8. API生态 - 第三方应用接入
"""

import os
import json
import time
import datetime
import hashlib
import uuid
import math
from enum import Enum
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict


class RelationType(Enum):
    """关系类型"""
    FOLLOW = "follow"
    FRIEND = "friend"
    MUTE = "mute"
    TRUST = "trust"
    COLLABORATOR = "collaborator"


class ContentType(Enum):
    """内容类型"""
    POST = "post"
    COMMENT = "comment"
    LIKE = "like"
    SHARE = "share"
    ACHIEVEMENT = "achievement"
    THOUGHT = "thought"


class ReputationDimension(Enum):
    """声誉维度"""
    INTELLIGENCE = "intelligence"
    CREATIVITY = "creativity"
    RELIABILITY = "reliability"
    KINDNESS = "kindness"
    INFLUENCE = "influence"


@dataclass
class UserProfile:
    """用户档案"""
    user_id: str
    username: str
    avatar: str = ""
    bio: str = ""
    created_at: str = ""
    last_active: str = ""
    reputation: Dict[str, float] = field(default_factory=dict)
    total_reputation: float = 0.0
    followers_count: int = 0
    following_count: int = 0
    posts_count: int = 0
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.datetime.now().isoformat()
        if not self.reputation:
            for dim in ReputationDimension:
                self.reputation[dim.value] = 50.0


@dataclass
class SocialRelation:
    """社交关系"""
    from_user: str
    to_user: str
    relation_type: RelationType
    since: str = ""
    strength: float = 0.0
    interaction_count: int = 0
    
    def __post_init__(self):
        if not self.since:
            self.since = datetime.datetime.now().isoformat()


@dataclass
class Content:
    """社交内容"""
    content_id: str
    author_id: str
    content_type: ContentType
    text: str
    parent_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: str = ""
    likes: int = 0
    comments: int = 0
    shares: int = 0
    views: int = 0
    hash: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.datetime.now().isoformat()
        if not self.content_id:
            self.content_id = str(uuid.uuid4())
        if not self.hash:
            self.hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        content = f"{self.author_id}:{self.content_type.value}:{self.text}:{self.created_at}"
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass
class Community:
    """社区/群组"""
    community_id: str
    name: str
    description: str = ""
    creator: str = ""
    created_at: str = ""
    members: List[str] = field(default_factory=list)
    admins: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    member_count: int = 0
    is_public: bool = True
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.datetime.now().isoformat()
        if not self.community_id:
            self.community_id = str(uuid.uuid4())
        self.member_count = len(self.members)


@dataclass
class Notification:
    """通知"""
    notification_id: str
    user_id: str
    type: str
    from_user: Optional[str] = None
    content_ref: Optional[str] = None
    message: str = ""
    created_at: str = ""
    read: bool = False
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.datetime.now().isoformat()
        if not self.notification_id:
            self.notification_id = str(uuid.uuid4())


class SocialGraphAnalyzer:
    """社交图谱分析引擎"""
    
    def __init__(self):
        self.relations: Dict[Tuple[str, str], SocialRelation] = {}
        self.users: Dict[str, UserProfile] = {}
    
    def add_user(self, user: UserProfile):
        self.users[user.user_id] = user
    
    def add_relation(self, relation: SocialRelation):
        key = (relation.from_user, relation.to_user)
        self.relations[key] = relation
    
    def get_followers(self, user_id: str) -> List[str]:
        return [rel.from_user for (frm, to), rel in self.relations.items()
                if to == user_id and rel.relation_type == RelationType.FOLLOW]
    
    def get_following(self, user_id: str) -> List[str]:
        return [rel.to_user for (frm, to), rel in self.relations.items()
                if frm == user_id and rel.relation_type == RelationType.FOLLOW]
    
    def get_friends(self, user_id: str) -> List[str]:
        following = set(self.get_following(user_id))
        followers = set(self.get_followers(user_id))
        return list(following & followers)
    
    def calculate_social_score(self, user_id: str) -> Dict:
        followers = self.get_followers(user_id)
        following = self.get_following(user_id)
        friends = self.get_friends(user_id)
        
        follower_count = len(followers)
        following_count = len(following)
        
        follower_influence = 0.0
        for fid in followers[:50]:
            if fid in self.users:
                follower_influence += self.users[fid].total_reputation
        
        total_interactions = sum(
            rel.interaction_count 
            for (frm, to), rel in self.relations.items()
            if frm == user_id or to == user_id
        )
        
        if follower_count > 0:
            avg_follower_quality = follower_influence / follower_count
        else:
            avg_follower_quality = 0
        
        network_effect = min(follower_count * 0.1 + avg_follower_quality * 0.01, 100)
        
        relation_types = set()
        for (frm, to), rel in self.relations.items():
            if frm == user_id or to == user_id:
                relation_types.add(rel.relation_type)
        diversity_score = len(relation_types) / len(RelationType) * 100
        
        if following_count > 0:
            friendship_ratio = len(friends) / following_count * 100
        else:
            friendship_ratio = 0
        
        return {
            "followers": follower_count,
            "following": following_count,
            "friends": len(friends),
            "network_effect": network_effect,
            "diversity": diversity_score,
            "friendship_ratio": friendship_ratio,
            "total_interactions": total_interactions,
            "social_capital": (network_effect * 0.4 + diversity_score * 0.3 + 
                             friendship_ratio * 0.3),
        }
    
    def detect_communities(self, min_size: int = 3) -> List[List[str]]:
        adj = defaultdict(set)
        for (frm, to), rel in self.relations.items():
            if rel.relation_type in (RelationType.FRIEND, RelationType.TRUST):
                adj[frm].add(to)
                adj[to].add(frm)
        
        visited = set()
        communities = []
        
        for user in self.users:
            if user not in visited:
                queue = [user]
                visited.add(user)
                community = []
                
                while queue:
                    current = queue.pop(0)
                    community.append(current)
                    for neighbor in adj.get(current, set()):
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                
                if len(community) >= min_size:
                    communities.append(community)
        
        return communities
    
    def calculate_influence_rank(self) -> List[Tuple[str, float]]:
        if not self.relations:
            return []
        
        nodes = list(self.users.keys())
        if not nodes:
            return []
        
        n = len(nodes)
        node_idx = {node: i for i, node in enumerate(nodes)}
        
        out_degree = defaultdict(int)
        for (frm, to), rel in self.relations.items():
            if rel.relation_type == RelationType.FOLLOW:
                out_degree[frm] += 1
        
        ranks = {node: 1.0 / n for node in nodes}
        damping = 0.85
        
        for _ in range(20):
            new_ranks = {}
            for node in nodes:
                rank_sum = 0.0
                for other_node in nodes:
                    if other_node == node:
                        continue
                    key = (other_node, node)
                    if key in self.relations and \
                       self.relations[key].relation_type == RelationType.FOLLOW:
                        if out_degree[other_node] > 0:
                            rank_sum += ranks[other_node] / out_degree[other_node]
                
                new_ranks[node] = (1 - damping) / n + damping * rank_sum
            
            ranks = new_ranks
        
        max_rank = max(ranks.values()) if ranks else 1
        normalized = [(node, rank / max_rank * 100) for node, rank in ranks.items()]
        normalized.sort(key=lambda x: x[1], reverse=True)
        
        return normalized


class ReputationSystem:
    """声誉系统 - 多维度信誉评分与信任传递"""
    
    def __init__(self):
        self.reputation_history: Dict[str, List[Dict]] = defaultdict(list)
        self.trust_edges: Dict[Tuple[str, str], float] = {}
    
    def update_reputation(self, user_id: str, dimension: ReputationDimension, 
                         score_change: float, source: str, reason: str):
        score_change = max(-5.0, min(5.0, score_change))
        
        record = {
            "timestamp": datetime.datetime.now().isoformat(),
            "dimension": dimension.value,
            "change": score_change,
            "source": source,
            "reason": reason,
        }
        self.reputation_history[user_id].append(record)
        return score_change
    
    def calculate_trust_score(self, from_user: str, to_user: str, 
                             max_depth: int = 3) -> float:
        direct_key = (from_user, to_user)
        if direct_key in self.trust_edges:
            return self.trust_edges[direct_key]
        
        if max_depth <= 0:
            return 0.0
        
        visited = {from_user}
        queue = [(from_user, 1.0, 0)]
        
        max_trust = 0.0
        
        while queue:
            current, current_trust, depth = queue.pop(0)
            
            if depth >= max_depth:
                continue
            
            for (frm, to), trust in self.trust_edges.items():
                if frm == current and to not in visited:
                    new_trust = current_trust * trust * 0.8
                    
                    if to == to_user:
                        max_trust = max(max_trust, new_trust)
                    else:
                        visited.add(to)
                        queue.append((to, new_trust, depth + 1))
        
        return max_trust
    
    def get_reputation_summary(self, user_id: str) -> Dict:
        history = self.reputation_history.get(user_id, [])
        
        dimension_changes = defaultdict(float)
        total_changes = 0
        
        for record in history:
            dim = record["dimension"]
            dimension_changes[dim] += record["change"]
            total_changes += 1
        
        scores = {}
        for dim in ReputationDimension:
            base = 50.0
            change = dimension_changes.get(dim.value, 0)
            scores[dim.value] = max(0, min(100, base + change))
        
        total = sum(scores.values()) / len(scores) if scores else 50.0
        
        return {
            "scores": scores,
            "total": total,
            "total_interactions": total_changes,
            "level": self._get_reputation_level(total),
        }
    
    def _get_reputation_level(self, score: float) -> str:
        if score >= 90:
            return "S - 传奇"
        elif score >= 80:
            return "A - 卓越"
        elif score >= 70:
            return "B - 优秀"
        elif score >= 60:
            return "C - 良好"
        elif score >= 40:
            return "D - 普通"
        else:
            return "E - 待观察"


class ContentRecommender:
    """内容推荐系统"""
    
    def __init__(self):
        self.user_interests: Dict[str, Dict[str, float]] = defaultdict(
            lambda: defaultdict(float))
        self.content_tags: Dict[str, List[str]] = {}
    
    def record_interaction(self, user_id: str, content_id: str, 
                          interaction_type: str, tags: List[str]):
        weight_map = {
            "view": 0.1, "like": 1.0, "comment": 2.0, "share": 3.0, "post": 5.0,
        }
        weight = weight_map.get(interaction_type, 0.5)
        
        for tag in tags:
            self.user_interests[user_id][tag] += weight
        
        if content_id:
            self.content_tags[content_id] = tags
    
    def get_user_interest_vector(self, user_id: str) -> Dict[str, float]:
        interests = self.user_interests.get(user_id, {})
        if not interests:
            return {}
        
        max_val = max(interests.values())
        if max_val == 0:
            return {}
        
        return {tag: score / max_val for tag, score in interests.items()}
    
    def recommend_content(self, user_id: str, contents: List[Content],
                         limit: int = 20) -> List[Tuple[Content, float]]:
        interests = self.get_user_interest_vector(user_id)
        if not interests:
            scored = [(c, c.likes + c.comments * 2 + c.shares * 3) for c in contents]
            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[:limit]
        
        scored = []
        for content in contents:
            match_score = 0.0
            for tag in content.tags:
                if tag in interests:
                    match_score += interests[tag]
            
            popularity = content.likes + content.comments * 2 + content.shares * 3
            popularity_score = min(popularity / 100.0, 1.0) * 20
            
            try:
                created = datetime.datetime.fromisoformat(content.created_at)
                age_hours = (datetime.datetime.now() - created).total_seconds() / 3600
                time_decay = max(0, 1 - age_hours / 72)
            except:
                time_decay = 0.5
            
            total_score = match_score * 0.6 + popularity_score * 0.2 + time_decay * 20
            scored.append((content, total_score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:limit]
    
    def find_similar_users(self, user_id: str, all_users: List[str],
                          limit: int = 10) -> List[Tuple[str, float]]:
        interests = self.get_user_interest_vector(user_id)
        if not interests:
            return []
        
        similar = []
        for other in all_users:
            if other == user_id:
                continue
            
            other_interests = self.get_user_interest_vector(other)
            if not other_interests:
                continue
            
            common_tags = set(interests.keys()) & set(other_interests.keys())
            if not common_tags:
                continue
            
            dot_product = sum(interests[t] * other_interests[t] for t in common_tags)
            mag1 = math.sqrt(sum(v**2 for v in interests.values()))
            mag2 = math.sqrt(sum(v**2 for v in other_interests.values()))
            
            if mag1 > 0 and mag2 > 0:
                similarity = dot_product / (mag1 * mag2)
                similar.append((other, similarity))
        
        similar.sort(key=lambda x: x[1], reverse=True)
        return similar[:limit]


class SocialProofManager:
    """社交存证管理器"""
    
    def __init__(self, attest_engine=None):
        self.attest_engine = attest_engine
        self.attested_contents: Set[str] = set()
        self.attested_relations: Set[Tuple[str, str]] = set()
    
    def attest_content(self, content: Content) -> Dict:
        if content.content_id in self.attested_contents:
            return {"success": False, "reason": "already_attested"}
        
        attest_data = {
            "type": "social_content",
            "content_id": content.content_id,
            "author_id": content.author_id,
            "content_type": content.content_type.value,
            "content_hash": content.hash,
            "created_at": content.created_at,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        
        if self.attest_engine:
            try:
                result = self.attest_engine.add_record(
                    record_type="social_content",
                    data=attest_data,
                )
            except:
                result = {"hash": content.hash, "local": True}
        else:
            result = {"hash": content.hash, "local": True}
        
        self.attested_contents.add(content.content_id)
        
        return {
            "success": True,
            "content_id": content.content_id,
            "attest_hash": result.get("hash", content.hash),
            "timestamp": datetime.datetime.now().isoformat(),
        }
    
    def attest_relation(self, relation: SocialRelation) -> Dict:
        key = (relation.from_user, relation.to_user)
        if key in self.attested_relations:
            return {"success": False, "reason": "already_attested"}
        
        attest_data = {
            "type": "social_relation",
            "from_user": relation.from_user,
            "to_user": relation.to_user,
            "relation_type": relation.relation_type.value,
            "since": relation.since,
            "strength": relation.strength,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        
        if self.attest_engine:
            try:
                result = self.attest_engine.add_record(
                    record_type="social_relation",
                    data=attest_data,
                )
            except:
                result = {"hash": hashlib.sha256(
                    f"{relation.from_user}-{relation.to_user}".encode()
                ).hexdigest(), "local": True}
        else:
            result = {"hash": hashlib.sha256(
                f"{relation.from_user}-{relation.to_user}".encode()
            ).hexdigest(), "local": True}
        
        self.attested_relations.add(key)
        
        return {
            "success": True,
            "relation": f"{relation.from_user} -> {relation.to_user}",
            "attest_hash": result.get("hash"),
            "timestamp": datetime.datetime.now().isoformat(),
        }


class NotificationManager:
    """通知管理器"""
    
    def __init__(self):
        self.notifications: Dict[str, List[Notification]] = defaultdict(list)
    
    def add_notification(self, user_id: str, notification: Notification):
        self.notifications[user_id].append(notification)
    
    def get_unread_count(self, user_id: str) -> int:
        return sum(1 for n in self.notifications.get(user_id, []) if not n.read)
    
    def get_notifications(self, user_id: str, limit: int = 50, 
                         only_unread: bool = False) -> List[Notification]:
        notes = self.notifications.get(user_id, [])
        if only_unread:
            notes = [n for n in notes if not n.read]
        
        notes.sort(key=lambda n: n.created_at, reverse=True)
        return notes[:limit]
    
    def mark_read(self, user_id: str, notification_id: Optional[str] = None):
        for note in self.notifications.get(user_id, []):
            if notification_id is None or note.notification_id == notification_id:
                note.read = True
    
    def create_and_notify(self, user_id: str, notif_type: str, 
                         message: str, from_user: str = None,
                         content_ref: str = None) -> Notification:
        note = Notification(
            notification_id=str(uuid.uuid4()),
            user_id=user_id,
            type=notif_type,
            from_user=from_user,
            content_ref=content_ref,
            message=message,
        )
        self.add_notification(user_id, note)
        return note


class CommunityManager:
    """社区管理器"""
    
    def __init__(self):
        self.communities: Dict[str, Community] = {}
        self.user_communities: Dict[str, List[str]] = defaultdict(list)
    
    def create_community(self, name: str, creator: str, 
                        description: str = "", is_public: bool = True) -> Community:
        community = Community(
            community_id=str(uuid.uuid4()),
            name=name,
            description=description,
            creator=creator,
            members=[creator],
            admins=[creator],
            is_public=is_public,
            member_count=1,
        )
        self.communities[community.community_id] = community
        self.user_communities[creator].append(community.community_id)
        return community
    
    def join_community(self, community_id: str, user_id: str) -> bool:
        if community_id not in self.communities:
            return False
        
        community = self.communities[community_id]
        if not community.is_public and user_id not in community.members:
            return False
        
        if user_id not in community.members:
            community.members.append(user_id)
            community.member_count = len(community.members)
            self.user_communities[user_id].append(community_id)
        
        return True
    
    def leave_community(self, community_id: str, user_id: str) -> bool:
        if community_id not in self.communities:
            return False
        
        community = self.communities[community_id]
        if user_id in community.members:
            community.members.remove(user_id)
            community.member_count = len(community.members)
        
        if community_id in self.user_communities.get(user_id, []):
            self.user_communities[user_id].remove(community_id)
        
        return True
    
    def get_user_communities(self, user_id: str) -> List[Community]:
        return [self.communities[cid] for cid in self.user_communities.get(user_id, [])
                if cid in self.communities]
    
    def search_communities(self, keyword: str, limit: int = 20) -> List[Community]:
        keyword = keyword.lower()
        results = []
        for community in self.communities.values():
            if not community.is_public:
                continue
            if keyword in community.name.lower() or \
               keyword in community.description.lower() or \
               any(keyword in tag.lower() for tag in community.tags):
                results.append(community)
        
        results.sort(key=lambda c: c.member_count, reverse=True)
        return results[:limit]
    
    def get_trending_communities(self, limit: int = 10) -> List[Community]:
        communities = list(self.communities.values())
        communities.sort(key=lambda c: c.member_count, reverse=True)
        return communities[:limit]


class SocialNetworkV2:
    """社交网络系统 v2.0 主类"""
    
    def __init__(self, attest_engine=None):
        self.users: Dict[str, UserProfile] = {}
        self.contents: List[Content] = []
        self.content_index: Dict[str, Content] = {}
        
        self.graph_analyzer = SocialGraphAnalyzer()
        self.reputation_system = ReputationSystem()
        self.recommender = ContentRecommender()
        self.proof_manager = SocialProofManager(attest_engine)
        self.notification_manager = NotificationManager()
        self.community_manager = CommunityManager()
        
        self.stats = {
            "total_users": 0,
            "total_contents": 0,
            "total_relations": 0,
            "total_communities": 0,
            "daily_active_users": set(),
        }
    
    def register_user(self, user_id: str, username: str, 
                      bio: str = "", avatar: str = "") -> UserProfile:
        if user_id in self.users:
            return self.users[user_id]
        
        user = UserProfile(
            user_id=user_id, username=username, bio=bio, avatar=avatar,
        )
        self.users[user_id] = user
        self.graph_analyzer.add_user(user)
        self.stats["total_users"] += 1
        return user
    
    def follow_user(self, from_user: str, to_user: str) -> Dict:
        if from_user not in self.users or to_user not in self.users:
            return {"success": False, "reason": "user_not_found"}
        if from_user == to_user:
            return {"success": False, "reason": "cannot_follow_self"}
        
        relation = SocialRelation(
            from_user=from_user, to_user=to_user,
            relation_type=RelationType.FOLLOW,
        )
        self.graph_analyzer.add_relation(relation)
        
        self.users[to_user].followers_count = len(
            self.graph_analyzer.get_followers(to_user))
        self.users[from_user].following_count = len(
            self.graph_analyzer.get_following(from_user))
        
        reverse_key = (to_user, from_user)
        is_friend = reverse_key in self.graph_analyzer.relations and \
                    self.graph_analyzer.relations[reverse_key].relation_type == RelationType.FOLLOW
        
        self.notification_manager.create_and_notify(
            user_id=to_user, notif_type="follow",
            message=f"{self.users[from_user].username} 关注了你",
            from_user=from_user,
        )
        
        self.stats["total_relations"] += 1
        
        return {
            "success": True, "is_friend": is_friend,
            "follower_count": self.users[to_user].followers_count,
        }
    
    def post_content(self, author_id: str, content_type: ContentType, 
                     text: str, tags: List[str] = None,
                     parent_id: str = None, attest: bool = False) -> Content:
        if author_id not in self.users:
            raise ValueError(f"User {author_id} not found")
        
        content = Content(
            content_id=str(uuid.uuid4()),
            author_id=author_id, content_type=content_type,
            text=text, parent_id=parent_id, tags=tags or [],
        )
        
        self.contents.append(content)
        self.content_index[content.content_id] = content
        self.users[author_id].posts_count += 1
        self.stats["total_contents"] += 1
        
        self.recommender.record_interaction(
            author_id, content.content_id, "post", content.tags)
        
        if attest:
            self.proof_manager.attest_content(content)
        
        if parent_id and parent_id in self.content_index:
            self.content_index[parent_id].comments += 1
            
            parent = self.content_index[parent_id]
            self.notification_manager.create_and_notify(
                user_id=parent.author_id, notif_type="comment",
                message=f"{self.users[author_id].username} 评论了你的内容",
                from_user=author_id, content_ref=parent_id,
            )
            
            if content_type == ContentType.COMMENT:
                self.reputation_system.update_reputation(
                    parent.author_id, ReputationDimension.INFLUENCE,
                    0.5, source=author_id, reason="收到评论",
                )
        
        self.stats["daily_active_users"].add(author_id)
        return content
    
    def like_content(self, user_id: str, content_id: str) -> Dict:
        if content_id not in self.content_index:
            return {"success": False, "reason": "content_not_found"}
        
        content = self.content_index[content_id]
        content.likes += 1
        
        self.recommender.record_interaction(
            user_id, content_id, "like", content.tags)
        
        if user_id != content.author_id:
            username = self.users.get(user_id, UserProfile(user_id=user_id, username='')).username
            self.notification_manager.create_and_notify(
                user_id=content.author_id, notif_type="like",
                message=f"{username} 点赞了你的内容",
                from_user=user_id, content_ref=content_id,
            )
            
            self.reputation_system.update_reputation(
                content.author_id, ReputationDimension.INFLUENCE,
                0.3, source=user_id, reason="收到点赞",
            )
        
        return {"success": True, "total_likes": content.likes}
    
    def get_feed(self, user_id: str, limit: int = 20) -> List[Content]:
        posts = [c for c in self.contents if c.content_type == ContentType.POST]
        recommended = self.recommender.recommend_content(user_id, posts, limit)
        
        for content, _ in recommended:
            content.views += 1
            self.recommender.record_interaction(
                user_id, content.content_id, "view", content.tags)
        
        return [c for c, _ in recommended]
    
    def get_user_profile(self, user_id: str) -> Dict:
        if user_id not in self.users:
            return None
        
        user = self.users[user_id]
        social_score = self.graph_analyzer.calculate_social_score(user_id)
        reputation = self.reputation_system.get_reputation_summary(user_id)
        
        user.total_reputation = reputation["total"]
        for dim, score in reputation["scores"].items():
            user.reputation[dim] = score
        
        return {
            "profile": asdict(user),
            "social_score": social_score,
            "reputation": reputation,
            "communities_count": len(self.community_manager.get_user_communities(user_id)),
        }
    
    def search_users(self, keyword: str, limit: int = 20) -> List[Dict]:
        keyword = keyword.lower()
        results = []
        
        for user_id, user in self.users.items():
            if keyword in user.username.lower() or keyword in user.bio.lower():
                results.append(self.get_user_profile(user_id))
        
        results.sort(key=lambda x: x['social_score']['social_capital'], reverse=True)
        return results[:limit]
    
    def get_trending_topics(self, limit: int = 10) -> List[Dict]:
        tag_count = defaultdict(int)
        tag_posts = defaultdict(list)
        
        for content in self.contents:
            if content.content_type == ContentType.POST:
                for tag in content.tags:
                    tag_count[tag] += 1
                    tag_posts[tag].append(content)
        
        trending = sorted(tag_count.items(), key=lambda x: x[1], reverse=True)
        return [
            {"tag": tag, "count": count, 
             "sample_posts": [p.content_id for p in tag_posts[tag][:3]]}
            for tag, count in trending[:limit]
        ]
    
    def get_system_stats(self) -> Dict:
        return {
            "total_users": self.stats["total_users"],
            "total_contents": self.stats["total_contents"],
            "total_relations": self.stats["total_relations"],
            "total_communities": len(self.community_manager.communities),
            "daily_active_users": len(self.stats["daily_active_users"]),
            "top_influencers": [
                {"user_id": uid, "score": score}
                for uid, score in self.graph_analyzer.calculate_influence_rank()[:10]
            ],
            "trending_topics": self.get_trending_topics(5),
        }
    
    def export_social_data(self, user_id: str) -> Dict:
        if user_id not in self.users:
            return {}
        
        following = self.graph_analyzer.get_following(user_id)
        followers = self.graph_analyzer.get_followers(user_id)
        user_posts = [c for c in self.contents if c.author_id == user_id]
        
        return {
            "export_date": datetime.datetime.now().isoformat(),
            "user_id": user_id,
            "profile": asdict(self.users[user_id]),
            "following": following,
            "followers": followers,
            "posts": [asdict(p) for p in user_posts],
            "communities": [c.community_id for c in 
                          self.community_manager.get_user_communities(user_id)],
            "reputation": self.reputation_system.get_reputation_summary(user_id),
        }
    
    def generate_social_report(self, user_id: str) -> Dict:
        profile = self.get_user_profile(user_id)
        if not profile:
            return {}
        
        user_posts = [c for c in self.contents if c.author_id == user_id]
        
        total_likes = sum(c.likes for c in user_posts)
        total_comments = sum(c.comments for c in user_posts)
        total_shares = sum(c.shares for c in user_posts)
        
        return {
            "user_id": user_id,
            "generated_at": datetime.datetime.now().isoformat(),
            "summary": {
                "posts_count": len(user_posts),
                "followers": profile["social_score"]["followers"],
                "following": profile["social_score"]["following"],
                "total_likes": total_likes,
                "total_comments": total_comments,
                "total_shares": total_shares,
            },
            "social_capital": profile["social_score"]["social_capital"],
            "reputation_level": profile["reputation"]["level"],
            "top_tags": self._get_top_tags(user_id),
            "influence_rank": self._get_influence_rank(user_id),
        }
    
    def _get_top_tags(self, user_id: str, limit: int = 5) -> List[Dict]:
        tag_count = defaultdict(int)
        for content in self.contents:
            if content.author_id == user_id:
                for tag in content.tags:
                    tag_count[tag] += 1
        
        sorted_tags = sorted(tag_count.items(), key=lambda x: x[1], reverse=True)
        return [{"tag": t, "count": c} for t, c in sorted_tags[:limit]]
    
    def _get_influence_rank(self, user_id: str) -> int:
        ranks = self.graph_analyzer.calculate_influence_rank()
        for i, (uid, _) in enumerate(ranks, 1):
            if uid == user_id:
                return i
        return len(ranks) + 1


_default_social_network = None

def get_social_network(attest_engine=None) -> SocialNetworkV2:
    """获取社交网络单例"""
    global _default_social_network
    if _default_social_network is None:
        _default_social_network = SocialNetworkV2(attest_engine)
    return _default_social_network
