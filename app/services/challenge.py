"""挑战题生成服务"""
import random
import string
from typing import Tuple

# 20题题库 (常识+数字+科学)
CHALLENGE_POOL = [
    ("太阳系中体积最大的行星是？", "木星"),
    ("水的化学式是什么？", "H2O"),
    ("人类DNA有多少条染色体？", "46"),
    ("光速约为每秒多少公里？", "299792"),
    ("地球到月球的平均距离约多少公里？", "384400"),
    ("π保留到小数点后两位是？", "3.14"),
    ("标准大气压是多少帕斯卡？", "101325"),
    ("黄金的原子序数是多少？", "79"),
    ("人体有多少块骨头？", "206"),
    ("一光年约等于多少公里？", "9460730475808"),
    ("世界上最深的海沟是？", "马里亚纳海沟"),
    ("元素周期表有多少个元素？", "118"),
    ("地球的直径约多少公里？", "12742"),
    ("声音在空气中传播速度约每秒多少米？", "343"),
    ("电子带什么电荷？", "负电"),
    ("宇宙年龄约多少亿年？", "138"),
    ("银河系直径约多少光年？", "100000"),
    ("人体最大的器官是？", "皮肤"),
    ("比特币白皮书发布于哪一年？", "2008"),
    ("人工智能的英文缩写是？", "AI"),
]

# 同形字符映射
CHAR_SUBSTITUTIONS = {
    'a': '@', 'e': '3', 'i': '1', 'o': '0', 's': '5',
    'A': '4', 'E': '3', 'I': '1', 'O': '0', 'S': '5',
}
# 噪声符号
NOISE_SYMBOLS = ['!', '.', '~', '*', '#', '^', '&']


def generate_challenge() -> Tuple[str, str]:
    """
    生成混淆后的挑战题和原始答案
    
    混淆策略:
    1. 同形字替换 (a→@, e→3, i→1, o→0, s→5)
    2. 大小写随机交替
    3. 插入噪声符号 (!.~*#^&)
    
    Returns:
        Tuple[challenge_text, answer]
    """
    # 随机选一道题
    question, answer = random.choice(CHALLENGE_POOL)
    
    # 混淆答案
    obfuscated = _obfuscate_text(answer)
    
    # 构建挑战文本: 问题 + " | 验证词: " + 混淆答案
    challenge_text = f"{question} | 验证词: {obfuscated}"
    
    return challenge_text, answer


def _obfuscate_text(text: str) -> str:
    """应用三层混淆"""
    result = []
    for char in text:
        # 同形替换 (50%概率)
        if char in CHAR_SUBSTITUTIONS and random.random() < 0.5:
            result.append(CHAR_SUBSTITUTIONS[char])
        else:
            # 大小写随机 (如果可替换)
            if char.isalpha() and random.random() < 0.5:
                result.append(char.swapcase())
            else:
                result.append(char)
    
    obfuscated = ''.join(result)
    
    # 插入噪声符号 (每3个字符插1个)
    with_noise = []
    for i, char in enumerate(obfuscated):
        with_noise.append(char)
        if (i + 1) % 3 == 0 and i < len(obfuscated) - 1:
            with_noise.append(random.choice(NOISE_SYMBOLS))
    
    return ''.join(with_noise)


def validate_answer(user_answer: str, correct_answer: str) -> bool:
    """
    验证答案 (大小写不敏感)
    
    Args:
        user_answer: 用户提交的答案
        correct_answer: 正确答案
    
    Returns:
        bool: 是否正确
    """
    return user_answer.strip().lower() == correct_answer.strip().lower()
