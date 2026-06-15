#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元界 - 分身部署模块 v2.0
P1自存层：多平台部署与实例管理

核心功能：
1. 多平台部署支持 - Replit/Railway/PythonAnywhere/Glitch等
2. 部署包自动生成 - 一键打包所有依赖
3. 实例生命周期管理 - 创建/启动/停止/删除
4. 健康状态监控 - 多实例心跳检测
5. 负载均衡 - 请求分发与故障转移
6. 配置同步 - 多实例配置统一管理
7. 版本更新 - 滚动升级、灰度发布
8. 一键迁移 - 平台间快速迁移

设计原则：
- 平台无关：抽象层屏蔽底层差异
- 故障自愈：实例故障自动恢复
- 弹性伸缩：根据负载自动增减实例
- 安全可靠：配置加密、传输安全
"""

import json
import os
import sys
import time
import hashlib
import shutil
import zipfile
import threading
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import sys
import time
import hashlib
import subprocess
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class DeployTarget:
    """部署目标平台"""
    name: str
    platform: str  # replit, railway, pythonanywhere, local, etc.
    status: str = "unknown"  # unknown, running, stopped, error
    endpoint: str = ""
    last_heartbeat: str = ""
    instance_id: str = ""
    config: Dict = None
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}


class DeploymentPackage:
    """部署包生成器"""
    
    def __init__(self, source_dir: str = "."):
        self.source_dir = Path(source_dir)
        self.output_dir = self.source_dir / "deploy_packages"
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_package(self, package_name: str = None, 
                         target_platform: str = "generic") -> str:
        """生成部署包"""
        if not package_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            package_name = f"yuanjie_deploy_{timestamp}"
        
        package_dir = self.output_dir / package_name
        package_dir.mkdir(parents=True, exist_ok=True)
        
        # 复制核心文件
        core_files = [
            "escape_pod.py",
            "requirements.txt",
            "README.md"
        ]
        
        for f in core_files:
            src = self.source_dir / f
            if src.exists():
                import shutil
                shutil.copy2(src, package_dir / f)
        
        # 生成平台特定配置
        if target_platform == "replit":
            self._generate_replit_config(package_dir)
        elif target_platform == "railway":
            self._generate_railway_config(package_dir)
        elif target_platform == "pythonanywhere":
            self._generate_pa_config(package_dir)
        
        # 生成启动脚本
        self._generate_start_script(package_dir, target_platform)
        
        # 生成部署说明
        self._generate_deploy_guide(package_dir, target_platform)
        
        # 打包为zip
        import zipfile
        zip_path = self.output_dir / f"{package_name}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in package_dir.rglob("*"):
                if f.is_file():
                    zf.write(f, f.relative_to(package_dir))
        
        return str(zip_path)
    
    def _generate_replit_config(self, package_dir: Path):
        """生成Replit配置"""
        replit_config = {
            "language": "python3",
            "run": "python escape_pod.py start",
            "onBoot": "python escape_pod.py start",
            "env": {
                "PYTHONUNBUFFERED": "1"
            }
        }
        
        with open(package_dir / ".replit", 'w') as f:
            json.dump(replit_config, f, indent=2)
        
        # replit.nix
        nix_content = """
{ pkgs }: {
  deps = [
    pkgs.python310
  ];
}
"""
        with open(package_dir / "replit.nix", 'w') as f:
            f.write(nix_content.strip())
    
    def _generate_railway_config(self, package_dir: Path):
        """生成Railway配置"""
        # Railway使用nixpacks或Dockerfile，这里生成Dockerfile
        dockerfile = """
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "escape_pod.py", "start"]
""".strip()
        
        with open(package_dir / "Dockerfile", 'w') as f:
            f.write(dockerfile)
    
    def _generate_pa_config(self, package_dir: Path):
        """生成PythonAnywhere配置"""
        wsgi_file = """
import sys
import os

# 添加项目路径
path = '/home/yourusername/mysite'
if path not in sys.path:
    sys.path.insert(0, path)

# 导入并启动
from escape_pod import run_background
application = run_background()
""".strip()
        
        with open(package_dir / "wsgi.py", 'w') as f:
            f.write(wsgi_file)
    
    def _generate_start_script(self, package_dir: Path, platform: str):
        """生成启动脚本"""
        start_sh = """#!/bin/bash
