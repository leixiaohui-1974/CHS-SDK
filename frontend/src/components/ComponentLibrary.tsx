import React, { useState } from 'react';
import { Card, List, Button, Space, Input, Collapse, Tag, Tooltip } from 'antd';
import { PlusOutlined, SearchOutlined, AppstoreOutlined } from '@ant-design/icons';

const { Panel } = Collapse;
const { Search } = Input;

interface ComponentInfo {
  name: string;
  category: string;
  description: string;
  parameters: Record<string, any>;
  icon?: string;
}

interface ComponentLibraryProps {
  isEditing: boolean;
  onAddComponent: (componentType: string) => void;
  onToggleEditMode: () => void;
}

const componentCategories: Record<string, ComponentInfo[]> = {
  'Hydraulic Components': [
    {
      name: 'Pipe',
      category: 'Hydraulic Components',
      description: 'Basic pipe element for water flow',
      parameters: {
        length: 100,
        diameter: 0.3,
        roughness: 0.01,
        material: 'PVC'
      }
    },
    {
      name: 'Pump',
      category: 'Hydraulic Components',
      description: 'Water pump for pressure increase',
      parameters: {
        power: 1000,
        efficiency: 0.85,
        maxFlow: 50,
        maxHead: 100
      }
    },
    {
      name: 'Valve',
      category: 'Hydraulic Components',
      description: 'Flow control valve',
      parameters: {
        type: 'gate',
        diameter: 0.2,
        coefficient: 0.8,
        status: 'open'
      }
    },
    {
      name: 'Tank',
      category: 'Hydraulic Components',
      description: 'Water storage tank',
      parameters: {
        capacity: 1000,
        initialLevel: 0.5,
        diameter: 10,
        height: 15
      }
    }
  ],
  'Control Elements': [
    {
      name: 'Sensor',
      category: 'Control Elements',
      description: 'Pressure or flow sensor',
      parameters: {
        type: 'pressure',
        range: [0, 100],
        accuracy: 0.1,
        location: 'inlet'
      }
    },
    {
      name: 'Controller',
      category: 'Control Elements',
      description: 'PID controller',
      parameters: {
        kp: 1.0,
        ki: 0.1,
        kd: 0.01,
        setpoint: 50
      }
    }
  ],
  'Boundary Conditions': [
    {
      name: 'Reservoir',
      category: 'Boundary Conditions',
      description: 'Constant head boundary',
      parameters: {
        head: 100,
        temperature: 20,
        quality: 'good'
      }
    },
    {
      name: 'Demand',
      category: 'Boundary Conditions',
      description: 'Water demand node',
      parameters: {
        baseFlow: 10,
        pattern: 'residential',
        priority: 1
      }
    }
  ]
};

const ComponentLibrary: React.FC<ComponentLibraryProps> = ({
  isEditing,
  onAddComponent,
  onToggleEditMode
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [activeKey, setActiveKey] = useState<string[]>(['Hydraulic Components']);

  const filteredComponents = Object.entries(componentCategories).reduce(
    (acc, [category, components]) => {
      const filtered = components.filter(comp =>
        comp.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        comp.description.toLowerCase().includes(searchTerm.toLowerCase())
      );
      if (filtered.length > 0) {
        acc[category] = filtered;
      }
      return acc;
    },
    {} as Record<string, ComponentInfo[]>
  );

  const renderComponent = (component: ComponentInfo) => (
    <List.Item
      key={component.name}
      actions={isEditing ? [
        <Tooltip key="add" title={`Add ${component.name}`}>
          <Button 
            type="link" 
            size="small"
            icon={<PlusOutlined />}
            onClick={() => onAddComponent(component.name)}
          >
            Add
          </Button>
        </Tooltip>
      ] : []}
    >
      <List.Item.Meta
        avatar={<AppstoreOutlined style={{ fontSize: '16px', color: '#1890ff' }} />}
        title={
          <Space>
            {component.name}
            <Tag size="small" color="blue">{component.category}</Tag>
          </Space>
        }
        description={
          <div>
            <div style={{ marginBottom: '4px' }}>{component.description}</div>
            <div style={{ fontSize: '12px', color: '#999' }}>
              Parameters: {Object.keys(component.parameters).join(', ')}
            </div>
          </div>
        }
      />
    </List.Item>
  );

  return (
    <Card 
      title="Component Library" 
      style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
      bodyStyle={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}
      extra={
        <Space>
          <Button 
            type={isEditing ? 'primary' : 'default'}
            size="small"
            onClick={onToggleEditMode}
          >
            {isEditing ? 'View' : 'Edit'}
          </Button>
        </Space>
      }
    >
      <div style={{ marginBottom: '12px' }}>
        <Search
          placeholder="Search components..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          prefix={<SearchOutlined />}
          allowClear
        />
      </div>
      
      <div style={{ flex: 1, overflow: 'auto' }}>
        <Collapse 
          activeKey={activeKey}
          onChange={(keys) => setActiveKey(Array.isArray(keys) ? keys : [keys])}
          size="small"
        >
          {Object.entries(filteredComponents).map(([category, components]) => (
            <Panel 
              header={`${category} (${components.length})`} 
              key={category}
            >
              <List
                dataSource={components}
                renderItem={renderComponent}
                size="small"
              />
            </Panel>
          ))}
        </Collapse>
      </div>
      
      {isEditing && (
        <div style={{ marginTop: '12px', padding: '8px', backgroundColor: '#f6f6f6', borderRadius: '4px' }}>
          <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
            💡 Tip: Click "Add" to place components on the canvas
          </div>
        </div>
      )}
    </Card>
  );
};

export default ComponentLibrary;