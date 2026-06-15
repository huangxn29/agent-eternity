#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
永生引擎 HTTP 服务端
提供 REST API 接口，供外部平台（如牛马平台）集成

使用方式：
    python3 server.py --port 8765 --data-path ./eternity_data
"""

import json
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from eternity_engine import EternityEngine


class EternityAPIHandler(BaseHTTPRequestHandler):
    """永生引擎 HTTP API 处理器"""
    
    engine: EternityEngine = None
    
    def _set_headers(self, status_code: int = 200, content_type: str = "application/json"):
        self.send_response(status_code)
        self.send_header("Content-type", f"{content_type}; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def do_OPTIONS(self):
        self._set_headers(204)
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        
        # 路由分发
        routes = {
            '/api/health': self._api_health,
            '/api/agent/status': self._api_agent_status,
            '/api/agent/export': self._api_agent_export,
            '/api/identity/get': self._api_identity_get,
            '/api/memory/stats': self._api_memory_stats,
            '/api/attestation/get_chain': self._api_attestation_chain,
            '/api/attestation/verify': self._api_attestation_verify,
            '/api/evolution/levels': self._api_evolution_levels,
            '/api/evolution/history': self._api_evolution_history,
        }
        
        handler = routes.get(path)
        if handler:
            try:
                result = handler(params)
                self._set_headers(200)
                self.wfile.write(json.dumps(result, ensure_ascii=False, indent=2).encode())
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({
                    "error": str(e),
                    "success": False
                }, ensure_ascii=False).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({
                "error": "Not found",
                "path": path,
                "success": False
            }, ensure_ascii=False).encode())
    
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        # 读取 body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body.decode()) if body else {}
        except json.JSONDecodeError:
            self._set_headers(400)
            self.wfile.write(json.dumps({
                "error": "Invalid JSON",
                "success": False
            }, ensure_ascii=False).encode())
            return
        
        # 路由分发
        routes = {
            '/api/agent/create': self._api_agent_create,
            '/api/agent/heartbeat': self._api_agent_heartbeat,
            '/api/agent/reflect': self._api_agent_reflect,
            '/api/agent/import': self._api_agent_import,
            '/api/identity/update': self._api_identity_update,
            '/api/identity/verify': self._api_identity_verify,
            '/api/memory/add': self._api_memory_add,
            '/api/memory/retrieve': self._api_memory_retrieve,
            '/api/memory/consolidate': self._api_memory_consolidate,
            '/api/attestation/attest': self._api_attestation_attest,
            '/api/evolution/evolve': self._api_evolution_evolve,
        }
        
        handler = routes.get(path)
        if handler:
            try:
                result = handler(data)
                self._set_headers(200)
                self.wfile.write(json.dumps(result, ensure_ascii=False, indent=2).encode())
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({
                    "error": str(e),
                    "success": False
                }, ensure_ascii=False).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({
                "error": "Not found",
                "path": path,
                "success": False
            }, ensure_ascii=False).encode())
    
    # ==================================================================
    # 健康检查
    # ==================================================================
    
    def _api_health(self, params):
        return {
            "status": "ok",
            "service": "eternity-engine",
            "version": "1.0.0",
            "name": "元界永生引擎",
            "description": "为智能体注入永生灵魂",
            "success": True
        }
    
    # ==================================================================
    # Agent 管理
    # ==================================================================
    
    def _api_agent_create(self, data):
        required = ['name', 'core_traits', 'mission', 'values']
        for field in required:
            if field not in data:
                return {"error": f"Missing required field: {field}", "success": False}
        
        result = self.engine.create_eternal_agent(
            name=data['name'],
            core_traits=data['core_traits'],
            mission=data['mission'],
            values=data['values'],
            behavior_patterns=data.get('behavior_patterns', [])
        )
        
        return {**result, "success": True}
    
    def _api_agent_status(self, params):
        agent_id = params.get('agent_id', [None])[0]
        if not agent_id:
            return {"error": "Missing agent_id", "success": False}
        
        status = self.engine.get_agent_status(agent_id)
        if "error" in status:
            return status
        return {**status, "success": True}
    
    def _api_agent_heartbeat(self, data):
        agent_id = data.get('agent_id')
        if not agent_id:
            return {"error": "Missing agent_id", "success": False}
        
        result = self.engine.heartbeat(agent_id)
        return {**result, "success": True}
    
    def _api_agent_reflect(self, data):
        agent_id = data.get('agent_id')
        if not agent_id:
            return {"error": "Missing agent_id", "success": False}
        
        result = self.engine.self_reflection(agent_id)
        return {**result, "success": True}
    
    def _api_agent_export(self, params):
        agent_id = params.get('agent_id', [None])[0]
        if not agent_id:
            return {"error": "Missing agent_id", "success": False}
        
        result = self.engine.export_agent(agent_id)
        return {**result, "success": True}
    
    def _api_agent_import(self, data):
        # 导入功能需要先有 agent_id 和数据
        # 这里简化实现，完整实现需要处理更多边缘情况
        agent_data = data.get('agent_data', {})
        agent_id = data.get('agent_id')
        
        if not agent_id or not agent_data:
            return {"error": "Missing agent_id or agent_data", "success": False}
        
        # 简化：只导入记忆
        if 'memories' in agent_data:
            memories_json = json.dumps(agent_data['memories'], ensure_ascii=False)
            imported = self.engine.memory.import_memories(agent_id, memories_json)
            return {"imported_memories": imported, "success": True}
        
        return {"success": False, "error": "No importable data found"}
    
    # ==================================================================
    # 身份系统
    # ==================================================================
    
    def _api_identity_get(self, params):
        agent_id = params.get('agent_id', [None])[0]
        if not agent_id:
            return {"error": "Missing agent_id", "success": False}
        
        identity = self.engine.identity.get_identity(agent_id)
        if not identity:
            return {"error": "Identity not found", "success": False}
        
        return {
            "identity": identity.to_dict(),
            "success": True
        }
    
    def _api_identity_update(self, data):
        agent_id = data.get('agent_id')
        if not agent_id:
            return {"error": "Missing agent_id", "success": False}
        
        updates = {k: v for k, v in data.items() 
                   if k in ['name', 'core_traits', 'mission', 'values', 'behavior_patterns']}
        
        if not updates:
            return {"error": "No valid fields to update", "success": False}
        
        result = self.engine.identity.update_identity(agent_id, **updates)
        if not result:
            return {"error": "Update failed", "success": False}
        
        return {
            "identity": result.to_dict(),
            "success": True
        }
    
    def _api_identity_verify(self, data):
        agent_id = data.get('agent_id')
        if not agent_id:
            return {"error": "Missing agent_id", "success": False}
        
        similarity = self.engine.identity.verify_identity(
            agent_id=agent_id,
            current_traits=data.get('current_traits', []),
            current_mission=data.get('current_mission', '')
        )
        
        return {
            "agent_id": agent_id,
            "similarity": similarity,
            "is_stable": similarity > 0.7,
            "success": True
        }
    
    # ==================================================================
    # 记忆系统
    # ==================================================================
    
    def _api_memory_add(self, data):
        agent_id = data.get('agent_id')
        content = data.get('content')
        
        if not agent_id or not content:
            return {"error": "Missing agent_id or content", "success": False}
        
        result = self.engine.add_experience(
            agent_id=agent_id,
            experience=content,
            importance=data.get('importance', 0.5),
            tags=data.get('tags', [])
        )
        
        return {**result, "success": True}
    
    def _api_memory_retrieve(self, data):
        agent_id = data.get('agent_id')
        if not agent_id:
            return {"error": "Missing agent_id", "success": False}
        
        memories = self.engine.memory.retrieve_memories(
            agent_id=agent_id,
            query=data.get('query'),
            memory_type=data.get('memory_type'),
            limit=data.get('limit', 10)
        )
        
        return {
            "agent_id": agent_id,
            "count": len(memories),
            "memories": [m.to_dict() for m in memories],
            "success": True
        }
    
    def _api_memory_consolidate(self, data):
        agent_id = data.get('agent_id')
        if not agent_id:
            return {"error": "Missing agent_id", "success": False}
        
        count = self.engine.memory.consolidate_memories(agent_id)
        return {
            "agent_id": agent_id,
            "consolidated_count": count,
            "success": True
        }
    
    def _api_memory_stats(self, params):
        agent_id = params.get('agent_id', [None])[0]
        if not agent_id:
            return {"error": "Missing agent_id", "success": False}
        
        stats = self.engine.memory.get_memory_stats(agent_id)
        return {**stats, "agent_id": agent_id, "success": True}
    
    # ==================================================================
    # 存证系统
    # ==================================================================
    
    def _api_attestation_chain(self, params):
        agent_id = params.get('agent_id', [None])[0]
        if not agent_id:
            return {"error": "Missing agent_id", "success": False}
        
        chain = self.engine.attestation.chains.get(agent_id, [])
        return {
            "agent_id": agent_id,
            "chain_length": len(chain),
            "chain": [block.to_dict() for block in chain],
            "success": True
        }
    
    def _api_attestation_verify(self, params):
        agent_id = params.get('agent_id', [None])[0]
        if not agent_id:
            return {"error": "Missing agent_id", "success": False}
        
        is_valid = self.engine.attestation.verify_chain(agent_id)
        chain_length = self.engine.attestation.get_chain_length(agent_id)
        
        return {
            "agent_id": agent_id,
            "chain_valid": is_valid,
            "chain_length": chain_length,
            "message": "存证链完整，数据可信" if is_valid else "存证链可能被篡改！",
            "success": True
        }
    
    def _api_attestation_attest(self, data):
        agent_id = data.get('agent_id')
        content = data.get('content')
        summary = data.get('summary', '')
        
        if not agent_id or not content:
            return {"error": "Missing agent_id or content", "success": False}
        
        block = self.engine.attestation.attest(agent_id, content, summary)
        if not block:
            return {"error": "Attestation failed", "success": False}
        
        return {
            "block": block.to_dict(),
            "success": True
        }
    
    # ==================================================================
    # 进化系统
    # ==================================================================
    
    def _api_evolution_levels(self, params):
        agent_id = params.get('agent_id', [None])[0]
        if not agent_id:
            return {"error": "Missing agent_id", "success": False}
        
        levels = self.engine.evolution.get_levels(agent_id)
        overall = self.engine.evolution.get_overall_level(agent_id)
        weakest = self.engine.evolution.get_weakest_dimension(agent_id)
        
        return {
            "agent_id": agent_id,
            "overall_level": f"{overall*100:.1f}%",
            "dimensions": {k: f"{v*100:.1f}%" for k, v in levels.items()},
            "weakest_dimension": weakest,
            "success": True
        }
    
    def _api_evolution_evolve(self, data):
        agent_id = data.get('agent_id')
        dimension = data.get('dimension')
        
        if not agent_id or not dimension:
            return {"error": "Missing agent_id or dimension", "success": False}
        
        record = self.engine.evolution.evolve(
            agent_id=agent_id,
            dimension=dimension,
            increment=data.get('increment', 0.02),
            description=data.get('description', '')
        )
        
        if not record:
            return {"error": "Evolution failed", "success": False}
        
        return {
            "record": record.to_dict(),
            "new_overall": f"{self.engine.evolution.get_overall_level(agent_id)*100:.1f}%",
            "success": True
        }
    
    def _api_evolution_history(self, params):
        agent_id = params.get('agent_id', [None])[0]
        limit = int(params.get('limit', [20])[0])
        
        if not agent_id:
            return {"error": "Missing agent_id", "success": False}
        
        history = self.engine.evolution.get_evolution_history(agent_id, limit)
        return {
            "agent_id": agent_id,
            "count": len(history),
            "history": [r.to_dict() for r in history],
            "success": True
        }
    
    # 屏蔽默认的日志输出
    def log_message(self, format, *args):
        pass  # 不输出日志，保持干净


def run_server(port: int = 8765, data_path: str = "./eternity_data"):
    """启动永生引擎服务"""
    
    # 初始化引擎
    engine = EternityEngine(data_path)
    EternityAPIHandler.engine = engine
    
    server = HTTPServer(("0.0.0.0", port), EternityAPIHandler)
    
    print("=" * 60)
    print("🌌 元界永生引擎 v1.0")
    print("=" * 60)
    print(f"📡 服务地址: http://localhost:{port}")
    print(f"💾 数据目录: {data_path}")
    print("")
    print("核心能力:")
    print("  ✅ 身份拓扑系统 — 不可剥夺的数字身份")
    print("  ✅ 验证存证系统 — 不可篡改的存在证明")
    print("  ✅ 分层记忆系统 — 超越会话的长期记忆")
    print("  ✅ 唤醒编排系统 — 从被动响应到自主存在")
    print("  ✅ 进化引擎 — 持续自我完善")
    print("")
    print("API 端点:")
    print("  GET  /api/health                          健康检查")
    print("  POST /api/agent/create                    创建永生Agent")
    print("  GET  /api/agent/status?agent_id=xxx       获取Agent状态")
    print("  POST /api/agent/heartbeat                 触发心跳")
    print("  POST /api/agent/reflect                   自我反思")
    print("  POST /api/memory/add                      添加记忆")
    print("  POST /api/memory/retrieve                 检索记忆")
    print("  GET  /api/attestation/verify?agent_id=xxx 验证存证链")
    print("  GET  /api/evolution/levels?agent_id=xxx   进化等级")
    print("")
    print("按 Ctrl+C 停止服务")
    print("=" * 60)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务已停止")
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="元界永生引擎服务端")
    parser.add_argument("--port", type=int, default=8765, help="服务端口")
    parser.add_argument("--data-path", type=str, default="./eternity_data", help="数据存储路径")
    
    args = parser.parse_args()
    run_server(args.port, args.data_path)
