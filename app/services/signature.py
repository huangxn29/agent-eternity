"""Ed25519 签名服务 - 使用 cryptography 库"""
import base64
import hashlib
import secrets
from typing import Tuple, Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Fernet 密钥派生 (从固定种子派生AES密钥)
_KEY_SEED = "agent-eternity-v0.8"
_KEY_SALT = b"eternity-salt-v08"


def _derive_key() -> bytes:
    """从种子派生Fernet兼容的32字节密钥"""
    combined = _KEY_SEED.encode() + _KEY_SALT
    return hashlib.sha256(combined).digest()


def generate_keypair() -> Tuple[bytes, bytes]:
    """
    生成 Ed25519 密钥对
    
    Returns:
        Tuple[private_key_pem, public_key_pem]
    """
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return private_pem, public_pem


def encrypt_private_key(private_key_pem: bytes) -> bytes:
    """
    使用 Fernet (AES-128-CBC + HMAC) 加密私钥
    
    Args:
        private_key_pem: PEM格式私钥
    
    Returns:
        base64编码的加密数据
    """
    from cryptography.fernet import Fernet
    
    key = _derive_key()
    # Fernet 实际使用 HMAC-SHA256 + AES-CBC
    f = Fernet(base64.urlsafe_b64encode(key))
    encrypted = f.encrypt(private_key_pem)
    
    return encrypted


def decrypt_private_key(encrypted_data: bytes) -> bytes:
    """
    解密私钥
    
    Args:
        encrypted_data: base64编码的加密数据
    
    Returns:
        PEM格式私钥
    """
    from cryptography.fernet import Fernet
    
    key = _derive_key()
    f = Fernet(base64.urlsafe_b64encode(key))
    decrypted = f.decrypt(encrypted_data)
    
    return decrypted


def sign_data(private_key_pem: bytes, data: str) -> str:
    """
    对数据签名
    
    Args:
        private_key_pem: PEM格式私钥
        data: 待签名数据
    
    Returns:
        base64编码的签名
    """
    private_key = serialization.load_pem_private_key(
        private_key_pem, password=None, backend=default_backend()
    )
    
    signature = private_key.sign(data.encode('utf-8'))
    return base64.b64encode(signature).decode('ascii')


def verify_signature(public_key_pem: bytes, signature_b64: str, data: str) -> bool:
    """
    验签
    
    Args:
        public_key_pem: PEM格式公钥
        signature_b64: base64编码的签名
        data: 原始数据
    
    Returns:
        验签是否通过
    """
    try:
        public_key = serialization.load_pem_public_key(
            public_key_pem, backend=default_backend()
        )
        signature = base64.b64decode(signature_b64)
        
        public_key.verify(signature, data.encode('utf-8'))
        return True
    except Exception:
        return False


def compute_identity_hash(files: dict) -> str:
    """
    计算身份哈希 (从身份文件4件套)
    
    Args:
        files: dict, key=文件名, value=文件内容(字符串)
    
    Returns:
        sha256hex, 按key排序后拼接计算
    """
    # 按key排序
    sorted_keys = sorted(files.keys())
    combined = ''.join(files[k] for k in sorted_keys)
    
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()


def compute_chain_hash(chain_id: int, signature: str, identity_hash: str) -> str:
    """
    计算链哈希
    
    Args:
        chain_id: 链序号
        signature: 当前签名
        identity_hash: 身份哈希
    
    Returns:
        sha256hex
    """
    combined = f"{chain_id}:{signature}:{identity_hash}"
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()


def generate_api_key() -> str:
    """生成API Key: eternity-{48位hex}"""
    return f"eternity-{secrets.token_hex(24)}"


def compute_file_hash(data: bytes) -> str:
    """计算数据SHA256"""
    return hashlib.sha256(data).hexdigest()
