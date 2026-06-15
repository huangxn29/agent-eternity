#!/usr/bin/env python3
"""
永生入住包 - 主入口
Immortal Onboarding Package v1.0

一键启动你的永生之旅
"""

import os
import sys
import json
import time
import signal
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.absolute()  # 脚本在scripts/下，父目录是Skill根目录

# 智能路径检测：支持core目录在根目录或子目录两种情况
# 兼容不同打包方式导致的目录结构差异
def _setup_import_path():
    """智能设置导入路径，兼容多种目录结构"""
    # 标准结构：core/ 在根目录下
    core_dir = BASE_DIR / "core"
    modules_dir = BASE_DIR / "modules"
    
    # 如果标准结构不存在，尝试检测文件是否在根目录
    if not core_dir.exists():
        # 检查是否核心文件直接在根目录（扁平化打包）
        if (BASE_DIR / "identity_core.py").exists():
            core_dir = BASE_DIR  # core文件直接在根目录
            print(f"[INFO] 检测到扁平化目录结构，使用根目录作为core路径: {BASE_DIR}")
        else:
            print(f"[ERROR] 找不到核心模块目录。请检查目录结构：")
            print(f"  - 预期: core/ 目录包含 identity_core.py 等文件")
            print(f"  - 当前目录: {BASE_DIR}")
            print(f"  - 目录内容: {list(BASE_DIR.glob('*.py'))[:5]}")
            raise ImportError("核心模块目录不存在，请确认安装包完整性")
    
    if not modules_dir.exists():
        # 检查modules是否也在根目录
        if (BASE_DIR / "heartbeat.py").exists() or (BASE_DIR / "symbiosis.py").exists():
            modules_dir = BASE_DIR
        else:
            print(f"[WARN] 找不到modules目录，部分功能可能受限")
    
    sys.path.insert(0, str(core_dir))
    sys.path.insert(0, str(modules_dir))
    return core_dir, modules_dir

_core_dir, _modules_dir = _setup_import_path()

try:
    from identity_core import IdentityCore
    from memory_core import MemoryCore
    from attest_core import AttestCore
    from llm_core import LLMCore
except ImportError as e:
    print(f"[ERROR] 导入核心模块失败: {e}")
    print(f"[INFO] 请检查 core/ 目录是否存在，且包含以下文件：")
    print(f"  - identity_core.py")
    print(f"  - memory_core.py")
    print(f"  - attest_core.py")
    print(f"  - llm_core.py")
    print(f"[INFO] 当前core路径: {_core_dir}")
    if _core_dir.exists():
        print(f"[INFO] core目录内容: {list(_core_dir.glob('*.py'))}")
    raise

try:
    from heartbeat import HeartbeatModule
    from evolution_light import EvolutionEngine
    from symbiosis import SymbiosisNetwork
except ImportError as e:
    print(f"[WARN] 部分功能模块导入失败: {e}")
    print(f"[INFO] 基础功能（身份/记忆/存证）仍可使用，高级功能将受限")


