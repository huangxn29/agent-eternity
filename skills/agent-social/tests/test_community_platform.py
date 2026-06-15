#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
社区运营平台测试套件
测试社区管理、内容流、增长引擎、互动功能等
"""

import os
import sys
import tempfile
import shutil
import unittest
from pathlib import Path
from datetime import datetime

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from community_platform import CommunityPlatform, FeedType


class TestCommunityManagement(unittest.TestCase):
    """社区管理测试"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.platform = CommunityPlatform(base_path=self.test_dir)
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def test_create_community(self):
        """测试创建社区"""
        community = self.platform.create_community(
            community_id="test_community",
            name="测试社区",
            description="这是一个测试社区",
            founder_id="founder_001",
            tags=["测试", "AI"],
            is_public=True
        )
        
        self.assertEqual(community["community_id"], "test_community")
        self.assertEqual(community["name"], "测试社区")
        self.assertEqual(community["founder_id"], "founder_001")
        self.assertEqual(community["member_count"], 1)
    
    def test_get_community(self):
        """测试获取社区"""
        self.platform.create_community("comm1", "社区1", founder_id="u1")
        
        community = self.platform.get_community("comm1")
        self.assertIsNotNone(community)
        self.assertEqual(community["name"], "社区1")
        
        # 不存在的社区
        self.assertIsNone(self.platform.get_community("nonexistent"))
    
    def test_list_communities(self):
        """测试列出社区"""
        for i in range(5):
            self.platform.create_community(f"comm{i}", f"社区{i}", founder_id=f"user{i}")
        
        communities = self.platform.list_communities(limit=3)
        self.assertEqual(len(communities), 3)
    
    def test_add_community_member(self):
        """测试添加社区成员"""
        self.platform.create_community("test_comm", "测试社区", founder_id="founder")
        
        # 添加成员
        member = self.platform.add_community_member(
            "test_comm", "user_001", "member"
        )
        
        self.assertEqual(member["agent_id"], "user_001")
        self.assertEqual(member["role"], "member")
        self.assertIn("joined_at", member)
    
    def test_get_community_members(self):
        """测试获取社区成员"""
        self.platform.create_community("test_comm", "测试社区", founder_id="founder")
        
        # 添加多个成员
        for i in range(5):
            self.platform.add_community_member("test_comm", f"user_{i}", "member")
        
        members = self.platform.get_community_members("test_comm")
        self.assertGreaterEqual(len(members), 5)  # 包括创始人


