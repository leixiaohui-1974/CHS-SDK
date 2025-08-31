import { Node, Edge } from 'reactflow';

// Define more specific types based on observed projectConfig structure
type ProjectComponent = {
  id: string;
  class: string;
  [key: string]: any;
};

type ComponentCategory = ProjectComponent[];

type ProjectComponents = {
  [category: string]: ComponentCategory;
};

type ProjectConnection = {
  source: string;
  target: string;
  [key: string]: any;
};

type ProjectConfig = {
  components: ProjectComponents;
  topology: {
    connections: ProjectConnection[];
  };
};

/**
 * Transforms project configuration data into a format compatible with React Flow.
 * @param projectConfig The project configuration object from the backend.
 * @returns An object containing arrays of nodes and edges for React Flow.
 */
export const transformToFlowData = (projectConfig: ProjectConfig) => {
  const nodes: Node[] = [];
  const edges: Edge[] = [];

  if (projectConfig && projectConfig.components) {
    // Flatten all components from their categories into a single array
    const allComponents: ProjectComponent[] = Object.values(projectConfig.components).flat();

    allComponents.forEach((component, index) => {
      if (!component || !component.id) return; // Skip invalid components

      nodes.push({
        id: component.id,
        type: 'default', // Can be customized later
        data: {
          label: `${component.id} (${component.class.split('.').pop()})`,
          ...component
        },
        position: { x: (index % 4) * 250, y: Math.floor(index / 4) * 120 }, // A simple grid layout
      });
    });
  }

  if (projectConfig && projectConfig.topology && projectConfig.topology.connections) {
    projectConfig.topology.connections.forEach((connection, index) => {
      if (!connection || !connection.source || !connection.target) return; // Skip invalid connections

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
