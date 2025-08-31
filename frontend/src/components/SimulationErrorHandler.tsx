import React, { useState, useEffect, useRef } from 'react';
import { Card, Row, Col, Alert, Button, Space, Table, Tag, Modal, Input, Select, Switch, Divider, Timeline, Statistic, Progress } from 'antd';
import { ExclamationCircleOutlined, ReloadOutlined, DownloadOutlined, ClearOutlined, BugOutlined, WarningOutlined, InfoCircleOutlined, CheckCircleOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { useModelingStore } from '../store/modelingStore';

interface ErrorLog {
  id: string;
  timestamp: number;
  level: 'error' | 'warning' | 'info' | 'debug';
  category: 'simulation' | 'computation' | 'network' | 'memory' | 'validation' | 'system';
  message: string;
  details?: string;
  stackTrace?: string;
  nodeId?: string;
  componentType?: string;
  recoverable: boolean;
  resolved: boolean;
  recoveryAction?: string;
}

interface RecoveryStrategy {
  id: string;
  name: string;
  description: string;
  applicableErrors: string[];
  autoApply: boolean;
  priority: number;
  action: () => Promise<boolean>;
}

interface SystemHealth {
  overall: 'healthy' | 'warning' | 'critical' | 'error';
  components: {
    simulation: 'healthy' | 'warning' | 'error';
    computation: 'healthy' | 'warning' | 'error';
    memory: 'healthy' | 'warning' | 'error';
    network: 'healthy' | 'warning' | 'error';
  };
  uptime: number;
  errorRate: number;
  lastCheck: number;
}

const { Option } = Select;
const { TextArea } = Input;

const SimulationErrorHandler: React.FC = () => {
  const { nodes } = useModelingStore();
  
  const [errorLogs, setErrorLogs] = useState<ErrorLog[]>([]);
  const [systemHealth, setSystemHealth] = useState<SystemHealth>({
    overall: 'healthy',
    components: {
      simulation: 'healthy',
      computation: 'healthy',
      memory: 'healthy',
      network: 'healthy'
    },
    uptime: 0,
    errorRate: 0,
    lastCheck: Date.now()
  });
  
  const [autoRecovery, setAutoRecovery] = useState(true);
  const [logLevel, setLogLevel] = useState<string>('info');
  const [selectedError, setSelectedError] = useState<ErrorLog | null>(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [recoveryInProgress, setRecoveryInProgress] = useState(false);
  
  const errorCountRef = useRef(0);
  const startTimeRef = useRef(Date.now());
  
  // Recovery strategies
  const recoveryStrategies: RecoveryStrategy[] = [
    {
      id: 'restart_simulation',
      name: '重启仿真',
      description: '停止当前仿真并重新开始',
      applicableErrors: ['simulation_crash', 'computation_overflow', 'memory_leak'],
      autoApply: true,
      priority: 1,
      action: async () => {
        // Simulate restart
        await new Promise(resolve => setTimeout(resolve, 2000));
        return true;
      }
    },
    {
      id: 'reset_component',
      name: '重置组件',
      description: '重置出错的组件到初始状态',
      applicableErrors: ['component_error', 'validation_failed'],
      autoApply: true,
      priority: 2,
      action: async () => {
        await new Promise(resolve => setTimeout(resolve, 1000));
        return true;
      }
    },
    {
      id: 'reduce_timestep',
      name: '减小时间步长',
      description: '减小仿真时间步长以提高稳定性',
      applicableErrors: ['numerical_instability', 'convergence_failed'],
      autoApply: true,
      priority: 3,
      action: async () => {
        await new Promise(resolve => setTimeout(resolve, 500));
        return true;
      }
    },
    {
      id: 'clear_cache',
      name: '清理缓存',
      description: '清理内存缓存并重新分配资源',
      applicableErrors: ['memory_error', 'cache_corruption'],
      autoApply: false,
      priority: 4,
      action: async () => {
        await new Promise(resolve => setTimeout(resolve, 1500));
        return true;
      }
    },
    {
      id: 'fallback_solver',
      name: '切换求解器',
      description: '切换到更稳定的求解器算法',
      applicableErrors: ['solver_error', 'computation_overflow'],
      autoApply: false,
      priority: 5,
      action: async () => {
        await new Promise(resolve => setTimeout(resolve, 1000));
        return true;
      }
    }
  ];
  
  // Generate simulated errors
  const generateSimulatedError = (): ErrorLog => {
    const errorTypes = [
      {
        level: 'error' as const,
        category: 'simulation' as const,
        message: '仿真计算发生数值溢出',
        details: '在时间步 t=125.3s 时，节点 reservoir_1 的水位计算结果超出物理范围',
        recoverable: true
      },
      {
        level: 'warning' as const,
        category: 'computation' as const,
        message: '收敛性检查失败',
        details: '迭代次数超过最大限制，可能影响计算精度',
        recoverable: true
      },
      {
        level: 'error' as const,
        category: 'memory' as const,
        message: '内存使用量过高',
        details: '当前内存使用量: 1.2GB，建议清理缓存或减少数据缓冲',
        recoverable: true
      },
      {
        level: 'warning' as const,
        category: 'validation' as const,
        message: '组件参数验证警告',
        details: '管道 pipe_3 的粗糙度系数可能不合理',
        recoverable: false
      },
      {
        level: 'info' as const,
        category: 'system' as const,
        message: '自动保存完成',
        details: '仿真状态已保存到本地存储',
        recoverable: false
      }
    ];
    
    const errorType = errorTypes[Math.floor(Math.random() * errorTypes.length)];
    const nodeId = nodes.length > 0 ? nodes[Math.floor(Math.random() * nodes.length)].id : undefined;
    
    return {
      id: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: Date.now(),
      ...errorType,
      nodeId,
      componentType: nodeId ? nodes.find(n => n.id === nodeId)?.type : undefined,
      resolved: false,
      stackTrace: errorType.level === 'error' ? 'at SimulationEngine.step()\n  at PhysicalModel.update()\n  at Component.calculate()' : undefined
    };
  };
  
  // Update system health
  const updateSystemHealth = () => {
    const now = Date.now();
    const recentErrors = errorLogs.filter(log => 
      now - log.timestamp < 300000 && // Last 5 minutes
      log.level === 'error' && 
      !log.resolved
    );
    
    const recentWarnings = errorLogs.filter(log => 
      now - log.timestamp < 300000 && 
      log.level === 'warning' && 
      !log.resolved
    );
    
    const uptime = now - startTimeRef.current;
    const totalErrors = errorLogs.filter(log => log.level === 'error').length;
    const errorRate = totalErrors / (uptime / 3600000); // errors per hour
    
    let overall: SystemHealth['overall'] = 'healthy';
    if (recentErrors.length > 0) overall = 'error';
    else if (recentWarnings.length > 2) overall = 'warning';
    else if (recentWarnings.length > 0) overall = 'warning';
    
    const components = {
      simulation: recentErrors.some(e => e.category === 'simulation') ? 'error' as const : 
                 recentWarnings.some(e => e.category === 'simulation') ? 'warning' as const : 'healthy' as const,
      computation: recentErrors.some(e => e.category === 'computation') ? 'error' as const : 
                  recentWarnings.some(e => e.category === 'computation') ? 'warning' as const : 'healthy' as const,
      memory: recentErrors.some(e => e.category === 'memory') ? 'error' as const : 
             recentWarnings.some(e => e.category === 'memory') ? 'warning' as const : 'healthy' as const,
      network: recentErrors.some(e => e.category === 'network') ? 'error' as const : 
              recentWarnings.some(e => e.category === 'network') ? 'warning' as const : 'healthy' as const
    };
    
    setSystemHealth({
      overall,
      components,
      uptime,
      errorRate,
      lastCheck: now
    });
  };
  
  // Auto-generate errors for demonstration
  useEffect(() => {
    const interval = setInterval(() => {
      if (Math.random() < 0.3) { // 30% chance to generate an error
        const newError = generateSimulatedError();
        setErrorLogs(prev => [newError, ...prev].slice(0, 100)); // Keep last 100 errors
        errorCountRef.current++;
        
        // Auto-recovery for applicable errors
        if (autoRecovery && newError.recoverable && newError.level === 'error') {
          const strategy = recoveryStrategies.find(s => 
            s.autoApply && s.applicableErrors.some(e => newError.message.includes(e.split('_').join(' ')))
          );
          
          if (strategy) {
            setTimeout(() => {
              applyRecoveryStrategy(newError.id, strategy);
            }, 2000);
          }
        }
      }
    }, 10000); // Generate error every 10 seconds
    
    return () => clearInterval(interval);
  }, [autoRecovery]);
  
  // Update system health periodically
  useEffect(() => {
    const interval = setInterval(updateSystemHealth, 5000);
    return () => clearInterval(interval);
  }, [errorLogs]);
  
  // Apply recovery strategy
  const applyRecoveryStrategy = async (errorId: string, strategy: RecoveryStrategy) => {
    setRecoveryInProgress(true);
    
    try {
      const success = await strategy.action();
      
      if (success) {
        setErrorLogs(prev => prev.map(log => 
          log.id === errorId 
            ? { ...log, resolved: true, recoveryAction: strategy.name }
            : log
        ));
        
        // Add recovery success log
        const recoveryLog: ErrorLog = {
          id: `recovery_${Date.now()}`,
          timestamp: Date.now(),
          level: 'info',
          category: 'system',
          message: `恢复策略执行成功: ${strategy.name}`,
          details: `错误 ${errorId} 已通过 ${strategy.description} 成功恢复`,
          recoverable: false,
          resolved: true
        };
        
        setErrorLogs(prev => [recoveryLog, ...prev]);
      }
    } catch (error) {
      console.error('Recovery strategy failed:', error);
    } finally {
      setRecoveryInProgress(false);
    }
  };
  
  // Get level color
  const getLevelColor = (level: string): string => {
    switch (level) {
      case 'error': return '#ff4d4f';
      case 'warning': return '#faad14';
      case 'info': return '#1890ff';
      case 'debug': return '#52c41a';
      default: return '#d9d9d9';
    }
  };
  
  // Get level icon
  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'error': return <ExclamationCircleOutlined />;
      case 'warning': return <WarningOutlined />;
      case 'info': return <InfoCircleOutlined />;
      case 'debug': return <BugOutlined />;
      default: return <InfoCircleOutlined />;
    }
  };
  
  // Get health color
  const getHealthColor = (health: string): string => {
    switch (health) {
      case 'healthy': return '#52c41a';
      case 'warning': return '#faad14';
      case 'critical': return '#fa8c16';
      case 'error': return '#ff4d4f';
      default: return '#d9d9d9';
    }
  };
  
  // Filter errors based on level
  const filteredErrors = errorLogs.filter(log => {
    const levels = ['error', 'warning', 'info', 'debug'];
    const currentLevelIndex = levels.indexOf(logLevel);
    const logLevelIndex = levels.indexOf(log.level);
    return logLevelIndex <= currentLevelIndex;
  });
  
  // Error table columns
  const errorColumns = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 120,
      render: (timestamp: number) => new Date(timestamp).toLocaleTimeString()
    },
    {
      title: '级别',
      dataIndex: 'level',
      key: 'level',
      width: 80,
      render: (level: string) => (
        <Tag color={getLevelColor(level)} icon={getLevelIcon(level)}>
          {level.toUpperCase()}
        </Tag>
      )
    },
    {
      title: '类别',
      dataIndex: 'category',
      key: 'category',
      width: 100
    },
    {
      title: '消息',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true
    },
    {
      title: '组件',
      dataIndex: 'nodeId',
      key: 'nodeId',
      width: 100,
      render: (nodeId: string) => nodeId || '-'
    },
    {
      title: '状态',
      key: 'status',
      width: 100,
      render: (record: ErrorLog) => (
        <Space>
          {record.resolved ? (
            <Tag color="green" icon={<CheckCircleOutlined />}>已解决</Tag>
          ) : record.recoverable ? (
            <Tag color="orange" icon={<ClockCircleOutlined />}>可恢复</Tag>
          ) : (
            <Tag color="red">需处理</Tag>
          )}
        </Space>
      )
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (record: ErrorLog) => (
        <Space>
          <Button size="small" onClick={() => {
            setSelectedError(record);
            setIsModalVisible(true);
          }}>
            详情
          </Button>
          {record.recoverable && !record.resolved && (
            <Button 
              size="small" 
              type="primary"
              loading={recoveryInProgress}
              onClick={() => {
                const strategy = recoveryStrategies.find(s => 
                  s.applicableErrors.some(e => record.message.includes(e.split('_').join(' ')))
                );
                if (strategy) {
                  applyRecoveryStrategy(record.id, strategy);
                }
              }}
            >
              恢复
            </Button>
          )}
        </Space>
      )
    }
  ];
  
  // Export error logs
  const exportLogs = () => {
    const csvContent = [
      ['时间', '级别', '类别', '消息', '详情', '组件ID', '状态'].join(','),
      ...filteredErrors.map(log => [
        new Date(log.timestamp).toISOString(),
        log.level,
        log.category,
        `"${log.message}"`,
        `"${log.details || ''}"`,
        log.nodeId || '',
        log.resolved ? '已解决' : '未解决'
      ].join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `error_logs_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };
  
  // Clear resolved errors
  const clearResolvedErrors = () => {
    setErrorLogs(prev => prev.filter(log => !log.resolved));
  };
  
  const unresolvedErrors = errorLogs.filter(log => !log.resolved && log.level === 'error').length;
  const unresolvedWarnings = errorLogs.filter(log => !log.resolved && log.level === 'warning').length;
  
  return (
    <Card title="错误处理与恢复" size="small">
      {/* System Health Overview */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="系统状态"
              value={systemHealth.overall === 'healthy' ? '正常' : 
                     systemHealth.overall === 'warning' ? '警告' : 
                     systemHealth.overall === 'critical' ? '严重' : '错误'}
              valueStyle={{ color: getHealthColor(systemHealth.overall) }}
              prefix={systemHealth.overall === 'healthy' ? <CheckCircleOutlined /> : <WarningOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="未解决错误"
              value={unresolvedErrors}
              valueStyle={{ color: unresolvedErrors > 0 ? '#ff4d4f' : '#52c41a' }}
              prefix={<ExclamationCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="警告数量"
              value={unresolvedWarnings}
              valueStyle={{ color: unresolvedWarnings > 0 ? '#faad14' : '#52c41a' }}
              prefix={<WarningOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="运行时间"
              value={Math.floor(systemHealth.uptime / 60000)}
              suffix="分钟"
              valueStyle={{ color: '#1890ff' }}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>
      
      {/* Component Health */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={24}>
          <Card title="组件健康状态" size="small">
            <Row gutter={16}>
              {Object.entries(systemHealth.components).map(([component, health]) => (
                <Col span={6} key={component}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ 
                      width: 60, 
                      height: 60, 
                      borderRadius: '50%', 
                      backgroundColor: getHealthColor(health),
                      margin: '0 auto 8px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                      fontSize: '20px'
                    }}>
                      {health === 'healthy' ? <CheckCircleOutlined /> : <WarningOutlined />}
                    </div>
                    <div style={{ fontWeight: 'bold' }}>
                      {component === 'simulation' ? '仿真' :
                       component === 'computation' ? '计算' :
                       component === 'memory' ? '内存' : '网络'}
                    </div>
                    <div style={{ fontSize: '12px', color: '#666' }}>
                      {health === 'healthy' ? '正常' : health === 'warning' ? '警告' : '错误'}
                    </div>
                  </div>
                </Col>
              ))}
            </Row>
          </Card>
        </Col>
      </Row>
      
      {/* Controls */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <Space>
            <span>自动恢复:</span>
            <Switch checked={autoRecovery} onChange={setAutoRecovery} />
          </Space>
        </Col>
        <Col span={8}>
          <Space>
            <span>日志级别:</span>
            <Select value={logLevel} onChange={setLogLevel} style={{ width: 120 }}>
              <Option value="error">错误</Option>
              <Option value="warning">警告</Option>
              <Option value="info">信息</Option>
              <Option value="debug">调试</Option>
            </Select>
          </Space>
        </Col>
        <Col span={8}>
          <Space>
            <Button icon={<DownloadOutlined />} onClick={exportLogs}>
              导出日志
            </Button>
            <Button icon={<ClearOutlined />} onClick={clearResolvedErrors}>
              清理已解决
            </Button>
            <Button icon={<ReloadOutlined />} onClick={() => setErrorLogs([])}>
              清空所有
            </Button>
          </Space>
        </Col>
      </Row>
      
      {/* Error Logs Table */}
      <Table
        dataSource={filteredErrors}
        columns={errorColumns}
        rowKey="id"
        size="small"
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条记录`
        }}
        scroll={{ y: 400 }}
      />
      
      {/* Error Detail Modal */}
      <Modal
        title="错误详情"
        visible={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setIsModalVisible(false)}>
            关闭
          </Button>,
          selectedError?.recoverable && !selectedError?.resolved && (
            <Button 
              key="recover" 
              type="primary"
              loading={recoveryInProgress}
              onClick={() => {
                if (selectedError) {
                  const strategy = recoveryStrategies.find(s => 
                    s.applicableErrors.some(e => selectedError.message.includes(e.split('_').join(' ')))
                  );
                  if (strategy) {
                    applyRecoveryStrategy(selectedError.id, strategy);
                    setIsModalVisible(false);
                  }
                }
              }}
            >
              执行恢复
            </Button>
          )
        ]}
        width={800}
      >
        {selectedError && (
          <div>
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={12}>
                <div><strong>时间:</strong> {new Date(selectedError.timestamp).toLocaleString()}</div>
                <div><strong>级别:</strong> <Tag color={getLevelColor(selectedError.level)}>{selectedError.level.toUpperCase()}</Tag></div>
                <div><strong>类别:</strong> {selectedError.category}</div>
              </Col>
              <Col span={12}>
                <div><strong>组件ID:</strong> {selectedError.nodeId || '无'}</div>
                <div><strong>组件类型:</strong> {selectedError.componentType || '无'}</div>
                <div><strong>可恢复:</strong> {selectedError.recoverable ? '是' : '否'}</div>
              </Col>
            </Row>
            
            <Divider />
            
            <div style={{ marginBottom: 16 }}>
              <strong>错误消息:</strong>
              <div style={{ padding: '8px', backgroundColor: '#f5f5f5', borderRadius: '4px', marginTop: '8px' }}>
                {selectedError.message}
              </div>
            </div>
            
            {selectedError.details && (
              <div style={{ marginBottom: 16 }}>
                <strong>详细信息:</strong>
                <TextArea 
                  value={selectedError.details} 
                  readOnly 
                  rows={3} 
                  style={{ marginTop: '8px' }}
                />
              </div>
            )}
            
            {selectedError.stackTrace && (
              <div style={{ marginBottom: 16 }}>
                <strong>堆栈跟踪:</strong>
                <TextArea 
                  value={selectedError.stackTrace} 
                  readOnly 
                  rows={4} 
                  style={{ marginTop: '8px', fontFamily: 'monospace' }}
                />
              </div>
            )}
            
            {selectedError.recoveryAction && (
              <div>
                <strong>恢复操作:</strong>
                <div style={{ padding: '8px', backgroundColor: '#f6ffed', borderRadius: '4px', marginTop: '8px', color: '#52c41a' }}>
                  {selectedError.recoveryAction}
                </div>
              </div>
            )}
            
            {/* Available Recovery Strategies */}
            {selectedError.recoverable && !selectedError.resolved && (
              <div style={{ marginTop: 16 }}>
                <strong>可用恢复策略:</strong>
                <Timeline size="small" style={{ marginTop: 8 }}>
                  {recoveryStrategies
                    .filter(s => s.applicableErrors.some(e => selectedError.message.includes(e.split('_').join(' '))))
                    .sort((a, b) => a.priority - b.priority)
                    .map(strategy => (
                      <Timeline.Item key={strategy.id} color={strategy.autoApply ? 'green' : 'blue'}>
                        <div>
                          <strong>{strategy.name}</strong>
                          {strategy.autoApply && <Tag color="green" size="small" style={{ marginLeft: 8 }}>自动</Tag>}
                        </div>
                        <div style={{ fontSize: '12px', color: '#666' }}>{strategy.description}</div>
                      </Timeline.Item>
                    ))
                  }
                </Timeline>
              </div>
            )}
          </div>
        )}
      </Modal>
    </Card>
  );
};

export default SimulationErrorHandler;