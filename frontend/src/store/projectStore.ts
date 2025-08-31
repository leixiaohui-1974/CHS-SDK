import { create } from 'zustand';
import axios from 'axios';

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
  updateProjectConfig: (config: ProjectConfig) => void;
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
      // Axios handles URL encoding for path segments automatically.
      const response = await axios.get<ProjectConfig>(`${API_BASE_URL}/examples/${examplePath}`);
      set({ projectConfig: response.data, isLoading: false });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'An unknown error occurred.';
      console.error(`Failed to load project '${examplePath}':`, error);
      set({ error: `Failed to load project: ${message}`, isLoading: false, selectedExamplePath: null });
    }
  },

  updateProjectConfig: (config: ProjectConfig) => {
    set({ projectConfig: config });
  },
}));
