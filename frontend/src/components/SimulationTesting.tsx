import React, { useState, useEffect, useRef } from 'react';
import { Card, Row, Col, Button, Space, Progress, Table, Tag, Alert, Tabs, Select, InputNumber, Switch, Timeline, Statistic, Modal, Divider } from 'antd';
import { PlayCircleOutlined, PauseCircleOutlined, StopOutlined, CheckCircleOutlined, CloseCircleOutlined, ExclamationCircleOutlined, DownloadOutlined, ReloadOutlined } from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { useModelingStore } from '../store/modelingStore';

interface TestCase {
  id: string;
  name: string;
  description: string;
  category: 'unit' | 'integration' | 'performance' | 'stability' | 'regression';
  priority: 'low' | 'medium' | 'high' | 'critical';
  duration: number; // seconds
  status: 'pending' | 'running' | 'passed' | 'failed' | 'skipped';
  progress: number;
  startTime?: number;
  endTime?: number;
  result?: TestResult;
}

interface TestResult {
  success: boolean;
  message: string;
  details?: string;
  metrics?: {
    executionTime: number;
    memoryUsage: number;
    cpuUsage: number;
    errorCount: number;
    warningCount: number;
  };
  assertions?: {
    total: number;
    passed: number;
    failed: number;
  };
}

interface TestSuite {
  id: string;
  name: string;
  description: string;
  testCases: TestCase[];
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  startTime?: number;
  endTime?: number;
}

interface PerformanceMetric {
  timestamp: number;
  fps: number;
  memoryUsage: number;
  cpuUsage: number;
  responseTime: number;
  throughput: number;
}

const { Option } = Select;
const { TabPane } = Tabs;

