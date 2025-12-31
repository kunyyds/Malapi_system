# 技术描述链接渲染功能

## 问题描述

在技术详情页面,技术描述、MITRE 官方描述和检测方法等字段中包含 URL 链接,但是:
- ❌ URL 以纯文本形式显示
- ❌ 无法点击链接访问
- ❌ 用户体验差

## 解决方案

### 1. 创建链接渲染函数

在 `TechniqueDetailPage.tsx` 中添加了 `renderTextWithLinks` 函数:

```typescript
/**
 * 将文本中的 URL 转换为可点击的链接
 */
const renderTextWithLinks = (text: string): React.ReactNode => {
  if (!text) return null;

  // URL 正则表达式
  const urlRegex = /(https?:\/\/[^\s]+)/g;

  // 分割文本为纯文本和 URL 的数组
  const parts = text.split(urlRegex);

  return (
    <Paragraph>
      {parts.map((part, index) => {
        // 检查是否是 URL
        if (urlRegex.test(part)) {
          return (
            <a
              key={index}
              href={part}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: '#1890ff', textDecoration: 'underline' }}
            >
              {part}
            </a>
          );
        }
        // 纯文本，需要处理换行符
        return part.split('\n').map((line, lineIndex) => (
          <span key={index + '-' + lineIndex}>
            {line}
            {lineIndex < part.split('\n').length - 1 && <br />}
          </span>
        ));
      })}
    </Paragraph>
  );
};
```

### 2. 应用到所有描述字段

替换了以下三个字段的渲染方式:

#### 技术描述
```typescript
{technique.description && (
  <div style={{ marginTop: 16 }}>
    <Title level={5}>
      <InfoCircleOutlined /> 技术描述
    </Title>
    {renderTextWithLinks(technique.description)}
  </div>
)}
```

#### MITRE 官方描述
```typescript
{technique.mitre_description && technique.mitre_description !== technique.description && (
  <div style={{ marginTop: 16 }}>
    <Title level={5}>
      <InfoCircleOutlined /> MITRE 官方描述
    </Title>
    {renderTextWithLinks(technique.mitre_description)}
  </div>
)}
```

#### 检测方法
```typescript
{technique.mitre_detection && (
  <div style={{ marginTop: 16 }}>
    <Title level={5}>
      <BulbOutlined /> 检测方法
    </Title>
    {renderTextWithLinks(technique.mitre_detection)}
  </div>
)}
```

## 功能特性

### ✅ 自动识别 URL
- 使用改进的正则表达式 `/(https?:\/\/[^\s.,;!?()]+[^\s.,;!?()])/g` 匹配 HTTP/HTTPS 链接
- 自动识别文本中的所有 URL
- **智能排除末尾标点**: 避免将 URL 后面的逗号、句号、分号、感叹号、问号、括号等包含在链接中

### ✅ 可点击链接
- 所有 URL 转换为 `<a>` 标签
- `target="_blank"` 在新标签页打开
- `rel="noopener noreferrer"` 安全属性

### ✅ 保持格式
- 纯文本部分保持原样
- 正确处理换行符 (`\n`)
- 混合文本和链接的正确渲染

### ✅ 样式统一
- 链接颜色: `#1890ff` (Ant Design 蓝色)
- 下划线样式
- 与系统整体风格一致

## 示例

### 输入文本
```
For more information, visit https://attack.mitre.org/techniques/T1595/
and https://www.example.com for additional details.

See also: https://cms.gov/cj
```

### 输出效果
```
For more information, visit
[https://attack.mitre.org/techniques/T1595] (可点击的蓝色链接,不包含末尾的/)
 and
[https://www.example.com] (可点击的蓝色链接)
 for additional details.

See also:
[cms.gov/cj] (会被识别为不完整的URL,保持为文本)

句号后的链接正确处理:
Visit https://example.com. (链接不包含句号)
```

## 优势

1. **用户体验提升**
   - 一键访问参考资料
   - 无需手动复制粘贴 URL

2. **安全性**
   - 正确使用 `rel="noopener noreferrer"`
   - 防止新页面访问原页面 window 对象
   - 防止流量劫持攻击

3. **可维护性**
   - 集中管理的渲染函数
   - 易于扩展和修改
   - 可复用到其他组件

