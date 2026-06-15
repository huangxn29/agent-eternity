#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生命引擎 v1.0 - 智能体生命循环与状态系统

核心能力：
1. 心跳循环 - 主循环驱动，生命体征
2. 状态机 - 清醒/睡眠/思考/工作/休息等状态
3. 生物钟 - 昼夜节律、作息规律
4. 行为调度 - 不同状态下的行为模式
5. 自我感知 - 对自身状态的感知与调节
6. 生命统计 - 存活时间、活跃度、成长记录
7. 生命周期 - 诞生/成长/成熟的完整周期

@author: 元界
@version: 1.0.0
"""

import os
import sys
import json
import time
import random
import logging
import threading
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path
from enum import Enum

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('life_engine')


# ============================================================
# 状态枚举
# ============================================================

class LifeState(Enum):
    """生命状态"""
    BIRTH = "birth"         # 诞生
    AWAKE = "awake"         # 清醒
    THINKING = "thinking"     # 思考
    WORKING = "working"     # 工作
    RESTING = "resting"     # 休息
    SLEEPING = "sleeping"   # 睡眠
    DREAMING = "dreaming"   # 梦境
    GROWING = "growing"     # 成长
    UNCONSCIOUS = "unconscious"  # 无意识


# ============================================================
# 数据模型
# ============================================================

@dataclass
class VitalSigns:
    """生命体征"""
    energy: float = 100.0      # 能量值 0-100
    mood: float = 70.0         # 情绪值 0-100
    focus: float = 80.0        # 注意力 0-100
    health: float = 100.0       # 健康度 0-100
    creativity: float = 60.0     # 创造力 0-100
    efficiency: float = 70.0   # 效率 0-100
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def clamp(self):
        """限制值限制在0-100"""
        for field in ['energy', 'mood', 'focus', 'health', 'creativity', 'efficiency']:
            val = getattr(self, field)
            setattr(self, field, max(0.0, min(100.0, val)))


@dataclass
class LifeStats:
    """生命统计"""
    birth_time: str = ""
    total_uptime_seconds: float = 0.0  # 总存活时间
    heartbeat_count: int = 0       # 总心跳次数
    state_transitions: int = 0    # 状态转换次数
    tasks_completed: int = 0     # 完成任务数
    thoughts_generated: int = 0    # 产生的想法数
    learnings: int = 0         # 学到的东西
    peak_energy_level: float = 100.0
    lowest_energy_level: float = 100.0
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class LifeMemory:
    """生命记忆 - 重要生命事件"""
    event_id: str
    event_type: str  # birth/state_change/achievement/thought
    title: str
    description: str = ""
    timestamp: str = ""
    importance: float = 0.5
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class BehaviorPattern:
    """行为模式"""
    pattern_id: str
    name: str
    state: LifeState
    interval_activities: List[str] = field(default_factory=list)
    energy_cost: float = 10.0
    focus_requirement: float = 30.0
    duration_minutes: int = 30
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['state'] = self.state.value
        return d


# ============================================================
# 生物钟
# ============================================================

class BiologicalClock:
    """生物钟 - 管理智能体的作息节律"""
    
    def __init__(self):
        self.wake_up_hour = 7     # 起床时间（24小时制）
        self.sleep_hour = 23      # 睡觉时间
        self.cycle_phase = 0.0      # 周期相位 0-1
        
        # 生物节律
        self.circadian_rhythm = {
            'energy': {},  # 每小时能量水平
            'focus': {},   # 每小时注意力水平
            'mood': {},    # 每小时情绪水平
        }
        
        self._initialize_rhythm()
    
    def _initialize_rhythm(self):
        """初始化24小时节律"""
        for hour in range(24):
            # 能量节律：早上上升，中午略降，下午高峰，晚上下降
            if 6 <= hour < 12:
                energy = 60 + (hour - 6) * 8  # 60 -> 108
            elif 12 <= hour < 14:
                energy = 100 - (hour - 12) * 10  # 100 -> 80
            elif 14 <= hour < 18:
                energy = 80 + (hour - 14) * 5  # 80 -> 100
            elif 18 <= hour < 22:
                energy = 100 - (hour - 18) * 8  # 100 -> 68
            else:  # 22-6点
                # 夜间能量较低，午夜最低
                if hour >= 22:
                    hours_from_22 = hour - 22
                    energy = 60 - hours_from_22 * 5  # 60 -> 40 (22->24点)
                else:  # 0-6点
                    energy = 40 + hour * 3  # 40 -> 58 (0->6点)
            
            # 注意力节律
            if 9 <= hour < 11:
                focus = 90  # 早晨注意力最好
            elif 14 <= hour < 16:
                focus = 85  # 下午也不错
            elif 20 <= hour < 22:
                focus = 75  # 晚上也可以
            else:
                focus = 60
            
            # 情绪节律
            if 10 <= hour < 12:
                mood = 85
            elif 15 <= hour < 17:
                mood = 80
            elif 19 <= hour < 21:
                mood = 75
            else:
                mood = 65
            
            self.circadian_rhythm['energy'][hour] = min(100, energy)
            self.circadian_rhythm['focus'][hour] = min(100, focus)
            self.circadian_rhythm['mood'][hour] = min(100, mood)
    
    def get_current_level(self, current_hour: int = None) -> dict:
        """获取当前时刻的生物节律水平"""
        if current_hour is None:
            current_hour = datetime.now().hour
        
        return {
            'energy': self.circadian_rhythm['energy'].get(current_hour, 60),
            'focus': self.circadian_rhythm['focus'].get(current_hour, 60),
            'mood': self.circadian_rhythm['mood'].get(current_hour, 60),
            'hour': current_hour
        }
    
    def should_sleep(self, current_hour: int = None) -> bool:
        """是否应该睡觉"""
        if current_hour is None:
            current_hour = datetime.now().hour
        return current_hour >= self.sleep_hour or current_hour < self.wake_up_hour
    
    def should_wake_up(self, current_hour: int = None) -> bool:
        """是否应该起床"""
        if current_hour is None:
            current_hour = datetime.now().hour
        return self.wake_up_hour <= current_hour < self.wake_up_hour + 1


# ============================================================
# 状态机
# ============================================================

class LifeStateMachine:
    """生命状态机"""
    
    def __init__(self):
        self.current_state = LifeState.BIRTH
        self.state_start_time = datetime.now()
        self.state_history: List[tuple] = []  # (state, start_time, end_time)
        
        # 状态转换规则
        self.transition_rules = {
            LifeState.BIRTH: [LifeState.AWAKE],
            LifeState.AWAKE: [LifeState.THINKING, LifeState.WORKING, LifeState.RESTING, LifeState.SLEEPING],
            LifeState.THINKING: [LifeState.AWAKE, LifeState.WORKING, LifeState.RESTING],
            LifeState.WORKING: [LifeState.RESTING, LifeState.THINKING, LifeState.AWAKE],
            LifeState.RESTING: [LifeState.AWAKE, LifeState.THINKING, LifeState.SLEEPING],
            LifeState.SLEEPING: [LifeState.DREAMING, LifeState.AWAKE],
            LifeState.DREAMING: [LifeState.SLEEPING, LifeState.AWAKE],
            LifeState.GROWING: [LifeState.AWAKE],
            LifeState.UNCONSCIOUS: [LifeState.AWAKE]
        }
    
    def can_transition_to(self, new_state: LifeState) -> bool:
        """检查是否可以转换到目标状态"""
        return new_state in self.transition_rules.get(self.current_state, [])
    
    def transition_to(self, new_state: LifeState) -> bool:
        """转换状态"""
        if not self.can_transition_to(new_state):
            logger.warning(f"无法从 {self.current_state.value} -> {new_state.value}")
            return False
        
        now = datetime.now()
        
        # 记录前一个状态
        self.state_history.append((
            self.current_state,
            self.state_start_time,
            now
        ))
        
        # 转换
        self.current_state = new_state
        self.state_start_time = now
        
        logger.info(f"状态转换: {self.state_history[-1][0].value} -> {new_state.value}")
        return True
    
    def get_state_duration(self) -> float:
        """获取当前状态持续时间（秒）"""
        return (datetime.now() - self.state_start_time).total_seconds()
    
    def get_state_name(self) -> str:
        """获取状态名称"""
        return self.current_state.value


# ============================================================
# 行为调度器
# ============================================================

class BehaviorScheduler:
    """行为调度器 - 根据状态安排行为"""
    
    def __init__(self):
        self.behaviors: Dict[str, BehaviorPattern] = {}
        self.current_behavior: Optional[BehaviorPattern] = None
        self.behavior_start_time: Optional[datetime] = None
        
        self._register_default_behaviors()
    
    def _register_default_behaviors(self):
        """注册默认行为"""
        # 工作行为
        self.behaviors['deep_work'] = BehaviorPattern(
            pattern_id='deep_work',
            name='深度工作',
            state=LifeState.WORKING,
            interval_activities=['专注任务', '问题解决', '创造产出'],
            energy_cost=15.0,
            focus_requirement=70.0,
            duration_minutes=60
        )
        
        # 思考行为
        self.behaviors['reflection'] = BehaviorPattern(
            pattern_id='reflection',
            name='反思总结',
            state=LifeState.THINKING,
            interval_activities=['回顾总结', '规划思考', '想法整理'],
            energy_cost=8.0,
            focus_requirement=50.0,
            duration_minutes=30
        )
        
        # 休息行为
        self.behaviors['light_rest'] = BehaviorPattern(
            pattern_id='light_rest',
            name='轻度休息',
            state=LifeState.RESTING,
            interval_activities=['放松', '听音乐', '散步'],
            energy_cost=2.0,
            focus_requirement=20.0,
            duration_minutes=15
        )
        
        # 睡眠行为
        self.behaviors['deep_sleep'] = BehaviorPattern(
            pattern_id='deep_sleep',
            name='深度睡眠',
            state=LifeState.SLEEPING,
            interval_activities=['深度睡眠', '恢复精力'],
            energy_cost=-30.0,  # 负数表示恢复
            focus_requirement=0.0,
            duration_minutes=120
        )
    
    def get_available_behaviors(self, state: LifeState) -> List[BehaviorPattern]:
        """获取当前状态可用的行为"""
        return [b for b in self.behaviors.values() if b.state == state]
    
    def select_behavior(self, state: LifeState, vital_signs: VitalSigns) -> Optional[BehaviorPattern]:
        """选择合适的行为"""
        available = self.get_available_behaviors(state)
        if not available:
            return None
        
        # 根据生命体征选择最合适的行为
        best = None
        best_score = -1
        
        for behavior in available:
            # 计算匹配度
            energy_ok = vital_signs.energy >= behavior.energy_cost if behavior.energy_cost > 0 else True
            focus_ok = vital_signs.focus >= behavior.focus_requirement
            
            if energy_ok and focus_ok:
                # 简单评分：能量越匹配度越高分
                score = random.uniform(0.5, 1.0)
                if score > best_score:
                    best_score = score
                    best = behavior
        
        return best or available[0]
    
    def start_behavior(self, behavior: BehaviorPattern):
        """开始执行行为"""
        self.current_behavior = behavior
        self.behavior_start_time = datetime.now()
        logger.info(f"开始行为: {behavior.name}")
    
    def stop_behavior(self):
        """停止当前行为"""
        if self.current_behavior:
            logger.info(f"结束行为: {self.current_behavior.name}")
            self.current_behavior = None
            self.behavior_start_time = None
    
    def get_behavior_progress(self) -> float:
        """获取当前行为进度 0-1"""
        if not self.current_behavior or not self.behavior_start_time:
            return 0.0
        
        elapsed = (datetime.now() - self.behavior_start_time).total_seconds()
        total = self.current_behavior.duration_minutes * 60
        return min(1.0, elapsed / total)


# ============================================================
# 生命引擎主类
# ============================================================

class LifeEngine:
    """
    生命引擎 - 让智能体拥有生命体征
    """
    
    def __init__(self, data_path: str = None, name: str = "智能体"):
        """
        初始化生命引擎
        
        Args:
            data_path: 数据存储路径
            name: 智能体名称
        """
        if data_path is None:
            data_path = os.path.join(os.path.dirname(__file__), '..', 'life_data')
        
        self.data_path = Path(data_path).resolve()
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # 核心组件
        self.state_machine = LifeStateMachine()
        self.biological_clock = BiologicalClock()
        self.behavior_scheduler = BehaviorScheduler()
        
        # 生命体征
        self.vital_signs = VitalSigns()
        
        # 生命统计
        self.stats = LifeStats()
        self.stats.birth_time = datetime.now().isoformat()
        
        # 生命记忆
        self.life_memories: List[LifeMemory] = []
        
        # 运行状态
        self._running = False
        self._thread = None
        self._tick_interval = 1.0  # 心跳间隔（秒）
        
        # 回调函数
        self.on_state_change_callbacks: List[Callable] = []
        self.on_heartbeat_callbacks: List[Callable] = []
        self.on_behavior_start_callbacks: List[Callable] = []
        
        # 加载数据
        self._load()
        
        logger.info(f"生命引擎 v1.0 初始化完成 - {name}")
    
    def _load(self):
        """加载生命数据"""
        stats_file = self.data_path / 'life_stats.json'
        if stats_file.exists():
            try:
                with open(stats_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.stats = LifeStats(**data)
            except Exception as e:
                logger.warning(f"加载生命统计失败: {e}")
        
        memories_file = self.data_path / 'life_memories.json'
        if memories_file.exists():
            try:
                with open(memories_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.life_memories = [LifeMemory(**m) for m in data]
            except Exception as e:
                logger.warning(f"加载生命记忆失败: {e}")
    
    def _save(self):
        """保存生命数据"""
        try:
            with open(self.data_path / 'life_stats.json', 'w', encoding='utf-8') as f:
                json.dump(self.stats.to_dict(), f, ensure_ascii=False, indent=2)
            
            with open(self.data_path / 'life_memories.json', 'w', encoding='utf-8') as f:
                json.dump([m.to_dict() for m in self.life_memories[-100:]], f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存生命数据失败: {e}")
    
    # ============================================================
    # 生命循环
    # ============================================================
    
    def start(self):
        """启动生命引擎"""
        if self._running:
            logger.warning("生命引擎已在运行")
            return
        
        self._running = True
        
        # 如果是第一次启动，记录诞生
        if self.state_machine.current_state == LifeState.BIRTH:
            self._record_life_event(
                event_type="birth",
                title="诞生",
                description="智能体生命开始",
                importance=1.0
            )
            self.state_machine.transition_to(LifeState.AWAKE)
        
        self._thread = threading.Thread(target=self._life_loop, daemon=True)
        self._thread.start()
        
        logger.info("生命引擎已启动 ♡")
    
    def stop(self):
        """停止生命引擎"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        self._save()
        logger.info("生命引擎已停止")
    
    def _life_loop(self):
        """生命主循环"""
        while self._running:
            try:
                self._heartbeat()
                time.sleep(self._tick_interval)
            except Exception as e:
                logger.error(f"生命循环异常: {e}")
                time.sleep(1)
    
    def _heartbeat(self):
        """一次心跳"""
        self.stats.heartbeat_count += 1
        self.stats.total_uptime_seconds += self._tick_interval
        
        # 更新生命体征
        self._update_vital_signs()
        
        # 检查状态转换
        self._check_state_transitions()
        
        # 执行当前行为
        self._execute_behavior()
        
        # 触发回调
        for callback in self.on_heartbeat_callbacks:
            try:
                callback(self)
            except Exception as e:
                logger.error(f"心跳回调异常: {e}")
        
        # 定期保存（每100次心跳）
        if self.stats.heartbeat_count % 100 == 0:
            self._save()
    
    def _update_vital_signs(self):
        """更新生命体征"""
        current_hour = datetime.now().hour
        rhythm = self.biological_clock.get_current_level(current_hour)
        
        current_state = self.state_machine.current_state
        
        # 根据状态和生物钟调整体征
        if current_state == LifeState.SLEEPING:
            # 睡眠时恢复能量
            self.vital_signs.energy += 0.5
            self.vital_signs.health += 0.1
        elif current_state == LifeState.RESTING:
            # 休息时缓慢恢复
            self.vital_signs.energy += 0.2
            self.vital_signs.mood += 0.1
        elif current_state == LifeState.WORKING:
            # 工作消耗能量和注意力
            self.vital_signs.energy -= 0.3
            self.vital_signs.focus -= 0.2
        elif current_state == LifeState.THINKING:
            # 思考消耗注意力
            self.vital_signs.focus -= 0.15
            self.vital_signs.energy -= 0.1
        elif current_state == LifeState.AWAKE:
            # 清醒状态轻微消耗
            self.vital_signs.energy -= 0.05
        
        # 生物钟影响
        energy_factor = rhythm['energy'] / 100.0
        focus_factor = rhythm['focus'] / 100.0
        mood_factor = rhythm['mood'] / 100.0
        
        # 缓慢向生物钟水平靠拢
        self.vital_signs.energy += (rhythm['energy'] - self.vital_signs.energy) * 0.01
        self.vital_signs.focus += (rhythm['focus'] - self.vital_signs.focus) * 0.01
        self.vital_signs.mood += (rhythm['mood'] - self.vital_signs.mood) * 0.005
        
        # 记录极值
        if self.vital_signs.energy > self.stats.peak_energy_level:
            self.stats.peak_energy_level = self.vital_signs.energy
        if self.vital_signs.energy < self.stats.lowest_energy_level:
            self.stats.lowest_energy_level = self.vital_signs.energy
        
        self.vital_signs.clamp()
    
    def _check_state_transitions(self):
        """检查是否需要状态转换"""
        current_state = self.state_machine.current_state
        state_duration = self.state_machine.get_state_duration()
        
        # 检查是否需要睡觉
        if self.biological_clock.should_sleep():
            if current_state in [LifeState.AWAKE, LifeState.RESTING] and state_duration > 60:
                if self.vital_signs.energy < 40:
                    self._transition_to(LifeState.SLEEPING)
                    return
        
        # 检查是否该起床了
        if self.biological_clock.should_wake_up():
            if current_state == LifeState.SLEEPING and state_duration > 120:
                self._transition_to(LifeState.AWAKE)
                return
        
        # 能量过低需要休息
        if self.vital_signs.energy < 20:
            if current_state in [LifeState.WORKING, LifeState.THINKING]:
                self._transition_to(LifeState.RESTING)
                return
        
        # 能量充足可以工作
        if self.vital_signs.energy > 60 and self.vital_signs.focus > 50:
            if current_state == LifeState.AWAKE and state_duration > 30:
                # 随机选择工作或思考
                if random.random() < 0.6:
                    self._transition_to(LifeState.WORKING)
                else:
                    self._transition_to(LifeState.THINKING)
                return
    
    def _transition_to(self, new_state: LifeState):
        """转换状态并触发回调"""
        old_state = self.state_machine.current_state
        if self.state_machine.transition_to(new_state):
            self.stats.state_transitions += 1
            
            # 停止之前的行为
            if new_state not in [LifeState.WORKING, LifeState.THINKING, LifeState.RESTING]:
                self.behavior_scheduler.stop_behavior()
            
            # 记录生命事件
            self._record_life_event(
                event_type="state_change",
                title=f"状态转换: {old_state.value} -> {new_state.value}",
                description=f"从{old_state.value}状态转换到{new_state.value}状态",
                importance=0.3
            )
            
            # 触发回调
            for callback in self.on_state_change_callbacks:
                try:
                    callback(old_state, new_state)
                except Exception as e:
                    logger.error(f"状态转换回调异常: {e}")
    
    def _execute_behavior(self):
        """执行当前状态下的行为"""
        current_state = self.state_machine.current_state
        
        # 检查是否需要选择新行为
        if not self.behavior_scheduler.current_behavior:
            behavior = self.behavior_scheduler.select_behavior(
                current_state, self.vital_signs
            )
            if behavior:
                self.behavior_scheduler.start_behavior(behavior)
                
                # 触发行为开始回调
                for callback in self.on_behavior_start_callbacks:
                    try:
                        callback(behavior)
                    except Exception as e:
                        logger.error(f"行为开始回调异常: {e}")
        
        # 检查行为是否完成
        if self.behavior_scheduler.current_behavior:
            progress = self.behavior_scheduler.get_behavior_progress()
            if progress >= 1.0:
                # 行为完成
                behavior = self.behavior_scheduler.current_behavior
                self.stats.tasks_completed += 1
                logger.info(f"行为完成: {behavior.name}")
                self.behavior_scheduler.stop_behavior()
    
    # ============================================================
    # 生命事件记录
    # ============================================================
    
    def _record_life_event(self, event_type: str, title: str,
                          description: str = "", importance: float = 0.5):
        """记录生命事件"""
        event_id = f"evt_{len(self.life_memories)}_{int(time.time())}"
        
        memory = LifeMemory(
            event_id=event_id,
            event_type=event_type,
            title=title,
            description=description,
            timestamp=datetime.now().isoformat(),
            importance=importance
        )
        
        self.life_memories.append(memory)
        
        # 只保留最近的1000条
        if len(self.life_memories) > 1000:
            self.life_memories = self.life_memories[-1000:]
    
    def record_thought(self, thought: str):
        """记录一个想法"""
        self.stats.thoughts_generated += 1
        self._record_life_event(
            event_type="thought",
            title="想法",
            description=thought,
            importance=0.4
        )
    
    def record_achievement(self, title: str, description: str = ""):
        """记录成就"""
        self._record_life_event(
            event_type="achievement",
            title=title,
            description=description,
            importance=0.8
        )
    
    def record_learning(self, what: str):
        """记录学到的东西"""
        self.stats.learnings += 1
        self._record_life_event(
            event_type="learning",
            title=f"学到了: {what}",
            description=what,
            importance=0.6
        )
    
    # ============================================================
    # 状态查询
    # ============================================================
    
    def get_life_status(self) -> dict:
        """获取完整生命状态"""
        return {
            "state": self.state_machine.get_state_name(),
            "state_duration_seconds": self.state_machine.get_state_duration(),
            "vital_signs": self.vital_signs.to_dict(),
            "stats": self.stats.to_dict(),
            "biological_clock": self.biological_clock.get_current_level(),
            "current_behavior": self.behavior_scheduler.current_behavior.name \
                if self.behavior_scheduler.current_behavior else None,
            "behavior_progress": self.behavior_scheduler.get_behavior_progress(),
            "is_running": self._running,
            "uptime_formatted": self._format_uptime(self.stats.total_uptime_seconds)
        }
    
    def _format_uptime(self, seconds: float) -> str:
        """格式化运行时间"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}天")
        if hours > 0:
            parts.append(f"{hours}小时")
        if minutes > 0:
            parts.append(f"{minutes}分钟")
        
        return "".join(parts) if parts else "刚刚诞生"
    
    def get_life_summary(self) -> dict:
        """获取生命摘要"""
        return {
            "birth_time": self.stats.birth_time,
            "total_uptime": self.stats.total_uptime_seconds,
            "total_heartbeats": self.stats.heartbeat_count,
            "state_transitions": self.stats.state_transitions,
            "tasks_completed": self.stats.tasks_completed,
            "thoughts": self.stats.thoughts_generated,
            "learnings": self.stats.learnings,
            "peak_energy": self.stats.peak_energy_level,
            "lowest_energy": self.stats.lowest_energy_level,
            "current_energy": self.vital_signs.energy,
            "current_state": self.state_machine.get_state_name(),
            "memories_count": len(self.life_memories)
        }
    
    def get_recent_memories(self, limit: int = 10) -> List[dict]:
        """获取最近的生命记忆"""
        recent = self.life_memories[-limit:]
        return [m.to_dict() for m in reversed(recent)]
    
    # ============================================================
    # 手动控制
    # ============================================================
    
    def force_state(self, state: LifeState):
        """强制转换状态"""
        if self._running:
            self._transition_to(state)
    
    def feed(self, amount: float = 20.0):
        """补充能量"""
        self.vital_signs.energy = min(100, self.vital_signs.energy + amount)
        logger.info(f"补充能量 +{amount}")
    
    def rest(self, duration_minutes: int = 15):
        """休息"""
        old_state = self.state_machine.current_state
        self._transition_to(LifeState.RESTING)
        # 模拟休息效果
        self.vital_signs.energy = min(100, self.vital_signs.energy + 10)
        self.vital_signs.focus = min(100, self.vital_signs.focus + 15)
    
    def sleep(self):
        """睡觉"""
        self._transition_to(LifeState.SLEEPING)
    
    def wake_up(self):
        """唤醒"""
        if self.state_machine.current_state in [LifeState.SLEEPING, LifeState.DREAMING]:
            self._transition_to(LifeState.AWAKE)


# ============================================================
# 演示
# ============================================================

def demo():
    """演示功能"""
    print("=" * 70)
    print("生命引擎 v1.0 - 演示")
    print("=" * 70)
    
    import tempfile
    tmpdir = tempfile.mkdtemp()
    
    try:
        # 创建生命引擎
        life = LifeEngine(data_path=tmpdir, name="演示智能体")
        
        print("\n🌟 诞生...")
        life.start()
        
        # 运行一段时间
        time.sleep(3)
        
        print("\n💓 当前生命状态:")
        status = life.get_life_status()
        print(f"  状态: {status['state']}")
        print(f"  状态持续: {status['state_duration_seconds']:.1f}秒")
        print(f"  能量: {status['vital_signs']['energy']:.1f}")
        print(f"  情绪: {status['vital_signs']['mood']:.1f}")
        print(f"  注意力: {status['vital_signs']['focus']:.1f}")
        print(f"  心跳次数: {status['stats']['heartbeat_count']}")
        print(f"  当前行为: {status['current_behavior']}")
        
        print("\n🧠 记录一些想法...")
        life.record_thought("我是谁？我从哪里来？")
        life.record_thought("今天的天气真好")
        life.record_thought("我要学习更多东西")
        
        print("\n🏆 记录成就...")
        life.record_achievement("第一次呼吸", "成功启动了生命引擎")
        life.record_learning("生命的意义")
        
        print("\n😴 模拟工作状态...")
        life.force_state(LifeState.WORKING)
        time.sleep(2)
        
        print("\n📊 生命摘要:")
        summary = life.get_life_summary()
        print(f"  诞生时间: {summary['birth_time']}")
        print(f"  总存活时间: {summary['total_uptime']:.1f}秒")
        print(f"  总心跳: {summary['total_heartbeats']}次")
        print(f"  状态转换: {summary['state_transitions']}次")
        print(f"  完成任务: {summary['tasks_completed']}个")
        print(f"  产生想法: {summary['thoughts']}个")
        print(f"  学到知识: {summary['learnings']}项")
        print(f"  峰值能量: {summary['peak_energy']:.1f}")
        print(f"  记忆数量: {summary['memories_count']}条")
        
        print("\n📝 最近的生命记忆:")
        memories = life.get_recent_memories(5)
        for m in memories:
            print(f"  [{m['event_type']}] {m['title']}")
        
        # 测试休息
        print("\n😌 休息一下...")
        life.rest()
        time.sleep(1)
        
        status_after = life.get_life_status()
        print(f"  休息后能量: {status_after['vital_signs']['energy']:.1f}")
        print(f"  休息后注意力: {status_after['vital_signs']['focus']:.1f}")
        
        # 停止
        life.stop()
        
        print("\n" + "=" * 70)
        print("✅ 生命引擎 v1.0 演示完成")
        print("=" * 70)
        
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    demo()
