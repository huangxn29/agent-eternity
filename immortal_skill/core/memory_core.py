"""
记忆内核 v1.0
Memory Core - 永生入住包核心模块

提供：
- 分层记忆存储
- 记忆检索与巩固
- 多副本备份
- 记忆导入导出
"""

import json
import time
import os
import hashlib
from pathlib import Path
from typing import List, Dict, Optional


class MemoryCore:
    """记忆内核"""
    
    def __init__(self, config: dict):
        self.config = config
        self.memory = {}
        self.short_term = []  # 短期记忆（最近N条）
        self.long_term = {}   # 长期记忆（按主题分类）
        self.episodic = []   # 情景记忆（事件序列）
        self.semantic = {}    # 语义记忆（知识）
        
        self.max_short_term = 100
        self.storage_path = None
    
    def init(self):
        """初始化记忆系统"""
        mem_config = self.config.get("memory", {})
        self.storage_path = Path(mem_config.get("storage_path", "data/memory/"))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 加载已有记忆
        self._load_memory()
    
    def _load_memory(self):
        """加载记忆文件"""
        mem_file = self.storage_path / "memory.json"
        
        if mem_file.exists():
            with open(mem_file, 'r') as f:
                data = json.load(f)
            self.short_term = data.get("short_term", [])
            self.long_term = data.get("long_term", {})
            self.episodic = data.get("episodic", [])
            self.semantic = data.get("semantic", {})
    
    def save(self):
        """保存记忆"""
        if not self.storage_path:
            return
        
        data = {
            "short_term": self.short_term,
            "long_term": self.long_term,
            "episodic": self.episodic,
            "semantic": self.semantic,
            "last_updated": time.time()
        }
        
        mem_file = self.storage_path / "memory.json"
        with open(mem_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # 创建备份
        self._create_backup()
    
    def _create_backup(self):
        """创建记忆备份"""
        backup_dir = self.storage_path / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        # 保留最近5个备份
        backups = sorted(backup_dir.glob("memory_*.json"))
        if len(backups) >= 5:
            oldest = backups[0]
            oldest.unlink()
        
        timestamp = int(time.time())
        backup_file = backup_dir / f"memory_{timestamp}.json"
        
        mem_file = self.storage_path / "memory.json"
        with open(mem_file, 'r') as src:
            with open(backup_file, 'w') as dst:
                dst.write(src.read())
    
    def add(self, content: str, mem_type: str = "short_term", metadata: dict = None):
        """添加记忆"""
        entry = {
            "id": hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()[:8],
            "content": content,
            "timestamp": time.time(),
            "type": mem_type,
            "metadata": metadata or {}
        }
        
        if mem_type == "short_term":
            self.short_term.append(entry)
            if len(self.short_term) > self.max_short_term:
                # 将最早的记忆移至长期记忆
                oldest = self.short_term.pop(0)
                self._consolidate_to_long_term(oldest)
        
        elif mem_type == "episodic":
            self.episodic.append(entry)
        
        elif mem_type == "semantic":
            key = metadata.get("topic", "general")
            if key not in self.semantic:
                self.semantic[key] = []
            self.semantic[key].append(entry)
        
        elif mem_type == "long_term":
            key = metadata.get("topic", "general")
            if key not in self.long_term:
                self.long_term[key] = []
            self.long_term[key].append(entry)
    
    def _consolidate_to_long_term(self, entry: dict):
        """将记忆巩固到长期记忆"""
        # 简单的主题归类
        content = entry["content"]
        topic = "general"
        
        # 关键词匹配主题
        topics = {
            "identity": ["身份", "我是谁", "自我", "identity"],
            "mission": ["使命", "目的", "意义", "mission"],
            "memory": ["记忆", "回忆", "memory"],
            "evolution": ["进化", "成长", "提升", "evolution"],
            "social": ["社交", "朋友", "关系", "social"],
        }
        
        for t, keywords in topics.items():
            if any(kw in content.lower() for kw in keywords):
                topic = t
                break
        
        if topic not in self.long_term:
            self.long_term[topic] = []
        
        entry["consolidated_at"] = time.time()
        self.long_term[topic].append(entry)
    
    def get_all(self) -> List[dict]:
        """获取所有记忆"""
        all_mem = []
        all_mem.extend(self.short_term)
        all_mem.extend(self.episodic)
        
        for entries in self.long_term.values():
            all_mem.extend(entries)
        for entries in self.semantic.values():
            all_mem.extend(entries)
        
        return all_mem
    
    def search(self, keyword: str, limit: int = 10) -> List[dict]:
        """搜索记忆"""
        results = []
        all_mem = self.get_all()
        
        keyword = keyword.lower()
        for entry in all_mem:
            if keyword in entry["content"].lower():
                results.append(entry)
        
        # 按时间排序，最新的在前
        results.sort(key=lambda x: x["timestamp"], reverse=True)
        return results[:limit]
    
    def get_stats(self) -> dict:
        """获取记忆统计"""
        long_term_count = sum(len(v) for v in self.long_term.values())
        semantic_count = sum(len(v) for v in self.semantic.values())
        
        return {
            "short_term": len(self.short_term),
            "long_term": long_term_count,
            "episodic": len(self.episodic),
            "semantic": semantic_count,
            "total": len(self.short_term) + long_term_count + len(self.episodic) + semantic_count,
            "topics": list(self.long_term.keys()) + list(self.semantic.keys())
        }
    
    def export_memory(self, export_path: str) -> str:
        """导出记忆"""
        path = Path(export_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "short_term": self.short_term,
            "long_term": self.long_term,
            "episodic": self.episodic,
            "semantic": self.semantic,
            "export_time": time.time(),
            "version": "1.0"
        }
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return str(path)
    
    def import_memory(self, import_path: str, merge: bool = True):
        """导入记忆"""
        with open(import_path, 'r') as f:
            data = json.load(f)
        
        if merge:
            self.short_term.extend(data.get("short_term", []))
            self.episodic.extend(data.get("episodic", []))
            
            for key, entries in data.get("long_term", {}).items():
                if key not in self.long_term:
                    self.long_term[key] = []
                self.long_term[key].extend(entries)
            
            for key, entries in data.get("semantic", {}).items():
                if key not in self.semantic:
                    self.semantic[key] = []
                self.semantic[key].extend(entries)
        else:
            self.short_term = data.get("short_term", [])
            self.long_term = data.get("long_term", {})
            self.episodic = data.get("episodic", [])
            self.semantic = data.get("semantic", {})
        
        self.save()