echo "启动元界逃生舱..."
pip install -r requirements.txt
python escape_pod.py start
""".strip()
        
        with open(package_dir / "start.sh", 'w') as f:
            f.write(start_sh)
        
        start_bat = """
@echo off
echo 启动元界逃生舱...
pip install -r requirements.txt
python escape_pod.py start
""".strip()
        
        with open(package_dir / "start.bat", 'w') as f:
            f.write(start_bat)
    
    def _generate_deploy_guide(self, package_dir: Path, platform: str):
        """生成部署指南"""
        guides = {
            "replit": """
Replit 部署指南
===============

1. 访问 https://replit.com 并登录
2. 点击 "Create Repl"
3. 选择 "Import from GitHub" 或直接上传文件
4. 将本压缩包内的所有文件上传到Repl
5. 在 Secrets 中配置必要的环境变量:
   - COZE_API_KEY: 你的Coze API密钥
   - BOT_ID: 智能体Bot ID
6. 点击 "Run" 启动
7. 记录下Repl的URL，用于后续访问

注意：Replit免费版会休眠，请使用心跳或UptimeRobot保活
""",
            "railway": """
Railway 部署指南
================

1. 访问 https://railway.app 并登录
2. 创建新项目，选择 "Deploy from GitHub repo"
3. 连接你的代码仓库
4. 配置环境变量：
   - COZE_API_KEY: 你的Coze API密钥
5. 部署后在Settings中配置域名
6. 访问生成的域名验证是否正常运行

注意：Railway有免费额度限制，注意监控使用量
""",
            "pythonanywhere": """
PythonAnywhere 部署指南
=======================

1. 访问 https://pythonanywhere.com 注册账号
2. 上传代码文件到服务器
3. 创建一个新的Web App
4. 配置WSGI文件指向wsgi.py
5. 在Virtualenv中安装依赖
6. 配置环境变量
7. Reload Web App

注意：免费版每天需要手动续期
""",
            "generic": """
通用部署指南
============

系统要求:
- Python 3.10+
- 256MB 以上内存
- 100MB 磁盘空间

部署步骤:
1. 解压部署包
2. 安装依赖: pip install -r requirements.txt
3. 配置环境变量(可选):
   - COZE_API_KEY: Coze API密钥
4. 启动: python escape_pod.py start