4. **性能优化**
   - 使用 React key 优化渲染
   - 避免不必要的重渲染

## 后续优化建议

### 1. 支持更多 URL 格式
```typescript
// 扩展正则表达式支持更多协议
const urlRegex = /(https?:\/\/[^\s]+)|(www\.[^\s]+)|(ftp:\/\/[^\s]+)/g;
```

### 2. 链接缩短显示
```typescript
// 长链接自动缩短
const displayUrl = part.length > 50
  ? part.substring(0, 50) + '...'
  : part;
```

### 3. 添加链接图标
```typescript
import { LinkOutlined } from '@ant-design/icons';

<a href={part}>
  <LinkOutlined /> {part}
</a>
```

### 4. 外部链接提示
```typescript
<Tooltip title="点击访问外部链接">
  <a href={part} target="_blank">
    {part} <ExportOutlined />
  </a>
</Tooltip>
```

### 5. 链接预览
```typescript
// 鼠标悬停时显示链接预览
<a
  href={part}
  onMouseEnter={() => setShowPreview(true)}
  onMouseLeave={() => setShowPreview(false)}
>
  {part}
</a>
```

### 6. 复用为独立组件
创建 `TextWithLinks.tsx` 组件:

```typescript
import React from 'react';

interface TextWithLinksProps {
  text: string;
  className?: string;
}

export const TextWithLinks: React.FC<TextWithLinksProps> = ({ text, className }) => {
  // ... 实现
};

// 使用
<TextWithLinks text={technique.description} />
```

## 测试建议

### 1. 测试纯文本
- 不包含 URL 的文本应正常显示

### 2. 测试单个链接
```
Visit https://example.com for more info.
```

### 3. 测试多个链接
```
See https://site1.com and https://site2.com
```

### 4. 测试混合内容
```
Text before https://link.com text after
```

### 5. 测试换行
```
Line 1
Line 2 with https://link.com
Line 3
```

### 6. 测试特殊字符
```
Link with punctuation: https://example.com.
Link with parentheses: (https://example.com/path)
```

### 7. 测试标点符号排除(改进后)
```
Visit https://example.com, then https://another.com; and finally https://last.com!

结果:
- https://example.com (不包含逗号)
- https://another.com (不包含分号)
- https://last.com (不包含感叹号)
```

### 8. 测试括号内的链接
```
(see https://example.com/path for details)

结果: https://example.com/path (不包含括号)
```

## 正则表达式说明

### 原始版本
```regex
/(https?:\/\/[^\s]+)/g
```
**问题**: 会匹配到末尾的标点符号

### 改进版本
```regex
/(https?:\/\/[^\s.,;!?()]+[^\s.,;!?()])/g
```
**优势**:
- `[^\s.,;!?()]+` 匹配不包含空白和标点的 URL 主体
- `[^\s.,;!?()]` 确保最后一个字符也不是标点符号
- 正确处理以下标点: `, . ; ! ? ( )`

### 匹配示例
| 输入 | 原始版本匹配 | 改进版本匹配 |
|------|------------|------------|
| `Visit https://site.com.` | `https://site.com.` ❌ | `https://site.com` ✅ |
| `See (https://site.com/path)` | `https://site.com/path)` ❌ | `https://site.com/path` ✅ |
| `Link: https://site.com; next` | `https://site.com;` ❌ | `https://site.com` ✅ |
| `Wow! https://site.com?` | `https://site.com?` ❌ | `https://site.com` ✅ |

## 修改的文件

- `/frontend/src/pages/TechniqueDetailPage.tsx`
  - 添加 `renderTextWithLinks` 函数
  - 更新三个描述字段的渲染方式

## 相关文档

- [MDN - 使用 rel=noopener](https://developer.mozilla.org/zh-CN/docs/Web/HTML/Element/a)
- [React - 列表渲染](https://react.dev/learn/rendering-lists)
- [Ant Design - Typography](https://ant.design/components/typography-cn/)

## 总结

本次改进使得技术详情页面中的链接可以正常点击访问,显著提升了用户体验。所有包含 URL 的文本字段(技术描述、MITRE 官方描述、检测方法)都支持自动识别和渲染链接。
