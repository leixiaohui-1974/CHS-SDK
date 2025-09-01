// 性能监控工具
export class PerformanceMonitor {
  private static instance: PerformanceMonitor;
  private metrics: { [key: string]: any } = {};
  private observers: PerformanceObserver[] = [];
  private isMonitoring = false;

  static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor();
    }
    return PerformanceMonitor.instance;
  }

  // 开始性能监控
  startMonitoring() {
    if (this.isMonitoring) return;
    
    this.isMonitoring = true;
    this.initializeObservers();
    this.monitorMemoryUsage();
    this.monitorNetworkPerformance();
    this.monitorRenderPerformance();
  }

  // 停止性能监控
  stopMonitoring() {
    this.isMonitoring = false;
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
  }

  // 初始化性能观察器
  private initializeObservers() {
    // 监控导航性能
    if ('PerformanceObserver' in window) {
      const navigationObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach(entry => {
          if (entry.entryType === 'navigation') {
            this.recordNavigationMetrics(entry as PerformanceNavigationTiming);
          }
        });
      });
      
      try {
        navigationObserver.observe({ entryTypes: ['navigation'] });
        this.observers.push(navigationObserver);
      } catch (e) {
        console.warn('Navigation performance monitoring not supported');
      }

      // 监控资源加载性能
      const resourceObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach(entry => {
          if (entry.entryType === 'resource') {
            this.recordResourceMetrics(entry as PerformanceResourceTiming);
          }
        });
      });
      
      try {
        resourceObserver.observe({ entryTypes: ['resource'] });
        this.observers.push(resourceObserver);
      } catch (e) {
        console.warn('Resource performance monitoring not supported');
      }

      // 监控长任务
      const longTaskObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach(entry => {
          this.recordLongTask(entry);
        });
      });
      
      try {
        longTaskObserver.observe({ entryTypes: ['longtask'] });
        this.observers.push(longTaskObserver);
      } catch (e) {
        console.warn('Long task monitoring not supported');
      }
    }
  }

  // 记录导航性能指标
  private recordNavigationMetrics(entry: PerformanceNavigationTiming) {
    this.metrics.navigation = {
      domContentLoaded: entry.domContentLoadedEventEnd - entry.domContentLoadedEventStart,
      loadComplete: entry.loadEventEnd - entry.loadEventStart,
      domInteractive: entry.domInteractive - entry.navigationStart,
      firstPaint: this.getFirstPaint(),
      firstContentfulPaint: this.getFirstContentfulPaint(),
      largestContentfulPaint: this.getLargestContentfulPaint(),
      cumulativeLayoutShift: this.getCumulativeLayoutShift(),
      firstInputDelay: this.getFirstInputDelay(),
      timeToInteractive: this.getTimeToInteractive()
    };
  }

  // 记录资源加载性能
  private recordResourceMetrics(entry: PerformanceResourceTiming) {
    if (!this.metrics.resources) {
      this.metrics.resources = [];
    }
    
    this.metrics.resources.push({
      name: entry.name,
      type: this.getResourceType(entry.name),
      duration: entry.duration,
      size: entry.transferSize || 0,
      cached: entry.transferSize === 0 && entry.decodedBodySize > 0
    });
  }

  // 记录长任务
  private recordLongTask(entry: PerformanceEntry) {
    if (!this.metrics.longTasks) {
      this.metrics.longTasks = [];
    }
    
    this.metrics.longTasks.push({
      duration: entry.duration,
      startTime: entry.startTime,
      name: entry.name
    });
  }

  // 监控内存使用情况
  private monitorMemoryUsage() {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      this.metrics.memory = {
        usedJSHeapSize: memory.usedJSHeapSize,
        totalJSHeapSize: memory.totalJSHeapSize,
        jsHeapSizeLimit: memory.jsHeapSizeLimit,
        usagePercentage: (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100
      };
    }
  }

  // 监控网络性能
  private monitorNetworkPerformance() {
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      this.metrics.network = {
        effectiveType: connection.effectiveType,
        downlink: connection.downlink,
        rtt: connection.rtt,
        saveData: connection.saveData
      };
    }
  }

  // 监控渲染性能
  private monitorRenderPerformance() {
    let frameCount = 0;
    let lastTime = performance.now();
    
    const measureFPS = () => {
      frameCount++;
      const currentTime = performance.now();
      
      if (currentTime - lastTime >= 1000) {
        this.metrics.fps = frameCount;
        frameCount = 0;
        lastTime = currentTime;
      }
      
      if (this.isMonitoring) {
        requestAnimationFrame(measureFPS);
      }
    };
    
    requestAnimationFrame(measureFPS);
  }

  // 获取核心Web指标
  private getFirstPaint(): number {
    const paintEntries = performance.getEntriesByType('paint');
    const fpEntry = paintEntries.find(entry => entry.name === 'first-paint');
    return fpEntry ? fpEntry.startTime : 0;
  }

  private getFirstContentfulPaint(): number {
    const paintEntries = performance.getEntriesByType('paint');
    const fcpEntry = paintEntries.find(entry => entry.name === 'first-contentful-paint');
    return fcpEntry ? fcpEntry.startTime : 0;
  }

  private getLargestContentfulPaint(): Promise<number> {
    return new Promise((resolve) => {
      if ('PerformanceObserver' in window) {
        const observer = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];
          resolve(lastEntry.startTime);
          observer.disconnect();
        });
        
        try {
          observer.observe({ entryTypes: ['largest-contentful-paint'] });
        } catch (e) {
          resolve(0);
        }
      } else {
        resolve(0);
      }
    });
  }

  private getCumulativeLayoutShift(): Promise<number> {
    return new Promise((resolve) => {
      let clsValue = 0;
      
      if ('PerformanceObserver' in window) {
        const observer = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry: any) => {
            if (!entry.hadRecentInput) {
              clsValue += entry.value;
            }
          });
        });
        
        try {
          observer.observe({ entryTypes: ['layout-shift'] });
          setTimeout(() => {
            observer.disconnect();
            resolve(clsValue);
          }, 5000);
        } catch (e) {
          resolve(0);
        }
      } else {
        resolve(0);
      }
    });
  }

  private getFirstInputDelay(): Promise<number> {
    return new Promise((resolve) => {
      if ('PerformanceObserver' in window) {
        const observer = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const firstEntry = entries[0];
          resolve((firstEntry as any).processingStart - firstEntry.startTime);
          observer.disconnect();
        });
        
        try {
          observer.observe({ entryTypes: ['first-input'] });
        } catch (e) {
          resolve(0);
        }
      } else {
        resolve(0);
      }
    });
  }

  private getTimeToInteractive(): number {
    // 简化的TTI计算
    const navigationEntry = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    return navigationEntry ? navigationEntry.domInteractive - navigationEntry.navigationStart : 0;
  }

  // 获取资源类型
  private getResourceType(url: string): string {
    if (url.includes('.js')) return 'script';
    if (url.includes('.css')) return 'stylesheet';
    if (url.includes('.png') || url.includes('.jpg') || url.includes('.svg')) return 'image';
    if (url.includes('.woff') || url.includes('.ttf')) return 'font';
    return 'other';
  }

  // 获取性能报告
  getPerformanceReport(): any {
    return {
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent,
      metrics: { ...this.metrics }
    };
  }

  // 获取性能评分
  getPerformanceScore(): number {
    const metrics = this.metrics;
    let score = 100;
    
    // FCP评分 (0-2.5s: 100分, 2.5-4s: 50分, >4s: 0分)
    if (metrics.navigation?.firstContentfulPaint) {
      const fcp = metrics.navigation.firstContentfulPaint / 1000;
      if (fcp > 4) score -= 30;
      else if (fcp > 2.5) score -= 15;
    }
    
    // 内存使用评分
    if (metrics.memory?.usagePercentage) {
      if (metrics.memory.usagePercentage > 80) score -= 20;
      else if (metrics.memory.usagePercentage > 60) score -= 10;
    }
    
    // FPS评分
    if (metrics.fps) {
      if (metrics.fps < 30) score -= 20;
      else if (metrics.fps < 50) score -= 10;
    }
    
    // 长任务评分
    if (metrics.longTasks?.length > 5) {
      score -= 15;
    }
    
    return Math.max(0, score);
  }

  // 清理性能数据
  clearMetrics() {
    this.metrics = {};
  }

  // 导出性能数据
  exportMetrics(): string {
    return JSON.stringify(this.getPerformanceReport(), null, 2);
  }
}

// 导出性能监控器实例
export const performanceMonitor = PerformanceMonitor.getInstance();

// 性能监控装饰器
export function withPerformanceMonitoring<T extends (...args: any[]) => any>(
  target: T,
  methodName: string
): T {
  return ((...args: any[]) => {
    const startTime = performance.now();
    const result = target.apply(this, args);
    const endTime = performance.now();
    
    console.log(`${methodName} 执行时间: ${endTime - startTime}ms`);
    
    return result;
  }) as T;
}

// React Hook for performance monitoring
export function usePerformanceMonitoring() {
  const [metrics, setMetrics] = React.useState<any>({});
  const [score, setScore] = React.useState<number>(100);
  
  React.useEffect(() => {
    performanceMonitor.startMonitoring();
    
    const interval = setInterval(() => {
      const report = performanceMonitor.getPerformanceReport();
      const currentScore = performanceMonitor.getPerformanceScore();
      setMetrics(report.metrics);
      setScore(currentScore);
    }, 5000);
    
    return () => {
      clearInterval(interval);
      performanceMonitor.stopMonitoring();
    };
  }, []);
  
  return { metrics, score };
}