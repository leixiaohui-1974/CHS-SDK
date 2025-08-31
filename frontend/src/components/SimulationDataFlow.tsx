import React, { useState, useEffect, useCallback } from 'react';
import { Card, Table, Tag, Progress, Alert, Space, Button, Modal, Descriptions, Tooltip } from 'antd';
import { InfoCircleOutlined, WarningOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { useModelingStore } from '../store/modelingStore';

interface DataFlowConnection {
  id: string;
  source: string;
  target: string;
  sourcePort?: string;
  targetPort?: string;
  dataType: string;
  flowRate: number;
  pressure: number;
  temperature: number;
  quality: number;
  lastUpdate: number;
  status: 'active' | 'inactive' | 'error' | 'warning';
  latency: number;
  throughput: number;
}

interface BoundaryCondition {
  id: string;
  nodeId: string;
  type: 'inflow' | 'outflow' | 'level' | 'pressure';
  value: number;
  unit: string;
  isActive: boolean;
  source: 'user' | 'sensor' | 'calculated';
  lastUpdate: number;
  trend: 'increasing' | 'decreasing' | 'stable';
}

interface SynchronizationStatus {
  nodeId: string;
  nodeName: string;
  lastSync: number;
  syncDelay: number;
  status: 'synced' | 'delayed' | 'error';
  pendingUpdates: number;
  dataIntegrity: number; // 0-100%
}

const SimulationDataFlow: React.FC = () => {
  const { nodes, edges } = useModelingStore();
  
  const [dataFlowConnections, setDataFlowConnections] = useState<DataFlowConnection[]>([]);
  const [boundaryConditions, setBoundaryConditions] = useState<BoundaryCondition[]>([]);
  const [syncStatus, setSyncStatus] = useState<SynchronizationStatus[]>([]);
  const [selectedConnection, setSelectedConnection] = useState<DataFlowConnection | null>(null);
  const [showConnectionDetails, setShowConnectionDetails] = useState(false);
  const [activeTab, setActiveTab] = useState<'connections' | 'boundaries' | 'sync'>('connections');

  // Initialize data flow connections from edges
  useEffect(() => {
    const connections: DataFlowConnection[] = edges.map(edge => {
      const sourceNode = nodes.find(n => n.id === edge.source);
      const targetNode = nodes.find(n => n.id === edge.target);
      
      return {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        sourcePort: edge.sourceHandle || 'output',
        targetPort: edge.targetHandle || 'input',
        dataType: getDataTypeForConnection(sourceNode?.type, targetNode?.type),
        flowRate: Math.random() * 100, // Simulated data
        pressure: Math.random() * 10 + 1,
        temperature: Math.random() * 5 + 20,
        quality: Math.random() * 20 + 80,
        lastUpdate: Date.now(),
        status: Math.random() > 0.1 ? 'active' : 'warning',
        latency: Math.random() * 10,
        throughput: Math.random() * 1000 + 500
      };
    });
    
    setDataFlowConnections(connections);
  }, [edges, nodes]);

  // Initialize boundary conditions
  useEffect(() => {
    const boundaries: BoundaryCondition[] = [];
    
    nodes.forEach(node => {
      // Add boundary conditions for nodes without upstream connections
      const hasUpstream = edges.some(edge => edge.target === node.id);
      if (!hasUpstream && ['reservoir', 'source'].includes(node.type)) {
        boundaries.push({
          id: `${node.id}_inflow`,
          nodeId: node.id,
          type: 'inflow',
          value: Math.random() * 50 + 10,
          unit: 'm³/s',
          isActive: true,
          source: 'sensor',
          lastUpdate: Date.now(),
          trend: ['increasing', 'decreasing', 'stable'][Math.floor(Math.random() * 3)] as any
        });
      }
      
      // Add boundary conditions for nodes without downstream connections
      const hasDownstream = edges.some(edge => edge.source === node.id);
      if (!hasDownstream && ['sink', 'outlet'].includes(node.type)) {
        boundaries.push({
          id: `${node.id}_level`,
          nodeId: node.id,
          type: 'level',
          value: Math.random() * 5 + 5,
          unit: 'm',
          isActive: true,
          source: 'user',
          lastUpdate: Date.now(),
          trend: 'stable'
        });
      }
    });
    
    setBoundaryConditions(boundaries);
  }, [nodes, edges]);

  // Initialize synchronization status
  useEffect(() => {
    const syncStatuses: SynchronizationStatus[] = nodes.map(node => ({
      nodeId: node.id,
      nodeName: node.data?.label || node.id,
      lastSync: Date.now() - Math.random() * 1000,
      syncDelay: Math.random() * 100,
      status: Math.random() > 0.05 ? 'synced' : 'delayed',
      pendingUpdates: Math.floor(Math.random() * 5),
      dataIntegrity: Math.random() * 10 + 90
    }));
    
    setSyncStatus(syncStatuses);
  }, [nodes]);

  // Determine data type for connection
  const getDataTypeForConnection = (sourceType?: string, targetType?: string): string => {
    if (!sourceType || !targetType) return 'unknown';
    
    const fluidTypes = ['reservoir', 'pipe', 'pump', 'valve', 'gate'];
    const controlTypes = ['controller', 'sensor', 'actuator'];
    
    if (fluidTypes.includes(sourceType) && fluidTypes.includes(targetType)) {
      return 'fluid';
    } else if (controlTypes.includes(sourceType) || controlTypes.includes(targetType)) {
      return 'control';
    } else {
      return 'data';
    }
  };

  // Get status color
  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'active':
      case 'synced':
        return 'green';
      case 'warning':
      case 'delayed':
        return 'orange';
      case 'error':
        return 'red';
      case 'inactive':
        return 'gray';
      default:
        return 'blue';
    }
  };

  // Get status icon
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
      case 'synced':
        return <CheckCircleOutlined style={{ color: 'green' }} />;
      case 'warning':
      case 'delayed':
        return <WarningOutlined style={{ color: 'orange' }} />;
      case 'error':
        return <CloseCircleOutlined style={{ color: 'red' }} />;
      default:
        return <InfoCircleOutlined style={{ color: 'blue' }} />;
    }
  };

  // Update data flow in real-time (simulated)
  useEffect(() => {
    const interval = setInterval(() => {
      setDataFlowConnections(prev => prev.map(conn => ({
        ...conn,
        flowRate: Math.max(0, conn.flowRate + (Math.random() - 0.5) * 10),
        pressure: Math.max(0, conn.pressure + (Math.random() - 0.5) * 0.5),
        temperature: conn.temperature + (Math.random() - 0.5) * 0.2,
        quality: Math.max(0, Math.min(100, conn.quality + (Math.random() - 0.5) * 2)),
        lastUpdate: Date.now(),
        latency: Math.max(0, conn.latency + (Math.random() - 0.5) * 2),
        throughput: Math.max(0, conn.throughput + (Math.random() - 0.5) * 100)
      })));
      
      setSyncStatus(prev => prev.map(status => ({
        ...status,
        lastSync: Date.now() - Math.random() * 100,
        syncDelay: Math.max(0, status.syncDelay + (Math.random() - 0.5) * 10),
        pendingUpdates: Math.max(0, status.pendingUpdates + Math.floor((Math.random() - 0.7) * 3)),
        dataIntegrity: Math.max(85, Math.min(100, status.dataIntegrity + (Math.random() - 0.5) * 2))
      })));
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  // Connection table columns
  const connectionColumns = [
    {
      title: '连接ID',
      dataIndex: 'id',
      key: 'id',
      width: 120,
      ellipsis: true
    },
    {
      title: '源节点',
      dataIndex: 'source',
      key: 'source',
      width: 100
    },
    {
      title: '目标节点',
      dataIndex: 'target',
      key: 'target',
      width: 100
    },
    {
      title: '数据类型',
      dataIndex: 'dataType',
      key: 'dataType',
      width: 80,
      render: (type: string) => (
        <Tag color={type === 'fluid' ? 'blue' : type === 'control' ? 'green' : 'orange'}>
          {type}
        </Tag>
      )
    },
    {
      title: '流量',
      dataIndex: 'flowRate',
      key: 'flowRate',
      width: 80,
      render: (value: number) => `${value.toFixed(1)} m³/s`
    },
    {
      title: '压力',
      dataIndex: 'pressure',
      key: 'pressure',
      width: 80,
      render: (value: number) => `${value.toFixed(2)} bar`
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: string) => (
        <Tag color={getStatusColor(status)} icon={getStatusIcon(status)}>
          {status}
        </Tag>
      )
    },
    {
      title: '延迟',
      dataIndex: 'latency',
      key: 'latency',
      width: 80,
      render: (value: number) => `${value.toFixed(1)} ms`
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: any, record: DataFlowConnection) => (
        <Button
          size="small"
          type="link"
          onClick={() => {
            setSelectedConnection(record);
            setShowConnectionDetails(true);
          }}
        >
          详情
        </Button>
      )
    }
  ];

  // Boundary conditions table columns
  const boundaryColumns = [
    {
      title: '节点ID',
      dataIndex: 'nodeId',
      key: 'nodeId',
      width: 100
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 80,
      render: (type: string) => (
        <Tag color={type === 'inflow' ? 'blue' : type === 'outflow' ? 'red' : 'green'}>
          {type}
        </Tag>
      )
    },
    {
      title: '值',
      key: 'value',
      width: 100,
      render: (_: any, record: BoundaryCondition) => `${record.value.toFixed(2)} ${record.unit}`
    },
    {
      title: '来源',
      dataIndex: 'source',
      key: 'source',
      width: 80,
      render: (source: string) => (
        <Tag color={source === 'sensor' ? 'blue' : source === 'user' ? 'green' : 'orange'}>
          {source}
        </Tag>
      )
    },
    {
      title: '趋势',
      dataIndex: 'trend',
      key: 'trend',
      width: 80,
      render: (trend: string) => {
        const color = trend === 'increasing' ? 'red' : trend === 'decreasing' ? 'blue' : 'green';
        return <Tag color={color}>{trend}</Tag>;
      }
    },
    {
      title: '状态',
      dataIndex: 'isActive',
      key: 'isActive',
      width: 80,
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'green' : 'red'}>
          {isActive ? '活跃' : '非活跃'}
        </Tag>
      )
    }
  ];

  // Synchronization status table columns
  const syncColumns = [
    {
      title: '节点名称',
      dataIndex: 'nodeName',
      key: 'nodeName',
      width: 120
    },
    {
      title: '同步状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={getStatusColor(status)} icon={getStatusIcon(status)}>
          {status}
        </Tag>
      )
    },
    {
      title: '同步延迟',
      dataIndex: 'syncDelay',
      key: 'syncDelay',
      width: 100,
      render: (delay: number) => `${delay.toFixed(1)} ms`
    },
    {
      title: '待处理更新',
      dataIndex: 'pendingUpdates',
      key: 'pendingUpdates',
      width: 100
    },
    {
      title: '数据完整性',
      dataIndex: 'dataIntegrity',
      key: 'dataIntegrity',
      width: 120,
      render: (integrity: number) => (
        <Tooltip title={`${integrity.toFixed(1)}%`}>
          <Progress
            percent={integrity}
            size="small"
            status={integrity > 95 ? 'success' : integrity > 90 ? 'normal' : 'exception'}
            showInfo={false}
          />
        </Tooltip>
      )
    }
  ];

  return (
    <Card title="仿真数据流管理" size="small">
      <Space style={{ marginBottom: 16 }}>
        <Button
          type={activeTab === 'connections' ? 'primary' : 'default'}
          onClick={() => setActiveTab('connections')}
        >
          数据连接 ({dataFlowConnections.length})
        </Button>
        <Button
          type={activeTab === 'boundaries' ? 'primary' : 'default'}
          onClick={() => setActiveTab('boundaries')}
        >
          边界条件 ({boundaryConditions.length})
        </Button>
        <Button
          type={activeTab === 'sync' ? 'primary' : 'default'}
          onClick={() => setActiveTab('sync')}
        >
          同步状态 ({syncStatus.length})
        </Button>
      </Space>

      {/* Data Flow Connections */}
      {activeTab === 'connections' && (
        <>
          {dataFlowConnections.some(conn => conn.status === 'error') && (
            <Alert
              message="检测到连接错误"
              description="部分数据连接存在错误，请检查网络拓扑和组件状态。"
              type="error"
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}
          
          <Table
            columns={connectionColumns}
            dataSource={dataFlowConnections}
            rowKey="id"
            size="small"
            pagination={{ pageSize: 10 }}
            scroll={{ y: 300 }}
          />
        </>
      )}

      {/* Boundary Conditions */}
      {activeTab === 'boundaries' && (
        <>
          {boundaryConditions.some(bc => !bc.isActive) && (
            <Alert
              message="边界条件警告"
              description="部分边界条件未激活，可能影响仿真结果的准确性。"
              type="warning"
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}
          
          <Table
            columns={boundaryColumns}
            dataSource={boundaryConditions}
            rowKey="id"
            size="small"
            pagination={{ pageSize: 10 }}
            scroll={{ y: 300 }}
          />
        </>
      )}

      {/* Synchronization Status */}
      {activeTab === 'sync' && (
        <>
          {syncStatus.some(status => status.status === 'error' || status.dataIntegrity < 90) && (
            <Alert
              message="同步问题"
              description="部分节点存在同步延迟或数据完整性问题。"
              type="warning"
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}
          
          <Table
            columns={syncColumns}
            dataSource={syncStatus}
            rowKey="nodeId"
            size="small"
            pagination={{ pageSize: 10 }}
            scroll={{ y: 300 }}
          />
        </>
      )}

      {/* Connection Details Modal */}
      <Modal
        title="连接详情"
        open={showConnectionDetails}
        onCancel={() => setShowConnectionDetails(false)}
        footer={null}
        width={600}
      >
        {selectedConnection && (
          <Descriptions column={2} size="small">
            <Descriptions.Item label="连接ID">{selectedConnection.id}</Descriptions.Item>
            <Descriptions.Item label="数据类型">
              <Tag color={selectedConnection.dataType === 'fluid' ? 'blue' : 'green'}>
                {selectedConnection.dataType}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="源节点">{selectedConnection.source}</Descriptions.Item>
            <Descriptions.Item label="目标节点">{selectedConnection.target}</Descriptions.Item>
            <Descriptions.Item label="源端口">{selectedConnection.sourcePort}</Descriptions.Item>
            <Descriptions.Item label="目标端口">{selectedConnection.targetPort}</Descriptions.Item>
            <Descriptions.Item label="流量">{selectedConnection.flowRate.toFixed(2)} m³/s</Descriptions.Item>
            <Descriptions.Item label="压力">{selectedConnection.pressure.toFixed(2)} bar</Descriptions.Item>
            <Descriptions.Item label="温度">{selectedConnection.temperature.toFixed(1)} °C</Descriptions.Item>
            <Descriptions.Item label="质量">{selectedConnection.quality.toFixed(1)}%</Descriptions.Item>
            <Descriptions.Item label="延迟">{selectedConnection.latency.toFixed(1)} ms</Descriptions.Item>
            <Descriptions.Item label="吞吐量">{selectedConnection.throughput.toFixed(0)} KB/s</Descriptions.Item>
            <Descriptions.Item label="状态" span={2}>
              <Tag color={getStatusColor(selectedConnection.status)} icon={getStatusIcon(selectedConnection.status)}>
                {selectedConnection.status}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="最后更新" span={2}>
              {new Date(selectedConnection.lastUpdate).toLocaleString()}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </Card>
  );
};

export default SimulationDataFlow;