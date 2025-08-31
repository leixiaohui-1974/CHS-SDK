import React, { DragEvent } from 'react';
import { Card, List, Typography } from 'antd';
import { useSimulationStore } from '../store/simulationStore';

const { Text } = Typography;

const onDragStart = (event: DragEvent, variableName: string) => {
  event.dataTransfer.setData('application/chs-sdk-variable', variableName);
  event.dataTransfer.effectAllowed = 'copy';
};

const VariableSidebar: React.FC = () => {
  const { availableVariables } = useSimulationStore();

  return (
    <Card title="Output Variables">
      {availableVariables.length === 0 ? (
        <Text type="secondary">No output variables defined or simulation not started.</Text>
      ) : (
        <List
          dataSource={availableVariables}
          renderItem={(variable: string) => (
            <List.Item
              onDragStart={(event) => onDragStart(event, variable)}
              draggable
              style={{ cursor: 'copy', border: '1px solid #f0f0f0', padding: '8px', marginBottom: '8px', borderRadius: '4px' }}
            >
              <Text>{variable}</Text>
            </List.Item>
          )}
        />
      )}
    </Card>
  );
};

export default VariableSidebar;
