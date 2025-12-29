import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.extend(relativeTime);

// 日期格式化
export const formatDate = (dateString: string, format: string = 'YYYY-MM-DD HH:mm:ss'): string => {
  return dayjs(dateString).format(format);
};

export const formatDateFromNow = (dateString: string): string => {
  return dayjs(dateString).fromNow();
};

// 计算强度颜色
export const getIntensityColor = (level: string): string => {
  switch (level) {
    case 'high': return '#ff4d4f';
    case 'medium': return '#fa8c16';
    case 'low': return '#52c41a';
    default: return '#f0f0f0';
  }
};

export const getIntensityLevel = (count: number): 'high' | 'medium' | 'low' | 'none' => {
  if (count >= 5) return 'high';
  if (count >= 2) return 'medium';
  if (count >= 1) return 'low';
  return 'none';
};

// 文本截断
export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

// 防抖函数
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void => {
  let timeoutId: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
};

// 节流函数
export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void => {
  let lastCall = 0;
  return (...args: Parameters<T>) => {
    const now = Date.now();
    if (now - lastCall >= delay) {
      lastCall = now;
      func(...args);
    }
  };
};

// 生成随机ID
export const generateId = (): string => {
  return Math.random().toString(36).substr(2, 9);
};

// 深拷贝
export const deepClone = <T>(obj: T): T => {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj.getTime()) as unknown as T;
  if (obj instanceof Array) return obj.map(item => deepClone(item)) as unknown as T;
  if (typeof obj === 'object') {
    const clonedObj = {} as T;
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        clonedObj[key] = deepClone(obj[key]);
      }
    }
    return clonedObj;
  }
  return obj;
};

// 数组去重
export const uniqueArray = <T>(array: T[], key?: keyof T): T[] => {
  if (!key) {
    return Array.from(new Set(array));
  }
  const seen = new Set();
  return array.filter(item => {
    const value = item[key];
    if (seen.has(value)) {
      return false;
    }
    seen.add(value);
    return true;
  });
};

// 数组分组
export const groupBy = <T, K extends keyof any>(
  array: T[],
  key: (item: T) => K
): Record<K, T[]> => {
  return array.reduce((groups, item) => {
    const group = key(item);
    groups[group] = groups[group] || [];
    groups[group].push(item);
    return groups;
  }, {} as Record<K, T[]>);
};

// 文件大小格式化
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// 数字格式化
export const formatNumber = (num: number): string => {
  return new Intl.NumberFormat('zh-CN').format(num);
};

// 百分比格式化
export const formatPercentage = (num: number, total: number): string => {
  if (total === 0) return '0%';
  return ((num / total) * 100).toFixed(1) + '%';
};

// URL参数解析
export const getQueryParams = (url?: string): Record<string, string> => {
  const queryString = url ? url.split('?')[1] : window.location.search.slice(1);
  const params: Record<string, string> = {};

  if (queryString) {
    queryString.split('&').forEach(param => {
      const [key, value] = param.split('=');
      params[decodeURIComponent(key)] = decodeURIComponent(value || '');
    });
  }

  return params;
};

// 构建URL参数
export const buildQueryString = (params: Record<string, any>): string => {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.append(key, String(value));
    }
  });

  return searchParams.toString();
};

// 本地存储工具
export const storage = {
  get: <T>(key: string, defaultValue?: T): T | null => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue || null;
    } catch {
      return defaultValue || null;
    }
  },

  set: (key: string, value: any): void => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error('保存到localStorage失败:', error);
    }
  },

  remove: (key: string): void => {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error('从localStorage删除失败:', error);
    }
  },

  clear: (): void => {
    try {
      localStorage.clear();
    } catch (error) {
      console.error('清空localStorage失败:', error);
    }
  }
};

// 类名合并工具
export const classNames = (...classes: (string | undefined | null | false)[]): string => {
  return classes.filter(Boolean).join(' ');
};

// 错误边界处理
export const safeExecute = <T>(
  fn: () => T,
  fallback: T
): T => {
  try {
    return fn();
  } catch {
    return fallback;
  }
};

// 异步重试
export const retry = async <T>(
  fn: () => Promise<T>,
  maxAttempts: number = 3,
  delay: number = 1000
): Promise<T> => {
  let lastError: Error | null = null;

  for (let i = 0; i < maxAttempts; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;
      if (i < maxAttempts - 1) {
        await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)));
      }
    }
  }

  throw lastError || new Error('Operation failed after maximum attempts');
};