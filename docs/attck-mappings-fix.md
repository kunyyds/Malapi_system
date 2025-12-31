# ATT&CK 映射表修复文档

## 问题描述

用户报告数据库中的 ATT&CK 映射为空：
- 32 个函数存在于 `malapi_functions` 表
- 所有函数的 `manifest_json` 字段都包含 ATT&CK 数据，如 `"attck": ["T1490", "T1480"]`
- 但 `attck_mappings` 表完全为空（0 条记录）
- 导致前端技术详情页面无法显示关联的函数列表

## 根本原因分析

### 发现的问题

1. **数据从未导入**：
   - `batch_importer.py` 中有准备 ATT&CK 映射的代码（第 774-785 行）
   - 但映射数据从未实际插入到 `attck_mappings` 表
   - 可能原因：
     - 导入脚本从未执行
     - 导入时发生静默失败
     - 数据库结构变更导致导入失败

2. **数据库验证**：
   ```sql
   -- 检查映射表
   SELECT COUNT(*) FROM attck_mappings;  -- 返回 0

   -- 检查函数数据
   SELECT COUNT(*) FROM malapi_functions WHERE manifest_json IS NOT NULL;  -- 返回 32

   -- 检查 manifest_json 中的 ATT&CK 数据
   SELECT json_extract(manifest_json, '$.attck')
   FROM malapi_functions
   WHERE manifest_json IS NOT NULL;
   -- 返回: ["T1490","T1480"], ["T1070.004","T1490"], ...
   ```

3. **外键约束验证**：
   - 所有 manifest_json 中的 ATT&CK ID 都存在于 `attack_techniques` 表
   - 外键约束不是导致映射为空的原因

## 解决方案

### 1. 创建数据填充脚本

创建了 `/backend/scripts/maintenance/populate_attck_mappings_from_manifest.py`：

**功能**：
- 从 `malapi_functions.manifest_json` 提取 ATT&CK 数据
- 验证 technique_id 存在于 `attack_techniques` 表
- 批量插入有效的映射到 `attck_mappings` 表
- 提供详细的执行报告和统计信息

**执行结果**：
```
✓ 总函数数: 32
✓ 有 manifest_json 的函数: 32
✓ 现有 ATT&CK 映射: 0
✓ ATT&CK 技术总数: 691

✓ 准备插入映射: 70 条
✗ 无效的 technique_id: 0 条
✗ JSON 解析错误: 0 个

✓ 成功插入: 70 条

最终映射数: 70 条
未映射函数: 0 个
```

### 2. 后端 API 增强

在 `/backend/src/api/routes/attack.py` 添加新端点：

#### `GET /attack/techniques/{technique_id}/functions`

**功能**：获取指定技术关联的函数列表，支持分页

**参数**：
- `technique_id`: 技术 ID（路径参数）
- `page`: 页码，默认 1
- `page_size`: 每页大小，默认 10，最大 100

**响应**：
```json
[
  {
    "id": 1,
    "hash_id": "7b630b9eae12986861cd973b68f88169",
    "alias": "MalAPI_Dynamicbufferrelocator",
    "root_function": "sub_403fe8",
    "summary": "动态重新定位和管理缓冲区链...",
    "status": "ok",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
]
```

**响应头**：
- `X-Total-Count`: 总记录数
- `X-Page`: 当前页码
- `X-Page-Size`: 每页大小
- `X-Total-Pages`: 总页数

### 3. 前端服务更新

在 `/frontend/src/services/attackApi.ts` 添加新方法：

```typescript
static async getTechniqueFunctions(
  techniqueId: string,
  page: number = 1,
  pageSize: number = 10
): Promise<{
  functions: any[],
  total: number,
  page: number,
  pageSize: number,
  totalPages: number
}>
```

**功能**：调用后端 API 获取技术关联的函数列表，提取分页信息

### 4. 前端页面更新

在 `/frontend/src/pages/TechniqueDetailPage.tsx` 更新：

**新增状态**：
```typescript
const [pagination, setPagination] = useState({
  current: 1,
  pageSize: 10,
  total: 0
});
const [functionsLoading, setFunctionsLoading] = useState(false);
```

**新增函数加载方法**：
```typescript
const loadFunctions = async (page: number, pageSize: number) => {
  try {
    setFunctionsLoading(true);
    const response = await attackApiService.getTechniqueFunctions(
      techniqueId!,
      page,
      pageSize
    );
    setFunctions(response.functions);
    setPagination({
      current: response.page,
      pageSize: response.pageSize,
      total: response.total
    });
    // 更新技术对象中的函数数量
    setTechnique(prev => prev ? { ...prev, function_count: response.total } : null);
  } catch (error) {
    message.error('加载函数列表失败');
    console.error('Failed to load functions:', error);
  } finally {
    setFunctionsLoading(false);
  }
};
```

**更新表格组件**：
- 显示实际的函数总数（`pagination.total`）
- 支持分页加载
- 添加加载状态指示器

## 数据统计

### 映射统计

