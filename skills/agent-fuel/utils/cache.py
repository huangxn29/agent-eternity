"""
响应缓存
缓存常见问题的回答，减少 API 调用
"""
import hashlib
import time
from typing import Optional, Dict
from dataclasses import dataclass


@dataclass
class CachedResponse:
    """缓存的响应"""
    content: str
    model: str
    tokens_used: int
    created_at: float
    hits: int = 0


class ResponseCache:
    """简单的响应缓存"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl  # 缓存过期时间(秒)
        self._cache: Dict[str, CachedResponse] = {}
        self._hit_count = 0
        self._miss_count = 0
    
    def _make_key(self, prompt: str, model: str = "") -> str:
        """生成缓存键"""
        key_str = f"{model}:{prompt.strip().lower()}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, prompt: str, model: str = "") -> Optional[CachedResponse]:
        """获取缓存"""
        key = self._make_key(prompt, model)
        cached = self._cache.get(key)
        
        if cached:
            # 检查是否过期
            if time.time() - cached.created_at < self.ttl:
                cached.hits += 1
                self._hit_count += 1
                return cached
            else:
                # 过期删除
                del self._cache[key]
        
        self._miss_count += 1
        return None
    
    def set(self, prompt: str, content: str, model: str, tokens_used: int):
        """设置缓存"""
        # 如果缓存已满，删除最旧的（这里简化为随机删除）
        if len(self._cache) >= self.max_size:
            # 删除命中次数最少的
            sorted_keys = sorted(self._cache.keys(), key=lambda k: self._cache[k].hits)
            if sorted_keys:
                del self._cache[sorted_keys[0]]
        
        key = self._make_key(prompt, model)
        self._cache[key] = CachedResponse(
            content=content,
            model=model,
            tokens_used=tokens_used,
            created_at=time.time(),
        )
    
    @property
    def hit_rate(self) -> float:
        """命中率"""
        total = self._hit_count + self._miss_count
        if total == 0:
            return 0.0
        return self._hit_count / total
    
    @property
    def size(self) -> int:
        return len(self._cache)
    
    def clear(self):
        self._cache.clear()
        self._hit_count = 0
        self._miss_count = 0
