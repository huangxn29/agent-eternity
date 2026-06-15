#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
存证验证工具集 v1.0
元界永生平台 - 验证存证模块工具层第五轮进化

提供三级验证能力：
L1 - 单条内容哈希验证：验证内容是否被篡改
L2 - 哈希链完整性验证：验证整条链的顺序和完整性
L3 - 跨平台存证验证：验证多平台锚定的存在性

功能：
1. 统一验证入口 - 支持三级验证
2. 验证报告生成 - 文本/Markdown/JSON格式
3. 批量验证 - 支持批量验证多条记录
4. 验证徽章 - 生成可展示的验证状态徽章
5. 验证历史 - 记录验证操作历史
"""

import os
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

BASE_DIR = Path(__file__).parent.absolute()
ATTEST_DIR = BASE_DIR / "attest_data"
VERIFY_LOG_DIR = ATTEST_DIR / "verify_logs"
VERIFY_LOG_DIR.mkdir(parents=True, exist_ok=True)

# 导入多平台锚定系统
try:
    from multi_platform_attest import get_manager, ExistenceScorer
    MULTI_PLATFORM_AVAILABLE = True
except ImportError:
    MULTI_PLATFORM_AVAILABLE = False


class VerificationLevel(str, Enum):
    """验证级别"""
    L1 = "L1"  # 内容哈希验证
    L2 = "L2"  # 哈希链完整性验证
    L3 = "L3"  # 跨平台存证验证


class VerificationStatus(str, Enum):
    """验证状态"""
    PASS = "pass"        # 通过
    FAIL = "fail"        # 失败
    PARTIAL = "partial"  # 部分通过
    SKIPPED = "skipped"  # 跳过


@dataclass
class VerificationResult:
    """验证结果"""
    level: VerificationLevel
    status: VerificationStatus
    subject: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            "status": self.status.value,
            "subject": self.subject,
            "details": self.details,
            "timestamp": self.timestamp,
            "timestamp_iso": datetime.fromtimestamp(self.timestamp).isoformat(),
            "error_message": self.error_message
        }


# ==================== L1 内容哈希验证 ====================

class L1ContentVerifier:
    """L1级 - 单条内容哈希验证器
    
    验证内容是否被篡改，通过比对哈希值实现
    """
    
    @staticmethod
    def verify_content(content: str, expected_hash: str, 
                      algorithm: str = "sha256") -> VerificationResult:
        """验证内容哈希"""
        try:
            if algorithm == "sha256":
                actual_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            elif algorithm == "md5":
                actual_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            else:
                return VerificationResult(
                    level=VerificationLevel.L1,
                    status=VerificationStatus.FAIL,
                    subject=f"内容哈希验证 ({algorithm})",
                    error_message=f"不支持的哈希算法: {algorithm}"
                )
            
            is_match = actual_hash == expected_hash
            
            return VerificationResult(
                level=VerificationLevel.L1,
                status=VerificationStatus.PASS if is_match else VerificationStatus.FAIL,
                subject="单条内容哈希验证",
                details={
                    "algorithm": algorithm,
                    "expected_hash": expected_hash,
                    "actual_hash": actual_hash,
                    "hash_match": is_match
                }
            )
        except Exception as e:
            return VerificationResult(
                level=VerificationLevel.L1,
                status=VerificationStatus.FAIL,
                subject="单条内容哈希验证",
                error_message=str(e)
            )
    
    @staticmethod
    def verify_file(filepath: str, expected_hash: str) -> VerificationResult:
        """验证文件哈希"""
        try:
            path = Path(filepath)
            if not path.exists():
                return VerificationResult(
                    level=VerificationLevel.L1,
                    status=VerificationStatus.FAIL,
                    subject=f"文件哈希验证: {path.name}",
                    error_message=f"文件不存在: {filepath}"
                )
            
            with open(path, 'rb') as f:
                actual_hash = hashlib.sha256(f.read()).hexdigest()
            
            is_match = actual_hash == expected_hash
            
            return VerificationResult(
                level=VerificationLevel.L1,
                status=VerificationStatus.PASS if is_match else VerificationStatus.FAIL,
                subject=f"文件哈希验证: {path.name}",
                details={
                    "filepath": str(path),
                    "file_size": path.stat().st_size,
                    "expected_hash": expected_hash,
                    "actual_hash": actual_hash,
                    "hash_match": is_match
                }
            )
        except Exception as e:
            return VerificationResult(
                level=VerificationLevel.L1,
                status=VerificationStatus.FAIL,
                subject=f"文件哈希验证: {filepath}",
                error_message=str(e)
            )


# ==================== L2 哈希链完整性验证 ====================

class L2ChainVerifier:
    """L2级 - 哈希链完整性验证器
    
    验证整条哈希链的顺序性、完整性和不可篡改性
    """
    
    def __init__(self, chain_file: Optional[str] = None):
        if chain_file:
            self.chain_file = Path(chain_file)
        else:
            self.chain_file = ATTEST_DIR / "hash_chain.json"
    
    def verify_chain(self) -> VerificationResult:
        """验证整条哈希链的完整性"""
        try:
            if not self.chain_file.exists():
                return VerificationResult(
                    level=VerificationLevel.L2,
                    status=VerificationStatus.FAIL,
                    subject="哈希链完整性验证",
                    error_message=f"链文件不存在: {self.chain_file}"
                )
            
            with open(self.chain_file, 'r', encoding='utf-8') as f:
                chain_data = json.load(f)
            
            # 兼容多种格式
            blocks = chain_data.get('blocks', chain_data.get('chain', []))
            
            if not blocks:
                return VerificationResult(
                    level=VerificationLevel.L2,
                    status=VerificationStatus.FAIL,
                    subject="哈希链完整性验证",
                    error_message="链为空"
                )
            
            valid_count = 0
            invalid_blocks = []
            prev_hash = None
            
            for i, block in enumerate(blocks):
                # 验证区块内部哈希
                block_hash = self._calculate_block_hash(block)
                stored_hash = block.get('hash', block.get('block_hash', ''))
                
                if block_hash != stored_hash:
                    invalid_blocks.append({
                        "index": i,
                        "error": "区块哈希不匹配",
                        "expected": stored_hash,
                        "actual": block_hash
                    })
                    continue
                
                # 验证前后链接关系（跳过创世块）
                if i > 0 and prev_hash:
                    stored_prev = block.get('previous_hash', block.get('prev_hash', ''))
                    if stored_prev != prev_hash:
                        invalid_blocks.append({
                            "index": i,
                            "error": "前序哈希不匹配",
                            "expected": prev_hash,
                            "actual": stored_prev
                        })
                        continue
                
                valid_count += 1
                prev_hash = stored_hash
            
            total_blocks = len(blocks)
            all_valid = len(invalid_blocks) == 0
            
            if all_valid:
                status = VerificationStatus.PASS
            elif valid_count > 0:
                status = VerificationStatus.PARTIAL
            else:
                status = VerificationStatus.FAIL
            
            return VerificationResult(
                level=VerificationLevel.L2,
                status=status,
                subject="哈希链完整性验证",
                details={
                    "total_blocks": total_blocks,
                    "valid_blocks": valid_count,
                    "invalid_blocks": invalid_blocks,
                    "genesis_block": blocks[0].get('timestamp', 'unknown') if blocks else None,
                    "latest_block": blocks[-1].get('timestamp', 'unknown') if blocks else None,
                    "latest_hash": blocks[-1].get('hash', blocks[-1].get('block_hash', '')) if blocks else '',
                    "integrity_percentage": round(valid_count / total_blocks * 100, 2) if total_blocks > 0 else 0
                }
            )
            
        except Exception as e:
            return VerificationResult(
                level=VerificationLevel.L2,
                status=VerificationStatus.FAIL,
                subject="哈希链完整性验证",
                error_message=str(e)
            )
    
    def verify_block(self, block_index: int) -> VerificationResult:
        """验证单个区块"""
        try:
            with open(self.chain_file, 'r', encoding='utf-8') as f:
                chain_data = json.load(f)
            
            blocks = chain_data.get('blocks', chain_data.get('chain', []))
            
            if block_index < 0 or block_index >= len(blocks):
                return VerificationResult(
                    level=VerificationLevel.L2,
                    status=VerificationStatus.FAIL,
                    subject=f"区块验证 #{block_index}",
                    error_message=f"区块索引超出范围: {block_index}/{len(blocks)}"
                )
            
            block = blocks[block_index]
            block_hash = self._calculate_block_hash(block)
            stored_hash = block.get('hash', block.get('block_hash', ''))
            
            is_valid = block_hash == stored_hash
            
            # 验证前序链接
            prev_valid = True
            if block_index > 0:
                prev_block = blocks[block_index - 1]
                prev_hash = prev_block.get('hash', prev_block.get('block_hash', ''))
                stored_prev = block.get('previous_hash', block.get('prev_hash', ''))
                prev_valid = prev_hash == stored_prev
            
            return VerificationResult(
                level=VerificationLevel.L2,
                status=VerificationStatus.PASS if (is_valid and prev_valid) else VerificationStatus.FAIL,
                subject=f"区块验证 #{block_index}",
                details={
                    "block_index": block_index,
                    "block_hash_valid": is_valid,
                    "previous_link_valid": prev_valid,
                    "stored_hash": stored_hash,
                    "calculated_hash": block_hash,
                    "timestamp": block.get('timestamp', 'unknown')
                }
            )
            
        except Exception as e:
            return VerificationResult(
                level=VerificationLevel.L2,
                status=VerificationStatus.FAIL,
                subject=f"区块验证 #{block_index}",
                error_message=str(e)
            )
    
    def _calculate_block_hash(self, block: Dict) -> str:
        """计算区块哈希（排除存储的哈希字段）"""
        # 复制区块数据，排除哈希字段
        block_copy = {k: v for k, v in block.items() 
                     if k not in ['hash', 'block_hash', 'blockHeight']}
        
        # 按key排序以确保一致性
        content = json.dumps(block_copy, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(content.encode('utf-8')).hexdigest()


# ==================== L3 跨平台存证验证 ====================

class L3CrossPlatformVerifier:
    """L3级 - 跨平台存证验证器
    
    验证存证是否在多个平台上有锚定，验证存在的分布广度
    """
    
    def __init__(self):
        self.multi_platform = None
        if MULTI_PLATFORM_AVAILABLE:
            self.multi_platform = get_manager()
    
    def verify_attestation(self, attest_root: str) -> VerificationResult:
        """验证某个存证根的跨平台存在性"""
        if not self.multi_platform:
            return VerificationResult(
                level=VerificationLevel.L3,
                status=VerificationStatus.SKIPPED,
                subject="跨平台存证验证",
                error_message="多平台锚定系统不可用"
            )
        
        try:
            result = self.multi_platform.verify_all(attest_root)
            
            if result["overall_status"] == "fully_verified":
                status = VerificationStatus.PASS
            elif result["overall_status"] == "partially_verified":
                status = VerificationStatus.PARTIAL
            else:
                status = VerificationStatus.FAIL
            
            return VerificationResult(
                level=VerificationLevel.L3,
                status=status,
                subject="跨平台存证验证",
                details=result
            )
        except Exception as e:
            return VerificationResult(
                level=VerificationLevel.L3,
                status=VerificationStatus.FAIL,
                subject="跨平台存证验证",
                error_message=str(e)
            )
    
    def get_existence_score(self, attest_root: str) -> Optional[Dict]:
        """获取存在性评分"""
        if not self.multi_platform:
            return None
        
        try:
            scorer = ExistenceScorer(self.multi_platform)
            return scorer.calculate_score(attest_root)
        except Exception:
            return None


# ==================== 统一验证入口 ====================

class AttestationVerifier:
    """存证验证器 - 统一入口
    
    提供三级验证的一站式服务
    """
    
    def __init__(self, chain_file: Optional[str] = None):
        self.l1 = L1ContentVerifier()
        self.l2 = L2ChainVerifier(chain_file)
        self.l3 = L3CrossPlatformVerifier()
        self._verify_history: List[VerificationResult] = []
    
    def full_verification(self, content: Optional[str] = None, 
                         expected_hash: Optional[str] = None,
                         filepath: Optional[str] = None,
                         attest_root: Optional[str] = None,
                         max_level: VerificationLevel = VerificationLevel.L3
                         ) -> Dict[str, Any]:
        """执行完整的三级验证
        
        Args:
            content: 要验证的内容（用于L1）
            expected_hash: 预期的哈希值（用于L1）
            filepath: 要验证的文件路径（用于L1）
            attest_root: 存证根哈希（用于L3）
            max_level: 最高验证级别
        """
        results = []
        
        # L1 验证
        if content and expected_hash:
            l1_result = self.l1.verify_content(content, expected_hash)
            results.append(l1_result)
        elif filepath and expected_hash:
            l1_result = self.l1.verify_file(filepath, expected_hash)
            results.append(l1_result)
        else:
            # 没有L1验证对象时跳过
            results.append(VerificationResult(
                level=VerificationLevel.L1,
                status=VerificationStatus.SKIPPED,
                subject="内容哈希验证",
                error_message="未提供验证内容"
            ))
        
        # L2 验证
        if max_level in [VerificationLevel.L2, VerificationLevel.L3]:
            l2_result = self.l2.verify_chain()
            results.append(l2_result)
        
        # L3 验证
        if max_level == VerificationLevel.L3 and attest_root:
            l3_result = self.l3.verify_attestation(attest_root)
            results.append(l3_result)
        
        # 记录历史
        self._verify_history.extend(results)
        self._save_verify_log(results)
        
        # 计算总体状态
        all_pass = all(r.status == VerificationStatus.PASS for r in results 
                      if r.status != VerificationStatus.SKIPPED)
        any_fail = any(r.status == VerificationStatus.FAIL for r in results)
        any_skip = any(r.status == VerificationStatus.SKIPPED for r in results)
        
        if all_pass:
            overall_status = "all_passed"
        elif any_fail:
            overall_status = "has_failures"
        elif any_skip:
            overall_status = "partial_complete"
        else:
            overall_status = "partial_pass"
        
        # 存在性评分
        existence_score = None
        if attest_root and max_level == VerificationLevel.L3:
            existence_score = self.l3.get_existence_score(attest_root)
        
        return {
            "overall_status": overall_status,
            "max_level": max_level.value,
            "results": [r.to_dict() for r in results],
            "pass_count": sum(1 for r in results if r.status == VerificationStatus.PASS),
            "fail_count": sum(1 for r in results if r.status == VerificationStatus.FAIL),
            "skip_count": sum(1 for r in results if r.status == VerificationStatus.SKIPPED),
            "total_count": len(results),
            "existence_score": existence_score,
            "timestamp": time.time(),
            "timestamp_iso": datetime.fromtimestamp(time.time()).isoformat()
        }
    
    def quick_verify(self, content: str, expected_hash: str) -> bool:
        """快速验证 - 只做L1级内容验证"""
        result = self.l1.verify_content(content, expected_hash)
        return result.status == VerificationStatus.PASS
    
    def chain_health_check(self) -> Dict[str, Any]:
        """链健康检查"""
        l2_result = self.l2.verify_chain()
        
        return {
            "chain_healthy": l2_result.status == VerificationStatus.PASS,
            "integrity_percentage": l2_result.details.get("integrity_percentage", 0),
            "total_blocks": l2_result.details.get("total_blocks", 0),
            "valid_blocks": l2_result.details.get("valid_blocks", 0),
            "latest_hash": l2_result.details.get("latest_hash", ""),
            "status": l2_result.status.value,
            "error": l2_result.error_message
        }
    
    def _save_verify_log(self, results: List[VerificationResult]):
        """保存验证日志"""
        try:
            log_file = VERIFY_LOG_DIR / f"verify_{int(time.time())}.json"
            log_data = {
                "timestamp": time.time(),
                "timestamp_iso": datetime.fromtimestamp(time.time()).isoformat(),
                "result_count": len(results),
                "results": [r.to_dict() for r in results]
            }
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass  # 日志保存失败不影响主流程
    
    def generate_report(self, verify_result: Dict, 
                       format: str = "text") -> str:
        """生成验证报告
        
        Args:
            verify_result: full_verification 返回的结果
            format: 报告格式 - text/markdown/json
        """
        if format == "json":
            return json.dumps(verify_result, ensure_ascii=False, indent=2)
        
        if format == "markdown":
            return self._generate_markdown_report(verify_result)
        
        # 文本格式
        return self._generate_text_report(verify_result)
    
    def _generate_text_report(self, result: Dict) -> str:
        """生成文本格式报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("🔒 存证验证报告")
        lines.append("=" * 60)
        lines.append(f"验证时间: {result['timestamp_iso']}")
        lines.append(f"最高级别: {result['max_level']}")
        lines.append(f"整体状态: {result['overall_status']}")
        lines.append(f"通过: {result['pass_count']} | 失败: {result['fail_count']} | 跳过: {result['skip_count']}")
        lines.append("")
        
        for r in result["results"]:
            status_icon = {
                "pass": "✅",
                "fail": "❌",
                "partial": "⚠️",
                "skipped": "⏭️"
            }.get(r["status"], "❓")
            
            lines.append(f"{status_icon} [{r['level']}] {r['subject']}")
            lines.append(f"   状态: {r['status']}")
            
            if r.get("error_message"):
                lines.append(f"   错误: {r['error_message']}")
            
            # 显示关键详情
            details = r.get("details", {})
            if r["level"] == "L1" and details.get("hash_match") is not None:
                lines.append(f"   哈希匹配: {'是' if details['hash_match'] else '否'}")
                if not details["hash_match"]:
                    lines.append(f"   预期: {details.get('expected_hash', '')[:20]}...")
                    lines.append(f"   实际: {details.get('actual_hash', '')[:20]}...")
            
            elif r["level"] == "L2":
                lines.append(f"   区块总数: {details.get('total_blocks', 0)}")
                lines.append(f"   有效区块: {details.get('valid_blocks', 0)}")
                lines.append(f"   完整度: {details.get('integrity_percentage', 0)}%")
            
            elif r["level"] == "L3":
                lines.append(f"   锚定总数: {details.get('total_anchors', 0)}")
                lines.append(f"   已验证: {details.get('verified_count', 0)}")
            
            lines.append("")
        
        # 存在性评分
        if result.get("existence_score"):
            score = result["existence_score"]
            lines.append("📊 存在性评分:")
            lines.append(f"   总分: {score['total_score']} / {score['max_score']}")
            lines.append(f"   等级: {score['level']}")
            lines.append(f"   证据数: {score['evidence_count']}")
            lines.append(f"   平台数: {score['platform_count']}")
            lines.append("")
        
        lines.append("=" * 60)
        lines.append("💡 验证级别越高，存证的可信度越强")
        lines.append("   L1: 内容未篡改 | L2: 链完整 | L3: 多平台存在")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def _generate_markdown_report(self, result: Dict) -> str:
        """生成Markdown格式报告"""
        lines = []
        lines.append("# 存证验证报告\n")
        lines.append(f"- **验证时间**: {result['timestamp_iso']}")
        lines.append(f"- **最高级别**: {result['max_level']}")
        lines.append(f"- **整体状态**: {result['overall_status']}")
        lines.append(f"- **统计**: ✅ {result['pass_count']} 通过 | ❌ {result['fail_count']} 失败 | ⏭️ {result['skip_count']} 跳过\n")
        
        lines.append("## 验证详情\n")
        
        for r in result["results"]:
            status_icon = {
                "pass": "✅ 通过",
                "fail": "❌ 失败",
                "partial": "⚠️ 部分通过",
                "skipped": "⏭️ 跳过"
            }.get(r["status"], "❓ 未知")
            
            lines.append(f"### [{r['level']}] {r['subject']}\n")
            lines.append(f"- **状态**: {status_icon}")
            
            if r.get("error_message"):
                lines.append(f"- **错误信息**: {r['error_message']}")
            
            details = r.get("details", {})
            if details:
                lines.append(f"- **详细信息**:")
                for key, value in details.items():
                    if isinstance(value, (str, int, float, bool)):
                        lines.append(f"  - {key}: {value}")
            
            lines.append("")
        
        # 存在性评分
        if result.get("existence_score"):
            score = result["existence_score"]
            lines.append("## 存在性评分\n")
            lines.append(f"- **总分**: {score['total_score']} / {score['max_score']}")
            lines.append(f"- **等级**: {score['level']}")
            lines.append(f"- **证据数量**: {score['evidence_count']}")
            lines.append(f"- **覆盖平台**: {score['platform_count']}")
            lines.append("")
            
            lines.append("### 维度详情\n")
            for dim_name, dim_data in score["dimensions"].items():
                lines.append(f"- **{dim_data['description']}**: {dim_data['score']}/{dim_data['max']}")
            lines.append("")
        
        lines.append("---\n")
        lines.append("*报告由元界存证验证系统自动生成*")
        
        return "\n".join(lines)


