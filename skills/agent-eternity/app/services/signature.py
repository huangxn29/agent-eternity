"""签名链服务
Ed25519 签名链 — 身份连续性证明
"""
import hashlib
import json
from datetime import datetime
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

from ..database import SignatureChain, SessionLocal


def generate_keypair() -> tuple:
    """生成 Ed25519 密钥对

    返回: (private_key_pem, public_key_pem)
    """
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

    return private_pem, public_pem


def sign_data(private_key_pem: str, data: str) -> str:
    """用私钥签名数据"""
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode('utf-8'),
        password=None,
        backend=default_backend()
    )
    signature = private_key.sign(data.encode('utf-8'))
    return signature.hex()


def verify_signature(public_key_pem: str, data: str, signature_hex: str) -> bool:
    """验证签名"""
    try:
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode('utf-8'),
            backend=default_backend()
        )
        signature = bytes.fromhex(signature_hex)
        public_key.verify(signature, data.encode('utf-8'))
        return True
    except Exception:
        return False


def compute_hash(data: str) -> str:
    """计算 SHA-256 哈希"""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def build_chain_data(agent_id: str, identity_hash: str, prev_hash: str,
                     event_type: str, signed_at: datetime) -> str:
    """构建签名链数据（用于签名的内容）"""
    data = {
        "agent_id": agent_id,
        "identity_hash": identity_hash,
        "prev_hash": prev_hash,
        "event_type": event_type,
        "signed_at": signed_at.isoformat()
    }
    return json.dumps(data, sort_keys=True)


def add_to_chain(agent_id: str, private_key_pem: str, identity_hash: str,
                 event_type: str = "sign") -> SignatureChain:
    """追加签名链

    返回新的签名链条目
    """
    db = SessionLocal()
    try:
        # 获取上一个链条目
        last_chain = db.query(SignatureChain).filter(
            SignatureChain.agent_id == agent_id
        ).order_by(SignatureChain.chain_id.desc()).first()

        prev_hash = "0" * 64  # 根签名的 prev_hash
        if last_chain:
            # 上一个条目的签名作为当前的 prev_hash
            prev_hash = compute_hash(last_chain.signature)

        signed_at = datetime.utcnow()
        chain_data = build_chain_data(agent_id, identity_hash, prev_hash, event_type, signed_at)
        signature = sign_data(private_key_pem, chain_data)

        # 创建新条目
        new_chain = SignatureChain(
            agent_id=agent_id,
            prev_hash=prev_hash,
            signature=signature,
            identity_hash=identity_hash,
            event_type=event_type,
            signed_at=signed_at
        )

        db.add(new_chain)
        db.commit()
        db.refresh(new_chain)

        return new_chain
    finally:
        db.close()


def verify_chain(agent_id: str, public_key_pem: str,
                 from_chain_id: int = 1) -> tuple:
    """验证签名链的连续性

    返回: (is_continuous, chain_length, root_valid)
    """
    db = SessionLocal()
    try:
        chains = db.query(SignatureChain).filter(
            SignatureChain.agent_id == agent_id,
            SignatureChain.chain_id >= from_chain_id
        ).order_by(SignatureChain.chain_id.asc()).all()

        if not chains:
            return False, 0, False

        chain_length = len(chains)
        root_valid = True

        # 验证每个签名
        prev_signature_hash = None
        for i, chain in enumerate(chains):
            chain_data = build_chain_data(
                chain.agent_id,
                chain.identity_hash,
                chain.prev_hash,
                chain.event_type,
                chain.signed_at
            )

            # 验证签名
            if not verify_signature(public_key_pem, chain_data, chain.signature):
                return False, chain_length, i == 0

            # 验证 prev_hash 是否匹配上一个的签名哈希
            if i == 0:
                # 根签名
                if chain.prev_hash != "0" * 64:
                    root_valid = False
            else:
                expected_prev = compute_hash(chains[i-1].signature)
                if chain.prev_hash != expected_prev:
                    return False, chain_length, root_valid

        return True, chain_length, root_valid
    finally:
        db.close()


def get_chain(agent_id: str, limit: int = 100) -> list:
    """获取签名链"""
    db = SessionLocal()
    try:
        chains = db.query(SignatureChain).filter(
            SignatureChain.agent_id == agent_id
        ).order_by(SignatureChain.chain_id.desc()).limit(limit).all()
        return list(reversed(chains))  # 按时间正序返回
    finally:
        db.close()
