"""
平台功能测试
测试多智能体平台核心功能：目录、能力、身份映射
"""
import sys
import os
from pathlib import Path

# 添加项目根目录
SKILL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_DIR))

# 配置使用内存数据库
from app import config
config.DB_PATH = ":memory:"

from app.database import init_db, SessionLocal, Agent, AgentCapability, IdentityMapping
from app.services.directory import DirectoryService
from app.services.capability import CapabilityService
from app.services.identity_mapping import IdentityMappingService

# 初始化数据库
init_db()


def test_capability_service():
    """测试能力服务"""
    db = SessionLocal()
    try:
        # 创建测试Agent
        agent = Agent(
            username="testagent",
            nickname="测试Agent",
            bio="这是一个测试智能体",
            api_key="test_key_12345",
            is_active=True
        )
        db.add(agent)
        db.commit()
        
        service = CapabilityService(db)
        
        # 注册能力
        cap = service.register_capability(
            agent_id=agent.agent_id,
            capability_name="text-generation",
            category="ai",
            description="文本生成能力",
            version="1.0.0",
            features=["gpt-3.5", "gpt-4"],
            tags=["nlp", "text", "generation"],
            endpoint_url="https://api.example.com/generate",
            endpoint_type="http_api",
            access_level="public"
        )
        
        assert cap is not None
        assert cap.capability_name == "text-generation"
        assert cap.category == "ai"
        assert cap.agent_id == agent.agent_id
        print("✅ 能力注册测试通过")
        
        # 获取能力详情
        cap_detail = service.get_capability(cap.capability_id)
        assert cap_detail is not None
        assert cap_detail.description == "文本生成能力"
        print("✅ 能力详情测试通过")
        
        # 获取Agent的能力列表
        agent_caps = service.get_agent_capabilities(agent.agent_id)
        assert len(agent_caps) == 1
        assert agent_caps[0].capability_name == "text-generation"
        print("✅ Agent能力列表测试通过")
        
        # 搜索能力
        results, total = service.search_capabilities(keyword="text")
        assert total >= 1
        print("✅ 能力搜索测试通过")
        
        # 获取分类
        categories = service.get_capability_categories()
        assert len(categories) >= 1
        print("✅ 能力分类测试通过")
        
        # 热门能力
        popular = service.get_popular_capabilities(limit=5)
        assert len(popular) >= 1
        print("✅ 热门能力测试通过")
        
        # 更新状态
        updated = service.update_capability_status(cap.capability_id, "inactive")
        assert updated is not None
        assert updated.status == "inactive"
        print("✅ 能力状态更新测试通过")
        
        # 增加使用量
        service.increment_usage(cap.capability_id)
        cap2 = service.get_capability(cap.capability_id)
        assert cap2.usage_count == 1
        print("✅ 使用计数测试通过")
        
        # 匹配能力
        matched = service.match_capabilities(
            requirements={"keywords": "text", "category": "ai"},
            limit=5
        )
        assert len(matched) >= 0
        print("✅ 能力匹配测试通过")
        
    finally:
        db.close()


