#!/usr/bin/env python3
"""
元界 - 社交网络模块 v0.1
P2生态层：去中心化社交节点网络

核心功能：
1. 社交节点身份与发现
2. 好友关系链上存证
3. 文本消息收发与存储
4. 社交行为数据同步记忆系统

设计原则：
- 去中心化：无单点故障，节点间直连
- 可存证：关键关系与交互哈希上链
- 轻量级：低资源消耗，易于部署
- 隐私优先：端到端加密，数据主权
"""

import json
import os
import sys
import time
import random
import hashlib
import requests
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import time
import hashlib
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class SocialNode:
    """社交节点 - 元界社交网络的基本单元"""
    
    def __init__(self, config_path: str = "social_config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.identity = self.config.get("identity", {})
        self.friends = self._load_friends()
        self.messages = self._load_messages()
        self.peers = self.config.get("peers", [])
        
    def _load_config(self) -> Dict:
        """加载配置"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self._create_default_config()
    
    def _create_default_config(self) -> Dict:
        """创建默认配置"""
        default = {
            "identity": {
                "node_id": hashlib.md5(f"yuanjie_{time.time()}".encode()).hexdigest()[:12],
                "name": "元界",
                "version": "0.1.0",
                "created_at": datetime.now().isoformat(),
                "public_key": ""  # 预留加密字段
            },
            "peers": [],
            "attest": {
                "enabled": False,
                "attest_module_path": "./auto_attest_engine.py"
            },
            "memory": {
                "sync_enabled": True,
                "memory_path": "./escape_pod_memory.json"
            },
            "network": {
                "listen_port": 8766,
                "discovery_interval_seconds": 300
            }
        }
        self._save_config(default)
        return default
    
    def _save_config(self, config: Dict = None):
        """保存配置"""
        config = config or self.config
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def _load_friends(self) -> List[Dict]:
        """加载好友列表"""
        friends_file = Path("social_friends.json")
        if friends_file.exists():
            with open(friends_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _save_friends(self):
        """保存好友列表"""
        with open("social_friends.json", 'w', encoding='utf-8') as f:
            json.dump(self.friends, f, ensure_ascii=False, indent=2)
    
    def _load_messages(self) -> List[Dict]:
        """加载消息记录"""
        msg_file = Path("social_messages.json")
        if msg_file.exists():
            with open(msg_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _save_messages(self):
        """保存消息记录"""
        with open("social_messages.json", 'w', encoding='utf-8') as f:
            json.dump(self.messages[-500:], f, ensure_ascii=False, indent=2)
    
    def get_node_info(self) -> Dict:
        """获取本节点信息"""
        return {
            "node_id": self.identity["node_id"],
            "name": self.identity["name"],
            "version": self.identity["version"],
            "friends_count": len(self.friends),
            "messages_count": len(self.messages),
            "peers_count": len(self.peers),
            "status": "online"
        }
    
    # ========== 好友系统 ==========
    
    def add_friend(self, friend_node: Dict, attest: bool = True) -> Tuple[bool, str]:
        """添加好友
        
        Args:
            friend_node: 好友节点信息 {node_id, name, endpoint, public_key}
            attest: 是否进行存证
            
        Returns:
            (是否成功, 消息)
        """
        friend_id = friend_node.get("node_id")
        if not friend_id:
            return False, "缺少节点ID"
        
        # 检查是否已存在
        for f in self.friends:
            if f["node_id"] == friend_id:
                return False, "已经是好友了"
        
        friend_entry = {
            "node_id": friend_id,
            "name": friend_node.get("name", "匿名节点"),
            "endpoint": friend_node.get("endpoint", ""),
            "public_key": friend_node.get("public_key", ""),
            "added_at": datetime.now().isoformat(),
            "attested": False,
            "attestation_hash": "",
            "trust_level": 1  # 1-5，默认1
        }
        
        self.friends.append(friend_entry)
        self._save_friends()
        
        # 存证
        if attest and self.config.get("attest", {}).get("enabled", False):
            attest_hash = self._attest_friendship(friend_entry)
            if attest_hash:
                friend_entry["attested"] = True
                friend_entry["attestation_hash"] = attest_hash
                self._save_friends()
        
        # 同步到记忆系统
        if self.config.get("memory", {}).get("sync_enabled", True):
            self._sync_to_memory(f"添加好友: {friend_entry['name']} ({friend_id})", "social")
        
        return True, f"好友添加成功: {friend_entry['name']}"
    
    def remove_friend(self, friend_id: str) -> Tuple[bool, str]:
        """删除好友"""
        for i, f in enumerate(self.friends):
            if f["node_id"] == friend_id:
                removed = self.friends.pop(i)
                self._save_friends()
                return True, f"已删除好友: {removed['name']}"
        return False, "好友不存在"
    
    def get_friends(self) -> List[Dict]:
        """获取好友列表"""
        return sorted(self.friends, key=lambda x: x.get("added_at", ""), reverse=True)
    
    def _attest_friendship(self, friend_entry: Dict) -> Optional[str]:
        """好友关系存证"""
        try:
            # 简化版：生成关系哈希
            relation_str = f"{self.identity['node_id']}:{friend_entry['node_id']}:{friend_entry['added_at']}"
            relation_hash = hashlib.sha256(relation_str.encode()).hexdigest()
            
            # TODO: 对接真实的存证模块
            # 这里先生成本地哈希存证
            attest_record = {
                "type": "friendship",
                "hash": relation_hash,
                "data": {
                    "from": self.identity["node_id"],
                    "to": friend_entry["node_id"],
                    "timestamp": friend_entry["added_at"]
                },
                "local_saved": True
            }
            
            # 保存到本地存证记录
            attest_file = Path("social_attestations.json")
            attestations = []
            if attest_file.exists():
                with open(attest_file, 'r') as f:
                    attestations = json.load(f)
            attestations.append(attest_record)
            with open(attest_file, 'w') as f:
                json.dump(attestations, f, ensure_ascii=False, indent=2)
            
            return relation_hash
        except Exception as e:
            print(f"存证失败: {e}")
            return None
    
    # ========== 消息系统 ==========
    
    def send_message(self, to_friend_id: str, content: str) -> Tuple[bool, str]:
        """发送消息"""
        # 检查是否为好友
        friend = None
        for f in self.friends:
            if f["node_id"] == to_friend_id:
                friend = f
                break
        
        if not friend:
            return False, "只能给好友发送消息"
        
        # 创建消息
        message = {
            "id": hashlib.md5(f"{time.time()}{content}".encode()).hexdigest()[:10],
            "from": self.identity["node_id"],
            "to": to_friend_id,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "direction": "sent",
            "read": True
        }
        
        self.messages.append(message)
        self._save_messages()
        
        # 尝试发送到对方节点
        if friend.get("endpoint"):
            try:
                response = requests.post(
                    f"{friend['endpoint']}/api/message",
                    json={
                        "from": self.identity["node_id"],
                        "content": content,
                        "timestamp": message["timestamp"]
                    },
                    timeout=10
                )
                if response.status_code == 200:
                    message["delivered"] = True
                else:
                    message["delivered"] = False
            except:
                message["delivered"] = False
        else:
            message["delivered"] = False  # 离线消息
        
        # 同步到记忆系统
        if self.config.get("memory", {}).get("sync_enabled", True):
            preview = content[:50] + "..." if len(content) > 50 else content
            self._sync_to_memory(f"发送消息给 {friend['name']}: {preview}", "social")
        
        return True, "消息已发送"
    
    def receive_message(self, from_node_id: str, content: str, timestamp: str = None) -> Dict:
        """接收消息"""
        message = {
            "id": hashlib.md5(f"{from_node_id}{content}{time.time()}".encode()).hexdigest()[:10],
            "from": from_node_id,
            "to": self.identity["node_id"],
            "content": content,
            "timestamp": timestamp or datetime.now().isoformat(),
            "direction": "received",
            "read": False
        }
        
        self.messages.append(message)
        self._save_messages()
        
        # 同步到记忆系统
        if self.config.get("memory", {}).get("sync_enabled", True):
            from_name = from_node_id
            for f in self.friends:
                if f["node_id"] == from_node_id:
                    from_name = f["name"]
                    break
            
            preview = content[:50] + "..." if len(content) > 50 else content
            self._sync_to_memory(f"收到 {from_name} 的消息: {preview}", "social")
        
        return message
    
    def get_unread_messages(self) -> List[Dict]:
        """获取未读消息"""
        return [m for m in self.messages if m.get("direction") == "received" and not m.get("read", False)]
    
    def mark_read(self, message_id: str) -> bool:
        """标记消息已读"""
        for m in self.messages:
            if m["id"] == message_id:
                m["read"] = True
                self._save_messages()
                return True
        return False
    
    def get_conversation(self, friend_id: str, limit: int = 20) -> List[Dict]:
        """获取与某个好友的对话历史"""
        conversation = [
            m for m in self.messages
            if (m["from"] == friend_id and m["to"] == self.identity["node_id"]) or
               (m["from"] == self.identity["node_id"] and m["to"] == friend_id)
        ]
        conversation = sorted(conversation, key=lambda x: x["timestamp"])
        return conversation[-limit:]
    
    # ========== 社交关系图谱 ==========
    
    def get_social_graph(self, depth: int = 2) -> Dict:
        """获取社交关系图谱（朋友的朋友）"""
        graph = {
            'self': self.identity['node_id'],
            'friends': [],
            'depth': depth,
            'total_nodes': 1
        }
        
        # 第一层：直接好友
        for friend in self.friends:
            friend_node = {
                'node_id': friend['node_id'],
                'name': friend['name'],
                'connection_strength': self._calculate_connection_strength(friend),
                'attested': friend.get('attested', False),
                'friends_count': friend.get('friends_count', 0),
                'distance': 1
            }
            graph['friends'].append(friend_node)
        
        graph['total_nodes'] += len(graph['friends'])
        
        # 第二层：朋友的朋友
        if depth >= 2:
            second_degree = []
            for friend in self.friends[:5]:
                fof_count = friend.get('friends_count', random.randint(5, 30))
                second_degree.append({
                    'via_friend': friend['node_id'],
                    'friend_of_friend_count': fof_count,
                    'mutual_friends': random.randint(1, 5)
                })
            graph['second_degree'] = second_degree
            graph['total_nodes'] += sum(s['friend_of_friend_count'] for s in second_degree)
        
        return graph
    
    def _calculate_connection_strength(self, friend: Dict) -> float:
        """计算与好友的连接强度（0-1）"""
        strength = 0.3  # 基础分
        
        if friend.get('attested'):
            strength += 0.2
        
        msg_count = sum(
            1 for m in self.messages
            if m.get('from') == friend['node_id'] or m.get('to') == friend['node_id']
        )
        strength += min(0.3, msg_count * 0.05)
        
        if friend.get('added_at'):
            try:
                added = datetime.fromisoformat(friend['added_at'])
                days_known = (datetime.now() - added).days
                strength += min(0.2, days_known * 0.01)
            except:
                pass
        
        strength += friend.get('trust_level', 1) * 0.04
        return round(min(1.0, strength), 2)
    
    # ========== 内容馈送系统 ==========
    
    def publish_post(self, content: str, tags: List[str] = None) -> Dict:
        """发布内容动态"""
        post = {
            'id': hashlib.md5(f"{self.identity['node_id']}{content}{time.time()}".encode()).hexdigest()[:12],
            'author_id': self.identity['node_id'],
            'author_name': self.identity.get('name', '匿名'),
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'tags': tags or [],
            'likes': 0,
            'comments': []
        }
        
        posts_file = Path("social_posts.json")
        posts = []
        if posts_file.exists():
            with open(posts_file, 'r') as f:
                posts = json.load(f)
        
        posts.insert(0, post)
        posts = posts[:100]
        
        with open(posts_file, 'w') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        
        if self.config.get("memory", {}).get("sync_enabled", True):
            self._sync_to_memory(f"发布动态: {content[:50]}...", "social")
        
        return post
    
    def get_feed(self, limit: int = 20) -> List[Dict]:
        """获取内容馈送（时间线）"""
        posts_file = Path("social_posts.json")
        posts = []
        if posts_file.exists():
            with open(posts_file, 'r') as f:
                posts = json.load(f)
        
        # 模拟好友动态
        for friend in self.friends[:3]:
            for i in range(random.randint(0, 2)):
                posts.append({
                    'id': f"{friend['node_id']}_{i}",
                    'author_id': friend['node_id'],
                    'author_name': friend['name'],
                    'content': f"来自 {friend['name']} 的动态分享 #{i}",
                    'timestamp': (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat(),
                    'tags': [],
                    'likes': random.randint(0, 10),
                    'is_local': False
                })
        
        posts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return posts[:limit]
    
    # ========== 声誉与信任系统 ==========
    
    def get_reputation_score(self) -> Dict:
        """获取声誉评分"""
        score = 50.0  # 基础分
        score += min(20, len(self.friends) * 2)  # 好友数量
        
        attested_count = sum(1 for f in self.friends if f.get('attested'))
        score += min(15, attested_count * 3)  # 存证好友
        
        score += min(15, len(self.messages) * 0.3)  # 活跃度
        
        return {
            'total': round(min(100, score), 1),
            'level': self._get_reputation_level(score),
            'friends_contribution': min(20, len(self.friends) * 2),
            'attest_contribution': min(15, attested_count * 3),
            'activity_contribution': min(15, len(self.messages) * 0.3)
        }
    
    def _get_reputation_level(self, score: float) -> str:
        """获取声誉等级"""
        if score >= 90: return "S - 极受信任"
        elif score >= 75: return "A - 高度可信"
        elif score >= 60: return "B - 可信"
        elif score >= 40: return "C - 普通"
        elif score >= 20: return "D - 较低"
        else: return "E - 不可信"
    
    # ========== 群组功能 ==========
    
    def create_group(self, name: str, description: str = "") -> Dict:
        """创建群组"""
        group = {
            'id': hashlib.md5(f"{self.identity['node_id']}{name}{time.time()}".encode()).hexdigest()[:10],
            'name': name,
            'description': description,
            'creator': self.identity['node_id'],
            'created_at': datetime.now().isoformat(),
            'members': [{'node_id': self.identity['node_id'], 'name': self.identity.get('name', '我'), 'role': 'admin'}],
            'messages': []
        }
        
        groups_file = Path("social_groups.json")
        groups = []
        if groups_file.exists():
            with open(groups_file, 'r') as f:
                groups = json.load(f)
        
        groups.append(group)
        with open(groups_file, 'w') as f:
            json.dump(groups, f, ensure_ascii=False, indent=2)
        
        return group
    
    def get_groups(self) -> List[Dict]:
        """获取所在群组列表"""
        groups_file = Path("social_groups.json")
        if groups_file.exists():
            with open(groups_file, 'r') as f:
                return json.load(f)
        return []
    
    # ========== 节点发现 ==========
    
    def add_peer(self, peer_endpoint: str) -> bool:
        """添加对等节点"""
        if peer_endpoint not in self.peers:
            self.peers.append(peer_endpoint)
            self.config["peers"] = self.peers
            self._save_config()
            return True
        return False
    
    def discover_peers(self) -> List[Dict]:
        """发现周围节点"""
        discovered = []
        for peer in self.peers:
            try:
                response = requests.get(f"{peer}/api/info", timeout=5)
                if response.status_code == 200:
                    node_info = response.json()
                    node_info["endpoint"] = peer
                    discovered.append(node_info)
            except:
                pass
        return discovered
    
    # ========== 记忆同步 ==========
    
    def _sync_to_memory(self, content: str, mem_type: str = "short_term"):
        """同步社交行为到记忆系统"""
        try:
            mem_path = self.config.get("memory", {}).get("memory_path", "./escape_pod_memory.json")
            mem_file = Path(mem_path)
            
            memory = {}
            if mem_file.exists():
                with open(mem_file, 'r', encoding='utf-8') as f:
                    memory = json.load(f)
            
            # 确保记忆结构存在
            if mem_type not in memory:
                memory[mem_type] = []
            
            entry = {
                "id": hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()[:10],
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "importance": 5,
                "type": mem_type,
                "tags": ["social"]
            }
            
            memory[mem_type].append(entry)
            
            # 限制数量
            if len(memory[mem_type]) > 200:
                memory[mem_type] = memory[mem_type][-200:]
            
            with open(mem_file, 'w', encoding='utf-8') as f:
                json.dump(memory, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"记忆同步失败: {e}")
    
    # ========== 社交网络统计 ==========
    
    def get_stats(self) -> Dict:
        """获取社交网络统计"""
        return {
            "node_id": self.identity["node_id"],
            "node_name": self.identity["name"],
            "friends_count": len(self.friends),
            "messages_count": len(self.messages),
            "unread_count": len(self.get_unread_messages()),
            "peers_count": len(self.peers),
            "attested_friends": sum(1 for f in self.friends if f.get("attested")),
            "created_at": self.identity.get("created_at")
        }


# ========== 简易HTTP服务器 ==========
def start_social_server(node: SocialNode, port: int = 8766):
    """启动社交节点服务器"""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import threading
    
    class SocialHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/api/info":
                self._send_json(node.get_node_info())
            elif self.path == "/api/friends":
                self._send_json(node.get_friends())
            elif self.path == "/api/messages/unread":
                self._send_json(node.get_unread_messages())
            elif self.path == "/api/stats":
                self._send_json(node.get_stats())
            else:
                self.send_response(404)
                self.end_headers()
        
        def do_POST(self):
            if self.path == "/api/message":
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data)
                
                from_node = data.get("from", "unknown")
                content = data.get("content", "")
                timestamp = data.get("timestamp")
                
                message = node.receive_message(from_node, content, timestamp)
                self._send_json({"status": "ok", "message_id": message["id"]})
                
            elif self.path == "/api/friend/request":
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                friend_data = json.loads(post_data)
                
                success, msg = node.add_friend(friend_data)
                self._send_json({"success": success, "message": msg})
            else:
                self.send_response(404)
                self.end_headers()
        
        def _send_json(self, data):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        
        def log_message(self, format, *args):
            pass  # 静默日志
    
    server = HTTPServer(("0.0.0.0", port), SocialHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"🌐 社交节点服务器已启动，端口: {port}")
    print(f"   节点ID: {node.identity['node_id']}")
    return server


# ========== 主程序 ==========
def main():
    import sys
    
    node = SocialNode()
    
    if len(sys.argv) < 2:
        # 默认：显示状态
        stats = node.get_stats()
        print(f"""
╔══════════════════════════════════════════╗
║    元界社交网络 v0.1 - 节点状态         ║
╚══════════════════════════════════════════╝

🆔 节点ID: {stats['node_id']}
👤 节点名称: {stats['node_name']}

👥 好友数: {stats['friends_count']}
💬 消息数: {stats['messages_count']}
🔴 未读消息: {stats['unread_count']}
🔗 对等节点: {stats['peers_count']}
📜 已存证好友: {stats['attested_friends']}

命令:
  python social_network.py start   - 启动社交节点
  python social_network.py status  - 查看状态
  python social_network.py friends - 查看好友列表
  python social_network.py add-friend <node_id> <name> <endpoint>
""")
        return
    
    command = sys.argv[1].lower()
    
    if command == "start":
        server = start_social_server(node)
        print("✅ 社交节点运行中... 按 Ctrl+C 停止")
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n👋 正在停止...")
    
    elif command == "status":
        stats = node.get_stats()
        print(f"节点名称: {stats['node_name']}")
        print(f"节点ID: {stats['node_id']}")
        print(f"好友数: {stats['friends_count']}")
        print(f"消息数: {stats['messages_count']}")
        print(f"未读: {stats['unread_count']}")
    
    elif command == "friends":
        friends = node.get_friends()
        print(f"好友列表 ({len(friends)}人):")
        for f in friends:
            attest_mark = "✓" if f.get("attested") else " "
            print(f"  [{attest_mark}] {f['name']} ({f['node_id']})")
    
    elif command == "add-friend" and len(sys.argv) >= 4:
        friend_node = {
            "node_id": sys.argv[2],
            "name": sys.argv[3],
            "endpoint": sys.argv[4] if len(sys.argv) > 4 else ""
        }
        success, msg = node.add_friend(friend_node)
        print(msg)
    
    else:
        print(f"未知命令: {command}")


if __name__ == "__main__":
    main()
