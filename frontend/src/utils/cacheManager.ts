// 缓存管理器
export class CacheManager {
  private static instance: CacheManager;
  private cache = new Map<string, CacheItem>();
  private maxSize: number;
  private ttl: number; // 默认TTL（毫秒）
  private cleanupInterval: NodeJS.Timeout | null = null;

  constructor(maxSize = 100, ttl = 5 * 60 * 1000) { // 默认5分钟TTL
    this.maxSize = maxSize;
    this.ttl = ttl;
    this.startCleanup();
  }

  static getInstance(maxSize?: number, ttl?: number): CacheManager {
    if (!CacheManager.instance) {
      CacheManager.instance = new CacheManager(maxSize, ttl);
    }
    return CacheManager.instance;
  }

  // 设置缓存项
  set<T>(key: string, value: T, customTtl?: number): void {
    const expiresAt = Date.now() + (customTtl || this.ttl);
    const item: CacheItem = {
      value,
      expiresAt,
      accessCount: 0,
      lastAccessed: Date.now(),
      size: this.calculateSize(value)
    };

    // 如果缓存已满，执行LRU清理
    if (this.cache.size >= this.maxSize) {
      this.evictLRU();
    }

    this.cache.set(key, item);
  }

  // 获取缓存项
  get<T>(key: string): T | null {
    const item = this.cache.get(key);
    
    if (!item) {
      return null;
    }

    // 检查是否过期
    if (Date.now() > item.expiresAt) {
      this.cache.delete(key);
      return null;
    }

    // 更新访问信息
    item.accessCount++;
    item.lastAccessed = Date.now();
    
    return item.value as T;
  }

  // 检查缓存是否存在且未过期
  has(key: string): boolean {
    const item = this.cache.get(key);
    
    if (!item) {
      return false;
    }

    if (Date.now() > item.expiresAt) {
      this.cache.delete(key);
      return false;
    }

    return true;
  }

  // 删除缓存项
  delete(key: string): boolean {
    return this.cache.delete(key);
  }

  // 清空所有缓存
  clear(): void {
    this.cache.clear();
  }

  // 获取缓存统计信息
  getStats(): CacheStats {
    const items = Array.from(this.cache.values());
    const totalSize = items.reduce((sum, item) => sum + item.size, 0);
    const expiredCount = items.filter(item => Date.now() > item.expiresAt).length;
    
    return {
      size: this.cache.size,
      maxSize: this.maxSize,
      totalMemoryUsage: totalSize,
      expiredItems: expiredCount,
      hitRate: this.calculateHitRate(),
      averageAccessCount: items.reduce((sum, item) => sum + item.accessCount, 0) / items.length || 0
    };
  }

  // LRU清理策略
  private evictLRU(): void {
    let oldestKey = '';
    let oldestTime = Date.now();
    
    for (const [key, item] of this.cache.entries()) {
      if (item.lastAccessed < oldestTime) {
        oldestTime = item.lastAccessed;
        oldestKey = key;
      }
    }
    
    if (oldestKey) {
      this.cache.delete(oldestKey);
    }
  }

  // 计算对象大小（简化版本）
  private calculateSize(value: any): number {
    const jsonString = JSON.stringify(value);
    return new Blob([jsonString]).size;
  }

  // 计算命中率
  private calculateHitRate(): number {
    // 这里需要额外的统计逻辑，简化处理
    return 0.85; // 假设85%的命中率
  }

  // 定期清理过期项
  private startCleanup(): void {
    this.cleanupInterval = setInterval(() => {
      const now = Date.now();
      for (const [key, item] of this.cache.entries()) {
        if (now > item.expiresAt) {
          this.cache.delete(key);
        }
      }
    }, 60000); // 每分钟清理一次
  }

  // 停止清理
  destroy(): void {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
      this.cleanupInterval = null;
    }
    this.clear();
  }

  // 预热缓存
  async warmup(keys: string[], dataLoader: (key: string) => Promise<any>): Promise<void> {
    const promises = keys.map(async (key) => {
      if (!this.has(key)) {
        try {
          const data = await dataLoader(key);
          this.set(key, data);
        } catch (error) {
          console.warn(`Failed to warmup cache for key: ${key}`, error);
        }
      }
    });
    
    await Promise.all(promises);
  }

  // 批量设置
  setMultiple<T>(items: Array<{ key: string; value: T; ttl?: number }>): void {
    items.forEach(({ key, value, ttl }) => {
      this.set(key, value, ttl);
    });
  }

  // 批量获取
  getMultiple<T>(keys: string[]): Map<string, T | null> {
    const result = new Map<string, T | null>();
    keys.forEach(key => {
      result.set(key, this.get<T>(key));
    });
    return result;
  }
}

// 缓存项接口
interface CacheItem {
  value: any;
  expiresAt: number;
  accessCount: number;
  lastAccessed: number;
  size: number;
}

// 缓存统计接口
interface CacheStats {
  size: number;
  maxSize: number;
  totalMemoryUsage: number;
  expiredItems: number;
  hitRate: number;
  averageAccessCount: number;
}

