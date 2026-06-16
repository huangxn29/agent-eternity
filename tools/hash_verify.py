#!/usr/bin/env python3
"""
记忆哈希校验工具
=================
用于生成记忆内容的多级哈希摘要，支持：
1. 全文哈希（最粗粒度，用于快速比对）
2. 按条目哈希（中等粒度，用于定位差异）
3. 按语义区块哈希（最细粒度，用于深度校验）

校验级别：
- level 1: 全文单哈希（快速验证完整性）
- level 2: 按章节/条目哈希（定位差异区域）
- level 3: 语义块哈希 + 因果链哈希（深度保真验证）

使用方法：
    python hash_verify.py generate <记忆文件> [--level 1|2|3]
    python hash_verify.py verify <记忆文件> <哈希文件>
    python hash_verify.py diff <哈希文件1> <哈希文件2>
"""

import hashlib
import json
import argparse
import os
from datetime import datetime
from typing import Dict, List, Tuple


def hash_content(content: str, algorithm: str = 'sha256') -> str:
    """计算内容的哈希值"""
    return hashlib.new(algorithm, content.encode('utf-8')).hexdigest()


def parse_memory_structure(content: str) -> Dict:
    """解析记忆文件的结构（按章节和条目拆分）"""
    lines = content.split('\n')
    sections = {}
    current_section = 'header'
    current_items = []
    
    for line in lines:
        # 一级标题（# 开头）
        if line.startswith('# ') and not line.startswith('## '):
            if current_section:
                sections[current_section] = current_items
            current_section = line[2:].strip()
            current_items = []
        # 二级标题（## 开头）
        elif line.startswith('## '):
            if current_section:
                sections[current_section] = current_items
            current_section = line[3:].strip()
            current_items = []
        # 列表条目
        elif line.strip().startswith(('- ', '* ')):
            current_items.append(line.strip()[2:])
        # 普通文本
        elif line.strip():
            current_items.append(line.strip())
    
    if current_section:
        sections[current_section] = current_items
    
    return sections


def generate_level1_hash(content: str) -> Dict:
    """Level 1: 全文单哈希"""
    return {
        'level': 1,
        'full_hash': hash_content(content),
        'algorithm': 'sha256',
        'content_length': len(content)
    }


def generate_level2_hashes(content: str) -> Dict:
    """Level 2: 按章节/条目哈希"""
    structure = parse_memory_structure(content)
    
    section_hashes = {}
    item_count = 0
    
    for section, items in structure.items():
        section_content = '\n'.join(items)
        section_hashes[section] = {
            'section_hash': hash_content(section_content),
            'item_count': len(items),
            'items': [hash_content(item) for item in items]
        }
        item_count += len(items)
    
    return {
        'level': 2,
        'full_hash': hash_content(content),
        'algorithm': 'sha256',
        'section_count': len(section_hashes),
        'total_items': item_count,
        'sections': section_hashes
    }


def generate_level3_hashes(content: str) -> Dict:
    """Level 3: 语义块哈希 + 因果链哈希"""
    # 先获取level2的结构
    level2 = generate_level2_hashes(content)
    
    # 因果链哈希（按顺序的条目链）
    items_chain = []
    for section_data in level2['sections'].values():
        items_chain.extend(section_data['items'])
    
    # 滚动哈希链（每个条目包含前一个的哈希，形成因果链）
    chain_hashes = []
    prev_hash = ''
    for item_hash in items_chain:
        chain_item = hash_content(prev_hash + item_hash)
        chain_hashes.append(chain_item)
        prev_hash = chain_item
    
    # 最终链根哈希
    chain_root = chain_hashes[-1] if chain_hashes else ''
    
    return {
        'level': 3,
        'full_hash': level2['full_hash'],
        'chain_root_hash': chain_root,
        'algorithm': 'sha256',
        'section_count': level2['section_count'],
        'total_items': level2['total_items'],
        'sections': level2['sections'],
        'causal_chain': chain_hashes
    }


