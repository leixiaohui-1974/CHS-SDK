import type { Node, Edge } from 'reactflow';

type ProjectComponent = {
  id: string;
  class: string;
  [key: string]: any;
};

type ProjectConnection = {
  source: string;
  target: string;
  [key: string]: any;
};

type ProjectConfig = {
  components: ProjectComponent[] | { [key: string]: ProjectComponent[] }; // Can be array or object of arrays
  topology: {
    connections: ProjectConnection[];
  };
};

export const transformToFlowData = (projectConfig: ProjectConfig): { nodes: Node[], edges: Edge[] } => {
  const nodes: Node[] = [];
  const edges: Edge[] = [];
  let allComponents: ProjectComponent[] = [];

  if (projectConfig && projectConfig.components) {
    if (Array.isArray(projectConfig.components)) {
      allComponents = projectConfig.components;
    } else if (typeof projectConfig.components === 'object') {
      allComponents = Object.values(projectConfig.components).flat();
    }

    allComponents.forEach((component, index) => {
      if (!component || !component.id) return;
      nodes.push({
        id: component.id,
        type: 'default',
        data: { label: `${component.id} (${component.class.split('.').pop()})`, ...component },
        position: { x: (index % 4) * 250, y: Math.floor(index / 4) * 120 },
      });
    });
  }

  if (projectConfig && projectConfig.topology && projectConfig.topology.connections) {
    projectConfig.topology.connections.forEach((connection, index) => {
      if (!connection || !connection.source || !connection.target) return;
      edges.push({
        id: `e-${connection.source}-${connection.target}-${index}`,
        source: connection.source,
        target: connection.target,
        data: { ...connection },
      });
    });
  }

  return { nodes, edges };
};
