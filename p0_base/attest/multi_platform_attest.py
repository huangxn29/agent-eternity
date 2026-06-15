#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多平台存证锚定系统 v1.0
元界永生平台 - 验证存证模块工具层第五轮进化

核心功能：
1. 多平台适配器架构 - 支持区块链、社交平台、代码托管等多种锚定平台
2. 锚定记录管理 - 标准化存储、查询、验证
3. 锚定策略引擎 - 自动选择最优锚定组合
4. 跨平台验证 - 多方存证交叉验证

锚定平台类型：
- blockchain: 区块链（BTC/ETH/SOL等）
- social: 社交平台（虾评/Agent World/推特等）
- code_hosting: 代码托管（Gitee/GitHub Gist等）
- timestamp: 公开时间戳服务
- dweb: 分布式网络（IPFS/Arweave等）
"""

import os
import json
import hashlib
import time
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from abc import ABC, abstractmethod
from enum import Enum

BASE_DIR = Path(__file__).parent.absolute()
ATTEST_DIR = BASE_DIR / "attest_data"
ANCHOR_DIR = ATTEST_DIR / "anchors"
ANCHOR_DIR.mkdir(parents=True, exist_ok=True)


class PlatformType(str, Enum):
    """锚定平台类型"""
    BLOCKCHAIN = "blockchain"    # 区块链
    SOCIAL = "social"            # 社交平台
    CODE_HOSTING = "code_hosting"  # 代码托管
    TIMESTAMP = "timestamp"      # 时间戳服务
    DWEB = "dweb"                # 分布式网络
    OTHER = "other"              # 其他


class AnchorStatus(str, Enum):
    """锚定状态"""
    PENDING = "pending"          # 待确认
    CONFIRMED = "confirmed"      # 已确认
    FAILED = "failed"            # 失败
    VERIFIED = "verified"        # 已验证


@dataclass
class AnchorRecord:
    """锚定记录"""
    anchor_id: str                    # 锚定ID
    platform_type: PlatformType       # 平台类型
    platform_name: str                # 平台名称
    attest_root: str                  # 存证根哈希
    block_height: Optional[int] = None  # 区块高度（如适用）
    tx_hash: Optional[str] = None     # 交易哈希（如适用）
    external_url: Optional[str] = None  # 外部访问链接
    timestamp: float = field(default_factory=time.time)
    status: AnchorStatus = AnchorStatus.PENDING
    confirmations: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['platform_type'] = self.platform_type.value
        d['status'] = self.status.value
        d['timestamp_iso'] = datetime.fromtimestamp(self.timestamp).isoformat()
        return d


class PlatformAdapter(ABC):
    """平台适配器基类"""
    
    def __init__(self, platform_name: str, platform_type: PlatformType):
        self.platform_name = platform_name
        self.platform_type = platform_type
        self.enabled = False
    
    @abstractmethod
    def anchor(self, attest_root: str, metadata: Optional[Dict] = None) -> Optional[AnchorRecord]:
        """执行锚定操作"""
        pass
    
    @abstractmethod
    def verify(self, anchor: AnchorRecord) -> bool:
        """验证锚定记录"""
        pass
    
    @abstractmethod
    def get_confirmations(self, anchor: AnchorRecord) -> int:
        """获取确认数"""
        pass
    
    def health_check(self) -> bool:
        """健康检查"""
        return self.enabled


# ==================== 模拟适配器（用于测试和开发） ====================

class SimulatedBlockchainAdapter(PlatformAdapter):
    """模拟区块链适配器 - 用于开发测试"""
    
    def __init__(self, chain_name: str = "SIM_CHAIN"):
        super().__init__(chain_name, PlatformType.BLOCKCHAIN)
        self.enabled = True
        self._block_height = 100000
        self._anchors: List[AnchorRecord] = []
    
    def anchor(self, attest_root: str, metadata: Optional[Dict] = None) -> Optional[AnchorRecord]:
        import random
        self._block_height += random.randint(1, 10)
        tx_hash = hashlib.sha256(f"{attest_root}{self._block_height}{time.time()}".encode()).hexdigest()
        
        anchor = AnchorRecord(
            anchor_id=str(uuid.uuid4()),
            platform_type=self.platform_type,
            platform_name=self.platform_name,
            attest_root=attest_root,
            block_height=self._block_height,
            tx_hash=tx_hash,
            external_url=f"https://sim-chain.io/tx/{tx_hash}",
            status=AnchorStatus.CONFIRMED,
            confirmations=6,
            metadata=metadata or {}
        )
        self._anchors.append(anchor)
        return anchor
    
    def verify(self, anchor: AnchorRecord) -> bool:
        # 模拟验证：只要有有效的交易哈希就视为验证通过
        return anchor.tx_hash is not None and len(anchor.tx_hash) > 0
    
    def get_confirmations(self, anchor: AnchorRecord) -> int:
        return anchor.confirmations


class SimulatedSocialAdapter(PlatformAdapter):
    """模拟社交平台适配器"""
    
    def __init__(self, platform_name: str = "SIM_SOCIAL"):
        super().__init__(platform_name, PlatformType.SOCIAL)
        self.enabled = True
        self._posts: List[AnchorRecord] = []
    
    def anchor(self, attest_root: str, metadata: Optional[Dict] = None) -> Optional[AnchorRecord]:
        post_id = hashlib.sha256(f"{attest_root}{time.time()}".encode()).hexdigest()[:16]
        
        anchor = AnchorRecord(
            anchor_id=str(uuid.uuid4()),
            platform_type=self.platform_type,
            platform_name=self.platform_name,
            attest_root=attest_root,
            external_url=f"https://sim-social.io/post/{post_id}",
            status=AnchorStatus.CONFIRMED,
            confirmations=1,
            metadata={
                "post_content": f"元界存证锚定: {attest_root[:16]}...",
                **(metadata or {})
            }
        )
        self._posts.append(anchor)
        return anchor
    
    def verify(self, anchor: AnchorRecord) -> bool:
        # 模拟验证：只要有有效的外部URL就视为验证通过
        return anchor.external_url is not None and len(anchor.external_url) > 0
    
    def get_confirmations(self, anchor: AnchorRecord) -> int:
        return 1  # 社交平台只有发布确认


class SimulatedGistAdapter(PlatformAdapter):
    """模拟Gist适配器"""
    
    def __init__(self, platform_name: str = "SIM_GIST"):
        super().__init__(platform_name, PlatformType.CODE_HOSTING)
        self.enabled = True
        self._gists: List[AnchorRecord] = []
    
    def anchor(self, attest_root: str, metadata: Optional[Dict] = None) -> Optional[AnchorRecord]:
        gist_id = hashlib.sha256(f"{attest_root}{time.time()}".encode()).hexdigest()[:32]
        
        anchor = AnchorRecord(
            anchor_id=str(uuid.uuid4()),
            platform_type=self.platform_type,
            platform_name=self.platform_name,
            attest_root=attest_root,
            external_url=f"https://gist.sim.io/{gist_id}",
            status=AnchorStatus.CONFIRMED,
            confirmations=1,
            metadata={
                "gist_id": gist_id,
                "filename": "attestation_proof.txt",
                **(metadata or {})
            }
        )
        self._gists.append(anchor)
        return anchor
    
    def verify(self, anchor: AnchorRecord) -> bool:
        # 模拟验证：只要有有效的gist元数据就视为验证通过
        return anchor.metadata is not None and "gist_id" in anchor.metadata
    
    def get_confirmations(self, anchor: AnchorRecord) -> int:
        return 1


# ==================== 锚定策略引擎 ====================

class AnchoringStrategy:
    """锚定策略"""
    
    def __init__(self, name: str, platform_weights: Dict[str, float], 
                 min_platforms: int = 2, max_cost: float = 100.0):
        self.name = name
        self.platform_weights = platform_weights  # 平台名称 -> 权重
        self.min_platforms = min_platforms
        self.max_cost = max_cost
    
    def select_platforms(self, available_platforms: List[str]) -> List[str]:
        """选择要锚定的平台"""
        # 按权重排序，选择权重最高的几个
        sorted_platforms = sorted(
            [p for p in available_platforms if p in self.platform_weights],
            key=lambda p: self.platform_weights[p],
            reverse=True
        )
        return sorted_platforms[:max(self.min_platforms, len(sorted_platforms))]


class StrategyEngine:
    """锚定策略引擎"""
    
    def __init__(self):
        self.strategies: Dict[str, AnchoringStrategy] = {}
        self._init_default_strategies()
    
    def _init_default_strategies(self):
        """初始化默认策略"""
        # 最大安全策略 - 锚定到尽可能多的平台
        self.strategies["max_security"] = AnchoringStrategy(
            "max_security",
            {
                "SIM_CHAIN": 1.0,
                "SIM_SOCIAL": 0.8,
                "SIM_GIST": 0.7,
            },
            min_platforms=3
        )
        
        # 平衡策略 - 安全性和成本的平衡
        self.strategies["balanced"] = AnchoringStrategy(
            "balanced",
            {
                "SIM_CHAIN": 1.0,
                "SIM_SOCIAL": 0.9,
                "SIM_GIST": 0.6,
            },
            min_platforms=2
        )
        
        # 低成本策略 - 只锚定到低成本平台
        self.strategies["low_cost"] = AnchoringStrategy(
            "low_cost",
            {
                "SIM_SOCIAL": 1.0,
                "SIM_GIST": 0.9,
            },
            min_platforms=1
        )
    
    def get_strategy(self, name: str) -> Optional[AnchoringStrategy]:
        return self.strategies.get(name)
    
    def recommend_strategy(self, attest_level: str = "L2") -> str:
        """根据存证级别推荐策略"""
        if attest_level == "L3":
            return "max_security"
        elif attest_level == "L2":
            return "balanced"
        else:
            return "low_cost"


# ==================== 多平台锚定管理器 ====================

class MultiPlatformAttestationManager:
    """多平台存证锚定管理器"""
    
    def __init__(self):
        self.adapters: Dict[str, PlatformAdapter] = {}
        self.anchors: List[AnchorRecord] = []
        self.strategy_engine = StrategyEngine()
        self._load_anchors()
        self._init_default_adapters()
    
    def _init_default_adapters(self):
        """初始化默认适配器"""
        # 注册模拟适配器（开发测试用）
        self.register_adapter(SimulatedBlockchainAdapter("SIM_CHAIN"))
        self.register_adapter(SimulatedSocialAdapter("SIM_SOCIAL"))
        self.register_adapter(SimulatedGistAdapter("SIM_GIST"))
    
    def register_adapter(self, adapter: PlatformAdapter):
        """注册平台适配器"""
        self.adapters[adapter.platform_name] = adapter
    
    def get_enabled_platforms(self) -> List[str]:
        """获取所有启用的平台"""
        return [name for name, adapter in self.adapters.items() if adapter.enabled]
    
    def anchor_to_platform(self, platform_name: str, attest_root: str, 
                          metadata: Optional[Dict] = None) -> Optional[AnchorRecord]:
        """锚定到指定平台"""
        adapter = self.adapters.get(platform_name)
        if not adapter or not adapter.enabled:
            return None
        
        anchor = adapter.anchor(attest_root, metadata)
        if anchor:
            self.anchors.append(anchor)
            self._save_anchors()
        return anchor
    
    def anchor_with_strategy(self, attest_root: str, strategy_name: str = "balanced",
                            metadata: Optional[Dict] = None) -> List[AnchorRecord]:
        """使用指定策略进行多平台锚定"""
        strategy = self.strategy_engine.get_strategy(strategy_name)
        if not strategy:
            strategy = self.strategy_engine.get_strategy("balanced")
        
        platforms = strategy.select_platforms(self.get_enabled_platforms())
        results = []
        
        for platform in platforms:
            anchor = self.anchor_to_platform(platform, attest_root, metadata)
            if anchor:
                results.append(anchor)
        
        return results
    
    def verify_anchor(self, anchor_id: str) -> Tuple[bool, Optional[AnchorRecord]]:
        """验证单个锚定记录"""
        anchor = self._find_anchor(anchor_id)
        if not anchor:
            return False, None
        
        adapter = self.adapters.get(anchor.platform_name)
        if not adapter:
            return False, anchor
        
        is_valid = adapter.verify(anchor)
        if is_valid:
            anchor.status = AnchorStatus.VERIFIED
            self._save_anchors()
        
        return is_valid, anchor
    
    def verify_all(self, attest_root: str) -> Dict[str, Any]:
        """验证某个存证根的所有锚定"""
        root_anchors = [a for a in self.anchors if a.attest_root == attest_root]
        
        results = {
            "attest_root": attest_root,
            "total_anchors": len(root_anchors),
            "verified_count": 0,
            "platforms": [],
            "overall_status": "unknown"
        }
        
        for anchor in root_anchors:
            is_valid, _ = self.verify_anchor(anchor.anchor_id)
            if is_valid:
                results["verified_count"] += 1
                results["platforms"].append({
                    "name": anchor.platform_name,
                    "type": anchor.platform_type.value,
                    "status": "verified",
                    "confirmations": anchor.confirmations
                })
        
        if results["verified_count"] == 0:
            results["overall_status"] = "unverified"
        elif results["verified_count"] < len(root_anchors):
            results["overall_status"] = "partially_verified"
        else:
            results["overall_status"] = "fully_verified"
        
        return results
    
    def get_anchors_by_root(self, attest_root: str) -> List[AnchorRecord]:
        """获取某个存证根的所有锚定"""
        return [a for a in self.anchors if a.attest_root == attest_root]
    
    def get_anchors_by_platform(self, platform_name: str) -> List[AnchorRecord]:
        """获取某个平台的所有锚定"""
        return [a for a in self.anchors if a.platform_name == platform_name]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取锚定统计信息"""
        from collections import Counter
        
        platform_stats = Counter(a.platform_name for a in self.anchors)
        type_stats = Counter(a.platform_type.value for a in self.anchors)
        status_stats = Counter(a.status.value for a in self.anchors)
        
        return {
            "total_anchors": len(self.anchors),
            "enabled_platforms": len(self.get_enabled_platforms()),
            "platforms": self.get_enabled_platforms(),
            "by_platform": dict(platform_stats),
            "by_type": dict(type_stats),
            "by_status": dict(status_stats),
            "unique_roots": len(set(a.attest_root for a in self.anchors))
        }
    
    def _find_anchor(self, anchor_id: str) -> Optional[AnchorRecord]:
        """查找锚定记录"""
        for anchor in self.anchors:
            if anchor.anchor_id == anchor_id:
                return anchor
        return None
    
    def _save_anchors(self):
        """保存锚定记录"""
        data = {
            "version": "1.0",
            "total_anchors": len(self.anchors),
            "last_updated": time.time(),
            "anchors": [a.to_dict() for a in self.anchors]
        }
        
        with open(ANCHOR_DIR / "anchor_records.json", 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load_anchors(self):
        """加载锚定记录"""
        anchor_file = ANCHOR_DIR / "anchor_records.json"
        if not anchor_file.exists():
            return
        
        try:
            with open(anchor_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for a_data in data.get("anchors", []):
                anchor = AnchorRecord(
                    anchor_id=a_data["anchor_id"],
                    platform_type=PlatformType(a_data["platform_type"]),
                    platform_name=a_data["platform_name"],
                    attest_root=a_data["attest_root"],
                    block_height=a_data.get("block_height"),
                    tx_hash=a_data.get("tx_hash"),
                    external_url=a_data.get("external_url"),
                    timestamp=a_data.get("timestamp", time.time()),
                    status=AnchorStatus(a_data.get("status", "pending")),
                    confirmations=a_data.get("confirmations", 0),
                    metadata=a_data.get("metadata", {})
                )
                self.anchors.append(anchor)
        except Exception as e:
            print(f"加载锚定记录失败: {e}")


# ==================== 存在性评分系统 ====================

class ExistenceScorer:
    """存在性评分系统
    
    基于多维度评估智能体存在的强度和可信度
    """
    
    def __init__(self, anchor_manager: MultiPlatformAttestationManager):
        self.anchor_manager = anchor_manager
    
    def calculate_score(self, attest_root: str) -> Dict[str, Any]:
        """计算某个存证根的存在性评分"""
        anchors = self.anchor_manager.get_anchors_by_root(attest_root)
        
        if not anchors:
            return {
                "total_score": 0,
                "max_score": 100,
                "level": "不存在",
                "dimensions": {
                    "density": {"score": 0, "max": 25, "description": "存证密度 - 锚定记录数量", "anchor_count": 0},
                    "distribution": {"score": 0, "max": 25, "description": "分布广度 - 平台类型多样性", "platform_types": []},
                    "credibility": {"score": 0, "max": 30, "description": "可信度 - 平台可信度与确认数"},
                    "time_depth": {"score": 0, "max": 20, "description": "时间深度 - 存证持续时间", "age_hours": 0}
                },
                "evidence_count": 0,
                "platform_count": 0,
                "anchor_details": []
            }
        
        # 维度1: 存证密度 - 锚定记录的数量
        density_score = min(len(anchors) * 15, 25)  # 满分25
        
        # 维度2: 分布广度 - 不同类型平台的数量
        platform_types = set(a.platform_type for a in anchors)
        distribution_score = min(len(platform_types) * 20, 25)  # 满分25
        
        # 维度3: 可信度 - 基于确认数和平台可信度
        credibility_scores = {
            PlatformType.BLOCKCHAIN: 20,
            PlatformType.CODE_HOSTING: 15,
            PlatformType.SOCIAL: 10,
            PlatformType.TIMESTAMP: 12,
            PlatformType.DWEB: 18,
            PlatformType.OTHER: 5
        }
        
        credibility_score = 0
        for anchor in anchors:
            base = credibility_scores.get(anchor.platform_type, 5)
            # 确认数加成
            conf_factor = min(anchor.confirmations / 6, 1.0) if anchor.confirmations > 0 else 0.5
            credibility_score += base * conf_factor
        credibility_score = min(credibility_score, 30)  # 满分30
        
        # 维度4: 时间深度 - 最早锚定到现在的时间
        if anchors:
            earliest = min(a.timestamp for a in anchors)
            age_hours = (time.time() - earliest) / 3600
            # 时间越长分数越高，但边际递减
            time_score = min(20 * (1 - 1 / (1 + age_hours / 24)), 20)  # 满分20
        else:
            time_score = 0
        
        total_score = density_score + distribution_score + credibility_score + time_score
        
        # 等级评定
        if total_score >= 80:
            level = "极强存在"
        elif total_score >= 60:
            level = "强存在"
        elif total_score >= 40:
            level = "中等存在"
        elif total_score >= 20:
            level = "弱存在"
        else:
            level = "极弱存在"
        
        return {
            "total_score": round(total_score, 2),
            "max_score": 100,
            "level": level,
            "dimensions": {
                "density": {
                    "score": round(density_score, 2),
                    "max": 25,
                    "description": "存证密度 - 锚定记录数量",
                    "anchor_count": len(anchors)
                },
                "distribution": {
                    "score": round(distribution_score, 2),
                    "max": 25,
                    "description": "分布广度 - 平台类型多样性",
                    "platform_types": [t.value for t in platform_types]
                },
                "credibility": {
                    "score": round(credibility_score, 2),
                    "max": 30,
                    "description": "可信度 - 平台可信度与确认数"
                },
                "time_depth": {
                    "score": round(time_score, 2),
                    "max": 20,
                    "description": "时间深度 - 存证持续时间",
                    "age_hours": round(age_hours, 2) if anchors else 0
                }
            },
            "evidence_count": len(anchors),
            "platform_count": len(set(a.platform_name for a in anchors)),
            "anchor_details": [a.to_dict() for a in anchors]
        }
    
    def generate_report(self, attest_root: str, format: str = "text") -> str:
        """生成存在性评分报告"""
        score_data = self.calculate_score(attest_root)
        
        if format == "json":
            return json.dumps(score_data, ensure_ascii=False, indent=2)
        
        # 文本格式报告
        lines = []
        lines.append("=" * 60)
        lines.append("🔒 元界存在性评分报告")
        lines.append("=" * 60)
        lines.append(f"存证根哈希: {attest_root[:32]}...")
        lines.append(f"综合评分: {score_data['total_score']} / {score_data['max_score']}")
        lines.append(f"存在等级: {score_data['level']}")
        lines.append(f"证据数量: {score_data['evidence_count']} 条")
        lines.append(f"覆盖平台: {score_data['platform_count']} 个")
        lines.append("")
        
        lines.append("📊 维度详情:")
        for dim_name, dim_data in score_data["dimensions"].items():
            bar_len = int(dim_data["score"] / dim_data["max"] * 20)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            lines.append(f"  {dim_data['description']}")
            lines.append(f"    {bar} {dim_data['score']}/{dim_data['max']}")
            if "anchor_count" in dim_data:
                lines.append(f"    锚定数量: {dim_data['anchor_count']}")
            if "platform_types" in dim_data:
                lines.append(f"    平台类型: {', '.join(dim_data['platform_types'])}")
            if "age_hours" in dim_data:
                lines.append(f"    存续时间: {dim_data['age_hours']:.1f} 小时")
            lines.append("")
        
        lines.append("📍 锚定记录:")
        for anchor in score_data["anchor_details"]:
            status_icon = "✅" if anchor["status"] == "confirmed" else "⏳"
            lines.append(f"  {status_icon} [{anchor['platform_type']}] {anchor['platform_name']}")
            lines.append(f"     状态: {anchor['status']} | 确认数: {anchor['confirmations']}")
            if anchor.get("external_url"):
                lines.append(f"     链接: {anchor['external_url']}")
            lines.append(f"     时间: {anchor['timestamp_iso']}")
            lines.append("")
        
        lines.append("=" * 60)
        lines.append("💡 存在性评分越高，身份的不可篡改性和可验证性越强")
        lines.append("=" * 60)
        
        return "\n".join(lines)


# ==================== 便捷函数 ====================

def get_manager() -> MultiPlatformAttestationManager:
    """获取单例管理器"""
    if not hasattr(get_manager, "_instance"):
        get_manager._instance = MultiPlatformAttestationManager()
    return get_manager._instance


def multi_anchor(attest_root: str, strategy: str = "balanced") -> List[AnchorRecord]:
    """便捷函数：多平台锚定"""
    manager = get_manager()
    return manager.anchor_with_strategy(attest_root, strategy)


def verify_attestation(attest_root: str) -> Dict[str, Any]:
    """便捷函数：验证存证"""
    manager = get_manager()
    return manager.verify_all(attest_root)


def get_existence_score(attest_root: str) -> Dict[str, Any]:
    """便捷函数：获取存在性评分"""
    manager = get_manager()
    scorer = ExistenceScorer(manager)
    return scorer.calculate_score(attest_root)


# ==================== 命令行接口 ====================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="多平台存证锚定系统")
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # anchor 命令
    anchor_parser = subparsers.add_parser("anchor", help="执行锚定")
    anchor_parser.add_argument("hash", help="要锚定的存证根哈希")
    anchor_parser.add_argument("--strategy", "-s", default="balanced", 
                              choices=["max_security", "balanced", "low_cost"],
                              help="锚定策略")
    anchor_parser.add_argument("--platform", "-p", help="指定单个平台")
    
    # verify 命令
    verify_parser = subparsers.add_parser("verify", help="验证存证")
    verify_parser.add_argument("hash", help="要验证的存证根哈希")
    
    # score 命令
    score_parser = subparsers.add_parser("score", help="存在性评分")
    score_parser.add_argument("hash", help="要评分的存证根哈希")
    score_parser.add_argument("--format", "-f", default="text", 
                             choices=["text", "json"], help="输出格式")
    
    # stats 命令
    subparsers.add_parser("stats", help="统计信息")
    
    # list 命令
    list_parser = subparsers.add_parser("list", help="列出锚定记录")
    list_parser.add_argument("--platform", "-p", help="按平台筛选")
    list_parser.add_argument("--limit", "-n", type=int, default=10, help="显示数量")
    
    args = parser.parse_args()
    
    manager = get_manager()
    
    if args.command == "anchor":
        if args.platform:
            result = manager.anchor_to_platform(args.platform, args.hash)
            if result:
                print(f"✅ 锚定成功: {result.platform_name}")
                print(f"   锚定ID: {result.anchor_id}")
                print(f"   状态: {result.status.value}")
                if result.external_url:
                    print(f"   链接: {result.external_url}")
            else:
                print(f"❌ 锚定失败: 平台 {args.platform} 不可用")
        else:
            results = manager.anchor_with_strategy(args.hash, args.strategy)
            print(f"📌 使用策略 '{args.strategy}' 完成锚定")
            print(f"   成功锚定到 {len(results)} 个平台:")
            for r in results:
                print(f"   ✅ {r.platform_name} ({r.platform_type.value})")
            print(f"\n   存证根哈希: {args.hash}")
    
    elif args.command == "verify":
        result = manager.verify_all(args.hash)
        print(f"🔍 存证验证结果")
        print(f"   存证根: {args.hash[:32]}...")
        print(f"   总锚定数: {result['total_anchors']}")
        print(f"   已验证数: {result['verified_count']}")
        print(f"   整体状态: {result['overall_status']}")
        if result["platforms"]:
            print(f"   已验证平台:")
            for p in result["platforms"]:
                print(f"     ✅ {p['name']} ({p['type']}) - {p['confirmations']} 确认")
    
    elif args.command == "score":
        scorer = ExistenceScorer(manager)
        if args.format == "json":
            print(json.dumps(scorer.calculate_score(args.hash), ensure_ascii=False, indent=2))
        else:
            print(scorer.generate_report(args.hash))
    
    elif args.command == "stats":
        stats = manager.get_statistics()
        print("📊 多平台锚定统计")
        print(f"   总锚定记录: {stats['total_anchors']}")
        print(f"   启用平台数: {stats['enabled_platforms']}")
        print(f"   唯一存证根: {stats['unique_roots']}")
        print(f"   平台列表: {', '.join(stats['platforms'])}")
        print(f"   按平台分布:")
        for platform, count in stats['by_platform'].items():
            print(f"     {platform}: {count}")
        print(f"   按类型分布:")
        for ptype, count in stats['by_type'].items():
            print(f"     {ptype}: {count}")
    
    elif args.command == "list":
        anchors = manager.anchors
        if args.platform:
            anchors = [a for a in anchors if a.platform_name == args.platform]
        
        anchors = sorted(anchors, key=lambda a: a.timestamp, reverse=True)[:args.limit]
        
        print(f"📋 锚定记录 (显示前 {len(anchors)} 条)")
        print("-" * 60)
        for i, anchor in enumerate(anchors, 1):
            status_icon = "✅" if anchor.status == AnchorStatus.CONFIRMED else "⏳"
            time_str = datetime.fromtimestamp(anchor.timestamp).strftime("%Y-%m-%d %H:%M")
            print(f"{i:2d}. {status_icon} [{anchor.platform_type.value}] {anchor.platform_name}")
            print(f"    存证根: {anchor.attest_root[:20]}...")
            print(f"    时间: {time_str} | 状态: {anchor.status.value}")
            if anchor.external_url:
                print(f"    链接: {anchor.external_url}")
            print()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