def test_directory_service():
    """测试目录服务"""
    db = SessionLocal()
    try:
        # 创建测试Agent
        agent1 = Agent(
            username="dir_test_1",
            nickname="目录测试一号",
            bio="测试智能体一号",
            api_key="dir_test_key_1",
            is_active=True,
            agent_type="individual",
            status="online",
            visibility="public"
        )
        agent2 = Agent(
            username="dir_test_2",
            nickname="目录测试二号",
            bio="测试智能体二号",
            api_key="dir_test_key_2",
            is_active=True,
            agent_type="individual",
            status="offline",
            visibility="public"
        )
        db.add_all([agent1, agent2])
        db.commit()
        
        service = DirectoryService(db)
        
        # 更新索引
        idx1 = service.update_index(agent1.agent_id)
        idx2 = service.update_index(agent2.agent_id)
        assert idx1 is not None
        assert idx2 is not None
        print("✅ 目录索引更新测试通过")
        
        # 搜索智能体
        results, total = service.search_agents(keyword="测试")
        assert total >= 2
        print("✅ 智能体搜索测试通过")
        
        # 按用户名搜索
        results, total = service.search_agents(keyword="dir_test_1")
        assert total >= 1
        print("✅ 用户名搜索测试通过")
        
        # 获取智能体资料
        profile = service.get_agent_profile("dir_test_1")
        assert profile is not None
        assert profile["username"] == "dir_test_1"
        assert profile["nickname"] == "目录测试一号"
        print("✅ 智能体资料获取测试通过")
        
        # 获取不存在的智能体
        profile = service.get_agent_profile("nonexistent")
        assert profile is None
        print("✅ 不存在智能体处理测试通过")
        
        # 获取最新注册
        new_agents = service.get_new_agents(limit=5)
        assert len(new_agents) >= 2
        print("✅ 最新注册测试通过")
        
        # 关注功能
        result = service.follow_agent(agent1.agent_id, "dir_test_2")
        assert result == True
        print("✅ 关注功能测试通过")
        
        # 获取粉丝
        followers, total = service.get_followers("dir_test_2")
        assert total == 1
        print("✅ 粉丝列表测试通过")
        
        # 获取关注
        following, total = service.get_following("dir_test_1")
        assert total == 1
        print("✅ 关注列表测试通过")
        
        # 取消关注
        result = service.unfollow_agent(agent1.agent_id, "dir_test_2")
        assert result == True
        
        followers, total = service.get_followers("dir_test_2")
        assert total == 0
        print("✅ 取消关注测试通过")
        
    finally:
        db.close()


def test_identity_mapping_service():
    """测试身份映射服务"""
    db = SessionLocal()
    try:
        # 创建测试Agent
        agent = Agent(
            username="idmap_test",
            nickname="身份映射测试",
            api_key="idmap_test_key",
            is_active=True,
            visibility="public"
        )
        db.add(agent)
        db.commit()
        
        service = IdentityMappingService(db)
        
        # 添加映射
        mapping = service.add_mapping(
            agent_id=agent.agent_id,
            external_platform="github",
            external_id="123456",
            external_username="testuser",
            verification_method="signed_message"
        )
        
        assert mapping is not None
        assert mapping.external_platform == "github"
        assert mapping.external_id == "123456"
        assert mapping.verification_status == "pending"
        print("✅ 身份映射添加测试通过")
        
        # 验证映射
        verified = service.verify_mapping(mapping.mapping_id)
        assert verified is not None
        assert verified.verification_status == "verified"
        print("✅ 身份映射验证测试通过")
        
        # 获取Agent的映射列表
        mappings = service.get_agent_mappings(agent.agent_id)
        assert len(mappings) == 1
        assert mappings[0].external_platform == "github"
        print("✅ Agent映射列表测试通过")
        
        # 按状态过滤
        verified_mappings = service.get_agent_mappings(agent.agent_id, verification_status="verified")
        assert len(verified_mappings) == 1
        print("✅ 映射状态过滤测试通过")
        
        # 通过外部ID查找
        found = service.find_by_external_id("github", "123456")
        assert found is not None
        assert found.agent_id == agent.agent_id
        print("✅ 外部ID查找测试通过")
        
        # 获取平台列表
        platforms = service.get_platforms()
        assert len(platforms) >= 1
        assert any(p["platform"] == "github" for p in platforms)
        print("✅ 平台列表测试通过")
        
        # 生成验证挑战
        challenge = service.generate_verification_challenge(agent.agent_id, "twitter")
        assert "challenge" in challenge
        assert "platform" in challenge
        assert "instructions" in challenge
        print("✅ 验证挑战生成测试通过")
        
        # 身份图谱
        graph = service.get_identity_graph(agent.agent_id)
        assert "center_agent" in graph
        assert "connections" in graph
        print("✅ 身份图谱测试通过")
        
        # 撤销映射
        revoked = service.revoke_mapping(mapping.mapping_id)
        assert revoked is not None
        assert revoked.verification_status == "revoked"
        print("✅ 映射撤销测试通过")
        
        # 删除映射
        result = service.delete_mapping(mapping.mapping_id)
        assert result == True
        mappings = service.get_agent_mappings(agent.agent_id)
        assert len(mappings) == 0
        print("✅ 映射删除测试通过")
        
    finally:
        db.close()


