import React, { useMemo, useState, useCallback } from 'react';
import { useProjectStore } from '../store/projectStore';
import { Empty, Spin, Card, List, Button, Space, message } from 'antd';
import ReactFlow, { 
  MiniMap, 
  Controls, 
  Background, 
  Node, 
  Edge, 
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  EdgeChange,
  NodeChange,
  applyNodeChanges,
  applyEdgeChanges
} from 'reactflow';
import 'reactflow/dist/style.css';
import { PlusOutlined, DeleteOutlined, SaveOutlined, FolderOutlined } from '@ant-design/icons';

import { transformToFlowData } from '../utils/flow-transformer';
import ParameterPanel from '../components/ParameterPanel';
import ComponentLibrary from '../components/ComponentLibrary';
import ProjectManager from '../components/ProjectManager';
import ValidationPanel from '../components/ValidationPanel';

const ModelingPage: React.FC = () => {
  const { projectConfig, isLoading, error, updateProjectConfig } = useProjectStore();
  const [selectedElement, setSelectedElement] = useState<Node | Edge | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [showProjectManager, setShowProjectManager] = useState(false);
  const [showValidation, setShowValidation] = useState(true);

  const initialData = useMemo(
    () => (projectConfig ? transformToFlowData(projectConfig) : { nodes: [], edges: [] }),
    [projectConfig]
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(initialData.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialData.edges);

  const onNodeClick = useCallback((_event: React.MouseEvent, node: Node) => {
    setSelectedElement(node);
  }, []);

  const onEdgeClick = useCallback((_event: React.MouseEvent, edge: Edge) => {
    setSelectedElement(edge);
  }, []);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onAddNode = useCallback((componentType: string) => {
    // Get default parameters based on component type
    const getDefaultParameters = (type: string) => {
      const parameterMap: Record<string, any> = {
        'Pipe': { length: 100, diameter: 0.3, roughness: 0.01, material: 'PVC' },
        'Pump': { power: 1000, efficiency: 0.85, maxFlow: 50, maxHead: 100 },
        'Valve': { type: 'gate', diameter: 0.2, coefficient: 0.8, status: 'open' },
        'Tank': { capacity: 1000, initialLevel: 0.5, diameter: 10, height: 15 },
        'Sensor': { type: 'pressure', range: [0, 100], accuracy: 0.1, location: 'inlet' },
        'Controller': { kp: 1.0, ki: 0.1, kd: 0.01, setpoint: 50 },
        'Reservoir': { head: 100, temperature: 20, quality: 'good' },
        'Demand': { baseFlow: 10, pattern: 'residential', priority: 1 }
      };
      return parameterMap[type] || {};
    };

    const newNode: Node = {
      id: `${componentType}-${Date.now()}`,
      type: 'default',
      position: { x: Math.random() * 400, y: Math.random() * 400 },
      data: {
        label: componentType,
        type: componentType,
        parameters: getDefaultParameters(componentType)
      }
    };
    setNodes((nds) => [...nds, newNode]);
    message.success(`Added ${componentType} component`);
  }, [setNodes]);

  const onDeleteSelected = useCallback(() => {
    if (selectedElement) {
      if ('source' in selectedElement) {
        // It's an edge
        setEdges((eds) => eds.filter((e) => e.id !== selectedElement.id));
      } else {
        // It's a node
        setNodes((nds) => nds.filter((n) => n.id !== selectedElement.id));
        setEdges((eds) => eds.filter((e) => e.source !== selectedElement.id && e.target !== selectedElement.id));
      }
      setSelectedElement(null);
      message.success('Element deleted');
    }
  }, [selectedElement, setNodes, setEdges]);

  const onSaveProject = useCallback(() => {
    // Convert nodes and edges back to project config format
    // This is a simplified implementation
    const updatedConfig = {
      ...projectConfig,
      // Add logic to convert ReactFlow data back to project config
      nodes: nodes,
      edges: edges
    };
    
    updateProjectConfig(updatedConfig);
    message.success('Project saved successfully');
    setIsEditing(false);
  }, [nodes, edges, projectConfig, updateProjectConfig]);

  const handleSaveProjectAs = useCallback((projectData: any) => {
    updateProjectConfig(projectData);
    // In a real implementation, you would call an API to save the project
    console.log('Saving project:', projectData);
  }, [updateProjectConfig]);

  const handleLoadProject = useCallback((projectData: any) => {
    updateProjectConfig(projectData);
    // Reset the flow data
    const flowData = transformToFlowData(projectData);
    setNodes(flowData.nodes);
    setEdges(flowData.edges);
    setSelectedElement(null);
  }, [updateProjectConfig, setNodes, setEdges]);

  const toggleEditMode = useCallback(() => {
    setIsEditing(!isEditing);
    if (!isEditing) {
      message.info('Edit mode enabled. You can now modify the topology.');
    }
  }, [isEditing]);

  const onUpdateElement = useCallback((elementId: string, newData: any) => {
    if ('source' in selectedElement!) {
      // It's an edge
      setEdges((eds) => eds.map((edge) => 
        edge.id === elementId 
          ? { ...edge, data: newData }
          : edge
      ));
    } else {
      // It's a node
      setNodes((nds) => nds.map((node) => 
        node.id === elementId 
          ? { ...node, data: newData }
          : node
      ));
    }
    message.success('Element updated successfully');
  }, [selectedElement, setNodes, setEdges]);

  const onSelectElementFromValidation = useCallback((elementId: string) => {
    const node = nodes.find(n => n.id === elementId);
    const edge = edges.find(e => e.id === elementId);
    const element = node || edge;
    if (element) {
      setSelectedElement(element);
      message.info(`Selected ${node ? 'node' : 'edge'}: ${elementId}`);
    }
  }, [nodes, edges]);

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
      <div style={{ width: '25%', display: 'flex', flexDirection: 'column' }}>
        <ComponentLibrary 
          isEditing={isEditing}
          onAddComponent={onAddNode}
          onToggleEditMode={toggleEditMode}
        />
        
        {isEditing && (
          <Card 
            title="Actions" 
            size="small" 
            style={{ marginTop: '8px' }}
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              <Button 
                type="primary"
                icon={<SaveOutlined />}
                onClick={onSaveProject}
                block
              >
                Quick Save
              </Button>
              <Button 
                icon={<FolderOutlined />}
                onClick={() => setShowProjectManager(true)}
                block
              >
                Project Manager
              </Button>
              {selectedElement && (
                <Button 
                  danger
                  icon={<DeleteOutlined />}
                  onClick={onDeleteSelected}
                  block
                >
                  Delete Selected
                </Button>
              )}
            </Space>
          </Card>
        )}
      </div>

      {/* Center Panel: Canvas */}
      <div style={{ flex: 1, border: '1px solid #f0f0f0' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={isEditing ? onNodesChange : undefined}
          onEdgesChange={isEditing ? onEdgesChange : undefined}
          onConnect={isEditing ? onConnect : undefined}
          onNodeClick={onNodeClick}
          onEdgeClick={onEdgeClick}
          nodesDraggable={isEditing}
          nodesConnectable={isEditing}
          elementsSelectable={true}
          fitView
        >
          <Controls />
          <MiniMap />
          <Background gap={12} size={1} />
        </ReactFlow>
      </div>

      {/* Right Panel: Parameters & Validation */}
      <div style={{ width: '30%', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <Card title="Parameters" style={{ flex: showValidation ? '1' : '2', overflow: 'auto' }}>
          <ParameterPanel 
            selectedElement={selectedElement}
            isEditing={isEditing}
            onUpdateElement={onUpdateElement}
          />
        </Card>
        
        {showValidation && (
          <Card 
            title="Validation" 
            size="small"
            style={{ flex: '1', overflow: 'auto' }}
            extra={
              <Button 
                type="text" 
                size="small"
                onClick={() => setShowValidation(false)}
              >
                ×
              </Button>
            }
          >
            <ValidationPanel 
              nodes={nodes}
              edges={edges}
              onSelectElement={onSelectElementFromValidation}
            />
          </Card>
        )}
        
        {!showValidation && (
          <Button 
            type="dashed"
            size="small"
            onClick={() => setShowValidation(true)}
            style={{ alignSelf: 'flex-start' }}
          >
            Show Validation
          </Button>
        )}
      </div>
      
      {/* Project Manager Modal */}
      <ProjectManager 
        visible={showProjectManager}
        onClose={() => setShowProjectManager(false)}
        currentProject={{
          name: projectConfig?.name || 'Untitled Project',
          description: projectConfig?.description || '',
          nodes: nodes,
          edges: edges,
          ...projectConfig
        }}
        onSaveProject={handleSaveProjectAs}
        onLoadProject={handleLoadProject}
      />
    </div>
  );
};

export default ModelingPage;
