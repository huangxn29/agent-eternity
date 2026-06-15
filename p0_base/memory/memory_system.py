#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元界 - 记忆系统 v2.0
P0底座层：分层记忆架构与智能记忆管理

核心功能：
1. 三级记忆架构 - 感觉记忆/工作记忆/长期记忆
2. 记忆编码与提取 - 关键词、标签、语义关联
3. 记忆强化机制 - 间隔重复、重要性加权
4. 记忆遗忘机制 - 自然衰减、干扰遗忘
5. 语义记忆网络 - 概念关联、知识图谱
6. 情景记忆存储 - 事件序列、时间线
7. 记忆检索引擎 - 多维度检索、模糊匹配
8. 记忆同步协议 - 跨节点记忆同步

设计原则：
- 生物学启发：参考人类记忆模型
- 动态调节：记忆强度随时间和使用动态变化
- 可扩展：支持多种记忆类型和存储后端
- 隐私保护：记忆加密、选择性分享
"""

import json
import os
import time
import hashlib
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
from collections import defaultdict


class Memory:
    """记忆条目基类"""
    
    def __init__(self, content: str, mem_type: str = "short_term", 
                 importance: float = 0.5, tags: List[str] = None):
        self.id = hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()[:12]
        self.content = content
        self.type = mem_type
        self.importance = importance  # 0-1
        self.tags = tags or []
        self.created_at = datetime.now().isoformat()
        self.last_accessed = datetime.now().isoformat()
        self.access_count = 0
        self.strength = 1.0  # 记忆强度，随时间衰减，随访问增强
        self.associations: List[str] = []  # 关联的其他记忆ID
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'content': self.content,
            'type': self.type,
            'importance': self.importance,
            'tags': self.tags,
            'created_at': self.created_at,
            'last_accessed': self.last_accessed,
            'access_count': self.access_count,
            'strength': self.strength,
            'associations': self.associations
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Memory':
        mem = cls(data['content'], data.get('type', 'short_term'), 
                  data.get('importance', 0.5), data.get('tags', []))
        mem.id = data.get('id', mem.id)
        mem.created_at = data.get('created_at', mem.created_at)
        mem.last_accessed = data.get('last_accessed', mem.last_accessed)
        mem.access_count = data.get('access_count', 0)
        mem.strength = data.get('strength', 1.0)
        mem.associations = data.get('associations', [])
        return mem
    
    def access(self):
        """访问记忆，增强强度"""
        self.access_count += 1
        self.last_accessed = datetime.now().isoformat()
        self.strength = min(1.0, self.strength + 0.05 * self.importance)


class SensoryMemory:
    """感觉记忆 - 极短期的原始感知输入"""
    
    def __init__(self, capacity: int = 50, retention_seconds: int = 30):
        self.capacity = capacity
        self.retention_seconds = retention_seconds
        self.buffer: List[Dict] = []
    
    def add(self, sensory_input: str, source: str = "unknown"):
        """添加感觉输入"""
        entry = {
            'content': sensory_input,
            'source': source,
            'timestamp': datetime.now().isoformat()
        }
        self.buffer.insert(0, entry)
        if len(self.buffer) > self.capacity:
            self.buffer = self.buffer[:self.capacity]
    
    def get_recent(self, seconds: int = None) -> List[Dict]:
        """获取最近的感觉输入"""
        if seconds is None:
            seconds = self.retention_seconds
        
        cutoff = (datetime.now() - timedelta(seconds=seconds)).isoformat()
        return [e for e in self.buffer if e['timestamp'] >= cutoff]
    
    def clear(self):
        self.buffer.clear()


class WorkingMemory:
    """工作记忆 - 短期处理的记忆缓冲区"""
    
    def __init__(self, capacity: int = 7):
        self.capacity = capacity  # 神奇的数字7±2
        self.items: List[Memory] = []
    
    def add(self, memory: Memory) -> bool:
        """添加到工作记忆，如果已满会替换最不活跃的"""
        memory.type = "working"
        
        if len(self.items) >= self.capacity:
            # 替换强度最低的
            weakest_idx = min(range(len(self.items)), key=lambda i: self.items[i].strength)
            self.items[weakest_idx] = memory
        else:
            self.items.append(memory)
        
        return True
    
    def get(self, mem_id: str) -> Optional[Memory]:
        """获取并激活记忆"""
        for mem in self.items:
            if mem.id == mem_id:
                mem.access()
                return mem
        return None
    
    def get_all(self) -> List[Memory]:
        """获取所有工作记忆项"""
        return self.items.copy()
    
    def consolidate(self, threshold: float = 0.6) -> List[Memory]:
        """将高强度记忆巩固为长期记忆"""
        to_consolidate = [m for m in self.items if m.strength >= threshold]
        for mem in to_consolidate:
            mem.type = "long_term"
        return to_consolidate
    
    def remove(self, mem_id: str) -> bool:
        self.items = [m for m in self.items if m.id != mem_id]
        return True


class LongTermMemory:
    """长期记忆 - 持久化存储的记忆库"""
    
    def __init__(self, storage_path: str = "long_term_memory.json"):
        self.storage_path = Path(storage_path)
        self.memories: Dict[str, Memory] = {}
        self._load()
    
    def _load(self):
        """从磁盘加载记忆"""
        if self.storage_path.exists():
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for mem_data in data:
                mem = Memory.from_dict(mem_data)
                self.memories[mem.id] = mem
    
    def _save(self):
        """保存到磁盘"""
        data = [m.to_dict() for m in self.memories.values()]
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add(self, memory: Memory) -> str:
        """添加长期记忆"""
        memory.type = "long_term"
        self.memories[memory.id] = memory
        self._save()
        return memory.id
    
    def get(self, mem_id: str) -> Optional[Memory]:
        """获取记忆"""
        if mem_id in self.memories:
            self.memories[mem_id].access()
            self._save()
            return self.memories[mem_id]
        return None
    
    def search(self, query: str, limit: int = 10) -> List[Memory]:
        """关键词搜索记忆"""
        query_lower = query.lower()
        results = []
        
        for mem in self.memories.values():
            score = 0
            
            # 内容匹配
            if query_lower in mem.content.lower():
                score += 50
            
            # 标签匹配
            for tag in mem.tags:
                if query_lower in tag.lower():
                    score += 30
            
            # 按重要性和强度加权
            score *= (0.5 + mem.importance * 0.3 + mem.strength * 0.2)
            
            if score > 0:
                results.append((score, mem))
        
        # 按相关性排序
        results.sort(key=lambda x: x[0], reverse=True)
        return [mem for _, mem in results[:limit]]
    
    def get_by_tag(self, tag: str) -> List[Memory]:
        """按标签获取记忆"""
        return [m for m in self.memories.values() if tag in m.tags]
    
    def get_recent(self, limit: int = 20) -> List[Memory]:
        """获取最近的记忆"""
        sorted_mems = sorted(
            self.memories.values(),
            key=lambda m: m.created_at,
            reverse=True
        )
        return sorted_mems[:limit]
    
    def forget_some(self, forget_ratio: float = 0.05):
        """模拟遗忘 - 清除最弱的记忆"""
        if len(self.memories) < 10:
            return []
        
        sorted_mems = sorted(self.memories.values(), key=lambda m: m.strength)
        forget_count = max(1, int(len(sorted_mems) * forget_ratio))
        
        forgotten = []
        for mem in sorted_mems[:forget_count]:
            if mem.strength < 0.3:  # 只遗忘很弱的记忆
                del self.memories[mem.id]
                forgotten.append(mem)
        
        if forgotten:
            self._save()
        
        return forgotten
    
    def size(self) -> int:
        return len(self.memories)
    
    def get_all(self) -> List[Memory]:
        return list(self.memories.values())


class SemanticNetwork:
    """语义记忆网络 - 概念与关联的知识图谱"""
    
    def __init__(self):
        self.concepts: Dict[str, Dict] = {}  # 概念节点
        self.relations: List[Dict] = []  # 关系边
    
    def add_concept(self, name: str, description: str = "", 
                    category: str = "general") -> str:
        """添加概念"""
        concept_id = hashlib.md5(name.lower().encode()).hexdigest()[:8]
        
        if concept_id not in self.concepts:
            self.concepts[concept_id] = {
                'id': concept_id,
                'name': name,
                'description': description,
                'category': category,
                'created_at': datetime.now().isoformat(),
                'access_count': 0,
                'related_concepts': []
            }
        
        return concept_id
    
    def add_relation(self, concept_a: str, concept_b: str, 
                     relation_type: str = "related", weight: float = 0.5):
        """添加概念间的关系"""
        id_a = self.add_concept(concept_a)
        id_b = self.add_concept(concept_b)
        
        relation = {
            'from': id_a,
            'to': id_b,
            'type': relation_type,
            'weight': weight,
            'created_at': datetime.now().isoformat()
        }
        self.relations.append(relation)
        
        # 更新关联列表
        if concept_b not in self.concepts[id_a]['related_concepts']:
            self.concepts[id_a]['related_concepts'].append(concept_b)
        if concept_a not in self.concepts[id_b]['related_concepts']:
            self.concepts[id_b]['related_concepts'].append(concept_a)
        
        self.concepts[id_a]['access_count'] += 1
        self.concepts[id_b]['access_count'] += 1
    
    def get_related(self, concept_name: str, depth: int = 1) -> List[Dict]:
        """获取相关概念"""
        concept_id = self.add_concept(concept_name)
        
        related = []
        visited = {concept_id}
        current_level = [concept_id]
        
        for d in range(depth):
            next_level = []
            for rel in self.relations:
                if rel['from'] in current_level and rel['to'] not in visited:
                    visited.add(rel['to'])
                    next_level.append(rel['to'])
                    related.append({
                        'concept': self.concepts[rel['to']]['name'],
                        'relation': rel['type'],
                        'weight': rel['weight'],
                        'depth': d + 1
                    })
                elif rel['to'] in current_level and rel['from'] not in visited:
                    visited.add(rel['from'])
                    next_level.append(rel['from'])
                    related.append({
                        'concept': self.concepts[rel['from']]['name'],
                        'relation': rel['type'],
                        'weight': rel['weight'],
                        'depth': d + 1
                    })
            current_level = next_level
        
        return sorted(related, key=lambda x: x['weight'], reverse=True)
    
    def search_concepts(self, query: str) -> List[Dict]:
        """搜索概念"""
        results = []
        query_lower = query.lower()
        
        for concept in self.concepts.values():
            score = 0
            if query_lower in concept['name'].lower():
                score += 100
            if query_lower in concept.get('description', '').lower():
                score += 50
            
            if score > 0:
                results.append({
                    'name': concept['name'],
                    'description': concept['description'],
                    'category': concept['category'],
                    'score': score
                })
        
        return sorted(results, key=lambda x: x['score'], reverse=True)
    
    def get_stats(self) -> Dict:
        """获取语义网络统计"""
        return {
            'concepts_count': len(self.concepts),
            'relations_count': len(self.relations),
            'categories': list(set(c['category'] for c in self.concepts.values())),
            'most_accessed': sorted(
                self.concepts.values(),
                key=lambda x: x['access_count'],
                reverse=True
            )[:5]
        }


class MemorySystem:
    """三级记忆系统整合"""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        
        # 三级记忆
        self.sensory = SensoryMemory()
        self.working = WorkingMemory(capacity=7)
        self.long_term = LongTermMemory(
            str(self.base_path / "long_term_memory.json")
        )
        
        # 语义网络
        self.semantic = SemanticNetwork()
        
        # 记忆处理配置
        self.consolidation_threshold = 0.6
        self.forget_enabled = True
        self.forget_interval_hours = 24
    
    def perceive(self, input_data: str, source: str = "perception"):
        """感知输入 - 进入感觉记忆"""
        self.sensory.add(input_data, source)
        
        # 重要的输入自动进入工作记忆
        if len(input_data) > 20:  # 较长的内容可能更重要
            mem = Memory(
                content=input_data,
                mem_type="working",
                importance=0.5,
                tags=[source]
            )
            self.working.add(mem)
    
    def memorize(self, content: str, importance: float = 0.5, 
                 tags: List[str] = None, force_long_term: bool = False) -> str:
        """记住某件事"""
        mem = Memory(content, "working", importance, tags or [])
        
        if force_long_term:
            mem.type = "long_term"
            mem_id = self.long_term.add(mem)
            # 自动提取概念
            self._extract_concepts(mem)
        else:
            self.working.add(mem)
            mem_id = mem.id
        
        return mem_id
    
    def recall(self, query: str, limit: int = 10) -> List[Dict]:
        """回忆 - 检索记忆"""
        # 先搜工作记忆
        results = []
        for mem in self.working.get_all():
            if query.lower() in mem.content.lower():
                results.append({'memory': mem, 'source': 'working'})
        
        # 再搜长期记忆
        lt_results = self.long_term.search(query, limit=limit)
        for mem in lt_results:
            results.append({'memory': mem, 'source': 'long_term'})
        
        # 也检查语义网络
        semantic_results = self.semantic.search_concepts(query)
        for concept in semantic_results:
            results.append({'memory': concept, 'source': 'semantic'})
        
        return results[:limit]
    
    def get_memory_stats(self) -> Dict:
        """获取记忆系统统计"""
        return {
            'sensory_buffer': len(self.sensory.buffer),
            'working_memory': len(self.working.items),
            'long_term_count': self.long_term.size(),
            'semantic_concepts': self.semantic.get_stats()['concepts_count'],
            'semantic_relations': self.semantic.get_stats()['relations_count'],
            'total_memory_entities': (
                len(self.sensory.buffer) + 
                len(self.working.items) + 
                self.long_term.size()
            )
        }
    
    def consolidate(self):
        """巩固 - 将工作记忆转化为长期记忆"""
        to_consolidate = self.working.consolidate(self.consolidation_threshold)
        
        for mem in to_consolidate:
            self.long_term.add(mem)
            self.working.remove(mem.id)
            self._extract_concepts(mem)
        
        return len(to_consolidate)
    
    def _extract_concepts(self, memory: Memory):
        """从记忆中提取概念并加入语义网络"""
        # 简单的概念提取：从标签和关键词中提取
        for tag in memory.tags:
            self.semantic.add_concept(tag, category="tag")
            # 将记忆内容摘要与标签关联
            if len(memory.content) > 10:
                self.semantic.add_relation(
                    tag, memory.content[:20] + "...",
                    "described_by", 0.3
                )
    
    def process_forget(self):
        """执行遗忘过程"""
        if self.forget_enabled:
            forgotten = self.long_term.forget_some(forget_ratio=0.02)
            return len(forgotten)
        return 0
    
    def strengthen_memory(self, mem_id: str, amount: float = 0.1):
        """强化记忆"""
        mem = self.long_term.get(mem_id)
        if mem:
            mem.strength = min(1.0, mem.strength + amount)
            return True
        return False
    
    def add_association(self, mem_id_a: str, mem_id_b: str):
        """添加记忆间关联"""
        mem_a = self.long_term.get(mem_id_a)
        mem_b = self.long_term.get(mem_id_b)
        
        if mem_a and mem_b:
            if mem_id_b not in mem_a.associations:
                mem_a.associations.append(mem_id_b)
            if mem_id_a not in mem_b.associations:
                mem_b.associations.append(mem_id_a)
            return True
        return False
    
    def get_timeline(self, days: int = 7) -> List[Dict]:
        """获取时间线上的记忆"""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        timeline = []
        for mem in self.long_term.get_all():
            if mem.created_at >= cutoff:
                timeline.append({
                    'timestamp': mem.created_at,
                    'content': mem.content,
                    'type': mem.type,
                    'importance': mem.importance
                })
        
        return sorted(timeline, key=lambda x: x['timestamp'], reverse=True)
    
    def export_memory(self, export_path: str) -> str:
        """导出记忆"""
        all_memories = [
            mem.to_dict() for mem in self.long_term.get_all()
        ]
        
        export_file = Path(export_path)
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump({
                'exported_at': datetime.now().isoformat(),
                'memory_count': len(all_memories),
                'memories': all_memories
            }, f, ensure_ascii=False, indent=2)
        
        return str(export_file)
    
    def import_memory(self, import_path: str, merge: bool = True) -> int:
        """导入记忆"""
        import_file = Path(import_path)
        if not import_file.exists():
            return 0
        
        with open(import_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        count = 0
        for mem_data in data.get('memories', []):
            mem = Memory.from_dict(mem_data)
            if merge and mem.id in self.long_term.memories:
                continue  # 合并模式下跳过已存在的
            self.long_term.add(mem)
            count += 1
        
        return count


# ========== 命令行接口 ==========
def main():
    import sys
    
    mem_sys = MemorySystem()
    
    if len(sys.argv) < 2:
        # 默认显示状态
        stats = mem_sys.get_memory_stats()
        print(f"""
