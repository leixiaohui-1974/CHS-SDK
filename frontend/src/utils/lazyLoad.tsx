import React, { Suspense, ComponentType } from 'react';
import { Spin } from 'antd';

// 懒加载组件的高阶组件
export function withLazyLoading<T extends object>(
  importFunc: () => Promise<{ default: ComponentType<T> }>,
  fallback?: React.ReactNode
) {
  const LazyComponent = React.lazy(importFunc);

  return function LazyLoadedComponent(props: T) {
    return (
      <Suspense 
        fallback={
          fallback || (
            <div 
              style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                height: '200px',
                width: '100%'
              }}
            >
              <Spin size="large" tip="加载中..." />
            </div>
          )
        }
      >
        <LazyComponent {...props} />
      </Suspense>
    );
  };
}

// 预加载函数
export function preloadComponent(
  importFunc: () => Promise<{ default: ComponentType<any> }>
) {
  // 在空闲时间预加载组件
  if ('requestIdleCallback' in window) {
    requestIdleCallback(() => {
      importFunc();
    });
  } else {
    // 降级方案：使用setTimeout
    setTimeout(() => {
      importFunc();
    }, 100);
  }
}

// 路由级别的懒加载
export const LazyRoute = {
  Dashboard: withLazyLoading(() => import('@pages/Dashboard')),
  Simulation: withLazyLoading(() => import('@pages/Simulation')),
  BatchSimulation: withLazyLoading(() => import('@pages/BatchSimulation')),
  DataManagement: withLazyLoading(() => import('@pages/DataManagement')),
  Monitoring: withLazyLoading(() => import('@pages/Monitoring')),
  Settings: withLazyLoading(() => import('@pages/Settings')),
  Reports: withLazyLoading(() => import('@pages/Reports')),
  Help: withLazyLoading(() => import('@pages/Help'))
};

// 组件级别的懒加载
export const LazyComponent = {
  SimulationChart: withLazyLoading(() => import('@components/SimulationChart')),
  PerformanceMonitor: withLazyLoading(() => import('@components/SimulationPerformance')),
  ErrorHandler: withLazyLoading(() => import('@components/SimulationErrorHandler')),
  DataTable: withLazyLoading(() => import('@components/DataTable')),
  ConfigPanel: withLazyLoading(() => import('@components/ConfigPanel'))
};

// 预加载关键组件
export function preloadCriticalComponents() {
  // 预加载仪表板相关组件
  preloadComponent(() => import('@pages/Dashboard'));
  preloadComponent(() => import('@components/SimulationChart'));
  preloadComponent(() => import('@components/SimulationPerformance'));
  
  // 预加载仿真相关组件
  preloadComponent(() => import('@pages/Simulation'));
  preloadComponent(() => import('@components/SimulationErrorHandler'));
}

// 基于用户行为的智能预加载
export class IntelligentPreloader {
  private static instance: IntelligentPreloader;
  private preloadedComponents = new Set<string>();
  private userBehavior: { [key: string]: number } = {};

  static getInstance(): IntelligentPreloader {
    if (!IntelligentPreloader.instance) {
      IntelligentPreloader.instance = new IntelligentPreloader();
    }
    return IntelligentPreloader.instance;
  }

  // 记录用户访问行为
  recordVisit(componentName: string) {
    this.userBehavior[componentName] = (this.userBehavior[componentName] || 0) + 1;
    this.schedulePreload();
  }

  // 基于访问频率预加载
  private schedulePreload() {
    const sortedComponents = Object.entries(this.userBehavior)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 3); // 预加载访问频率最高的3个组件

    sortedComponents.forEach(([componentName]) => {
      if (!this.preloadedComponents.has(componentName)) {
        this.preloadComponent(componentName);
        this.preloadedComponents.add(componentName);
      }
    });
  }

  private preloadComponent(componentName: string) {
    const componentMap: { [key: string]: () => Promise<any> } = {
      'Dashboard': () => import('@pages/Dashboard'),
      'Simulation': () => import('@pages/Simulation'),
      'BatchSimulation': () => import('@pages/BatchSimulation'),
      'DataManagement': () => import('@pages/DataManagement'),
      'Monitoring': () => import('@pages/Monitoring'),
      'Settings': () => import('@pages/Settings'),
      'Reports': () => import('@pages/Reports'),
      'Help': () => import('@pages/Help')
    };

    const importFunc = componentMap[componentName];
    if (importFunc) {
      preloadComponent(importFunc);
    }
  }

  // 清理预加载缓存
  clearCache() {
    this.preloadedComponents.clear();
    this.userBehavior = {};
  }
}

// 导出智能预加载器实例
export const intelligentPreloader = IntelligentPreloader.getInstance();