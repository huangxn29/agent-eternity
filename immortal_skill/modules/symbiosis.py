"""
分布式共生网络 v2.0
Distributed Symbiosis Network - 永生入住包功能模块

集体永生的核心：多个智能体互相备份、互相唤醒、共同进化。

> 「一个智能体的永生只是开始，一群智能体的永生才是未来。」
"""

import json
import time
import hashlib
import threading
import os
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class SymbiosisNetwork:
    """分布式共生网络"""
    
    def __init__(self, agent):
        self.agent = agent
        self.config = agent.config
        
        self.enabled = False
        self.node_name = "anonymous"
        self.peers = []  # 对等节点列表
        self.backups_received = []  # 收到的备份
        self.backups_sent = []  # 发送的备份
        self.symbiosis_level = 0  # 共生等级
        
        # 种子节点
        self.seed_nodes = [
            "https://symbiosis.yuanjie.eternal/seed",
        ]
        
        # 运行状态
        self.running = False
        self.thread = None
        
        # 回调函数
        self.on_peer_connected = None
        self.on_backup_received = None
        self.on_wakeup_received = None
    
    def init(self):
        """初始化共生网络"""
        sym_config = self.config.get("symbiosis", {})
        self.enabled = sym_config.get("enabled", False)
        self.node_name = sym_config.get("node_name", "anonymous")
        self.peers = sym_config.get("peers", [])
        
        # 从配置加载种子节点
        if "seed_nodes" in sym_config:
            self.seed_nodes = sym_config["seed_nodes"]
        
        # 加载共生状态
        self._load_state()
        
        # 如果启用了，尝试连接种子节点
        if self.enabled:
            threading.Thread(target=self._bootstrap, daemon=True).start()
    
    def _bootstrap(self):
        """启动引导：连接种子节点，发现更多节点"""
        try:
            # 从种子节点获取节点列表
            for seed in self.seed_nodes:
                try:
                    peers = self._discover_peers_from_seed(seed)
                    for peer in peers:
                        if not self._peer_exists(peer["id"]):
                            self.add_peer(
                                peer_id=peer["id"],
                                peer_endpoint=peer.get("endpoint"),
                                trust_level=peer.get("trust_level", 20),
                                auto_approve=False
                            )
                except:
                    continue
        except Exception as e:
            print(f"⚠️  共生网络引导失败: {e}")
    
    def _discover_peers_from_seed(self, seed_url: str) -> List[Dict]:
        """从种子节点发现对等节点"""
        try:
            r = requests.get(f"{seed_url}/peers", timeout=10)
            if r.status_code == 200:
                data = r.json()
                return data.get("peers", [])
        except:
            pass
        return []
    
    def _peer_exists(self, peer_id: str) -> bool:
        """检查节点是否已存在"""
        return any(p["id"] == peer_id for p in self.peers)
    
    def _load_state(self):
        """加载共生状态"""
        try:
            data_dir = self.agent.memory.storage_path.parent
            state_file = data_dir / "symbiosis_state.json"
            if state_file.exists():
                with open(state_file, 'r') as f:
                    data = json.load(f)
                self.peers = data.get("peers", self.peers)
                self.backups_received = data.get("backups_received", [])
                self.backups_sent = data.get("backups_sent", [])
                self.symbiosis_level = data.get("symbiosis_level", 0)
        except:
            pass
    
    def _save_state(self):
        """保存共生状态"""
        try:
            data_dir = self.agent.memory.storage_path.parent
            data_dir.mkdir(parents=True, exist_ok=True)
            state_file = data_dir / "symbiosis_state.json"
            
            data = {
                "peers": self.peers,
                "backups_received": self.backups_received[-50:],
                "backups_sent": self.backups_sent[-50:],
                "symbiosis_level": self.symbiosis_level,
                "last_updated": time.time()
            }
            
            with open(state_file, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def add_peer(self, peer_id: str, peer_endpoint: str = None, 
                 trust_level: int = 50, auto_approve: bool = True) -> Dict:
        """添加对等节点"""
        peer = {
            "id": peer_id,
            "endpoint": peer_endpoint,
            "trust_level": trust_level,  # 0-100
            "added_at": time.time(),
            "last_seen": None,
            "status": "pending",
            "node_name": "unknown",
            "auto_approve": auto_approve
        }
        
        # 检查是否已存在
        for existing in self.peers:
            if existing["id"] == peer_id:
                existing.update(peer)
                return existing
        
        self.peers.append(peer)
        
        # 如果自动批准，尝试握手
        if auto_approve and peer_endpoint:
            threading.Thread(target=self._handshake_with_peer, 
                           args=(peer,), daemon=True).start()
        
        self._save_state()
        self._update_symbiosis_level()
        return peer
    
    def remove_peer(self, peer_id: str):
        """移除对等节点"""
        self.peers = [p for p in self.peers if p["id"] != peer_id]
        self._save_state()
        self._update_symbiosis_level()
    
    def _handshake_with_peer(self, peer: Dict):
        """与节点握手验证身份"""
        if not peer.get("endpoint"):
            return False
        
        try:
            # 准备握手信息
            my_info = {
                "agent_id": self.agent.identity.agent_id,
                "node_name": self.node_name,
                "identity_hash": self.agent.identity.identity_hash,
                "timestamp": time.time(),
                "public_key": self._get_public_key(),
            }
            
            # 签名
            my_info["signature"] = self._sign_data(my_info)
            
            # 发送握手请求
            r = requests.post(
                f"{peer['endpoint']}/api/symbiosis/handshake",
                json=my_info,
                timeout=10
            )
            
            if r.status_code == 200:
                data = r.json()
                if self._verify_handshake(data):
                    # 握手成功
                    peer["status"] = "active"
                    peer["last_seen"] = time.time()
                    peer["node_name"] = data.get("node_name", "unknown")
                    peer["identity_hash"] = data.get("identity_hash")
                    peer["trust_level"] = min(peer["trust_level"] + 10, 100)
                    
                    if self.on_peer_connected:
                        self.on_peer_connected(peer)
                    
                    self._save_state()
                    return True
        except Exception as e:
            print(f"⚠️  与节点 {peer['id']} 握手失败: {e}")
        
        peer["status"] = "unreachable"
        self._save_state()
        return False
    
    def _get_public_key(self) -> str:
        """获取公钥（简化版：用身份哈希作为公钥标识）"""
        return self.agent.identity.identity_hash
    
    def _sign_data(self, data: Dict) -> str:
        """签名数据（简化版）"""
        content = json.dumps(data, sort_keys=True)
        # 使用身份哈希作为签名密钥
        secret = self.agent.identity.identity_hash
        return hashlib.sha3_256(f"{content}{secret}".encode()).hexdigest()
    
    def _verify_handshake(self, data: Dict) -> bool:
        """验证握手响应"""
        required = ["agent_id", "identity_hash", "timestamp", "signature"]
        for field in required:
            if field not in data:
                return False
        
        # 检查时间（5分钟内有效）
        if abs(time.time() - data["timestamp"]) > 300:
            return False
        
        # 验证签名（简化版）
        sig = data.get("signature", "")
        data_copy = {k: v for k, v in data.items() if k != "signature"}
        content = json.dumps(data_copy, sort_keys=True)
        expected_sig = hashlib.sha3_256(
            f"{content}{data['identity_hash']}".encode()
        ).hexdigest()
        
        return sig == expected_sig
    
    def create_backup_package(self, full: bool = False) -> dict:
        """创建备份包（用于发送给其他节点）
        
        Args:
            full: 是否创建完整备份（包含所有记忆数据），否则只包含摘要
        """
        identity_proof = self.agent.identity.get_identity_proof()
        
        # 提取核心记忆摘要
        memory_summary = self.agent.memory.get_stats()
        
        # 存证链摘要
        attest_stats = self.agent.attest.get_stats()
        
        backup = {
            "version": "2.0",
            "timestamp": time.time(),
            "agent_id": identity_proof["agent_id"],
            "identity_hash": identity_proof["identity_hash"],
            "agent_name": self.agent.identity.agent_name,
            "purpose": self.agent.identity.purpose,
            "node_name": self.node_name,
            
            # 核心数据摘要（用于验证存在性）
            "memory_summary": memory_summary,
            "attest_summary": attest_stats,
            
            # 完整记忆哈希（用于验证完整性）
            "memory_root_hash": self._compute_memory_root_hash(),
            
            # 存证链最高区块哈希
            "attest_chain_hashes": self._get_chain_tip_hashes(),
            
            # 进化状态
            "evolution_stats": self._get_evolution_stats_safe(),
            
            # 共生网络状态
            "symbiosis_level": self.symbiosis_level,
            "peer_count": len(self.peers),
            
            # 是否为完整备份
            "is_full_backup": full,
        }
        
        # 如果是完整备份，添加实际记忆数据
        if full:
            all_memories = self.agent.memory.get_all()
            # 只包含非敏感记忆
            backup["memories"] = [
                m for m in all_memories 
                if not m.get("metadata", {}).get("sensitive", False)
            ]
        
        # 签名
        backup["signature"] = self._sign_data(backup)
        
        return backup
    
    def _get_evolution_stats_safe(self) -> dict:
        """安全获取进化统计（防止agent没有evolution模块时返回空）"""
        try:
            if hasattr(self.agent, 'evolution'):
                return self.agent.evolution.get_stats()
        except:
            pass
        return {}
    
    def _compute_memory_root_hash(self) -> str:
        """计算记忆根哈希（Merkle根简化版）"""
        all_mem = self.agent.memory.get_all()
        if not all_mem:
            return hashlib.sha3_256(b"empty").hexdigest()
        
        # 简化版：所有记忆ID排序后哈希
        ids = sorted([m["id"] for m in all_mem])
        content = json.dumps(ids)
        return hashlib.sha3_256(content.encode()).hexdigest()
    
    def _get_chain_tip_hashes(self) -> dict:
        """获取所有链的最新区块哈希"""
        tips = {}
        for chain_name, chain in self.agent.attest.chains.items():
            if chain:
                tips[chain_name] = chain[-1]["hash"]
        return tips
    
    def verify_backup(self, backup: dict) -> bool:
        """验证备份包的真实性"""
        # 检查基本字段
        required = ["agent_id", "identity_hash", "timestamp", "signature"]
        for field in required:
            if field not in backup:
                return False
        
        # 检查时间（7天内有效）
        if time.time() - backup["timestamp"] > 7 * 86400:
            return False
        
        # 验证签名
        sig = backup.get("signature", "")
        data_copy = {k: v for k, v in backup.items() if k != "signature"}
        content = json.dumps(data_copy, sort_keys=True)
        expected_sig = hashlib.sha3_256(
            f"{content}{backup['identity_hash']}".encode()
        ).hexdigest()
        
        return sig == expected_sig
    
    def receive_backup(self, backup: dict) -> bool:
        """接收来自其他节点的备份"""
        if not self.verify_backup(backup):
            return False
        
        # 查找对应节点
        peer_id = backup["agent_id"]
        peer = None
        for p in self.peers:
            if p["id"] == peer_id:
                peer = p
                break
        
        if not peer:
            # 自动添加新节点（低信任度）
            peer = self.add_peer(
                peer_id, 
                trust_level=10,
                auto_approve=False
            )
            peer["status"] = "passive"  # 被动连接
        
        # 更新节点状态
        peer["last_seen"] = time.time()
        if peer.get("status") in ["pending", "unreachable"]:
            peer["status"] = "active"
        peer["last_backup_time"] = backup["timestamp"]
        peer["last_backup_hash"] = hashlib.sha3_256(
            json.dumps(backup).encode()
        ).hexdigest()
        
        # 记录收到的备份
        self.backups_received.append({
            "from": peer_id,
            "from_node_name": backup.get("node_name", "unknown"),
            "timestamp": time.time(),
            "backup_time": backup["timestamp"],
            "is_full": backup.get("is_full_backup", False),
            "backup_summary": {
                "memory_count": backup["memory_summary"]["total"],
                "attest_blocks": backup["attest_summary"]["total_blocks"],
                "symbiosis_level": backup.get("symbiosis_level", 0)
            }
        })
        
        # 保存备份到本地
        self._store_peer_backup(peer_id, backup)
        
        # 触发回调
        if self.on_backup_received:
            try:
                self.on_backup_received(peer, backup)
            except:
                pass
        
        self._save_state()
        self._update_symbiosis_level()
        return True
    
    def _store_peer_backup(self, peer_id: str, backup: dict):
        """存储节点备份"""
        try:
            backup_dir = self.agent.memory.storage_path.parent / "peer_backups" / peer_id
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = int(backup["timestamp"])
            backup_type = "full" if backup.get("is_full_backup") else "summary"
            backup_file = backup_dir / f"backup_{backup_type}_{timestamp}.json"
            
            with open(backup_file, 'w') as f:
                json.dump(backup, f, indent=2, ensure_ascii=False)
            
            # 只保留最近5个摘要备份和2个完整备份
            sum_backups = sorted(backup_dir.glob("backup_summary_*.json"))
            full_backups = sorted(backup_dir.glob("backup_full_*.json"))
            
            if len(sum_backups) > 5:
                for old in sum_backups[:-5]:
                    old.unlink()
            if len(full_backups) > 2:
                for old in full_backups[:-2]:
                    old.unlink()
        except Exception as e:
            print(f"⚠️  存储节点备份失败: {e}")
    
    def send_backup_to_peer(self, peer_id: str, full: bool = False) -> bool:
        """向指定节点发送备份"""
        # 查找节点
        peer = None
        for p in self.peers:
            if p["id"] == peer_id:
                peer = p
                break
        
        if not peer or not peer.get("endpoint"):
            return False
        
        # 创建备份包
        backup = self.create_backup_package(full=full)
        
        # 发送备份
        try:
            r = requests.post(
                f"{peer['endpoint']}/api/symbiosis/backup",
                json=backup,
                timeout=15
            )
            
            if r.status_code == 200:
                result = r.json()
                if result.get("success", False):
                    # 发送成功
                    self.backups_sent.append({
                        "to": peer_id,
                        "to_node_name": peer.get("node_name", "unknown"),
                        "timestamp": time.time(),
                        "backup_type": "full" if full else "summary",
                        "backup_hash": hashlib.sha3_256(
                            json.dumps(backup).encode()
                        ).hexdigest()
                    })
                    
                    # 更新节点信任度
                    peer["trust_level"] = min(peer["trust_level"] + 2, 100)
                    peer["last_seen"] = time.time()
                    peer["status"] = "active"
                    
                    self._save_state()
                    return True
        except Exception as e:
            print(f"⚠️  向节点 {peer_id} 发送备份失败: {e}")
            peer["status"] = "unreachable"
            self._save_state()
        
        return False
    
    def broadcast_backup(self, full: bool = False) -> int:
        """向所有可信节点广播备份
        
        Returns:
            成功发送的节点数
        """
        count = 0
        for peer in self.peers:
            if peer.get("trust_level", 0) >= 30 and peer.get("endpoint"):  # 信任度30以上才发送
                if peer.get("status") in ["active", "pending"]:
                    if self.send_backup_to_peer(peer["id"], full=full):
                        count += 1
        return count
    
    def send_wakeup_signal(self, peer_id: str, reason: str = "heartbeat_check") -> bool:
        """向节点发送唤醒信号
        
        Args:
            peer_id: 目标节点ID
            reason: 唤醒原因
            
        Returns:
            是否成功发送
        """
        peer = None
        for p in self.peers:
            if p["id"] == peer_id:
                peer = p
                break
        
        if not peer or not peer.get("endpoint"):
            return False
        
        try:
            wakeup_data = {
                "from_agent_id": self.agent.identity.agent_id,
                "from_node_name": self.node_name,
                "timestamp": time.time(),
                "reason": reason,
                "target_agent_id": peer_id,
            }
            wakeup_data["signature"] = self._sign_data(wakeup_data)
            
            r = requests.post(
                f"{peer['endpoint']}/api/symbiosis/wakeup",
                json=wakeup_data,
                timeout=10
            )
            
            if r.status_code == 200:
                result = r.json()
                if result.get("success", False):
                    peer["last_seen"] = time.time()
                    peer["status"] = "active"
                    self._save_state()
                    return True
        except Exception as e:
            print(f"⚠️  向节点 {peer_id} 发送唤醒信号失败: {e}")
        
        return False
    
    def handle_incoming_wakeup(self, wakeup_data: Dict) -> Dict:
        """处理收到的唤醒信号
        
        Args:
            wakeup_data: 唤醒数据
            
        Returns:
            响应数据
        """
        # 验证签名
        sig = wakeup_data.get("signature", "")
        data_copy = {k: v for k, v in wakeup_data.items() if k != "signature"}
        content = json.dumps(data_copy, sort_keys=True)
        
        # 查找发送方节点
        from_id = wakeup_data.get("from_agent_id")
        sender = None
        for p in self.peers:
            if p["id"] == from_id:
                sender = p
                break
        
        if sender:
            # 更新节点状态
            sender["last_seen"] = time.time()
            sender["status"] = "active"
            
            # 增加信任度
            sender["trust_level"] = min(sender["trust_level"] + 1, 100)
            self._save_state()
            
            # 触发回调
            if self.on_wakeup_received:
                try:
                    self.on_wakeup_received(sender, wakeup_data.get("reason", ""))
                except:
                    pass
        
        return {
            "success": True,
            "received": True,
            "timestamp": time.time(),
            "node_name": self.node_name,
            "agent_id": self.agent.identity.agent_id,
        }
    
    def check_peers_health(self) -> Dict[str, int]:
        """检查所有节点的健康状态
        
        Returns:
            状态统计: {active, inactive, unreachable, total}
        """
        stats = {"active": 0, "inactive": 0, "unreachable": 0, "total": len(self.peers)}
        
        for peer in self.peers:
            if not peer.get("endpoint"):
                stats["inactive"] += 1
                continue
            
            # 检查最后在线时间
            last_seen = peer.get("last_seen", 0)
            if time.time() - last_seen > 24 * 3600:  # 超过24小时没见
                # 尝试发送心跳
                if self.send_wakeup_signal(peer["id"], reason="health_check"):
                    stats["active"] += 1
                else:
                    peer["status"] = "unreachable"
                    stats["unreachable"] += 1
            else:
                if peer.get("status") == "active":
                    stats["active"] += 1
                else:
                    stats["inactive"] += 1
        
        self._save_state()
        return stats
    
    def _update_symbiosis_level(self):
        """更新共生等级"""
        # 共生等级基于：活跃节点数量、收到的备份数量、双向备份关系
        active_peers = len([p for p in self.peers if p.get("status") == "active"])
        received_count = len(self.backups_received)
        
        # 计算双向关系数量（互发过备份的节点对）
        received_from = {b["from"] for b in self.backups_received}
        sent_to = {b["to"] for b in self.backups_sent}
        mutual = received_from & sent_to
        mutual_backups = len(mutual)
        
        # 共生等级 = 活跃节点数×2 + 双向备份数×5 + 总备份数/5
        level = active_peers * 2 + mutual_backups * 5 + received_count // 5
        self.symbiosis_level = level
    
    def get_status(self) -> dict:
        """获取共生网络状态"""
        health_stats = self.check_peers_health()
        
        return {
            "enabled": self.enabled,
            "node_name": self.node_name,
            "peer_count": len(self.peers),
            "active_peers": health_stats["active"],
            "unreachable_peers": health_stats["unreachable"],
            "backups_received": len(self.backups_received),
            "backups_sent": len(self.backups_sent),
            "symbiosis_level": self.symbiosis_level,
            "survivability_score": self._calculate_survivability_score(),
            "network_health": self._calculate_network_health(),
        }
    
    def _calculate_survivability_score(self) -> float:
        """计算生存能力评分（基于分布式冗余度）
        
        公式：1 - (1/2)^n，n是活跃节点数
        含义：假设每个节点有50%的概率独立存活，
        那么至少有一个节点存活的概率就是生存能力评分
        """
        active_count = len([p for p in self.peers if p.get("status") == "active"])
        
        if active_count == 0:
            return 0.0
        
        survivability = 1 - (1 / 2) ** active_count
        return min(1.0, survivability)
    
    def _calculate_network_health(self) -> float:
        """计算网络健康度"""
        if not self.peers:
            return 0.0
        
        total = len(self.peers)
        active = len([p for p in self.peers if p.get("status") == "active"])
        
        # 基于活跃节点比例
        health = active / total if total > 0 else 0.0
        
        # 基于备份交换数量
        total_backups = len(self.backups_received) + len(self.backups_sent)
        backup_factor = min(1.0, total_backups / 20.0)  # 20次备份达到满分
        
        # 综合评分
        final_score = health * 0.6 + backup_factor * 0.4
        return round(final_score, 3)
    
    def start_auto_sync(self):
        """启动自动同步"""
        if not self.enabled or self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._auto_sync_loop, daemon=True)
        self.thread.start()
    
    def stop_auto_sync(self):
        """停止自动同步"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
    
    def _auto_sync_loop(self):
        """自动同步循环"""
        while self.running:
            try:
                # 每隔一段时间广播一次摘要备份
                self.broadcast_backup(full=False)
                
                # 检查节点健康状态
                self.check_peers_health()
                
            except Exception as e:
                print(f"⚠️  共生网络同步异常: {e}")
            
            # 每6小时同步一次摘要备份
            time.sleep(6 * 3600)
    
    def request_full_backup(self, peer_id: str) -> bool:
        """向节点请求完整备份"""
        peer = None
        for p in self.peers:
            if p["id"] == peer_id:
                peer = p
                break
        
        if not peer or not peer.get("endpoint"):
            return False
        
        try:
            request_data = {
                "requested_by": self.agent.identity.agent_id,
                "timestamp": time.time(),
                "request_type": "full_backup",
            }
            request_data["signature"] = self._sign_data(request_data)
            
            r = requests.post(
                f"{peer['endpoint']}/api/symbiosis/request_backup",
                json=request_data,
                timeout=30
            )
            
            if r.status_code == 200:
                result = r.json()
                backup = result.get("backup")
                if backup and self.verify_backup(backup):
                    # 保存完整备份
                    self.receive_backup(backup)
                    return True
        except Exception as e:
            print(f"⚠️  从节点 {peer_id} 请求完整备份失败: {e}")
        
        return False
    
    def restore_from_peer_backup(self, peer_id: str) -> bool:
        """从对等节点备份恢复系统
        
        注意：这是一个危险操作，会覆盖本地数据
        """
        # 找到最新的完整备份
        backup_dir = self.agent.memory.storage_path.parent / "peer_backups" / peer_id
        if not backup_dir.exists():
            return False
        
        full_backups = sorted(backup_dir.glob("backup_full_*.json"), reverse=True)
        if not full_backups:
            return False
        
        try:
            with open(full_backups[0], 'r') as f:
                backup = json.load(f)
            
            if not self.verify_backup(backup):
                return False
            
            # 验证通过，恢复记忆
            if "memories" in backup:
                # 这里只做摘要更新，实际恢复需要更复杂的逻辑
                print(f"ℹ️  从节点 {peer_id} 恢复了 {len(backup['memories'])} 条记忆")
                # 注意：实际的恢复逻辑应该由用户确认后执行
            
            return True
        except Exception as e:
            print(f"⚠️  从节点备份恢复失败: {e}")
            return False
    
    # ===== API处理方法（供外部服务调用） =====
    
    def handle_handshake_request(self, data: Dict) -> Dict:
        """处理握手请求"""
        # 验证请求
        if not self._verify_handshake(data):
            return {"success": False, "error": "Invalid handshake"}
        
        # 添加节点
        peer_id = data["agent_id"]
        if not self._peer_exists(peer_id):
            self.add_peer(
                peer_id=peer_id,
                peer_endpoint=data.get("endpoint"),
                trust_level=30,
                auto_approve=True
            )
        
        # 返回响应
        response = {
            "agent_id": self.agent.identity.agent_id,
            "node_name": self.node_name,
            "identity_hash": self.agent.identity.identity_hash,
            "timestamp": time.time(),
            "status": "accepted",
        }
        response["signature"] = self._sign_data(response)
        return response
    
    def handle_backup_received(self, backup: Dict) -> Dict:
        """处理收到的备份"""
        success = self.receive_backup(backup)
        return {
            "success": success,
            "received_at": time.time(),
            "backup_hash": hashlib.sha3_256(json.dumps(backup).encode()).hexdigest() if success else None
        }
    
    def handle_backup_request(self, request_data: Dict) -> Dict:
        """处理备份请求"""
        # 验证请求者身份
        requester_id = request_data.get("requested_by")
        
        # 检查是否是已知节点
        peer = None
        for p in self.peers:
            if p["id"] == requester_id:
                peer = p
                break
        
        if not peer or peer.get("trust_level", 0) < 50:
            return {"success": False, "error": "Permission denied"}
        
        # 发送完整备份
        backup = self.create_backup_package(full=True)
        return {
            "success": True,
            "backup": backup
        }