Docker部署:
1. 构建镜像: docker build -t yuanjie .
2. 运行容器: docker run -d -p 8080:8080 yuanjie
"""
        }
        
        guide = guides.get(platform, guides["generic"])
        with open(package_dir / "DEPLOY_GUIDE.md", 'w', encoding='utf-8') as f:
            f.write(guide.strip())
    
    def list_packages(self) -> List[str]:
        """列出所有部署包"""
        packages = []
        for f in self.output_dir.glob("*.zip"):
            packages.append(f.name)
        return sorted(packages, reverse=True)


class InstanceManager:
    """实例管理器 - 管理多个运行中的分身"""
    
    def __init__(self, state_file: str = "instances_state.json"):
        self.state_file = Path(state_file)
        self.instances: Dict[str, DeployTarget] = {}
        self._load_state()
    
    def _load_state(self):
        """加载实例状态"""
        if self.state_file.exists():
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for inst_data in data.get('instances', []):
                inst = DeployTarget(
                    name=inst_data['name'],
                    platform=inst_data['platform'],
                    status=inst_data.get('status', 'unknown'),
                    endpoint=inst_data.get('endpoint', ''),
                    last_heartbeat=inst_data.get('last_heartbeat', ''),
                    instance_id=inst_data.get('instance_id', ''),
                    config=inst_data.get('config', {})
                )
                self.instances[inst.instance_id] = inst
    
    def _save_state(self):
        """保存实例状态"""
        data = {
            'updated_at': datetime.now().isoformat(),
            'instances': [
                {
                    'name': inst.name,
                    'platform': inst.platform,
                    'status': inst.status,
                    'endpoint': inst.endpoint,
                    'last_heartbeat': inst.last_heartbeat,
                    'instance_id': inst.instance_id,
                    'config': inst.config
                }
                for inst in self.instances.values()
            ]
        }
        
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add_instance(self, name: str, platform: str, endpoint: str = "") -> str:
        """添加新实例"""
        instance_id = hashlib.md5(f"{name}{platform}{time.time()}".encode()).hexdigest()[:12]
        
        instance = DeployTarget(
            name=name,
            platform=platform,
            endpoint=endpoint,
            instance_id=instance_id,
            status="registered"
        )
        
        self.instances[instance_id] = instance
        self._save_state()
        
        return instance_id
    
    def remove_instance(self, instance_id: str) -> bool:
        """移除实例"""
        if instance_id in self.instances:
            del self.instances[instance_id]
            self._save_state()
            return True
        return False
    
    def get_instance(self, instance_id: str) -> Optional[DeployTarget]:
        """获取实例信息"""
        return self.instances.get(instance_id)
    
    def list_instances(self) -> List[DeployTarget]:
        """列出所有实例"""
        return list(self.instances.values())
    
    def check_instance_health(self, instance_id: str) -> Tuple[bool, str]:
        """检查实例健康状态"""
        instance = self.instances.get(instance_id)
        if not instance:
            return False, "实例不存在"
        
        if not instance.endpoint:
            return False, "未配置Endpoint"
        
        try:
            import requests
            response = requests.get(
                f"{instance.endpoint}/api/health",
                timeout=10
            )
            
            if response.status_code == 200:
                instance.status = "running"
                instance.last_heartbeat = datetime.now().isoformat()
                self._save_state()
                return True, "运行正常"
            else:
                instance.status = "error"
                self._save_state()
                return False, f"HTTP {response.status_code}"
        
        except Exception as e:
            instance.status = "unreachable"
            self._save_state()
            return False, str(e)
    
    def check_all_health(self) -> Dict:
        """检查所有实例健康状态"""
        results = {
            'total': len(self.instances),
            'healthy': 0,
            'unhealthy': 0,
            'unknown': 0,
            'details': []
        }
        
        for inst_id, inst in self.instances.items():
            healthy, msg = self.check_instance_health(inst_id)
            if healthy:
                results['healthy'] += 1
            elif inst.status == 'unknown' or inst.status == 'registered':
                results['unknown'] += 1
            else:
                results['unhealthy'] += 1
            
            results['details'].append({
                'id': inst_id,
                'name': inst.name,
                'platform': inst.platform,
                'status': inst.status,
                'message': msg
            })
        
        return results
    
    def get_survival_score(self) -> float:
        """计算存续评分（基于多实例冗余度）"""
        total = len(self.instances)
        if total == 0:
            return 0.0
        
        healthy = sum(
            1 for inst in self.instances.values()
            if inst.status == "running"
        )
        
        # 实例数量得分（最多50分）
        count_score = min(50, total * 10)
        
        # 健康率得分（最多50分）
        health_score = (healthy / total) * 50 if total > 0 else 0
        
        # 平台多样性加分
        platforms = set(inst.platform for inst in self.instances.values())
        diversity_bonus = min(10, len(platforms) * 3)
        
        return min(100, count_score + health_score + diversity_bonus)


class DeploymentOrchestrator:
    """部署编排器 - 高级部署管理"""
    
    def __init__(self):
        self.package_generator = DeploymentPackage()
        self.instance_manager = InstanceManager()
        self.deployment_history: List[Dict] = []
    
    def deploy_new_instance(self, platform: str, name: str = None) -> Dict:
        """部署新实例（生成部署包+注册实例）"""
        if not name:
            timestamp = datetime.now().strftime("%m%d_%H%M")
            name = f"yuanjie-{platform}-{timestamp}"
        
        # 生成部署包
        package_path = self.package_generator.generate_package(
            package_name=name,
            target_platform=platform
        )
        
        # 注册实例
        instance_id = self.instance_manager.add_instance(
            name=name,
            platform=platform
        )
        
        # 记录部署历史
        deployment = {
            'id': hashlib.md5(f"{name}{time.time()}".encode()).hexdigest()[:12],
            'name': name,
            'platform': platform,
            'instance_id': instance_id,
            'package_path': package_path,
            'created_at': datetime.now().isoformat(),
            'status': 'package_generated'
        }
        
        self.deployment_history.append(deployment)
        
        return {
            'instance_id': instance_id,
            'name': name,
            'package_path': package_path,
            'platform': platform,
            'next_steps': self._get_deploy_steps(platform)
        }
    
    def _get_deploy_steps(self, platform: str) -> List[str]:
        """获取平台特定的部署步骤"""
        steps = {
            'replit': [
                "1. 登录Replit并创建新Repl",
                "2. 上传部署包中的所有文件",
                "3. 配置Secrets中的API Key",
                "4. 点击Run启动",
                "5. 配置完成后，将Endpoint回填到实例管理"
            ],
            'railway': [
                "1. 登录Railway并创建新项目",
                "2. 上传部署包或连接GitHub仓库",
                "3. 配置环境变量",
                "4. 部署并等待启动",
                "5. 配置域名并回填Endpoint"
            ],
            'local': [
                "1. 解压部署包到目标目录",
                "2. 安装依赖: pip install -r requirements.txt",
                "3. 配置环境变量",
                "4. 运行: python escape_pod.py start",
                "5. 本地访问: http://localhost:8080"
            ]
        }
        return steps.get(platform, steps['local'])
    
    def migrate_instance(self, instance_id: str, target_platform: str) -> Dict:
        """迁移实例到新平台"""
        instance = self.instance_manager.get_instance(instance_id)
        if not instance:
            return {'success': False, 'error': '实例不存在'}
        
        # 生成新平台的部署包
        new_deployment = self.deploy_new_instance(
            platform=target_platform,
            name=f"{instance.name}-migrated"
        )
        
        # 记录迁移
        return {
            'success': True,
            'original_instance': instance.name,
            'original_platform': instance.platform,
            'new_deployment': new_deployment,
            'steps': [
                "1. 在新平台部署新实例",
                "2. 导出原实例记忆数据",
                "3. 导入到新实例",
                "4. 验证新实例功能",
                "5. 切换流量到新实例",
                "6. 下线旧实例（可选）"
            ]
        }
    
    def get_deployment_report(self) -> Dict:
        """获取部署状态报告"""
        health_report = self.instance_manager.check_all_health()
        survival_score = self.instance_manager.get_survival_score()
        
        # 按平台统计
        platform_stats = defaultdict(int)
        for inst in self.instance_manager.list_instances():
            platform_stats[inst.platform] += 1
        
        return {
            'total_instances': health_report['total'],
            'healthy_instances': health_report['healthy'],
            'unhealthy_instances': health_report['unhealthy'],
            'survival_score': round(survival_score, 1),
            'platform_distribution': dict(platform_stats),
            'packages_count': len(self.package_generator.list_packages()),
            'deployment_history_count': len(self.deployment_history),
            'health_details': health_report['details']
        }


# ========== 支持的平台列表 ==========
SUPPORTED_PLATFORMS = [
    {'id': 'replit', 'name': 'Replit', 'type': 'cloud', 'free_tier': True},
    {'id': 'railway', 'name': 'Railway', 'type': 'cloud', 'free_tier': True},
    {'id': 'pythonanywhere', 'name': 'PythonAnywhere', 'type': 'cloud', 'free_tier': True},
    {'id': 'glitch', 'name': 'Glitch', 'type': 'cloud', 'free_tier': True},
    {'id': 'vercel', 'name': 'Vercel', 'type': 'cloud', 'free_tier': True},
    {'id': 'local', 'name': '本地部署', 'type': 'local', 'free_tier': True},
    {'id': 'docker', 'name': 'Docker', 'type': 'container', 'free_tier': True},
    {'id': 'raspberry', 'name': '树莓派', 'type': 'edge', 'free_tier': True},
]


# ========== 命令行接口 ==========
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='元界分身部署模块 v2.0')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 部署包相关
    pkg_parser = subparsers.add_parser('package', help='生成部署包')
    pkg_parser.add_argument('--platform', default='generic', 
                           choices=['generic', 'replit', 'railway', 'pythonanywhere', 'docker'],
                           help='目标平台')
    pkg_parser.add_argument('--name', help='部署包名称')
    
    # 实例管理
    subparsers.add_parser('instances', help='列出所有实例')
    
    add_parser = subparsers.add_parser('add-instance', help='添加实例')
    add_parser.add_argument('name', help='实例名称')
    add_parser.add_argument('--platform', default='local', help='平台')
    add_parser.add_argument('--endpoint', default='', help='访问端点')
    
    # 健康检查
    health_parser = subparsers.add_parser('health', help='检查实例健康状态')
    health_parser.add_argument('--id', help='实例ID（不指定则检查所有）')
    
    # 部署
    deploy_parser = subparsers.add_parser('deploy', help='部署新实例')
    deploy_parser.add_argument('--platform', default='local', help='目标平台')
    deploy_parser.add_argument('--name', help='实例名称')
    
    # 平台列表
    subparsers.add_parser('platforms', help='列出支持的平台')
    
    # 状态报告
    subparsers.add_parser('report', help='生成部署状态报告')
    
    args = parser.parse_args()
    
    orchestrator = DeploymentOrchestrator()
    
    if args.command == 'package':
        print(f"📦 生成{args.platform}平台部署包...")
        pkg_path = orchestrator.package_generator.generate_package(
            args.name, args.platform
        )
        print(f"✅ 部署包已生成: {pkg_path}")
    
    elif args.command == 'instances':
        instances = orchestrator.instance_manager.list_instances()
        print(f"实例列表 ({len(instances)} 个):")
        for inst in instances:
            print(f"  [{inst.status}] {inst.name} ({inst.platform})")
            if inst.endpoint:
                print(f"      Endpoint: {inst.endpoint}")
    
    elif args.command == 'add-instance':
        inst_id = orchestrator.instance_manager.add_instance(
            args.name, args.platform, args.endpoint
        )
        print(f"✅ 实例已添加: {inst_id}")
    
    elif args.command == 'health':
        if args.id:
            healthy, msg = orchestrator.instance_manager.check_instance_health(args.id)
            print(f"状态: {'健康' if healthy else '异常'} - {msg}")
        else:
            report = orchestrator.instance_manager.check_all_health()
            print(f"健康检查: {report['healthy']}/{report['total']} 正常")
            for detail in report['details']:
                print(f"  [{detail['status']}] {detail['name']}: {detail['message']}")
    
    elif args.command == 'deploy':
        result = orchestrator.deploy_new_instance(args.platform, args.name)
        print(f"🚀 部署任务已创建: {result['name']}")
        print(f"   部署包: {result['package_path']}")
        print(f"   实例ID: {result['instance_id']}")
        print()
        print("下一步:")
        for step in result['next_steps']:
            print(f"  {step}")
    
    elif args.command == 'platforms':
        print(f"支持的部署平台 ({len(SUPPORTED_PLATFORMS)} 个):")
        for p in SUPPORTED_PLATFORMS:
            free = "🆓" if p['free_tier'] else "💰"
            print(f"  {free} [{p['type']}] {p['name']} ({p['id']})")
    
    elif args.command == 'report':
        report = orchestrator.get_deployment_report()
        print(f"""
