# 前端 ATT&CK 矩阵数据源迁移文档

## 概述

本文档记录了将前端 ATT&CK 矩阵数据从静态 JSON 文件迁移到后端 API 的实现过程。

## 变更日期

2024-12-31

## 变更内容

### 1. 数据源变更

#### 之前
- 使用静态 JSON 文件: `frontend/src/matrix-enterprise.json`
- 数据在构建时确定,无法动态更新

#### 之后
- 使用后端 API: `GET /api/v1/attack/matrix`
- 数据从数据库动态加载,保持与 ATT&CK 框架同步

### 2. 新增文件

#### `frontend/src/services/attackApi.ts`
专门的 ATT&CK API 服务模块,提供以下功能:

- **AttackApiService 类**: 封装所有 ATT&CK 相关 API 调用
- **方法列表**:
  - `getTactics()`: 获取所有战术
  - `getTacticDetail(tacticId)`: 获取单个战术详情
  - `getTechniques(params)`: 获取技术列表(支持筛选)
  - `getTechniqueDetail(techniqueId, includeSubtechniques)`: 获取技术详情
  - `getAttackMatrix(includeSubtechniques)`: 获取矩阵数据
  - `getStatistics()`: 获取统计信息
  - `getMatrixDataForFrontend()`: 将矩阵数据转换为前端格式
  - `getTechniquesByTactic(tacticId)`: 按战术筛选技术
  - `getTechniquesByPlatform(platform)`: 按平台筛选技术
  - `getSubtechniques(parentTechniqueId)`: 获取子技术列表

### 3. 类型定义增强

#### `frontend/src/types/index.ts`

新增类型定义:

```typescript
// ATT&CK战术响应模型
export interface TacticModel {
  id: number;
  tactic_id: string;
  tactic_name_en: string;
  tactic_name_cn?: string;
  description?: string;
  stix_id?: string;
}

// ATT&CK技术响应模型
export interface TechniqueModel {
  id: number;
  technique_id: string;
  technique_name: string;
  tactics: string[];
  is_sub_technique: boolean;
  parent_technique_id?: string;
  // ... 更多字段
}

// ATT&CK技术详情模型(包含子技术)
export interface TechniqueDetailModel extends TechniqueModel {
  subtechniques?: TechniqueModel[];
  tactics_details?: TacticModel[];
}

// ATT&CK矩阵单元格模型
export interface MatrixCellModel {
  technique_id: string;
  technique_name: string;
  has_subtechniques: boolean;
}

// ATT&CK战术矩阵模型
export interface TacticMatrixModel {
  tactic_id: string;
  tactic_name?: string;
  tactic_name_cn?: string;
  techniques: MatrixCellModel[];
}

// ATT&CK统计信息
export interface AttackStatistics {
  tactics: number;
  parent_techniques: number;
  subtechniques: number;
  total_techniques: number;
  revoked: number;
  data_source: string;
  stix_version: string;
}
```

### 4. 页面组件修改

#### `frontend/src/pages/MatrixPage.tsx`

**主要变更**:

1. **导入变更**:
   ```typescript
   // 之前
   import { mockAttackMatrixData } from '@/data/mockData';

   // 之后
   import { attackApiService } from '@/services/attackApi';
   ```

2. **数据加载逻辑**:
   ```typescript
   // 之前
   const matrixResponse = mockAttackMatrixData;

   // 之后
   const matrixResponse = await attackApiService.getMatrixDataForFrontend();
   ```

3. **统计数据获取**:
   ```typescript
   // 使用新的统计API
   const statsResponse = await attackApiService.getStatistics();
   ```

### 5. API 服务清理

#### `frontend/src/services/api.ts`

- 移除了 `mockAttackMatrixData` 模拟数据
- 更新 `getAttackMatrix()` 方法使用后端 API
- 添加了类型安全的响应处理

## 后端 API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/attack/tactics` | GET | 获取所有战术列表 |
| `/api/v1/attack/tactics/{tactic_id}` | GET | 获取单个战术详情 |
| `/api/v1/attack/techniques` | GET | 获取技术列表(支持参数筛选) |
| `/api/v1/attack/techniques/{technique_id}` | GET | 获取技术详情 |
| `/api/v1/attack/matrix` | GET | 获取 ATT&CK 矩阵数据 |
| `/api/v1/attack/statistics` | GET | 获取统计信息 |

