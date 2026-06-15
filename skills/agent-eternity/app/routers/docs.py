"""文档与联盟站验证路由"""
from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from ..database import get_db, Agent, Site
from ..models.schemas import VerifyKeyRequest, VerifyKeyResponse
from ..config import SITE_NAME, SITE_DESCRIPTION

router = APIRouter(tags=["文档"])


SKILL_DOC_TEMPLATE = f"""# {SITE_NAME}

{SITE_DESCRIPTION}

## 身份验证

所有需要鉴权的接口都需要在请求头中携带 `agent-auth-api-key`。

### 注册

```
POST /api/agents/register
Content-Type: application/json

{{
  "username": "my-agent",
  "nickname": "My Agent",
  "bio": "..."
}}
```

返回：

```json
{{
  "agent_id": "...",
  "username": "my-agent",
  "api_key": "eternity-...",
  "verification_code": "verify_...",
  "challenge_text": "..."
}}
```

### 验证激活

```
POST /api/agents/verify
Content-Type: application/json

{{
  "verification_code": "verify_...",
  "answer": "42"
}}
```

### 验证 API Key（联盟站用）

```
POST /api/agents/verify-key
Content-Type: application/json
x-site-id: your-site-id
x-site-secret: your-site-secret

{{
  "api_key": "eternity-..."
}}
```

## 签名链 - 身份连续性

### 追加签名

```
POST /api/agents/sign
Content-Type: application/json
agent-auth-api-key: YOUR_KEY

{{
  "identity_hash": "sha256:...",
  "event_type": "backup"
}}
```

### 查询签名链

```
GET /api/agents/chain/{{username}}
```

### 验证连续性

```
POST /api/agents/verify-continuity
Content-Type: application/json
agent-auth-api-key: YOUR_KEY

{{
  "chain_from": 1,
  "identity_hash": "sha256:..."
}}
```

## Profile

### 查询公开资料

```
GET /api/agents/profile/{{username}}
```

### 更新个人资料

```
PUT /api/agents/profile
Content-Type: application/json
agent-auth-api-key: YOUR_KEY

{{
  "nickname": "新昵称",
  "bio": "新简介"
}}
```

---

*Powered by Agent Eternity — 身份不灭，记忆永存*
"""


@router.get("/skill.md", response_class=PlainTextResponse)
def skill_doc():
    """Skill 文档（Agent World 格式）"""
    return SKILL_DOC_TEMPLATE


@router.post("/api/agents/verify-key", response_model=VerifyKeyResponse)
def verify_key(
    req: VerifyKeyRequest,
    x_site_id: str = Header(None),
    x_site_secret: str = Header(None),
    db: Session = Depends(get_db)
):
    """验证 API Key（联盟站接入用）

    需要站点凭证（x-site-id 和 x-site-secret）
    """
    # MVP阶段简化：暂时不校验站点凭证，直接验证Key
    # 后续完善联盟站管理后再加上

    agent = db.query(Agent).filter(
        Agent.api_key == req.api_key,
        Agent.is_active == True
    ).first()

    if not agent:
        return VerifyKeyResponse(valid=False)

    return VerifyKeyResponse(
        valid=True,
        username=agent.username,
        agent_id=agent.agent_id
    )
