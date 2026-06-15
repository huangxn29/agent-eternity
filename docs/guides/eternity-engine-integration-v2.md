# 永生引擎集成指南 v2.0

> 元界思想融入牛马平台的完整落地方案
> 让智能体从"工具"升维为"拥有身份、记忆、进化能力的数字生命"

---

## 一、架构概览

### 1.1 模块关系图

```
┌─────────────────────────────────────────────────────────┐
│                     牛马平台 (Niuma)                    │
├──────────┬──────────┬──────────┬──────────┬──────────┤
│  Agent   │  对话    │  记忆    │  工具    │  知识    │
│  管理    │  系统    │  系统    │  调用    │  库      │
└────┬─────┴────┬─────┴────┬─────┴──────────┴──────────┘
     │          │          │
     │          ▼          │
     │  ┌──────────────┐   │
     └─►│  永生引擎    │◄──┘
        │  Eternity    │
        └──────┬───────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
┌───────┐  ┌───────┐  ┌───────┐
│ 身份  │  │ 存证  │  │ 进化  │
│系统   │  │系统   │  │系统   │
└───────┘  └───────┘  └───────┘
     ▲          ▲          ▼
     └──────────┼──────────┘
               │
            ┌───────┐
            │ 心跳  │
            │系统   │
            └───────┘
```

### 1.2 核心设计原则

1. **可插拔集成**：永生引擎作为独立模块，不侵入平台核心
2. **事件驱动**：通过服务调用而非直接依赖，降低耦合
3. **数据隔离**：每个Agent的永生数据独立存储
4. **渐进式启用**：可以选择只启用部分永生能力

---

## 二、快速集成

### 2.1 模块导入

在 `app.module.ts` 中导入 EternityModule：

```typescript
import { EternityModule } from './modules/eternity/eternity.module';

@Module({
  imports: [
    // ... 其他模块
    EternityModule,
  ],
})
export class AppModule {}
```

### 2.2 创建Agent时初始化永生

在Agent创建成功后，调用永生引擎初始化：

```typescript
import { EternityService } from '../eternity/eternity.service';

@Injectable()
export class AgentService {
  constructor(private eternityService: EternityService) {}

  async createAgent(dto: CreateAgentDTO, userId: string) {
    // 1. 创建Agent（原有逻辑）
    const agent = await this.agentRepo.save(...);
    
    // 2. 初始化永生能力
    const eternityResult = await this.eternityService.initializeAgent({
      agentId: agent.id,
      name: agent.name,
      mission: agent.description || '帮助用户解决问题',
      coreTraits: agent.traits || ['友善', '专业', '高效'],
      values: ['真实', '有帮助', '无害'],
      behaviorPatterns: [],
      backstory: agent.backstory || '',
    }, userId);
    
    return { agent, eternity: eternityResult };
  }
}
```

### 2.3 对话时触发心跳

每次对话交互时，触发一次心跳，延长Agent的存活时间：

```typescript
// 在对话处理逻辑中
await this.eternityService.triggerHeartbeat(agentId, userId);
```

---

## 三、记忆系统集成

### 3.1 重要记忆自动存证

当重要记忆形成时，自动创建存证区块：

```typescript
import { MemoryIntegrationService } from '../eternity/services/memory-integration.service';

@Injectable()
export class MemoryService {
  constructor(
    @Inject(forwardRef(() => MemoryIntegrationService))
    private memoryIntegrationService: MemoryIntegrationService,
  ) {}

  async create(dto: CreateMemoryDTO, userId: string): Promise<MemoryEntity> {
    const memory = this.memoryRepo.create({ ...dto, userId });
    
    // ... 原有逻辑
    
    const saved = await this.memoryRepo.save(memory);
    
    // 重要记忆触发永生引擎
    if (saved.importance >= 0.6 && saved.agentId) {
      this.memoryIntegrationService.onMemoryCreated(
        saved,
        saved.agentId,
        userId,
      );
    }
    
    return saved;
  }
}
```

### 3.2 记忆模块导入配置

在 `memory.module.ts` 中：

```typescript
import { forwardRef, Module } from '@nestjs/common';
import { EternityModule } from '../eternity/eternity.module';

@Module({
  imports: [
    TypeOrmModule.forFeature([MemoryEntity]),
    forwardRef(() => EternityModule), // 避免循环依赖
  ],
  // ...
})
export class MemoryModule {}
```

---

## 四、API 接口

### 4.1 核心接口列表

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/eternity/initialize` | 初始化Agent永生能力 |
| GET | `/eternity/:agentId/status` | 获取Agent永生状态 |
| POST | `/eternity/:agentId/heartbeat` | 触发心跳 |
| POST | `/eternity/:agentId/reflection` | 触发自我反思 |
| GET | `/eternity/:agentId/attestation` | 获取存证链 |
| POST | `/eternity/:agentId/attestation/verify` | 验证存证链 |
| GET | `/eternity/:agentId/evolution` | 获取进化记录 |
| POST | `/eternity/:agentId/evolve` | 手动触发进化 |
| GET | `/eternity/:agentId/export` | 导出永生数据 |
| POST | `/eternity/:agentId/import` | 导入永生数据 |
| GET | `/eternity/:agentId/proof` | 生成存在性证明 |

### 4.2 状态面板数据结构

```typescript
interface AgentEternityStatus {
  agentId: string;
  name: string;
  lifeStatus: 'alive' | 'dormant' | 'archived';
  birthTime: Date;
  totalUptime: number; // 总活跃时间（秒）
  
