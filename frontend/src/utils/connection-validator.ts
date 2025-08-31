import { Connection, Edge, Node } from 'reactflow';

// Define the port configuration for each component class.
// This is a frontend assumption for now and should ideally be driven by backend data.
const portConfig: { [key: string]: { inputs: number; outputs: number } } = {
  'core_lib.physical_objects.reservoir.Reservoir': { inputs: 0, outputs: 1 },
  'core_lib.physical_objects.gate.Gate': { inputs: 1, outputs: 1 },
  'core_lib.physical_objects.valve.Valve': { inputs: 1, outputs: 1 },
  'core_lib.physical_objects.pump.Pump': { inputs: 1, outputs: 1 },
  'core_lib.physical_objects.pipe.Pipe': { inputs: 1, outputs: 1 },
  // Add other components as needed
};

/**
 * Validates if a new connection is allowed based on node types and port availability.
 * @param connection The connection being attempted.
 * @param nodes The list of all nodes on the canvas.
 * @param edges The list of all edges on the canvas.
 * @returns boolean True if the connection is valid, false otherwise.
 */
export const isValidConnection = (
  connection: Connection,
  nodes: Node[],
  edges: Edge[]
): boolean => {
  if (!connection.source || !connection.target) {
    return false;
  }

  const sourceNode = nodes.find(node => node.id === connection.source);
  const targetNode = nodes.find(node => node.id === connection.target);

  if (!sourceNode || !targetNode) {
    return false;
  }

  const sourceClass = sourceNode.data.class;
  const targetClass = targetNode.data.class;

  const sourcePortConfig = portConfig[sourceClass] || { inputs: 1, outputs: 1 }; // Default
  const targetPortConfig = portConfig[targetClass] || { inputs: 1, outputs: 1 }; // Default

  // Rule 1: Source node must have available outputs.
  if (sourcePortConfig.outputs === 0) {
    console.warn(`Connection failed: Source node ${sourceNode.id} has no outputs.`);
    return false;
  }

  // Rule 2: Target node must have available inputs.
  if (targetPortConfig.inputs === 0) {
    console.warn(`Connection failed: Target node ${targetNode.id} has no inputs.`);
    return false;
  }

  // Rule 3: Target input port cannot have more than one connection.
  const existingConnectionsToTarget = edges.filter(
    edge => edge.target === connection.target
  );

  if (existingConnectionsToTarget.length >= targetPortConfig.inputs) {
    console.warn(`Connection failed: Target node ${targetNode.id} input is already full.`);
    return false;
  }

  // Rule 4: Cannot connect a node to itself.
  if (connection.source === connection.target) {
    return false;
  }

  return true;
};
