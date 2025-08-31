import { create } from 'zustand';
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';
import type { Node, Edge } from 'reactflow';

// In a real app, this would be in a .env file
const API_BASE_URL = 'http://localhost:8000/api';

// A more specific type for the project configuration can be defined later.
// For now, 'any' is a placeholder.
type ProjectConfig = any;

interface ProjectState {
  exampleList: string[];
  selectedExamplePath: string | null;
  projectConfig: ProjectConfig | null;
  isLoading: boolean;
  error: string | null;
  fetchExampleList: () => Promise<void>;
  loadProject: (examplePath: string) => Promise<void>;
  addComponent: (component: any) => void;
  deleteElements: (params: { nodes: Pick<Node, 'id'>[], edges: Pick<Edge, 'id'>[] }) => void;
  addConnection: (connection: { source: string | null; target: string | null }) => void;
  updateElementData: (elementId: string, newData: any) => void;
}

export const useProjectStore = create<ProjectState>((set) => ({
  exampleList: [],
  selectedExamplePath: null,
  projectConfig: null,
  isLoading: false,
  error: null,

  fetchExampleList: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await axios.get<string[]>(`${API_BASE_URL}/examples`);
      set({ exampleList: response.data, isLoading: false });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'An unknown error occurred.';
      console.error("Failed to fetch example list:", error);
      set({ error: `Failed to fetch example list: ${message}`, isLoading: false });
    }
  },

  loadProject: async (examplePath: string) => {
    set({ isLoading: true, error: null, projectConfig: null, selectedExamplePath: examplePath });
    try {
      const response = await axios.get<ProjectConfig>(`${API_BASE_URL}/examples/${examplePath}`);
      const projectConfig = response.data;

      // Add unique IDs to connections for easier manipulation
      if (projectConfig.topology && Array.isArray(projectConfig.topology.connections)) {
        projectConfig.topology.connections.forEach((c: any) => {
          if (!c._id) {
            c._id = uuidv4();
          }
        });
      }

      console.log('Received project config:', projectConfig); // <-- ADDED FOR DEBUGGING
      set({ projectConfig: projectConfig, isLoading: false });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'An unknown error occurred.';
      console.error(`Failed to load project '${examplePath}':`, error);
      set({ error: `Failed to load project: ${message}`, isLoading: false, selectedExamplePath: null });
    }
  },

  addComponent: (component) =>
    set((state) => {
      if (!state.projectConfig || !Array.isArray(state.projectConfig.components)) {
        console.error("Cannot add component: projectConfig or components array is not initialized.");
        return {};
      }

      const newProjectConfig = {
        ...state.projectConfig,
        components: [...state.projectConfig.components, component],
      };

      return { projectConfig: newProjectConfig };
    }),

  deleteElements: ({ nodes, edges }) =>
    set((state) => {
      if (!state.projectConfig) return {};

      const deletedNodeIds = new Set(nodes.map(n => n.id));
      const deletedEdgeIds = new Set(edges.map(e => e.id));

      const remainingComponents = state.projectConfig.components.filter(
        (c: any) => !deletedNodeIds.has(c.id)
      );

      const remainingConnections = state.projectConfig.topology.connections.filter(
        (c: any) => !deletedEdgeIds.has(c._id)
      );

      const newProjectConfig = {
        ...state.projectConfig,
        components: remainingComponents,
        topology: {
          ...state.projectConfig.topology,
          connections: remainingConnections,
        },
      };

      return { projectConfig: newProjectConfig };
    }),

  addConnection: (connection) =>
    set((state) => {
      if (!state.projectConfig || !state.projectConfig.topology || !Array.isArray(state.projectConfig.topology.connections)) {
        console.error("Cannot add connection: projectConfig or topology is not correctly initialized.");
        return {};
      }

      const newConnection = {
        ...connection,
        _id: uuidv4(),
      };

      const newProjectConfig = {
        ...state.projectConfig,
        topology: {
          ...state.projectConfig.topology,
          connections: [...state.projectConfig.topology.connections, newConnection],
        },
      };

      return { projectConfig: newProjectConfig };
    }),

  updateElementData: (elementId, newData) =>
    set((state) => {
      if (!state.projectConfig) return {};

      const newComponents = state.projectConfig.components.map((c: any) => {
        if (c.id === elementId) {
          return { ...c, ...newData };
        }
        return c;
      });

      const newConnections = state.projectConfig.topology.connections.map((c: any) => {
        if (c._id === elementId) {
          return { ...c, ...newData };
        }
        return c;
      });

      return {
        projectConfig: {
          ...state.projectConfig,
          components: newComponents,
          topology: {
            ...state.projectConfig.topology,
            connections: newConnections,
          },
        },
      };
    }),
}));
