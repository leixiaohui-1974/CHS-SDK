import React, { useEffect, useState } from 'react';
import { Layout, Menu, Card, Row, Col, Button, Space, Alert, Spin, Modal, message } from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  SettingOutlined,
  BarChartOutlined,
  MonitorOutlined,
  BugOutlined,
  ExperimentOutlined,
  CloudServerOutlined,
  DashboardOutlined,
  FileTextOutlined,
  DownloadOutlined
} from '@ant-design/icons';
import { useSimulationStore, simulationSelectors, SimulationState } from '../stores/simulationStore';
import { ConnectionState } from '../services/websocketManager';
import ModelingCanvas from './ModelingCanvas';
import SimulationEngine from './SimulationEngine';
import SimulationDataFlow from './SimulationDataFlow';
import SimulationControl from './SimulationControl';
import SimulationVisualization from './SimulationVisualization';
import SimulationPerformance from './SimulationPerformance';
import SimulationErrorHandler from './SimulationErrorHandler';
import SimulationTesting from './SimulationTesting';

const { Header, Sider, Content } = Layout;
const { SubMenu } = Menu;

// 菜单项类型
type MenuKey = 'modeling' | 'engine' | 'dataflow' | 'control' | 'visualization' | 'performance' | 'errors' | 'testing';

// 状态指示器组件
const StatusIndicator: React.FC = () => {
  const currentState = useSimulationStore(simulationSelectors.getCurrentState);
  const connectionState = useSimulationStore(simulationSelectors.getConnectionState);
  const isLoading = useSimulationStore(simulationSelectors.getIsLoading);
  const errors = useSimulationStore(simulationSelectors.getUnresolvedErrors);
  const performance = useSimulationStore(simulationSelectors.getPerformance);

  const getStateColor = (state: SimulationState) => {
    switch (state) {
      case SimulationState.RUNNING:
        return '#52c41a';
      case SimulationState.PAUSED:
        return '#faad14';
      case SimulationState.ERROR:
        return '#ff4d4f';
      case SimulationState.STOPPED:
        return '#d9d9d9';
      default:
        return '#1890ff';
    }
  };

  const getConnectionColor = (state: ConnectionState) => {
    switch (state) {
      case ConnectionState.CONNECTED:
        return '#52c41a';
      case ConnectionState.CONNECTING:
      case ConnectionState.RECONNECTING:
        return '#faad14';
      case ConnectionState.ERROR:
        return '#ff4d4f';
      default:
        return '#d9d9d9';
    }
  };

  return (
    <Space size="large" style={{ color: 'white' }}>
      <Space>
        <div
          style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            backgroundColor: getStateColor(currentState)
          }}
        />
        <span>仿真状态: {currentState}</span>
        {isLoading && <Spin size="small" />}
      </Space>
      
      <Space>
        <div
          style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            backgroundColor: getConnectionColor(connectionState)
          }}
        />
        <span>连接状态: {connectionState}</span>
      </Space>
      
      {errors.length > 0 && (
        <Space>
          <BugOutlined style={{ color: '#ff4d4f' }} />
          <span style={{ color: '#ff4d4f' }}>{errors.length} 个错误</span>
        </Space>
      )}
      
      <Space>
        <MonitorOutlined />
        <span>FPS: {performance.fps.toFixed(1)}</span>
      </Space>
      
      <Space>
        <DashboardOutlined />
        <span>延迟: {performance.latency.toFixed(0)}ms</span>
      </Space>
    </Space>
  );
};

