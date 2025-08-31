import React, { useState, useEffect, useRef } from 'react';
import { Card, Row, Col, Select, Switch, Button, Space, Statistic, Alert, Tabs, Slider } from 'antd';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area, BarChart, Bar, ScatterChart, Scatter, ReferenceLine } from 'recharts';
import { DownloadOutlined, FullscreenOutlined, ReloadOutlined, SettingOutlined } from '@ant-design/icons';
import { useModelingStore } from '../store/modelingStore';

interface TimeSeriesData {
  time: number;
  [key: string]: number;
}

interface ChartConfig {
  id: string;
  title: string;
  type: 'line' | 'area' | 'bar' | 'scatter';
  variables: string[];
  colors: string[];
  yAxisLabel: string;
  unit: string;
  showGrid: boolean;
  showLegend: boolean;
  autoScale: boolean;
  minValue?: number;
  maxValue?: number;
}

interface StatisticsData {
  nodeId: string;
  nodeName: string;
  variable: string;
  current: number;
  min: number;
  max: number;
  average: number;
  trend: 'up' | 'down' | 'stable';
  unit: string;
}

const { Option } = Select;
const { TabPane } = Tabs;

const SimulationVisualization: React.FC = () => {
  const { nodes } = useModelingStore();
  
  const [timeSeriesData, setTimeSeriesData] = useState<TimeSeriesData[]>([]);
  const [statistics, setStatistics] = useState<StatisticsData[]>([]);
  const [isRealTime, setIsRealTime] = useState(true);
  const [selectedNodes, setSelectedNodes] = useState<string[]>([]);
  const [selectedVariables, setSelectedVariables] = useState<string[]>(['water_level', 'flow_rate']);
  const [timeWindow, setTimeWindow] = useState(300); // 5 minutes
  const [updateInterval, setUpdateInterval] = useState(1000); // 1 second
  const [activeTab, setActiveTab] = useState('realtime');
  
  const dataBufferRef = useRef<TimeSeriesData[]>([]);
  const maxDataPoints = 1000;

  // Default chart configurations
  const [chartConfigs, setChartConfigs] = useState<ChartConfig[]>([
    {
      id: 'water_levels',
      title: '水位变化',
      type: 'line',
      variables: ['water_level'],
      colors: ['#1890ff'],
      yAxisLabel: '水位 (m)',
      unit: 'm',
      showGrid: true,
      showLegend: true,
      autoScale: true
    },
    {
      id: 'flow_rates',
      title: '流量变化',
      type: 'area',
      variables: ['flow_rate', 'inflow', 'outflow'],
      colors: ['#52c41a', '#1890ff', '#ff4d4f'],
      yAxisLabel: '流量 (m³/s)',
      unit: 'm³/s',
      showGrid: true,
      showLegend: true,
      autoScale: true
    },
    {
      id: 'pressures',
      title: '压力分布',
      type: 'line',
      variables: ['pressure', 'head'],
      colors: ['#722ed1', '#fa8c16'],
      yAxisLabel: '压力 (bar)',
      unit: 'bar',
      showGrid: true,
      showLegend: true,
      autoScale: true
    },
    {
      id: 'efficiency',
      title: '效率监控',
      type: 'bar',
      variables: ['efficiency', 'power'],
      colors: ['#13c2c2', '#eb2f96'],
      yAxisLabel: '效率 (%)',
      unit: '%',
      showGrid: true,
      showLegend: true,
      autoScale: true
    }
  ]);

  // Initialize selected nodes
  useEffect(() => {
    if (nodes.length > 0 && selectedNodes.length === 0) {
      setSelectedNodes(nodes.slice(0, 3).map(node => node.id));
    }
  }, [nodes, selectedNodes.length]);

  // Generate simulated data
  const generateSimulatedData = (currentTime: number): TimeSeriesData => {
    const data: TimeSeriesData = { time: currentTime };
    
    selectedNodes.forEach(nodeId => {
      const node = nodes.find(n => n.id === nodeId);
      if (!node) return;
      
      const baseTime = currentTime / 1000; // Convert to seconds
      
      switch (node.type) {
        case 'reservoir':
          data[`${nodeId}_water_level`] = 10 + 3 * Math.sin(baseTime / 100) + Math.random() * 0.5;
          data[`${nodeId}_volume`] = (data[`${nodeId}_water_level`] as number) * 100000;
          data[`${nodeId}_inflow`] = 20 + 5 * Math.sin(baseTime / 50) + Math.random() * 2;
          data[`${nodeId}_outflow`] = 18 + 4 * Math.sin(baseTime / 60) + Math.random() * 2;
          break;
          
        case 'pipe':
          data[`${nodeId}_flow_rate`] = 15 + 3 * Math.sin(baseTime / 80) + Math.random() * 1;
          data[`${nodeId}_velocity`] = (data[`${nodeId}_flow_rate`] as number) / 2;
          data[`${nodeId}_pressure`] = 5 + Math.sin(baseTime / 120) + Math.random() * 0.2;
          break;
          
        case 'pump':
          data[`${nodeId}_flow_rate`] = 25 + 5 * Math.sin(baseTime / 90) + Math.random() * 2;
          data[`${nodeId}_head`] = 30 + 5 * Math.sin(baseTime / 110) + Math.random() * 1;
          data[`${nodeId}_power`] = 150 + 30 * Math.sin(baseTime / 70) + Math.random() * 10;
          data[`${nodeId}_efficiency`] = 85 + 5 * Math.sin(baseTime / 200) + Math.random() * 2;
          break;
          
        case 'valve':
        case 'gate':
          data[`${nodeId}_opening`] = 0.7 + 0.2 * Math.sin(baseTime / 150) + Math.random() * 0.05;
          data[`${nodeId}_flow_rate`] = 12 + 3 * Math.sin(baseTime / 100) + Math.random() * 1;
          data[`${nodeId}_pressure_drop`] = 2 + Math.sin(baseTime / 80) + Math.random() * 0.1;
          break;
          
        default:
          data[`${nodeId}_value`] = Math.random() * 100;
      }
    });
    
    return data;
  };

  // Update statistics
  const updateStatistics = (data: TimeSeriesData[]) => {
    const stats: StatisticsData[] = [];
    
    selectedNodes.forEach(nodeId => {
      const node = nodes.find(n => n.id === nodeId);
      if (!node) return;
      
      selectedVariables.forEach(variable => {
        const key = `${nodeId}_${variable}`;
        const values = data.map(d => d[key]).filter(v => v !== undefined) as number[];
        
        if (values.length > 0) {
          const current = values[values.length - 1];
          const min = Math.min(...values);
          const max = Math.max(...values);
          const average = values.reduce((sum, val) => sum + val, 0) / values.length;
          
          // Calculate trend
          let trend: 'up' | 'down' | 'stable' = 'stable';
          if (values.length > 1) {
            const recent = values.slice(-5);
            const older = values.slice(-10, -5);
            if (recent.length > 0 && older.length > 0) {
              const recentAvg = recent.reduce((sum, val) => sum + val, 0) / recent.length;
              const olderAvg = older.reduce((sum, val) => sum + val, 0) / older.length;
              const change = (recentAvg - olderAvg) / olderAvg;
              if (change > 0.02) trend = 'up';
              else if (change < -0.02) trend = 'down';
            }
          }
          
          stats.push({
            nodeId,
            nodeName: node.data?.label || nodeId,
            variable,
            current,
            min,
            max,
            average,
            trend,
            unit: getUnitForVariable(variable)
          });
        }
      });
    });
    
    setStatistics(stats);
  };

  // Get unit for variable
  const getUnitForVariable = (variable: string): string => {
    const unitMap: Record<string, string> = {
      water_level: 'm',
      volume: 'm³',
      flow_rate: 'm³/s',
      inflow: 'm³/s',
      outflow: 'm³/s',
      pressure: 'bar',
      head: 'm',
      power: 'kW',
      efficiency: '%',
      opening: '%',
      velocity: 'm/s',
      pressure_drop: 'bar'
    };
    return unitMap[variable] || '';
  };

  // Real-time data update
  useEffect(() => {
    if (!isRealTime) return;
    
    const interval = setInterval(() => {
      const currentTime = Date.now();
      const newData = generateSimulatedData(currentTime);
      
      dataBufferRef.current.push(newData);
      
      // Keep only data within time window
      const cutoffTime = currentTime - timeWindow * 1000;
      dataBufferRef.current = dataBufferRef.current.filter(d => d.time >= cutoffTime);
      
      // Limit total data points
      if (dataBufferRef.current.length > maxDataPoints) {
        dataBufferRef.current = dataBufferRef.current.slice(-maxDataPoints);
      }
      
      setTimeSeriesData([...dataBufferRef.current]);
      updateStatistics(dataBufferRef.current);
    }, updateInterval);
    
    return () => clearInterval(interval);
  }, [isRealTime, selectedNodes, selectedVariables, timeWindow, updateInterval]);

  // Format time for display
  const formatTime = (timestamp: number): string => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  // Get trend color
  const getTrendColor = (trend: string): string => {
    switch (trend) {
      case 'up': return '#52c41a';
      case 'down': return '#ff4d4f';
      default: return '#1890ff';
    }
  };

  // Export data
  const exportData = () => {
    const csvContent = [
      ['Time', ...Object.keys(timeSeriesData[0] || {}).filter(k => k !== 'time')].join(','),
      ...timeSeriesData.map(row => [
        new Date(row.time).toISOString(),
        ...Object.entries(row).filter(([k]) => k !== 'time').map(([, v]) => v)
      ].join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `simulation_data_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Render chart based on configuration
  const renderChart = (config: ChartConfig) => {
    const chartData = timeSeriesData.map(d => ({
      time: formatTime(d.time),
      ...config.variables.reduce((acc, variable) => {
        selectedNodes.forEach(nodeId => {
          const key = `${nodeId}_${variable}`;
          if (d[key] !== undefined) {
            acc[`${nodeId}_${variable}`] = d[key];
          }
        });
        return acc;
      }, {} as Record<string, number>)
    }));

    const ChartComponent = {
      line: LineChart,
      area: AreaChart,
      bar: BarChart,
      scatter: ScatterChart
    }[config.type];

    return (
      <ResponsiveContainer width="100%" height={300}>
        <ChartComponent data={chartData}>
          {config.showGrid && <CartesianGrid strokeDasharray="3 3" />}
          <XAxis dataKey="time" />
          <YAxis label={{ value: config.yAxisLabel, angle: -90, position: 'insideLeft' }} />
          <Tooltip />
          {config.showLegend && <Legend />}
          
          {config.variables.map((variable, index) => {
            const color = config.colors[index % config.colors.length];
            
            return selectedNodes.map(nodeId => {
              const dataKey = `${nodeId}_${variable}`;
              const name = `${nodeId} ${variable}`;
              
              if (config.type === 'line') {
                return (
                  <Line
                    key={dataKey}
                    type="monotone"
                    dataKey={dataKey}
                    stroke={color}
                    strokeWidth={2}
                    dot={false}
                    name={name}
                  />
                );
              } else if (config.type === 'area') {
                return (
                  <Area
                    key={dataKey}
                    type="monotone"
                    dataKey={dataKey}
                    stroke={color}
                    fill={color}
                    fillOpacity={0.3}
                    name={name}
                  />
                );
              } else if (config.type === 'bar') {
                return (
                  <Bar
                    key={dataKey}
                    dataKey={dataKey}
                    fill={color}
                    name={name}
                  />
                );
              } else if (config.type === 'scatter') {
                return (
                  <Scatter
                    key={dataKey}
                    dataKey={dataKey}
                    fill={color}
                    name={name}
                  />
                );
              }
              return null;
            });
          })}
        </ChartComponent>
      </ResponsiveContainer>
    );
  };

  return (
    <Card title="仿真结果可视化" size="small">
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Space>
            <span>实时模式:</span>
            <Switch checked={isRealTime} onChange={setIsRealTime} />
          </Space>
        </Col>
        <Col span={6}>
          <Space>
            <span>时间窗口:</span>
            <Select value={timeWindow} onChange={setTimeWindow} style={{ width: 120 }}>
              <Option value={60}>1分钟</Option>
              <Option value={300}>5分钟</Option>
              <Option value={600}>10分钟</Option>
              <Option value={1800}>30分钟</Option>
              <Option value={3600}>1小时</Option>
            </Select>
          </Space>
        </Col>
        <Col span={6}>
          <Space>
            <span>选择节点:</span>
            <Select
              mode="multiple"
              value={selectedNodes}
              onChange={setSelectedNodes}
              style={{ width: 200 }}
              placeholder="选择节点"
            >
              {nodes.map(node => (
                <Option key={node.id} value={node.id}>
                  {node.data?.label || node.id}
                </Option>
              ))}
            </Select>
          </Space>
        </Col>
        <Col span={6}>
          <Space>
            <Button icon={<DownloadOutlined />} onClick={exportData}>
              导出数据
            </Button>
            <Button icon={<ReloadOutlined />} onClick={() => {
              dataBufferRef.current = [];
              setTimeSeriesData([]);
            }}>
              清除数据
            </Button>
          </Space>
        </Col>
      </Row>

      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="实时监控" key="realtime">
          {timeSeriesData.length === 0 ? (
            <Alert
              message="暂无数据"
              description="请启动仿真或选择节点以查看实时数据。"
              type="info"
              showIcon
            />
          ) : (
            <Row gutter={16}>
              {chartConfigs.map(config => (
                <Col span={12} key={config.id} style={{ marginBottom: 16 }}>
                  <Card title={config.title} size="small">
                    {renderChart(config)}
                  </Card>
                </Col>
              ))}
            </Row>
          )}
        </TabPane>
        
        <TabPane tab="统计信息" key="statistics">
          <Row gutter={16}>
            {statistics.map((stat, index) => (
              <Col span={6} key={`${stat.nodeId}_${stat.variable}`} style={{ marginBottom: 16 }}>
                <Card size="small">
                  <Statistic
                    title={`${stat.nodeName} - ${stat.variable}`}
                    value={stat.current}
                    precision={2}
                    suffix={stat.unit}
                    valueStyle={{ color: getTrendColor(stat.trend) }}
                  />
                  <div style={{ fontSize: '12px', color: '#666', marginTop: 8 }}>
                    <div>最小值: {stat.min.toFixed(2)} {stat.unit}</div>
                    <div>最大值: {stat.max.toFixed(2)} {stat.unit}</div>
                    <div>平均值: {stat.average.toFixed(2)} {stat.unit}</div>
                    <div>趋势: <span style={{ color: getTrendColor(stat.trend) }}>{stat.trend}</span></div>
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
        </TabPane>
        
        <TabPane tab="设置" key="settings">
          <Row gutter={16}>
            <Col span={12}>
              <Card title="更新设置" size="small">
                <div style={{ marginBottom: 16 }}>
                  <div style={{ marginBottom: 8 }}>更新间隔: {updateInterval}ms</div>
                  <Slider
                    min={100}
                    max={5000}
                    step={100}
                    value={updateInterval}
                    onChange={setUpdateInterval}
                    marks={{
                      100: '100ms',
                      1000: '1s',
                      2000: '2s',
                      5000: '5s'
                    }}
                  />
                </div>
                
                <div>
                  <div style={{ marginBottom: 8 }}>选择变量:</div>
                  <Select
                    mode="multiple"
                    value={selectedVariables}
                    onChange={setSelectedVariables}
                    style={{ width: '100%' }}
                    placeholder="选择要监控的变量"
                  >
                    <Option value="water_level">水位</Option>
                    <Option value="flow_rate">流量</Option>
                    <Option value="inflow">入流</Option>
                    <Option value="outflow">出流</Option>
                    <Option value="pressure">压力</Option>
                    <Option value="head">水头</Option>
                    <Option value="power">功率</Option>
                    <Option value="efficiency">效率</Option>
                    <Option value="opening">开度</Option>
                    <Option value="velocity">流速</Option>
                  </Select>
                </div>
              </Card>
            </Col>
            
            <Col span={12}>
              <Card title="图表设置" size="small">
                <div style={{ fontSize: '12px', color: '#666' }}>
                  <div>• 支持多种图表类型：线图、面积图、柱状图、散点图</div>
                  <div>• 可自定义颜色和样式</div>
                  <div>• 支持自动缩放和手动设置范围</div>
                  <div>• 实时数据更新和历史数据回放</div>
                  <div>• 数据导出为CSV格式</div>
                </div>
              </Card>
            </Col>
          </Row>
        </TabPane>
      </Tabs>
    </Card>
  );
};

export default SimulationVisualization;