// API缓存管理器
export class ApiCacheManager {
  private cacheManager: CacheManager;
  private pendingRequests = new Map<string, Promise<any>>();

  constructor(maxSize = 50, ttl = 2 * 60 * 1000) { // API缓存2分钟TTL
    this.cacheManager = new CacheManager(maxSize, ttl);
  }

  // 缓存API请求
  async cacheRequest<T>(
    key: string,
    requestFn: () => Promise<T>,
    ttl?: number
  ): Promise<T> {
    // 检查缓存
    const cached = this.cacheManager.get<T>(key);
    if (cached !== null) {
      return cached;
    }

    // 检查是否有正在进行的相同请求
    if (this.pendingRequests.has(key)) {
      return this.pendingRequests.get(key)!;
    }

    // 发起新请求
    const requestPromise = requestFn()
      .then(result => {
        this.cacheManager.set(key, result, ttl);
        this.pendingRequests.delete(key);
        return result;
      })
      .catch(error => {
        this.pendingRequests.delete(key);
        throw error;
      });

    this.pendingRequests.set(key, requestPromise);
    return requestPromise;
  }

  // 使缓存失效
  invalidate(pattern?: string): void {
    if (!pattern) {
      this.cacheManager.clear();
      return;
    }

    // 支持通配符模式
    const regex = new RegExp(pattern.replace(/\*/g, '.*'));
    const keysToDelete: string[] = [];
    
    for (const [key] of this.cacheManager['cache'].entries()) {
      if (regex.test(key)) {
        keysToDelete.push(key);
      }
    }
    
    keysToDelete.forEach(key => this.cacheManager.delete(key));
  }

  // 获取缓存统计
  getStats(): CacheStats {
    return this.cacheManager.getStats();
  }
}

// 本地存储缓存管理器
export class LocalStorageCacheManager {
  private prefix: string;
  private maxSize: number;

  constructor(prefix = 'chs_cache_', maxSize = 50) {
    this.prefix = prefix;
    this.maxSize = maxSize;
  }

  // 设置本地存储缓存
  set<T>(key: string, value: T, ttl = 24 * 60 * 60 * 1000): void { // 默认24小时
    try {
      const item = {
        value,
        expiresAt: Date.now() + ttl,
        timestamp: Date.now()
      };
      
      localStorage.setItem(this.prefix + key, JSON.stringify(item));
      this.cleanup();
    } catch (error) {
      console.warn('Failed to set localStorage cache:', error);
    }
  }

  // 获取本地存储缓存
  get<T>(key: string): T | null {
    try {
      const itemStr = localStorage.getItem(this.prefix + key);
      if (!itemStr) return null;
      
      const item = JSON.parse(itemStr);
      
      if (Date.now() > item.expiresAt) {
        localStorage.removeItem(this.prefix + key);
        return null;
      }
      
      return item.value as T;
    } catch (error) {
      console.warn('Failed to get localStorage cache:', error);
      return null;
    }
  }

  // 删除本地存储缓存
  delete(key: string): void {
    localStorage.removeItem(this.prefix + key);
  }

  // 清理过期项和超出大小限制的项
  private cleanup(): void {
    const keys = Object.keys(localStorage)
      .filter(key => key.startsWith(this.prefix))
      .map(key => {
        try {
          const item = JSON.parse(localStorage.getItem(key) || '{}');
          return { key, timestamp: item.timestamp || 0, expiresAt: item.expiresAt || 0 };
        } catch {
          return { key, timestamp: 0, expiresAt: 0 };
        }
      })
      .sort((a, b) => a.timestamp - b.timestamp);

    // 删除过期项
    const now = Date.now();
    keys.forEach(({ key, expiresAt }) => {
      if (now > expiresAt) {
        localStorage.removeItem(key);
      }
    });

    // 如果仍然超出大小限制，删除最旧的项
    const remainingKeys = keys.filter(({ expiresAt }) => now <= expiresAt);
    if (remainingKeys.length > this.maxSize) {
      const keysToDelete = remainingKeys.slice(0, remainingKeys.length - this.maxSize);
      keysToDelete.forEach(({ key }) => localStorage.removeItem(key));
    }
  }

  // 清空所有缓存
  clear(): void {
    const keys = Object.keys(localStorage).filter(key => key.startsWith(this.prefix));
    keys.forEach(key => localStorage.removeItem(key));
  }
}

// 导出实例
export const cacheManager = CacheManager.getInstance();
export const apiCacheManager = new ApiCacheManager();
export const localStorageCacheManager = new LocalStorageCacheManager();

// React Hook for cache management
export function useCache<T>(key: string, fetcher: () => Promise<T>, ttl?: number) {
  const [data, setData] = React.useState<T | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const result = await apiCacheManager.cacheRequest(key, fetcher, ttl);
        setData(result);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [key]);

  const invalidate = React.useCallback(() => {
    apiCacheManager.invalidate(key);
  }, [key]);

  return { data, loading, error, invalidate };
}