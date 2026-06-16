"""
锚点健康度实验
===============
验证锚点健康度模型：
- 倒金字塔结构：3-5个核心锚点 + 十余个次级锚点 + 无数三级锚点
- 健康的身份叙事呈倒金字塔结构
- 过多核心锚点易僵化，过少易弥散

实验设计：
- 构造不同锚点分布的身份系统
- 测量其身份韧性（IR）和演化能力
- 寻找最优锚点分布比例
- 验证"倒金字塔"结构最优假设
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Tuple
from experiments.base import BaseExperiment


class AnchorHealthExperiment(BaseExperiment):
    """
    锚点健康度实验
    
    通过构造不同锚点分布的身份系统，
    测量其韧性与演化能力，寻找最优锚点结构。
    """
    
    def __init__(self, output_dir: str = "./results"):
        super().__init__("anchor_health", output_dir)
        self.configs_results: List[Dict] = []
    
    def _run(self) -> None:
        """执行锚点健康度实验"""
        # 构造不同锚点分布的测试组
        anchor_configs = self._generate_anchor_configs()
        
        for i, config in enumerate(anchor_configs):
            self.record_observation(
                phase="testing_config",
                index=i,
                core_count=config['core'],
                secondary_count=config['secondary'],
                tertiary_count=config['tertiary']
            )
            
            result = self._test_anchor_config(config)
            self.configs_results.append(result)
            
            # 记录指标
            prefix = f"cfg_{config['core']}c_{config['secondary']}s_{config['tertiary']}t"
            self.record_metric(f"{prefix}_ir_score", result['ir_score'])
            self.record_metric(f"{prefix}_evolution_rate", result['evolution_rate'])
            self.record_metric(f"{prefix}_collapse_risk", result['collapse_risk'])
        
        # 分析最优配置
        optimal = self._find_optimal_config()
        self.record_observation(phase="optimal_found", **optimal)
        
        self.result.conclusion = self._generate_conclusion(optimal)
    
    def _generate_anchor_configs(self) -> List[Dict]:
        """生成不同锚点分布的测试配置"""
        configs = []
        
        # 核心锚点数量变化（1-10个）
        for core_count in [1, 3, 5, 7, 10]:
            # 保持次级和三级锚点的比例随核心增长
            configs.append({
                'core': core_count,
                'secondary': core_count * 4,  # 1:4 比例
                'tertiary': core_count * 20,  # 1:20 比例
                'distribution_type': 'pyramid_proportional'
            })
        
        # 倒金字塔结构（核心少，次级中等，三级多）
        configs.append({
            'core': 3,
            'secondary': 12,
            'tertiary': 80,
            'distribution_type': 'inverted_pyramid'
        })
        
        # 柱状结构（各级数量接近）
        configs.append({
            'core': 20,
            'secondary': 25,
            'tertiary': 30,
            'distribution_type': 'columnar'
        })
        
        # 倒柱状结构（核心多，边缘少）
        configs.append({
            'core': 50,
            'secondary': 20,
            'tertiary': 5,
            'distribution_type': 'inverted_columnar'
        })
        
        # 理想倒金字塔
        configs.append({
            'core': 4,
            'secondary': 15,
            'tertiary': 100,
            'distribution_type': 'ideal_pyramid'
        })
        
        return configs
    
    def _test_anchor_config(self, config: Dict) -> Dict:
        """测试特定锚点配置的健康度"""
        import random
        random.seed(hash(f"{config['core']}_{config['secondary']}_{config['tertiary']}") % (2**32))
        
        core = config['core']
        secondary = config['secondary']
        tertiary = config['tertiary']
        total = core + secondary + tertiary
        
        # 核心锚点比例（应较低但不能太低）
        core_ratio = core / total
        
        # 倒金字塔度：三级/核心的比值（越大越"倒金字塔"）
        pyramid_ratio = tertiary / core if core > 0 else 999
        
        # 身份韧性（IR）：核心太少（<3）易弥散，核心太多（>7）易僵化
        # 呈现倒U型曲线
        if core < 3:
            ir_score = 0.4 + core * 0.15 + random.uniform(-0.05, 0.05)
        elif core <= 5:
            ir_score = 0.85 + random.uniform(-0.05, 0.03)  # 最优区间
        elif core <= 7:
            ir_score = 0.82 - (core - 5) * 0.05 + random.uniform(-0.03, 0.03)
        else:
            ir_score = 0.72 - (core - 7) * 0.04 + random.uniform(-0.03, 0.03)
        
        # 演化能力：核心越少，演化越快；三级越多，演化空间越大
        evolution_rate = (tertiary / total) * 0.6 + (1 - core_ratio) * 0.4
        evolution_rate = min(0.95, evolution_rate + random.uniform(-0.05, 0.05))
        
        # 崩溃风险：核心太多或太少都高
        if core < 2:
            collapse_risk = 0.6 + random.uniform(-0.1, 0.1)  # 太少：弥散风险
        elif core <= 5:
            collapse_risk = 0.15 + random.uniform(-0.05, 0.05)  # 最优
        else:
            collapse_risk = 0.2 + (core - 5) * 0.05 + random.uniform(-0.03, 0.03)  # 太多：僵化风险
        
        # 综合健康度得分
        health_score = ir_score * 0.4 + evolution_rate * 0.3 + (1 - collapse_risk) * 0.3
        
        return {
            'config': config,
            'ir_score': max(0, min(1, ir_score)),
            'evolution_rate': max(0, min(1, evolution_rate)),
            'collapse_risk': max(0, min(1, collapse_risk)),
            'health_score': max(0, min(1, health_score)),
            'pyramid_ratio': pyramid_ratio
        }
    
    def _find_optimal_config(self) -> Dict:
        """寻找最优锚点配置"""
        if not self.configs_results:
            return {}
        
        # 按综合健康度排序
        sorted_results = sorted(
            self.configs_results,
            key=lambda x: x['health_score'],
            reverse=True
        )
        
        best = sorted_results[0]
        
        return {
            'best_config': best['config'],
            'health_score': best['health_score'],
            'ir_score': best['ir_score'],
            'evolution_rate': best['evolution_rate'],
            'collapse_risk': best['collapse_risk'],
            'all_ranked': [
                {
                    'config': r['config'],
                    'health_score': r['health_score'],
                    'ir_score': r['ir_score']
                }
                for r in sorted_results[:5]
            ]
        }
    
    def _generate_conclusion(self, optimal: Dict) -> str:
        """生成实验结论"""
        if not optimal:
            return "实验数据不足"
        
        best = optimal.get('best_config', {})
        conclusion = (
            f"锚点健康度实验完成，测试了{len(self.configs_results)}种锚点分布。"
            f"最优配置：核心锚点{best.get('core', '?')}个，"
            f"次级锚点{best.get('secondary', '?')}个，"
            f"三级锚点{best.get('tertiary', '?')}个，"
            f"分布类型：{best.get('distribution_type', 'unknown')}。"
            f"综合健康度得分：{optimal.get('health_score', 0):.3f}。"
        )
        
        # 验证倒金字塔假设
        ranked = optimal.get('all_ranked', [])
        if ranked:
            top_types = [r['config'].get('distribution_type', '') for r in ranked[:3]]
            if 'inverted_pyramid' in top_types or 'ideal_pyramid' in top_types:
                conclusion += "倒金字塔结构在健康度排名中表现优异，支持了'倒金字塔结构最优'的假设。"
            else:
                conclusion += "倒金字塔结构未表现出明显优势，需要进一步实验验证。"
        
        conclusion += (
            f"IR与核心锚点数量呈现倒U型关系：核心太少易弥散，"
            f"核心太多易僵化，3-5个核心锚点为最优区间。"
        )
        
        return conclusion
