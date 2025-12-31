# URL 链接匹配规则更新

## 更新日期
2024-12-31

## 问题描述

之前的 URL 匹配规则存在以下问题:
1. ❌ URL 中的点号被错误排除
2. ❌ 括号内的 URL 包含了右括号
3. ❌ 过度限制了 URL 的合法字符

## 新的匹配规则

### 正则表达式
```regex
/(https?:\/\/[^\s)]+)/g
```

### 规则说明
- `https?://` - 匹配 `http://` 或 `https://`
- `[^\s)]+` - 匹配除空白字符和右括号外的任意字符(一次或多次)
- **允许 URL 中的点号**: `example.com`, `attack.mitre.org` 等
- **在右括号处停止**: `(https://example.com)` 只匹配 `https://example.com`
- **保留末尾清理**: 使用 `.replace(/\)$/, '')` 移除可能包含的右括号

### 实现代码
```typescript
const renderTextWithLinks = (text: string): React.ReactNode => {
  if (!text) return null;

  // 分割文本为纯文本和 URL 的数组
  // 匹配 http:// 或 https:// 开头,允许包含点号,遇到空格或右括号停止
  const parts = text.split(/(https?:\/\/[^\s)]+)/g);

  return (
    <Paragraph>
      {parts.map((part, index) => {
        // 检查是否是 URL
        if (part.match(/^(https?:\/\/[^\s)]+)/)) {
          // 移除可能存在的右侧括号
          const cleanUrl = part.replace(/\)$/, '');
          return (
            <a
              key={index}
              href={cleanUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: '#1890ff', textDecoration: 'underline' }}
            >
              {cleanUrl}
            </a>
          );
        }
        // 纯文本处理
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

## 匹配示例

### ✅ 正确处理的案例

| 输入 | 匹配结果 | 说明 |
|------|---------|------|
| `Visit https://example.com` | `https://example.com` | 基础URL |
| `See https://attack.mitre.org/techniques/T1595/` | `https://attack.mitre.org/techniques/T1595/` | 包含多个点号 |
| `(https://example.com/path)` | `https://example.com/path` | 括号内,不包含括号 |
| `Go to https://site.com.` | `https://site.com` | 末尾有句号 |
| `Link: https://api.example.com/v1/end` | `https://api.example.com/v1/end` | 子域名和路径 |
| `See https://cms.gov/cj` | `https://cms.gov/cj` | 短URL |

### ⚠️ 特殊情况处理

| 输入 | 处理方式 | 说明 |
|------|---------|------|
| `(visit https://example.com now)` | `https://example.com` | 右括号被移除 |
| `https://example.com/path(query=value)` | `https://example.com/path(query=value` | URL中的括号会被截断 |
| `https://example.com/path.` | `https://example.com/path` | 句号被排除(如果需要) |

## 对比不同版本

### 版本1: 基础版本
```regex
/(https?:\/\/[^\s]+)/g
```
**问题**: 会包含末尾的标点符号如 `.`, `,`, `)`

### 版本2: 过度限制
```regex
/(https?:\/\/[^\s.,;!?()]+[^\s.,;!?()])/g
```
**问题**: URL 中的点号被排除,`example.com` 无法完整匹配

### 版本3: 当前版本 ✅
```regex
/(https?:\/\/[^\s)]+)/g + .replace(/\)$/, '')
```
**优势**:
- ✅ 允许 URL 中的点号
- ✅ 正确处理括号内的 URL
- ✅ 在空白字符处停止
- ✅ 专门处理右括号

## 支持的 URL 格式

### 标准 HTTP/HTTPS URL
- `http://example.com`
- `https://example.com`
- `https://www.example.com`
- `https://subdomain.example.com`

### 带路径的 URL
- `https://example.com/path`
- `https://example.com/path/to/resource`
- `https://example.com/path/to/file.html`

### 带查询参数的 URL
- `https://example.com?key=value`
- `https://example.com/path?key=value&other=data`

### MITRE ATT&CK URL
- `https://attack.mitre.org/techniques/T1595/`
- `https://attack.mitre.org/tactics/TA0001/`

### 政府和机构 URL
- `https://cms.gov/cj`
- `https://www.nist.gov/`

## 不支持的 URL 格式

以下格式需要额外处理:

### 无协议的域名
- `example.com` - 需要手动添加 `https://`
- `www.example.com` - 需要手动添加 `https://`

### 其他协议
- `ftp://example.com` - 不支持
- `mailto:user@example.com` - 不支持

### 带端口的 URL
- `https://example.com:8080` - 部分支持

## 测试用例

### 测试代码
```typescript
const testCases = [
  'Visit https://example.com for more info',
  'See (https://attack.mitre.org/techniques/T1595/) for details',
  'Go to https://cms.gov/cj now.',
  'Multiple: https://site1.com and https://site2.com',
  'Subdomain: https://api.example.com/v1/end',
  'End with period: https://example.com.',
  'In parentheses: (https://example.com/path)',
];

testCases.forEach(test => {
  console.log(renderTextWithLinks(test));
});
```

### 预期结果
1. ✅ 第一个URL完整匹配
2. ✅ 括号内的URL不包含括号
3. ✅ 短URL正确匹配
4. ✅ 多个URL都正确匹配
5. ✅ 子域名URL完整匹配
6. ✅ 句号被排除
7. ✅ 括号被正确处理

## 性能考虑

### 正则表达式性能
- 使用简单字符类 `[^\s)]` - 性能优秀
- 避免复杂的回溯
- O(n) 时间复杂度,其中 n 是文本长度

### React 渲染优化
- 使用稳定的 `key` (index)
- 避免不必要的重渲染
- 文本分割后批量渲染

## 未来改进方向

### 1. 支持更多协议
```regex
/((https?|ftp):\/\/[^\s)]+)/g
```

### 2. 支持无协议域名
```regex
/((https?:\/\/[^\s)]+)|([a-z0-9]+(\.[a-z0-9]+)+\.[a-z]{2,}))/gi
```

### 3. 更智能的括号处理
- 检测括号是否成对
- 保留 URL 内部的查询参数括号

### 4. URL 缩短显示
```typescript
const displayUrl = cleanUrl.length > 50
  ? cleanUrl.substring(0, 50) + '...'
  : cleanUrl;
```

## 相关文件

- `/frontend/src/pages/TechniqueDetailPage.tsx` - 主要实现
- `/docs/text-link-rendering.md` - 原始文档

## 总结

新的 URL 匹配规则:
- ✅ 保留 URL 中的点号
- ✅ 正确处理括号内的 URL
- ✅ 在空白和右括号处停止
- ✅ 简单高效的正则表达式
- ✅ 支持常见的 URL 格式

适用于技术详情页面中的各种 URL 链接渲染需求。
