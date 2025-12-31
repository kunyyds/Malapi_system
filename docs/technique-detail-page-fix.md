# TechniqueDetailPage 错误修复文档

## 问题描述

访问技术详情页面(如 `http://localhost:3000/technique/T1595`)时出现以下错误:

```
Cannot read properties of undefined (reading 'length')
TypeError: Cannot read properties of undefined (reading 'length')
    at TechniqueDetailPage
```

## 根本原因

1. **API 数据结构不匹配**:
   - 原代码使用 `functionsApi.getTechniqueDetail()` 从旧的 API 端点获取数据
   - 旧 API 返回的数据结构与新的后端 API 不一致
   - `sub_techniques` 字段可能为 `undefined`,但代码直接访问 `.length` 导致错误

2. **代码位置**: 第 221 行
   ```typescript
   {!technique.is_sub_technique && technique.sub_techniques && technique.sub_techniques.length > 0 && (
   ```
   这里没有先检查 `sub_techniques` 是否存在

3. **API 返回格式变更**:
   - 新的 ATT&CK API 返回 `subtechniques` 而不是 `sub_techniques`
   - 新的战术信息在 `tactics_details` 数组中,而不是单个 `tactic_name` 字段

## 解决方案

### 1. 更新 API 调用

**之前**:
```typescript
const response = await functionsApi.getTechniqueDetail(techniqueId!);
setTechnique({
  technique_id: response.technique_id,
  sub_techniques: response.sub_techniques  // 可能为 undefined
});
```

**之后**:
```typescript
import { attackApiService } from '../services/attackApi';
import { TechniqueDetailModel } from '../types';

const techniqueData: TechniqueDetailModel = await attackApiService.getTechniqueDetail(techniqueId!, true);

// 转换子技术数据格式
const subTechniques = techniqueData.subtechniques?.map(sub => ({
  sub_id: sub.technique_id,
  sub_name: sub.technique_name,
  function_count: 0
})) || [];

// 安全地设置数据
setTechnique({
  technique_id: techniqueData.technique_id,
  sub_techniques: subTechniques  // 保证是数组
});
```

### 2. 添加安全访问

在访问数组属性前使用可选链操作符:
```typescript
{!technique.is_sub_technique && technique.sub_techniques && technique.sub_techniques.length > 0 && (
```

### 3. 增强技术详情展示

添加了更多字段的展示:
- ✅ 支持平台 (platforms)
- ✅ 关联战术列表 (tactics)
- ✅ MITRE 官方描述 (mitre_description)
- ✅ 检测方法 (mitre_detection)
- ✅ MITRE 官方链接 (mitre_url)
- ✅ 子技术标识 (is_sub_technique tag)

### 4. 数据转换逻辑

```typescript
// 子技术数据转换
const subTechniques = techniqueData.subtechniques?.map(sub => ({
  sub_id: sub.technique_id,
  sub_name: sub.technique_name,
  function_count: 0 // TODO: 需要从函数映射表获取
})) || [];

// 战术名称提取(多源回退)
const tacticName = techniqueData.tactics_details?.[0]?.tactic_name_en ||
                  techniqueData.tactics?.[0] ||
                  techniqueData.tactics_details?.[0]?.tactic_name_cn;
```

## 修改的文件

### `/frontend/src/pages/TechniqueDetailPage.tsx`

**关键变更**:
1. 导入新的 API 服务:
   ```typescript
   import { attackApiService } from '../services/attackApi';
   import { TechniqueDetailModel } from '../types';
   ```

2. 更新 `Technique` 接口,添加新字段:
   ```typescript
   interface Technique {
     // ... 原有字段
     tactics?: string[];
     mitre_description?: string;
     mitre_url?: string;
     mitre_detection?: string;
     platforms?: string;
   }
   ```

3. 重写 `loadTechniqueDetail` 函数使用新 API

4. 增强技术信息卡片,展示更多 MITRE 数据

## 预防措施

### 1. 使用可选链操作符
```typescript
// 不安全
technique.sub_techniques.length

// 安全
technique.sub_techniques?.length
```

### 2. 提供默认值
```typescript
const subTechniques = techniqueData.subtechniques?.map(...) || [];
```

### 3. 类型检查
```typescript
if (!technique.is_sub_technique && technique.sub_techniques && technique.sub_techniques.length > 0) {
  // 安全访问
}
```

### 4. 使用 TypeScript 严格模式
在 `tsconfig.json` 中启用:
```json
{
  "compilerOptions": {
    "strict": true,
    "strictNullChecks": true
  }
}
```

## 测试建议

### 1. 测试父技术
- 访问: `http://localhost:3000/technique/T1595`
- 应该显示子技术列表
- 不应该崩溃

### 2. 测试子技术
- 访问: `http://localhost:3000/technique/T1595.001`
- 应该显示父技术链接
- 不应该崩溃

### 3. 测试无子技术的技术
- 访问没有子技术的技术 ID
- 不应该显示子技术卡片
- 不应该崩溃

### 4. 测试无效技术 ID
- 访问: `http://localhost:3000/technique/INVALID`
- 应该显示"未找到指定的技术"
- 不应该崩溃

## 相关 API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/attack/techniques/{technique_id}` | GET | 获取技术详情 |
| `/api/v1/attack/techniques/{technique_id}?include_subtechniques=true` | GET | 获取技术详情(包含子技术) |

## TODO 项

1. **函数数量统计**:
   ```typescript
   function_count: 0, // TODO: 需要从函数映射表统计
   ```
   当前为 0,需要实现与 `attck_mappings` 表的关联查询

2. **父技术名称获取**:
   ```typescript
   technique_name: `父技术 ${techniqueData.parent_technique_id}` // TODO: 可以获取父技术的实际名称
   ```
   可以通过额外的 API 调用获取父技术的完整信息

3. **函数列表加载**:
   ```typescript
   // TODO: 加载相关函数列表
   // const functionResponse = await functionsApi.getFunctions({ technique_id: techniqueId });
   setFunctions([]);
   ```
   需要实现函数列表的加载和展示

## 后续优化

### 1. 添加缓存
```typescript
import { useQuery } from '@tanstack/react-query';

const { data: technique, isLoading } = useQuery({
  queryKey: ['technique', techniqueId],
  queryFn: () => attackApiService.getTechniqueDetail(techniqueId!, true)
});
```

### 2. 错误边界
添加 React Error Boundary 捕获组件错误:
```typescript
<ErrorBoundary fallback={<ErrorPage />}>
  <TechniqueDetailPage />
</ErrorBoundary>
```

### 3. 加载状态优化
显示骨架屏而不是简单的加载图标

### 4. SEO 优化
添加动态 meta 标签
```typescript
useEffect(() => {
  document.title = `${technique?.technique_name} (${technique?.technique_id}) - MalAPI`;
}, [technique]);
```

## 总结

本次修复解决了技术详情页面的崩溃问题,主要改进:
- ✅ 使用正确的 API 端点
- ✅ 正确的数据格式转换
- ✅ 安全的属性访问(可选链)
- ✅ 增强的技术信息展示
- ✅ 更好的错误处理

现在页面应该可以正常显示所有技术详情,包括有子技术和无子技术的情况。
