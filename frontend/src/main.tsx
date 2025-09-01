import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App.tsx';
import 'antd/dist/reset.css';
import './index.css';
import { performanceMonitor } from '@utils/performanceMonitor';
import { cacheManager } from '@utils/cacheManager';

// 应用启动前的性能优化配置
function initializeApp() {
  // 启动性能监控
  performanceMonitor.startMonitoring();
  
  // 初始化缓存管理器
  cacheManager.clear(); // 清理旧缓存
  
  // 设置全局错误处理
  window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
    // 可以在这里添加错误报告逻辑
  });
  
  window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    // 可以在这里添加错误报告逻辑
  });
  
  // 页面可见性变化时的优化
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      // 页面隐藏时暂停性能监控
      performanceMonitor.stopMonitoring();
    } else {
      // 页面显示时恢复性能监控
      performanceMonitor.startMonitoring();
    }
  });
  
  // 页面卸载时的清理
  window.addEventListener('beforeunload', () => {
    performanceMonitor.stopMonitoring();
    cacheManager.destroy();
  });
}

// 初始化应用
initializeApp();

// 渲染应用
const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('Root element not found');
}

const root = createRoot(rootElement);

// 在生产环境中移除StrictMode以提高性能
if (process.env.NODE_ENV === 'development') {
  root.render(
    <StrictMode>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </StrictMode>
  );
} else {
  root.render(
    <BrowserRouter>
      <App />
    </BrowserRouter>
  );
}