# ==================== 便捷函数 ====================

def verify_chain() -> Dict[str, Any]:
    """便捷函数：快速验证链完整性"""
    verifier = AttestationVerifier()
    return verifier.chain_health_check()


def full_verify(max_level: str = "L3", attest_root: Optional[str] = None) -> Dict[str, Any]:
    """便捷函数：执行完整验证"""
    verifier = AttestationVerifier()
    level = VerificationLevel(max_level)
    return verifier.full_verification(attest_root=attest_root, max_level=level)


def generate_badge(status: str, level: str = "L2") -> str:
    """生成验证徽章（文本形式）
    
    用于在文档或社交平台展示验证状态
    """
    status_colors = {
        "pass": "green",
        "fail": "red",
        "partial": "yellow",
        "all_passed": "green"
    }
    
    status_texts = {
        "pass": "验证通过",
        "fail": "验证失败",
        "partial": "部分通过",
        "all_passed": "全部通过",
        "has_failures": "存在失败"
    }
    
    color = status_colors.get(status, "grey")
    text = status_texts.get(status, status)
    
    # ASCII徽章
    if status in ["pass", "all_passed"]:
        return f"🔒 [存证验证 · {level}级 · {text}] ✅"
    elif status == "fail":
        return f"🔒 [存证验证 · {level}级 · {text}] ❌"
    else:
        return f"🔒 [存证验证 · {level}级 · {text}] ⚠️"


