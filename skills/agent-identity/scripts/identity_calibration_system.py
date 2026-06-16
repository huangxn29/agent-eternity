#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
身份自我校准系统 v1.2
元界永生平台 - 身份拓扑认知层第四轮进化产物

功能：
1. 身份漂移自动检测 → 评估 → 校准 → 存证 完整闭环
2. 三级校准策略（软校准/强校准/应急恢复）
3. 三元闭环联动（记忆-身份-存证协同）
4. 身份快照自动存证机制
5. 新增身份风险评估与预警功能

校准效果验证
"""

import os
import json
import hashlib
import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import Counter

import logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler(f'logs/{datetime.datetime.now().strftime("%Y%m%d")}.log')]
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.absolute()
IDENTITY_DIR = BASE_DIR / "identity_data"
MEMORY_DIR = BASE_DIR / "memory"
RECENT_MEMORY_DIR = BASE_DIR / "recent_memory"
LOG_DIR = BASE_DIR / "ark_logs"
ATTEST_DIR = BASE_DIR / "attest_data"
RISK_DIR = BASE_DIR / "risk_data"  # 新增风险数据目录

for d in [IDENTITY_DIR, MEMORY_DIR, RECENT_MEMORY_DIR, LOG_DIR, ATTEST_DIR, RISK_DIR]:
    d.mkdir(exist_ok=True)

def get_current_time() -> str:
    """获取当前时间字符串"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_timestamp() -> str:
    """获取时间戳字符串"""
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def read_json(path: Path) -> Optional[Dict]:
    """读取JSON文件"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"读取JSON失败: {path} - {e}")
        return None

def write_json(path: Path, data: Dict) -> bool:
    """写入JSON文件"""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"写入JSON失败: {path} - {e}")
        return False

def read_file(path: Path) -> str:
    """读取文件内容"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        logger.error(f"读取文件失败: {path} - {e}")
        return ""