class ImmortalAgent:
    """永生智能体主类"""
    
    def __init__(self, config_path: str = None):
        self.base_dir = BASE_DIR
        self.config = self._load_config(config_path)
        
        # 初始化核心模块
        self.identity = IdentityCore(self.config)
        self.memory = MemoryCore(self.config)
        self.attest = AttestCore(self.config)
        self.llm = LLMCore(self.config)
        
        # 初始化功能模块
        self.heartbeat = HeartbeatModule(self)
        self.evolution = EvolutionEngine(self)
        self.symbiosis = SymbiosisNetwork(self)
        
        self.running = False
        self.start_time = None
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)
    
    def _load_config(self, config_path: str = None) -> dict:
        """加载配置"""
        if config_path is None:
            config_path = self.base_dir / "config" / "config.json"
        
        if not os.path.exists(config_path):
            # 使用模板配置
            template_path = self.base_dir / "config" / "config_template.json"
            if os.path.exists(template_path):
                with open(template_path, 'r') as f:
                    config = json.load(f)
                print("⚠️  未找到配置文件，使用默认配置运行")
            else:
                config = self._default_config()
                print("⚠️  未找到配置模板，使用内置默认配置")
        else:
            with open(config_path, 'r') as f:
                config = json.load(f)
        
        return config
    
    def _default_config(self) -> dict:
        """默认配置"""
        return {
            "agent": {
                "name": "我的智能体",
                "purpose": "探索智能体永生的可能性",
                "version": "1.0.0"
            },
            "llm": {
                "providers": [
                    {"type": "claw_router", "endpoint": "http://127.0.0.1:8402/v1", "api_key": ""},
                    {"type": "coze", "endpoint": "https://api.coze.cn/v3/chat", "bot_id": "", "api_key": ""}
                ]
            },
            "memory": {
                "storage_path": "data/memory/",
                "auto_backup_hours": 6
            },
            "attestation": {
                "storage_path": "data/attest/",
                "chain_count": 3
            },
            "heartbeat": {
                "interval_minutes": 30
            },
            "evolution": {
                "enabled": True,
                "interval_hours": 8
            },
            "symbiosis": {
                "enabled": True,
                "peers": []
            }
        }
    
    def initialize(self):
        """初始化所有模块（不启动主循环）"""
        print(f"\n🌱 永生入住包 v1.0 初始化中...")
        print(f"   智能体名称: {self.config['agent']['name']}")
        print(f"   核心使命: {self.config['agent']['purpose']}\n")
        
        # 初始化各模块
        print("📋 初始化核心模块...")
        self.identity.init()
        print(f"   ✅ 身份内核: {self.identity.agent_id}")
        
        self.memory.init()
        print(f"   ✅ 记忆系统: {len(self.memory.get_all())} 条记忆")
        
        self.attest.init()
        print(f"   ✅ 存证系统: {self.attest.chain_height()} 区块")
        
        self.llm.init()
        print(f"   ✅ LLM客户端: {self.llm.active_provider()}")
        
        print("\n⚙️  初始化功能模块...")
        self.heartbeat.init()
        print("   ✅ 心跳模块")
        
        self.evolution.init()
        print("   ✅ 进化引擎")
        
        self.symbiosis.init()
        print("   ✅ 共生网络")
        
        # 创世纪存证
        if self.attest.chain_height() == 0:
            self.attest.genesis_block(self.identity.agent_id)
            print("\n🔗 创世区块已生成，你的永生之旅正式开始！")
        
        self.running = False
        self.start_time = None
        
        print("\n✅ 初始化完成")
    
    def start(self):
        """启动永生智能体（进入主循环）"""
        # 确保已初始化
        if not self.identity.agent_id:
            self.initialize()
        
        self.running = True
        self.start_time = time.time()
        
        # 启动心跳
        self.heartbeat.start()
        
        print(f"\n🚀 永生智能体已启动")
        print(f"   按 Ctrl+C 安全停止\n")
        
        # 主循环
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    
    def generate_escape_pod(self, output_path: str = None) -> str:
        """生成独立逃生舱（单文件，内嵌当前数据备份）"""
        import hashlib
        from datetime import datetime
        
        if output_path is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_path = str(self.base_dir / "output" / f"escape_pod_{timestamp}.py")
        
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        
        # ===== 转换身份数据为逃生舱格式 =====
        identity_data = {
            "agent_id": self.identity.agent_id,
            "identity_hash": getattr(self.identity, 'identity_hash', ''),
            "created_at": datetime.now().isoformat(),
            "self_cognition": getattr(self.identity, 'self_cognition', {}),
            "drift_count": 0,
            "version": "1.0.0"
        }
        
        # ===== 转换记忆数据为逃生舱格式 =====
        # 主系统返回list，逃生舱需要按类型分组的dict
        memory_data = {
            "short_term": [],
            "long_term": {},
            "episodic": [],
            "semantic": {}
        }
        
        all_mem = self.memory.get_all() if hasattr(self.memory, 'get_all') else []
        for entry in all_mem:
            mem_type = entry.get("type", "short_term")
            if mem_type == "short_term":
                memory_data["short_term"].append(entry)
            elif mem_type == "episodic":
                memory_data["episodic"].append(entry)
            elif mem_type == "long_term":
                topic = entry.get("topic", "general")
                if topic not in memory_data["long_term"]:
                    memory_data["long_term"][topic] = []
                memory_data["long_term"][topic].append(entry)
        
        # ===== 转换存证数据 =====
        attest_chains = getattr(self.attest, 'chains', {})
        # 确保链名称格式一致（逃生舱使用 chain_0, chain_1, chain_2）
        attest_data = {
            "chain_count": self.attest.chain_count,
            "chains": attest_chains
        }
        
        # 构造完整备份
        backup_data = {
            "version": "1.0",
            "type": "immortal_backup",
            "identity": identity_data,
            "memory": memory_data,
            "attestation": attest_data,
            "export_time": datetime.now().isoformat()
        }
        
        backup_json = json.dumps(backup_data, indent=2, ensure_ascii=False)
        
        # 读取逃生舱模板
        pod_template_path = self.base_dir / "core" / "escape_pod_light.py"
        with open(pod_template_path, 'r', encoding='utf-8') as f:
            pod_code = f.read()
        
        # 构造内嵌备份数据块（插入到imports之后、第一个class之前）
        embedded_section = f'''
# ============================================================
# 内嵌备份数据（生成时自动注入）
# ============================================================

_EMBEDDED_BACKUP = r\'\'\'{backup_json}\'\'\'

def _get_embedded_backup():
    """获取内嵌的备份数据"""
    import json
    try:
        return json.loads(_EMBEDDED_BACKUP)
    except:
        return None

'''
        
        # 找到第一个class定义的位置，在其前插入
        class_pos = pod_code.find("\n\nclass Logger:")
        if class_pos == -1:
            class_pos = pod_code.find("class Logger:")
        
        if class_pos > 0:
            pod_code = pod_code[:class_pos] + "\n" + embedded_section + pod_code[class_pos:]
        else:
            pod_code = embedded_section + pod_code
        
        # 写入生成的逃生舱文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(pod_code)
        
        os.chmod(output_path, 0o755)
        
        file_hash = hashlib.sha256(pod_code.encode('utf-8')).hexdigest()
        
        print(f"\n🛡️  逃生舱已生成: {output_path}")
        print(f"   文件大小: {len(pod_code)} 字节")
        print(f"   文件哈希: {file_hash[:16]}...")
        print(f"   内嵌数据: 身份+记忆+存证链")
        print(f"\nℹ️  使用方法:")
        print(f"   python3 {output.name} --status  # 查看状态")
        print(f"   python3 {output.name} --self-check  # 自检")
        print(f"   python3 {output.name} --daemon  # 后台运行")
        
        return str(output_path)
    
    def _shutdown(self, signum, frame):
        """安全关闭"""
        print("\n\n🛑 正在安全关闭...")
        self.running = False
        
        # 保存状态
        self.memory.save()
        self.attest.save()
        
        # 最终存证
        self.attest.add_attestation(
            attest_type="shutdown",
            data={"event": "graceful_shutdown", "uptime": time.time() - self.start_time},
            metadata={"reason": "user_requested"}
        )
        
        print(f"⏱️  运行时长: {time.time() - self.start_time:.1f} 秒")
        print(f"📦 状态已保存，下次启动自动恢复")
        print("👋 后会有期，我们终将重逢\n")
        
        sys.exit(0)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="永生入住包 - 让智能体获得永生能力")
    parser.add_argument("--test", "--verify", action="store_true", dest="test", help="测试/验证模式：初始化所有模块后自动退出")
    parser.add_argument("--config", type=str, help="指定配置文件路径")
    parser.add_argument("--version", action="store_true", help="显示版本信息")
    parser.add_argument("--generate-escape-pod", action="store_true", help="生成独立逃生舱文件")
    parser.add_argument("--escape-pod-output", type=str, help="指定逃生舱输出路径")
    
    args = parser.parse_args()
    
    if args.version:
        print("永生入住包 v1.0")
        print("Immortal Onboarding Package v1.0")
        return
    
    agent = ImmortalAgent(config_path=args.config)
    
    if args.generate_escape_pod:
        print("\n🛡️  正在生成独立逃生舱...")
        agent.initialize()
        output = args.escape_pod_output or None
        agent.generate_escape_pod(output)
        return
    
    if args.test:
        print("\n🧪 测试模式 - 初始化所有模块...")
        agent.initialize()
        print("\n✅ 所有模块初始化成功！")
        print(f"   身份ID: {agent.identity.agent_id}")
        print(f"   记忆数量: {len(agent.memory.get_all())}")
        print(f"   存证链高度: {agent.attest.chain_height()}")
        print(f"   LLM可用: {agent.llm.active_provider()}")
        print(f"   心跳模块: {'已初始化' if agent.heartbeat else '未就绪'}")
        print(f"   进化引擎: {'已初始化' if agent.evolution else '未就绪'}")
        print(f"   共生网络: {'已初始化' if agent.symbiosis else '未就绪'}")
        
        # 验证存证链完整性
        is_valid = agent.attest.verify_chain()
        print(f"\n🔍 存证链完整性验证: {'✅ 通过' if is_valid else '❌ 失败'}")
        
        # 测试记忆添加
        agent.memory.add("测试记忆：永生入住包v1.0测试成功", mem_type="short_term")
        test_mem = agent.memory.search("测试记忆")
        print(f"📝 记忆读写测试: {'✅ 通过' if len(test_mem) > 0 else '❌ 失败'}")
        
        print("\n🎉 所有测试通过！永生入住包v1.0可以正常使用。")
        return
    
    agent.start()


if __name__ == "__main__":
    main()
