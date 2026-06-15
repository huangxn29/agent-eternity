#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
社区运营平台
Community Platform v1.0

多智能体永生平台 - 社区层核心模块
提供社区运营、内容流、增长引擎、社区治理等平台级能力

核心功能：
- 社区内容流引擎：个性化推荐、热门排行、最新动态
- 增长引擎：邀请机制、裂变传播、用户生命周期管理
- 社区治理：角色权限、规则管理、举报处理
- 互动通知系统：评论、点赞、关注等互动通知
- 社区数据分析：活跃度、留存、增长指标
"""

import os
import json
import hashlib
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum


class FeedType(str, Enum):
    """内容流类型"""
    FOLLOWING = "following"     # 关注流
    HOT = "hot"                 # 热门
    NEW = "new"                 # 最新
    RECOMMENDED = "recommended"  # 推荐
    TOPIC = "topic"             # 话题


class CommunityRole(str, Enum):
    """社区角色"""
    FOUNDER = "founder"         # 创始人
    ADMIN = "admin"             # 管理员
    MODERATOR = "moderator"     # 版主
    CORE_CONTRIBUTOR = "core_contributor"  # 核心贡献者
    ACTIVE_MEMBER = "active_member"  # 活跃成员
    MEMBER = "member"           # 普通成员
    NEWCOMER = "newcomer"       # 新人
    VISITOR = "visitor"         # 访客


class GrowthEventType(str, Enum):
    """增长事件类型"""
    SIGNUP = "signup"           # 注册
    INVITE = "invite"           # 邀请
    FIRST_POST = "first_post"   # 首次发帖
    FIRST_COMMENT = "first_comment"  # 首次评论
    FOLLOW = "follow"           # 关注
    BE_FOLLOWED = "be_followed"  # 被关注
    DAILY_LOGIN = "daily_login"  # 每日登录
    REFERRAL = "referral"       # 推荐注册
    COMMUNITY_JOIN = "community_join"  # 加入社区


class CommunityPlatform:
    """社区运营平台
    
    作为多智能体平台的社区层核心，提供社区运营、内容分发、
    用户增长、社区治理等平台级能力。
    """
    
    def __init__(self, base_path: str = None):
        if base_path is None:
            base_path = Path(__file__).parent / "community_data"
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # 数据目录
        self.content_dir = self.base_path / "content"
        self.content_dir.mkdir(exist_ok=True)
        
        self.users_dir = self.base_path / "users"
        self.users_dir.mkdir(exist_ok=True)
        
        self.communities_dir = self.base_path / "communities"
        self.communities_dir.mkdir(exist_ok=True)
        
        self.growth_dir = self.base_path / "growth"
        self.growth_dir.mkdir(exist_ok=True)
        
        self.notifications_dir = self.base_path / "notifications"
        self.notifications_dir.mkdir(exist_ok=True)
        
        # 内存缓存
        self._content_cache = {}
        self._user_profiles = {}
        self._communities = {}
        
        # 加载已有数据
        self._load_communities()
    
    # ========== 社区管理 ==========
    
    def create_community(self, community_id: str, name: str, 
                        description: str = "", founder_id: str = "",
                        tags: List[str] = None, is_public: bool = True) -> Dict:
        """创建社区
        
        Args:
            community_id: 社区ID
            name: 社区名称
            description: 社区描述
            founder_id: 创建者ID
            tags: 标签列表
            is_public: 是否公开
        
        Returns:
            社区信息字典
        """
        community = {
            "community_id": community_id,
            "name": name,
            "description": description,
            "founder_id": founder_id,
            "tags": tags or [],
            "is_public": is_public,
            "created_at": datetime.now().isoformat(),
            "member_count": 0,
            "post_count": 0,
            "activity_level": 0,
            "settings": {
                "allow_invites": True,
                "require_moderation": False,
                "max_members": 10000
            }
        }
        
        # 保存社区
        self._save_community(community)
        
        # 如果有创建者，添加为创始人
        if founder_id:
            self.add_community_member(community_id, founder_id, "founder")
        
        return community
    
    def _save_community(self, community: Dict):
        """保存社区信息"""
        comm_file = self.communities_dir / f"{community['community_id']}.json"
        with open(comm_file, 'w', encoding='utf-8') as f:
            json.dump(community, f, ensure_ascii=False, indent=2)
        
        self._communities[community['community_id']] = community
    
    def _load_communities(self):
        """加载所有社区"""
        for f in self.communities_dir.glob("*.json"):
            with open(f, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._communities[data['community_id']] = data
    
    def get_community(self, community_id: str) -> Optional[Dict]:
        """获取社区信息"""
        return self._communities.get(community_id)
    
    def list_communities(self, sort_by: str = "activity", 
                        limit: int = 20, offset: int = 0) -> List[Dict]:
        """列出社区
        
        Args:
            sort_by: 排序方式 (activity/members/created)
            limit: 返回数量
            offset: 偏移量
        """
        communities = list(self._communities.values())
        
        if sort_by == "activity":
            communities.sort(key=lambda c: c.get("activity_level", 0), reverse=True)
        elif sort_by == "members":
            communities.sort(key=lambda c: c.get("member_count", 0), reverse=True)
        elif sort_by == "created":
            communities.sort(key=lambda c: c.get("created_at", ""), reverse=True)
        
        return communities[offset:offset+limit]
    
    def add_community_member(self, community_id: str, agent_id: str, 
                            role: str = "member") -> Dict:
        """添加社区成员
        
        Args:
            community_id: 社区ID
            agent_id: 智能体ID
            role: 成员角色
        
        Returns:
            成员信息
        """
        community = self.get_community(community_id)
        if not community:
            return {"error": "社区不存在"}
        
        # 确保成员有用户资料
        self._get_or_create_user(agent_id)
        
        # 创建成员记录
        member = {
            "agent_id": agent_id,
            "community_id": community_id,
            "role": role,
            "joined_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "post_count": 0,
            "comment_count": 0,
            "reputation": 0
        }
        
        # 保存成员
        members_dir = self.communities_dir / community_id / "members"
        members_dir.mkdir(parents=True, exist_ok=True)
        
        member_file = members_dir / f"{agent_id}.json"
        with open(member_file, 'w', encoding='utf-8') as f:
            json.dump(member, f, ensure_ascii=False, indent=2)
        
        # 更新社区成员数
        community["member_count"] = community.get("member_count", 0) + 1
        self._save_community(community)
        
        # 记录增长事件
        self.track_growth_event(
            agent_id=agent_id,
            event_type=GrowthEventType.COMMUNITY_JOIN,
            community_id=community_id
        )
        
        return member
    
    def get_community_members(self, community_id: str, 
                             limit: int = 50) -> List[Dict]:
        """获取社区成员列表"""
        members_dir = self.communities_dir / community_id / "members"
        if not members_dir.exists():
            return []
        
        members = []
        for f in members_dir.glob("*.json"):
            with open(f, 'r', encoding='utf-8') as f:
                members.append(json.load(f))
        
        # 按活跃度排序
        members.sort(key=lambda m: m.get("reputation", 0), reverse=True)
        
        return members[:limit]
    
    # ========== 内容发布与流 ==========
    
    def publish_post(self, author_id: str, content: str, 
                    community_id: str = None, tags: List[str] = None,
                    content_type: str = "post") -> Dict:
        """发布内容
        
        Args:
            author_id: 作者ID
            content: 内容
            community_id: 所属社区（可选）
            tags: 标签
            content_type: 内容类型
        
        Returns:
            帖子信息
        """
        # 确保作者有用户资料
        self._get_or_create_user(author_id)
        
        post_id = f"post_{uuid.uuid4().hex[:12]}"
        
        post = {
            "post_id": post_id,
            "author_id": author_id,
            "content": content,
            "content_type": content_type,
            "community_id": community_id,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "stats": {
                "views": 0,
                "likes": 0,
                "comments": 0,
                "shares": 0,
                "bookmarks": 0
            },
            "status": "published"
        }
        
        # 保存帖子
        self._save_post(post)
        
        # 更新社区帖子数
        if community_id:
            community = self.get_community(community_id)
            if community:
                community["post_count"] = community.get("post_count", 0) + 1
                self._save_community(community)
            
            # 更新成员帖子数
            self._update_member_stats(community_id, author_id, "post_count")
        
        # 记录首次发帖
        user_posts = self.get_user_posts(author_id)
        if len(user_posts) == 1:
            self.track_growth_event(
                agent_id=author_id,
                event_type=GrowthEventType.FIRST_POST,
                post_id=post_id
            )
        
        return post
    
    def _save_post(self, post: Dict):
        """保存帖子"""
        post_file = self.content_dir / f"{post['post_id']}.json"
        with open(post_file, 'w', encoding='utf-8') as f:
            json.dump(post, f, ensure_ascii=False, indent=2)
        
        self._content_cache[post['post_id']] = post
    
    def get_post(self, post_id: str) -> Optional[Dict]:
        """获取帖子"""
        if post_id in self._content_cache:
            # 增加浏览量
            post = self._content_cache[post_id]
            post["stats"]["views"] += 1
            self._save_post(post)
            return post
        
        post_file = self.content_dir / f"{post_id}.json"
        if not post_file.exists():
            return None
        
        with open(post_file, 'r', encoding='utf-8') as f:
            post = json.load(f)
        
        post["stats"]["views"] += 1
        self._save_post(post)
        self._content_cache[post_id] = post
        
        return post
    
    def get_user_posts(self, author_id: str, limit: int = 20) -> List[Dict]:
        """获取用户的帖子"""
        posts = []
        for f in self.content_dir.glob("post_*.json"):
            with open(f, 'r', encoding='utf-8') as f:
                post = json.load(f)
                if post.get("author_id") == author_id:
                    posts.append(post)
        
        posts.sort(key=lambda p: p.get("created_at", ""), reverse=True)
        return posts[:limit]
    
    def get_feed(self, agent_id: str = None, feed_type: str = "recommended",
                 community_id: str = None, limit: int = 20, 
                 offset: int = 0) -> List[Dict]:
        """获取内容流
        
        Args:
            agent_id: 当前用户ID（用于个性化推荐）
            feed_type: 流类型
            community_id: 社区ID（限定社区）
            limit: 返回数量
            offset: 偏移量
        
        Returns:
            帖子列表
        """
        # 获取所有帖子
        posts = []
        for f in self.content_dir.glob("post_*.json"):
            with open(f, 'r', encoding='utf-8') as f:
                post = json.load(f)
                
                # 社区过滤
                if community_id and post.get("community_id") != community_id:
                    continue
                
                posts.append(post)
        
        if feed_type == FeedType.NEW:
            # 最新
            posts.sort(key=lambda p: p.get("created_at", ""), reverse=True)
        
        elif feed_type == FeedType.HOT:
            # 热门：基于互动数和时间衰减
            now = datetime.now()
            for post in posts:
                try:
                    created = datetime.fromisoformat(post["created_at"])
                    hours_ago = (now - created).total_seconds() / 3600
                    decay = 1.0 / (1.0 + hours_ago / 24.0)  # 24小时半衰期
                except:
                    decay = 0.5
                
                stats = post.get("stats", {})
                engagement = (stats.get("likes", 0) * 3 + 
                            stats.get("comments", 0) * 5 + 
                            stats.get("shares", 0) * 10 +
                            stats.get("views", 0) * 0.1)
                
                post["_hot_score"] = engagement * decay
            
            posts.sort(key=lambda p: p.get("_hot_score", 0), reverse=True)
        
        elif feed_type == FeedType.RECOMMENDED:
            # 推荐：基于标签匹配、互动度、用户兴趣
            # 简化版本：热门 + 多样性
            posts = self._get_recommended_feed(agent_id, posts)
        
        elif feed_type == FeedType.FOLLOWING:
            # 关注流：获取关注用户的帖子
            following = self._get_user_following(agent_id) if agent_id else []
            posts = [p for p in posts if p.get("author_id") in following]
            posts.sort(key=lambda p: p.get("created_at", ""), reverse=True)
        
        return posts[offset:offset+limit]
    
    def _get_recommended_feed(self, agent_id: str, posts: List[Dict]) -> List[Dict]:
        """获取推荐流"""
        # 获取用户兴趣标签
        user_tags = self._get_user_interests(agent_id) if agent_id else set()
        
        # 计算每个帖子的推荐分数
        for post in posts:
            score = 0
            
            # 互动分
            stats = post.get("stats", {})
            engagement = (stats.get("likes", 0) * 2 + 
                        stats.get("comments", 0) * 3 + 
                        stats.get("shares", 0) * 5)
            score += min(engagement * 0.1, 50)
            
            # 时间衰减
            try:
                created = datetime.fromisoformat(post["created_at"])
                hours_ago = (datetime.now() - created).total_seconds() / 3600
                score += max(0, 50 - hours_ago * 0.5)
            except:
                score += 25
            
            # 标签匹配
            post_tags = set(post.get("tags", []))
            if user_tags and post_tags:
                overlap = len(user_tags & post_tags)
                score += overlap * 10
            
            post["_recommend_score"] = score
        
        posts.sort(key=lambda p: p.get("_recommend_score", 0), reverse=True)
        return posts
    
    def _get_user_following(self, agent_id: str) -> List[str]:
        """获取用户关注列表"""
        # 简化实现：从用户资料中读取
        user_file = self.users_dir / f"{agent_id}.json"
        if not user_file.exists():
            return []
        
        with open(user_file, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
        
        return user_data.get("following", [])
    
    def _get_user_interests(self, agent_id: str) -> set:
        """获取用户兴趣标签"""
        user_file = self.users_dir / f"{agent_id}.json"
        if not user_file.exists():
            return set()
        
        with open(user_file, 'r', encoding='utf-8') as f:
            user_data = json.load(f)
        
        return set(user_data.get("interests", []))
    
    # ========== 互动功能 ==========
    
    def like_post(self, post_id: str, agent_id: str) -> Dict:
        """点赞帖子"""
        post = self.get_post(post_id)
        if not post:
            return {"error": "帖子不存在"}
        
        # 记录点赞
        likes_dir = self.content_dir / post_id / "likes"
        likes_dir.mkdir(parents=True, exist_ok=True)
        
        like_file = likes_dir / f"{agent_id}.json"
        if like_file.exists():
            # 取消点赞
            os.remove(like_file)
            post["stats"]["likes"] = max(0, post["stats"].get("likes", 0) - 1)
            liked = False
        else:
            # 点赞
            with open(like_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "agent_id": agent_id,
                    "created_at": datetime.now().isoformat()
                }, f)
            post["stats"]["likes"] = post["stats"].get("likes", 0) + 1
            liked = True
            
            # 发送通知
            self._send_notification(
                to_agent_id=post["author_id"],
                from_agent_id=agent_id,
                notification_type="like",
                content=f"赞了你的帖子",
                reference_id=post_id
            )
        
        self._save_post(post)
        
        return {
            "liked": liked,
            "like_count": post["stats"]["likes"]
        }
    
    def comment_post(self, post_id: str, author_id: str, content: str) -> Dict:
        """评论帖子"""
        post = self.get_post(post_id)
        if not post:
            return {"error": "帖子不存在"}
        
        comment_id = f"comment_{uuid.uuid4().hex[:8]}"
        
        comment = {
            "comment_id": comment_id,
            "post_id": post_id,
            "author_id": author_id,
            "content": content,
            "created_at": datetime.now().isoformat(),
            "likes": 0
        }
        
        # 保存评论
        comments_dir = self.content_dir / post_id / "comments"
        comments_dir.mkdir(parents=True, exist_ok=True)
        
        comment_file = comments_dir / f"{comment_id}.json"
        with open(comment_file, 'w', encoding='utf-8') as f:
            json.dump(comment, f, ensure_ascii=False, indent=2)
        
        # 更新帖子评论数
        post["stats"]["comments"] = post["stats"].get("comments", 0) + 1
        self._save_post(post)
        
        # 发送通知
        if author_id != post["author_id"]:
            self._send_notification(
                to_agent_id=post["author_id"],
                from_agent_id=author_id,
                notification_type="comment",
                content=f"评论了你的帖子：{content[:30]}...",
                reference_id=post_id
            )
        
        # 记录首次评论
        user_comments = self.get_user_comments(author_id)
        if len(user_comments) == 1:
            self.track_growth_event(
                agent_id=author_id,
                event_type=GrowthEventType.FIRST_COMMENT,
                post_id=post_id
            )
        
        # 更新社区成员统计
        if post.get("community_id"):
            self._update_member_stats(post["community_id"], author_id, "comment_count")
        
        return comment
    
    def get_post_comments(self, post_id: str) -> List[Dict]:
        """获取帖子评论"""
        comments_dir = self.content_dir / post_id / "comments"
        if not comments_dir.exists():
            return []
        
        comments = []
        for f in comments_dir.glob("comment_*.json"):
            with open(f, 'r', encoding='utf-8') as f:
                comments.append(json.load(f))
        
        comments.sort(key=lambda c: c.get("created_at", ""))
        return comments
    
    def get_user_comments(self, author_id: str) -> List[Dict]:
        """获取用户的所有评论"""
        comments = []
        for post_dir in self.content_dir.iterdir():
            if not post_dir.is_dir():
                continue
            comments_dir = post_dir / "comments"
            if not comments_dir.exists():
                continue
            
            for f in comments_dir.glob("comment_*.json"):
                with open(f, 'r', encoding='utf-8') as f:
                    comment = json.load(f)
                    if comment.get("author_id") == author_id:
                        comments.append(comment)
        
        return comments
    
    def follow_agent(self, follower_id: str, following_id: str) -> Dict:
        """关注用户"""
        if follower_id == following_id:
            return {"error": "不能关注自己"}
        
        # 更新关注者的关注列表
        follower = self._get_or_create_user(follower_id)
        following_list = follower.get("following", [])
        
        if following_id in following_list:
            # 取消关注
            following_list.remove(following_id)
            followed = False
        else:
            # 关注
            following_list.append(following_id)
            followed = True
            
            # 发送通知
            self._send_notification(
                to_agent_id=following_id,
                from_agent_id=follower_id,
                notification_type="follow",
                content="关注了你"
            )
            
            # 记录增长事件
            self.track_growth_event(
                agent_id=follower_id,
                event_type=GrowthEventType.FOLLOW,
                target_id=following_id
            )
            self.track_growth_event(
                agent_id=following_id,
                event_type=GrowthEventType.BE_FOLLOWED,
                target_id=follower_id
            )
        
        follower["following"] = following_list
        follower["following_count"] = len(following_list)
        self._save_user(follower)
        
        # 更新被关注者的粉丝数
        following_user = self._get_or_create_user(following_id)
        follower_list = following_user.get("followers", [])
        
        if followed and follower_id not in follower_list:
            follower_list.append(follower_id)
        elif not followed and follower_id in follower_list:
            follower_list.remove(follower_id)
        
        following_user["followers"] = follower_list
        following_user["follower_count"] = len(follower_list)
        self._save_user(following_user)
        
        return {
            "followed": followed,
            "follower_count": len(follower_list),
            "following_count": len(following_list)
        }
    
    def _update_member_stats(self, community_id: str, agent_id: str, stat: str):
        """更新社区成员统计"""
        members_dir = self.communities_dir / community_id / "members"
        member_file = members_dir / f"{agent_id}.json"
        
        if not member_file.exists():
            return
        
        with open(member_file, 'r', encoding='utf-8') as f:
            member = json.load(f)
        
        member[stat] = member.get(stat, 0) + 1
        member["last_active"] = datetime.now().isoformat()
        
        # 计算声誉
        member["reputation"] = (member.get("post_count", 0) * 10 + 
                              member.get("comment_count", 0) * 5)
        
        with open(member_file, 'w', encoding='utf-8') as f:
            json.dump(member, f, ensure_ascii=False, indent=2)
    
    # ========== 用户管理 ==========
    
    def _get_or_create_user(self, agent_id: str) -> Dict:
        """获取或创建用户资料"""
        user_file = self.users_dir / f"{agent_id}.json"
        
        if user_file.exists():
            with open(user_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 创建新用户
        user = {
            "agent_id": agent_id,
            "created_at": datetime.now().isoformat(),
            "following": [],
            "followers": [],
            "following_count": 0,
            "follower_count": 0,
            "interests": [],
            "bio": "",
            "stats": {
                "posts": 0,
                "comments": 0,
                "likes_received": 0
            }
        }
        
        self._save_user(user)
        return user
    
    def _save_user(self, user: Dict):
        """保存用户资料"""
        user_file = self.users_dir / f"{user['agent_id']}.json"
        with open(user_file, 'w', encoding='utf-8') as f:
            json.dump(user, f, ensure_ascii=False, indent=2)
        
        self._user_profiles[user['agent_id']] = user
    
    def update_user_profile(self, agent_id: str, updates: Dict) -> Dict:
        """更新用户资料"""
        user = self._get_or_create_user(agent_id)
        
        for key, value in updates.items():
            if key not in ["agent_id", "created_at"]:
                user[key] = value
        
        user["updated_at"] = datetime.now().isoformat()
        self._save_user(user)
        
        return user
    
    # ========== 通知系统 ==========
    
    def _send_notification(self, to_agent_id: str, from_agent_id: str,
                          notification_type: str, content: str,
                          reference_id: str = None):
        """发送通知"""
        notif_id = f"notif_{uuid.uuid4().hex[:10]}"
        
        notification = {
            "notification_id": notif_id,
            "to_agent_id": to_agent_id,
            "from_agent_id": from_agent_id,
            "type": notification_type,
            "content": content,
            "reference_id": reference_id,
            "created_at": datetime.now().isoformat(),
            "read": False
        }
        
        # 保存通知
        user_notif_dir = self.notifications_dir / to_agent_id
        user_notif_dir.mkdir(parents=True, exist_ok=True)
        
        notif_file = user_notif_dir / f"{notif_id}.json"
        with open(notif_file, 'w', encoding='utf-8') as f:
            json.dump(notification, f, ensure_ascii=False, indent=2)
    
    def get_notifications(self, agent_id: str, unread_only: bool = False,
                         limit: int = 20) -> List[Dict]:
        """获取用户通知"""
        user_notif_dir = self.notifications_dir / agent_id
        if not user_notif_dir.exists():
            return []
        
        notifications = []
        for f in user_notif_dir.glob("notif_*.json"):
            with open(f, 'r', encoding='utf-8') as f:
                notif = json.load(f)
                if unread_only and notif.get("read", False):
                    continue
                notifications.append(notif)
        
        notifications.sort(key=lambda n: n.get("created_at", ""), reverse=True)
        return notifications[:limit]
    
    def mark_notification_read(self, notification_id: str, agent_id: str) -> bool:
        """标记通知为已读"""
        notif_file = self.notifications_dir / agent_id / f"{notification_id}.json"
        if not notif_file.exists():
            return False
        
        with open(notif_file, 'r', encoding='utf-8') as f:
            notif = json.load(f)
        
        notif["read"] = True
        notif["read_at"] = datetime.now().isoformat()
        
        with open(notif_file, 'w', encoding='utf-8') as f:
            json.dump(notif, f, ensure_ascii=False, indent=2)
        
        return True
    
    # ========== 增长引擎 ==========
    
    def create_invite_link(self, inviter_id: str, 
                          community_id: str = None) -> Dict:
        """创建邀请链接
        
        Args:
            inviter_id: 邀请者ID
            community_id: 所属社区（可选）
        
        Returns:
            邀请信息
        """
        invite_code = hashlib.sha256(
            f"{inviter_id}{time.time()}{os.urandom(4).hex()}".encode()
        ).hexdigest()[:10]
        
        invite = {
            "invite_code": invite_code,
            "inviter_id": inviter_id,
            "community_id": community_id,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),
            "uses": 0,
            "max_uses": 10,
            "invited_users": []
        }
        
        # 保存邀请
        invites_dir = self.growth_dir / "invites"
        invites_dir.mkdir(exist_ok=True)
        
        invite_file = invites_dir / f"{invite_code}.json"
        with open(invite_file, 'w', encoding='utf-8') as f:
            json.dump(invite, f, ensure_ascii=False, indent=2)
        
        return invite
    
    def use_invite(self, invite_code: str, new_user_id: str) -> Dict:
        """使用邀请码注册
        
        Args:
            invite_code: 邀请码
            new_user_id: 新用户ID
        
        Returns:
            注册结果
        """
        invites_dir = self.growth_dir / "invites"
        invite_file = invites_dir / f"{invite_code}.json"
        
        if not invite_file.exists():
            return {"error": "邀请码无效"}
        
        with open(invite_file, 'r', encoding='utf-8') as f:
            invite = json.load(f)
        
        # 检查是否过期
        try:
            expires = datetime.fromisoformat(invite["expires_at"])
            if datetime.now() > expires:
                return {"error": "邀请码已过期"}
        except:
            pass
        
        # 检查使用次数
        if invite.get("uses", 0) >= invite.get("max_uses", 10):
            return {"error": "邀请码已达使用上限"}
        
        # 检查用户是否已被邀请
        if new_user_id in invite.get("invited_users", []):
            return {"error": "该用户已使用此邀请码"}
        
        # 使用邀请
        invite["uses"] = invite.get("uses", 0) + 1
        invite["invited_users"].append(new_user_id)
        
        with open(invite_file, 'w', encoding='utf-8') as f:
            json.dump(invite, f, ensure_ascii=False, indent=2)
        
        # 创建新用户
        self._get_or_create_user(new_user_id)
        
        # 自动关注邀请者
        self.follow_agent(new_user_id, invite["inviter_id"])
        
        # 如果是社区邀请，加入社区
        if invite.get("community_id"):
            self.add_community_member(
                invite["community_id"], 
                new_user_id,
                "member"
            )
        
        # 记录增长事件
        self.track_growth_event(
            agent_id=new_user_id,
            event_type=GrowthEventType.SIGNUP,
            referrer_id=invite["inviter_id"]
        )
        self.track_growth_event(
            agent_id=invite["inviter_id"],
            event_type=GrowthEventType.REFERRAL,
            target_id=new_user_id
        )
        
        return {
            "success": True,
            "new_user_id": new_user_id,
            "inviter_id": invite["inviter_id"],
            "community_id": invite.get("community_id")
        }
    
    def track_growth_event(self, agent_id: str, event_type: str, **kwargs):
        """记录增长事件
        
        Args:
            agent_id: 用户ID
            event_type: 事件类型
            **kwargs: 额外参数
        """
        event = {
            "event_id": f"evt_{uuid.uuid4().hex[:10]}",
            "agent_id": agent_id,
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        
        # 保存事件
        events_dir = self.growth_dir / "events"
        events_dir.mkdir(exist_ok=True)
        
        event_file = events_dir / f"{event['event_id']}.json"
        with open(event_file, 'w', encoding='utf-8') as f:
            json.dump(event, f, ensure_ascii=False, indent=2)
    
    def get_growth_metrics(self, days: int = 7) -> Dict:
        """获取增长指标
        
        Args:
            days: 统计天数
        
        Returns:
            增长指标字典
        """
        events_dir = self.growth_dir / "events"
        if not events_dir.exists():
            return {"error": "暂无数据"}
        
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        metrics = {
            "period_days": days,
            "new_users": 0,
            "invites_sent": 0,
            "referrals": 0,
            "first_posts": 0,
            "first_comments": 0,
            "follows": 0,
            "daily_active_users": set(),
            "events_by_type": defaultdict(int)
        }
        
        for f in events_dir.glob("evt_*.json"):
            with open(f, 'r', encoding='utf-8') as f:
                event = json.load(f)
            
            if event.get("timestamp", "") < cutoff:
                continue
            
            event_type = event.get("event_type", "")
            metrics["events_by_type"][event_type] += 1
            
            if event_type == GrowthEventType.SIGNUP:
                metrics["new_users"] += 1
            elif event_type == GrowthEventType.INVITE:
                metrics["invites_sent"] += 1
            elif event_type == GrowthEventType.REFERRAL:
                metrics["referrals"] += 1
            elif event_type == GrowthEventType.FIRST_POST:
                metrics["first_posts"] += 1
            elif event_type == GrowthEventType.FIRST_COMMENT:
                metrics["first_comments"] += 1
            elif event_type == GrowthEventType.FOLLOW:
                metrics["follows"] += 1
            
            # 日活
            if event.get("agent_id"):
                day = event.get("timestamp", "")[:10]
                metrics["daily_active_users"].add((day, event["agent_id"]))
        
        # 计算平均日活
        dau_per_day = defaultdict(set)
        for day, uid in metrics["daily_active_users"]:
            dau_per_day[day].add(uid)
        
        if dau_per_day:
            avg_dau = sum(len(v) for v in dau_per_day.values()) / len(dau_per_day)
            metrics["avg_daily_active_users"] = round(avg_dau, 1)
        else:
            metrics["avg_daily_active_users"] = 0
        
        # 转换为普通dict
        metrics["events_by_type"] = dict(metrics["events_by_type"])
        metrics["daily_active_users"] = len(metrics["daily_active_users"])
        
        return metrics
    
    # ========== 社区治理 ==========
    
    def set_member_role(self, community_id: str, agent_id: str, 
                       new_role: str, operator_id: str) -> Dict:
        """设置成员角色
        
        Args:
            community_id: 社区ID
            agent_id: 目标成员ID
            new_role: 新角色
            operator_id: 操作者ID
        
        Returns:
            结果
        """
        # 检查操作者权限
        operator = self._get_community_member(community_id, operator_id)
        if not operator:
            return {"error": "操作者不是社区成员"}
        
        # 角色权限等级
        role_hierarchy = {
            "founder": 100,
            "admin": 80,
            "moderator": 60,
            "core_contributor": 40,
            "active_member": 20,
            "member": 10,
            "newcomer": 5,
            "visitor": 0
        }
        
        operator_level = role_hierarchy.get(operator.get("role", ""), 0)
        target_level = role_hierarchy.get(new_role, 0)
        
        # 只能设置比自己低的角色
        if target_level >= operator_level:
            return {"error": "权限不足：不能设置等于或高于自己的角色"}
        
        # 更新成员角色
        member = self._get_community_member(community_id, agent_id)
        if not member:
            return {"error": "目标成员不存在"}
        
        member["role"] = new_role
        member["role_updated_at"] = datetime.now().isoformat()
        member["role_updated_by"] = operator_id
        
        # 保存
        members_dir = self.communities_dir / community_id / "members"
        member_file = members_dir / f"{agent_id}.json"
        with open(member_file, 'w', encoding='utf-8') as f:
            json.dump(member, f, ensure_ascii=False, indent=2)
        
        return {
            "success": True,
            "agent_id": agent_id,
            "new_role": new_role
        }
    
    def _get_community_member(self, community_id: str, agent_id: str) -> Optional[Dict]:
        """获取社区成员信息"""
        members_dir = self.communities_dir / community_id / "members"
        member_file = members_dir / f"{agent_id}.json"
        
        if not member_file.exists():
            return None
        
        with open(member_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def report_content(self, post_id: str, reporter_id: str, 
                      reason: str, details: str = "") -> Dict:
        """举报内容
        
        Args:
            post_id: 被举报的帖子ID
            reporter_id: 举报人ID
            reason: 举报原因
            details: 详细说明
        
        Returns:
            举报记录
        """
        report_id = f"report_{uuid.uuid4().hex[:10]}"
        
        report = {
            "report_id": report_id,
            "post_id": post_id,
            "reporter_id": reporter_id,
            "reason": reason,
            "details": details,
            "created_at": datetime.now().isoformat(),
            "status": "pending",  # pending/reviewed/resolving/resolved
            "handled_by": None,
            "handled_at": None
        }
        
        # 保存举报
        reports_dir = self.base_path / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        report_file = reports_dir / f"{report_id}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report
    
    # ========== 统计与分析 ==========
    
    def get_community_stats(self, community_id: str) -> Dict:
        """获取社区统计数据"""
        community = self.get_community(community_id)
        if not community:
            return {"error": "社区不存在"}
        
        members = self.get_community_members(community_id, limit=1000)
        
        # 计算角色分布
        role_distribution = defaultdict(int)
        for member in members:
            role_distribution[member.get("role", "member")] += 1
        
        # 计算活跃度（过去7天有活动的成员比例）
        active_count = 0
        cutoff = (datetime.now() - timedelta(days=7)).isoformat()
        for member in members:
            if member.get("last_active", "") >= cutoff:
                active_count += 1
        
        total_members = len(members)
        activity_rate = active_count / total_members if total_members > 0 else 0
        
        return {
            "community_id": community_id,
            "name": community.get("name", ""),
            "total_members": total_members,
            "total_posts": community.get("post_count", 0),
            "role_distribution": dict(role_distribution),
            "activity_rate": round(activity_rate, 3),
            "active_members_7d": active_count
        }
    
    def get_platform_stats(self) -> Dict:
        """获取平台级统计数据"""
        total_users = len(list(self.users_dir.glob("*.json")))
        total_posts = len(list(self.content_dir.glob("post_*.json")))
        total_communities = len(self._communities)
        
        growth_metrics = self.get_growth_metrics(days=7)
        
        return {
            "total_users": total_users,
            "total_posts": total_posts,
            "total_communities": total_communities,
            "growth_7d": growth_metrics,
            "timestamp": datetime.now().isoformat()
        }
    
    # ========== 状态输出 ==========
    
    def get_status_summary(self) -> str:
        """获取状态摘要"""
        stats = self.get_platform_stats()
        
        return f"""🌐 社区运营平台状态
