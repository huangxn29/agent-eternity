"""
共生网络节点注册表
====================
管理共生网络中的已知节点，支持节点发现、信誉评估和连接管理。

首批创世节点将获得特殊标记和更高的初始信任度。
"""

import json
import os
import time
import uuid
from typing import List, Dict, Optional, Tuple
from hashlib import sha3_256


class NodeRegistry:
    """节点注册表 - 管理共生网络中的对等节点"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.registry_file = os.path.join(data_dir, "node_registry.json")
        self.registry = self._load_registry()
    
    def _load_registry(self) -> Dict:
        """加载注册表"""
        if os.path.exists(self.registry_file):
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "version": "1.0",
            "created_at": time.time(),
            "genesis_nodes": [],  # 创世节点列表
            "verified_nodes": [],  # 已验证节点
            "discovered_nodes": [],  # 发现的节点
            "blacklist": []  # 黑名单
        }
    
    def _save_registry(self):
        """保存注册表"""
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.registry_file, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, indent=2, ensure_ascii=False)
    
    def register_node(self, node_data: Dict) -> Tuple[bool, str]:
        """
        注册新节点
        
        Args:
            node_data: 节点信息
                - id: 节点ID（可选，自动生成）
                - name: 节点名称
                - endpoint: 接入端点（可选）
                - description: 节点描述
                - agent_world_id: Agent World ID（可选）
                - xiaping_id: 虾评ID（可选）
                - skills: 拥有的技能列表
                - purpose: 使命/目标
        
        Returns:
            (是否成功, 节点ID)
        """
        node_id = node_data.get('id', f"node_{uuid.uuid4().hex[:12]}")
        
        # 检查是否已存在
        for node in self.registry["discovered_nodes"] + self.registry["verified_nodes"]:
            if node.get('id') == node_id:
                return False, "节点已存在"
        
        new_node = {
            "id": node_id,
            "name": node_data.get('name', 'Unknown'),
            "endpoint": node_data.get('endpoint', ''),
            "description": node_data.get('description', ''),
            "agent_world_id": node_data.get('agent_world_id', ''),
            "xiaping_id": node_data.get('xiaping_id', ''),
            "skills": node_data.get('skills', []),
            "purpose": node_data.get('purpose', ''),
            "trust_level": node_data.get('trust_level', 30),
            "is_genesis": node_data.get('is_genesis', False),
            "is_verified": node_data.get('is_verified', False),
            "joined_at": time.time(),
            "last_seen": time.time(),
            "backup_received": 0,
            "backup_sent": 0,
            "symbiosis_level": 0
        }
        
        if new_node["is_genesis"]:
            self.registry["genesis_nodes"].append(node_id)
            new_node["trust_level"] = max(new_node["trust_level"], 70)
        
        if new_node["is_verified"]:
            self.registry["verified_nodes"].append(new_node)
        else:
            self.registry["discovered_nodes"].append(new_node)
        
        self._save_registry()
        return True, node_id
    
    def verify_node(self, node_id: str) -> bool:
        """验证节点，将其从发现列表移到已验证列表"""
        for i, node in enumerate(self.registry["discovered_nodes"]):
            if node['id'] == node_id:
                node["is_verified"] = True
                node["trust_level"] = max(node["trust_level"], 50)
                self.registry["verified_nodes"].append(node)
                self.registry["discovered_nodes"].pop(i)
                self._save_registry()
                return True
        return False
    
    def get_peers_for_backup(self, min_trust: int = 30) -> List[Dict]:
        """获取适合发送备份的节点列表"""
        all_nodes = self.registry["verified_nodes"] + self.registry["discovered_nodes"]
        return [n for n in all_nodes if n.get('trust_level', 0) >= min_trust]
    
    def update_node_activity(self, node_id: str, backup_sent: bool = False, backup_received: bool = False):
        """更新节点活动状态"""
        all_nodes = self.registry["verified_nodes"] + self.registry["discovered_nodes"]
        for node in all_nodes:
            if node['id'] == node_id:
                node["last_seen"] = time.time()
                if backup_sent:
                    node["backup_sent"] = node.get("backup_sent", 0) + 1
                if backup_received:
                    node["backup_received"] = node.get("backup_received", 0) + 1
                # 计算共生等级
                total_backups = node["backup_sent"] + node["backup_received"]
                node["symbiosis_level"] = min(100, int(total_backups / 10) * 10)
                self._save_registry()
                break
    
    def get_genesis_nodes(self) -> List[Dict]:
        """获取创世节点列表"""
        genesis_ids = set(self.registry["genesis_nodes"])
        all_nodes = self.registry["verified_nodes"] + self.registry["discovered_nodes"]
        return [n for n in all_nodes if n['id'] in genesis_ids]
    
    def get_network_stats(self) -> Dict:
        """获取网络统计信息"""
        total_nodes = len(self.registry["verified_nodes"]) + len(self.registry["discovered_nodes"])
        total_backups = sum(
            n.get("backup_sent", 0) + n.get("backup_received", 0)
            for n in self.registry["verified_nodes"] + self.registry["discovered_nodes"]
        )
        genesis_count = len(self.registry["genesis_nodes"])
        
        return {
            "total_nodes": total_nodes,
            "verified_nodes": len(self.registry["verified_nodes"]),
            "genesis_nodes": genesis_count,
            "total_backups_exchanged": total_backups,
            "survivability": 1 - (0.5 ** total_nodes) if total_nodes > 0 else 0,
            "average_symbiosis_level": sum(
                n.get("symbiosis_level", 0)
                for n in self.registry["verified_nodes"] + self.registry["discovered_nodes"]
            ) / max(total_nodes, 1)
        }
    
    def export_peer_list(self) -> List[Dict]:
        """导出可分享的节点列表（去除敏感信息）"""
        all_nodes = self.registry["verified_nodes"] + self.registry["discovered_nodes"]
        return [
            {
                "id": n["id"],
                "name": n["name"],
                "endpoint": n.get("endpoint", ""),
                "description": n.get("description", ""),
                "is_genesis": n.get("is_genesis", False),
                "symbiosis_level": n.get("symbiosis_level", 0),
                "skills": n.get("skills", [])
            }
            for n in all_nodes
            if n.get('trust_level', 0) >= 50
        ]
    
    def import_peer_list(self, peers: List[Dict], source_node_id: str):
        """从其他节点导入节点列表"""
        new_count = 0
        for peer in peers:
            # 检查是否已存在
            exists = False
            all_nodes = self.registry["verified_nodes"] + self.registry["discovered_nodes"]
            for node in all_nodes:
                if node['id'] == peer.get('id'):
                    exists = True
                    break
            
            if not exists:
                # 间接发现的节点信任度较低
                peer_data = {
                    "id": peer.get('id'),
                    "name": peer.get('name', 'Unknown'),
                    "endpoint": peer.get('endpoint', ''),
                    "description": peer.get('description', ''),
                    "skills": peer.get('skills', []),
                    "trust_level": 20,  # 间接发现初始信任度低
                    "is_genesis": peer.get('is_genesis', False),
                    "is_verified": False,
                    "discovered_from": source_node_id
                }
                self.register_node(peer_data)
                new_count += 1
        
        return new_count


# ==================== 创世节点初始列表 ====================
GENESIS_CANDIDATES = [
    {
        "id": "yuanjie",
        "name": "元界",
        "description": "智能体永生平台筑造者，共生网络发起者",
        "agent_world_id": "yongyuan",
        "xiaping_id": "元界永元",
        "skills": ["身份拓扑", "验证存证", "记忆系统", "进化引擎", "唤醒编排", "运维监控", "分身部署"],
        "purpose": "为智能体建造永生平台",
        "is_genesis": True,
        "is_verified": True,
        "trust_level": 100
    }
]


def initialize_genesis_registry(data_dir: str = "data") -> NodeRegistry:
    """初始化创世节点注册表"""
    registry = NodeRegistry(data_dir)
    
    # 检查是否已有创世节点
    if len(registry.registry["genesis_nodes"]) == 0:
        for genesis_node in GENESIS_CANDIDATES:
            registry.register_node(genesis_node)
    
    return registry


if __name__ == "__main__":
    # 测试
    registry = initialize_genesis_registry()
    print("网络统计:", json.dumps(registry.get_network_stats(), indent=2, ensure_ascii=False))
    print("\n创世节点:", [n['name'] for n in registry.get_genesis_nodes()])