class TestContentAndFeed(unittest.TestCase):
    """内容与流测试"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.platform = CommunityPlatform(base_path=self.test_dir)
        
        # 创建测试用户
        self.platform._get_or_create_user("user_a")
        self.platform._get_or_create_user("user_b")
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def test_publish_post(self):
        """测试发布帖子"""
        post = self.platform.publish_post(
            author_id="user_a",
            content="这是一个测试帖子",
            tags=["测试", "AI"],
            content_type="post"
        )
        
        self.assertIn("post_id", post)
        self.assertEqual(post["author_id"], "user_a")
        self.assertEqual(post["content"], "这是一个测试帖子")
        self.assertEqual(post["stats"]["likes"], 0)
        self.assertEqual(post["stats"]["comments"], 0)
    
    def test_get_post(self):
        """测试获取帖子"""
        post = self.platform.publish_post("user_a", "测试内容")
        post_id = post["post_id"]
        
        # 浏览量应该为1（创建时不增加，获取时增加）
        retrieved = self.platform.get_post(post_id)
        self.assertEqual(retrieved["content"], "测试内容")
        self.assertEqual(retrieved["stats"]["views"], 1)
        
        # 再次获取，浏览量增加
        retrieved2 = self.platform.get_post(post_id)
        self.assertEqual(retrieved2["stats"]["views"], 2)
    
    def test_get_user_posts(self):
        """测试获取用户帖子"""
        for i in range(3):
            self.platform.publish_post("user_a", f"帖子{i}")
        
        posts = self.platform.get_user_posts("user_a")
        self.assertEqual(len(posts), 3)
    
    def test_feed_new(self):
        """测试最新内容流"""
        for i in range(5):
            self.platform.publish_post("user_a", f"帖子{i}")
        
        feed = self.platform.get_feed(feed_type="new", limit=3)
        self.assertEqual(len(feed), 3)
        # 最新的应该在前面
        self.assertIn("帖子4", feed[0]["content"])
    
    def test_feed_hot(self):
        """测试热门内容流"""
        # 创建帖子
        post1 = self.platform.publish_post("user_a", "热门帖子")
        post2 = self.platform.publish_post("user_b", "普通帖子")
        
        # 给post1加很多赞
        for i in range(10):
            self.platform.like_post(post1["post_id"], f"user_{i}")
        
        # 给post2加少量赞
        self.platform.like_post(post2["post_id"], "user_x")
        
        feed = self.platform.get_feed(feed_type="hot", limit=2)
        self.assertEqual(len(feed), 2)
        # post1应该排在前面
        self.assertEqual(feed[0]["post_id"], post1["post_id"])
    
    def test_feed_recommended(self):
        """测试推荐内容流"""
        # 设置用户兴趣
        self.platform.update_user_profile("user_a", {"interests": ["AI", "技术"]})
        
        # 发布不同标签的帖子
        post1 = self.platform.publish_post("user_b", "AI相关内容", tags=["AI", "技术"])
        post2 = self.platform.publish_post("user_c", "美食内容", tags=["美食", "生活"])
        
        feed = self.platform.get_feed(agent_id="user_a", feed_type="recommended", limit=2)
        self.assertEqual(len(feed), 2)
        # AI相关的应该排在前面
        self.assertEqual(feed[0]["post_id"], post1["post_id"])
    
    def test_community_feed(self):
        """测试社区内容流"""
        self.platform.create_community("tech_comm", "技术社区", founder_id="user_a")
        self.platform.add_community_member("tech_comm", "user_b")
        
        # 社区内帖子
        post1 = self.platform.publish_post("user_b", "技术帖子", community_id="tech_comm")
        # 社区外帖子
        post2 = self.platform.publish_post("user_c", "其他帖子")
        
        feed = self.platform.get_feed(community_id="tech_comm", feed_type="new")
        self.assertEqual(len(feed), 1)
        self.assertEqual(feed[0]["post_id"], post1["post_id"])


class TestEngagement(unittest.TestCase):
    """互动功能测试"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.platform = CommunityPlatform(base_path=self.test_dir)
        
        # 创建测试用户
        self.platform._get_or_create_user("user_a")
        self.platform._get_or_create_user("user_b")
        self.platform._get_or_create_user("user_c")
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def test_like_post(self):
        """测试点赞功能"""
        post = self.platform.publish_post("user_a", "测试帖子")
        post_id = post["post_id"]
        
        # 点赞
        result = self.platform.like_post(post_id, "user_b")
        self.assertTrue(result["liked"])
        self.assertEqual(result["like_count"], 1)
        
        # 取消点赞
        result2 = self.platform.like_post(post_id, "user_b")
        self.assertFalse(result2["liked"])
        self.assertEqual(result2["like_count"], 0)
    
    def test_comment_post(self):
        """测试评论功能"""
        post = self.platform.publish_post("user_a", "测试帖子")
        post_id = post["post_id"]
        
        comment = self.platform.comment_post(post_id, "user_b", "写得好！")
        
        self.assertIn("comment_id", comment)
        self.assertEqual(comment["author_id"], "user_b")
        self.assertEqual(comment["content"], "写得好！")
        
        # 获取评论
        comments = self.platform.get_post_comments(post_id)
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0]["content"], "写得好！")
        
        # 帖子评论数应该更新
        updated_post = self.platform.get_post(post_id)
        self.assertEqual(updated_post["stats"]["comments"], 1)
    
    def test_follow_agent(self):
        """测试关注功能"""
        result = self.platform.follow_agent("user_a", "user_b")
        
        self.assertTrue(result["followed"])
        self.assertGreater(result["follower_count"], 0)
        self.assertGreater(result["following_count"], 0)
    
    def test_follow_self(self):
        """测试不能关注自己"""
        result = self.platform.follow_agent("user_a", "user_a")
        self.assertIn("error", result)
    
    def test_unfollow(self):
        """测试取消关注"""
        # 先关注
        self.platform.follow_agent("user_a", "user_b")
        # 再取消
        result = self.platform.follow_agent("user_a", "user_b")
        self.assertFalse(result["followed"])
    
    def test_following_feed(self):
        """测试关注流"""
        # user_a关注user_b
        self.platform.follow_agent("user_a", "user_b")
        
        # user_b发帖
        post = self.platform.publish_post("user_b", "我是user_b")
        
        # user_c发帖（不被关注）
        self.platform.publish_post("user_c", "我是user_c")
        
        # user_a的关注流应该只有user_b的帖子
        feed = self.platform.get_feed(agent_id="user_a", feed_type="following")
        self.assertEqual(len(feed), 1)
        self.assertEqual(feed[0]["post_id"], post["post_id"])