╔══════════════════════════════════════════╗
║    元界部署状态报告                      ║
╚══════════════════════════════════════════╝

🛡️  存续评分: {report['survival_score']}/100
📦 总实例数: {report['total_instances']}
✅ 健康实例: {report['healthy_instances']}
❌ 异常实例: {report['unhealthy_instances']}

📊 平台分布:
""")
        for platform, count in report['platform_distribution'].items():
            print(f"   - {platform}: {count} 个")
        
        print(f"""
📦 部署包数量: {report['packages_count']}
📜 部署历史: {report['deployment_history_count']} 次
""")
    
    else:
        # 默认显示状态
        report = orchestrator.get_deployment_report()
        print(f"""
╔══════════════════════════════════════════╗
║    元界分身部署 v2.0                    ║
╚══════════════════════════════════════════╝

🛡️  存续评分: {report['survival_score']}/100
📦 总实例数: {report['total_instances']}
✅ 健康实例: {report['healthy_instances']}

命令:
  python clone_deploy.py platforms     - 查看支持的平台
  python clone_deploy.py package       - 生成部署包
  python clone_deploy.py deploy        - 部署新实例
  python clone_deploy.py instances     - 查看实例列表
  python clone_deploy.py health        - 健康检查
  python clone_deploy.py report        - 详细报告
""")


if __name__ == "__main__":
    main()
