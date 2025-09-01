import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import jaJP from 'antd/locale/ja_JP';
import { useLanguageStore } from '@stores/languageStore';
import Layout from '@components/Layout';
import ErrorBoundary from '@components/ErrorBoundary';
import { LazyRoute, preloadCriticalComponents, intelligentPreloader } from '@utils/lazyLoad';
import { performanceMonitor } from '@utils/performanceMonitor';
import '@styles/global.css';

function App() {
  const { language } = useLanguageStore();
  
  // 根据语言设置Ant Design的locale
  const getAntdLocale = () => {
    switch (language) {
      case 'ja-JP':
        return jaJP;
      case 'zh-CN':
      default:
        return zhCN;
    }
  };
  
  // 应用启动时的性能优化
  React.useEffect(() => {
    // 启动性能监控
    performanceMonitor.startMonitoring();
    
    // 预加载关键组件
    preloadCriticalComponents();
    
    // 记录应用启动
    intelligentPreloader.recordVisit('App');
    
    return () => {
      // 清理性能监控
      performanceMonitor.stopMonitoring();
    };
  }, []);
  
  return (
    <ErrorBoundary 
      showErrorDetails={process.env.NODE_ENV === 'development'}
      enableReporting={process.env.NODE_ENV === 'production'}
    >
      <ConfigProvider locale={getAntdLocale()}>
        <div className="App">
          <Router>
            <Layout>
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<LazyRoute.Dashboard />} />
                <Route path="/simulation" element={<LazyRoute.Simulation />} />
                <Route path="/batch-simulation" element={<LazyRoute.BatchSimulation />} />
                <Route path="/data-management" element={<LazyRoute.DataManagement />} />
                <Route path="/monitoring" element={<LazyRoute.Monitoring />} />
                <Route path="/settings" element={<LazyRoute.Settings />} />
                <Route path="/reports" element={<LazyRoute.Reports />} />
                <Route path="/help" element={<LazyRoute.Help />} />
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </Layout>
          </Router>
        </div>
      </ConfigProvider>
    </ErrorBoundary>
  );
}

export default App;