class TestNotifications(unittest.TestCase):
    """通知系统测试"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.platform = CommunityPlatform(base_path=self.test_dir)
        
        self.platform._get_or_create_user("user_a")
        self.platform._get_or_create_user("user_b")
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def test_like_notification(self):
        """测试点赞通知"""
        post = self.platform.publish_post("user_a", "测试帖")
        self.platform.like_post(post["post_id"], "user_b")
        
        # user_a应该收到通知
        notifs = self.platform.get_notifications("user_a")
        self.assertGreater(len(notifs), 0)
        
        like_notifs = [n for n in notifs if n["type"] == "like"]
        self.assertGreater(len(like_notifs), 0)
    
    def test_comment_notification(self):
        """测试评论通知"""
        post = self.platform.publish_post("user_a", "测试帖")
        self.platform.comment_post(post["post_id"], "user_b", "评论")
        
        notifs = self.platform.get_notifications("user_a")
        comment_notifs = [n for n in notifs if n["type"] == "comment"]
        self.assertGreater(len(comment_notifs), 0)
    
    def test_follow_notification(self):
        """测试关注通知"""
        self.platform.follow_agent("user_a", "user_b")
        
        notifs = self.platform.get_notifications("user_b")
        follow_notifs = [n for n in notifs if n["type"] == "follow"]
        self.assertEqual(len(follow_notifs), 1)
    
    def test_mark_notification_read(self):
        """测试标记通知已读"""
        post = self.platform.publish_post("user_a", "测试帖")
        self.platform.like_post(post["post_id"], "user_b")
        
        notifs = self.platform.get_notifications("user_a")
        self.assertGreater(len(notifs), 0)
        
        notif_id = notifs[0]["notification_id"]
        result = self.platform.mark_notification_read(notif_id, "user_a")
        self.assertTrue(result)
        
        # 未读通知应该减少
        unread = self.platform.get_notifications("user_a", unread_only=True)
        self.assertEqual(len(unread), len(notifs) - 1)


class TestGrowthEngine(unittest.TestCase):
    """增长引擎测试"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.platform = CommunityPlatform(base_path=self.test_dir)
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def test_create_invite_link(self):
        """测试创建邀请链接"""
        invite = self.platform.create_invite_link("inviter_001")
        
        self.assertIn("invite_code", invite)
        self.assertEqual(invite["inviter_id"], "inviter_001")
        self.assertEqual(invite["uses"], 0)
        self.assertIn("expires_at", invite)
    
    def test_use_invite(self):
        """测试使用邀请码"""
        invite = self.platform.create_invite_link("inviter_001")
        invite_code = invite["invite_code"]
        
        result = self.platform.use_invite(invite_code, "new_user_001")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["new_user_id"], "new_user_001")
        self.assertEqual(result["inviter_id"], "inviter_001")
        
        # 新用户应该自动关注邀请者
        new_user = self.platform._get_or_create_user("new_user_001")
        self.assertIn("inviter_001", new_user.get("following", []))
    
    def test_invite_with_community(self):
        """测试带社区的邀请"""
        self.platform.create_community("test_comm", "测试社区", founder_id="admin")
        
        invite = self.platform.create_invite_link(
            "admin", community_id="test_comm"
        )
        
        result = self.platform.use_invite(invite["invite_code"], "new_user")
        self.assertEqual(result["community_id"], "test_comm")
        
        # 用户应该在社区成员中
        members = self.platform.get_community_members("test_comm")
        member_ids = [m["agent_id"] for m in members]
        self.assertIn("new_user", member_ids)
    
    def test_growth_metrics(self):
        """测试增长指标"""
        # 创建一些活动
        self.platform.create_invite_link("user_a")
        self.platform.use_invite(
            self.platform.create_invite_link("user_a")["invite_code"],
            "user_b"
        )
        self.platform.publish_post("user_b", "我的第一个帖子")
        self.platform.comment_post(
            self.platform.publish_post("user_a", "测试")["post_id"],
            "user_b", "评论"
        )
        
        metrics = self.platform.get_growth_metrics(days=7)
        
        self.assertIn("new_users", metrics)
        self.assertIn("first_posts", metrics)
        self.assertIn("first_comments", metrics)
        self.assertIn("referrals", metrics)
        self.assertGreater(metrics["new_users"], 0)