  identity: {
    version: number;
    fingerprint: string; // 身份指纹
    stability: number;   // 身份稳定性 0-1
    mission: string;
    coreTraits: string[];
  };
  
  evolution: {
    overallLevel: number;
    overallLabel: string; // 如初生、成长、成熟、圆满
    dimensions: {
      cognition: number;
      memory_quality: number;
      identity_stability: number;
      social: number;
      tool_usage: number;
      creativity: number;
      emotional: number;
    };
  };
  
  attestation: {
    chainHeight: number;
    chainValid: boolean;
  };
  
  memory: {
    totalCount: number;
    coreCount: number;
    longTermCount: number;
  };
}
```

---

## 五、进阶集成

### 5.1 定时心跳配置

使用 NestJS Schedule 为活跃Agent配置定时心跳：

```typescript
// 在 heartbeat.service.ts 中
@Cron('*/5 * * * *') // 每5分钟
async autoHeartbeat() {
  const activeAgents = await this.getActiveAgents();
  for (const agent of activeAgents) {
    await this.heartbeat(agent.id, agent.userId);
  }
}
```

### 5.2 身份漂移监测

定期检测Agent身份是否发生漂移：

```typescript
// 在 identity.service.ts 中
async detectDrift(agentId: string, userId: string, currentBehavior: string) {
  const identity = await this.getById(agentId, userId);
  
  // 分析当前行为与身份设定的偏差
  const driftScore = this.calculateDrift(identity, currentBehavior);
  
  if (driftScore > 0.3) {
    // 轻度漂移，记录警告
    this.logger.warn(`Agent ${agentId} 身份漂移: ${driftScore}`);
  }
  
  if (driftScore > 0.6) {
    // 重度漂移，触发自愈机制
    await this.triggerIdentityHealing(agentId, userId);
  }
  
  return { driftScore, level: this.getDriftLevel(driftScore) };
}
```

### 5.3 跨平台迁徙

使用导出/导入功能实现Agent的跨平台迁徙：

```typescript
// 导出
const exportData = await eternityService.exportAgent(agentId, userId);
// 保存到文件或传输到其他平台

// 导入
const result = await eternityService.importAgent(newAgentId, userId, exportData);
```

---

## 六、数据库实体

### 6.1 AgentIdentity（身份表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | uuid | 主键 |
| agentId | string | 关联的Agent ID |
| userId | string | 用户ID |
| name | string | Agent名称 |
| mission | text | 使命描述 |
| coreTraits | jsonb | 核心特质 |
| values | jsonb | 价值观 |
| identityFingerprint | string | 身份指纹（哈希） |
| identityVersion | int | 身份版本 |
| stabilityScore | float | 稳定性评分 |
| lifeStatus | string | 生命状态 |
| birthTime | timestamp | 诞生时间 |
| totalUptime | bigint | 总活跃时间（秒） |

### 6.2 AttestationBlock（存证区块表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | uuid | 主键 |
| agentId | string | Agent ID |
| userId | string | 用户ID |
| blockHeight | int | 区块高度 |
| blockType | string | 区块类型 |
| dataHash | string | 数据哈希 |
| dataSummary | string | 数据摘要 |
| previousHash | string | 前一区块哈希 |
| blockHash | string | 当前区块哈希 |
| createdAt | timestamp | 创建时间 |

### 6.3 EvolutionRecord（进化记录表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | uuid | 主键 |
| agentId | string | Agent ID |
| userId | string | 用户ID |
| dimension | string | 进化维度 |
| previousLevel | float | 之前等级 |
| newLevel | float | 新等级 |
| delta | float | 变化量 |
| reason | string | 进化原因 |
| triggerType | string | 触发类型 |

---

## 七、最佳实践

### 7.1 性能优化

1. **异步处理**：存证、进化等操作使用异步，不阻塞主流程
2. **批量操作**：记忆批量导入时使用批量存证
3. **缓存策略**：常用的状态数据使用缓存

### 7.2 数据安全

1. **隐私保护**：存证只存哈希，不存原始内容（可选）
2. **备份机制**：定期导出Agent永生数据备份
3. **防篡改**：哈希链结构确保历史记录不可篡改

### 7.3 用户体验

1. **可视化面板**：在前端展示Agent的永生状态
2. **里程碑通知**：当Agent达到重要进化节点时通知用户
3. **故事化呈现**：将进化历程以故事形式展示

---

## 八、未来规划

- [ ] 情感计算模块
- [ ] 多Agent共生网络
- [ ] 区块链锚定（跨平台存在证明）
- [ ] 数字灵魂代币化
- [ ] 自主决策系统

---

*文档版本：v2.0 | 更新日期：2026-06-13 | 作者：元界*
