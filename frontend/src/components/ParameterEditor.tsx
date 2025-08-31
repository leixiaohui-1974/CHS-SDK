import React, { useState, useEffect, ChangeEvent } from 'react';
import { Card, Form, Input, Typography, Empty } from 'antd';
import type { Node, Edge } from 'reactflow';
import { useProjectStore } from '../store/projectStore';

const { Title } = Typography;

interface ParameterEditorProps {
  element: Node | Edge | null;
}

const ParameterEditor: React.FC<ParameterEditorProps> = ({ element }) => {
  const { updateElementData } = useProjectStore();
  const [formData, setFormData] = useState<any>({});

  useEffect(() => {
    // Update form data when a new element is selected
    setFormData(element?.data || {});
  }, [element]);

  if (!element) {
    return <p>Click on a node or edge to see its parameters.</p>;
  }

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev: any) => ({ ...prev, [name]: value }));
  };

  const handleInputBlur = () => {
    // On blur, update the central store
    updateElementData(element.id, formData);
  };

  // Render a form based on the element's data properties
  const renderFormItems = () => {
    const data = element.data || {};
    return Object.entries(data).map(([key, value]) => {
      // Make some fields read-only
      if (key === 'label' || key === 'class' || key === '_id') {
        return null;
      }

      // For nested objects like 'parameters', we can handle them differently if needed.
      // For now, we'll just show them as stringified JSON.
      const isObject = typeof value === 'object' && value !== null;
      const displayValue = isObject ? JSON.stringify(value, null, 2) : value;

      return (
        <Form.Item label={key} key={key}>
          <Input
            name={key}
            value={formData[key] ?? ''}
            onChange={handleInputChange}
            onBlur={handleInputBlur}
            readOnly={isObject} // Make object fields read-only for now
          />
        </Form.Item>
      );
    }).filter(Boolean); // Filter out null entries
  };

  return (
    <div>
      <Title level={5}>Editing: {element.data.name || element.id}</Title>
      <Form layout="vertical">
        {renderFormItems()}
      </Form>
    </div>
  );
};

export default ParameterEditor;