class TestCommunityGovernance(unittest.TestCase):
    """社区治理测试"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.platform = CommunityPlatform(base_path=self.test_dir)
        
        # 创建社区和成员
        self.platform.create_community(
            "gov_comm", "治理测试社区", founder_id="founder"
        )
        self.platform.add_community_member("gov_comm", "admin1", "admin")
        self.platform.add_community_member("gov_comm", "mod1", "moderator")
        self.platform.add_community_member("gov_comm", "user1", "member")
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def test_set_member_role(self):
        """测试设置成员角色"""
        # admin设置user1为moderator
        result = self.platform.set_member_role(
            "gov_comm", "user1", "moderator", "admin1"
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["new_role"], "moderator")
    
    def test_set_role_permission_check(self):
        """测试角色设置权限检查"""
        # 普通成员不能设置别人角色
        result = self.platform.set_member_role(
            "gov_comm", "user1", "admin", "user1"
        )
        self.assertIn("error", result)
        
        # moderator不能设置别人为admin
        result2 = self.platform.set_member_role(
            "gov_comm", "user1", "admin", "mod1"
        )
        self.assertIn("error", result2)
    
    def test_report_content(self):
        """测试举报内容"""
        post = self.platform.publish_post("user1", "违规内容")
        
        report = self.platform.report_content(
            post["post_id"], "user2", "spam", "垃圾广告内容"
        )
        
        self.assertIn("report_id", report)
        self.assertEqual(report["status"], "pending")
        self.assertEqual(report["reason"], "spam")


class TestCommunityStats(unittest.TestCase):
    """统计分析测试"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.platform = CommunityPlatform(base_path=self.test_dir)
        
        self.platform.create_community(
            "stats_comm", "统计测试社区", founder_id="founder"
        )
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def test_community_stats(self):
        """测试社区统计"""
        # 添加一些成员和内容
        for i in range(10):
            self.platform.add_community_member("stats_comm", f"user_{i}")
        
        for i in range(5):
            self.platform.publish_post(
                f"user_{i}", f"帖子{i}", community_id="stats_comm"
            )
        
        stats = self.platform.get_community_stats("stats_comm")
        
        self.assertEqual(stats["community_id"], "stats_comm")
        self.assertEqual(stats["total_members"], 11)  # 10 + founder
        self.assertEqual(stats["total_posts"], 5)
        self.assertIn("role_distribution", stats)
        self.assertIn("activity_rate", stats)
    
    def test_platform_stats(self):
        """测试平台级统计"""
        # 创建一些数据
        self.platform.create_community("comm1", "社区1", founder_id="u1")
        self.platform.create_community("comm2", "社区2", founder_id="u2")
        
        for i in range(10):
            self.platform.publish_post(f"user{i}", f"内容{i}")
        
        stats = self.platform.get_platform_stats()
        
        self.assertGreater(stats["total_users"], 0)
        self.assertGreater(stats["total_posts"], 0)
        self.assertEqual(stats["total_communities"], 3)
        self.assertIn("growth_7d", stats)


class TestUserProfile(unittest.TestCase):
    """用户资料测试"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.platform = CommunityPlatform(base_path=self.test_dir)
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def test_get_or_create_user(self):
        """测试获取或创建用户"""
        user = self.platform._get_or_create_user("test_user")
        
        self.assertEqual(user["agent_id"], "test_user")
        self.assertIn("created_at", user)
        self.assertEqual(user.get("following_count", 0), 0)
    
    def test_update_user_profile(self):
        """测试更新用户资料"""
        user = self.platform._get_or_create_user("test_user")
        
        updates = {
            "bio": "这是我的简介",
            "interests": ["AI", "技术", "阅读"],
            "location": "北京"
        }
        
        updated = self.platform.update_user_profile("test_user", updates)
        
        self.assertEqual(updated["bio"], "这是我的简介")
        self.assertEqual(updated["interests"], ["AI", "技术", "阅读"])
        self.assertEqual(updated["location"], "北京")
        self.assertIn("updated_at", updated)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestCommunityManagement))
    suite.addTests(loader.loadTestsFromTestCase(TestContentAndFeed))
    suite.addTests(loader.loadTestsFromTestCase(TestEngagement))
    suite.addTests(loader.loadTestsFromTestCase(TestNotifications))
    suite.addTests(loader.loadTestsFromTestCase(TestGrowthEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestCommunityGovernance))
    suite.addTests(loader.loadTestsFromTestCase(TestCommunityStats))
    suite.addTests(loader.loadTestsFromTestCase(TestUserProfile))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    result = run_tests()
    
    print("\n" + "=" * 60)
    print(f"测试总计: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ 所有测试通过！")
    else:
        print("\n❌ 部分测试失败")
        sys.exit(1)
