import React, { useMemo, useState, useRef, useCallback, DragEvent } from 'react';
import { useProjectStore } from '../store/projectStore';
import { Empty, Spin, Card, List, message } from 'antd';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  Node,
  Edge,
  ReactFlowProvider, // Import ReactFlowProvider
  ReactFlowInstance,
  Connection,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { v4 as uuidv4 } from 'uuid';

import { transformToFlowData } from '../utils/flow-transformer';
import { isValidConnection as validateConnection } from '../utils/connection-validator';
import ParameterEditor from '../components/ParameterEditor';

// Define a list of components that can be dragged from the library
const availableComponents = [
  { label: 'Reservoir', class: 'core_lib.physical_objects.reservoir.Reservoir' },
  { label: 'Gate', class: 'core_lib.physical_objects.gate.Gate' },
  { label: 'Valve', class: 'core_lib.physical_objects.valve.Valve' },
  { label: 'Pump', class: 'core_lib.physical_objects.pump.Pump' },
  { label: 'Pipe', class: 'core_lib.physical_objects.pipe.Pipe' },
];

const onDragStart = (event: DragEvent, componentClass: string) => {
  event.dataTransfer.setData('application/reactflow', componentClass);
  event.dataTransfer.effectAllowed = 'move';
};

const ModelingPageContent: React.FC = () => {
  const { projectConfig, isLoading, error, addComponent, deleteElements, addConnection } = useProjectStore();
  const [selectedElement, setSelectedElement] = useState<Node | Edge | null>(null);
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null);

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

  const onNodesDelete = useCallback((deleted: Node[]) => {
    deleteElements({ nodes: deleted, edges: [] });
  }, [deleteElements]);

  const onEdgesDelete = useCallback((deleted: Edge[]) => {
    deleteElements({ nodes: [], edges: deleted });
  }, [deleteElements]);

  const onConnect = useCallback((connection: Connection) => {
    if (validateConnection(connection, nodes, edges)) {
      addConnection({ source: connection.source, target: connection.target });
    } else {
      message.error('This connection is not allowed.');
    }
  }, [addConnection, nodes, edges]);

  const isValidConnection = (connection: Connection) => validateConnection(connection, nodes, edges);

  const onDragOver = useCallback((event: DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: DragEvent) => {
      event.preventDefault();

      if (!reactFlowInstance || !reactFlowWrapper.current) {
        return;
      }

      const componentClass = event.dataTransfer.getData('application/reactflow');
      if (!componentClass) {
        return;
      }

      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      const componentName = componentClass.split('.').pop() ?? 'Component';
      const newNodeId = `${componentName}_${uuidv4().substring(0, 4)}`;

      const newComponent = {
        id: newNodeId,
        class: componentClass,
        name: newNodeId,
        // Add default parameters based on component type later if needed
        initial_state: {},
        parameters: {},
      };

      addComponent(newComponent);
    },
    [reactFlowInstance, addComponent]
  );

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

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 112px)', gap: '16px' }}>
      {/* Left Panel: Component Library */}
      <Card title="Component Library" style={{ width: '20%' }}>
        <List
          dataSource={availableComponents}
          renderItem={item => (
            <List.Item
              onDragStart={(event) => onDragStart(event, item.class)}
              draggable
              style={{ cursor: 'grab', border: '1px solid #f0f0f0', padding: '8px', marginBottom: '8px', borderRadius: '4px' }}
            >
              {item.label}
            </List.Item>
          )}
        />
      </Card>

      {/* Center Panel: Canvas */}
      <div style={{ flex: 1, border: '1px solid #f0f0f0' }} ref={reactFlowWrapper}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodeClick={onNodeClick}
          onEdgeClick={onEdgeClick}
          onNodesDelete={onNodesDelete}
          onEdgesDelete={onEdgesDelete}
          onConnect={onConnect}
          isValidConnection={isValidConnection}
          onInit={setReactFlowInstance}
          onDrop={onDrop}
          onDragOver={onDragOver}
          fitView
        >
          <Controls />
          <MiniMap />
          <Background gap={12} size={1} />
        </ReactFlow>
      </div>

      {/* Right Panel: Parameters */}
      <Card title="Parameters" style={{ width: '25%', overflowY: 'auto' }}>
        <ParameterEditor element={selectedElement} />
      </Card>
    </div>
  );
};

// Wrap ModelingPage with ReactFlowProvider
const ModelingPage: React.FC = () => (
  <ReactFlowProvider>
    <ModelingPageContent />
  </ReactFlowProvider>
);


export default ModelingPage;