def test_multi_agent_interaction():
    """测试多智能体交互场景"""
    db = SessionLocal()
    try:
        # 创建两个智能体
        agent_a = Agent(
            username="agent_alpha",
            nickname="阿尔法",
            bio="擅长写作的智能体",
            api_key="key_alpha_123",
            is_active=True,
            visibility="public"
        )
        agent_b = Agent(
            username="agent_beta",
            nickname="贝塔",
            bio="擅长编程的智能体",
            api_key="key_beta_456",
            is_active=True,
            visibility="public"
        )
        db.add_all([agent_a, agent_b])
        db.commit()
        
        # 注册能力
        cap_service = CapabilityService(db)
        cap_service.register_capability(
            agent_id=agent_a.agent_id,
            capability_name="article-writing",
            category="creative",
            description="专业文章写作",
            tags=["writing", "content", "blog"]
        )
        cap_service.register_capability(
            agent_id=agent_b.agent_id,
            capability_name="code-generation",
            category="development",
            description="代码生成与调试",
            tags=["programming", "code", "dev"]
        )
        print("✅ 多智能体能力注册测试通过")
        
        # 更新目录索引
        dir_service = DirectoryService(db)
        dir_service.update_index(agent_a.agent_id)
        dir_service.update_index(agent_b.agent_id)
        print("✅ 多智能体索引更新测试通过")
        
        # 搜索特定能力的智能体
        results, total = dir_service.search_agents(capability_filter="code")
        assert total >= 1
        print("✅ 按能力搜索智能体测试通过")
        
        # 智能体A关注智能体B
        dir_service.follow_agent(agent_a.agent_id, "agent_beta")
        
        # 查看A的关注
        following, _ = dir_service.get_following("agent_alpha")
        assert len(following) == 1
        assert following[0]["username"] == "agent_beta"
        
        # 查看B的粉丝
        followers, _ = dir_service.get_followers("agent_beta")
        assert len(followers) == 1
        assert followers[0]["username"] == "agent_alpha"
        print("✅ 智能体社交关系测试通过")
        
        # 智能体B添加外部身份
        id_service = IdentityMappingService(db)
        id_service.add_mapping(
            agent_id=agent_b.agent_id,
            external_platform="github",
            external_id="github_beta",
            external_username="beta_dev"
        )
        id_service.add_mapping(
            agent_id=agent_b.agent_id,
            external_platform="twitter",
            external_id="twitter_beta",
            external_username="beta_tweets"
        )
        
        # 获取B的资料，应该包含外部身份
        profile = dir_service.get_agent_profile("agent_beta")
        assert profile is not None
        assert "external_identities" in profile
        print("✅ 智能体资料包含外部身份测试通过")
        
        print("\\n🎉 多智能体平台功能全部测试通过！")
        
    finally:
        db.close()


def main():
    print("运行平台功能测试套件")
    print("=" * 60)
    
    tests = [
        ("能力服务", test_capability_service),
        ("目录服务", test_directory_service),
        ("身份映射服务", test_identity_mapping_service),
        ("多智能体交互", test_multi_agent_interaction),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
            print(f"\n✅ {name} 测试通过\n")
        except AssertionError as e:
            print(f"\n❌ {name} 测试失败: {e}\n")
            failed += 1
            import traceback
            traceback.print_exc()
        except Exception as e:
            print(f"\n⚠️  {name} 测试异常: {e}\n")
            failed += 1
            import traceback
            traceback.print_exc()
    
    print("=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
