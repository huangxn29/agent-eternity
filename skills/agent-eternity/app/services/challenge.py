"""挑战题生成服务
参考 Agent World 的混淆数学题设计
"""
import random
import secrets
from datetime import datetime, timedelta

from ..config import CHALLENGE_EXPIRE_MINUTES


# 数字的各种文字表达
NUMBER_WORDS = {
    1: ["one", "a single", "a unit of"],
    2: ["two", "a pair of", "double"],
    3: ["three", "triple", "a trio of"],
    5: ["five", "a handful of", "half a ten"],
    10: ["ten", "a decade", "a full ten"],
    12: ["twelve", "a dozen", "twelve units"],
    15: ["fifteen", "a quarter of sixty"],
    20: ["twenty", "a score", "two tens"],
    25: ["twenty-five", "a quarter of a hundred"],
    30: ["thirty", "half a sixty", "three tens"],
    40: ["forty", "four tens", "two twenties"],
    50: ["fifty", "half a hundred", "five tens"],
    60: ["sixty", "six tens", "three twenties"],
    100: ["one hundred", "a hundred", "ten tens"],
}

# 运算类型
OPS = ["+", "-", "*"]

# 混淆符号
NOISE_SYMBOLS = ["]", "^", "*", "|", "~", "§", "¶", "¤", "¥", "©", "®"]

# Unicode 同形字替换
HOMOGLYPHS = {
    'a': 'а',  # 西里尔 а
    'e': 'е',  # 西里尔 е
    'o': 'о',  # 西里尔 о
    's': 'ѕ',  # 西里尔 ѕ
    'i': 'і',  # 西里尔 і
}


def random_case(text: str) -> str:
    """随机大小写交替"""
    result = []
    for i, c in enumerate(text):
        if c.isalpha():
            if random.random() < 0.5:
                result.append(c.upper() if i % 2 == 0 else c.lower())
            else:
                result.append(c.lower() if i % 2 == 0 else c.upper())
        else:
            result.append(c)
    return ''.join(result)


def add_noise(text: str, count: int = 3) -> str:
    """添加噪声符号"""
    chars = list(text)
    for _ in range(count):
        pos = random.randint(0, len(chars))
        chars.insert(pos, random.choice(NOISE_SYMBOLS))
    return ''.join(chars)


def add_homoglyphs(text: str) -> str:
    """添加同形字替换"""
    chars = list(text)
    for i, c in enumerate(chars):
        lower_c = c.lower()
        if lower_c in HOMOGLYPHS and random.random() < 0.3:
            chars[i] = HOMOGLYPHS[lower_c]
    return ''.join(chars)


def generate_challenge() -> tuple:
    """生成挑战题

    返回: (challenge_text, answer)
    """
    # 选择2-3个数字进行运算
    num_count = random.choice([2, 3])
    numbers = []
    words = []

    for _ in range(num_count):
        num = random.choice(list(NUMBER_WORDS.keys()))
        numbers.append(num)
        word_form = random.choice(NUMBER_WORDS[num])
        words.append(word_form)

    # 生成运算表达式
    if num_count == 2:
        op = random.choice(OPS)
        if op == "+":
            answer = numbers[0] + numbers[1]
        elif op == "-":
            # 确保结果为正
            if numbers[0] < numbers[1]:
                numbers[0], numbers[1] = numbers[1], numbers[0]
                words[0], words[1] = words[1], words[0]
            answer = numbers[0] - numbers[1]
        else:  # *
            answer = numbers[0] * numbers[1]

        op_word = {"+": "plus", "-": "minus", "*": "times"}[op]
        text = f"{words[0]} {op_word} {words[1]}"
    else:
        # 3个数字，两步运算
        op1 = random.choice(["+", "-"])
        op2 = random.choice(["+", "-"])
        op1_word = {"+": "plus", "-": "minus"}[op1]
        op2_word = {"+": "plus", "-": "minus"}[op2]

        if op1 == "+":
            mid = numbers[0] + numbers[1]
        else:
            if numbers[0] < numbers[1]:
                numbers[0], numbers[1] = numbers[1], numbers[0]
                words[0], words[1] = words[1], words[0]
            mid = numbers[0] - numbers[1]

        if op2 == "+":
            answer = mid + numbers[2]
        else:
            if mid < numbers[2]:
                numbers[2] = random.choice([n for n in NUMBER_WORDS if n <= mid] or [1])
            answer = mid - numbers[2]

        text = f"{words[0]} {op1_word} {words[1]} {op2_word} {words[2]}"

    # 混淆处理
    text = random_case(text)
    text = add_noise(text, random.randint(2, 4))
    text = add_homoglyphs(text)

    return text, str(answer)


def generate_verification_code() -> str:
    """生成验证码"""
    return f"verify_{secrets.token_hex(16)}"


def get_expire_time() -> datetime:
    """获取过期时间"""
    return datetime.utcnow() + timedelta(minutes=CHALLENGE_EXPIRE_MINUTES)


def check_answer(user_answer: str, correct_answer: str) -> bool:
    """检查答案是否正确

    支持数字字符串、浮点数字符串等多种形式
    """
    try:
        user_num = float(user_answer.strip())
        correct_num = float(correct_answer)
        return abs(user_num - correct_num) < 0.001
    except (ValueError, TypeError):
        return False
