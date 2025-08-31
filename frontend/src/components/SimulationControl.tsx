import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Button, Space, InputNumber, Select, Switch, Slider, Progress, Alert, Divider, Tooltip, Badge, Tag } from 'antd';
import { PlayCircleOutlined, PauseCircleOutlined, StopOutlined, StepForwardOutlined, ReloadOutlined, SettingOutlined, ClockCircleOutlined, ThunderboltOutlined } from '@ant-design/icons';
import { useModelingStore } from '../store/modelingStore';

interface SimulationConfig {
  timeStep: number; // seconds
  totalTime: number; // seconds
  solverType: 'euler' | 'rk4' | 'adaptive';
  tolerance: number;
  maxIterations: number;
  convergenceCriteria: number;
  enableLogging: boolean;
  logLevel: 'debug' | 'info' | 'warning' | 'error';
  outputInterval: number; // seconds
  realTimeMode: boolean;
  speedMultiplier: number;
}

interface SimulationState {
  status: 'idle' | 'running' | 'paused' | 'completed' | 'error';
  currentTime: number;
  progress: number;
  iterationsCount: number;
  lastError?: string;
  performance: {
    fps: number;
    avgStepTime: number;
    memoryUsage: number;
  };
}

const { Option } = Select;

const SimulationControl: React.FC = () => {
  const { nodes, edges } = useModelingStore();
  
  const [config, setConfig] = useState<SimulationConfig>({
    timeStep: 0.1,
    totalTime: 300,
    solverType: 'rk4',
    tolerance: 1e-6,
    maxIterations: 1000,
    convergenceCriteria: 1e-8,
    enableLogging: true,
    logLevel: 'info',
    outputInterval: 1.0,
    realTimeMode: false,
    speedMultiplier: 1.0
  });
  
  const [state, setState] = useState<SimulationState>({
    status: 'idle',
    currentTime: 0,
    progress: 0,
    iterationsCount: 0,
    performance: {
      fps: 0,
      avgStepTime: 0,
      memoryUsage: 0
    }
  });
  
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  
  // Validate simulation configuration
  const validateConfiguration = (): string[] => {
    const errors: string[] = [];
    
    if (nodes.length === 0) {
      errors.push('至少需要一个组件才能运行仿真');
    }
    
    if (config.timeStep <= 0) {
      errors.push('时间步长必须大于0');
    }
    
    if (config.totalTime <= 0) {
      errors.push('总仿真时间必须大于0');
    }
    
    if (config.timeStep > config.totalTime) {
      errors.push('时间步长不能大于总仿真时间');
    }
    
    if (config.tolerance <= 0) {
      errors.push('求解器容差必须大于0');
    }
    
    if (config.maxIterations <= 0) {
      errors.push('最大迭代次数必须大于0');
    }
    
    // Check for disconnected components
    const connectedNodes = new Set<string>();
    edges.forEach(edge => {
      connectedNodes.add(edge.source);
      connectedNodes.add(edge.target);
    });
    
    const disconnectedNodes = nodes.filter(node => !connectedNodes.has(node.id));
    if (disconnectedNodes.length > 0 && nodes.length > 1) {
      errors.push(`发现${disconnectedNodes.length}个未连接的组件`);
    }
    
    return errors;
  };
  
  // Update validation on configuration change
  useEffect(() => {
    const errors = validateConfiguration();
    setValidationErrors(errors);
  }, [config, nodes, edges]);
  
  // Simulate performance metrics
  useEffect(() => {
    if (state.status === 'running') {
      const interval = setInterval(() => {
        setState(prev => ({
          ...prev,
          currentTime: prev.currentTime + config.timeStep,
          progress: Math.min((prev.currentTime + config.timeStep) / config.totalTime * 100, 100),
          iterationsCount: prev.iterationsCount + 1,
          performance: {
            fps: 60 + Math.random() * 10 - 5,
            avgStepTime: config.timeStep * 1000 + Math.random() * 10,
            memoryUsage: 45 + Math.random() * 10
          }
        }));
      }, config.realTimeMode ? config.timeStep * 1000 / config.speedMultiplier : 50);
      
      return () => clearInterval(interval);
    }
  }, [state.status, config.timeStep, config.realTimeMode, config.speedMultiplier]);
  
  // Auto-complete simulation
  useEffect(() => {
    if (state.status === 'running' && state.currentTime >= config.totalTime) {
      setState(prev => ({ ...prev, status: 'completed', progress: 100 }));
    }
  }, [state.status, state.currentTime, config.totalTime]);
  
  // Control functions
  const startSimulation = () => {
    if (validationErrors.length > 0) return;
    
    setState(prev => ({
      ...prev,
      status: 'running',
      lastError: undefined
    }));
  };
  
  const pauseSimulation = () => {
    setState(prev => ({ ...prev, status: 'paused' }));
  };
  
  const resumeSimulation = () => {
    setState(prev => ({ ...prev, status: 'running' }));
  };
  
  const stopSimulation = () => {
    setState({
      status: 'idle',
      currentTime: 0,
      progress: 0,
      iterationsCount: 0,
      performance: {
        fps: 0,
        avgStepTime: 0,
        memoryUsage: 0
      }
    });
  };
  
  const stepSimulation = () => {
    if (state.status === 'running') return;
    
    setState(prev => ({
      ...prev,
      currentTime: Math.min(prev.currentTime + config.timeStep, config.totalTime),
      progress: Math.min((prev.currentTime + config.timeStep) / config.totalTime * 100, 100),
      iterationsCount: prev.iterationsCount + 1,
      status: prev.currentTime + config.timeStep >= config.totalTime ? 'completed' : 'paused'
    }));
  };
  
  const resetSimulation = () => {
    stopSimulation();
  };
  
  // Get status color
  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'running': return '#52c41a';
      case 'paused': return '#faad14';
      case 'completed': return '#1890ff';
      case 'error': return '#ff4d4f';
      default: return '#d9d9d9';
    }
  };
  
  // Get status text
  const getStatusText = (status: string): string => {
    switch (status) {
      case 'idle': return '空闲';
      case 'running': return '运行中';
      case 'paused': return '已暂停';
      case 'completed': return '已完成';
      case 'error': return '错误';
      default: return '未知';
    }
  };
  
  // Format time
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(1);
    return `${mins}:${secs.padStart(4, '0')}`;
  };
  
  return (
    <Card title="仿真控制" size="small">
      {/* Status and Progress */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <Card size="small" title="仿真状态">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Badge color={getStatusColor(state.status)} text={getStatusText(state.status)} />
              </div>
              <Progress 
                percent={state.progress} 
                size="small" 
                status={state.status === 'error' ? 'exception' : state.status === 'completed' ? 'success' : 'active'}
              />
              <div style={{ fontSize: '12px', color: '#666' }}>
                时间: {formatTime(state.currentTime)} / {formatTime(config.totalTime)}
              </div>
            </Space>
          </Card>
        </Col>
        
        <Col span={8}>
          <Card size="small" title="性能监控">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div style={{ fontSize: '12px' }}>
                <div>FPS: {state.performance.fps.toFixed(1)}</div>
                <div>步长时间: {state.performance.avgStepTime.toFixed(1)}ms</div>
                <div>内存使用: {state.performance.memoryUsage.toFixed(1)}%</div>
                <div>迭代次数: {state.iterationsCount}</div>
              </div>
            </Space>
          </Card>
        </Col>
        
        <Col span={8}>
          <Card size="small" title="系统信息">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div style={{ fontSize: '12px' }}>
                <div>组件数量: {nodes.length}</div>
                <div>连接数量: {edges.length}</div>
                <div>求解器: {config.solverType.toUpperCase()}</div>
                <div>时间步长: {config.timeStep}s</div>
              </div>
            </Space>
          </Card>
        </Col>
      </Row>
      
      {/* Validation Errors */}
      {validationErrors.length > 0 && (
        <Alert
          message="配置验证失败"
          description={
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              {validationErrors.map((error, index) => (
                <li key={index}>{error}</li>
              ))}
            </ul>
          }
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}
      
      {/* Control Buttons */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={24}>
          <Space size="middle">
            {state.status === 'idle' || state.status === 'completed' ? (
              <Tooltip title="开始仿真">
                <Button 
                  type="primary" 
                  icon={<PlayCircleOutlined />} 
                  onClick={startSimulation}
                  disabled={validationErrors.length > 0}
                  size="large"
                >
                  开始
                </Button>
              </Tooltip>
            ) : state.status === 'running' ? (
              <Tooltip title="暂停仿真">
                <Button 
                  icon={<PauseCircleOutlined />} 
                  onClick={pauseSimulation}
                  size="large"
                >
                  暂停
                </Button>
              </Tooltip>
            ) : (
              <Tooltip title="继续仿真">
                <Button 
                  type="primary" 
                  icon={<PlayCircleOutlined />} 
                  onClick={resumeSimulation}
                  size="large"
                >
                  继续
                </Button>
              </Tooltip>
            )}
            
            <Tooltip title="停止仿真">
              <Button 
                icon={<StopOutlined />} 
                onClick={stopSimulation}
                disabled={state.status === 'idle'}
                size="large"
              >
                停止
              </Button>
            </Tooltip>
            
            <Tooltip title="单步执行">
              <Button 
                icon={<StepForwardOutlined />} 
                onClick={stepSimulation}
                disabled={state.status === 'running' || state.status === 'completed'}
                size="large"
              >
                单步
              </Button>
            </Tooltip>
            
            <Tooltip title="重置仿真">
              <Button 
                icon={<ReloadOutlined />} 
                onClick={resetSimulation}
                size="large"
              >
                重置
              </Button>
            </Tooltip>
            
            <Divider type="vertical" />
            
            <Tooltip title="高级设置">
              <Button 
                icon={<SettingOutlined />} 
                onClick={() => setShowAdvanced(!showAdvanced)}
                type={showAdvanced ? 'primary' : 'default'}
              >
                高级设置
              </Button>
            </Tooltip>
          </Space>
        </Col>
      </Row>
      
      {/* Basic Configuration */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <div style={{ marginBottom: 8 }}>时间步长 (s)</div>
          <InputNumber
            value={config.timeStep}
            onChange={(value) => setConfig(prev => ({ ...prev, timeStep: value || 0.1 }))}
            min={0.001}
            max={10}
            step={0.01}
            style={{ width: '100%' }}
            disabled={state.status === 'running'}
          />
        </Col>
        
        <Col span={6}>
          <div style={{ marginBottom: 8 }}>总时间 (s)</div>
          <InputNumber
            value={config.totalTime}
            onChange={(value) => setConfig(prev => ({ ...prev, totalTime: value || 300 }))}
            min={1}
            max={86400}
            step={10}
            style={{ width: '100%' }}
            disabled={state.status === 'running'}
          />
        </Col>
        
        <Col span={6}>
          <div style={{ marginBottom: 8 }}>求解器类型</div>
          <Select
            value={config.solverType}
            onChange={(value) => setConfig(prev => ({ ...prev, solverType: value }))}
            style={{ width: '100%' }}
            disabled={state.status === 'running'}
          >
            <Option value="euler">欧拉法</Option>
            <Option value="rk4">四阶龙格-库塔</Option>
            <Option value="adaptive">自适应步长</Option>
          </Select>
        </Col>
        
        <Col span={6}>
          <div style={{ marginBottom: 8 }}>实时模式</div>
          <div>
            <Switch 
              checked={config.realTimeMode} 
              onChange={(checked) => setConfig(prev => ({ ...prev, realTimeMode: checked }))}
              disabled={state.status === 'running'}
            />
            <span style={{ marginLeft: 8 }}>{config.realTimeMode ? '开启' : '关闭'}</span>
          </div>
        </Col>
      </Row>
      
      {/* Advanced Configuration */}
      {showAdvanced && (
        <Card title="高级配置" size="small" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={8}>
              <div style={{ marginBottom: 8 }}>求解器容差</div>
              <InputNumber
                value={config.tolerance}
                onChange={(value) => setConfig(prev => ({ ...prev, tolerance: value || 1e-6 }))}
                min={1e-12}
                max={1e-3}
                step={1e-7}
                style={{ width: '100%' }}
                disabled={state.status === 'running'}
                formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              />
            </Col>
            
            <Col span={8}>
              <div style={{ marginBottom: 8 }}>最大迭代次数</div>
              <InputNumber
                value={config.maxIterations}
                onChange={(value) => setConfig(prev => ({ ...prev, maxIterations: value || 1000 }))}
                min={10}
                max={10000}
                step={100}
                style={{ width: '100%' }}
                disabled={state.status === 'running'}
              />
            </Col>
            
            <Col span={8}>
              <div style={{ marginBottom: 8 }}>收敛准则</div>
              <InputNumber
                value={config.convergenceCriteria}
                onChange={(value) => setConfig(prev => ({ ...prev, convergenceCriteria: value || 1e-8 }))}
                min={1e-15}
                max={1e-5}
                step={1e-9}
                style={{ width: '100%' }}
                disabled={state.status === 'running'}
                formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              />
            </Col>
          </Row>
          
          <Row gutter={16} style={{ marginTop: 16 }}>
            <Col span={8}>
              <div style={{ marginBottom: 8 }}>输出间隔 (s)</div>
              <InputNumber
                value={config.outputInterval}
                onChange={(value) => setConfig(prev => ({ ...prev, outputInterval: value || 1.0 }))}
                min={0.1}
                max={60}
                step={0.1}
                style={{ width: '100%' }}
                disabled={state.status === 'running'}
              />
            </Col>
            
            <Col span={8}>
              <div style={{ marginBottom: 8 }}>日志级别</div>
              <Select
                value={config.logLevel}
                onChange={(value) => setConfig(prev => ({ ...prev, logLevel: value }))}
                style={{ width: '100%' }}
                disabled={state.status === 'running'}
              >
                <Option value="debug">调试</Option>
                <Option value="info">信息</Option>
                <Option value="warning">警告</Option>
                <Option value="error">错误</Option>
              </Select>
            </Col>
            
            <Col span={8}>
              <div style={{ marginBottom: 8 }}>启用日志</div>
              <div>
                <Switch 
                  checked={config.enableLogging} 
                  onChange={(checked) => setConfig(prev => ({ ...prev, enableLogging: checked }))}
                  disabled={state.status === 'running'}
                />
                <span style={{ marginLeft: 8 }}>{config.enableLogging ? '开启' : '关闭'}</span>
              </div>
            </Col>
          </Row>
          
          {config.realTimeMode && (
            <Row gutter={16} style={{ marginTop: 16 }}>
              <Col span={24}>
                <div style={{ marginBottom: 8 }}>速度倍数: {config.speedMultiplier}x</div>
                <Slider
                  value={config.speedMultiplier}
                  onChange={(value) => setConfig(prev => ({ ...prev, speedMultiplier: value }))}
                  min={0.1}
                  max={10}
                  step={0.1}
                  marks={{
                    0.1: '0.1x',
                    0.5: '0.5x',
                    1: '1x',
                    2: '2x',
                    5: '5x',
                    10: '10x'
                  }}
                  disabled={state.status === 'running'}
                />
              </Col>
            </Row>
          )}
        </Card>
      )}
      
      {/* Quick Actions */}
      <Row gutter={16}>
        <Col span={24}>
          <Card title="快速配置" size="small">
            <Space wrap>
              <Tag.CheckableTag
                checked={config.timeStep === 0.01 && config.totalTime === 60}
                onChange={() => setConfig(prev => ({ ...prev, timeStep: 0.01, totalTime: 60 }))}
              >
                <ClockCircleOutlined /> 精细仿真 (0.01s, 1min)
              </Tag.CheckableTag>
              
              <Tag.CheckableTag
                checked={config.timeStep === 0.1 && config.totalTime === 300}
                onChange={() => setConfig(prev => ({ ...prev, timeStep: 0.1, totalTime: 300 }))}
              >
                <ClockCircleOutlined /> 标准仿真 (0.1s, 5min)
              </Tag.CheckableTag>
              
              <Tag.CheckableTag
                checked={config.timeStep === 1.0 && config.totalTime === 3600}
                onChange={() => setConfig(prev => ({ ...prev, timeStep: 1.0, totalTime: 3600 }))}
              >
                <ClockCircleOutlined /> 长时间仿真 (1s, 1h)
              </Tag.CheckableTag>
              
              <Tag.CheckableTag
                checked={config.realTimeMode && config.speedMultiplier === 1.0}
                onChange={() => setConfig(prev => ({ ...prev, realTimeMode: true, speedMultiplier: 1.0 }))}
              >
                <ThunderboltOutlined /> 实时模式
              </Tag.CheckableTag>
              
              <Tag.CheckableTag
                checked={config.solverType === 'adaptive'}
                onChange={() => setConfig(prev => ({ ...prev, solverType: 'adaptive' }))}
              >
                <SettingOutlined /> 自适应求解
              </Tag.CheckableTag>
            </Space>
          </Card>
        </Col>
      </Row>
    </Card>
  );
};

export default SimulationControl;