// 快速操作栏组件
const QuickActions: React.FC = () => {
  const { actions } = useSimulationStore();
  const canStart = useSimulationStore(simulationSelectors.getCanStart);
  const canPause = useSimulationStore(simulationSelectors.getCanPause);
  const canResume = useSimulationStore(simulationSelectors.getCanResume);
  const canStop = useSimulationStore(simulationSelectors.getCanStop);
  const isLoading = useSimulationStore(simulationSelectors.getIsLoading);
  const currentSession = useSimulationStore(simulationSelectors.getCurrentSession);
  const historicalData = useSimulationStore(simulationSelectors.getHistoricalData);

  const handleStart = async () => {
    try {
      await actions.startSimulation();
      message.success('仿真已启动');
    } catch (error) {
      message.error('启动仿真失败');
    }
  };

  const handlePause = async () => {
    try {
      await actions.pauseSimulation();
      message.success('仿真已暂停');
    } catch (error) {
      message.error('暂停仿真失败');
    }
  };

  const handleResume = async () => {
    try {
      await actions.resumeSimulation();
      message.success('仿真已恢复');
    } catch (error) {
      message.error('恢复仿真失败');
    }
  };

  const handleStop = async () => {
    Modal.confirm({
      title: '确认停止仿真',
      content: '停止仿真将结束当前会话，确定要继续吗？',
      onOk: async () => {
        try {
          await actions.stopSimulation();
          message.success('仿真已停止');
        } catch (error) {
          message.error('停止仿真失败');
        }
      }
    });
  };

  const handleExportData = async (format: 'json' | 'csv' | 'excel') => {
    try {
      const blob = await actions.exportData(format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `simulation_data_${Date.now()}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      message.success(`数据已导出为 ${format.toUpperCase()} 格式`);
    } catch (error) {
      message.error('导出数据失败');
    }
  };

  return (
    <Space>
      {canStart && (
        <Button
          type="primary"
          icon={<PlayCircleOutlined />}
          onClick={handleStart}
          loading={isLoading}
        >
          启动
        </Button>
      )}
      
      {canPause && (
        <Button
          icon={<PauseCircleOutlined />}
          onClick={handlePause}
          loading={isLoading}
        >
          暂停
        </Button>
      )}
      
      {canResume && (
        <Button
          type="primary"
          icon={<PlayCircleOutlined />}
          onClick={handleResume}
          loading={isLoading}
        >
          恢复
        </Button>
      )}
      
      {canStop && (
        <Button
          danger
          icon={<StopOutlined />}
          onClick={handleStop}
          loading={isLoading}
        >
          停止
        </Button>
      )}
      
      {currentSession && (
        <Button
          icon={<SettingOutlined />}
          onClick={() => message.info('配置面板功能开发中')}
        >
          配置
        </Button>
      )}
      
      {historicalData && (
        <Button.Group>
          <Button
            icon={<DownloadOutlined />}
            onClick={() => handleExportData('json')}
          >
            JSON
          </Button>
          <Button
            icon={<DownloadOutlined />}
            onClick={() => handleExportData('csv')}
          >
            CSV
          </Button>
          <Button
            icon={<DownloadOutlined />}
            onClick={() => handleExportData('excel')}
          >
            Excel
          </Button>
        </Button.Group>
      )}
    </Space>
  );
};

// 主应用组件
const SimulationApp: React.FC = () => {
  const [selectedMenu, setSelectedMenu] = useState<MenuKey>('modeling');
  const [collapsed, setCollapsed] = useState(false);
  
  const { actions } = useSimulationStore();
  const error = useSimulationStore(simulationSelectors.getError);
  const errors = useSimulationStore(simulationSelectors.getUnresolvedErrors);
  const currentSession = useSimulationStore(simulationSelectors.getCurrentSession);
  const performance = useSimulationStore(simulationSelectors.getPerformance);

  // 性能监控
  useEffect(() => {
    const updatePerformance = () => {
      const now = performance.now();
      const memoryInfo = (performance as any).memory;
      
      actions.updatePerformance({
        fps: 60, // 简化的FPS计算
        latency: Math.random() * 50 + 10, // 模拟延迟
        memoryUsage: memoryInfo ? memoryInfo.usedJSHeapSize / 1024 / 1024 : 0,
        cpuUsage: Math.random() * 30 + 10, // 模拟CPU使用率
        networkBandwidth: Math.random() * 1000 + 500 // 模拟网络带宽
      });
    };

    const interval = setInterval(updatePerformance, 1000);
    return () => clearInterval(interval);
  }, [actions]);

  // 渲染内容区域
  const renderContent = () => {
    switch (selectedMenu) {
      case 'modeling':
        return <ModelingCanvas />;
      case 'engine':
        return <SimulationEngine />;
      case 'dataflow':
        return <SimulationDataFlow />;
      case 'control':
        return <SimulationControl />;
      case 'visualization':
        return <SimulationVisualization />;
      case 'performance':
        return <SimulationPerformance />;
      case 'errors':
        return <SimulationErrorHandler />;
      case 'testing':
        return <SimulationTesting />;
      default:
        return <ModelingCanvas />;
    }
  };

  return (
    <Layout style={{ height: '100vh' }}>
      {/* 头部 */}
      <Header style={{ 
        background: '#001529', 
        padding: '0 24px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div style={{ color: 'white', fontSize: '18px', fontWeight: 'bold' }}>
          <CloudServerOutlined style={{ marginRight: 8 }} />
          CHS仿真平台
        </div>
        
        <StatusIndicator />
        
        <QuickActions />
      </Header>

      <Layout>
        {/* 侧边栏 */}
        <Sider
          collapsible
          collapsed={collapsed}
          onCollapse={setCollapsed}
          theme="light"
          width={250}
        >
          <Menu
            mode="inline"
            selectedKeys={[selectedMenu]}
            style={{ height: '100%', borderRight: 0 }}
            onSelect={({ key }) => setSelectedMenu(key as MenuKey)}
          >
            <Menu.Item key="modeling" icon={<FileTextOutlined />}>
              模型建模
            </Menu.Item>
            
            <SubMenu key="simulation" icon={<ExperimentOutlined />} title="仿真执行">
              <Menu.Item key="engine" icon={<CloudServerOutlined />}>
                仿真引擎
              </Menu.Item>
              <Menu.Item key="dataflow" icon={<BarChartOutlined />}>
                数据流管理
              </Menu.Item>
              <Menu.Item key="control" icon={<SettingOutlined />}>
                仿真控制
              </Menu.Item>
            </SubMenu>
            
            <SubMenu key="monitoring" icon={<MonitorOutlined />} title="监控分析">
              <Menu.Item key="visualization" icon={<DashboardOutlined />}>
                结果可视化
              </Menu.Item>
              <Menu.Item key="performance" icon={<BarChartOutlined />}>
                性能监控
              </Menu.Item>
            </SubMenu>
            
            <SubMenu key="maintenance" icon={<BugOutlined />} title="维护测试">
              <Menu.Item key="errors" icon={<BugOutlined />}>
                错误处理
              </Menu.Item>
              <Menu.Item key="testing" icon={<ExperimentOutlined />}>
                集成测试
              </Menu.Item>
            </SubMenu>
          </Menu>
        </Sider>

        {/* 主内容区 */}
        <Layout style={{ padding: '0' }}>
          <Content style={{ 
            margin: 0, 
            minHeight: 280,
            background: '#f0f2f5',
            overflow: 'auto'
          }}>
            {/* 错误提示 */}
            {error && (
              <Alert
                message="系统错误"
                description={error}
                type="error"
                closable
                onClose={() => actions.reset()}
                style={{ margin: '16px 16px 0 16px' }}
              />
            )}
            
            {/* 未解决错误提示 */}
            {errors.length > 0 && (
              <Alert
                message={`发现 ${errors.length} 个未解决的错误`}
                description="请检查错误处理面板以获取详细信息"
                type="warning"
                action={
                  <Button 
                    size="small" 
                    onClick={() => setSelectedMenu('errors')}
                  >
                    查看详情
                  </Button>
                }
                closable
                style={{ margin: '16px 16px 0 16px' }}
              />
            )}
            
            {/* 会话信息 */}
            {currentSession && (
              <Card 
                size="small" 
                style={{ margin: '16px 16px 0 16px' }}
                bodyStyle={{ padding: '8px 16px' }}
              >
                <Row gutter={16}>
                  <Col span={6}>
                    <strong>会话ID:</strong> {currentSession.session_id}
                  </Col>
                  <Col span={6}>
                    <strong>创建时间:</strong> {new Date(currentSession.created_at).toLocaleString()}
                  </Col>
                  <Col span={6}>
                    <strong>状态:</strong> {currentSession.status}
                  </Col>
                  <Col span={6}>
                    <strong>配置:</strong> {currentSession.config ? '已加载' : '未配置'}
                  </Col>
                </Row>
              </Card>
            )}
            
            {/* 主要内容 */}
            <div style={{ padding: '16px' }}>
              {renderContent()}
            </div>
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
};

export default SimulationApp;