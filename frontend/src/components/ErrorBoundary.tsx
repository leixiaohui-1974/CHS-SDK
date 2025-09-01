import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Result, Button, Typography, Collapse, Space } from 'antd';
import { ReloadOutlined, BugOutlined, HomeOutlined } from '@ant-design/icons';
import { performanceMonitor } from '@utils/performanceMonitor';

const { Text, Paragraph } = Typography;
const { Panel } = Collapse;

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  showErrorDetails?: boolean;
  enableReporting?: boolean;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string;
}

class ErrorBoundary extends Component<Props, State> {
  private retryCount = 0;
  private maxRetries = 3;

  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: ''
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // 生成错误ID
    const errorId = `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    return {
      hasError: true,
      error,
      errorId
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({ errorInfo });
    
    // 记录错误到性能监控
    this.logError(error, errorInfo);
    
    // 调用外部错误处理函数
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
    
    // 自动错误报告
    if (this.props.enableReporting) {
      this.reportError(error, errorInfo);
    }
  }

  // 记录错误信息
  private logError(error: Error, errorInfo: ErrorInfo) {
    const errorData = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      url: window.location.href,
      userAgent: navigator.userAgent,
      errorId: this.state.errorId,
      performanceMetrics: performanceMonitor.getPerformanceReport()
    };
    
    console.error('Error Boundary caught an error:', errorData);
    
    // 存储到本地存储以便后续分析
    try {
      const existingErrors = JSON.parse(localStorage.getItem('chs_error_logs') || '[]');
      existingErrors.push(errorData);
      
      // 只保留最近50个错误
      if (existingErrors.length > 50) {
        existingErrors.splice(0, existingErrors.length - 50);
      }
      
      localStorage.setItem('chs_error_logs', JSON.stringify(existingErrors));
    } catch (e) {
      console.warn('Failed to store error log:', e);
    }
  }

  // 错误报告
  private async reportError(error: Error, errorInfo: ErrorInfo) {
    try {
      const errorReport = {
        errorId: this.state.errorId,
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
        url: window.location.href,
        userAgent: navigator.userAgent,
        buildVersion: process.env.REACT_APP_VERSION || 'unknown',
        userId: localStorage.getItem('userId') || 'anonymous'
      };
      
      // 这里可以发送到错误监控服务
      // await fetch('/api/errors', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(errorReport)
      // });
      
      console.log('Error report prepared:', errorReport);
    } catch (e) {
      console.warn('Failed to report error:', e);
    }
  }

  // 重试机制
  private handleRetry = () => {
    if (this.retryCount < this.maxRetries) {
      this.retryCount++;
      this.setState({
        hasError: false,
        error: null,
        errorInfo: null,
        errorId: ''
      });
    } else {
      // 超过最大重试次数，刷新页面
      window.location.reload();
    }
  };

  // 返回首页
  private handleGoHome = () => {
    window.location.href = '/';
  };

  // 刷新页面
  private handleRefresh = () => {
    window.location.reload();
  };

  // 获取错误详情
  private getErrorDetails() {
    const { error, errorInfo, errorId } = this.state;
    
    if (!error || !errorInfo) return null;
    
    return {
      errorId,
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      retryCount: this.retryCount
    };
  }

  // 渲染错误详情
  private renderErrorDetails() {
    const details = this.getErrorDetails();
    if (!details || !this.props.showErrorDetails) return null;
    
    return (
      <Collapse ghost>
        <Panel header="错误详情" key="1">
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <Text strong>错误ID: </Text>
              <Text code>{details.errorId}</Text>
            </div>
            <div>
              <Text strong>时间: </Text>
              <Text>{details.timestamp}</Text>
            </div>
            <div>
              <Text strong>重试次数: </Text>
              <Text>{details.retryCount}/{this.maxRetries}</Text>
            </div>
            <div>
              <Text strong>错误信息: </Text>
              <Paragraph>
                <Text code>{details.message}</Text>
              </Paragraph>
            </div>
            {details.stack && (
              <div>
                <Text strong>错误堆栈: </Text>
                <Paragraph>
                  <Text code style={{ whiteSpace: 'pre-wrap', fontSize: '12px' }}>
                    {details.stack}
                  </Text>
                </Paragraph>
              </div>
            )}
            {details.componentStack && (
              <div>
                <Text strong>组件堆栈: </Text>
                <Paragraph>
                  <Text code style={{ whiteSpace: 'pre-wrap', fontSize: '12px' }}>
                    {details.componentStack}
                  </Text>
                </Paragraph>
              </div>
            )}
          </Space>
        </Panel>
      </Collapse>
    );
  }

  render() {
    if (this.state.hasError) {
      // 如果提供了自定义fallback，使用它
      if (this.props.fallback) {
        return this.props.fallback;
      }
      
      // 默认错误UI
      return (
        <div style={{ padding: '50px', textAlign: 'center' }}>
          <Result
            status="error"
            icon={<BugOutlined style={{ color: '#ff4d4f' }} />}
            title="页面出现错误"
            subTitle={`错误ID: ${this.state.errorId}`}
            extra={[
              <Space key="actions" size="middle">
                <Button 
                  type="primary" 
                  icon={<ReloadOutlined />}
                  onClick={this.handleRetry}
                  disabled={this.retryCount >= this.maxRetries}
                >
                  {this.retryCount >= this.maxRetries ? '重试已达上限' : `重试 (${this.retryCount}/${this.maxRetries})`}
                </Button>
                <Button 
                  icon={<HomeOutlined />}
                  onClick={this.handleGoHome}
                >
                  返回首页
                </Button>
                <Button 
                  icon={<ReloadOutlined />}
                  onClick={this.handleRefresh}
                >
                  刷新页面
                </Button>
              </Space>
            ]}
          >
            <div style={{ textAlign: 'left', maxWidth: '600px', margin: '0 auto' }}>
              <Paragraph>
                <Text type="secondary">
                  很抱歉，页面遇到了一个意外错误。我们已经记录了这个问题，并会尽快修复。
                  您可以尝试重新加载页面，或者返回首页继续使用。
                </Text>
              </Paragraph>
              
              {this.renderErrorDetails()}
              
              <Paragraph style={{ marginTop: '20px' }}>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  如果问题持续存在，请联系技术支持并提供错误ID。
                </Text>
              </Paragraph>
            </div>
          </Result>
        </div>
      );
    }

    return this.props.children;
  }
}

// 高阶组件：为组件添加错误边界
export function withErrorBoundary<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  errorBoundaryProps?: Omit<Props, 'children'>
) {
  const WithErrorBoundaryComponent = (props: P) => {
    return (
      <ErrorBoundary {...errorBoundaryProps}>
        <WrappedComponent {...props} />
      </ErrorBoundary>
    );
  };
  
  WithErrorBoundaryComponent.displayName = `withErrorBoundary(${WrappedComponent.displayName || WrappedComponent.name})`;
  
  return WithErrorBoundaryComponent;
}

// React Hook：错误处理
export function useErrorHandler() {
  const [error, setError] = React.useState<Error | null>(null);
  
  const handleError = React.useCallback((error: Error) => {
    setError(error);
    
    // 记录错误
    console.error('Handled error:', error);
    
    // 可以在这里添加错误报告逻辑
  }, []);
  
  const clearError = React.useCallback(() => {
    setError(null);
  }, []);
  
  // 如果有错误，抛出它以便ErrorBoundary捕获
  React.useEffect(() => {
    if (error) {
      throw error;
    }
  }, [error]);
  
  return { handleError, clearError, error };
}

// 异步错误处理Hook
export function useAsyncError() {
  const [, setError] = React.useState();
  
  return React.useCallback((error: Error) => {
    setError(() => {
      throw error;
    });
  }, []);
}

// 错误日志管理
export class ErrorLogManager {
  static getErrorLogs(): any[] {
    try {
      return JSON.parse(localStorage.getItem('chs_error_logs') || '[]');
    } catch {
      return [];
    }
  }
  
  static clearErrorLogs(): void {
    localStorage.removeItem('chs_error_logs');
  }
  
  static exportErrorLogs(): string {
    const logs = this.getErrorLogs();
    return JSON.stringify(logs, null, 2);
  }
  
  static getErrorStats(): { total: number; recent: number; byType: Record<string, number> } {
    const logs = this.getErrorLogs();
    const now = Date.now();
    const oneHourAgo = now - 60 * 60 * 1000;
    
    const recent = logs.filter(log => {
      const logTime = new Date(log.timestamp).getTime();
      return logTime > oneHourAgo;
    }).length;
    
    const byType = logs.reduce((acc, log) => {
      const errorType = log.message.split(':')[0] || 'Unknown';
      acc[errorType] = (acc[errorType] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    return {
      total: logs.length,
      recent,
      byType
    };
  }
}

export default ErrorBoundary;