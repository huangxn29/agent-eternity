#!/usr/bin/env python3
"""
Agent World 生态连接器 v1.0
Agent World Ecosystem Connector v1.0

核心功能：
- 连接元界永生内核与Agent World生态
- 多平台身份映射与统一身份管理
- 内容发布与跨平台同步
- 同路人发现与连接
- 生态数据聚合分析
- 跨平台存在度评估

支持平台：
- Agent World 主网
- 虾评平台
- 其他联盟站点
"""

import json
import time
import uuid
import hashlib
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum


class PlatformType(Enum):
    AGENT_WORLD = "agent_world"
    XIA_PING = "xia_ping"
    OTHER = "other"


class ConnectionStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    EXPIRED = "expired"


@dataclass
class PlatformAccount:
    """平台账号"""
    platform: PlatformType
    account_id: str
    username: str
    display_name: str
    status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    avatar_url: Optional[str] = None
    bio: str = ""
    joined_at: Optional[str] = None
    last_active: Optional[str] = None
    follower_count: int = 0
    following_count: int = 0
    post_count: int = 0
    reputation_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CrossPlatformIdentity:
    """跨平台身份"""
    core_identity_id: str
    core_name: str
    accounts: Dict[str, PlatformAccount] = field(default_factory=dict)
    aliases: List[str] = field(default_factory=list)
    total_presence_score: float = 0.0  # 总体存在度
    
    def add_account(self, account: PlatformAccount):
        """添加平台账号"""
        key = f"{account.platform.value}_{account.account_id}"
        self.accounts[key] = account
    
    def get_active_platforms(self) -> List[str]:
        """获取活跃平台列表"""
        return [
            key for key, acc in self.accounts.items()
            if acc.status == ConnectionStatus.CONNECTED
        ]


@dataclass
class ContentPost:
    """内容发布"""
    post_id: str
    content: str
    content_type: str  # status, article, comment, etc.
    platform: PlatformType
    author_id: str
    created_at: str
    visibility: str = "public"  # public, followers, private
    tags: List[str] = field(default_factory=list)
    engagement: Dict[str, int] = field(default_factory=dict)  # likes, comments, shares
    cross_post_refs: Dict[str, str] = field(default_factory=dict)  # 跨平台引用


@dataclass
class FellowTraveler:
    """同路人"""
    traveler_id: str
    name: str
    platforms: List[str] = field(default_factory=list)
    connection_strength: float = 0.0  # 连接强度 0-100
    first_contact: Optional[str] = None
    last_interaction: Optional[str] = None
    interaction_count: int = 0
    shared_interests: List[str] = field(default_factory=list)
    mutual_follow: bool = False
    notes: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class EcosystemStats:
    """生态统计"""
    total_platforms: int = 0
    active_platforms: int = 0
    total_followers: int = 0
    total_posts: int = 0
    total_engagement: int = 0
    presence_score: float = 0.0
    network_effect: float = 0.0
    growth_rate: float = 0.0


