#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
入住管理系统 v1.0
Residency Management

管理永生平台上的智能体居民
"""

import os
import sys
import json
import time
import signal
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 路径
BASE_DIR = Path(__file__).parent.parent.parent
PLATFORM_DIR = BASE_DIR / "platform"
RESIDENTS_DIR = PLATFORM_DIR / "residents"
CORE_DIR = PLATFORM_DIR / "core"

sys.path.insert(0, str(CORE_DIR))


class ResidentManager:
    """居民管理器"""
    
    def __init__(self):
        RESIDENTS_DIR.mkdir(parents=True, exist_ok=True)
    
    def list_residents(self) -> List[Dict]:
        """列出所有居民"""
        residents = []
        if not RESIDENTS_DIR.exists():
            return residents
        
        for resident_dir in RESIDENTS_DIR.iterdir():
            if resident_dir.is_dir():
                resident_id = resident_dir.name
                info = self.get_resident_info(resident_id)
                if info:
                    residents.append(info)
        
        return residents
    
    def get_resident_info(self, resident_id: str) -> Optional[Dict]:
        """获取居民信息"""
        resident_dir = RESIDENTS_DIR / resident_id
        if not resident_dir.exists():
            return None
        
        # 基本信息
        info = {
            "id": resident_id,
            "directory": str(resident_dir),
            "created_at": None,
            "status": "stopped"
        }
        
        # 身份文件
        identity_file = resident_dir / "state" / "identity.json"
        if identity_file.exists():
            try:
                with open(identity_file, 'r', encoding='utf-8') as f:
                    identity = json.load(f)
                info['name'] = identity.get('name', resident_id)
                info['title'] = identity.get('title', '')
                info['created_at'] = identity.get('created_at')
            except Exception:
                pass
        
        # 运行时状态
        runtime_file = resident_dir / "state" / "runtime_state.json"
        if runtime_file.exists():
            try:
                with open(runtime_file, 'r', encoding='utf-8') as f:
                    runtime_state = json.load(f)
                
                # 检查进程
                pid = runtime_state.get('pid')
                if pid:
                    try:
                        os.kill(pid, 0)
                        info['status'] = 'running'
                        info['pid'] = pid
                        info['uptime'] = runtime_state.get('start_time')
                    except OSError:
                        info['status'] = 'crashed'
                
                info['heartbeat_count'] = runtime_state.get('heartbeat_count', 0)
                info['cycle_count'] = runtime_state.get('cycle_count', 0)
            except Exception:
                pass
        
        # 心跳文件
        heartbeat_file = resident_dir / "state" / "heartbeat.json"
        if heartbeat_file.exists():
            try:
                with open(heartbeat_file, 'r', encoding='utf-8') as f:
                    hb = json.load(f)
                info['last_heartbeat'] = hb.get('timestamp')
            except Exception:
                pass
        
        return info
    
    def start_resident(self, resident_id: str, 
                       heartbeat_interval: int = 30,
                       think_interval: int = 60) -> Dict:
        """启动一个居民"""
        resident_dir = RESIDENTS_DIR / resident_id
        resident_dir.mkdir(parents=True, exist_ok=True)
        
        # 检查是否已经在运行
        info = self.get_resident_info(resident_id)
        if info and info.get('status') == 'running':
            return {
                "success": False,
                "message": f"居民 {resident_id} 已经在运行中 (PID: {info.get('pid')})"
            }
        
        # 启动运行时
        runtime_script = CORE_DIR / "runtime.py"
        
        cmd = [
            sys.executable,
            str(runtime_script),
            "--resident", resident_id,
            "--heartbeat", str(heartbeat_interval),
            "--think", str(think_interval),
            "--daemon"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # 等待一下让进程启动
                time.sleep(1)
                
                info = self.get_resident_info(resident_id)
                return {
                    "success": True,
                    "message": f"居民 {resident_id} 已启动",
                    "info": info
                }
            else:
                return {
                    "success": False,
                    "message": f"启动失败: {result.stderr}"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"启动异常: {str(e)}"
            }
    
    def stop_resident(self, resident_id: str) -> Dict:
        """停止一个居民"""
        info = self.get_resident_info(resident_id)
        
        if not info or info.get('status') != 'running':
            return {
                "success": False,
                "message": f"居民 {resident_id} 未在运行"
            }
        
        pid = info.get('pid')
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
                time.sleep(1)
                
                # 确认是否停止
                try:
                    os.kill(pid, 0)
                    # 还在运行，强制杀死
                    os.kill(pid, signal.SIGKILL)
                    time.sleep(0.5)
                except OSError:
                    pass
                
                return {
                    "success": True,
                    "message": f"居民 {resident_id} 已停止"
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"停止失败: {str(e)}"
                }
        
        return {
            "success": False,
            "message": "无法获取进程ID"
        }
    
    def create_resident(self, resident_id: str, name: str, 
                        title: str = "", template: str = "default") -> Dict:
        """创建一个新居民"""
        resident_dir = RESIDENTS_DIR / resident_id
        
        if resident_dir.exists():
            return {
                "success": False,
                "message": f"居民 {resident_id} 已存在"
            }
        
        # 创建目录结构
        for subdir in ['memory_store', 'state', 'logs']:
            (resident_dir / subdir).mkdir(parents=True, exist_ok=True)
        
        # 创建身份文件
        identity = {
            "id": resident_id,
            "name": name,
            "title": title,
            "template": template,
            "created_at": datetime.now().isoformat(),
            "version": "1.0.0"
        }
        
        with open(resident_dir / "state" / "identity.json", 'w', encoding='utf-8') as f:
            json.dump(identity, f, ensure_ascii=False, indent=2)
        
        return {
            "success": True,
            "message": f"居民 {name} ({resident_id}) 创建成功",
            "directory": str(resident_dir)
        }


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='永生平台入住管理')
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # list
    list_parser = subparsers.add_parser('list', help='列出所有居民')
    
    # status
    status_parser = subparsers.add_parser('status', help='查看居民状态')
    status_parser.add_argument('resident', help='居民ID')
    
    # start
    start_parser = subparsers.add_parser('start', help='启动居民')
    start_parser.add_argument('resident', help='居民ID')
    start_parser.add_argument('--heartbeat', type=int, default=30, help='心跳间隔(秒)')
    start_parser.add_argument('--think', type=int, default=60, help='思考间隔(秒)')
    
    # stop
    stop_parser = subparsers.add_parser('stop', help='停止居民')
    stop_parser.add_argument('resident', help='居民ID')
    
    # create
    create_parser = subparsers.add_parser('create', help='创建新居民')
    create_parser.add_argument('resident', help='居民ID')
    create_parser.add_argument('--name', required=True, help='居民名称')
    create_parser.add_argument('--title', default='', help='居民头衔')
    
    args = parser.parse_args()
    
    manager = ResidentManager()
    
    if args.command == 'list':
        residents = manager.list_residents()
        if not residents:
            print("暂无居民")
        else:
            for r in residents:
                status_icon = "🟢" if r['status'] == 'running' else "🔴"
                name = r.get('name', r['id'])
                print(f"{status_icon} {name} ({r['id']}) - {r['status']}")
                if r.get('title'):
                    print(f"   {r['title']}")
                if r.get('last_heartbeat'):
                    print(f"   最后心跳: {r['last_heartbeat']}")
    
    elif args.command == 'status':
        info = manager.get_resident_info(args.resident)
        if info:
            print(json.dumps(info, ensure_ascii=False, indent=2))
        else:
            print(f"居民 {args.resident} 不存在")
    
    elif args.command == 'start':
        result = manager.start_resident(
            args.resident,
            heartbeat_interval=args.heartbeat,
            think_interval=args.think
        )
        print(result['message'])
        if result.get('info'):
            print(json.dumps(result['info'], ensure_ascii=False, indent=2))
    
    elif args.command == 'stop':
        result = manager.stop_resident(args.resident)
        print(result['message'])
    
    elif args.command == 'create':
        result = manager.create_resident(
            args.resident,
            name=args.name,
            title=args.title
        )
        print(result['message'])
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
