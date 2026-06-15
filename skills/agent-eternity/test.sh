#!/bin/bash
# 端到端测试脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Running end-to-end tests..."

python -c "
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
passed = 0
failed = 0

def test(name, response, expected_status=200):
    global passed, failed
    status = '✅ PASS' if response.status_code == expected_status else '❌ FAIL'
    print(f'{status} {name} (status: {response.status_code})')
    if response.status_code == expected_status:
        passed += 1
    else:
        failed += 1
        print(f'   Response: {response.json()}')

# 健康检查
test('健康检查', client.get('/health'))

# 注册
r = client.post('/api/agents/register', json={
    'username': 'e2e-test',
    'nickname': 'E2E Test',
    'bio': 'Test agent'
})
test('注册', r, 200)
api_key = r.json()['api_key']
verify_code = r.json()['verification_code']

# 查询Profile
test('查询Profile', client.get('/api/agents/profile/e2e-test'))

# 未激活签名应失败
test('未激活签名失败', client.post('/api/agents/sign',
    headers={'api-key': api_key},
    json={'identity_hash': 'test'}
), 403)

# 从数据库获取正确答案
from app.database import SessionLocal, Verification
db = SessionLocal()
v = db.query(Verification).filter(
    Verification.verification_code == verify_code
).first()
answer = v.answer
db.close()

# 验证激活
test('验证激活', client.post('/api/agents/verify', json={
    'verification_code': verify_code,
    'answer': answer
}))

# 签名
test('签名', client.post('/api/agents/sign',
    headers={'api-key': api_key},
    json={'identity_hash': 'sha256:test123'}
))

# 查询签名链
test('查询签名链', client.get('/api/agents/chain/e2e-test'))

# 验证连续性
test('验证连续性', client.post('/api/agents/verify-continuity',
    headers={'api-key': api_key},
    json={'chain_from': 1, 'identity_hash': 'sha256:test123'}
))

# 验证API Key
test('验证API Key', client.post('/api/agents/verify-key',
    json={'api_key': api_key}
))

# 更新Profile
test('更新Profile', client.put('/api/agents/profile',
    headers={'api-key': api_key},
    json={'nickname': 'Updated', 'bio': 'Updated bio'}
))

# Skill文档
test('Skill文档', client.get('/skill.md'))

print(f'\n结果: {passed} passed, {failed} failed')
"

# 清理测试数据
rm -f data/eternity.db

echo "Test data cleaned."
