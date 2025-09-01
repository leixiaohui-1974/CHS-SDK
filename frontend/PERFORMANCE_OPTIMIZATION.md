# CHS 仿真平台前端性能优化指南

## 概述

本文档描述了 CHS 仿真平台前端项目中实施的性能优化策略和工具。这些优化旨在提供更快的加载速度、更流畅的用户体验和更高效的资源利用。

## 性能优化特性

### 1. 代码分割和懒加载

#### 路由级别懒加载
- 所有页面组件都采用懒加载策略
- 使用 React.lazy() 和 Suspense 实现
- 智能预加载基于用户行为模式

```typescript
// 使用示例
import { LazyRoute } from '@utils/lazyLoad';

// 在路由中使用
<Route path="/dashboard" element={<LazyRoute.Dashboard />} />
```

#### 组件级别懒加载
- 重型组件（如图表、数据表格）采用懒加载
- 提供加载状态和错误处理

```typescript
// 使用示例
import { LazyComponent } from '@utils/lazyLoad';

// 在组件中使用
<LazyComponent.SimulationChart data={chartData} />
```

### 2. 智能预加载系统

#### 基于用户行为的预加载
- 记录用户访问模式
- 自动预加载高频访问的组件
- 在空闲时间进行预加载

```typescript
// 使用示例
import { intelligentPreloader } from '@utils/lazyLoad';

// 记录用户访问
intelligentPreloader.recordVisit('Dashboard');
```

### 3. 性能监控系统

#### 实时性能指标
- Core Web Vitals 监控（FCP, LCP, CLS, FID）
- 内存使用监控
- 网络性能监控
- 渲染性能监控（FPS）

```typescript
// 使用示例
import { usePerformanceMonitoring } from '@utils/performanceMonitor';

function MyComponent() {
  const { metrics, score } = usePerformanceMonitoring();
  
  return (
    <div>
      <p>性能评分: {score}</p>
      <p>FPS: {metrics.fps}</p>
    </div>
  );
}
```

#### 性能报告
- 自动生成性能报告
- 支持导出性能数据
- 性能评分系统

### 4. 缓存管理系统

#### 多层缓存策略
- 内存缓存（LRU策略）
- API响应缓存
- 本地存储缓存

```typescript
// 使用示例
import { useCache } from '@utils/cacheManager';

function DataComponent() {
  const { data, loading, error } = useCache(
    'api-data-key',
    () => fetchApiData(),
    5 * 60 * 1000 // 5分钟TTL
  );
  
  if (loading) return <Spin />;
  if (error) return <div>Error: {error.message}</div>;
  
  return <div>{JSON.stringify(data)}</div>;
}
```

#### 缓存统计和管理
- 缓存命中率统计
- 内存使用监控
- 自动清理过期缓存

### 5. 错误边界和错误处理

#### 全局错误捕获
- React 错误边界
- 全局错误处理
- 错误报告和日志记录

```typescript
// 使用示例
import ErrorBoundary from '@components/ErrorBoundary';

<ErrorBoundary 
  showErrorDetails={isDevelopment}
  enableReporting={isProduction}
>
  <MyComponent />
</ErrorBoundary>
```

#### 错误恢复机制
- 自动重试机制
- 优雅降级
- 用户友好的错误提示

### 6. 构建优化

#### Vite 配置优化
- 代码压缩和混淆
- Tree shaking
- 资源优化
- 开发服务器优化

```typescript
// vite.config.ts 关键配置
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          antd: ['antd'],
          utils: ['lodash', 'dayjs']
        }
      }
    },
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    }
  }
});
```

## 性能指标和目标

### 目标性能指标
- **First Contentful Paint (FCP)**: < 2.5s
- **Largest Contentful Paint (LCP)**: < 4.0s
- **Cumulative Layout Shift (CLS)**: < 0.1
- **First Input Delay (FID)**: < 100ms
- **Time to Interactive (TTI)**: < 5.0s

### 资源优化目标
- **JavaScript Bundle Size**: < 500KB (gzipped)
- **CSS Bundle Size**: < 100KB (gzipped)
- **Image Optimization**: WebP format, lazy loading
- **Font Loading**: Preload critical fonts

## 使用指南

### 开发环境设置

1. **安装依赖**
```bash
npm install
```

2. **启动开发服务器**
```bash
npm run dev
```

3. **性能分析**
```bash
npm run build:analyze
```

### 性能监控

#### 开启性能监控
```typescript
import { performanceMonitor } from '@utils/performanceMonitor';

// 启动监控
performanceMonitor.startMonitoring();

// 获取性能报告
const report = performanceMonitor.getPerformanceReport();
console.log('性能报告:', report);
```

#### 查看性能指标
- 打开浏览器开发者工具
- 查看 Console 中的性能日志
- 使用 Performance 面板分析性能

### 缓存管理

#### 清理缓存
```typescript
import { cacheManager, apiCacheManager } from '@utils/cacheManager';

// 清理所有缓存
cacheManager.clear();

// 清理API缓存
apiCacheManager.invalidate();
```

#### 缓存统计
```typescript
// 获取缓存统计
const stats = cacheManager.getStats();
console.log('缓存统计:', stats);
```

### 错误处理

#### 查看错误日志
```typescript
import { ErrorLogManager } from '@components/ErrorBoundary';

// 获取错误日志
const logs = ErrorLogManager.getErrorLogs();
console.log('错误日志:', logs);

// 获取错误统计
const stats = ErrorLogManager.getErrorStats();
console.log('错误统计:', stats);
```

## 最佳实践

### 1. 组件开发
- 使用 React.memo 优化组件渲染
- 合理使用 useMemo 和 useCallback
- 避免在渲染函数中创建对象和函数

### 2. 数据获取
- 使用缓存管理器缓存API响应
- 实现数据预加载策略
- 使用分页和虚拟滚动处理大量数据

### 3. 资源优化
- 使用 SVG 替代位图图像
- 实现图片懒加载
- 压缩和优化静态资源

### 4. 代码组织
- 按功能模块分割代码
- 使用动态导入减少初始包大小
- 避免循环依赖

## 性能测试

### 自动化测试
```bash
# 运行性能测试
npm run test:performance

# 生成性能报告
npm run build:report
```

### 手动测试
1. 使用 Chrome DevTools 的 Lighthouse
2. 使用 WebPageTest 进行在线测试
3. 使用 Performance API 进行自定义测试

## 监控和维护

### 持续监控
- 定期检查性能指标
- 监控错误率和类型
- 分析用户行为模式

### 优化建议
- 根据性能报告调整优化策略
- 定期更新依赖包
- 清理无用代码和资源

## 故障排除

### 常见问题

1. **加载速度慢**
   - 检查网络连接
   - 清理浏览器缓存
   - 检查资源大小

2. **内存泄漏**
   - 检查事件监听器清理
   - 检查定时器清理
   - 使用性能监控工具分析

3. **渲染性能差**
   - 检查组件重渲染
   - 优化状态管理
   - 使用 React DevTools Profiler

### 调试工具
- React DevTools
- Chrome DevTools Performance
- 内置性能监控器
- 错误日志管理器

## 更新日志

### v1.0.0 (当前版本)
- 实现基础性能优化框架
- 添加懒加载和代码分割
- 集成性能监控系统
- 实现缓存管理策略
- 添加错误边界和错误处理

---

如有任何问题或建议，请联系开发团队。