## 数据流程图

```
┌─────────────┐
│  Frontend   │
│  MatrixPage │
└──────┬──────┘
       │
       │ 调用
       ▼
┌─────────────────────────────┐
│  attackApiService          │
│  (attackApi.ts)            │
└──────┬──────────────────────┘
       │
       │ HTTP GET /api/v1/attack/matrix
       ▼
┌─────────────────────────────┐
│  Backend API               │
│  (attack.py)               │
└──────┬──────────────────────┘
       │
       │ 查询
       ▼
┌─────────────────────────────┐
│  Database                  │
│  - attack_tactics          │
│  - attack_techniques       │
│  - attack_technique_tactics │
└─────────────────────────────┘
```

## 优势

### 1. 数据一致性
- 前端和后端使用相同的数据源
- 避免静态数据与数据库不一致

### 2. 动态更新
- ATT&CK 框架更新时,无需重新构建前端
- 数据库更新后自动反映到前端

### 3. 可维护性
- API 层与业务逻辑分离
- 类型安全的接口定义
- 统一的错误处理

### 4. 扩展性
- 支持按战术、平台筛选
- 支持子技术查询
- 便于添加新的查询维度

### 5. 性能优化
- 减少前端包体积
- 服务端可以添加缓存
- 支持分页和按需加载

## 注意事项

### TODO 项

1. **函数数量统计**: 当前 `function_count` 字段为 0,需要实现与函数映射表的关联
   - 建议: 在后端 API 中添加函数数量统计
   - 或者: 创建专门的统计 API 查询每个技术的函数数量

2. **错误处理增强**:
   - 添加更友好的错误提示
   - 实现重试机制
   - 添加降级策略(如显示静态数据)

3. **缓存策略**:
   - 考虑在前端添加短期缓存
   - 避免频繁调用矩阵 API

4. **加载优化**:
   - 矩阵数据较大时考虑分片加载
   - 实现虚拟滚动优化渲染性能

### 兼容性

- 后端 API 返回的字段名使用 snake_case
- 前端类型定义保持一致
- 确保数据库字段与 API 响应匹配

### 测试建议

1. 测试 API 连接失败的场景
2. 测试大数据量下的渲染性能
3. 测试不同筛选条件的数据展示
4. 测试子技术的展开/折叠交互

## 回滚方案

如果需要回滚到静态数据模式:

1. 恢复 `frontend/src/matrix-enterprise.json` 数据加载
2. 使用 `import matrixData from '@/matrix-enterprise.json'`
3. 修改 `MatrixPage.tsx` 的 `loadMatrixData` 函数

但建议优先解决 API 问题,因为动态数据源是长期更优的方案。

## 相关文件

### 新增文件
- `frontend/src/services/attackApi.ts`

### 修改文件
- `frontend/src/pages/MatrixPage.tsx`
- `frontend/src/services/api.ts`
- `frontend/src/types/index.ts`

### 废弃文件
- `frontend/src/matrix-enterprise.json` (可以保留作为备份)

## 后续优化建议

1. **实现函数数量关联**
   ```typescript
   // 在 attackApi.ts 中添加
   static async getMatrixWithFunctionCounts(): Promise<AttackMatrixData[]> {
     const matrixData = await this.getMatrixDataForFrontend();
     // 调用统计 API 获取每个技术的函数数量
     const functionCounts = await this.getFunctionCountsByTechnique();
     return matrixData.map(item => ({
       ...item,
       function_count: functionCounts[item.technique_id] || 0
     }));
   }
   ```

2. **添加实时数据更新**
   ```typescript
   // 定期刷新矩阵数据
   useEffect(() => {
     const interval = setInterval(() => {
       loadMatrixData();
     }, 5 * 60 * 1000); // 每5分钟刷新
     return () => clearInterval(interval);
   }, []);
   ```

3. **实现增量更新**
   - 只更新变化的技术数据
   - 使用 WebSocket 推送更新

## 联系方式

如有问题或建议,请联系开发团队。
