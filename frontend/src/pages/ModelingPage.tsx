import React, { useMemo, useState } from 'react';
import { useProjectStore } from '../store/projectStore';
import { Empty, Spin, Card, List } from 'antd';
import ReactFlow, { MiniMap, Controls, Background, Node, Edge } from 'reactflow';
import 'reactflow/dist/style.css';

import { transformToFlowData } from '../utils/flow-transformer';

const ModelingPage: React.FC = () => {
  const { projectConfig, isLoading, error } = useProjectStore();
  const [selectedElement, setSelectedElement] = useState<Node | Edge | null>(null);

  const { nodes, edges } = useMemo(
    () => (projectConfig ? transformToFlowData(projectConfig) : { nodes: [], edges: [] }),
    [projectConfig]
  );

  const onNodeClick = (_event: React.MouseEvent, node: Node) => {
    setSelectedElement(node);
  };

  const onEdgeClick = (_event: React.MouseEvent, edge: Edge) => {
    setSelectedElement(edge);
  };

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }} data-testid="loader">
        <Spin size="large" tip="Loading project..." />
      </div>
    );
  }

  if (error) {
    return <Empty description={<span><strong>Error:</strong> {error}</span>} />;
  }

  if (!projectConfig) {
    return <Empty description="No project loaded. Please select an example from the header." />;
  }

  const componentTypes = projectConfig.components ? Object.keys(projectConfig.components) : [];

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 112px)', gap: '16px' }}>
      {/* Left Panel: Component Library */}
      <Card title="Component Library" style={{ width: '20%' }}>
        <List
          dataSource={componentTypes}
          renderItem={item => <List.Item>{item}</List.Item>}
        />
      </Card>

      {/* Center Panel: Canvas */}
      <div style={{ flex: 1, border: '1px solid #f0f0f0' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodeClick={onNodeClick}
          onEdgeClick={onEdgeClick}
          fitView
        >
          <Controls />
          <MiniMap />
          <Background gap={12} size={1} />
        </ReactFlow>
      </div>

      {/* Right Panel: Parameters */}
      <Card title="Parameters" style={{ width: '25%' }}>
        {selectedElement ? (
          <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
            {JSON.stringify(selectedElement.data, null, 2)}
          </pre>
        ) : (
          <p>Click on a node or edge to see its parameters.</p>
        )}
      </Card>
    </div>
  );
};

export default ModelingPage;