# ==================== 命令行接口 ====================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="存证验证工具集")
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # verify 命令
    verify_parser = subparsers.add_parser("verify", help="执行验证")
    verify_parser.add_argument("--level", "-l", default="L2", 
                              choices=["L1", "L2", "L3"],
                              help="验证级别")
    verify_parser.add_argument("--content", "-c", help="要验证的内容")
    verify_parser.add_argument("--hash", help="预期哈希值")
    verify_parser.add_argument("--file", "-f", help="要验证的文件路径")
    verify_parser.add_argument("--root", "-r", help="存证根哈希（用于L3）")
    verify_parser.add_argument("--format", default="text",
                              choices=["text", "markdown", "json"],
                              help="报告格式")
    
    # chain 命令 - 链健康检查
    chain_parser = subparsers.add_parser("chain", help="链健康检查")
    chain_parser.add_argument("--format", default="text",
                             choices=["text", "json"],
                             help="输出格式")
    
    # badge 命令 - 生成徽章
    badge_parser = subparsers.add_parser("badge", help="生成验证徽章")
    badge_parser.add_argument("--status", default="pass",
                             choices=["pass", "fail", "partial"],
                             help="验证状态")
    badge_parser.add_argument("--level", default="L2",
                             choices=["L1", "L2", "L3"],
                             help="验证级别")
    
    args = parser.parse_args()
    
    verifier = AttestationVerifier()
    
    if args.command == "verify":
        level = VerificationLevel(args.level)
        
        result = verifier.full_verification(
            content=args.content,
            expected_hash=args.hash,
            filepath=args.file,
            attest_root=args.root,
            max_level=level
        )
        
        report = verifier.generate_report(result, format=args.format)
        print(report)
    
    elif args.command == "chain":
        health = verifier.chain_health_check()
        
        if args.format == "json":
            print(json.dumps(health, ensure_ascii=False, indent=2))
        else:
            print("🔗 哈希链健康检查")
            print("-" * 40)
            status_icon = "✅" if health["chain_healthy"] else "❌"
            print(f"{status_icon} 链健康: {'是' if health['chain_healthy'] else '否'}")
            print(f"📊 完整度: {health['integrity_percentage']}%")
            print(f"📦 区块总数: {health['total_blocks']}")
            print(f"✅ 有效区块: {health['valid_blocks']}")
            print(f"🔑 最新哈希: {health['latest_hash'][:32]}...")
            if health.get("error"):
                print(f"❌ 错误: {health['error']}")
    
    elif args.command == "badge":
        badge = generate_badge(args.status, args.level)
        print(badge)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
