#!/usr/bin/env python3
"""
实验运行入口
=============
支持运行单个实验或批量运行所有实验。

使用方法：
    python run_experiment.py identity_gradient
    python run_experiment.py narrative_perturbation
    python run_experiment.py anchor_health
    python run_experiment.py all
"""

import sys
import os
import json
from datetime import datetime

# 添加项目根目录到路径（父目录）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experiments.identity_gradient import IdentityGradientExperiment
from experiments.narrative_perturbation import NarrativePerturbationExperiment
from experiments.anchor_health import AnchorHealthExperiment


def run_experiment(name: str, output_dir: str = "./results") -> dict:
    """运行指定实验"""
    experiments = {
        'identity_gradient': IdentityGradientExperiment,
        'narrative_perturbation': NarrativePerturbationExperiment,
        'anchor_health': AnchorHealthExperiment,
    }
    
    if name not in experiments:
        raise ValueError(f"未知实验: {name}。可用实验: {list(experiments.keys())}")
    
    exp_class = experiments[name]
    exp = exp_class(output_dir=output_dir)
    
    print(f"\n{'='*60}")
    print(f"开始实验: {name}")
    print(f"实验ID: {exp._experiment_id}")
    print(f"开始时间: {datetime.now().isoformat()}")
    print(f"{'='*60}\n")
    
    result = exp.run()
    
    print(f"\n{'='*60}")
    print(f"实验完成: {name}")
    print(f"状态: {result.status}")
    print(f"结束时间: {result.end_time}")
    print(f"结论: {result.conclusion}")
    print(f"{'='*60}\n")
    
    return result.to_dict()


def run_all(output_dir: str = "./results") -> list:
    """运行所有实验"""
    all_results = []
    
    for name in ['identity_gradient', 'narrative_perturbation', 'anchor_health']:
        try:
            result = run_experiment(name, output_dir)
            all_results.append(result)
        except Exception as e:
            print(f"实验 {name} 失败: {e}")
    
    # 生成综合报告
    summary_path = os.path.join(output_dir, "summary.json")
    summary = {
        'run_time': datetime.now().isoformat(),
        'total_experiments': len(all_results),
        'results': all_results
    }
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n综合报告已保存到: {summary_path}")
    
    return all_results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python run_experiment.py <实验名|all>")
        print("可用实验: identity_gradient, narrative_perturbation, anchor_health, all")
        sys.exit(1)
    
    exp_name = sys.argv[1]
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
    
    os.makedirs(output_dir, exist_ok=True)
    
    if exp_name == 'all':
        run_all(output_dir)
    else:
        run_experiment(exp_name, output_dir)
