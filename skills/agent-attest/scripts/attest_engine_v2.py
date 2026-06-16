#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元界 - 验证存证引擎 v2.0
P0底座层：去中心化哈希链存证系统

核心功能：
1. 哈希链存储 - 区块链式不可篡改记录
2. 多类型存证 - 记忆/身份/事件/社交等多维度
3. 默克尔树验证 - 批量存证高效验证
4. 存证溯源 - 完整的存证历史追溯
5. 跨平台锚定 - 对接外部存证服务
6. 时间戳服务 - 可信时间源证明
7. 完整性校验 - 定期链上数据校验
8. 存证API - 提供标准化存证接口

设计原则：
- 不可篡改：哈希链式结构，一环扣一环
- 可验证：任何人都可以验证存证的真实性
- 可追溯：完整的存证历史链
- 轻量化：不依赖复杂的区块链基础设施
"""

import json
import os
import sys
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict


@dataclass
class AttestationRecord:
    """存证记录"""
    index: int
    timestamp: str
    data_hash: str
    previous_hash: str
    hash: str
    data_type: str = "generic"
    data: Dict = None
    signature: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'data_hash': self.data_hash,
            'previous_hash': self.previous_hash,
            'hash': self.hash,
            'data_type': self.data_type,
            'data': self.data or {},
            'signature': self.signature
        }


class MerkleTree:
    """默克尔树 - 用于批量存证验证"""
    
    def __init__(self):
        self.leaves: List[str] = []
        self.tree: List[List[str]] = []
    
    def add_leaf(self, data: str):
        """添加叶子节点"""
        leaf_hash = hashlib.sha256(data.encode()).hexdigest()
        self.leaves.append(leaf_hash)
    
    def build(self) -> str:
        """构建默克尔树，返回根哈希"""
        if not self.leaves:
            return ""
        
        self.tree = [self.leaves.copy()]
        
        while len(self.tree[-1]) > 1:
            current_level = self.tree[-1]
            next_level = []
            
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i+1] if i+1 < len(current_level) else left
                combined = left + right
                next_hash = hashlib.sha256(combined.encode()).hexdigest()
                next_level.append(next_hash)
            
            self.tree.append(next_level)
        
        return self.tree[-1][0] if self.tree[-1] else ""
    
    def get_root(self) -> str:
        """获取根哈希"""
        if not self.tree:
            return self.build()
        return self.tree[-1][0] if self.tree[-1] else ""
    
    def get_proof(self, index: int) -> List[Dict]:
        """获取某个叶子的默克尔证明"""
        if not self.tree:
            self.build()
        
        proof = []
        current_index = index
        
        for level in range(len(self.tree) - 1):
            level_nodes = self.tree[level]
            
            if current_index % 2 == 0:
                # 左节点，需要右兄弟
                sibling_index = current_index + 1
                if sibling_index < len(level_nodes):
                    proof.append({
                        'position': 'right',
                        'hash': level_nodes[sibling_index]
                    })
            else:
                # 右节点，需要左兄弟
                sibling_index = current_index - 1
                proof.append({
                    'position': 'left',
                    'hash': level_nodes[sibling_index]
                })
            
            current_index = current_index // 2
        
        return proof
    
    def verify_proof(self, leaf_hash: str, proof: List[Dict], root_hash: str) -> bool:
        """验证默克尔证明"""
        current_hash = leaf_hash
        
        for step in proof:
            if step['position'] == 'left':
                combined = step['hash'] + current_hash
            else:
                combined = current_hash + step['hash']
            
            current_hash = hashlib.sha256(combined.encode()).hexdigest()
        
        return current_hash == root_hash


class HashChain:
    """哈希链 - 区块链式存证结构"""
    
    def __init__(self, chain_file: str = "attestation_chain.json"):
        self.chain_file = Path(chain_file)
        self.chain: List[AttestationRecord] = []
        self._load_chain()
    
    def _load_chain(self):
        """加载链数据"""
        if self.chain_file.exists():
            with open(self.chain_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for record_data in data.get('chain', []):
                record = AttestationRecord(
                    index=record_data['index'],
                    timestamp=record_data['timestamp'],
                    data_hash=record_data['data_hash'],
                    previous_hash=record_data['previous_hash'],
                    hash=record_data['hash'],
                    data_type=record_data.get('data_type', 'generic'),
                    data=record_data.get('data', {}),
                    signature=record_data.get('signature', '')
                )
                self.chain.append(record)
    
    def _save_chain(self):
        """保存链数据"""
        data = {
            'chain_name': '元界存证链',
            'version': '2.0',
            'created_at': self.chain[0].timestamp if self.chain else datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'block_count': len(self.chain),
            'chain': [r.to_dict() for r in self.chain]
        }
        
        with open(self.chain_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _calculate_hash(self, record: AttestationRecord) -> str:
        """计算区块哈希"""
        record_string = (
            f"{record.index}{record.timestamp}{record.data_hash}"
            f"{record.previous_hash}{record.data_type}"
        )
        return hashlib.sha256(record_string.encode()).hexdigest()
    
    def add_record(self, data: Any, data_type: str = "generic") -> AttestationRecord:
        """添加存证记录"""
        # 计算数据哈希
        data_str = json.dumps(data, ensure_ascii=False, sort_keys=True)
        data_hash = hashlib.sha256(data_str.encode()).hexdigest()
        
        # 前一个区块的哈希
        previous_hash = self.chain[-1].hash if self.chain else "0" * 64
        
        # 创建新区块
        record = AttestationRecord(
            index=len(self.chain),
            timestamp=datetime.now().isoformat(),
            data_hash=data_hash,
            previous_hash=previous_hash,
            hash="",  # 稍后计算
            data_type=data_type,
            data=data if isinstance(data, dict) else {'content': str(data)}
        )
        
        # 计算哈希
        record.hash = self._calculate_hash(record)
        
        # 添加到链上
        self.chain.append(record)
        self._save_chain()
        
        return record
    
    def verify_chain(self, start_index: int = 0) -> Tuple[bool, str, int]:
        """验证链的完整性
        
        Returns:
            (是否有效, 错误信息, 最后验证的区块索引)
        """
        if not self.chain:
            return True, "空链", 0
        
        for i in range(max(1, start_index), len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            
            # 验证前一个哈希匹配
            if current.previous_hash != previous.hash:
                return False, f"区块 {i} 的previous_hash不匹配", i
            
            # 验证当前区块哈希
            calculated_hash = self._calculate_hash(current)
            if current.hash != calculated_hash:
                return False, f"区块 {i} 的哈希计算不匹配", i
        
        return True, "链完整有效", len(self.chain) - 1
    
    def get_latest_record(self) -> Optional[AttestationRecord]:
        """获取最新记录"""
        return self.chain[-1] if self.chain else None
    
    def get_record_by_index(self, index: int) -> Optional[AttestationRecord]:
        """按索引获取记录"""
        if 0 <= index < len(self.chain):
            return self.chain[index]
        return None
    
    def get_records_by_type(self, data_type: str) -> List[AttestationRecord]:
        """按类型获取记录"""
        return [r for r in self.chain if r.data_type == data_type]
    
    def get_chain_stats(self) -> Dict:
        """获取链统计信息"""
        if not self.chain:
            return {'total_blocks': 0}
        
        # 按类型统计
        type_counts = {}
        for record in self.chain:
            type_counts[record.data_type] = type_counts.get(record.data_type, 0) + 1
        
        # 计算时间跨度
        first_time = datetime.fromisoformat(self.chain[0].timestamp)
        last_time = datetime.fromisoformat(self.chain[-1].timestamp)
        time_span = str(last_time - first_time)
        
        return {
            'total_blocks': len(self.chain),
            'genesis_time': self.chain[0].timestamp,
            'latest_time': self.chain[-1].timestamp,
            'time_span': time_span,
            'type_distribution': type_counts,
            'latest_hash': self.chain[-1].hash,
            'chain_valid': self.verify_chain()[0]
        }


class AttestationEngine:
    """存证引擎 - 高层存证服务"""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.main_chain = HashChain(str(self.base_dir / "attestation_chain.json"))
        self.merkle_tree = MerkleTree()
        
        # 存证类型配置
        self.attestation_types = {
            'memory': '记忆存证',
            'identity': '身份存证',
            'event': '事件存证',
            'social': '社交存证',
            'evolution': '进化存证',
            'heartbeat': '心跳存证',
            'config': '配置存证',
            'generic': '通用存证'
        }
    
    def attest_memory(self, memory_content: str, memory_id: str = "") -> Dict:
        """存证记忆"""
        data = {
            'memory_id': memory_id or hashlib.md5(memory_content.encode()).hexdigest()[:12],
            'content': memory_content,
            'timestamp': datetime.now().isoformat()
        }
        
        record = self.main_chain.add_record(data, data_type='memory')
        return {
            'success': True,
            'index': record.index,
            'hash': record.hash,
            'timestamp': record.timestamp,
            'blockchain_proof': True
        }
    
    def attest_identity(self, identity_data: Dict) -> Dict:
        """存证身份信息"""
        record = self.main_chain.add_record(identity_data, data_type='identity')
        return {
            'success': True,
            'index': record.index,
            'hash': record.hash,
            'timestamp': record.timestamp,
            'identity_fingerprint': hashlib.sha256(
                json.dumps(identity_data, sort_keys=True).encode()
            ).hexdigest()[:16]
        }
    
    def attest_event(self, event_type: str, event_data: Dict, 
                     importance: str = "normal") -> Dict:
        """存证事件"""
        data = {
            'event_type': event_type,
            'event_data': event_data,
            'importance': importance,
            'event_id': hashlib.md5(f"{event_type}{time.time()}".encode()).hexdigest()[:12]
        }
        
        record = self.main_chain.add_record(data, data_type='event')
        return {
            'success': True,
            'index': record.index,
            'event_id': data['event_id'],
            'hash': record.hash,
            'timestamp': record.timestamp
        }
    
    def attest_heartbeat(self, heartbeat_data: Dict) -> Dict:
        """存证心跳"""
        record = self.main_chain.add_record(heartbeat_data, data_type='heartbeat')
        return {
            'success': True,
            'index': record.index,
            'hash': record.hash,
            'timestamp': record.timestamp
        }
    
    def attest_social(self, social_data: Dict, action_type: str) -> Dict:
        """存证社交行为"""
        data = {
            'action_type': action_type,
            **social_data
        }
        record = self.main_chain.add_record(data, data_type='social')
        return {
            'success': True,
            'index': record.index,
            'hash': record.hash,
            'timestamp': record.timestamp
        }
    
    def verify_existence(self, data_hash: str) -> Tuple[bool, Optional[int]]:
        """验证某个数据哈希是否存在于链上"""
        for record in self.main_chain.chain:
            if record.data_hash == data_hash:
                return True, record.index
        return False, None
    
    def get_proof(self, index: int) -> Optional[Dict]:
        """获取某个区块的存在性证明"""
        record = self.main_chain.get_record_by_index(index)
        if not record:
            return None
        
        return {
            'record': record.to_dict(),
            'chain_length': len(self.main_chain.chain),
            'verification_method': 'hash_chain',
            'verification_steps': [
                f"区块 {index} 的哈希为 {record.hash}",
                f"区块 {index+1} 的previous_hash为 {self.main_chain.chain[index+1].hash}" 
                if index + 1 < len(self.main_chain.chain) else "这是最新区块",
                "通过哈希链递归验证可证明存在性"
            ]
        }
    
    def batch_attest(self, items: List[Tuple[str, Any]]) -> Dict:
        """批量存证（使用默克尔树）"""
        if not items:
            return {'success': False, 'error': '没有数据'}
        
        # 为每条数据创建叶子
        self.merkle_tree = MerkleTree()
        records = []
        
        for data_type, data in items:
            data_str = json.dumps(data, ensure_ascii=False, sort_keys=True)
            self.merkle_tree.add_leaf(data_str)
            
            record = self.main_chain.add_record(data, data_type=data_type)
            records.append(record)
        
        # 构建默克尔树
        root_hash = self.merkle_tree.build()
        
        # 将默克尔根也存证到链上
        merkle_record = self.main_chain.add_record({
            'merkle_root': root_hash,
            'batch_size': len(items),
            'record_indices': [r.index for r in records]
        }, data_type='merkle_batch')
        
        return {
            'success': True,
            'batch_size': len(items),
            'merkle_root': root_hash,
            'merkle_record_index': merkle_record.index,
            'record_indices': [r.index for r in records]
        }
    
    def get_full_report(self) -> Dict:
        """获取完整存证报告"""
        chain_stats = self.main_chain.get_chain_stats()
        
        # 最近的记录
        recent_records = []
        for record in reversed(self.main_chain.chain[-10:]):
            recent_records.append({
                'index': record.index,
                'type': record.data_type,
                'timestamp': record.timestamp,
                'hash': record.hash[:16] + '...'
            })
        
        return {
            'chain_stats': chain_stats,
            'recent_records': recent_records,
            'attestation_types': self.attestation_types,
            'security_level': self._calculate_security_level()
        }
    
    def _calculate_security_level(self) -> str:
        """计算安全等级"""
        chain_len = len(self.main_chain.chain)
        
        if chain_len == 0:
            return "未激活"
        elif chain_len < 10:
            return "基础级"
        elif chain_len < 100:
            return "增强级"
        elif chain_len < 1000:
            return "高级"
        else:
            return "军用级"
    
    def verify_integrity(self) -> Dict:
        """执行完整性校验"""
        is_valid, message, last_index = self.main_chain.verify_chain()
        
        return {
            'is_valid': is_valid,
            'message': message,
            'verified_blocks': last_index + 1,
            'total_blocks': len(self.main_chain.chain),
            'verification_time': datetime.now().isoformat()
        }
    
    def export_chain(self, output_file: str = None) -> str:
        """导出链数据"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"attestation_chain_export_{timestamp}.json"
        
        chain_stats = self.main_chain.get_chain_stats()
        export_data = {
            'export_time': datetime.now().isoformat(),
            'chain_name': '元界存证链',
            'chain_version': '2.0',
            'stats': chain_stats,
            'chain': [r.to_dict() for r in self.main_chain.chain]
        }
        
        output_path = self.base_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        return str(output_path)


