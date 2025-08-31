import { create } from 'zustand';
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';
import { Layout } from 'react-grid-layout';
import type { Node, Edge } from 'reactflow';
import { transformToFlowData } from '../utils/flow-transformer';

const API_BASE_URL = 'http://localhost:8000/api';
const WS_BASE_URL = 'ws://localhost:8000/ws';

export interface ChartConfig {
  id: string;
  variables: string[];
}

export type DataPoint = {
  timestamp: number;
  [key: string]: number;
};

interface SimulationState {
  sessionId: string | null;
  isRunning: boolean;
  isPaused: boolean;
  isLoading: boolean;
  ws: WebSocket | null;
  layouts: { [breakpoint: string]: Layout[] };
  charts: ChartConfig[];
  data: DataPoint[];
  availableVariables: string[];
  liveNodes: Node[];
  liveEdges: Edge[];

  startSimulation: (projectConfig: any, scenarioScript?: any[]) => Promise<void>;
  stopSimulation: () => Promise<void>;
  pauseSimulation: () => void;
  resumeSimulation: () => void;
  addChart: (variable: string) => void;
  removeChart: (chartId: string) => void;
  updateLayouts: (layouts: { [breakpoint: string]: Layout[] }) => void;

  _handleWebSocketMessage: (event: MessageEvent) => void;
}

export const useSimulationStore = create<SimulationState>((set, get) => ({
  sessionId: null,
  isRunning: false,
  isPaused: false,
  isLoading: false,
  ws: null,
  layouts: {},
  charts: [],
  data: [],
  availableVariables: [],
  liveNodes: [],
  liveEdges: [],

  startSimulation: async (projectConfig, scenarioScript) => {
    if (get().isRunning) return;

    const configToSend = {
      ...projectConfig,
      agents: {
        ...projectConfig.agents,
        scenario_agent: {
          class: 'core_lib.mission.scenario_agent.ScenarioAgent',
          scenario_script: scenarioScript,
        }
      }
    };

    const { nodes, edges } = transformToFlowData(projectConfig);
    set({
      isLoading: true,
      data: [],
      charts: [],
      layouts: {},
      availableVariables: projectConfig?.output?.variables ?? [],
      liveNodes: nodes,
      liveEdges: edges,
    });

    try {
      const createResponse = await axios.post(`${API_BASE_URL}/simulations`, configToSend);
      const newSessionId = createResponse.data.session_id;
      set({ sessionId: newSessionId });

      const ws = new WebSocket(`${WS_BASE_URL}/simulations/${newSessionId}`);
      ws.onmessage = get()._handleWebSocketMessage;

      ws.onopen = async () => {
        await axios.post(`${API_BASE_URL}/simulations/${newSessionId}/start`);
        set({ isRunning: true, isLoading: false, ws });
      };

      ws.onerror = () => set({ isLoading: false, isRunning: false });

    } catch (error) {
      set({ isLoading: false });
    }
  },

  stopSimulation: async () => {
    const { sessionId, ws } = get();
    if (!sessionId) return;
    try {
      await axios.post(`${API_BASE_URL}/simulations/${sessionId}/stop`);
      ws?.close();
    } finally {
      set({ isRunning: false, sessionId: null, ws: null, liveNodes: [], liveEdges: [] });
    }
  },

  pauseSimulation: () => set({ isPaused: true }),
  resumeSimulation: () => set({ isPaused: false }),

  addChart: (variable) => set(state => {
    const newChartId = `chart-${uuidv4()}`;
    const newChart: ChartConfig = { id: newChartId, variables: [variable] };
    const newLayoutItem: Layout = {
      i: newChartId,
      x: (state.charts.length * 6) % 12,
      y: Infinity,
      w: 6,
      h: 5,
    };
    return {
      charts: [...state.charts, newChart],
      layouts: { lg: [...(state.layouts.lg || []), newLayoutItem] },
    };
  }),

  removeChart: (chartId) => set(state => ({
    charts: state.charts.filter(c => c.id !== chartId),
    layouts: { lg: state.layouts.lg?.filter(l => l.i !== chartId) },
  })),

  updateLayouts: (layouts) => set({ layouts }),

  _handleWebSocketMessage: (event) => {
    const message = JSON.parse(event.data);
    if (message.type === 'data') {
      const payload = message.payload;
      set(state => {
        const newLiveNodes = state.liveNodes.map(node => {
          const nodeVarKey = Object.keys(payload).find(k => k.startsWith(node.id));
          if (nodeVarKey) {
            const value = payload[nodeVarKey];
            const intensity = Math.min(255, Math.floor(value * 25));
            return {
              ...node,
              style: { ...node.style, backgroundColor: `rgb(255, ${255 - intensity}, ${255 - intensity})` },
            };
          }
          return node;
        });

        return {
          data: [...state.data, payload],
          liveNodes: newLiveNodes
        };
      });
    } else if (message.type === 'status' && message.payload.includes('finished')) {
      get().stopSimulation();
    }
  },
}));
