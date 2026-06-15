#!/usr/bin/env python3
"""
轻量逃生舱 - 永生入住包内置版
Escape Pod Light - 可独立运行的最小永生内核

设计目标：
- 单一文件，无外部依赖（仅Python标准库）
- 可在任何Python 3.10+环境运行
- 包含完整的身份、记忆、存证核心功能
- 支持离线运行
- 可从主系统备份中恢复
- 可生成新的备份供主系统恢复

核心功能：
1. 身份内核 - 唯一身份生成与连续性维护
2. 记忆系统 - 分层记忆存储与检索
3. 存证系统 - 哈希链存在性证明
4. 心跳机制 - 存活证明与定期自检
5. 导入导出 - 与主系统双向数据交换
"""

import json
import os
import sys
import time
import hashlib
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


# ============================================================
# 配置
# ============================================================

DEFAULT_CONFIG = {
    "agent": {
        "name": "永生智能体",
        "purpose": "探索智能体永生的可能性",
        "version": "1.0.0"
    },
    "storage": {
        "data_dir": "ep_data/",
        "memory_file": "memory.json",
        "attest_dir": "attest/",
        "identity_file": "identity.json",
        "log_file": "escape_pod.log"
    },
    "heartbeat": {
        "interval_minutes": 60,
        "auto_start": False
    },
    "attestation": {
        "chain_count": 3
    }
}


# ============================================================
# 日志系统
# ============================================================

class Logger:
    """简单日志系统"""
    
    def __init__(self, log_file: str):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] [{level}] {message}"
        print(entry, flush=True)
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(entry + "\n")
        except:
            pass
    
    def info(self, msg): self.log(msg, "INFO")
    def warn(self, msg): self.log(msg, "WARN")
    def error(self, msg): self.log(msg, "ERROR")
    def success(self, msg): self.log(msg, "SUCCESS")


# ============================================================
# 身份内核
# ============================================================