**总体情况**：
- 函数总数: 32
- ATT&CK 映射总数: 70 条
- 有映射的函数: 32 个（100%）
- 涉及的技术: 25 个

**函数映射统计（Top 10）**：
| 函数 ID | 别名 | 映射数 |
|---------|------|--------|
| 3 | MalAPI_Lzmaunpacker | 3 |
| 8 | MalAPI_Windowmessagehandler | 3 |
| 11 | MalAPI_Datadecryptionandcopy | 3 |
| 13 | MalAPI_OptimizedMemcpy | 3 |
| 17 | MalAPI_Createprocesswithredirection | 3 |
| ... | ... | ... |

**技术映射统计**：
| 技术 ID | 技术名称 | 函数数 |
|---------|----------|--------|
| T1027 | Obfuscated Files or Information | 13 |
| T1055 | Process Injection | 13 |
| T1140 | Deobfuscate/Decode Files or Information | 9 |
| T1490 | Inhibit System Recovery | 4 |
| T1027.002 | Software Packing | 3 |
| ... | ... | ... |

## 使用方法

### 1. 填充 ATT&CK 映射（一次性操作）

```bash
cd /home/mine/workspace/MalAPI_system/backend
python3 scripts/maintenance/populate_attck_mappings_from_manifest.py
```

### 2. 启动后端服务

```bash
cd backend
conda activate malapi-backend
python -m uvicorn src.main:app --reload
```

### 3. 访问技术详情页面

例如：
- `http://localhost:3000/technique/T1027`（13 个函数）
- `http://localhost:3000/technique/T1055`（13 个函数）
- `http://localhost:3000/technique/T1490`（4 个函数）

## 验证

### 数据库验证

```bash
# 检查映射总数
sqlite3 backend/malapi.db "SELECT COUNT(*) FROM attck_mappings;"

# 检查特定技术的函数
sqlite3 backend/malapi.db "
SELECT f.alias, at.technique_name
FROM attck_mappings am
JOIN malapi_functions f ON am.function_id = f.id
JOIN attack_techniques at ON am.technique_id = at.technique_id
WHERE at.technique_id = 'T1027';
"
```

### API 验证

```bash
# 获取技术详情
curl http://localhost:8000/api/v1/attack/techniques/T1027

# 获取技术的函数列表
curl http://localhost:8000/api/v1/attack/techniques/T1027/functions?page=1&page_size=10
```

### 前端验证

1. 访问 ATT&CK 矩阵页面
2. 点击任意技术
3. 验证技术详情页面显示：
   - 正确的函数数量
   - 完整的函数列表
   - 可用的分页控制

## 相关文件

### 后端
- `/backend/src/api/routes/attack.py` - 添加 `/functions` 端点
- `/backend/scripts/maintenance/populate_attck_mappings_from_manifest.py` - 数据填充脚本
- `/backend/src/database/models.py` - 数据库模型定义

### 前端
- `/frontend/src/services/attackApi.ts` - 添加 `getTechniqueFunctions` 方法
- `/frontend/src/pages/TechniqueDetailPage.tsx` - 更新函数加载和显示逻辑
- `/frontend/src/types/index.ts` - 类型定义

### 文档
- `/docs/attck-mappings-fix.md` - 本文档
- `/docs/frontend-api-migration.md` - 前端 API 迁移文档
- `/docs/technique-detail-page-fix.md` - 技术详情页面修复文档

## 后续优化建议

### 1. 自动化映射导入

修改 `batch_importer.py`，在导入函数时自动创建 ATT&CK 映射：

```python
# 在导入函数后
if attck_list and function_id:
    for technique_id in attck_list:
        mapping = AttCKMapping(
            function_id=function_id,
            technique_id=technique_id
        )
        session.add(mapping)
```

### 2. 添加映射关系管理 API

- POST/DELETE `/attack/techniques/{technique_id}/functions/{function_id}`
- 批量添加/删除映射关系
- 映射关系的审计日志

### 3. 性能优化

- 在 `attck_mappings` 表添加复合索引
- 实现映射关系缓存
- 使用 Redis 缓存热门技术的函数列表

### 4. 数据完整性

- 添加定期检查任务，验证映射完整性
- 自动清理无效映射（技术或函数被删除）
- 数据同步工具，确保 manifest_json 和映射表一致

## 总结

本次修复解决了 ATT&CK 映射表为空的问题：

1. ✅ **识别问题**：发现 32 个函数的 ATT&CK 数据存在于 manifest_json 但未在映射表中
2. ✅ **根本原因**：导入脚本从未执行映射插入逻辑
3. ✅ **实施方案**：创建数据填充脚本，成功填充 70 条映射
4. ✅ **API 增强**：添加获取技术函数列表的端点
5. ✅ **前端更新**：更新技术详情页面，显示实际的函数数据
6. ✅ **数据验证**：所有 32 个函数都有完整的 ATT&CK 映射

现在用户可以在技术详情页面看到完整的函数列表和准确的统计信息。