const SimulationTesting: React.FC = () => {
  const { nodes, edges } = useModelingStore();
  
  const [testSuites, setTestSuites] = useState<TestSuite[]>([]);
  const [currentSuite, setCurrentSuite] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetric[]>([]);
  const [testConfig, setTestConfig] = useState({
    timeout: 30,
    retries: 3,
    parallel: true,
    maxConcurrency: 4,
    enableProfiling: true,
    enableCoverage: false
  });
  const [selectedTest, setSelectedTest] = useState<TestCase | null>(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [activeTab, setActiveTab] = useState('suites');
  
  const metricsIntervalRef = useRef<NodeJS.Timeout | null>(null);
  
  // Initialize test suites
  useEffect(() => {
    const suites: TestSuite[] = [
      {
        id: 'unit_tests',
        name: '单元测试',
        description: '测试各个组件的基本功能',
        status: 'pending',
        progress: 0,
        testCases: [
          {
            id: 'test_reservoir_calculation',
            name: '水库计算测试',
            description: '验证水库水位和体积计算的正确性',
            category: 'unit',
            priority: 'high',
            duration: 5,
            status: 'pending',
            progress: 0
          },
          {
            id: 'test_pipe_flow',
            name: '管道流量测试',
            description: '验证管道流量计算和压力损失',
            category: 'unit',
            priority: 'high',
            duration: 3,
            status: 'pending',
            progress: 0
          },
          {
            id: 'test_pump_performance',
            name: '水泵性能测试',
            description: '验证水泵扬程和效率计算',
            category: 'unit',
            priority: 'medium',
            duration: 4,
            status: 'pending',
            progress: 0
          },
          {
            id: 'test_valve_control',
            name: '阀门控制测试',
            description: '验证阀门开度控制和流量调节',
            category: 'unit',
            priority: 'medium',
            duration: 3,
            status: 'pending',
            progress: 0
          }
        ]
      },
      {
        id: 'integration_tests',
        name: '集成测试',
        description: '测试组件间的交互和数据流',
        status: 'pending',
        progress: 0,
        testCases: [
          {
            id: 'test_system_connectivity',
            name: '系统连通性测试',
            description: '验证所有组件的连接和数据传递',
            category: 'integration',
            priority: 'critical',
            duration: 10,
            status: 'pending',
            progress: 0
          },
          {
            id: 'test_control_loop',
            name: '控制回路测试',
            description: '验证控制器和执行器的协调工作',
            category: 'integration',
            priority: 'high',
            duration: 8,
            status: 'pending',
            progress: 0
          },
          {
            id: 'test_data_synchronization',
            name: '数据同步测试',
            description: '验证实时数据同步和状态更新',
            category: 'integration',
            priority: 'high',
            duration: 6,
            status: 'pending',
            progress: 0
          }
        ]
      },
      {
        id: 'performance_tests',
        name: '性能测试',
        description: '测试系统性能和资源使用',
        status: 'pending',
        progress: 0,
        testCases: [
          {
            id: 'test_load_performance',
            name: '负载性能测试',
            description: '测试大规模仿真的性能表现',
            category: 'performance',
            priority: 'high',
            duration: 30,
            status: 'pending',
            progress: 0
          },
          {
            id: 'test_memory_usage',
            name: '内存使用测试',
            description: '监控长时间运行的内存使用情况',
            category: 'performance',
            priority: 'medium',
            duration: 60,
            status: 'pending',
            progress: 0
          },
          {
            id: 'test_response_time',
            name: '响应时间测试',
            description: '测试用户操作的响应时间',
            category: 'performance',
            priority: 'medium',
            duration: 15,
            status: 'pending',
            progress: 0
          }
        ]
      },
      {
        id: 'stability_tests',
        name: '稳定性测试',
        description: '测试系统的稳定性和可靠性',
        status: 'pending',
        progress: 0,
        testCases: [
          {
            id: 'test_long_running',
            name: '长时间运行测试',
            description: '测试系统长时间运行的稳定性',
            category: 'stability',
            priority: 'high',
            duration: 300,
            status: 'pending',
            progress: 0
          },
          {
            id: 'test_error_recovery',
            name: '错误恢复测试',
            description: '测试系统的错误处理和恢复能力',
            category: 'stability',
            priority: 'high',
            duration: 20,
            status: 'pending',
            progress: 0
          },
          {
            id: 'test_stress_conditions',
            name: '压力条件测试',
            description: '测试极端条件下的系统表现',
            category: 'stability',
            priority: 'medium',
            duration: 45,
            status: 'pending',
            progress: 0
          }
        ]
      }
    ];
    
    setTestSuites(suites);
  }, []);
  
  // Simulate test execution
  const executeTest = async (testCase: TestCase): Promise<TestResult> => {
    return new Promise((resolve) => {
      const startTime = Date.now();
      
      // Simulate test execution with progress updates
      const interval = setInterval(() => {
        setTestSuites(prev => prev.map(suite => ({
          ...suite,
          testCases: suite.testCases.map(test => 
            test.id === testCase.id 
              ? { ...test, progress: Math.min(test.progress + 10, 100) }
              : test
          )
        })));
      }, testCase.duration * 100); // Update every 10% of duration
      
      setTimeout(() => {
        clearInterval(interval);
        
        const executionTime = Date.now() - startTime;
        const success = Math.random() > 0.1; // 90% success rate
        
        const result: TestResult = {
          success,
          message: success ? '测试通过' : '测试失败',
          details: success 
            ? `所有断言都通过，执行时间: ${executionTime}ms`
            : `断言失败: 期望值与实际值不匹配`,
          metrics: {
            executionTime,
            memoryUsage: 50 + Math.random() * 100,
            cpuUsage: 20 + Math.random() * 60,
            errorCount: success ? 0 : Math.floor(Math.random() * 3) + 1,
            warningCount: Math.floor(Math.random() * 2)
          },
          assertions: {
            total: Math.floor(Math.random() * 10) + 5,
            passed: 0,
            failed: 0
          }
        };
        
        result.assertions!.passed = success 
          ? result.assertions!.total 
          : Math.floor(Math.random() * result.assertions!.total);
        result.assertions!.failed = result.assertions!.total - result.assertions!.passed;
        
        resolve(result);
      }, testCase.duration * 1000);
    });
  };
  
  // Run test suite
  const runTestSuite = async (suiteId: string) => {
    const suite = testSuites.find(s => s.id === suiteId);
    if (!suite) return;
    
    setIsRunning(true);
    setCurrentSuite(suiteId);
    
    // Update suite status
    setTestSuites(prev => prev.map(s => 
      s.id === suiteId 
        ? { ...s, status: 'running', startTime: Date.now(), progress: 0 }
        : s
    ));
    
    // Start performance monitoring
    if (testConfig.enableProfiling) {
      startPerformanceMonitoring();
    }
    
    try {
      const testCases = suite.testCases;
      let completedTests = 0;
      
      if (testConfig.parallel) {
        // Run tests in parallel with concurrency limit
        const chunks = [];
        for (let i = 0; i < testCases.length; i += testConfig.maxConcurrency) {
          chunks.push(testCases.slice(i, i + testConfig.maxConcurrency));
        }
        
        for (const chunk of chunks) {
          const promises = chunk.map(async (testCase) => {
            // Update test status
            setTestSuites(prev => prev.map(s => ({
              ...s,
              testCases: s.testCases.map(t => 
                t.id === testCase.id 
                  ? { ...t, status: 'running', startTime: Date.now(), progress: 0 }
                  : t
              )
            })));
            
            const result = await executeTest(testCase);
            
            // Update test result
            setTestSuites(prev => prev.map(s => ({
              ...s,
              testCases: s.testCases.map(t => 
                t.id === testCase.id 
                  ? { 
                      ...t, 
                      status: result.success ? 'passed' : 'failed',
                      endTime: Date.now(),
                      progress: 100,
                      result
                    }
                  : t
              )
            })));
            
            completedTests++;
            
            // Update suite progress
            const progress = (completedTests / testCases.length) * 100;
            setTestSuites(prev => prev.map(s => 
              s.id === suiteId ? { ...s, progress } : s
            ));
          });
          
          await Promise.all(promises);
        }
      } else {
        // Run tests sequentially
        for (const testCase of testCases) {
          setTestSuites(prev => prev.map(s => ({
            ...s,
            testCases: s.testCases.map(t => 
              t.id === testCase.id 
                ? { ...t, status: 'running', startTime: Date.now(), progress: 0 }
                : t
            )
          })));
          
          const result = await executeTest(testCase);
          
          setTestSuites(prev => prev.map(s => ({
            ...s,
            testCases: s.testCases.map(t => 
              t.id === testCase.id 
                ? { 
                    ...t, 
                    status: result.success ? 'passed' : 'failed',
                    endTime: Date.now(),
                    progress: 100,
                    result
                  }
                : t
            )
          })));
          
          completedTests++;
          const progress = (completedTests / testCases.length) * 100;
          setTestSuites(prev => prev.map(s => 
            s.id === suiteId ? { ...s, progress } : s
          ));
        }
      }
      
      // Update suite completion status
      const updatedSuite = testSuites.find(s => s.id === suiteId);
      const allPassed = updatedSuite?.testCases.every(t => t.status === 'passed');
      
      setTestSuites(prev => prev.map(s => 
        s.id === suiteId 
          ? { 
              ...s, 
              status: allPassed ? 'completed' : 'failed',
              endTime: Date.now(),
              progress: 100
            }
          : s
      ));
      
    } catch (error) {
      console.error('Test suite execution failed:', error);
      setTestSuites(prev => prev.map(s => 
        s.id === suiteId ? { ...s, status: 'failed', endTime: Date.now() } : s
      ));
    } finally {
      setIsRunning(false);
      setCurrentSuite(null);
      stopPerformanceMonitoring();
    }
  };
  
  // Performance monitoring
  const startPerformanceMonitoring = () => {
    metricsIntervalRef.current = setInterval(() => {
      const metric: PerformanceMetric = {
        timestamp: Date.now(),
        fps: 60 + Math.random() * 10 - 5,
        memoryUsage: 100 + Math.random() * 200,
        cpuUsage: 30 + Math.random() * 40,
        responseTime: 10 + Math.random() * 50,
        throughput: 1000 + Math.random() * 500
      };
      
      setPerformanceMetrics(prev => [...prev.slice(-59), metric]); // Keep last 60 points
    }, 1000);
  };
  
  const stopPerformanceMonitoring = () => {
    if (metricsIntervalRef.current) {
      clearInterval(metricsIntervalRef.current);
      metricsIntervalRef.current = null;
    }
  };
  
  // Get status color
  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'passed': return '#52c41a';
      case 'failed': return '#ff4d4f';
      case 'running': return '#1890ff';
      case 'pending': return '#d9d9d9';
      case 'skipped': return '#faad14';
      default: return '#d9d9d9';
    }
  };
  
  // Get status icon
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'passed': return <CheckCircleOutlined />;
      case 'failed': return <CloseCircleOutlined />;
      case 'running': return <PlayCircleOutlined />;
      case 'pending': return <ExclamationCircleOutlined />;
      default: return <ExclamationCircleOutlined />;
    }
  };
  
  // Calculate statistics
  const calculateStats = () => {
    const allTests = testSuites.flatMap(s => s.testCases);
    const total = allTests.length;
    const passed = allTests.filter(t => t.status === 'passed').length;
    const failed = allTests.filter(t => t.status === 'failed').length;
    const running = allTests.filter(t => t.status === 'running').length;
    const pending = allTests.filter(t => t.status === 'pending').length;
    
    return { total, passed, failed, running, pending };
  };
  
  const stats = calculateStats();
  
  // Test suite table columns
  const suiteColumns = [
    {
      title: '测试套件',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: TestSuite) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{name}</div>
          <div style={{ fontSize: '12px', color: '#666' }}>{record.description}</div>
        </div>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getStatusColor(status)} icon={getStatusIcon(status)}>
          {status === 'pending' ? '待执行' :
           status === 'running' ? '运行中' :
           status === 'completed' ? '已完成' : '失败'}
        </Tag>
      )
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      render: (progress: number) => (
        <Progress percent={progress} size="small" />
      )
    },
    {
      title: '测试用例',
      key: 'testCases',
      render: (record: TestSuite) => {
        const passed = record.testCases.filter(t => t.status === 'passed').length;
        const failed = record.testCases.filter(t => t.status === 'failed').length;
        const total = record.testCases.length;
        
        return (
          <div>
            <Tag color="green">{passed} 通过</Tag>
            <Tag color="red">{failed} 失败</Tag>
            <Tag>{total} 总计</Tag>
          </div>
        );
      }
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: TestSuite) => (
        <Space>
          <Button 
            size="small" 
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={() => runTestSuite(record.id)}
            disabled={isRunning || record.status === 'running'}
          >
            运行
          </Button>
          <Button 
            size="small"
            onClick={() => {
              // Reset suite
              setTestSuites(prev => prev.map(s => 
                s.id === record.id 
                  ? {
                      ...s,
                      status: 'pending',
                      progress: 0,
                      startTime: undefined,
                      endTime: undefined,
                      testCases: s.testCases.map(t => ({
                        ...t,
                        status: 'pending',
                        progress: 0,
                        startTime: undefined,
                        endTime: undefined,
                        result: undefined
                      }))
                    }
                  : s
              ));
            }}
          >
            重置
          </Button>
        </Space>
      )
    }
  ];
  
  // Test case table columns
  const testColumns = [
    {
      title: '测试用例',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: TestCase) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{name}</div>
          <div style={{ fontSize: '12px', color: '#666' }}>{record.description}</div>
        </div>
      )
    },
    {
      title: '类别',
      dataIndex: 'category',
      key: 'category',
      render: (category: string) => (
        <Tag color={category === 'unit' ? 'blue' : 
                   category === 'integration' ? 'green' :
                   category === 'performance' ? 'orange' :
                   category === 'stability' ? 'purple' : 'default'}>
          {category === 'unit' ? '单元' :
           category === 'integration' ? '集成' :
           category === 'performance' ? '性能' :
           category === 'stability' ? '稳定性' : category}
        </Tag>
      )
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      render: (priority: string) => (
        <Tag color={priority === 'critical' ? 'red' :
                   priority === 'high' ? 'orange' :
                   priority === 'medium' ? 'blue' : 'default'}>
          {priority === 'critical' ? '严重' :
           priority === 'high' ? '高' :
           priority === 'medium' ? '中' : '低'}
        </Tag>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getStatusColor(status)} icon={getStatusIcon(status)}>
          {status === 'pending' ? '待执行' :
           status === 'running' ? '运行中' :
           status === 'passed' ? '通过' :
           status === 'failed' ? '失败' : '跳过'}
        </Tag>
      )
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      render: (progress: number, record: TestCase) => (
        <div>
          <Progress percent={progress} size="small" />
          {record.result && (
            <div style={{ fontSize: '10px', marginTop: '2px' }}>
              {record.result.metrics?.executionTime}ms
            </div>
          )}
        </div>
      )
    },
    {
      title: '操作',
      key: 'actions',
      render: (record: TestCase) => (
        <Button 
          size="small"
          onClick={() => {
            setSelectedTest(record);
            setIsModalVisible(true);
          }}
        >
          详情
        </Button>
      )
    }
  ];
  
  const allTestCases = testSuites.flatMap(s => s.testCases);
  
  return (
    <Card title="集成测试" size="small">
      {/* Statistics */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Statistic
            title="总测试数"
            value={stats.total}
            prefix={<ExclamationCircleOutlined />}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="通过"
            value={stats.passed}
            valueStyle={{ color: '#52c41a' }}
            prefix={<CheckCircleOutlined />}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="失败"
            value={stats.failed}
            valueStyle={{ color: '#ff4d4f' }}
            prefix={<CloseCircleOutlined />}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="通过率"
            value={stats.total > 0 ? ((stats.passed / stats.total) * 100).toFixed(1) : 0}
            suffix="%"
            valueStyle={{ color: stats.total > 0 && stats.passed / stats.total > 0.8 ? '#52c41a' : '#faad14' }}
          />
        </Col>
      </Row>
      
      {/* Controls */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <Space>
            <Button 
              type="primary" 
              icon={<PlayCircleOutlined />}
              onClick={() => {
                // Run all suites
                testSuites.forEach(suite => {
                  if (suite.status !== 'running') {
                    setTimeout(() => runTestSuite(suite.id), Math.random() * 1000);
                  }
                });
              }}
              disabled={isRunning}
              loading={isRunning}
            >
              运行所有测试
            </Button>
            <Button 
              icon={<StopOutlined />}
              onClick={() => {
                setIsRunning(false);
                setCurrentSuite(null);
                stopPerformanceMonitoring();
              }}
              disabled={!isRunning}
            >
              停止测试
            </Button>
            <Button 
              icon={<ReloadOutlined />}
              onClick={() => {
                // Reset all tests
                setTestSuites(prev => prev.map(s => ({
                  ...s,
                  status: 'pending',
                  progress: 0,
                  startTime: undefined,
                  endTime: undefined,
                  testCases: s.testCases.map(t => ({
                    ...t,
                    status: 'pending',
                    progress: 0,
                    startTime: undefined,
                    endTime: undefined,
                    result: undefined
                  }))
                })));
                setPerformanceMetrics([]);
              }}
            >
              重置所有
            </Button>
          </Space>
        </Col>
        <Col span={8}>
          <Space>
            <span>并行执行:</span>
            <Switch 
              checked={testConfig.parallel} 
              onChange={(checked) => setTestConfig(prev => ({ ...prev, parallel: checked }))}
              disabled={isRunning}
            />
            {testConfig.parallel && (
              <>
                <span>并发数:</span>
                <InputNumber 
                  value={testConfig.maxConcurrency}
                  onChange={(value) => setTestConfig(prev => ({ ...prev, maxConcurrency: value || 1 }))}
                  min={1}
                  max={8}
                  size="small"
                  style={{ width: 60 }}
                  disabled={isRunning}
                />
              </>
            )}
          </Space>
        </Col>
        <Col span={8}>
          <Space>
            <span>性能分析:</span>
            <Switch 
              checked={testConfig.enableProfiling} 
              onChange={(checked) => setTestConfig(prev => ({ ...prev, enableProfiling: checked }))}
              disabled={isRunning}
            />
          </Space>
        </Col>
      </Row>
      
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="测试套件" key="suites">
          <Table
            dataSource={testSuites}
            columns={suiteColumns}
            rowKey="id"
            size="small"
            pagination={false}
          />
        </TabPane>
        
        <TabPane tab="测试用例" key="cases">
          <Table
            dataSource={allTestCases}
            columns={testColumns}
            rowKey="id"
            size="small"
            pagination={{
              pageSize: 10,
              showSizeChanger: true
            }}
          />
        </TabPane>
        
        <TabPane tab="性能监控" key="performance">
          {performanceMetrics.length > 0 ? (
            <Row gutter={16}>
              <Col span={12}>
                <Card title="性能指标" size="small">
                  <ResponsiveContainer width="100%" height={250}>
                    <LineChart data={performanceMetrics.map(m => ({
                      time: new Date(m.timestamp).toLocaleTimeString(),
                      FPS: m.fps,
                      '响应时间': m.responseTime
                    }))}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="time" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="FPS" stroke="#1890ff" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="响应时间" stroke="#52c41a" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </Card>
              </Col>
              <Col span={12}>
                <Card title="资源使用" size="small">
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={performanceMetrics.slice(-10).map(m => ({
                      time: new Date(m.timestamp).toLocaleTimeString(),
                      '内存使用': m.memoryUsage,
                      'CPU使用': m.cpuUsage
                    }))}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="time" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="内存使用" fill="#fa8c16" />
                      <Bar dataKey="CPU使用" fill="#722ed1" />
                    </BarChart>
                  </ResponsiveContainer>
                </Card>
              </Col>
            </Row>
          ) : (
            <Alert
              message="暂无性能数据"
              description="请启用性能分析并运行测试以查看性能监控数据。"
              type="info"
              showIcon
            />
          )}
        </TabPane>
      </Tabs>
      
      {/* Test Detail Modal */}
      <Modal
        title="测试详情"
        visible={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setIsModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={800}
      >
        {selectedTest && (
          <div>
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={12}>
                <div><strong>测试名称:</strong> {selectedTest.name}</div>
                <div><strong>描述:</strong> {selectedTest.description}</div>
                <div><strong>类别:</strong> {selectedTest.category}</div>
                <div><strong>优先级:</strong> {selectedTest.priority}</div>
              </Col>
              <Col span={12}>
                <div><strong>状态:</strong> 
                  <Tag color={getStatusColor(selectedTest.status)} style={{ marginLeft: 8 }}>
                    {selectedTest.status}
                  </Tag>
                </div>
                <div><strong>预计时长:</strong> {selectedTest.duration}秒</div>
                <div><strong>进度:</strong> {selectedTest.progress}%</div>
              </Col>
            </Row>
            
            {selectedTest.result && (
              <>
                <Divider />
                <div style={{ marginBottom: 16 }}>
                  <strong>测试结果:</strong>
                  <div style={{ 
                    padding: '8px', 
                    backgroundColor: selectedTest.result.success ? '#f6ffed' : '#fff2f0', 
                    borderRadius: '4px', 
                    marginTop: '8px',
                    color: selectedTest.result.success ? '#52c41a' : '#ff4d4f'
                  }}>
                    {selectedTest.result.message}
                  </div>
                  {selectedTest.result.details && (
                    <div style={{ marginTop: '8px', fontSize: '12px', color: '#666' }}>
                      {selectedTest.result.details}
                    </div>
                  )}
                </div>
                
                {selectedTest.result.metrics && (
                  <Row gutter={16} style={{ marginBottom: 16 }}>
                    <Col span={12}>
                      <div><strong>执行时间:</strong> {selectedTest.result.metrics.executionTime}ms</div>
                      <div><strong>内存使用:</strong> {selectedTest.result.metrics.memoryUsage.toFixed(1)}MB</div>
                      <div><strong>CPU使用:</strong> {selectedTest.result.metrics.cpuUsage.toFixed(1)}%</div>
                    </Col>
                    <Col span={12}>
                      <div><strong>错误数量:</strong> {selectedTest.result.metrics.errorCount}</div>
                      <div><strong>警告数量:</strong> {selectedTest.result.metrics.warningCount}</div>
                    </Col>
                  </Row>
                )}
                
                {selectedTest.result.assertions && (
                  <div>
                    <strong>断言统计:</strong>
                    <div style={{ marginTop: '8px' }}>
                      <Tag color="green">通过: {selectedTest.result.assertions.passed}</Tag>
                      <Tag color="red">失败: {selectedTest.result.assertions.failed}</Tag>
                      <Tag>总计: {selectedTest.result.assertions.total}</Tag>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </Modal>
    </Card>
  );
};

export default SimulationTesting;