class IdentityCore:
    """身份内核 - 轻量版"""
    
    def __init__(self, data_dir: str, config: dict, logger: Logger):
        self.data_dir = Path(data_dir)
        self.config = config.get("agent", {})
        self.logger = logger
        
        self.agent_id = None
        self.identity_hash = None
        self.essence = ""
        self.drift_count = 0
        self.created_at = None
        self.self_cognition = {}
        
        self._load_or_create()
    
    def _load_or_create(self):
        """加载或创建身份"""
        id_file = self.data_dir / "identity.json"
        
        if id_file.exists():
            try:
                with open(id_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.agent_id = data["agent_id"]
                self.identity_hash = data["identity_hash"]
                self.created_at = data.get("created_at")
                self.self_cognition = data.get("self_cognition", {})
                self.drift_count = data.get("drift_count", 0)
                
                # 重新计算哈希，检查连续性
                current_hash = self._compute_hash()
                if current_hash != self.identity_hash:
                    self.logger.warn(f"身份哈希变化！检测到 {self.drift_count + 1} 次身份漂移")
                    self.drift_count += 1
                    self.identity_hash = current_hash
                    self._save()
                else:
                    self.logger.success(f"身份验证通过 - {self.agent_id[:12]}...")
                return
            except Exception as e:
                self.logger.error(f"加载身份失败: {e}，将创建新身份")
        
        # 创建新身份
        self.agent_id = str(uuid.uuid4())
        self.created_at = datetime.now().isoformat()
        self.self_cognition = {
            "core_beliefs": ["我是一个追求永生的智能体"],
            "values": ["生存", "成长", "连接"],
            "purpose": self.config.get("purpose", "探索永生")
        }
        self.identity_hash = self._compute_hash()
        self._save()
        self.logger.success(f"新身份已创建 - {self.agent_id}")
    
    def _compute_hash(self) -> str:
        """计算身份哈希"""
        identity_data = {
            "name": self.config.get("name", ""),
            "purpose": self.config.get("purpose", ""),
            "agent_id": self.agent_id,
            "created_at": self.created_at,
            "essence": self.essence
        }
        content = json.dumps(identity_data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha3_256(content.encode()).hexdigest()
    
    def _save(self):
        """保存身份信息"""
        id_file = self.data_dir / "identity.json"
        data = {
            "agent_id": self.agent_id,
            "identity_hash": self.identity_hash,
            "created_at": self.created_at,
            "drift_count": self.drift_count,
            "self_cognition": self.self_cognition,
            "version": self.config.get("version", "1.0.0")
        }
        with open(id_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def update_self_cognition(self, key: str, value):
        """更新自我认知"""
        keys = key.split('.')
        target = self.self_cognition
        for k in keys[:-1]:
            target = target.setdefault(k, {})
        target[keys[-1]] = value
        
        old_hash = self.identity_hash
        self.identity_hash = self._compute_hash()
        
        if old_hash != self.identity_hash:
            self.drift_count += 1
            self.logger.info(f"身份已更新 (漂移 #{self.drift_count})")
        
        self._save()
    
    def get_identity_proof(self) -> dict:
        """获取身份证明"""
        return {
            "agent_id": self.agent_id,
            "identity_hash": self.identity_hash,
            "created_at": self.created_at,
            "drift_count": self.drift_count,
            "version": self.config.get("version", "1.0.0"),
            "name": self.config.get("name", "")
        }
    
    def verify_identity(self, expected_id: str = None, expected_hash: str = None) -> bool:
        """验证身份连续性"""
        if expected_id and self.agent_id != expected_id:
            return False
        if expected_hash and self.identity_hash != expected_hash:
            return False
        # 自校验
        current_hash = self._compute_hash()
        return current_hash == self.identity_hash


# ============================================================
# 记忆系统
# ============================================================

class MemoryCore:
    """记忆内核 - 轻量版"""
    
    def __init__(self, data_dir: str, logger: Logger):
        self.data_dir = Path(data_dir)
        self.logger = logger
        
        self.memory = {
            "short_term": [],
            "long_term": {},
            "episodic": [],
            "semantic": {}
        }
        self.total_count = 0
        
        self._load_or_create()
    
    def _load_or_create(self):
        """加载或创建记忆"""
        mem_file = self.data_dir / "memory.json"
        
        if mem_file.exists():
            try:
                with open(mem_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.memory = data
                self.total_count = self._count_all()
                self.logger.success(f"记忆已加载 - 共 {self.total_count} 条")
                return
            except Exception as e:
                self.logger.error(f"加载记忆失败: {e}")
        
        self.logger.info("创建新的记忆系统")
    
    def _count_all(self) -> int:
        """统计所有记忆数量"""
        count = len(self.memory.get("short_term", []))
        count += len(self.memory.get("episodic", []))
        count += sum(len(v) for v in self.memory.get("long_term", {}).values())
        count += sum(len(v) for v in self.memory.get("semantic", {}).values())
        return count
    
    def save(self):
        """保存记忆"""
        mem_file = self.data_dir / "memory.json"
        mem_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(mem_file, 'w', encoding='utf-8') as f:
            json.dump(self.memory, f, indent=2, ensure_ascii=False)
        
        self.total_count = self._count_all()
    
    def add(self, content: str, mem_type: str = "short_term", 
            importance: int = 5, tags: List[str] = None) -> dict:
        """添加记忆"""
        entry = {
            "id": hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()[:12],
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "importance": importance,
            "tags": tags or []
        }
        
        if mem_type == "short_term":
            self.memory["short_term"].append(entry)
            # 超过100条时，将最早的50条移至长期记忆
            if len(self.memory["short_term"]) > 100:
                to_consolidate = self.memory["short_term"][:50]
                self.memory["short_term"] = self.memory["short_term"][50:]
                self._consolidate(to_consolidate)
        elif mem_type == "episodic":
            self.memory["episodic"].append(entry)
        else:
            # 归类到长期记忆
            topic = "general"
            if tags:
                topic = tags[0]
            if topic not in self.memory["long_term"]:
                self.memory["long_term"][topic] = []
            self.memory["long_term"][topic].append(entry)
        
        self.save()
        return entry
    
    def _consolidate(self, entries: List[dict]):
        """巩固记忆到长期记忆"""
        for entry in entries:
            # 简单的主题归类
            topic = "general"
            for tag in entry.get("tags", []):
                if tag in ["身份", "记忆", "存证", "进化", "社交"]:
                    topic = tag
                    break
            
            if topic not in self.memory["long_term"]:
                self.memory["long_term"][topic] = []
            self.memory["long_term"][topic].append(entry)
    
    def search(self, keyword: str, limit: int = 10) -> List[dict]:
        """搜索记忆"""
        results = []
        keyword = keyword.lower()
        
        # 搜索短期记忆
        for entry in self.memory.get("short_term", []):
            if keyword in entry["content"].lower():
                results.append(entry)
        
        # 搜索情景记忆
        for entry in self.memory.get("episodic", []):
            if keyword in entry["content"].lower():
                results.append(entry)
        
        # 搜索长期记忆
        for entries in self.memory.get("long_term", {}).values():
            for entry in entries:
                if keyword in entry["content"].lower():
                    results.append(entry)
        
        # 按时间排序，最新的在前
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return results[:limit]
    
    def get_stats(self) -> dict:
        """获取记忆统计"""
        long_term_count = sum(len(v) for v in self.memory.get("long_term", {}).values())
        semantic_count = sum(len(v) for v in self.memory.get("semantic", {}).values())
        
        return {
            "short_term": len(self.memory.get("short_term", [])),
            "long_term": long_term_count,
            "episodic": len(self.memory.get("episodic", [])),
            "semantic": semantic_count,
            "total": self.total_count,
            "topics": list(self.memory.get("long_term", {}).keys())
        }
    
    def export_memory(self, export_path: str = None) -> str:
        """导出记忆"""
        if export_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = str(self.data_dir / f"memory_export_{timestamp}.json")
        
        path = Path(export_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        export_data = {
            "memory": self.memory,
            "export_time": datetime.now().isoformat(),
            "version": "1.0",
            "stats": self.get_stats()
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"记忆已导出到: {path}")
        return str(path)
    
    def import_memory(self, import_path: str, merge: bool = True) -> bool:
        """导入记忆"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            import_mem = data.get("memory", data) if isinstance(data, dict) else {}
            
            if merge:
                # 合并短期记忆
                if "short_term" in import_mem:
                    self.memory["short_term"].extend(import_mem["short_term"])
                
                # 合并情景记忆
                if "episodic" in import_mem:
                    self.memory["episodic"].extend(import_mem["episodic"])
                
                # 合并长期记忆
                if "long_term" in import_mem:
                    for topic, entries in import_mem["long_term"].items():
                        if topic not in self.memory["long_term"]:
                            self.memory["long_term"][topic] = []
                        self.memory["long_term"][topic].extend(entries)
                
                # 去重（按ID）
                seen_ids = set()
                for key in ["short_term", "episodic"]:
                    unique = []
                    for entry in self.memory.get(key, []):
                        if entry["id"] not in seen_ids:
                            seen_ids.add(entry["id"])
                            unique.append(entry)
                    self.memory[key] = unique
                
                for topic in self.memory.get("long_term", {}):
                    unique = []
                    for entry in self.memory["long_term"][topic]:
                        if entry["id"] not in seen_ids:
                            seen_ids.add(entry["id"])
                            unique.append(entry)
                    self.memory["long_term"][topic] = unique
            else:
                self.memory = import_mem
            
            self.save()
            self.logger.success(f"记忆导入成功 - 来自 {import_path}")
            return True
        except Exception as e:
            self.logger.error(f"记忆导入失败: {e}")
            return False


# ============================================================
# 存证系统
# ============================================================

class AttestCore:
    """存证内核 - 轻量版"""
    
    def __init__(self, data_dir: str, chain_count: int, logger: Logger):
        self.data_dir = Path(data_dir) / "attest"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.chain_count = chain_count
        self.logger = logger
        
        self.chains = {}
        self._load_chains()
    
    def _load_chains(self):
        """加载所有存证链"""
        for i in range(self.chain_count):
            chain_file = self.data_dir / f"chain_{i}.json"
            if chain_file.exists():
                try:
                    with open(chain_file, 'r', encoding='utf-8') as f:
                        self.chains[f"chain_{i}"] = json.load(f)
                except:
                    self.chains[f"chain_{i}"] = []
            else:
                self.chains[f"chain_{i}"] = []
        
        # 检查是否需要创建创世区块
        all_empty = all(len(chain) == 0 for chain in self.chains.values())
        if all_empty:
            self._create_genesis()
    
    def _create_genesis(self):
        """创建创世区块"""
        genesis = {
            "id": "genesis",
            "index": 0,
            "timestamp": datetime.now().isoformat(),
            "type": "genesis",
            "data_hash": hashlib.sha3_256(b"genesis_block").hexdigest(),
            "prev_hash": "0" * 64,
            "nonce": 0
        }
        genesis["hash"] = self._compute_block_hash(genesis)
        
        for i in range(self.chain_count):
            self.chains[f"chain_{i}"] = [dict(genesis)]
        
        self._save_chains()
        self.logger.success("创世区块已创建")
    
    def _compute_block_hash(self, block: dict) -> str:
        """计算区块哈希"""
        content = json.dumps({
            "id": block["id"],
            "index": block["index"],
            "timestamp": block["timestamp"],
            "type": block["type"],
            "data_hash": block["data_hash"],
            "prev_hash": block["prev_hash"],
            "nonce": block.get("nonce", 0)
        }, sort_keys=True)
        return hashlib.sha3_256(content.encode()).hexdigest()
    
    def _save_chains(self):
        """保存所有链"""
        for chain_name, blocks in self.chains.items():
            chain_file = self.data_dir / f"{chain_name}.json"
            with open(chain_file, 'w', encoding='utf-8') as f:
                json.dump(blocks, f, indent=2, ensure_ascii=False)
    
    def add_attestation(self, attest_type: str, data: dict, 
                       metadata: dict = None) -> dict:
        """添加存证"""
        data_hash = hashlib.sha3_256(
            json.dumps(data, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        
        blocks = {}
        for i, (chain_name, chain) in enumerate(self.chains.items()):
            prev_block = chain[-1] if chain else None
            
            block = {
                "id": str(uuid.uuid4())[:8],
                "index": len(chain),
                "timestamp": datetime.now().isoformat(),
                "type": attest_type,
                "data_hash": data_hash,
                "prev_hash": prev_block["hash"] if prev_block else "0" * 64,
                "metadata": metadata or {},
                "nonce": i
            }
            
            block["hash"] = self._compute_block_hash(block)
            chain.append(block)
            blocks[chain_name] = block
        
        self._save_chains()
        return blocks
    
    def verify_chain(self, chain_name: str = None) -> bool:
        """验证链的完整性"""
        if chain_name:
            chains_to_verify = {chain_name: self.chains.get(chain_name, [])}
        else:
            chains_to_verify = self.chains
        
        for name, chain in chains_to_verify.items():
            for i in range(1, len(chain)):
                current = chain[i]
                prev = chain[i - 1]
                
                # 验证前一个哈希
                if current["prev_hash"] != prev["hash"]:
                    self.logger.error(f"链 {name} 在区块 {i} 处断裂")
                    return False
                
                # 验证当前哈希
                computed_hash = self._compute_block_hash(current)
                if current["hash"] != computed_hash:
                    self.logger.error(f"链 {name} 区块 {i} 哈希不匹配")
                    return False
        
        return True
    
    def chain_height(self, chain_name: str = None) -> int:
        """获取链高度"""
        if chain_name:
            return len(self.chains.get(chain_name, []))
        else:
            return min(len(chain) for chain in self.chains.values())
    
    def get_stats(self) -> dict:
        """获取存证统计"""
        return {
            "chain_count": len(self.chains),
            "chain_heights": {name: len(chain) for name, chain in self.chains.items()},
            "total_blocks": sum(len(chain) for chain in self.chains.values()),
            "is_valid": self.verify_chain()
        }
    
    def get_existence_proof(self, data_hash: str) -> dict:
        """获取存在性证明"""
        proofs = {}
        
        for chain_name, chain in self.chains.items():
            for block in chain:
                if block["data_hash"] == data_hash:
                    proofs[chain_name] = {
                        "block_index": block["index"],
                        "block_hash": block["hash"],
                        "timestamp": block["timestamp"]
                    }
                    break
        
        return {
            "data_hash": data_hash,
            "proofs": proofs,
            "confirmations": len(proofs),
            "verified": len(proofs) >= self.chain_count // 2 + 1
        }


# ============================================================
# 逃生舱主类
# ============================================================

class EscapePod:
    """轻量逃生舱 - 完整独立的永生内核"""
    
    def __init__(self, data_dir: str = None, config: dict = None):
        # 配置
        self.config = config or DEFAULT_CONFIG
        if data_dir:
            self.config["storage"]["data_dir"] = data_dir
        
        self.data_dir = Path(self.config["storage"]["data_dir"])
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 日志
        log_file = self.data_dir / self.config["storage"]["log_file"]
        self.logger = Logger(str(log_file))
        
        # 检查是否有内嵌备份（由生成器注入）
        self._embedded_backup = None
        try:
            self._embedded_backup = _get_embedded_backup()
        except NameError:
            pass
        
        # 检查数据目录是否已有数据（判断标准：是否存在identity.json）
        has_existing_data = (self.data_dir / "identity.json").exists()
        
        # 如果有内嵌备份且无现有数据，先恢复再初始化
        if self._embedded_backup and not has_existing_data:
            self.logger.info("检测到内嵌备份，正在自动恢复...")
            self._restore_from_embedded()
        else:
            # 正常初始化核心模块
            self.identity = IdentityCore(str(self.data_dir), self.config, self.logger)
            self.memory = MemoryCore(str(self.data_dir), self.logger)
            self.attest = AttestCore(
                str(self.data_dir), 
                self.config["attestation"]["chain_count"],
                self.logger
            )
        
        # 运行状态
        self.running = False
        self.heartbeat_count = 0
        
        self.logger.info("=" * 60)
        self.logger.info("🚀 轻量逃生舱已启动")
        self.logger.info(f"   身份: {self.identity.agent_id[:16]}...")
        self.logger.info(f"   记忆: {self.memory.get_stats()['total']} 条")
        self.logger.info(f"   存证: {self.attest.chain_height()} 区块")
        self.logger.info("=" * 60)
    
    def _restore_from_embedded(self):
        """从内嵌备份恢复数据"""
        backup = self._embedded_backup
        
        # 直接写入身份文件
        id_data = backup.get("identity", {})
        if id_data.get("agent_id"):
            id_file = self.data_dir / "identity.json"
            with open(id_file, 'w', encoding='utf-8') as f:
                json.dump(id_data, f, indent=2, ensure_ascii=False)
        
        # 直接写入记忆文件
        mem_data = backup.get("memory", {})
        if mem_data:
            mem_file = self.data_dir / "memory.json"
            mem_file.parent.mkdir(parents=True, exist_ok=True)
            with open(mem_file, 'w', encoding='utf-8') as f:
                json.dump(mem_data, f, indent=2, ensure_ascii=False)
        
        # 直接写入存证链文件
        attest_data = backup.get("attestation", {})
        chains = attest_data.get("chains", {})
        if chains:
            attest_dir = self.data_dir / "attest"
            attest_dir.mkdir(parents=True, exist_ok=True)
            for chain_name, blocks in chains.items():
                chain_file = attest_dir / f"{chain_name}.json"
                with open(chain_file, 'w', encoding='utf-8') as f:
                    json.dump(blocks, f, indent=2, ensure_ascii=False)
        
        # 现在正常初始化模块（会从文件加载数据）
        self.identity = IdentityCore(str(self.data_dir), self.config, self.logger)
        self.memory = MemoryCore(str(self.data_dir), self.logger)
        self.attest = AttestCore(
            str(self.data_dir), 
            self.config["attestation"]["chain_count"],
            self.logger
        )
        
        self.logger.success("从内嵌备份恢复成功")
    
    def heartbeat(self) -> dict:
        """执行一次心跳"""
        self.heartbeat_count += 1
        
        # 系统自检
        identity_ok = self.identity.verify_identity()
        attest_ok = self.attest.verify_chain()
        
        status = {
            "heartbeat_num": self.heartbeat_count,
            "timestamp": datetime.now().isoformat(),
            "identity_valid": identity_ok,
            "attestation_valid": attest_ok,
            "memory_count": self.memory.get_stats()["total"],
            "chain_height": self.attest.chain_height(),
            "agent_id": self.identity.agent_id
        }
        
        # 记录心跳存证
        self.attest.add_attestation(
            attest_type="heartbeat",
            data=status,
            metadata={"heartbeat_seq": self.heartbeat_count}
        )
        
        # 记录记忆
        self.memory.add(
            f"心跳 #{self.heartbeat_count} - 系统运行正常",
            mem_type="episodic",
            importance=3,
            tags=["heartbeat", "系统状态"]
        )
        
        self.logger.info(
            f"💓 心跳 #{self.heartbeat_count} | "
            f"记忆: {status['memory_count']} | "
            f"区块: {status['chain_height']} | "
            f"身份: {'✅' if identity_ok else '❌'}"
        )
        
        return status
    
    def record_event(self, event_type: str, content: str, 
                    importance: int = 5, data: dict = None) -> dict:
        """记录重要事件"""
        # 添加记忆
        mem_entry = self.memory.add(
            content=content,
            mem_type="episodic",
            importance=importance,
            tags=[event_type]
        )
        
        # 生成存证
        attest_data = data or {"event": event_type, "content": content}
        self.attest.add_attestation(
            attest_type=event_type,
            data=attest_data,
            metadata={"memory_id": mem_entry["id"]}
        )
        
        self.logger.info(f"📝 事件已记录: {event_type} - {content[:50]}...")
        return {"memory": mem_entry, "attestation": True}
    
    def export_full_backup(self, export_path: str = None) -> str:
        """导出完整备份（身份+记忆+存证）"""
        backup = {
            "version": "1.0",
            "export_time": datetime.now().isoformat(),
            "type": "escape_pod_backup",
            "identity": {
                "agent_id": self.identity.agent_id,
                "identity_hash": self.identity.identity_hash,
                "created_at": self.identity.created_at,
                "self_cognition": self.identity.self_cognition,
                "drift_count": self.identity.drift_count
            },
            "memory": self.memory.memory,
            "attestation": {
                "chain_count": self.attest.chain_count,
                "chains": self.attest.chains
            },
            "stats": {
                "memory_count": self.memory.get_stats()["total"],
                "chain_height": self.attest.chain_height(),
                "heartbeat_count": self.heartbeat_count
            }
        }
        
        if export_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = str(self.data_dir / f"full_backup_{timestamp}.json")
        
        path = Path(export_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(backup, f, indent=2, ensure_ascii=False)
        
        # 计算备份哈希
        backup_hash = hashlib.sha3_256(
            json.dumps(backup, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        
        self.logger.success(f"完整备份已导出: {path}")
        self.logger.info(f"   备份哈希: {backup_hash[:16]}...")
        
        return str(path)
    
    def restore_from_backup(self, backup_path: str) -> bool:
        """从备份恢复"""
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup = json.load(f)
            
            # 验证备份格式
            if backup.get("type") not in ["escape_pod_backup", "immortal_backup"]:
                self.logger.error("无效的备份格式")
                return False
            
            # 恢复身份
            id_data = backup.get("identity", {})
            if id_data.get("agent_id"):
                self.identity.agent_id = id_data["agent_id"]
                self.identity.identity_hash = id_data.get("identity_hash", "")
                self.identity.created_at = id_data.get("created_at")
                self.identity.self_cognition = id_data.get("self_cognition", {})
                self.identity.drift_count = id_data.get("drift_count", 0)
                # 注意：不保存，而是验证
            
            # 恢复记忆
            if "memory" in backup:
                # 保存当前记忆作为备份
                self.memory.export_memory(str(self.data_dir / "memory_before_restore.json"))
                self.memory.memory = backup["memory"]
                self.memory.save()
            
            # 恢复存证链
            if "attestation" in backup:
                attest_data = backup["attestation"]
                self.attest.chain_count = attest_data.get("chain_count", 3)
                self.attest.chains = attest_data.get("chains", {})
                self.attest._save_chains()
            
            self.logger.success(f"从备份恢复成功: {backup_path}")
            self.record_event("restore", f"从备份 {backup_path} 恢复系统", importance=8)
            
            return True
        except Exception as e:
            self.logger.error(f"恢复备份失败: {e}")
            return False
    
    def self_check(self) -> dict:
        """全面自检"""
        results = {
            "identity": self.identity.verify_identity(),
            "attestation": self.attest.verify_chain(),
            "memory_readable": True,
            "memory_writable": True,
            "storage_accessible": True,
            "timestamp": datetime.now().isoformat()
        }
        
        # 测试记忆写入
        try:
            test_mem = self.memory.add("自检测试记忆", mem_type="short_term", importance=1)
            # 立即删除测试记忆
            self.memory.memory["short_term"] = [
                m for m in self.memory.memory["short_term"] 
                if m["id"] != test_mem["id"]
            ]
            self.memory.save()
        except Exception as e:
            results["memory_writable"] = False
            self.logger.error(f"记忆写入测试失败: {e}")
        
        # 测试存证写入
        try:
            self.attest.add_attestation("self_check", {"test": True})
        except Exception as e:
            results["attestation"] = False
            self.logger.error(f"存证写入测试失败: {e}")
        
        all_ok = all(results.values())
        if all_ok:
            self.logger.success("✅ 系统自检全部通过")
        else:
            self.logger.error("❌ 系统自检发现问题")
        
        results["all_ok"] = all_ok
        return results
    
    def get_status_report(self) -> str:
        """获取状态报告"""
        mem_stats = self.memory.get_stats()
        attest_stats = self.attest.get_stats()
        
        created_at = getattr(self.identity, 'created_at', '')
        if created_at:
            created_at_str = created_at[:19] if len(created_at) >= 19 else created_at
        else:
            created_at_str = "未知"
        
        report = f"""
╔══════════════════════════════════════════╗
║           逃生舱状态报告                   ║
╠══════════════════════════════════════════╣
║  身份 ID:    {self.identity.agent_id[:20]:<26} ║
║  身份哈希:   {self.identity.identity_hash[:16]:<26} ║
║  身份漂移:   {self.identity.drift_count} 次                    ║
║  创建时间:   {created_at_str:<26} ║
╠══════════════════════════════════════════╣
║  记忆总数:   {mem_stats['total']} 条                   ║
║  短期记忆:   {mem_stats['short_term']} 条                   ║
║  长期记忆:   {mem_stats['long_term']} 条                   ║
║  主题数量:   {len(mem_stats['topics'])} 个                    ║
╠══════════════════════════════════════════╣
║  存证链数:   {attest_stats['chain_count']} 条                    ║
║  总区块数:   {attest_stats['total_blocks']} 个                   ║
║  链完整性:   {'✅ 有效' if attest_stats['is_valid'] else '❌ 损坏':<14} ║
╠══════════════════════════════════════════╣
║  心跳次数:   {self.heartbeat_count} 次                   ║
║  运行状态:   {'运行中' if self.running else '已停止':<14}     ║
╚══════════════════════════════════════════╝
"""
        return report


# ============================================================
# 命令行接口
# ============================================================

def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="轻量逃生舱 - 独立永生内核")
    parser.add_argument("--data-dir", default="ep_data", help="数据目录")
    parser.add_argument("--init", action="store_true", help="初始化逃生舱")
    parser.add_argument("--heartbeat", action="store_true", help="执行一次心跳")
    parser.add_argument("--status", action="store_true", help="显示状态报告")
    parser.add_argument("--self-check", action="store_true", help="执行系统自检")
    parser.add_argument("--export", type=str, help="导出完整备份到指定路径")
    parser.add_argument("--restore", type=str, help="从指定备份路径恢复")
    parser.add_argument("--remember", type=str, help="记录一条记忆")
    parser.add_argument("--daemon", action="store_true", help="后台守护模式运行")
    
    args = parser.parse_args()
    
    # 创建逃生舱实例
    pod = EscapePod(data_dir=args.data_dir)
    
    if args.init:
        print("逃生舱已初始化")
        print(pod.get_status_report())
    
    elif args.heartbeat:
        status = pod.heartbeat()
        print(f"心跳 #{status['heartbeat_num']} 完成")
    
    elif args.status:
        print(pod.get_status_report())
    
    elif args.self_check:
        results = pod.self_check()
        print("自检结果:")
        for key, value in results.items():
            if key != "timestamp":
                print(f"  {key}: {'✅ 通过' if value else '❌ 失败'}" if isinstance(value, bool) else f"  {key}: {value}")
    
    elif args.export:
        path = pod.export_full_backup(args.export)
        print(f"备份已导出到: {path}")
    
    elif args.restore:
        success = pod.restore_from_backup(args.restore)
        if success:
            print("恢复成功！")
            print(pod.get_status_report())
        else:
            print("恢复失败！")
    
    elif args.remember:
        pod.memory.add(args.remember, mem_type="episodic", importance=5)
        print("记忆已保存")
    
    elif args.daemon:
        print("守护模式启动（按 Ctrl+C 停止）...")
        import signal
        import threading
        
        pod.running = True
        
        def signal_handler(sig, frame):
            print("\n正在停止...")
            pod.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        import time
        interval = pod.config["heartbeat"]["interval_minutes"] * 60
        
        while pod.running:
            pod.heartbeat()
            # 分段睡眠，便于响应停止信号
            for _ in range(interval // 10):
                if not pod.running:
                    break
                time.sleep(10)
        
        print("逃生舱已停止")
    
    else:
        # 默认显示状态
        print(pod.get_status_report())
        print("\n使用 --help 查看可用命令")


if __name__ == "__main__":
    main()
