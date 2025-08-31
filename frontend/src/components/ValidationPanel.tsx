import React, { useMemo } from 'react';
import { Card, Alert, List, Tag, Button, Space, Tooltip, Progress } from 'antd';
import { CheckCircleOutlined, ExclamationCircleOutlined, CloseCircleOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { Node, Edge } from 'reactflow';

interface ValidationIssue {
  id: string;
  type: 'error' | 'warning' | 'info';
  category: 'topology' | 'parameters' | 'configuration';
  message: string;
  elementId?: string;
  suggestion?: string;
}

interface ValidationPanelProps {
  nodes: Node[];
  edges: Edge[];
  onSelectElement?: (elementId: string) => void;
}

const ValidationPanel: React.FC<ValidationPanelProps> = ({
  nodes,
  edges,
  onSelectElement
}) => {
  const validationResults = useMemo(() => {
    const issues: ValidationIssue[] = [];

    // Topology validation
    const validateTopology = () => {
      // Check for isolated nodes
      const connectedNodes = new Set<string>();
      edges.forEach(edge => {
        connectedNodes.add(edge.source);
        connectedNodes.add(edge.target);
      });

      nodes.forEach(node => {
        if (!connectedNodes.has(node.id)) {
          issues.push({
            id: `isolated-${node.id}`,
            type: 'warning',
            category: 'topology',
            message: `Node "${node.data?.label || node.id}" is not connected to any other component`,
            elementId: node.id,
            suggestion: 'Connect this node to other components or remove it if not needed'
          });
        }
      });

      // Check for circular connections (simplified)
      const checkCircularConnections = () => {
        const visited = new Set<string>();
        const recursionStack = new Set<string>();

        const hasCycle = (nodeId: string): boolean => {
          if (recursionStack.has(nodeId)) return true;
          if (visited.has(nodeId)) return false;

          visited.add(nodeId);
          recursionStack.add(nodeId);

          const outgoingEdges = edges.filter(edge => edge.source === nodeId);
          for (const edge of outgoingEdges) {
            if (hasCycle(edge.target)) return true;
          }

          recursionStack.delete(nodeId);
          return false;
        };

        for (const node of nodes) {
          if (!visited.has(node.id) && hasCycle(node.id)) {
            issues.push({
              id: 'circular-connection',
              type: 'error',
              category: 'topology',
              message: 'Circular connection detected in the network',
              suggestion: 'Review the connections to eliminate circular dependencies'
            });
            break;
          }
        }
      };

      checkCircularConnections();

      // Check for required components
      const componentTypes = nodes.map(node => node.data?.type).filter(Boolean);
      const hasReservoir = componentTypes.includes('Reservoir');
      const hasDemand = componentTypes.includes('Demand');

      if (!hasReservoir) {
        issues.push({
          id: 'missing-reservoir',
          type: 'error',
          category: 'topology',
          message: 'No water source (Reservoir) found in the network',
          suggestion: 'Add at least one Reservoir component to provide water supply'
        });
      }

      if (!hasDemand) {
        issues.push({
          id: 'missing-demand',
          type: 'warning',
          category: 'topology',
          message: 'No demand nodes found in the network',
          suggestion: 'Add Demand components to represent water consumption points'
        });
      }
    };

    // Parameter validation
    const validateParameters = () => {
      nodes.forEach(node => {
        const { data } = node;
        const { type, parameters } = data || {};

        if (!parameters) {
          issues.push({
            id: `no-params-${node.id}`,
            type: 'warning',
            category: 'parameters',
            message: `Node "${data?.label || node.id}" has no parameters defined`,
            elementId: node.id,
            suggestion: 'Define appropriate parameters for this component'
          });
          return;
        }

        // Type-specific parameter validation
        switch (type) {
          case 'Pipe':
            if (!parameters.length || parameters.length <= 0) {
              issues.push({
                id: `pipe-length-${node.id}`,
                type: 'error',
                category: 'parameters',
                message: `Pipe "${data?.label || node.id}" has invalid length`,
                elementId: node.id,
                suggestion: 'Set a positive length value for the pipe'
              });
            }
            if (!parameters.diameter || parameters.diameter <= 0) {
              issues.push({
                id: `pipe-diameter-${node.id}`,
                type: 'error',
                category: 'parameters',
                message: `Pipe "${data?.label || node.id}" has invalid diameter`,
                elementId: node.id,
                suggestion: 'Set a positive diameter value for the pipe'
              });
            }
            break;

          case 'Pump':
            if (!parameters.power || parameters.power <= 0) {
              issues.push({
                id: `pump-power-${node.id}`,
                type: 'error',
                category: 'parameters',
                message: `Pump "${data?.label || node.id}" has invalid power rating`,
                elementId: node.id,
                suggestion: 'Set a positive power value for the pump'
              });
            }
            if (parameters.efficiency && (parameters.efficiency <= 0 || parameters.efficiency > 1)) {
              issues.push({
                id: `pump-efficiency-${node.id}`,
                type: 'warning',
                category: 'parameters',
                message: `Pump "${data?.label || node.id}" has unrealistic efficiency`,
                elementId: node.id,
                suggestion: 'Set efficiency between 0 and 1 (0-100%)'
              });
            }
            break;

          case 'Tank':
            if (!parameters.capacity || parameters.capacity <= 0) {
              issues.push({
                id: `tank-capacity-${node.id}`,
                type: 'error',
                category: 'parameters',
                message: `Tank "${data?.label || node.id}" has invalid capacity`,
                elementId: node.id,
                suggestion: 'Set a positive capacity value for the tank'
              });
            }
            if (parameters.initialLevel && (parameters.initialLevel < 0 || parameters.initialLevel > 1)) {
              issues.push({
                id: `tank-level-${node.id}`,
                type: 'warning',
                category: 'parameters',
                message: `Tank "${data?.label || node.id}" has invalid initial level`,
                elementId: node.id,
                suggestion: 'Set initial level between 0 and 1 (0-100%)'
              });
            }
            break;
        }
      });
    };

    // Configuration validation
    const validateConfiguration = () => {
      if (nodes.length === 0) {
        issues.push({
          id: 'empty-network',
          type: 'error',
          category: 'configuration',
          message: 'Network is empty',
          suggestion: 'Add components to create a hydraulic network'
        });
      }

      if (edges.length === 0 && nodes.length > 1) {
        issues.push({
          id: 'no-connections',
          type: 'error',
          category: 'configuration',
          message: 'No connections between components',
          suggestion: 'Connect components to create a functional network'
        });
      }

      // Check for duplicate node IDs (shouldn't happen but good to check)
      const nodeIds = nodes.map(node => node.id);
      const duplicateIds = nodeIds.filter((id, index) => nodeIds.indexOf(id) !== index);
      if (duplicateIds.length > 0) {
        issues.push({
          id: 'duplicate-ids',
          type: 'error',
          category: 'configuration',
          message: `Duplicate component IDs found: ${duplicateIds.join(', ')}`,
          suggestion: 'Ensure all components have unique identifiers'
        });
      }
    };

    validateTopology();
    validateParameters();
    validateConfiguration();

    return issues;
  }, [nodes, edges]);

  const getIssueIcon = (type: ValidationIssue['type']) => {
    switch (type) {
      case 'error': return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'warning': return <ExclamationCircleOutlined style={{ color: '#faad14' }} />;
      case 'info': return <InfoCircleOutlined style={{ color: '#1890ff' }} />;
      default: return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
    }
  };

  const getIssueColor = (type: ValidationIssue['type']) => {
    switch (type) {
      case 'error': return 'error';
      case 'warning': return 'warning';
      case 'info': return 'processing';
      default: return 'success';
    }
  };

  const errorCount = validationResults.filter(issue => issue.type === 'error').length;
  const warningCount = validationResults.filter(issue => issue.type === 'warning').length;
  const infoCount = validationResults.filter(issue => issue.type === 'info').length;

  const overallScore = Math.max(0, 100 - (errorCount * 20 + warningCount * 5));
  const scoreColor = overallScore >= 80 ? '#52c41a' : overallScore >= 60 ? '#faad14' : '#ff4d4f';

  return (
    <Card 
      title="Validation Results" 
      size="small"
      extra={
        <Space>
          <Tag color={getIssueColor('error')}>{errorCount} Errors</Tag>
          <Tag color={getIssueColor('warning')}>{warningCount} Warnings</Tag>
          <Tag color={getIssueColor('info')}>{infoCount} Info</Tag>
        </Space>
      }
    >
      <div style={{ marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
          <span style={{ marginRight: '8px' }}>Network Health:</span>
          <Progress 
            percent={overallScore} 
            size="small" 
            strokeColor={scoreColor}
            style={{ flex: 1 }}
          />
        </div>
      </div>

      {validationResults.length === 0 ? (
        <Alert
          message="All validations passed!"
          description="Your network configuration looks good."
          type="success"
          icon={<CheckCircleOutlined />}
          showIcon
        />
      ) : (
        <List
          dataSource={validationResults}
          size="small"
          renderItem={(issue) => (
            <List.Item
              actions={issue.elementId && onSelectElement ? [
                <Button 
                  key="select"
                  type="link" 
                  size="small"
                  onClick={() => onSelectElement(issue.elementId!)}
                >
                  Select
                </Button>
              ] : []}
            >
              <List.Item.Meta
                avatar={getIssueIcon(issue.type)}
                title={
                  <Space>
                    <span>{issue.message}</span>
                    <Tag size="small">{issue.category}</Tag>
                  </Space>
                }
                description={issue.suggestion && (
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    💡 {issue.suggestion}
                  </div>
                )}
              />
            </List.Item>
          )}
        />
      )}
    </Card>
  );
};

export default ValidationPanel;