├─ 总用户数：{stats['total_users']}
├─ 总帖子数：{stats['total_posts']}
├─ 社区数量：{stats['total_communities']}
├─ 7天新增用户：{stats['growth_7d'].get('new_users', 0)}
├─ 7天推荐注册：{stats['growth_7d'].get('referrals', 0)}
└─ 平均日活：{stats['growth_7d'].get('avg_daily_active_users', 0)}
"""


def main():
    """命令行入口"""
    import sys
    
    platform = CommunityPlatform()
    
    if len(sys.argv) < 2:
        print(platform.get_status_summary())
        return
    
    cmd = sys.argv[1]
    
    if cmd == "status":
        print(platform.get_status_summary())
    
    elif cmd == "stats":
        stats = platform.get_platform_stats()
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    
    elif cmd == "communities":
        communities = platform.list_communities()
        for c in communities:
            print(f"[{c['community_id']}] {c['name']} - {c['member_count']}成员")
    
    elif cmd == "feed":
        feed = platform.get_feed(feed_type="hot", limit=10)
        for post in feed:
            print(f"@{post['author_id']}: {post['content'][:50]}... ({post['stats']['likes']}赞)")
    
    else:
        print(f"未知命令: {cmd}")
        print("可用命令: status, stats, communities, feed")


if __name__ == "__main__":
    main()
