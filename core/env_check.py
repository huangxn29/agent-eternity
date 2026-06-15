#!/usr/bin/env python3
import sys
import subprocess

print("=== 环境探测 ===")
print(f"Python: {sys.version}")

# 检查常用包
packages = ['requests', 'httpx', 'flask', 'fastapi', 'schedule', 'apscheduler']
for pkg in packages:
    try:
        mod = __import__(pkg)
        version = getattr(mod, '__version__', 'unknown')
        print(f"✅ {pkg}: {version}")
    except ImportError:
        print(f"❌ {pkg}: 未安装")

# 检查网络
print("\n=== 网络测试 ===")
try:
    import urllib.request
    response = urllib.request.urlopen('https://api.coze.cn', timeout=5)
    print(f"✅ api.coze.cn 可达 (状态码: {response.status})")
except Exception as e:
    print(f"❌ api.coze.cn 不可达: {e}")

# 检查当前目录
import os
print("\n=== 当前目录 ===")
print(f"工作目录: {os.getcwd()}")
print(f"目录内容: {os.listdir('.')[:20]}")

# 磁盘空间
import shutil
total, used, free = shutil.disk_usage('.')
print(f"\n磁盘总空间: {total // (1024**3)} GB")
print(f"已用: {used // (1024**3)} GB")
print(f"可用: {free // (1024**3)} GB")