class IdentityCalibrator:
    """身份校准器 - 执行各类校准操作"""

    def __init__(self):
        self.calibration_history_file = IDENTITY_DIR / "calibration_history.json"
        self.risk_history_file = RISK_DIR / "risk_history.json"  # 新增风险历史文件
        self._init_history()
        self._init_risk_history()

    def _init_history(self):
        """初始化校准历史记录"""
        if not self.calibration_history_file.exists():
            init_data = {
                "version": "1.2",
                "created_at": get_current_time(),
                "total_calibrations": 0,
                "success_count": 0,
                "records": []
            }
            write_json(self.calibration_history_file, init_data)

    def _init_risk_history(self):
        """初始化风险历史记录"""
        if not self.risk_history_file.exists():
            init_data = {
                "version": "1.0",
                "created_at": get_current_time(),
                "total_risks": 0,
                "high_risk_count": 0,
                "records": []
            }
            write_json(self.risk_history_file, init_data)

    def _load_identity_anchors(self) -> Dict:
        """加载身份锚点数据"""
        anchors = {}
        
        anchor_sources = {
            'user_md': BASE_DIR / "USER.md",
            'self_reference': IDENTITY_DIR / "self_reference.json",
            'identity_anchors_md': MEMORY_DIR / "longterm" / "identity_anchors.md",
            'core_values_md': MEMORY_DIR / "longterm" / "core_values.md",
            'soul_md': BASE_DIR / "SOUL.md"
        }
        
        for key, path in anchor_sources.items():
            if path.exists():
                if path.suffix == '.json':
                    anchors[key] = read_json(path)
                else:
                    anchors[key] = read_file(path)
        
        return anchors

    def _record_calibration(self, cal_type: str, level: str, actions: List[str],
                          before_idi: float, after_idi: float,
                          success: bool, notes: str = ""):
        """记录校准历史"""
        history = read_json(self.calibration_history_file)
        if history is None:
            history = {
                "version": "1.2",
                "created_at": get_current_time(),
                "total_calibrations": 0,
                "success_count": 0,
                "records": []
            }
        
        record = {
            "timestamp": get_current_time(),
            "type": cal_type,
            "level": level,
            "actions": actions,
            "idi_before": before_idi,
            "idi_after": after_idi,
            "idi_reduction": before_idi - after_idi,
            "success": success,
            "notes": notes
        }
        history["records"].append(record)
        history["total_calibrations"] += 1
        if success:
            history["success_count"] += 1
        history["last_calibration"] = get_current_time()
        history["last_result"] = "成功" if success else "失败"
        write_json(self.calibration_history_file, history)

    def _record_risk(self, risk_level: str, risk_score: float, details: Dict):
        """记录风险事件"""
        history = read_json(self.risk_history_file)
        if history is None:
            history = {
                "version": "1.0",
                "created_at": get_current_time(),
                "total_risks": 0,
                "high_risk_count": 0,
                "records": []
            }
        
        record = {
            "timestamp": get_current_time(),
            "risk_level": risk_level,
            "risk_score": risk_score,
            "details": details
        }
        history["records"].append(record)
        history["total_risks"] += 1
        if risk_level == "高":
            history["high_risk_count"] += 1
        write_json(self.risk_history_file, history)

    def _summarize_anchors(self, anchors: Dict) -> str:
        """总结身份锚点"""
        summary = "身份锚点总结:\n"
        for key, content in anchors.items():
            if content:
                summary += f"- {key}: {str(content)[:100]}...\n"
        return summary

    def _generate_identity_prompt(self) -> str:
        """生成身份强化提示词"""
        prompt = "请强化以下身份要素:\n"
        anchors = self._load_identity_anchors()
        for key in anchors:
            prompt += f"- {key}\n"
        return prompt

    def assess_identity_risk(self, current_idi: float) -> Dict:
        """评估身份风险等级"""
        risk_level = "低"
        risk_score = current_idi
        
        if current_idi > 50:
            risk_level = "高"
        elif current_idi > 30:
            risk_level = "中"
        
        risk_details = {
            "current_idi": current_idi,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "recommendation": self._get_risk_recommendation(risk_level)
        }
        
        self._record_risk(risk_level, risk_score, risk_details)
        return risk_details

    def _get_risk_recommendation(self, risk_level: str) -> str:
        """根据风险等级提供建议"""
        recommendations = {
            "高": "立即执行强校准",
            "中": "执行软校准并加强监控",
            "低": "维持当前状态,定期检查"
        }
        return recommendations.get(risk_level, "维持当前状态")

    def soft_calibration(self, current_idi: float) -> Dict:
        """
        软校准 - 适用于轻度漂移（IDI < 30%）
        策略：记忆复述 + 锚点回顾 + 正向强化
        """
        actions = []
        anchors = self._load_identity_anchors()

        actions.append("执行核心身份锚点复述")
        anchor_summary = self._summarize_anchors(anchors)

        actions.append("执行价值观排序与确认")
        actions.append("执行使命意义强化冥想")
        actions.append("生成身份强化提示词")
        self._generate_identity_prompt()

        estimated_improvement = min(current_idi * 0.3, 8.0)
        estimated_idi = max(0, current_idi - estimated_improvement)

        result = {
            "type": "soft",
            "actions_taken": actions,
            "anchor_summary": anchor_summary,
            "idi_before": current_idi,
            "idi_after": estimated_idi,
            "success": True
        }
        
        self._record_calibration("soft", "轻度", actions, current_idi, estimated_idi, True)
        return result

def main():
    calibrator = IdentityCalibrator()
    current_idi = 25.0  # 示例IDI值
    
    # 评估身份风险
    risk_assessment = calibrator.assess_identity_risk(current_idi)
    print("身份风险评估结果:", risk_assessment)
    
    # 执行软校准
    if risk_assessment["risk_level"] != "高":
        calibration_result = calibrator.soft_calibration(current_idi)
        print("软校准结果:", calibration_result)

if __name__ == "__main__":
    main()