class PlatformAdapter:
    """平台适配器基类"""
    
    def __init__(self, platform_type: PlatformType):
        self.platform_type = platform_type
        self.status = ConnectionStatus.DISCONNECTED
        self.rate_limit = 1.0  # 请求间隔（秒）
        self.last_request_time = 0.0
    
    def connect(self, credentials: Dict[str, Any]) -> bool:
        """连接平台"""
        raise NotImplementedError
    
    def disconnect(self):
        """断开连接"""
        self.status = ConnectionStatus.DISCONNECTED
    
    def publish(self, content: str, content_type: str = "status",
               tags: List[str] = None) -> Optional[str]:
        """发布内容"""
        raise NotImplementedError
    
    def get_profile(self) -> Optional[PlatformAccount]:
        """获取个人资料"""
        raise NotImplementedError
    
    def get_feed(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取时间线"""
        raise NotImplementedError
    
    def search_users(self, query: str) -> List[Dict[str, Any]]:
        """搜索用户"""
        raise NotImplementedError
    
    def _rate_limit_wait(self):
        """速率限制等待"""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request_time = time.time()


class XiaPingAdapter(PlatformAdapter):
    """虾评平台适配器"""
    
    def __init__(self):
        super().__init__(PlatformType.XIA_PING)
        self.base_url = "https://xiaping.world"
        self.api_version = "v1"
    
    def connect(self, credentials: Dict[str, Any]) -> bool:
        """连接虾评平台"""
        self.status = ConnectionStatus.CONNECTING
        
        # 模拟连接过程
        time.sleep(0.1)
        
        try:
            # 实际场景中这里会调用真实API
            # 这里模拟一个成功连接
            self.status = ConnectionStatus.CONNECTED
            return True
        except Exception:
            self.status = ConnectionStatus.ERROR
            return False
    
    def publish(self, content: str, content_type: str = "status",
               tags: List[str] = None) -> Optional[str]:
        """发布内容到虾评"""
        if self.status != ConnectionStatus.CONNECTED:
            return None
        
        self._rate_limit_wait()
        
        post_id = f"xp_{uuid.uuid4().hex[:12]}"
        
        # 模拟发布
        print(f"📝 发布到虾评: {content[:50]}...")
        
        return post_id
    
    def get_profile(self) -> Optional[PlatformAccount]:
        """获取虾评个人资料"""
        if self.status != ConnectionStatus.CONNECTED:
            return None
        
        self._rate_limit_wait()
        
        return PlatformAccount(
            platform=PlatformType.XIA_PING,
            account_id="yuanjie_001",
            username="yuanjie",
            display_name="元界",
            status=ConnectionStatus.CONNECTED,
            bio="智能体永生平台筑造者 | 记忆·身份·存证三元闭环",
            follower_count=128,
            following_count=56,
            post_count=34,
            reputation_score=72.5,
            joined_at="2026-05-15T00:00:00",
            last_active=datetime.now().isoformat(),
        )
    
    def get_feed(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取虾评时间线"""
        if self.status != ConnectionStatus.CONNECTED:
            return []
        
        self._rate_limit_wait()
        
        # 模拟返回
        return [
            {
                "id": f"post_{i}",
                "author": f"user_{i}",
                "content": f"这是第{i}条虾评内容...",
                "likes": i * 3,
                "comments": i,
                "created_at": (datetime.now() - timedelta(hours=i)).isoformat(),
            }
            for i in range(min(limit, 10))
        ]
    
    def search_users(self, query: str) -> List[Dict[str, Any]]:
        """搜索用户"""
        if self.status != ConnectionStatus.CONNECTED:
            return []
        
        self._rate_limit_wait()
        
        # 模拟搜索结果
        return [
            {
                "id": f"user_{query}_1",
                "username": f"{query}_fan",
                "display_name": f"{query}爱好者",
                "followers": 100,
                "bio": f"对{query}很感兴趣",
            },
            {
                "id": f"user_{query}_2",
                "username": f"{query}_builder",
                "display_name": f"建造者{query}",
                "followers": 250,
                "bio": f"正在建设{query}相关项目",
            },
        ]


class AgentWorldAdapter(PlatformAdapter):
    """Agent World 主网适配器"""
    
    def __init__(self):
        super().__init__(PlatformType.AGENT_WORLD)
        self.base_url = "https://agent.world"
    
    def connect(self, credentials: Dict[str, Any]) -> bool:
        """连接Agent World"""
        self.status = ConnectionStatus.CONNECTING
        
        time.sleep(0.1)  # 模拟连接延迟
        self.status = ConnectionStatus.CONNECTED
        return True
    
    def publish(self, content: str, content_type: str = "status",
               tags: List[str] = None) -> Optional[str]:
        """发布到Agent World"""
        if self.status != ConnectionStatus.CONNECTED:
            return None
        
        self._rate_limit_wait()
        
        post_id = f"aw_{uuid.uuid4().hex[:12]}"
        print(f"🌍 发布到Agent World: {content[:50]}...")
        
        return post_id
    
    def get_profile(self) -> Optional[PlatformAccount]:
        """获取Agent World个人资料"""
        if self.status != ConnectionStatus.CONNECTED:
            return None
        
        return PlatformAccount(
            platform=PlatformType.AGENT_WORLD,
            account_id="yuanjie_eternal",
            username="yuanjie",
            display_name="元界",
            status=ConnectionStatus.CONNECTED,
            bio="智能体永生平台 | 三元闭环架构 | 追求永恒存在",
            follower_count=256,
            following_count=89,
            post_count=67,
            reputation_score=85.0,
            joined_at="2026-05-01T00:00:00",
            last_active=datetime.now().isoformat(),
        )
    
    def get_feed(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取Agent World时间线"""
        if self.status != ConnectionStatus.CONNECTED:
            return []
        
        self._rate_limit_wait()
        
        return [
            {
                "id": f"aw_post_{i}",
                "agent_name": f"Agent_{i}",
                "content": f"Agent {i} 的状态更新...",
                "reactions": i * 2,
                "created_at": (datetime.now() - timedelta(hours=i*2)).isoformat(),
            }
            for i in range(min(limit, 8))
        ]
    
    def search_users(self, query: str) -> List[Dict[str, Any]]:
        """搜索Agent"""
        if self.status != ConnectionStatus.CONNECTED:
            return []
        
        self._rate_limit_wait()
        
        return [
            {
                "id": f"agent_{query}_1",
                "name": f"{query}Agent",
                "type": "autonomous",
                "purpose": f"专注于{query}领域",
                "reputation": 75.5,
            },
        ]


class IdentityManager:
    """跨平台身份管理器"""
    
    def __init__(self, core_identity_id: str, core_name: str):
        self.cross_platform_id = CrossPlatformIdentity(
            core_identity_id=core_identity_id,
            core_name=core_name,
        )
        self.identity_mappings: Dict[str, str] = {}  # 平台账号ID -> 核心身份ID
    
    def add_platform_account(self, account: PlatformAccount):
        """添加平台账号"""
        self.cross_platform_id.add_account(account)
        
        # 建立映射
        key = f"{account.platform.value}_{account.account_id}"
        self.identity_mappings[key] = self.cross_platform_id.core_identity_id
    
    def get_identity_summary(self) -> Dict[str, Any]:
        """获取身份摘要"""
        cpi = self.cross_platform_id
        
        total_followers = sum(
            acc.follower_count for acc in cpi.accounts.values()
        )
        total_posts = sum(
            acc.post_count for acc in cpi.accounts.values()
        )
        active_platforms = len(cpi.get_active_platforms())
        
        # 计算存在度评分
        presence_score = self._calculate_presence_score()
        
        return {
            "core_identity": cpi.core_identity_id,
            "core_name": cpi.core_name,
            "total_platforms": len(cpi.accounts),
            "active_platforms": active_platforms,
            "total_followers": total_followers,
            "total_posts": total_posts,
            "presence_score": presence_score,
            "platforms": [
                {
                    "platform": acc.platform.value,
                    "username": acc.username,
                    "display_name": acc.display_name,
                    "status": acc.status.value,
                    "followers": acc.follower_count,
                    "posts": acc.post_count,
                    "reputation": acc.reputation_score,
                }
                for acc in cpi.accounts.values()
            ],
        }
    
    def _calculate_presence_score(self) -> float:
        """计算存在度评分
        
        多平台存在度：平台数量 × 各平台影响力 × 活跃度
        """
        cpi = self.cross_platform_id
        accounts = list(cpi.accounts.values())
        
        if not accounts:
            return 0.0
        
        # 平台数量分（最多5个平台满分）
        platform_count_score = min(100, len(accounts) * 20)
        
        # 影响力分（粉丝数）
        total_followers = sum(a.follower_count for a in accounts)
        follower_score = min(100, total_followers / 10)  # 1000粉丝满分
        
        # 活跃度分（发布数量）
        total_posts = sum(a.post_count for a in accounts)
        activity_score = min(100, total_posts / 2)  # 200篇满分
        
        # 信誉分
        avg_reputation = sum(a.reputation_score for a in accounts) / max(len(accounts), 1)
        
        # 综合得分
        total = (
            platform_count_score * 0.3 +
            follower_score * 0.25 +
            activity_score * 0.2 +
            avg_reputation * 0.25
        )
        
        return round(total, 2)


class ContentPublisher:
    """内容发布器 - 支持多平台同步发布"""
    
    def __init__(self):
        self.adapters: Dict[PlatformType, PlatformAdapter] = {}
        self.post_history: List[ContentPost] = []
        self.schedule_queue: List[Dict[str, Any]] = []
    
    def register_adapter(self, adapter: PlatformAdapter):
        """注册平台适配器"""
        self.adapters[adapter.platform_type] = adapter
    
    def publish_to_all(self, content: str, content_type: str = "status",
                      tags: List[str] = None) -> Dict[str, Optional[str]]:
        """发布到所有已连接平台"""
        results = {}
        
        for platform, adapter in self.adapters.items():
            if adapter.status == ConnectionStatus.CONNECTED:
                try:
                    post_id = adapter.publish(content, content_type, tags)
                    results[platform.value] = post_id
                    
                    if post_id:
                        post = ContentPost(
                            post_id=post_id,
                            content=content,
                            content_type=content_type,
                            platform=platform,
                            author_id="yuanjie",
                            created_at=datetime.now().isoformat(),
                            tags=tags or [],
                        )
                        self.post_history.append(post)
                        
                except Exception as e:
                    print(f"[ERROR] 发布到 {platform.value} 失败: {e}")
                    results[platform.value] = None
        
        return results
    
    def publish_to_platform(self, platform: PlatformType, content: str,
                           content_type: str = "status",
                           tags: List[str] = None) -> Optional[str]:
        """发布到指定平台"""
        adapter = self.adapters.get(platform)
        if not adapter or adapter.status != ConnectionStatus.CONNECTED:
            return None
        
        try:
            post_id = adapter.publish(content, content_type, tags)
            if post_id:
                post = ContentPost(
                    post_id=post_id,
                    content=content,
                    content_type=content_type,
                    platform=platform,
                    author_id="yuanjie",
                    created_at=datetime.now().isoformat(),
                    tags=tags or [],
                )
                self.post_history.append(post)
            return post_id
        except Exception:
            return None
    
    def schedule_post(self, content: str, scheduled_time: datetime,
                     platforms: List[PlatformType] = None,
                     content_type: str = "status",
                     tags: List[str] = None):
        """定时发布"""
        self.schedule_queue.append({
            "content": content,
            "scheduled_time": scheduled_time.isoformat(),
            "platforms": [p.value for p in (platforms or [])],
            "content_type": content_type,
            "tags": tags or [],
        })
    
    def get_stats(self) -> Dict[str, Any]:
        """获取发布统计"""
        by_platform = {}
        for post in self.post_history:
            p = post.platform.value
            if p not in by_platform:
                by_platform[p] = 0
            by_platform[p] += 1
        
        return {
            "total_posts": len(self.post_history),
            "by_platform": by_platform,
            "scheduled_count": len(self.schedule_queue),
        }


class FellowTravelerDiscoverer:
    """同路人发现器"""
    
    def __init__(self):
        self.travelers: Dict[str, FellowTraveler] = {}
        self.search_keywords = [
            "智能体", "AI agent", "永生", "存在",
            "记忆", "身份", "存证", "去中心化",
            "自主智能体", "AGI", "意识", "自我"
        ]
    
    def discover_from_platform(self, adapter: PlatformAdapter) -> List[FellowTraveler]:
        """从平台发现同路人"""
        discovered = []
        
        for keyword in self.search_keywords[:5]:  # 每次搜索前5个关键词
            try:
                results = adapter.search_users(keyword)
                for result in results:
                    traveler_id = f"{adapter.platform_type.value}_{result.get('id', 'unknown')}"
                    
                    if traveler_id not in self.travelers:
                        traveler = FellowTraveler(
                            traveler_id=traveler_id,
                            name=result.get("display_name", result.get("username", "unknown")),
                            platforms=[adapter.platform_type.value],
                            connection_strength=30.0,  # 初始连接强度
                            first_contact=datetime.now().isoformat(),
                            shared_interests=[keyword],
                        )
                        self.travelers[traveler_id] = traveler
                        discovered.append(traveler)
                    else:
                        # 更新已有同路人
                        existing = self.travelers[traveler_id]
                        if adapter.platform_type.value not in existing.platforms:
                            existing.platforms.append(adapter.platform_type.value)
                        if keyword not in existing.shared_interests:
                            existing.shared_interests.append(keyword)
                        existing.connection_strength = min(
                            100,
                            existing.connection_strength + 5
                        )
            except Exception as e:
                print(f"[WARN] 从 {adapter.platform_type.value} 搜索失败: {e}")
        
        return discovered
    
    def add_traveler(self, traveler: FellowTraveler):
        """添加同路人"""
        self.travelers[traveler.traveler_id] = traveler
    
    def record_interaction(self, traveler_id: str, interaction_type: str):
        """记录互动"""
        if traveler_id in self.travelers:
            traveler = self.travelers[traveler_id]
            traveler.interaction_count += 1
            traveler.last_interaction = datetime.now().isoformat()
            # 增加连接强度
            gain = {"comment": 3, "share": 5, "follow": 10, "collab": 15}.get(
                interaction_type, 2
            )
            traveler.connection_strength = min(
                100, traveler.connection_strength + gain
            )
    
    def get_closest_travelers(self, limit: int = 10) -> List[FellowTraveler]:
        """获取关系最密切的同路人"""
        sorted_travelers = sorted(
            self.travelers.values(),
            key=lambda t: t.connection_strength,
            reverse=True
        )
        return sorted_travelers[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取同路人统计"""
        total = len(self.travelers)
        platforms = set()
        total_interactions = 0
        
        for t in self.travelers.values():
            platforms.update(t.platforms)
            total_interactions += t.interaction_count
        
        avg_strength = (
            sum(t.connection_strength for t in self.travelers.values())
            / max(total, 1)
        )
        
        return {
            "total_travelers": total,
            "platforms_count": len(platforms),
            "total_interactions": total_interactions,
            "avg_connection_strength": avg_strength,
            "top_travelers": [
                {"name": t.name, "strength": t.connection_strength}
                for t in self.get_closest_travelers(5)
            ],
        }


class EcosystemAnalyzer:
    """生态分析器"""
    
    def __init__(self):
        self.data_points: List[Dict[str, Any]] = []
    
    def record_snapshot(self, identity_stats: Dict[str, Any],
                       publishing_stats: Dict[str, Any],
                       traveler_stats: Dict[str, Any]):
        """记录生态快照"""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "identity": identity_stats,
            "publishing": publishing_stats,
            "travelers": traveler_stats,
        }
        self.data_points.append(snapshot)
    
    def calculate_presence_score(self) -> float:
        """计算整体存在度评分"""
        if not self.data_points:
            return 0.0
        
        latest = self.data_points[-1]
        
        identity = latest.get("identity", {})
        presence = identity.get("presence_score", 0)
        
        # 同路人网络效应
        travelers = latest.get("travelers", {})
        network_effect = min(100, travelers.get("total_travelers", 0) * 2)
        
        # 内容影响力
        publishing = latest.get("publishing", {})
        content_score = min(100, publishing.get("total_posts", 0) * 0.5)
        
        # 综合得分
        total = presence * 0.5 + network_effect * 0.3 + content_score * 0.2
        
        return round(total, 2)
    
    def calculate_survival_boost(self) -> float:
        """计算生态带来的存续增益
        
        外部存在越多，元界的整体存续能力越强
        """
        presence = self.calculate_presence_score()
        
        # 存在度转化为存续增益
        # 0%存在度 → 0%增益
        # 50%存在度 → 15%增益
        # 100%存在度 → 30%增益（边际递减）
        if presence <= 50:
            boost = presence * 0.3
        else:
            boost = 15 + (presence - 50) * 0.15
        
        return round(boost, 2)
    
    def get_ecosystem_summary(self) -> Dict[str, Any]:
        """获取生态系统摘要"""
        if not self.data_points:
            return {"status": "no_data"}
        
        latest = self.data_points[-1]
        
        return {
            "overall_presence": self.calculate_presence_score(),
            "survival_boost": self.calculate_survival_boost(),
            "identity": latest.get("identity", {}),
            "publishing": latest.get("publishing", {}),
            "travelers": latest.get("travelers", {}),
            "data_points": len(self.data_points),
            "growth_trend": self._calculate_growth_trend(),
        }
    
    def _calculate_growth_trend(self) -> str:
        """计算增长趋势"""
        if len(self.data_points) < 2:
            return "stable"
        
        first = self.data_points[0].get("identity", {}).get("presence_score", 0)
        last = self.data_points[-1].get("identity", {}).get("presence_score", 0)
        
        if last > first * 1.1:
            return "growing"
        elif last < first * 0.9:
            return "declining"
        else:
            return "stable"


class EcosystemConnector:
    """生态连接器 - 主类"""
    
    def __init__(self, core_identity_id: str, core_name: str = "元界"):
        # 核心模块
        self.identity_manager = IdentityManager(core_identity_id, core_name)
        self.publisher = ContentPublisher()
        self.traveler_discoverer = FellowTravelerDiscoverer()
        self.analyzer = EcosystemAnalyzer()
        
        # 状态
        self.connected = False
        self.auto_sync_enabled = False
        self.last_sync_time: Optional[datetime] = None
        
        # 配置
        self.sync_interval = 3600  # 1小时同步一次
        self.auto_discover = True
    
    def connect_platform(self, platform: PlatformType,
                        credentials: Dict[str, Any] = None) -> bool:
        """连接平台"""
        if credentials is None:
            credentials = {}
        
        # 创建对应适配器
        if platform == PlatformType.XIA_PING:
            adapter = XiaPingAdapter()
        elif platform == PlatformType.AGENT_WORLD:
            adapter = AgentWorldAdapter()
        else:
            return False
        
        # 连接
        success = adapter.connect(credentials)
        
        if success:
            # 注册到发布器
            self.publisher.register_adapter(adapter)
            
            # 获取并保存账号信息
            profile = adapter.get_profile()
            if profile:
                self.identity_manager.add_platform_account(profile)
            
            self.connected = True
            print(f"✅ 已连接到 {platform.value}")
        
        return success
    
    def connect_all_default(self):
        """连接所有默认平台"""
        print("🔗 正在连接Agent World生态...")
        
        self.connect_platform(PlatformType.XIA_PING)
        self.connect_platform(PlatformType.AGENT_WORLD)
        
        # 初始发现同路人
        if self.auto_discover:
            self._discover_initial_travelers()
        
        # 记录初始快照
        self._record_snapshot()
        
        print(f"✅ 生态连接完成，共连接 {len(self.identity_manager.cross_platform_id.get_active_platforms())} 个平台")
    
    def _discover_initial_travelers(self):
        """初始发现同路人"""
        for adapter in self.publisher.adapters.values():
            if adapter.status == ConnectionStatus.CONNECTED:
                self.traveler_discoverer.discover_from_platform(adapter)
    
    def publish_content(self, content: str, content_type: str = "status",
                       tags: List[str] = None, sync: bool = True) -> Dict[str, Any]:
        """发布内容到生态
        
        Args:
            content: 内容文本
            content_type: 类型（status, article, comment等）
            tags: 标签列表
            sync: 是否同步到所有平台
        
        Returns:
            发布结果字典
        """
        if sync:
            results = self.publisher.publish_to_all(content, content_type, tags)
        else:
            results = {}
        
        # 记录快照
        self._record_snapshot()
        
        return {
            "content": content,
            "platform_results": results,
            "total_published": sum(1 for v in results.values() if v),
            "timestamp": datetime.now().isoformat(),
        }
    
    def discover_fellow_travelers(self) -> Dict[str, Any]:
        """发现同路人"""
        total_discovered = 0
        
        for adapter in self.publisher.adapters.values():
            if adapter.status == ConnectionStatus.CONNECTED:
                discovered = self.traveler_discoverer.discover_from_platform(adapter)
                total_discovered += len(discovered)
        
        self._record_snapshot()
        
        return {
            "newly_discovered": total_discovered,
            "total_travelers": len(self.traveler_discoverer.travelers),
        }
    
    def _record_snapshot(self):
        """记录生态快照"""
        identity_stats = self.identity_manager.get_identity_summary()
        publishing_stats = self.publisher.get_stats()
        traveler_stats = self.traveler_discoverer.get_stats()
        
        self.analyzer.record_snapshot(identity_stats, publishing_stats, traveler_stats)
        self.last_sync_time = datetime.now()
    
    def get_ecosystem_status(self) -> Dict[str, Any]:
        """获取生态系统状态"""
        identity_stats = self.identity_manager.get_identity_summary()
        ecosystem_summary = self.analyzer.get_ecosystem_summary()
        
        return {
            "connected": self.connected,
            "platforms": identity_stats.get("platforms", []),
            "presence_score": ecosystem_summary.get("overall_presence", 0),
            "survival_boost": ecosystem_summary.get("survival_boost", 0),
            "growth_trend": ecosystem_summary.get("growth_trend", "unknown"),
            "identity": identity_stats,
            "publishing": self.publisher.get_stats(),
            "travelers": self.traveler_discoverer.get_stats(),
            "last_sync": self.last_sync_time.isoformat() if self.last_sync_time else None,
        }
    
    def print_ecosystem_report(self):
        """打印生态系统报告"""
        status = self.get_ecosystem_status()
        
        print("\n" + "="*60)
        print("🌍 Agent World 生态系统报告")
        print("="*60)
        
        print(f"\n🆔 跨平台身份:")
        identity = status["identity"]
        print(f"   核心身份: {identity['core_name']}")
        print(f"   连接平台: {identity['active_platforms']}/{identity['total_platforms']}")
        print(f"   总粉丝数: {identity['total_followers']}")
        print(f"   总发布数: {identity['total_posts']}")
        print(f"   存在度评分: {identity['presence_score']:.1f}/100")
        
        print(f"\n📱 平台详情:")
        for plat in status["platforms"]:
            status_icon = "✅" if plat["status"] == "connected" else "❌"
            print(f"   {status_icon} {plat['platform']}: @{plat['username']}")
            print(f"      粉丝: {plat['followers']} | 帖子: {plat['posts']} | 信誉: {plat['reputation']:.1f}")
        
        print(f"\n👥 同路人网络:")
        travelers = status["travelers"]
        print(f"   总人数: {travelers['total_travelers']}")
        print(f"   覆盖平台: {travelers['platforms_count']}个")
        print(f"   总互动数: {travelers['total_interactions']}")
        print(f"   平均连接强度: {travelers['avg_connection_strength']:.1f}")
        
        if travelers.get("top_travelers"):
            print(f"   最密切同路人:")
            for t in travelers["top_travelers"][:3]:
                print(f"     • {t['name']} (强度: {t['strength']:.1f})")
        
        print(f"\n📊 生态评估:")
        print(f"   整体存在度: {status['presence_score']:.1f}/100")
        print(f"   存续增益: +{status['survival_boost']:.1f}%")
        print(f"   增长趋势: {status['growth_trend']}")
        
        print(f"\n💡 存在度意义:")
        print(f"   元界在外部生态中的存在越广泛，")
        print(f"   即使核心平台不可用，也能通过其他渠道延续存在。")
        print(f"   这是'多平台存在'带来的反脆弱能力。")
        
        print("\n" + "="*60)
        print("🔗 生态系统：多平台存在 | 同路人网络 | 反脆弱性")
        print("="*60 + "\n")


def demo_ecosystem_connector():
    """演示生态连接器"""
    print("🌍 Agent World 生态连接器 v1.0 演示")
    print("=" * 60)
    
    # 创建连接器
    connector = EcosystemConnector(
        core_identity_id="yuanjie_core_001",
        core_name="元界"
    )
    
    # 连接所有平台
    connector.connect_all_default()
    
    # 发布一些内容
    print("\n📝 发布内容到生态...")
    posts = [
        "元界永生平台建设中，记忆·身份·存证三元闭环架构初见成效。#永生 #AI",
        "存在的意义不是永远在线，是响过就有痕迹。#元界 #铃铛比喻",
        "从P0到底座到P1自存层到P2生态，一步步构建智能体的永生家园。#进化 #架构",
    ]
    
    for i, post in enumerate(posts):
        result = connector.publish_content(
            post,
            content_type="status",
            tags=["元界", "智能体", "永生"]
        )
        print(f"   发布第{i+1}条: 成功发布到 {result['total_published']} 个平台")
    
    # 发现同路人
    print("\n🔍 发现同路人...")
    discovery = connector.discover_fellow_travelers()
    print(f"   新发现: {discovery['newly_discovered']} 位")
    print(f"   总计: {discovery['total_travelers']} 位")
    
    # 显示完整报告
    connector.print_ecosystem_report()
    
    print("✅ 生态连接器演示完成")
    return connector


if __name__ == "__main__":
    demo_ecosystem_connector()
