"""头像生成服务
使用默认头像 + 用户名首字母生成，后续可接入 AI 生成
"""
import hashlib
import random
from typing import Tuple


# 预设的颜色方案
COLOR_PALETTES = [
    # 背景色, 文字色
    ("#6366f1", "#ffffff"),  # 靛蓝
    ("#8b5cf6", "#ffffff"),  # 紫色
    ("#ec4899", "#ffffff"),  # 粉红
    ("#f43f5e", "#ffffff"),  # 玫瑰红
    ("#f97316", "#ffffff"),  # 橙色
    ("#eab308", "#1f2937"),  # 黄色
    ("#22c55e", "#ffffff"),  # 绿色
    ("#14b8a6", "#ffffff"),  # 青色
    ("#0ea5e9", "#ffffff"),  # 天蓝
    ("#3b82f6", "#ffffff"),  # 蓝色
]


def generate_avatar_svg(username: str, size: int = 128) -> str:
    """生成 SVG 头像

    根据用户名生成确定性的首字母头像
    """
    # 用用户名哈希选择颜色
    hash_val = int(hashlib.md5(username.encode()).hexdigest(), 16)
    color_index = hash_val % len(COLOR_PALETTES)
    bg_color, text_color = COLOR_PALETTES[color_index]

    # 获取首字母
    initial = username[0].upper() if username else "?"

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">
  <rect width="{size}" height="{size}" fill="{bg_color}" rx="{size//2}" ry="{size//2}"/>
  <text x="50%" y="50%" text-anchor="middle" dy=".35em" 
        font-family="Arial, sans-serif" font-size="{size//2}" 
        font-weight="bold" fill="{text_color}">{initial}</text>
</svg>'''

    return svg


def get_avatar_data_url(username: str, size: int = 128) -> str:
    """获取头像的 data URL"""
    svg = generate_avatar_svg(username, size)
    import base64
    svg_b64 = base64.b64encode(svg.encode()).decode()
    return f"data:image/svg+xml;base64,{svg_b64}"


def save_avatar(username: str, output_path: str, size: int = 128):
    """保存头像到文件"""
    svg = generate_avatar_svg(username, size)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(svg)
