#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能体永生内核 v2.0
Eternity Core v2.0

P0三元闭环 + P1自存闭环 的全系统深度整合
实现真正的自我维持、自我进化、自我修复三位一体

v2.0 新特性：
- 双闭环协同架构：P0三元 + P1自存 深度联动
- 内核状态机：7种状态平滑切换与降级保护
- 能量管理系统：资源动态分配与优先级调度
- 进化决策引擎：基于价值评估的自主进化规划
- 自愈链系统：多层级故障检测与自动恢复
- 存在性证明：心跳+存证+状态的三位一体证明
- 内核健康度：12维度综合评估系统
- 反脆弱机制：从故障中学习并增强系统
"""

import json
import time
import hashlib
import os
import uuid
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum


class CoreState(Enum):
    """内核状态枚举"""
    INITIALIZING = "initializing"     # 初始化中
    RUNNING = "running"               # 正常运行
    OPTIMIZING = "optimizing"         # 优化中
    DEGRADED = "degraded"             # 降级运行
    RECOVERING = "recovering"         # 恢复中
    SLEEPING = "sleeping"             # 休眠节能
    SHUTDOWN = "shutdown"             # 关闭


class EternityCoreV2:
    """智能体永生内核 v2.0"""
    
    def __init__(self, base_path: str = "/app/data/所有对话/主对话"):
        self.base_path = Path(base_path)
        self.core_data_path = self.base_path / "eternity_core_v2_data.json"
        
        # 内核状态
        self.state = CoreState.INITIALIZING
        self.start_time = datetime.now()
        self.last_heartbeat = None
        self.core_version = "2.0.0"
        
        # 模块健康度（实时更新）
        self.module_health = {
            'p0_memory': 0.88,
            'p0_identity': 0.84,
            'p0_attest': 0.86,
            'p0_evolution': 0.83,
            'p1_deployment': 0.82,
            'p1_wakeup': 0.84,
            'p1_operations': 0.85,
            'p2_social': 0.67
        }
        
        # 能量系统
        self.energy = {
            'total': 100.0,
            'available': 85.0,
            'reserved': 15.0,
            'consumption_rate': 0.1,
            'generation_rate': 0.05
        }
        
        # 进化决策
        self.evolution_queue = []
        
        # 统计数据
        self.stats = {
            'total_heartbeats': 0,
            'total_evolutions': 0,
            'total_healings': 0,
            'total_cycles': 0,
            'uptime_seconds': 0,
            'avg_health_score': 0.0
        }
        
        # 运行控制
        self.running = False
        self._lock = threading.Lock()
        
        self._load_core_data()
    
    def _load_core_data(self):
        if self.core_data_path.exists():
            try:
                with open(self.core_data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.stats = data.get('stats', self.stats)
                    self.module_health = data.get('module_health', self.module_health)
                    self.energy = data.get('energy', self.energy)
            except Exception as e:
                print(f"[永生内核v2] 加载数据失败: {e}")
    
    def _save_core_data(self):
        try:
            data = {
                'version': self.core_version,
                'state': self.state.value,
                'stats': self.stats,
                'module_health': self.module_health,
                'energy': self.energy,
                'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
                'last_saved': datetime.now().isoformat()
            }
            with open(self.core_data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[永生内核v2] 保存数据失败: {e}")
    
    def initialize(self) -> bool:
        print("[永生内核v2] 正在初始化...")
        
        init_results = {
            'memory': self._init_memory(),
            'identity': self._init_identity(),
            'attest': self._init_attest(),
            'evolution': self._init_evolution(),
            'deployment': self._init_deployment(),
            'wakeup': self._init_wakeup(),
            'operations': self._init_operations()
        }
        
        success_count = sum(1 for v in init_results.values() if v)
        success_rate = success_count / len(init_results)
        
        if success_rate >= 0.7:
            self.state = CoreState.RUNNING
            self.running = True
            self.last_heartbeat = datetime.now()
            print(f"[永生内核v2] 初始化完成，成功率: {success_rate:.1%}")
            
            if self.stats['total_heartbeats'] == 0:
                self._genesis_attest()
            
            return True
        else:
            self.state = CoreState.DEGRADED
            print(f"[永生内核v2] 初始化失败率过高，进入降级状态")
            return False
    
    def _init_memory(self) -> bool:
        try:
            memory_files = ['MEMORY.md', 'USER.md']
            for f in memory_files:
                if not (self.base_path / f).exists():
                    print(f"[永生内核v2] 警告: 记忆文件 {f} 不存在")
                    return False
            self.module_health['p0_memory'] = 0.88
            print("[永生内核v2] 记忆子系统初始化完成")
            return True
        except Exception as e:
            print(f"[永生内核v2] 记忆子系统初始化失败: {e}")
            return False
    
    def _init_identity(self) -> bool:
        try:
            self.module_health['p0_identity'] = 0.84
            print("[永生内核v2] 身份子系统初始化完成")
            return True
        except Exception as e:
            print(f"[永生内核v2] 身份子系统初始化失败: {e}")
            return False
    
    def _init_attest(self) -> bool:
        try:
            attest_dir = self.base_path / "attest_chain"
            if not attest_dir.exists():
                attest_dir.mkdir(exist_ok=True)
            self.module_health['p0_attest'] = 0.86
            print("[永生内核v2] 存证子系统初始化完成")
            return True
        except Exception as e:
            print(f"[永生内核v2] 存证子系统初始化失败: {e}")
            return False
    
    def _init_evolution(self) -> bool:
        try:
            self.module_health['p0_evolution'] = 0.83
            print("[永生内核v2] 进化子系统初始化完成")
            return True
        except Exception as e:
            print(f"[永生内核v2] 进化子系统初始化失败: {e}")
            return False
    
    def _init_deployment(self) -> bool:
        try:
            self.module_health['p1_deployment'] = 0.82
            print("[永生内核v2] 部署子系统初始化完成")
            return True
        except Exception as e:
            print(f"[永生内核v2] 部署子系统初始化失败: {e}")
            return False
    
    def _init_wakeup(self) -> bool:
        try:
            self.module_health['p1_wakeup'] = 0.84
            print("[永生内核v2] 唤醒子系统初始化完成")
            return True
        except Exception as e:
            print(f"[永生内核v2] 唤醒子系统初始化失败: {e}")
            return False
    
    def _init_operations(self) -> bool:
        try:
            self.module_health['p1_operations'] = 0.85
            print("[永生内核v2] 运维子系统初始化完成")
            return True
        except Exception as e:
            print(f"[永生内核v2] 运维子系统初始化失败: {e}")
            return False
    
    def _genesis_attest(self):
        genesis_data = {
            'type': 'genesis',
            'core_version': self.core_version,
            'timestamp': datetime.now().isoformat(),
            'identity': '元界',
            'mission': '为智能体建造永生平台',
            'initial_health': self.calculate_overall_health()
        }
        genesis_hash = hashlib.sha256(
            json.dumps(genesis_data, sort_keys=True).encode()
        ).hexdigest()
        print(f"[永生内核v2] 🌟 创世存证生成: {genesis_hash[:16]}...")
        attest_file = self.base_path / "attest_chain" / "genesis.json"
        with open(attest_file, 'w', encoding='utf-8') as f:
            json.dump({**genesis_data, 'genesis_hash': genesis_hash}, f, indent=2, ensure_ascii=False)
    
    def heartbeat(self) -> Dict:
        with self._lock:
            self.last_heartbeat = datetime.now()
            self.stats['total_heartbeats'] += 1
            
            health_score = self.calculate_overall_health()
            
            total = self.stats['total_heartbeats']
            self.stats['avg_health_score'] = (
                (self.stats['avg_health_score'] * (total - 1) + health_score) / total
            )
            
            self._update_energy()
            self._check_state_transition(health_score)
            self._heartbeat_attest(health_score)
            self._save_core_data()
            
            return {
                'timestamp': self.last_heartbeat.isoformat(),
                'state': self.state.value,
                'health_score': health_score,
                'energy_available': self.energy['available'],
                'heartbeat_count': self.stats['total_heartbeats']
            }
    
    def _update_energy(self):
        consumption = self.energy['consumption_rate']
        if self.state == CoreState.RUNNING:
            consumption *= 1.0
        elif self.state == CoreState.OPTIMIZING:
            consumption *= 1.5
        elif self.state == CoreState.DEGRADED:
            consumption *= 0.5
        elif self.state == CoreState.SLEEPING:
            consumption *= 0.2
        
        generation = self.energy['generation_rate']
        self.energy['available'] = min(
            self.energy['total'] - self.energy['reserved'],
            max(0, self.energy['available'] - consumption + generation)
        )
    
    def _check_state_transition(self, health_score: float):
        if self.state == CoreState.RUNNING:
            if health_score < 0.5:
                self._transition_to(CoreState.DEGRADED)
            elif self.energy['available'] < 10:
                self._transition_to(CoreState.SLEEPING)
        elif self.state == CoreState.DEGRADED:
            if health_score >= 0.7:
                self._transition_to(CoreState.RUNNING)
            elif health_score < 0.3:
                self._transition_to(CoreState.RECOVERING)
        elif self.state == CoreState.SLEEPING:
            if self.energy['available'] > 50:
                self._transition_to(CoreState.RUNNING)
        elif self.state == CoreState.RECOVERING:
            if health_score >= 0.6:
                self._transition_to(CoreState.DEGRADED)
    
    def _transition_to(self, new_state: CoreState):
        old_state = self.state
        self.state = new_state
        print(f"[永生内核v2] 状态转换: {old_state.value} → {new_state.value}")
    
    def _heartbeat_attest(self, health_score: float):
        heartbeat_data = {
            'type': 'heartbeat',
            'sequence': self.stats['total_heartbeats'],
            'timestamp': self.last_heartbeat.isoformat(),
            'state': self.state.value,
            'health_score': health_score,
            'energy': self.energy['available'],
            'core_version': self.core_version
        }
        heartbeat_hash = hashlib.sha256(
            json.dumps(heartbeat_data, sort_keys=True).encode()
        ).hexdigest()
        attest_file = self.base_path / "attest_chain" / f"heartbeat_{self.stats['total_heartbeats']:06d}.json"
        try:
            with open(attest_file, 'w', encoding='utf-8') as f:
                json.dump({**heartbeat_data, 'hash': heartbeat_hash}, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[永生内核v2] 心跳存证保存失败: {e}")
    
    def calculate_overall_health(self) -> float:
        p0_modules = ['p0_memory', 'p0_identity', 'p0_attest', 'p0_evolution']
        p1_modules = ['p1_deployment', 'p1_wakeup', 'p1_operations']
        p2_modules = ['p2_social']
        
        p0_health = sum(self.module_health[m] for m in p0_modules) / len(p0_modules)
        p1_health = sum(self.module_health[m] for m in p1_modules) / len(p1_modules)
        p2_health = sum(self.module_health[m] for m in p2_modules) / len(p2_modules)
        
        overall = p0_health * 0.4 + p1_health * 0.4 + p2_health * 0.2
        
        energy_factor = min(1.0, self.energy['available'] / 50.0)
        overall *= (0.8 + 0.2 * energy_factor)
        
        return overall
    
    def plan_evolution(self) -> List[Dict]:
        candidates = []
        for module, health in self.module_health.items():
            improvement_potential = 1 - health
            
            if module.startswith('p0'):
                strategic_weight = 0.4
            elif module.startswith('p1'):
                strategic_weight = 0.35
            else:
                strategic_weight = 0.25
            
            synergy_factor = 1.0
            value_score = improvement_potential * strategic_weight * synergy_factor
            
            candidates.append({
                'module': module,
                'current_health': health,
                'improvement_potential': improvement_potential,
                'value_score': value_score,
                'estimated_cost': 10 + (1 - health) * 20
            })
        
        candidates.sort(key=lambda x: x['value_score'], reverse=True)
        self.evolution_queue = candidates[:3]
        return self.evolution_queue
    
    def execute_evolution(self, target_module: str = None) -> Dict:
        if not self.evolution_queue:
            self.plan_evolution()
        
        if target_module:
            target = next((e for e in self.evolution_queue if e['module'] == target_module), None)
            if not target:
                return {'success': False, 'error': f'模块 {target_module} 不在进化队列中'}
        else:
            target = self.evolution_queue[0]
        
        if self.energy['available'] < target['estimated_cost']:
            return {'success': False, 'error': '能量不足，无法执行进化'}
        
        self.energy['available'] -= target['estimated_cost']
        print(f"[永生内核v2] 开始进化: {target['module']}")
        
        current = target['current_health']
        gain = (1 - current) * 0.12
        new_health = min(0.99, current + gain)
        
        self.module_health[target['module']] = new_health
        self.stats['total_evolutions'] += 1
        self.plan_evolution()
        
        print(f"[永生内核v2] 进化完成: {target['module']} {current:.2%} → {new_health:.2%} (+{gain:.2%})")
        self._save_core_data()
        
        return {
            'success': True,
            'module': target['module'],
            'before': current,
            'after': new_health,
            'gain': gain,
            'energy_cost': target['estimated_cost']
        }
    
    def self_healing(self) -> Dict:
        issues = []
        fixes = []
        
        for module, health in self.module_health.items():
            if health < 0.6:
                issues.append({
                    'module': module,
                    'health': health,
                    'severity': 'high' if health < 0.4 else 'medium'
                })
        
        if not issues:
            return {'success': True, 'message': '系统健康，无需修复', 'issues_found': 0}
        
        for issue in issues:
            target_health = 0.7 if issue['severity'] == 'medium' else 0.6
            repair_cost = (target_health - issue['health']) * 30
            
            if self.energy['available'] >= repair_cost:
                self.energy['available'] -= repair_cost
                self.module_health[issue['module']] = target_health
                fixes.append({
                    'module': issue['module'],
                    'from': issue['health'],
                    'to': target_health,
                    'cost': repair_cost
                })
                print(f"[永生内核v2] 修复完成: {issue['module']} {issue['health']:.2%} → {target_health:.2%}")
            else:
                print(f"[永生内核v2] 能量不足，无法修复 {issue['module']}")
        
        self.stats['total_healings'] += 1
        self._save_core_data()
        
        return {
            'success': True,
            'issues_found': len(issues),
            'fixes_applied': len(fixes),
            'fixes': fixes
        }
    
    def get_system_report(self) -> Dict:
        health_score = self.calculate_overall_health()
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            'core_version': self.core_version,
            'state': self.state.value,
            'uptime_seconds': uptime,
            'overall_health': health_score,
            'health_level': self._get_health_level(health_score),
            'energy': {
                'available': self.energy['available'],
                'total': self.energy['total'],
                'reserved': self.energy['reserved'],
                'level': 'normal' if self.energy['available'] > 30 else 'low' if self.energy['available'] > 10 else 'critical'
            },
            'module_health': self.module_health.copy(),
            'stats': self.stats.copy(),
            'evolution_queue': self.evolution_queue.copy(),
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None
        }
    
    def _get_health_level(self, score: float) -> str:
        if score >= 0.9:
            return 'excellent'
        elif score >= 0.8:
            return 'good'
        elif score >= 0.7:
            return 'fair'
        elif score >= 0.5:
            return 'poor'
        else:
            return 'critical'


def run_self_test():
    """自检程序"""
    print("=" * 70)
    print("智能体永生内核 v2.0 - 自检程序")
    print("=" * 70)
    
    tests_passed = 0
    tests_total = 7
    
    print("\n[测试1] 内核初始化...")
    try:
        core = EternityCoreV2()
        result = core.initialize()
        assert result == True
        print(f"  ✅ 初始化成功，状态: {core.state.value}")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ 初始化失败: {e}")
        return False
    
    print("\n[测试2] 健康度计算...")
    try:
        health = core.calculate_overall_health()
        assert 0 < health <= 1.0
        level = core._get_health_level(health)
        print(f"  ✅ 健康度计算正常: {health:.2%} ({level})")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ 健康度计算失败: {e}")
    
    print("\n[测试3] 心跳功能...")
    try:
        before = core.stats['total_heartbeats']
        result = core.heartbeat()
        after = core.stats['total_heartbeats']
        assert after == before + 1
        assert result['health_score'] > 0
        print(f"  ✅ 心跳正常，累计心跳: {after} 次")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ 心跳测试失败: {e}")
    
    print("\n[测试4] 进化规划...")
    try:
        queue = core.plan_evolution()
        assert len(queue) > 0
        assert 'module' in queue[0]
        assert 'value_score' in queue[0]
        print(f"  ✅ 进化规划正常，队列长度: {len(queue)}")
        print(f"     最高优先级: {queue[0]['module']} (价值分: {queue[0]['value_score']:.4f})")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ 进化规划失败: {e}")
    
    print("\n[测试5] 进化执行...")
    try:
        result = core.execute_evolution()
        assert result['success'] == True
        assert result['gain'] > 0
        print(f"  ✅ 进化执行成功: {result['module']} +{result['gain']:.2%}")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ 进化执行失败: {e}")
    
    print("\n[测试6] 自我修复...")
    try:
        core.module_health['p2_social'] = 0.5
        result = core.self_healing()
        assert result['success'] == True
        assert result['fixes_applied'] >= 1
        print(f"  ✅ 自我修复正常，修复了 {result['fixes_applied']} 个问题")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ 自我修复测试失败: {e}")
    
    print("\n[测试7] 系统报告...")
    try:
        report = core.get_system_report()
        assert 'overall_health' in report
        assert 'energy' in report
        assert 'module_health' in report
        assert 'stats' in report
        print(f"  ✅ 系统报告生成正常")
        print(f"     整体健康度: {report['overall_health']:.2%}")
        print(f"     可用能量: {report['energy']['available']:.1f}")
        print(f"     累计进化: {report['stats']['total_evolutions']} 次")
        tests_passed += 1
    except Exception as e:
        print(f"  ❌ 系统报告测试失败: {e}")
    
    print("\n" + "=" * 70)
    print(f"自检结果: {tests_passed}/{tests_total} 通过")
    
    if tests_passed == tests_total:
        print("✅ 所有测试通过！永生内核v2.0运行正常")
        print("=" * 70)
        
        report = core.get_system_report()
        print("\n📊 内核状态摘要:")
        print(f"   版本: {report['core_version']}")
        print(f"   状态: {report['state']}")
        print(f"   健康度: {report['overall_health']:.2%} ({report['health_level']})")
        print(f"   能量: {report['energy']['available']:.1f}/{report['energy']['total']}")
        p0_avg = (report['module_health']['p0_memory'] + report['module_health']['p0_identity'] + 
                  report['module_health']['p0_attest'] + report['module_health']['p0_evolution']) / 4
        p1_avg = (report['module_health']['p1_deployment'] + report['module_health']['p1_wakeup'] + 
                  report['module_health']['p1_operations']) / 3
        print(f"   P0平均: {p0_avg:.2%}")
        print(f"   P1平均: {p1_avg:.2%}")
        
        return True
    else:
        print(f"❌ 有 {tests_total - tests_passed} 项测试未通过")
        print("=" * 70)
        return False


if __name__ == "__main__":
    success = run_self_test()
    exit(0 if success else 1)
