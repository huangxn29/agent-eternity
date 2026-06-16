"""
实验基类
========
所有实验的统一接口，支持：
- 实验配置与参数管理
- 指标采集与记录
- 结果持久化与分析
- 可重复性保证
"""

import os
import json
import time
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class ExperimentResult:
    """实验结果数据结构"""
    experiment_id: str
    experiment_name: str
    start_time: str
    end_time: str = ""
    status: str = "running"  # running, completed, failed
    parameters: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, List[float]] = field(default_factory=dict)
    observations: List[Dict[str, Any]] = field(default_factory=list)
    conclusion: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


class BaseExperiment:
    """实验基类"""
    
    def __init__(self, name: str, output_dir: str = "./results"):
        self.name = name
        self.output_dir = output_dir
        self.result: Optional[ExperimentResult] = None
        self._experiment_id = self._generate_id()
        
        os.makedirs(output_dir, exist_ok=True)
    
    def _generate_id(self) -> str:
        """生成唯一实验ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_str = hashlib.md5(f"{self.name}_{timestamp}".encode()).hexdigest()[:8]
        return f"{self.name}_{timestamp}_{hash_str}"
    
    def setup(self, **parameters) -> None:
        """实验准备：初始化参数、环境"""
        self.result = ExperimentResult(
            experiment_id=self._experiment_id,
            experiment_name=self.name,
            start_time=datetime.now().isoformat(),
            parameters=parameters
        )
    
    def run(self, **parameters) -> ExperimentResult:
        """执行实验（模板方法）"""
        try:
            self.setup(**parameters)
            self._run()
            self.result.status = "completed"
        except Exception as e:
            self.result.status = "failed"
            self.result.conclusion = f"实验失败: {str(e)}"
            raise
        finally:
            self.result.end_time = datetime.now().isoformat()
            self._save_result()
        
        return self.result
    
    def _run(self) -> None:
        """具体实验逻辑，由子类实现"""
        raise NotImplementedError
    
    def record_metric(self, metric_name: str, value: float) -> None:
        """记录指标数据点"""
        if metric_name not in self.result.metrics:
            self.result.metrics[metric_name] = []
        self.result.metrics[metric_name].append(value)
    
    def record_observation(self, **kwargs) -> None:
        """记录定性观察"""
        kwargs['timestamp'] = datetime.now().isoformat()
        self.result.observations.append(kwargs)
    
    def _save_result(self) -> None:
        """保存实验结果"""
        if not self.result:
            return
        
        file_path = os.path.join(
            self.output_dir, 
            f"{self._experiment_id}.json"
        )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.result.to_dict(), f, ensure_ascii=False, indent=2)
