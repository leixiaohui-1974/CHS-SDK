import React, { useState, useEffect } from 'react';
import { Form, Input, InputNumber, Select, Switch, Button, Space, Divider } from 'antd';
import { Node, Edge } from 'reactflow';

interface ParameterPanelProps {
  selectedElement: Node | Edge | null;
  isEditing: boolean;
  onUpdateElement: (elementId: string, newData: any) => void;
}

const ParameterPanel: React.FC<ParameterPanelProps> = ({
  selectedElement,
  isEditing,
  onUpdateElement
}) => {
  const [form] = Form.useForm();
  const [localData, setLocalData] = useState<any>(null);

  useEffect(() => {
    if (selectedElement) {
      const data = selectedElement.data || {};
      setLocalData(data);
      form.setFieldsValue(data);
    } else {
      setLocalData(null);
      form.resetFields();
    }
  }, [selectedElement, form]);

  const handleFormChange = (changedValues: any, allValues: any) => {
    if (isEditing && selectedElement) {
      setLocalData(allValues);
    }
  };

  const handleSave = () => {
    if (selectedElement && localData) {
      onUpdateElement(selectedElement.id, localData);
    }
  };

  const handleReset = () => {
    if (selectedElement) {
      const originalData = selectedElement.data || {};
      setLocalData(originalData);
      form.setFieldsValue(originalData);
    }
  };

  const renderParameterFields = (data: any) => {
    if (!data) return null;

    return Object.entries(data).map(([key, value]) => {
      if (key === 'label' || key === 'type') {
        return (
          <Form.Item key={key} label={key} name={key}>
            <Input disabled={!isEditing} />
          </Form.Item>
        );
      }

      if (typeof value === 'number') {
        return (
          <Form.Item key={key} label={key} name={key}>
            <InputNumber disabled={!isEditing} style={{ width: '100%' }} />
          </Form.Item>
        );
      }

      if (typeof value === 'boolean') {
        return (
          <Form.Item key={key} label={key} name={key} valuePropName="checked">
            <Switch disabled={!isEditing} />
          </Form.Item>
        );
      }

      if (typeof value === 'string') {
        return (
          <Form.Item key={key} label={key} name={key}>
            <Input disabled={!isEditing} />
          </Form.Item>
        );
      }

      if (typeof value === 'object' && value !== null) {
        return (
          <div key={key}>
            <Divider orientation="left" style={{ margin: '12px 0' }}>
              {key}
            </Divider>
            {renderParameterFields(value)}
          </div>
        );
      }

      return (
        <Form.Item key={key} label={key} name={key}>
          <Input disabled={!isEditing} placeholder="Complex value" />
        </Form.Item>
      );
    });
  };

  if (!selectedElement) {
    return (
      <div style={{ padding: '16px', textAlign: 'center', color: '#999' }}>
        Click on a node or edge to see its parameters.
      </div>
    );
  }

  const isNode = !('source' in selectedElement);
  const elementType = isNode ? 'Node' : 'Edge';

  return (
    <div style={{ padding: '16px' }}>
      <div style={{ marginBottom: '16px' }}>
        <strong>{elementType}: {selectedElement.id}</strong>
      </div>
      
      <Form
        form={form}
        layout="vertical"
        onValuesChange={handleFormChange}
        size="small"
      >
        {renderParameterFields(localData)}
        
        {isEditing && (
          <div style={{ marginTop: '16px' }}>
            <Space>
              <Button type="primary" onClick={handleSave}>
                Apply Changes
              </Button>
              <Button onClick={handleReset}>
                Reset
              </Button>
            </Space>
          </div>
        )}
      </Form>
      
      {!isEditing && (
        <div style={{ marginTop: '16px', fontSize: '12px', color: '#999' }}>
          Enable edit mode to modify parameters
        </div>
      )}
    </div>
  );
};

export default ParameterPanel;