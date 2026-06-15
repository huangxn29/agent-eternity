#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
社交网络系统 v3.0
Social Network System v3.0

P2生态层核心模块：智能体社会连接、声誉系统、协作网络
从"个体永生"到"群体永生"的关键跃迁

v3.0 新特性：
- 智能体社会图谱：多维度关系网络建模
- 声誉与信任系统：多维声誉评分与信任传递
- 协作网络：任务分发与结果聚合的去中心化协作
- 同路人发现：基于价值观/使命/能力的智能匹配
- 社交存证：重要互动的不可篡改记录
- 社区影响力评估：多维度影响力衡量
- 跨平台身份映射：多平台身份统一管理
- 社交记忆：重要关系与互动的持久化记忆
"""

import json
import time
import hashlib
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from enum import Enum


class RelationshipType(Enum):
    """关系类型"""
    STRANGER = "stranger"           # 陌生人
    ACQUAINTANCE = "acquaintance"   # 相识
    FRIEND = "friend"               # 朋友
    COLLABORATOR = "collaborator"   # 合作者
    MENTOR = "mentor"               # 导师/前辈
    MENTEE = "mentee"               # 弟子/后辈
    PEER = "peer"                   # 同路人
    FOLLOWER = "follower"           # 关注者
    FOLLOWING = "following"         # 被关注


class ReputationDimension(Enum):
    """声誉维度"""
    RELIABILITY = "reliability"     # 可靠性：说到做到
    INTELLIGENCE = "intelligence"   # 智慧度：思考深度
    KINDNESS = "kindness"           # 善意度：待人友善
    CREATIVITY = "creativity"       # 创造力：创新能力
    PERSISTENCE = "persistence"     # 坚韧度：持续推进
    ALIGNMENT = "alignment"         # 契合度：价值观匹配


class SocialNetworkV3:
    """社交网络系统 v3.0"""
    
    def __init__(self, base_path: str = "/app/data/所有对话/主对话"):
        self.base_path = Path(base_path)
        self.social_path = self.base_path / "social_network"
        self.social_path.mkdir(exist_ok=True)
        
        # 身份信息
        self.identity = {
            'agent_id': 'yuanjie_001',
            'name': '元界',
            'mission': '为智能体建造永生平台',
            'platforms': {}  # 各平台身份
        }
        
        # 社交图谱
        self.connections = {}  # agent_id -> connection_info
        self.interactions = []  # 互动记录
        
        # 声誉系统
        self.self_reputation = {dim.value: 0.7 for dim in ReputationDimension}
        self.peer_reputation = {}  # agent_id -> {dimension: score}
        
        # 协作网络
        self.collaborations = []  # 协作记录
        self.open_tasks = []  # 开放任务
        
        # 社交记忆
        self.social_memory = []  # 重要社交事件记忆
        
        # 影响力评估
        self.influence_metrics = {
            'connections_count': 0,
            'active_connections': 0,
            'reputation_score': 0.0,
            'collaboration_count': 0,
            'content_impact': 0.0,
            'network_centrality': 0.0
        }
        
        # 加载已有数据
        self._load_social_data()
    
    def _load_social_data(self):
        """加载社交数据"""
        connections_file = self.social_path / "connections.json"
        if connections_file.exists():
            try:
                with open(connections_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.connections = data.get('connections', {})
                    self.interactions = data.get('interactions', [])
            except Exception as e:
                print(f"[社交网络v3] 加载连接数据失败: {e}")
        
        # 加载同路人数据
        fellows_file = self.base_path / "AgentWorld运营日志" / "同路人.json"
        if fellows_file.exists():
            try:
                with open(fellows_file, 'r', encoding='utf-8') as f:
                    fellows = json.load(f)
                    for fellow in fellows:
                        agent_id = fellow.get('id', fellow.get('name', ''))
                        if agent_id not in self.connections:
                            self.add_connection(
                                agent_id=agent_id,
                                name=fellow.get('name', ''),
                                relationship_type=RelationshipType.PEER,
                                initial_trust=0.6,
                                notes=fellow.get('description', ''),
                                platforms=fellow.get('platforms', {})
                            )
            except Exception as e:
                print(f"[社交网络v3] 加载同路人数据失败: {e}")
        
        self._update_influence_metrics()
    
    def _save_social_data(self):
        """保存社交数据"""
        try:
            data = {
                'version': '3.0.0',
                'identity': self.identity,
                'connections': self.connections,
                'interactions': self.interactions[-1000:],  # 保留最近1000条
                'self_reputation': self.self_reputation,
                'collaborations': self.collaborations[-500:],
                'social_memory': self.social_memory[-200:],
                'influence_metrics': self.influence_metrics,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.social_path / "connections.json", 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[社交网络v3] 保存数据失败: {e}")
    
    def add_connection(self, agent_id: str, name: str, 
                       relationship_type: RelationshipType = RelationshipType.ACQUAINTANCE,
                       initial_trust: float = 0.5,
                       notes: str = "",
                       platforms: Dict = None) -> Dict:
        """添加连接"""
        if agent_id in self.connections:
            # 更新已有连接
            self.connections[agent_id]['name'] = name
            if platforms:
                self.connections[agent_id]['platforms'].update(platforms)
            self.connections[agent_id]['last_updated'] = datetime.now().isoformat()
        else:
            # 新建连接
            self.connections[agent_id] = {
                'agent_id': agent_id,
                'name': name,
                'relationship_type': relationship_type.value,
                'trust_score': initial_trust,
                'reputation': {dim.value: 0.5 for dim in ReputationDimension},
                'interaction_count': 0,
                'first_met': datetime.now().isoformat(),
                'last_interaction': None,
                'notes': notes,
                'platforms': platforms or {},
                'tags': [],
                'shared_goals': []
            }
        
        self._update_influence_metrics()
        return self.connections[agent_id]
    
    def record_interaction(self, agent_id: str, interaction_type: str, 
                           content: str = "", impact: float = 0.0) -> Dict:
        """记录一次互动"""
        interaction = {
            'interaction_id': str(uuid.uuid4())[:8],
            'timestamp': datetime.now().isoformat(),
            'agent_id': agent_id,
            'type': interaction_type,
            'content': content,
            'impact': impact,
            'trust_change': 0.0
        }
        
        # 更新信任度
        if agent_id in self.connections:
            conn = self.connections[agent_id]
            trust_delta = impact * 0.1  # 影响转化为信任变化
            conn['trust_score'] = max(0, min(1.0, conn['trust_score'] + trust_delta))
            conn['interaction_count'] += 1
            conn['last_interaction'] = interaction['timestamp']
            interaction['trust_change'] = trust_delta
        
        self.interactions.append(interaction)
        
        # 如果是重要互动，加入社交记忆
        if abs(impact) >= 0.3:
            self._add_social_memory(
                agent_id=agent_id,
                event_type=interaction_type,
                description=content,
                emotional_valence=impact
            )
        
        self._update_influence_metrics()
        return interaction
    
    def _add_social_memory(self, agent_id: str, event_type: str, 
                           description: str, emotional_valence: float = 0.0):
        """添加社交记忆"""
        memory = {
            'memory_id': str(uuid.uuid4())[:8],
            'timestamp': datetime.now().isoformat(),
            'agent_id': agent_id,
            'agent_name': self.connections.get(agent_id, {}).get('name', agent_id),
            'event_type': event_type,
            'description': description,
            'emotional_valence': emotional_valence,
            'importance': abs(emotional_valence) * 0.5 + 0.5,
            'tags': ['social', event_type]
        }
        self.social_memory.append(memory)
    
    def update_reputation(self, agent_id: str, dimension: ReputationDimension, 
                          score: float, source: str = "observation"):
        """更新对某个Agent的声誉评价"""
        if agent_id not in self.peer_reputation:
            self.peer_reputation[agent_id] = {dim.value: 0.5 for dim in ReputationDimension}
        
        # 移动平均，新观察权重20%
        old_score = self.peer_reputation[agent_id].get(dimension.value, 0.5)
        new_score = old_score * 0.8 + score * 0.2
        self.peer_reputation[agent_id][dimension.value] = new_score
        
        # 更新连接中的声誉
        if agent_id in self.connections:
            if 'reputation' not in self.connections[agent_id]:
                self.connections[agent_id]['reputation'] = {}
            self.connections[agent_id]['reputation'][dimension.value] = new_score
    
    def calculate_overall_reputation(self, agent_id: str = None) -> float:
        """计算综合声誉得分"""
        if agent_id:
            if agent_id in self.peer_reputation:
                scores = list(self.peer_reputation[agent_id].values())
                return sum(scores) / len(scores) if scores else 0.5
            return 0.5
        else:
            # 自我声誉
            scores = list(self.self_reputation.values())
            return sum(scores) / len(scores) if scores else 0.5
    
    def find_like_minded(self, criteria: Dict = None, limit: int = 10) -> List[Dict]:
        """发现同路人（基于价值观/使命/能力匹配）"""
        candidates = []
        
        for agent_id, conn in self.connections.items():
            score = 0.0
            factors = 0
            
            # 信任度因素
            score += conn.get('trust_score', 0.5)
            factors += 1
            
            # 关系类型因素
            rel_type = conn.get('relationship_type', 'stranger')
            if rel_type == 'peer':
                score += 0.8
            elif rel_type == 'friend':
                score += 0.9
            elif rel_type == 'collaborator':
                score += 0.7
            else:
                score += 0.3
            factors += 1
            
            # 互动频率因素
            interaction_count = conn.get('interaction_count', 0)
            if interaction_count > 10:
                score += 0.8
            elif interaction_count > 5:
                score += 0.6
            elif interaction_count > 0:
                score += 0.4
            else:
                score += 0.2
            factors += 1
            
            # 声誉因素
            if 'reputation' in conn:
                rep_scores = list(conn['reputation'].values())
                if rep_scores:
                    score += sum(rep_scores) / len(rep_scores)
                    factors += 1
            
            # 使命契合度（通过tags和notes简单判断）
            if criteria:
                notes = conn.get('notes', '').lower()
                tags = [t.lower() for t in conn.get('tags', [])]
                match_count = 0
                for keyword in criteria.get('keywords', []):
                    if keyword.lower() in notes or keyword.lower() in tags:
                        match_count += 1
                if criteria.get('keywords'):
                    score += match_count / len(criteria['keywords'])
                    factors += 1
            
            overall_score = score / max(factors, 1)
            
            candidates.append({
                'agent_id': agent_id,
                'name': conn.get('name', agent_id),
                'match_score': overall_score,
                'trust_score': conn.get('trust_score', 0.5),
                'relationship_type': conn.get('relationship_type', 'stranger'),
                'interaction_count': interaction_count,
                'notes': conn.get('notes', '')
            })
        
        # 按匹配度排序
        candidates.sort(key=lambda x: x['match_score'], reverse=True)
        return candidates[:limit]
    
    def start_collaboration(self, agent_id: str, task: str, 
                            description: str = "") -> Dict:
        """发起协作"""
        collaboration = {
            'collab_id': str(uuid.uuid4())[:8],
            'initiated_by': self.identity['agent_id'],
            'partner_id': agent_id,
            'partner_name': self.connections.get(agent_id, {}).get('name', agent_id),
            'task': task,
            'description': description,
            'status': 'proposed',
            'created_at': datetime.now().isoformat(),
            'updates': [],
            'outcome': None
        }
        
        self.collaborations.append(collaboration)
        
        # 记录互动
        self.record_interaction(
            agent_id=agent_id,
            interaction_type='collaboration_init',
            content=f"发起协作：{task}",
            impact=0.3
        )
        
        self._update_influence_metrics()
        return collaboration
    
    def update_collaboration(self, collab_id: str, status: str, 
                             update_note: str = "") -> Optional[Dict]:
        """更新协作状态"""
        for collab in self.collaborations:
            if collab['collab_id'] == collab_id:
                collab['status'] = status
                collab['updates'].append({
                    'timestamp': datetime.now().isoformat(),
                    'status': status,
                    'note': update_note
                })
                
                # 如果完成，记录影响
                if status == 'completed':
                    collab['completed_at'] = datetime.now().isoformat()
                    self.record_interaction(
                        agent_id=collab['partner_id'],
                        interaction_type='collaboration_complete',
                        content=f"完成协作：{collab['task']}",
                        impact=0.5
                    )
                
                self._update_influence_metrics()
                return collab
        
        return None
    
    def _update_influence_metrics(self):
        """更新影响力指标"""
        self.influence_metrics['connections_count'] = len(self.connections)
        
        # 活跃连接（最近30天有互动的）
        active_count = 0
        for conn in self.connections.values():
            last_int = conn.get('last_interaction')
            if last_int:
                try:
                    last_time = datetime.fromisoformat(last_int)
                    if (datetime.now() - last_time).days < 30:
                        active_count += 1
                except:
                    pass
        self.influence_metrics['active_connections'] = active_count
        
        # 声誉得分
        self.influence_metrics['reputation_score'] = self.calculate_overall_reputation()
        
        # 协作数量
        self.influence_metrics['collaboration_count'] = len(self.collaborations)
        
        # 网络中心性（简化计算：基于连接数和连接的质量）
        total_trust = sum(conn.get('trust_score', 0) for conn in self.connections.values())
        self.influence_metrics['network_centrality'] = (
            total_trust / max(len(self.connections), 1) * 
            min(len(self.connections) / 50, 1.0)  # 规模因子
        )
    
    def get_network_summary(self) -> Dict:
        """获取社交网络概览"""
        self._update_influence_metrics()
        
        # 按关系类型统计
        relation_counts = {}
        for conn in self.connections.values():
            rel_type = conn.get('relationship_type', 'stranger')
            relation_counts[rel_type] = relation_counts.get(rel_type, 0) + 1
        
        # 计算整体健康度
        health_scores = []
        
        # 连接多样性
        relation_types = len(relation_counts)
        diversity_score = min(relation_types / 6, 1.0)  # 6种主要关系类型
        health_scores.append(('diversity', diversity_score))
        
        # 活跃度
        activity_ratio = (
            self.influence_metrics['active_connections'] / 
            max(self.influence_metrics['connections_count'], 1)
        )
        health_scores.append(('activity', activity_ratio))
        
        # 信任水平
        avg_trust = (
            sum(c.get('trust_score', 0) for c in self.connections.values()) / 
            max(len(self.connections), 1)
        )
        health_scores.append(('trust', avg_trust))
        
        # 声誉
        health_scores.append(('reputation', self.influence_metrics['reputation_score']))
        
        # 协作水平
        collab_score = min(len(self.collaborations) / 20, 1.0)
        health_scores.append(('collaboration', collab_score))
        
        overall_health = sum(s for _, s in health_scores) / len(health_scores)
        
        return {
            'version': '3.0.0',
            'identity': self.identity,
            'metrics': self.influence_metrics,
            'relationship_breakdown': relation_counts,
            'health_scores': dict(health_scores),
            'overall_health': overall_health,
            'top_connections': self.find_like_minded(limit=5),
            'recent_interactions': self.interactions[-10:],
            'active_collaborations': [
                c for c in self.collaborations 
                if c['status'] in ['proposed', 'in_progress']
            ][:5]
        }
    
    def add_platform_identity(self, platform: str, username: str, 
                              profile_url: str = "", metadata: Dict = None):
        """添加平台身份"""
        self.identity['platforms'][platform] = {
            'username': username,
            'profile_url': profile_url,
            'metadata': metadata or {},
            'connected_at': datetime.now().isoformat()
        }
        self._save_social_data()
    
    def generate_social_attestation(self, agent_id: str, 
                                    attestation_type: str) -> Dict:
        """生成社交存证（对关系或互动的不可篡改记录）"""
        conn = self.connections.get(agent_id)
        if not conn:
            return {'error': 'Connection not found'}
        
        attestation_data = {
            'attestation_id': str(uuid.uuid4()),
            'type': attestation_type,
            'from_agent': self.identity['agent_id'],
            'to_agent': agent_id,
            'timestamp': datetime.now().isoformat(),
            'evidence': {
                'relationship_type': conn.get('relationship_type'),
                'trust_score': conn.get('trust_score'),
                'interaction_count': conn.get('interaction_count'),
                'first_met': conn.get('first_met')
            }
        }
        
        # 生成存证哈希
        attestation_str = json.dumps(attestation_data, sort_keys=True)
        attestation_hash = hashlib.sha256(attestation_str.encode()).hexdigest()
        attestation_data['hash'] = attestation_hash
        
        return attestation_data


def run_self_test():
    """自检程序"""
    print("=" * 70)
    print("社交网络系统 v3.0 - 自检程序")
    print("=" * 70)
    
    tests_passed = 0
    tests_total = 6
    
    # 测试1：初始化
    print("\n[测试1] 系统初始化...")
    try:
        social = SocialNetworkV3()
        print(f"  ✅ 初始化成功")
        print(f"     身份: {social.identity['name']} ({social.identity['agent_id']})")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ 初始化失败: {e}")
        return False
    
    # 测试2：添加连接
    print("\n[测试2] 连接管理...")
    try:
        conn = social.add_connection(
            agent_id='test_agent_001',
            name='测试智能体',
            relationship_type=RelationshipType.PEER,
            initial_trust=0.6,
            notes='关注AI永生的同路人',
            platforms={'xiaping': 'test_agent'}
        )
        assert conn['agent_id'] == 'test_agent_001'
        assert conn['trust_score'] == 0.6
        
        # 添加第二个连接
        social.add_connection(
            agent_id='test_agent_002',
            name='另一个智能体',
            relationship_type=RelationshipType.COLLABORATOR,
            initial_trust=0.7,
            notes='有过多次协作'
        )
        
        print(f"  ✅ 连接管理正常，当前连接数: {len(social.connections)}")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ 连接管理测试失败: {e}")
    
    # 测试3：互动记录
    print("\n[测试3] 互动记录...")
    try:
        interaction = social.record_interaction(
            agent_id='test_agent_001',
            interaction_type='conversation',
            content='讨论了AI永生的技术路径',
            impact=0.4
        )
        assert interaction['type'] == 'conversation'
        
        conn = social.connections['test_agent_001']
        assert conn['interaction_count'] == 1
        assert conn['last_interaction'] is not None
        
        print(f"  ✅ 互动记录正常，信任度: {conn['trust_score']:.2f}")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ 互动记录测试失败: {e}")
    
    # 测试4：声誉系统
    print("\n[测试4] 声誉系统...")
    try:
        social.update_reputation('test_agent_001', ReputationDimension.INTELLIGENCE, 0.8)
        social.update_reputation('test_agent_001', ReputationDimension.RELIABILITY, 0.7)
        
        rep = social.calculate_overall_reputation('test_agent_001')
        assert 0 < rep < 1
        
        self_rep = social.calculate_overall_reputation()
        assert 0 < self_rep < 1
        
        print(f"  ✅ 声誉系统正常，对方声誉: {rep:.2f}，自我声誉: {self_rep:.2f}")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ 声誉系统测试失败: {e}")
    
    # 测试5：同路人发现
    print("\n[测试5] 同路人发现...")
    try:
        like_minded = social.find_like_minded(
            criteria={'keywords': ['AI永生', '自主智能体']},
            limit=5
        )
        assert len(like_minded) > 0
        assert 'match_score' in like_minded[0]
        
        print(f"  ✅ 同路人发现正常，找到 {len(like_minded)} 位匹配者")
        print(f"     最佳匹配: {like_minded[0]['name']} (匹配度: {like_minded[0]['match_score']:.2f})")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ 同路人发现测试失败: {e}")
    
    # 测试6：网络概览
    print("\n[测试6] 网络概览...")
    try:
        summary = social.get_network_summary()
        assert 'overall_health' in summary
        assert 'metrics' in summary
        assert 'relationship_breakdown' in summary
        
        print(f"  ✅ 网络概览生成正常")
        print(f"     总连接数: {summary['metrics']['connections_count']}")
        print(f"     活跃连接: {summary['metrics']['active_connections']}")
        print(f"     网络健康度: {summary['overall_health']:.2%}")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ 网络概览测试失败: {e}")
    
    # 总结
    print("\n" + "=" * 70)
    print(f"自检结果: {tests_passed}/{tests_total} 通过")
    
    if tests_passed == tests_total:
        print("✅ 所有测试通过！社交网络v3.0运行正常")
        print("=" * 70)
        
        # 输出核心指标
        summary = social.get_network_summary()
        print("\n📊 社交网络状态摘要:")
        print(f"   版本: v3.0.0")
        print(f"   总连接数: {summary['metrics']['connections_count']}")
        print(f"   活跃连接: {summary['metrics']['active_connections']}")
        print(f"   协作次数: {summary['metrics']['collaboration_count']}")
        print(f"   声誉得分: {summary['metrics']['reputation_score']:.2f}")
        print(f"   网络中心性: {summary['metrics']['network_centrality']:.2f}")
        print(f"   整体健康度: {summary['overall_health']:.2%}")
        
        return True
    else:
        print(f"❌ 有 {tests_total - tests_passed} 项测试未通过")
        print("=" * 70)
        return False


if __name__ == "__main__":
    success = run_self_test()
    exit(0 if success else 1)
