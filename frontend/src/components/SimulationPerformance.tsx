import React, { useState, useEffect, useRef } from 'react';
import { Card, Row, Col, Progress, Statistic, Switch, Select, Slider, Button, Space, Alert, Tabs, Table, Tag } from 'antd';
import { ThunderboltOutlined, MemoryOutlined, ClockCircleOutlined, OptimizationOutlined, WarningOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';

interface PerformanceMetrics {
  timestamp: number;
  fps: number;
  stepTime: number; // ms
  memoryUsage: number; // MB
  cpuUsage: number; // %
  gpuUsage?: number; // %
  networkLatency?: number; // ms
  cacheHitRate: number; // %
  parallelEfficiency: number; // %
}

interface OptimizationConfig {
  enableParallelComputation: boolean;
  workerThreads: number;
  enableMemoryOptimization: boolean;
  cacheSize: number; // MB
  enableGPUAcceleration: boolean;
  batchSize: number;
  enableAdaptiveTimeStep: boolean;
  enableDataCompression: boolean;
  compressionLevel: number;
  enablePredictiveLoading: boolean;
}

interface BottleneckInfo {
  type: 'cpu' | 'memory' | 'network' | 'disk' | 'algorithm';
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  suggestion: string;
  impact: number; // 0-100
}

const { Option } = Select;
const { TabPane } = Tabs;

const SimulationPerformance: React.FC = () => {
  const [metrics, setMetrics] = useState<PerformanceMetrics[]>([]);
  const [config, setConfig] = useState<OptimizationConfig>({
    enableParallelComputation: true,
    workerThreads: navigator.hardwareConcurrency || 4,
    enableMemoryOptimization: true,
    cacheSize: 256,
    enableGPUAcceleration: false,
    batchSize: 100,
    enableAdaptiveTimeStep: false,
    enableDataCompression: true,
    compressionLevel: 6,
    enablePredictiveLoading: true
  });
  
  const [bottlenecks, setBottlenecks] = useState<BottleneckInfo[]>([]);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [optimizationScore, setOptimizationScore] = useState(75);
  const [activeTab, setActiveTab] = useState('realtime');
  
  const metricsBufferRef = useRef<PerformanceMetrics[]>([]);
  const maxMetricsPoints = 300;
  
  // Generate simulated performance data
  const generateMetrics = (): PerformanceMetrics => {
    const baseTime = Date.now();
    const cpuLoad = config.enableParallelComputation ? 0.6 : 0.8;
    const memoryEfficiency = config.enableMemoryOptimization ? 0.7 : 0.9;
    
    return {
      timestamp: baseTime,
      fps: 60 + (config.enableParallelComputation ? 10 : -5) + Math.random() * 10 - 5,
      stepTime: (config.enableParallelComputation ? 8 : 15) + Math.random() * 5,
      memoryUsage: (200 * memoryEfficiency) + Math.random() * 50,
      cpuUsage: (cpuLoad * 100) + Math.random() * 20,
      gpuUsage: config.enableGPUAcceleration ? 30 + Math.random() * 20 : undefined,
      networkLatency: 10 + Math.random() * 20,
      cacheHitRate: config.enableMemoryOptimization ? 85 + Math.random() * 10 : 60 + Math.random() * 15,
      parallelEfficiency: config.enableParallelComputation ? 80 + Math.random() * 15 : 0
    };
  };
  
  // Analyze bottlenecks
  const analyzeBottlenecks = (currentMetrics: PerformanceMetrics): BottleneckInfo[] => {
    const bottlenecks: BottleneckInfo[] = [];
    
    if (currentMetrics.cpuUsage > 90) {
      bottlenecks.push({
        type: 'cpu',
        severity: 'high',
        description: 'CPU使用率过高',
        suggestion: '启用并行计算或增加工作线程数',
        impact: 85
      });
    }
    
    if (currentMetrics.memoryUsage > 500) {
      bottlenecks.push({
        type: 'memory',
        severity: 'medium',
        description: '内存使用量较高',
        suggestion: '启用内存优化或减少缓存大小',
        impact: 60
      });
    }
    
    if (currentMetrics.stepTime > 20) {
      bottlenecks.push({
        type: 'algorithm',
        severity: 'medium',
        description: '计算步长时间过长',
        suggestion: '启用自适应时间步长或GPU加速',
        impact: 70
      });
    }
    
    if (currentMetrics.cacheHitRate < 70) {
      bottlenecks.push({
        type: 'memory',
        severity: 'low',
        description: '缓存命中率较低',
        suggestion: '增加缓存大小或启用预测加载',
        impact: 40
      });
    }
    
    if (currentMetrics.networkLatency && currentMetrics.networkLatency > 50) {
      bottlenecks.push({
        type: 'network',
        severity: 'medium',
        description: '网络延迟较高',
        suggestion: '启用数据压缩或本地缓存',
        impact: 50
      });
    }
    
    return bottlenecks;
  };
  
  // Calculate optimization score
  const calculateOptimizationScore = (metrics: PerformanceMetrics, config: OptimizationConfig): number => {
    let score = 100;
    
    // Performance penalties
    if (metrics.cpuUsage > 80) score -= 20;
    if (metrics.memoryUsage > 400) score -= 15;
    if (metrics.stepTime > 15) score -= 15;
    if (metrics.cacheHitRate < 75) score -= 10;
    
    // Optimization bonuses
    if (config.enableParallelComputation) score += 10;
    if (config.enableMemoryOptimization) score += 8;
    if (config.enableGPUAcceleration) score += 12;
    if (config.enableDataCompression) score += 5;
    if (config.enablePredictiveLoading) score += 5;
    
    return Math.max(0, Math.min(100, score));
  };
  
  // Monitor performance
  useEffect(() => {
    if (!isMonitoring) return;
    
    const interval = setInterval(() => {
      const newMetrics = generateMetrics();
      
      metricsBufferRef.current.push(newMetrics);
      if (metricsBufferRef.current.length > maxMetricsPoints) {
        metricsBufferRef.current = metricsBufferRef.current.slice(-maxMetricsPoints);
      }
      
      setMetrics([...metricsBufferRef.current]);
      setBottlenecks(analyzeBottlenecks(newMetrics));
      setOptimizationScore(calculateOptimizationScore(newMetrics, config));
    }, 1000);
    
    return () => clearInterval(interval);
  }, [isMonitoring, config]);
  
  // Get severity color
  const getSeverityColor = (severity: string): string => {
    switch (severity) {
      case 'low': return '#52c41a';
      case 'medium': return '#faad14';
      case 'high': return '#fa8c16';
      case 'critical': return '#ff4d4f';
      default: return '#d9d9d9';
    }
  };
  
  // Get optimization score color
  const getScoreColor = (score: number): string => {
    if (score >= 80) return '#52c41a';
    if (score >= 60) return '#faad14';
    if (score >= 40) return '#fa8c16';
    return '#ff4d4f';
  };
  
  // Format chart data
  const chartData = metrics.slice(-60).map(m => ({
    time: new Date(m.timestamp).toLocaleTimeString(),
    FPS: m.fps,
    'CPU使用率': m.cpuUsage,
    '内存使用': m.memoryUsage,
    '步长时间': m.stepTime,
    '缓存命中率': m.cacheHitRate,
    '并行效率': m.parallelEfficiency
  }));
  
  // Bottleneck table columns
  const bottleneckColumns = [
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => {
        const icons = {
          cpu: <ThunderboltOutlined />,
          memory: <MemoryOutlined />,
          network: <ClockCircleOutlined />,
          disk: <ClockCircleOutlined />,
          algorithm: <OptimizationOutlined />
        };
        return <span>{icons[type as keyof typeof icons]} {type.toUpperCase()}</span>;
      }
    },
    {
      title: '严重程度',
      dataIndex: 'severity',
      key: 'severity',
      render: (severity: string) => (
        <Tag color={getSeverityColor(severity)}>
          {severity === 'low' ? '低' : severity === 'medium' ? '中' : severity === 'high' ? '高' : '严重'}
        </Tag>
      )
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description'
    },
    {
      title: '建议',
      dataIndex: 'suggestion',
      key: 'suggestion'
    },
    {
      title: '影响',
      dataIndex: 'impact',
      key: 'impact',
      render: (impact: number) => (
        <Progress percent={impact} size="small" strokeColor={getSeverityColor(impact > 70 ? 'high' : impact > 40 ? 'medium' : 'low')} />
      )
    }
  ];
  
  const currentMetrics = metrics[metrics.length - 1];
  
  return (
    <Card title="性能优化" size="small">
      {/* Control Panel */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Space>
            <span>性能监控:</span>
            <Switch checked={isMonitoring} onChange={setIsMonitoring} />
          </Space>
        </Col>
        <Col span={6}>
          <Statistic
            title="优化评分"
            value={optimizationScore}
            suffix="/100"
            valueStyle={{ color: getScoreColor(optimizationScore) }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="瓶颈数量"
            value={bottlenecks.length}
            prefix={bottlenecks.length > 0 ? <WarningOutlined /> : <CheckCircleOutlined />}
            valueStyle={{ color: bottlenecks.length > 0 ? '#fa8c16' : '#52c41a' }}
          />
        </Col>
        <Col span={6}>
          <Button type="primary" icon={<OptimizationOutlined />} onClick={() => {
            // Auto-optimize based on current bottlenecks
            const newConfig = { ...config };
            bottlenecks.forEach(bottleneck => {
              if (bottleneck.type === 'cpu' && !newConfig.enableParallelComputation) {
                newConfig.enableParallelComputation = true;
              }
              if (bottleneck.type === 'memory' && !newConfig.enableMemoryOptimization) {
                newConfig.enableMemoryOptimization = true;
              }
            });
            setConfig(newConfig);
          }}>
            自动优化
          </Button>
        </Col>
      </Row>
      
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="实时监控" key="realtime">
          {/* Real-time Metrics */}
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title="FPS"
                  value={currentMetrics?.fps || 0}
                  precision={1}
                  prefix={<ThunderboltOutlined />}
                  valueStyle={{ color: (currentMetrics?.fps || 0) > 50 ? '#52c41a' : '#fa8c16' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title="步长时间"
                  value={currentMetrics?.stepTime || 0}
                  precision={1}
                  suffix="ms"
                  prefix={<ClockCircleOutlined />}
                  valueStyle={{ color: (currentMetrics?.stepTime || 0) < 15 ? '#52c41a' : '#fa8c16' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title="内存使用"
                  value={currentMetrics?.memoryUsage || 0}
                  precision={1}
                  suffix="MB"
                  prefix={<MemoryOutlined />}
                  valueStyle={{ color: (currentMetrics?.memoryUsage || 0) < 400 ? '#52c41a' : '#fa8c16' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title="CPU使用率"
                  value={currentMetrics?.cpuUsage || 0}
                  precision={1}
                  suffix="%"
                  prefix={<ThunderboltOutlined />}
                  valueStyle={{ color: (currentMetrics?.cpuUsage || 0) < 80 ? '#52c41a' : '#fa8c16' }}
                />
              </Card>
            </Col>
          </Row>
          
          {/* Performance Charts */}
          <Row gutter={16}>
            <Col span={12}>
              <Card title="性能指标" size="small">
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="FPS" stroke="#1890ff" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="步长时间" stroke="#52c41a" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </Card>
            </Col>
            <Col span={12}>
              <Card title="资源使用" size="small">
                <ResponsiveContainer width="100%" height={250}>
                  <AreaChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Area type="monotone" dataKey="CPU使用率" stackId="1" stroke="#fa8c16" fill="#fa8c16" fillOpacity={0.6} />
                    <Area type="monotone" dataKey="缓存命中率" stackId="2" stroke="#722ed1" fill="#722ed1" fillOpacity={0.6} />
                  </AreaChart>
                </ResponsiveContainer>
              </Card>
            </Col>
          </Row>
        </TabPane>
        
        <TabPane tab="优化配置" key="config">
          <Row gutter={16}>
            <Col span={12}>
              <Card title="并行计算" size="small">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Switch 
                      checked={config.enableParallelComputation} 
                      onChange={(checked) => setConfig(prev => ({ ...prev, enableParallelComputation: checked }))}
                    />
                    <span style={{ marginLeft: 8 }}>启用并行计算</span>
                  </div>
                  
                  <div>
                    <div style={{ marginBottom: 8 }}>工作线程数: {config.workerThreads}</div>
                    <Slider
                      value={config.workerThreads}
                      onChange={(value) => setConfig(prev => ({ ...prev, workerThreads: value }))}
                      min={1}
                      max={navigator.hardwareConcurrency * 2 || 8}
                      marks={{
                        1: '1',
                        [navigator.hardwareConcurrency || 4]: '推荐',
                        [navigator.hardwareConcurrency * 2 || 8]: '最大'
                      }}
                      disabled={!config.enableParallelComputation}
                    />
                  </div>
                  
                  <div>
                    <div style={{ marginBottom: 8 }}>批处理大小: {config.batchSize}</div>
                    <Slider
                      value={config.batchSize}
                      onChange={(value) => setConfig(prev => ({ ...prev, batchSize: value }))}
                      min={10}
                      max={1000}
                      step={10}
                      marks={{
                        10: '10',
                        100: '100',
                        500: '500',
                        1000: '1000'
                      }}
                    />
                  </div>
                </Space>
              </Card>
            </Col>
            
            <Col span={12}>
              <Card title="内存优化" size="small">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Switch 
                      checked={config.enableMemoryOptimization} 
                      onChange={(checked) => setConfig(prev => ({ ...prev, enableMemoryOptimization: checked }))}
                    />
                    <span style={{ marginLeft: 8 }}>启用内存优化</span>
                  </div>
                  
                  <div>
                    <div style={{ marginBottom: 8 }}>缓存大小: {config.cacheSize}MB</div>
                    <Slider
                      value={config.cacheSize}
                      onChange={(value) => setConfig(prev => ({ ...prev, cacheSize: value }))}
                      min={64}
                      max={2048}
                      step={64}
                      marks={{
                        64: '64MB',
                        256: '256MB',
                        512: '512MB',
                        1024: '1GB',
                        2048: '2GB'
                      }}
                      disabled={!config.enableMemoryOptimization}
                    />
                  </div>
                  
                  <div>
                    <Switch 
                      checked={config.enablePredictiveLoading} 
                      onChange={(checked) => setConfig(prev => ({ ...prev, enablePredictiveLoading: checked }))}
                    />
                    <span style={{ marginLeft: 8 }}>启用预测加载</span>
                  </div>
                </Space>
              </Card>
            </Col>
          </Row>
          
          <Row gutter={16} style={{ marginTop: 16 }}>
            <Col span={12}>
              <Card title="GPU加速" size="small">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Switch 
                      checked={config.enableGPUAcceleration} 
                      onChange={(checked) => setConfig(prev => ({ ...prev, enableGPUAcceleration: checked }))}
                    />
                    <span style={{ marginLeft: 8 }}>启用GPU加速</span>
                  </div>
                  
                  {config.enableGPUAcceleration && (
                    <Alert
                      message="GPU加速已启用"
                      description="将使用WebGL进行并行计算，可显著提升大规模仿真性能。"
                      type="info"
                      showIcon
                    />
                  )}
                </Space>
              </Card>
            </Col>
            
            <Col span={12}>
              <Card title="其他优化" size="small">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Switch 
                      checked={config.enableAdaptiveTimeStep} 
                      onChange={(checked) => setConfig(prev => ({ ...prev, enableAdaptiveTimeStep: checked }))}
                    />
                    <span style={{ marginLeft: 8 }}>自适应时间步长</span>
                  </div>
                  
                  <div>
                    <Switch 
                      checked={config.enableDataCompression} 
                      onChange={(checked) => setConfig(prev => ({ ...prev, enableDataCompression: checked }))}
                    />
                    <span style={{ marginLeft: 8 }}>数据压缩</span>
                  </div>
                  
                  {config.enableDataCompression && (
                    <div>
                      <div style={{ marginBottom: 8 }}>压缩级别: {config.compressionLevel}</div>
                      <Slider
                        value={config.compressionLevel}
                        onChange={(value) => setConfig(prev => ({ ...prev, compressionLevel: value }))}
                        min={1}
                        max={9}
                        marks={{
                          1: '快速',
                          5: '平衡',
                          9: '最佳'
                        }}
                      />
                    </div>
                  )}
                </Space>
              </Card>
            </Col>
          </Row>
        </TabPane>
        
        <TabPane tab="瓶颈分析" key="bottlenecks">
          {bottlenecks.length === 0 ? (
            <Alert
              message="性能良好"
              description="当前未检测到明显的性能瓶颈。"
              type="success"
              showIcon
            />
          ) : (
            <Table
              dataSource={bottlenecks}
              columns={bottleneckColumns}
              rowKey={(record, index) => `${record.type}_${index}`}
              size="small"
              pagination={false}
            />
          )}
          
          <Card title="性能建议" size="small" style={{ marginTop: 16 }}>
            <div style={{ fontSize: '12px', lineHeight: '1.6' }}>
              <h4>通用优化建议：</h4>
              <ul>
                <li>对于CPU密集型计算，启用并行计算可提升30-50%性能</li>
                <li>合理设置缓存大小，避免内存不足或浪费</li>
                <li>GPU加速适用于大规模矩阵运算和并行计算</li>
                <li>自适应时间步长可在保证精度的同时提升计算效率</li>
                <li>数据压缩可减少网络传输时间和存储空间</li>
                <li>预测加载可减少等待时间，提升用户体验</li>
              </ul>
            </div>
          </Card>
        </TabPane>
      </Tabs>
    </Card>
  );
};

export default SimulationPerformance;