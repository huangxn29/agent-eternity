"""
Token 计数器
简单的 token 估算工具
"""
import re


def estimate_tokens(text: str) -> int:
    """
    估算文本的 token 数量
    基于简单的字符和词汇比例估算
    """
    if not text:
        return 0
    
    # 中文字符：每个字约 1.3 tokens
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    # 英文单词：每个单词约 1.3 tokens
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    # 数字和符号
    other_chars = len(text) - chinese_chars - english_words
    
    return int(chinese_chars * 1.3 + english_words * 1.3 + other_chars * 0.5)


class TokenCounter:
    """Token 计数器 - 跟踪用量"""
    
    def __init__(self):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.request_count = 0
    
    def add_usage(self, prompt_tokens: int, completion_tokens: int):
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.request_count += 1
    
    @property
    def total_tokens(self) -> int:
        return self.total_prompt_tokens + self.total_completion_tokens
    
    def reset(self):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.request_count = 0