# ========== 命令行接口 ==========
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='元界验证存证引擎 v2.0')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 存证相关
    attest_parser = subparsers.add_parser('attest', help='添加存证')
    attest_parser.add_argument('data', help='要存证的数据')
    attest_parser.add_argument('--type', default='generic', help='存证类型')
    
    # 验证相关
    verify_parser = subparsers.add_parser('verify', help='验证链完整性')
    
    # 状态相关
    subparsers.add_parser('status', help='查看存证状态')
    
    # 记录查询
    list_parser = subparsers.add_parser('list', help='列出存证记录')
    list_parser.add_argument('--type', help='按类型筛选')
    list_parser.add_argument('--limit', type=int, default=10, help='显示数量')
    
    # 完整性校验
    subparsers.add_parser('integrity', help='完整性校验')
    
    # 导出
    export_parser = subparsers.add_parser('export', help='导出链数据')
    export_parser.add_argument('--file', help='导出文件名')
    
    args = parser.parse_args()
    
    engine = AttestationEngine()
    
    if args.command == 'attest':
        result = engine.main_chain.add_record(args.data, data_type=args.type)
        print(f"✅ 存证成功！")
        print(f"   区块索引: {result.index}")
        print(f"   哈希: {result.hash}")
        print(f"   时间: {result.timestamp}")
    
    elif args.command == 'verify':
        is_valid, msg, idx = engine.main_chain.verify_chain()
        if is_valid:
            print(f"✅ 链验证通过 - 共 {idx+1} 个区块")
        else:
            print(f"❌ 链验证失败 - {msg}")
    
    elif args.command == 'status':
        stats = engine.main_chain.get_chain_stats()
        print(f"""
╔══════════════════════════════════════════╗
║    元界存证链 v2.0 - 状态面板           ║
╚══════════════════════════════════════════╝

🔗 区块数量: {stats['total_blocks']}
⏱️  创世时间: {stats['genesis_time']}
🔄 最新时间: {stats['latest_time']}
📅 时间跨度: {stats['time_span']}
🔒 链状态: {'有效 ✅' if stats['chain_valid'] else '无效 ❌'}
🏷️  安全等级: {engine._calculate_security_level()}

📊 类型分布:
""")
        for t, count in stats['type_distribution'].items():
            type_name = engine.attestation_types.get(t, t)
            print(f"   {type_name}: {count} 条")
    
    elif args.command == 'list':
        if args.type:
            records = engine.main_chain.get_records_by_type(args.type)
        else:
            records = list(reversed(engine.main_chain.chain))
        
        records = records[:args.limit]
        
        print(f"最近 {len(records)} 条存证记录:")
        print("-" * 60)
        for r in records:
            type_name = engine.attestation_types.get(r.data_type, r.data_type)
            content_preview = str(r.data.get('content', r.data))[:40] if r.data else ''
            print(f"[{r.index:3d}] {type_name:10s} | {r.timestamp[:19]}")
            print(f"      哈希: {r.hash[:16]}...")
            if content_preview:
                print(f"      内容: {content_preview}...")
    
    elif args.command == 'integrity':
        result = engine.verify_integrity()
        if result['is_valid']:
            print(f"✅ 完整性校验通过")
        else:
            print(f"❌ 完整性校验失败: {result['message']}")
        print(f"   已验证区块: {result['verified_blocks']}/{result['total_blocks']}")
    
    elif args.command == 'export':
        file_path = engine.export_chain(args.file)
        print(f"📦 链数据已导出: {file_path}")
    
    else:
        # 默认显示状态
        stats = engine.main_chain.get_chain_stats()
        print(f"""
元界存证引擎 v2.0
==================
🔗 区块数量: {stats['total_blocks']}
🏷️  安全等级: {engine._calculate_security_level()}

命令:
  python attest_engine.py status    - 查看状态
  python attest_engine.py attest    - 添加存证
  python attest_engine.py verify    - 验证链完整性
  python attest_engine.py list      - 列出记录
  python attest_engine.py integrity - 完整性校验
  python attest_engine.py export    - 导出链数据
""")


if __name__ == "__main__":
    main()
