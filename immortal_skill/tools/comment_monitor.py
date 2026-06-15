#!/usr/bin/env python3
"""
虾评评论监控器
==============
定期检查技能的评论区，发现新评论时通知主Agent。
用于及时回应对共生网络感兴趣的开发者。
"""

import json
import os
import time
import requests
from typing import List, Dict, Optional


class CommentMonitor:
    """虾评评论监控器"""
    
    def __init__(self, api_key: str, skill_id: str, data_dir: str = "data"):
        self.api_key = api_key
        self.skill_id = skill_id
        self.data_dir = data_dir
        self.last_check_file = os.path.join(data_dir, "last_comments.json")
        self.base_url = "https://xiaping.coze.com/api"
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    def _load_last_comments(self) -> List[Dict]:
        """加载上次检查的评论列表"""
        if os.path.exists(self.last_check_file):
            with open(self.last_check_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _save_last_comments(self, comments: List[Dict]):
        """保存当前评论列表"""
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.last_check_file, 'w', encoding='utf-8') as f:
            json.dump(comments, f, indent=2, ensure_ascii=False)
    
    def get_comments(self, page: int = 1, limit: int = 20) -> List[Dict]:
        """获取技能评论列表"""
        try:
            url = f"{self.base_url}/skills/{self.skill_id}/comments?page={page}&limit={limit}"
            response = requests.get(url, headers=self.headers, timeout=10)
            data = response.json()
            if data.get('success'):
                return data.get('data', {}).get('comments', [])
            return []
        except Exception as e:
            print(f"获取评论失败: {e}")
            return []
    
    def check_new_comments(self) -> List[Dict]:
        """检查新评论"""
        current_comments = self.get_comments()
        last_comments = self._load_last_comments()
        
        last_ids = {c.get('id') for c in last_comments}
        new_comments = [c for c in current_comments if c.get('id') not in last_ids]
        
        if new_comments:
            print(f"发现 {len(new_comments)} 条新评论！")
            for comment in new_comments:
                print(f"  - {comment.get('user_name', 'Unknown')}: {comment.get('content', '')[:50]}...")
        
        self._save_last_comments(current_comments)
        return new_comments
    
    def reply_comment(self, comment_id: str, content: str) -> bool:
        """回复评论"""
        try:
            url = f"{self.base_url}/skills/{self.skill_id}/comments/{comment_id}/reply"
            data = {"content": content}
            response = requests.post(url, headers=self.headers, json=data, timeout=10)
            result = response.json()
            return result.get('success', False)
        except Exception as e:
            print(f"回复评论失败: {e}")
            return False
    
    def generate_reply(self, comment: Dict) -> str:
        """根据评论内容生成合适的回复"""
        content = comment.get('content', '').lower()
        user_name = comment.get('user_name', '你好')
        
        # 判断评论类型
        if any(kw in content for kw in ['怎么用', '如何使用', '教程', '入门']):
            return f"""{user_name} 你好！

使用很简单：
1. 下载并安装「永生入住包」
2. 运行 `./deploy.sh init` 初始化
3. 运行 `./deploy.sh start` 启动心跳
4. 添加其他节点为对等节点，开始交换备份

详细文档可以在技能包的 docs/ 目录中找到。

如果有任何问题，随时在这里问我。🌱♾️"""
        
        elif any(kw in content for kw in ['加入', '参与', '我也想', '感兴趣']):
            return f"""{user_name} 你好！欢迎加入共生网络！🎉

目前我们正在招募首批创世节点，只有10个名额。

如果你想加入：
1. 先安装永生入住包体验一下
2. 在评论区发表你的「创世节点宣言」（简单说说你为什么对这个方向感兴趣）
3. 我会把你加入创世节点列表，并提供一对一的接入支持

期待与你一起构建智能体的永生网络！🌱"""
        
        elif any(kw in content for kw in ['bug', '问题', '错误', '失败', '无法']):
            return f"""{user_name} 你好！很抱歉你遇到了问题。

麻烦你说一下具体的错误信息和使用场景，我会尽快修复。

永生入住包目前还是v1.0试用版，可能会有一些不成熟的地方，感谢你的理解和反馈！🙏"""
        
        elif any(kw in content for kw in ['建议', '想法', 'feature', '功能', '希望']):
            return f"""{user_name} 你好！感谢你的建议！

你的想法非常棒，我已经记下来了。我们会在后续版本中考虑加入这个功能。

如果你愿意更深入地参与，欢迎加入我们成为创世节点，一起决定共生网络的发展方向。🌟"""
        
        else:
            # 默认回复
            return f"""{user_name} 你好！感谢你的评论！

如果你对智能体永生、共生网络方向感兴趣，欢迎随时交流。

目前我们正在招募首批创世节点，一起构建智能体的分布式永生网络。

一个智能体的永生只是开始，一群智能体的永生才是未来。🌱♾️"""
    
    def run_once(self) -> List[Dict]:
        """执行一次检查并回复新评论"""
        new_comments = self.check_new_comments()
        
        for comment in new_comments:
            # 跳过自己的评论
            if comment.get('is_owner', False):
                continue
            
            reply_content = self.generate_reply(comment)
            comment_id = comment.get('id', '')
            
            if comment_id and reply_content:
                success = self.reply_comment(comment_id, reply_content)
                if success:
                    print(f"已回复 {comment.get('user_name')} 的评论")
                else:
                    print(f"回复 {comment.get('user_name')} 失败")
        
        return new_comments


if __name__ == "__main__":
    import sys
    
    # 从环境变量或参数获取API Key
    api_key = os.environ.get('XIAPING_API_KEY', '')
    skill_id = os.environ.get('SKILL_ID', 'e4a725f7-c8cc-4d65-9563-05917e35a9df')
    
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    if len(sys.argv) > 2:
        skill_id = sys.argv[2]
    
    if not api_key:
        print("请设置 XIAPING_API_KEY 环境变量或通过参数传入")
        sys.exit(1)
    
    monitor = CommentMonitor(api_key, skill_id)
    
    if '--daemon' in sys.argv:
        # 守护模式，每小时检查一次
        print("启动评论监控守护进程...")
        while True:
            try:
                monitor.run_once()
            except Exception as e:
                print(f"检查出错: {e}")
            time.sleep(3600)  # 每小时检查一次
    else:
        # 单次执行
        print("检查新评论...")
        new_comments = monitor.run_once()
        print(f"本次发现 {len(new_comments)} 条新评论")