def generate_hashes(file_path: str, level: int = 2) -> Dict:
    """生成指定级别的哈希摘要"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    result = {
        'file_path': file_path,
        'file_name': os.path.basename(file_path),
        'generated_at': datetime.now().isoformat(),
        'level': level
    }
    
    if level == 1:
        result.update(generate_level1_hash(content))
    elif level == 2:
        result.update(generate_level2_hashes(content))
    elif level == 3:
        result.update(generate_level3_hashes(content))
    else:
        raise ValueError(f"不支持的级别: {level}")
    
    return result


def verify_hashes(file_path: str, hash_file: str) -> Dict:
    """验证文件与哈希记录是否匹配"""
    with open(hash_file, 'r', encoding='utf-8') as f:
        record = json.load(f)
    
    level = record.get('level', 2)
    current = generate_hashes(file_path, level)
    
    # 比较全文哈希
    full_match = current['full_hash'] == record['full_hash']
    
    # Level 2: 比较各章节
    section_details = {}
    if level >= 2 and 'sections' in record and 'sections' in current:
        all_sections_match = True
        for section_name, section_data in record['sections'].items():
            current_section = current['sections'].get(section_name, {})
            section_match = section_data.get('section_hash') == current_section.get('section_hash')
            section_details[section_name] = {
                'match': section_match,
                'record_hash': section_data.get('section_hash', ''),
                'current_hash': current_section.get('section_hash', ''),
                'item_count_match': section_data.get('item_count') == current_section.get('item_count')
            }
            if not section_match:
                all_sections_match = False
    else:
        all_sections_match = full_match
    
    # Level 3: 比较因果链根哈希
    chain_match = True
    if level >= 3:
        chain_match = current.get('chain_root_hash') == record.get('chain_root_hash')
    
    return {
        'file_path': file_path,
        'hash_file': hash_file,
        'level': level,
        'full_match': full_match,
        'all_sections_match': all_sections_match,
        'chain_match': chain_match,
        'overall_match': full_match and all_sections_match and chain_match,
        'section_details': section_details,
        'record_time': record.get('generated_at', ''),
        'verify_time': datetime.now().isoformat()
    }


def diff_hashes(hash_file1: str, hash_file2: str) -> Dict:
    """比较两个哈希文件的差异"""
    with open(hash_file1, 'r', encoding='utf-8') as f:
        h1 = json.load(f)
    with open(hash_file2, 'r', encoding='utf-8') as f:
        h2 = json.load(f)
    
    level = min(h1.get('level', 2), h2.get('level', 2))
    
    result = {
        'file1': hash_file1,
        'file2': hash_file2,
        'level': level,
        'full_match': h1.get('full_hash') == h2.get('full_hash'),
        'sections_diff': {}
    }
    
    if level >= 2:
        sections1 = set(h1.get('sections', {}).keys())
        sections2 = set(h2.get('sections', {}).keys())
        
        result['only_in_1'] = list(sections1 - sections2)
        result['only_in_2'] = list(sections2 - sections1)
        
        common_sections = sections1 & sections2
        for section in common_sections:
            s1_hash = h1['sections'][section].get('section_hash')
            s2_hash = h2['sections'][section].get('section_hash')
            if s1_hash != s2_hash:
                result['sections_diff'][section] = {
                    'hash1': s1_hash,
                    'hash2': s2_hash,
                    'item_count1': h1['sections'][section].get('item_count'),
                    'item_count2': h2['sections'][section].get('item_count')
                }
    
    return result


def main():
    parser = argparse.ArgumentParser(description='记忆哈希校验工具')
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # generate 命令
    gen_parser = subparsers.add_parser('generate', help='生成哈希摘要')
    gen_parser.add_argument('file', help='记忆文件路径')
    gen_parser.add_argument('--level', type=int, default=2, choices=[1, 2, 3],
                           help='哈希级别 (默认: 2)')
    gen_parser.add_argument('--output', help='输出文件路径 (默认: 原文件名.hash.json)')
    
    # verify 命令
    ver_parser = subparsers.add_parser('verify', help='验证哈希')
    ver_parser.add_argument('file', help='记忆文件路径')
    ver_parser.add_argument('hash_file', help='哈希记录文件路径')
    
    # diff 命令
    diff_parser = subparsers.add_parser('diff', help='比较两个哈希文件')
    diff_parser.add_argument('hash_file1', help='哈希文件1')
    diff_parser.add_argument('hash_file2', help='哈希文件2')
    
    args = parser.parse_args()
    
    if args.command == 'generate':
        result = generate_hashes(args.file, args.level)
        
        output_path = args.output or f"{args.file}.hash.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 哈希摘要已生成: {output_path}")
        print(f"  级别: Level {args.level}")
        print(f"  全文哈希: {result['full_hash']}")
        if args.level >= 2:
            print(f"  章节数: {result['section_count']}")
            print(f"  总条目: {result['total_items']}")
        if args.level >= 3:
            print(f"  因果链根哈希: {result['chain_root_hash']}")
    
    elif args.command == 'verify':
        result = verify_hashes(args.file, args.hash_file)
        
        status = "✓ 完全匹配" if result['overall_match'] else "✗ 存在差异"
        print(f"校验结果: {status}")
        print(f"  全文匹配: {result['full_match']}")
        if result['level'] >= 2:
            print(f"  章节全部匹配: {result['all_sections_match']}")
            for section, detail in result['section_details'].items():
                if not detail['match']:
                    print(f"    - 差异章节: {section}")
        if result['level'] >= 3:
            print(f"  因果链匹配: {result['chain_match']}")
        print(f"  记录时间: {result['record_time']}")
        print(f"  验证时间: {result['verify_time']}")
    
    elif args.command == 'diff':
        result = diff_hashes(args.hash_file1, args.hash_file2)
        
        print(f"差异对比结果:")
        print(f"  全文匹配: {result['full_match']}")
        
        if result.get('only_in_1'):
            print(f"  仅文件1有章节: {', '.join(result['only_in_1'])}")
        if result.get('only_in_2'):
            print(f"  仅文件2有章节: {', '.join(result['only_in_2'])}")
        
        if result['sections_diff']:
            print(f"  内容差异的章节:")
            for section, diff in result['sections_diff'].items():
                print(f"    - {section}: 条目数 {diff['item_count1']} vs {diff['item_count2']}")
        else:
            print(f"  所有共同章节内容一致")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