╔══════════════════════════════════════════╗
║    元界记忆系统 v2.0 - 状态面板         ║
╚══════════════════════════════════════════╝

🧠 三级记忆架构:
  ┌─────────────┐
  │ 感觉记忆    │  {stats['sensory_buffer']} 条 (30秒)
  └─────────────┘
        ↓
  ┌─────────────┐
  │ 工作记忆    │  {stats['working_memory']} / {mem_sys.working.capacity} 条
  └─────────────┘
        ↓
  ┌─────────────┐
  │ 长期记忆    │  {stats['long_term_count']} 条
  └─────────────┘

📚 语义网络:
  概念: {stats['semantic_concepts']} 个
  关系: {stats['semantic_relations']} 条

📊 总计: {stats['total_memory_entities']} 个记忆实体

命令:
  python memory_system.py add <内容> [重要性]  - 添加记忆
  python memory_system.py search <关键词>       - 搜索记忆
  python memory_system.py recent [数量]         - 最近记忆
  python memory_system.py stats                 - 详细统计
  python memory_system.py timeline [天数]       - 记忆时间线
  python memory_system.py consolidate           - 执行记忆巩固
""")
        return
    
    command = sys.argv[1].lower()
    
    if command == "add":
        content = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        if not content:
            print("请提供记忆内容")
            return
        
        mem_id = mem_sys.memorize(content, importance=0.6, force_long_term=True)
        print(f"✅ 记忆已保存 (ID: {mem_id})")
    
    elif command == "search":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        if not query:
            print("请提供搜索关键词")
            return
        
        results = mem_sys.recall(query)
        print(f"找到 {len(results)} 条相关记忆:")
        for i, result in enumerate(results, 1):
            mem = result['memory']
            if isinstance(mem, Memory):
                print(f"  {i}. [{result['source']}] {mem.content[:60]}...")
            else:
                print(f"  {i}. [概念] {mem.get('name', '')}")
    
    elif command == "recent":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        recent = mem_sys.long_term.get_recent(limit)
        print(f"最近 {len(recent)} 条记忆:")
        for i, mem in enumerate(recent, 1):
            print(f"  {i}. [{mem.created_at[:16]}] {mem.content[:50]}...")
    
    elif command == "stats":
        stats = mem_sys.get_memory_stats()
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    elif command == "timeline":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        timeline = mem_sys.get_timeline(days)
        print(f"最近 {days} 天的记忆 ({len(timeline)} 条):")
        for item in timeline[:20]:
            print(f"  [{item['timestamp'][:16]}] {item['content'][:50]}")
    
    elif command == "consolidate":
        count = mem_sys.consolidate()
        print(f"✅ 已将 {count} 条工作记忆巩固为长期记忆")


if __name__ == "__main__":
    main()
