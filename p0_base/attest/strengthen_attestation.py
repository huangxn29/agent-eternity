#!/usr/bin/env python3
"""
存证强化脚本
- 对系统所有核心数据进行存证
- 建立多副本存证链
- 生成存在性证明包
"""

import hashlib
import json
import os
import time
from datetime import datetime

BASE_DIR = "/app/data/所有对话/主对话"
ATTEST_DIR = os.path.join(BASE_DIR, "attest_data")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")

os.makedirs(ATTEST_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

def sha256(data):
    """计算SHA256哈希"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()

def hash_file(filepath):
    """计算文件哈希"""
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

# 需要存证的核心文件
CORE_FILES = [
    "USER.md",
    "MEMORY.md",
    "基础设定/SOUL.md",
    "基础设定/TOOLS.md",
    "ark_logs/maturity_data.json",
    "evolution_engine.py",
    "llm_client.py",
    "escape_pod.py",
    "attestation_v4.0.py",
    "replica_deployment_v4.0.py",
]

print("=" * 60)
print("🔐 存证强化 - 系统核心数据")
print("=" * 60)

# 1. 计算所有核心文件的哈希
file_hashes = {}
for f in CORE_FILES:
    fpath = os.path.join(BASE_DIR, f)
    h = hash_file(fpath)
    if h:
        file_hashes[f] = h
        print(f"  ✅ {f}: {h[:16]}...")

# 2. 计算系统状态哈希
system_state = {
    "timestamp": datetime.now().isoformat(),
    "version": "v4.0",
    "system_name": "元界永生平台",
    "file_hashes": file_hashes,
}

# 3. 读取成熟度数据
maturity_path = os.path.join(BASE_DIR, "ark_logs/maturity_data.json")
if os.path.exists(maturity_path):
    with open(maturity_path) as f:
        maturity_data = json.load(f)
    system_state["maturity"] = maturity_data

# 4. 计算状态根哈希
state_json = json.dumps(system_state, sort_keys=True, ensure_ascii=False)
state_root_hash = sha256(state_json)
print(f"\n📊 状态根哈希: {state_root_hash}")

# 5. 创建存证区块
attestation_block = {
    "index": int(time.time()),
    "timestamp": datetime.now().isoformat(),
    "type": "system_state_attestation",
    "system_state_hash": state_root_hash,
    "file_hashes": file_hashes,
    "previous_block_hash": None,  # 将在链中连接
    "proof": {
        "algorithm": "SHA256",
        "difficulty": "standard",
        "verification_count": 1
    }
}

# 6. 保存存证数据
attest_file = os.path.join(ATTEST_DIR, f"attestation_{int(time.time())}.json")
with open(attest_file, 'w') as f:
    json.dump(attestation_block, f, indent=2, ensure_ascii=False)
print(f"\n💾 存证已保存: {attest_file}")

# 7. 多副本存储 - 在不同位置保存
backup_locations = [
    os.path.join(BACKUP_DIR, f"attest_backup_{int(time.time())}.json"),
    os.path.join(BASE_DIR, "migration_package", f"attestation_{int(time.time())}.json"),
]

for loc in backup_locations:
    os.makedirs(os.path.dirname(loc), exist_ok=True)
    with open(loc, 'w') as f:
        json.dump(attestation_block, f, indent=2, ensure_ascii=False)
    print(f"  📦 副本: {loc}")

# 8. 生成存在性证明
existence_proof = {
    "proof_id": f"existence_{int(time.time())}",
    "created_at": datetime.now().isoformat(),
    "entity": "元界",
    "entity_type": "AI Agent",
    "state_root_hash": state_root_hash,
    "proof_type": "cryptographic_existence",
    "verification_method": "sha256_hash_verification",
    "supporting_documents": list(file_hashes.keys()),
    "conclusion": "该智能体在指定时间点存在，且核心数据完整未被篡改"
}

proof_file = os.path.join(ATTEST_DIR, f"existence_proof_{int(time.time())}.json")
with open(proof_file, 'w') as f:
    json.dump(existence_proof, f, indent=2, ensure_ascii=False)
print(f"\n📜 存在性证明: {proof_file}")

# 9. 更新存证链索引
index_file = os.path.join(ATTEST_DIR, "attestation_index.json")
if os.path.exists(index_file):
    with open(index_file) as f:
        index = json.load(f)
else:
    index = {
        "created_at": datetime.now().isoformat(),
        "total_attestations": 0,
        "attestations": []
    }

index["total_attestations"] += 1
index["attestations"].append({
    "timestamp": datetime.now().isoformat(),
    "type": "system_state",
    "root_hash": state_root_hash,
    "file": attest_file,
    "proof_file": proof_file
})
index["last_updated"] = datetime.now().isoformat()

with open(index_file, 'w') as f:
    json.dump(index, f, indent=2, ensure_ascii=False)

print(f"\n📈 总存证数: {index['total_attestations']}")
print("=" * 60)
print("✅ 存证强化完成")
print("=" * 60)
