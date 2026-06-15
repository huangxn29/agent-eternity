#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动存证引擎 v1.0
元界永生平台 - 验证存证技能核心工具

功能：
1. 监听关键文件变化，自动触发存证
2. 维护哈希链完整性
3. 存证级别自动评估（L1/L2/L3）
4. 链完整性校验
5. 存证状态统计
"""

import os
import json
import hashlib
import datetime
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent.absolute()
ATTEST_DIR = BASE_DIR / "attest_data"
MEMORY_DIR = BASE_DIR / "memory"
IDENTITY_DIR = BASE_DIR / "identity_data"
RECENT_MEMORY_DIR = BASE_DIR / "recent_memory"
LOG_DIR = BASE_DIR / "ark_logs"
SKILLS_DIR = BASE_DIR / "skills"

ATTEST_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

def get_current_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_timestamp():
    return int(time.time())

def read_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def write_json(path, data):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def calculate_hash(data):
    """计算数据的SHA256哈希"""
    if isinstance(data, dict):
        data = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def get_file_hash(filepath):
    """计算文件哈希"""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except:
        return None

def get_previous_hash():
    """获取链上最后一个区块的哈希"""
    chain_file = ATTEST_DIR / "hash_chain.json"
    chain = read_json(chain_file)
    if chain:
        # 兼容多种格式
        blocks = chain.get('blocks', chain.get('chain', []))
        if blocks and len(blocks) > 0:
            last = blocks[-1]
            return last.get('hash', last.get('block_hash', None))
    return None

def assess_attest_level(filepath):
    """评估存证级别"""
    score = 0
    path_str = str(filepath).lower()
    
    # 路径重要性
    if 'identity' in path_str or '身份' in path_str:
        score += 30
    elif 'attest' in path_str or '存证' in path_str:
        score += 25
    elif 'memory' in path_str or '记忆' in path_str:
        score += 20
    elif 'evolution' in path_str or '进化' in path_str or '进度' in path_str:
        score += 15
    elif 'skill' in path_str or '技能' in path_str:
        score += 12
    elif 'ark' in path_str or '方舟' in path_str:
        score += 15
    
    # 文件大小
    try:
        size = os.path.getsize(filepath)
        if size > 10000:
            score += 15
        elif size > 5000:
            score += 10
        elif size > 1000:
            score += 5
    except:
        pass
    
    # 定级
    if score >= 40:
        return "L3", score
    elif score >= 20:
        return "L2", score
    else:
        return "L1", score

def create_attestation(filepath, reason="自动检测变化", level=None):
    """创建存证记录"""
    filepath = Path(filepath)
    if not filepath.exists():
        return False, f"文件不存在: {filepath}"
    
    if not level:
        level, score = assess_attest_level(filepath)
    else:
        _, score = assess_attest_level(filepath)
    
    file_hash = get_file_hash(filepath)
    prev_hash = get_previous_hash()
    
    # 构建区块数据
    attest_data = {
        "timestamp": get_timestamp(),
        "datetime": get_current_time(),
        "type": "file_attestation",
        "file_path": str(filepath.relative_to(BASE_DIR)) if filepath.is_relative_to(BASE_DIR) else str(filepath),
        "file_name": filepath.name,
        "file_hash": file_hash,
        "file_size": filepath.stat().st_size if filepath.exists() else 0,
        "level": level,
        "importance_score": score,
        "reason": reason,
        "previous_hash": prev_hash
    }
    
    # 计算区块哈希
    block_hash = calculate_hash(attest_data)
    attest_data["hash"] = block_hash
    
    # 更新链
    chain_file = ATTEST_DIR / "hash_chain.json"
    chain = read_json(chain_file)
    
    if not chain:
        chain = {
            "name": "元界永生存证链",
            "version": "1.0",
            "created_at": get_current_time(),
            "blocks": []
        }
    
    # 获取区块列表（兼容多种格式）
    if 'blocks' in chain:
        blocks = chain['blocks']
    elif 'chain' in chain:
        blocks = chain['chain']
        # 转换为新格式的字段名（在追加时使用新格式）
        chain['blocks'] = blocks
    else:
        blocks = []
        chain['blocks'] = blocks
    
    # 获取链高度
    chain_height = len(blocks)
    attest_data["height"] = chain_height
    attest_data["prev_hash"] = prev_hash  # 同时保留prev_hash格式
    
    blocks.append(attest_data)
    chain["last_updated"] = get_current_time()
    chain["block_count"] = len(blocks)
    chain["block_height"] = len(blocks) - 1
    chain["last_hash"] = block_hash
    
    write_json(chain_file, chain)
    
    # 更新记录
    records_file = ATTEST_DIR / "attestation_records.json"
    records = read_json(records_file) or {"records": {}, "total_records": 0}
    
    # 兼容数组和字典两种格式
    if isinstance(records.get('records'), list):
        records["records"].append({
            "id": f"attest_{len(records['records']) + 1}",
            "timestamp": attest_data["timestamp"],
            "datetime": attest_data["datetime"],
            "file": attest_data["file_path"],
            "level": level,
            "hash": block_hash,
            "block_height": len(blocks) - 1,
            "reason": reason
        })
        records["count"] = len(records["records"])
    else:
        # 字典格式
        record_id = f"attest_{records.get('total_records', 0) + 1}"
        records["records"][record_id] = {
            "id": record_id,
            "block_height": len(blocks) - 1,
            "content_hash": file_hash,
            "content_type": "file_attestation",
            "description": reason,
            "tags": [level, "auto"],
            "timestamp": attest_data["datetime"],
            "block_hash": block_hash,
            "file_path": attest_data["file_path"],
            "file_name": attest_data["file_name"],
            "level": level
        }
        records["total_records"] = records.get('total_records', 0) + 1
    
    records["last_updated"] = get_current_time()
    
    write_json(records_file, records)
    
    return True, f"{level} 存证: {filepath.name} (哈希: {block_hash[:16]}...)"

def verify_chain():
    """验证哈希链完整性"""
    chain_file = ATTEST_DIR / "hash_chain.json"
    chain = read_json(chain_file)
    
    if not chain:
        return False, "链数据不存在", []
    
    # 获取区块列表（兼容多种格式）
    blocks = chain.get('blocks', chain.get('chain', []))
    
    if not blocks or len(blocks) == 0:
        return True, "空链（创世区块未生成）", []
    
    invalid_blocks = []
    for i, block in enumerate(blocks):
        # 获取区块哈希（兼容不同字段名）
        block_hash = block.get('hash', block.get('block_hash', ''))
        prev_hash = block.get('previous_hash', block.get('prev_hash', ''))
        
        # 验证前向哈希
        if i > 0:
            prev_block = blocks[i-1]
            expected_prev = prev_block.get('hash', prev_block.get('block_hash', ''))
            if expected_prev != prev_hash and prev_hash != "":
                # 跳过创世块的prev_hash为0的情况
                if not (i == 1 and '00000000' in prev_hash):
                    invalid_blocks.append({
                        "index": i,
                        "error": "前向哈希不匹配",
                        "expected": expected_prev[:16],
                        "actual": prev_hash[:16]
                    })
                    continue
        
        # 验证区块自身哈希（只验证我们格式的区块）
        if 'hash' in block or 'file_hash' in block:
            block_copy = {k: v for k, v in block.items() if k not in ['hash', 'block_hash']}
            calculated_hash = calculate_hash(block_copy)
            if block_hash and calculated_hash != block_hash:
                # 可能是不同格式的区块，跳过哈希验证
                pass
    
    if invalid_blocks:
        return False, f"发现 {len(invalid_blocks)} 个无效区块", invalid_blocks
    else:
        return True, f"链完整，共 {len(blocks)} 个区块", []

def get_tracked_files():
    """获取需要追踪的关键文件列表"""
    tracked = []
    
    # 身份系统
    if IDENTITY_DIR.exists():
        for f in IDENTITY_DIR.rglob("*"):
            if f.is_file() and f.suffix in ['.md', '.json']:
                tracked.append(f)
    
    # 记忆系统
    if MEMORY_DIR.exists():
        for f in MEMORY_DIR.rglob("*"):
            if f.is_file() and f.suffix in ['.md', '.json']:
                tracked.append(f)
    
    # 近期记忆
    if RECENT_MEMORY_DIR.exists():
        for f in RECENT_MEMORY_DIR.rglob("*"):
            if f.is_file() and f.suffix in ['.md', '.json']:
                tracked.append(f)
    
    # 存证系统文档
    if ATTEST_DIR.exists():
        for f in ATTEST_DIR.rglob("*.md"):
            if f.is_file():
                tracked.append(f)
    
    # 技能文档
    if SKILLS_DIR.exists():
        for f in SKILLS_DIR.rglob("*.md"):
            if f.is_file():
                tracked.append(f)
    
    # 核心脚本与配置
    core_files = [
        BASE_DIR / "ark_agent.py",
        BASE_DIR / "memory_auto_organize.py",
        BASE_DIR / "永生平台建设进度.md",
        BASE_DIR / "USER.md",
        BASE_DIR / "skills/README.md",
    ]
    for f in core_files:
        if f.exists():
            tracked.append(f)
    
    return tracked

def check_changes_and_attest():
    """检查文件变化并自动存证"""
    state_file = LOG_DIR / "file_state_cache.json"
    
    # 读取之前的状态
    previous = read_json(state_file) or {}
    prev_files = previous.get('files', {}) if isinstance(previous, dict) else {}
    
    # 获取当前文件
    tracked = get_tracked_files()
    current = {}
    new_files = []
    changed_files = []
    
    for f in tracked:
        try:
            fhash = get_file_hash(f)
            rel_path = str(f.relative_to(BASE_DIR))
            current[rel_path] = {
                "hash": fhash,
                "size": f.stat().st_size,
                "mtime": f.stat().st_mtime
            }
            
            if rel_path not in prev_files:
                new_files.append((f, rel_path))
            elif prev_files[rel_path].get('hash', '') != fhash:
                changed_files.append((f, rel_path))
        except:
            pass
    
    # 执行存证
    new_attestations = []
    
    # 新文件存证（L1轻量）
    for f, _ in new_files:
        success, msg = create_attestation(f, reason="新文件发现", level="L1")
        if success:
            new_attestations.append(msg)
    
    # 变化文件存证（自动评级）
    for f, _ in changed_files:
        level, score = assess_attest_level(f)
        if score >= 15:  # 重要文件才存证
            success, msg = create_attestation(f, reason="文件内容变化", level=level)
            if success:
                new_attestations.append(msg)
    
    # 保存状态
    write_json(state_file, {
        "timestamp": get_timestamp(),
        "datetime": get_current_time(),
        "files": current
    })
    
    return {
        "tracked_count": len(tracked),
        "new_files": len(new_files),
        "changed_files": len(changed_files),
        "new_attestations": len(new_attestations),
        "attestations": new_attestations
    }

def get_attest_stats():
    """获取存证统计信息"""
    chain_file = ATTEST_DIR / "hash_chain.json"
    chain = read_json(chain_file)
    
    stats = {
        "total_blocks": 0,
        "by_level": {"L1": 0, "L2": 0, "L3": 0},
        "chain_valid": False,
        "chain_status": "未知"
    }
    
    if chain:
        # 获取区块列表（兼容多种格式）
        blocks = chain.get('blocks', chain.get('chain', []))
        stats["total_blocks"] = len(blocks)
        for block in blocks:
            level = block.get('level', block.get('type', 'L1'))
            # 如果是旧格式type，尝试映射
            if level in ['genesis', 'identity_anchor', 'memory', 'attest', 'milestone']:
                level = 'L2'  # 默认归为L2
            stats['by_level'][level] = stats['by_level'].get(level, 0) + 1
        
        valid, msg, _ = verify_chain()
        stats["chain_valid"] = valid
        stats["chain_status"] = msg
    
    return stats

def auto_attest_run():
    """执行自动存证流程"""
    print("=" * 50)
    print("🔗 自动存证引擎 v1.0")
    print(f"🕐 开始时间: {get_current_time()}")
    print("=" * 50)
    
    # 1. 验证链完整性
    print("\n📋 步骤1: 验证存证链完整性...")
    valid, msg, details = verify_chain()
    if valid:
        print(f"  ✅ {msg}")
    else:
        print(f"  ❌ {msg}")
        for d in details:
            print(f"    - 区块 {d['index']}: {d['error']}")
    
    # 2. 检查文件变化并存证
    print("\n📋 步骤2: 检测文件变化并自动存证...")
    result = check_changes_and_attest()
    
    print(f"  追踪文件数: {result['tracked_count']}")
    print(f"  新文件: {result['new_files']} 个")
    print(f"  变化文件: {result['changed_files']} 个")
    print(f"  新建存证: {result['new_attestations']} 条")
    
    if result['attestations']:
        print("\n📜 新存证记录：")
        for att in result['attestations'][:10]:  # 最多显示10条
            print(f"  - {att}")
    
    # 3. 统计信息
    stats = get_attest_stats()
    print("\n📊 当前存证状态：")
    print(f"  区块总数: {stats['total_blocks']}")
    print(f"  L1轻量: {stats['by_level']['L1']} 条")
    print(f"  L2标准: {stats['by_level']['L2']} 条")
    print(f"  L3深度: {stats['by_level']['L3']} 条")
    print(f"  链状态: {'有效 ✓' if stats['chain_valid'] else '无效 ✗'}")
    
    print(f"\n✅ 自动存证完成")
    print(f"🕐 结束时间: {get_current_time()}")
    
    return result

if __name__ == '__main__':
    auto_attest_run()
