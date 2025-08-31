import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { ApiService, SimulationRequest, SimulationSession, SimulationStatus } from '../services/apiService';
import { WebSocketManager, WebSocketManagerFactory, SimulationData, ConnectionState } from '../services/websocketManager';

// 仿真状态枚举
export enum SimulationState {
  IDLE = 'idle',
  CREATING = 'creating',
  STARTING = 'starting',
  RUNNING = 'running',
  PAUSED = 'paused',
  STOPPING = 'stopping',
  STOPPED = 'stopped',
  ERROR = 'error'
}

// 实时数据接口
export interface RealtimeData {
  timestamp: number;
  components: Map<string, SimulationData>;
  statistics: {
    totalComponents: number;
    activeComponents: number;
    averageWaterLevel: number;
    totalFlowRate: number;
    maxPressure: number;
    minPressure: number;
  };
}

// 历史数据接口
export interface HistoricalData {
  timeRange: [number, number];
  data: SimulationData[];
  aggregatedData: {
    hourly: SimulationData[];
    daily: SimulationData[];
  };
}

// 错误信息接口
export interface ErrorInfo {
  id: string;
  timestamp: number;
  type: 'connection' | 'simulation' | 'api' | 'validation';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  details?: any;
  resolved: boolean;
}

// 性能指标接口
export interface PerformanceMetrics {
  fps: number;
  latency: number;
  memoryUsage: number;
  cpuUsage: number;
  networkBandwidth: number;
  simulationSpeed: number;
  lastUpdated: number;
}

// Store状态接口
export interface SimulationStoreState {
  // 基本状态
  currentState: SimulationState;
  isLoading: boolean;
  error: string | null;
  
  // 会话管理
  currentSession: SimulationSession | null;
  sessionHistory: SimulationSession[];
  
  // WebSocket连接
  connectionState: ConnectionState;
  wsManager: WebSocketManager | null;
  
  // 仿真数据
  realtimeData: RealtimeData | null;
  historicalData: HistoricalData | null;
  
  // 错误管理
  errors: ErrorInfo[];
  
  // 性能监控
  performance: PerformanceMetrics;
  
  // 配置
  simulationConfig: SimulationRequest | null;
  
  // Actions
  actions: {
    // 会话管理
    createSession: (config: SimulationRequest) => Promise<void>;
    startSimulation: () => Promise<void>;
    pauseSimulation: () => Promise<void>;
    resumeSimulation: () => Promise<void>;
    stopSimulation: () => Promise<void>;
    
    // WebSocket管理
    connectWebSocket: () => Promise<void>;
    disconnectWebSocket: () => void;
    
    // 数据管理
    updateRealtimeData: (data: SimulationData) => void;
    clearHistoricalData: () => void;
    exportData: (format: 'json' | 'csv' | 'excel') => Promise<Blob>;
    
    // 错误管理
    addError: (error: Omit<ErrorInfo, 'id' | 'timestamp'>) => void;
    resolveError: (errorId: string) => void;
    clearErrors: () => void;
    
    // 性能监控
    updatePerformance: (metrics: Partial<PerformanceMetrics>) => void;
    
    // 配置管理
    updateConfig: (config: Partial<SimulationRequest>) => void;
    resetConfig: () => void;
    
    // 状态重置
    reset: () => void;
  };
}

// 初始状态
const initialState = {
  currentState: SimulationState.IDLE,
  isLoading: false,
  error: null,
  currentSession: null,
  sessionHistory: [],
  connectionState: ConnectionState.DISCONNECTED,
  wsManager: null,
  realtimeData: null,
  historicalData: null,
  errors: [],
  performance: {
    fps: 0,
    latency: 0,
    memoryUsage: 0,
    cpuUsage: 0,
    networkBandwidth: 0,
    simulationSpeed: 1.0,
    lastUpdated: Date.now()
  },
  simulationConfig: null
};

// API服务实例
const apiService = new ApiService();

// 创建Store
export const useSimulationStore = create<SimulationStoreState>()()
  (devtools(
    subscribeWithSelector((set, get) => ({
      ...initialState,
      
      actions: {
        // 创建仿真会话
        createSession: async (config: SimulationRequest) => {
          const state = get();
          
          try {
            set({ isLoading: true, error: null, currentState: SimulationState.CREATING });
            
            // 验证配置
            if (!config.components || Object.keys(config.components).length === 0) {
              throw new Error('仿真配置中必须包含至少一个组件');
            }
            
            // 创建会话
            const session = await apiService.createSimulation(config);
            
            // 更新状态
            set({
              currentSession: session,
              simulationConfig: config,
              sessionHistory: [...state.sessionHistory, session],
              currentState: SimulationState.IDLE,
              isLoading: false
            });
            
            // 自动连接WebSocket
            await get().actions.connectWebSocket();
            
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : '创建仿真会话失败';
            set({ 
              error: errorMessage, 
              isLoading: false, 
              currentState: SimulationState.ERROR 
            });
            
            get().actions.addError({
              type: 'api',
              severity: 'high',
              message: errorMessage,
              details: error
            });
            
            throw error;
          }
        },
        
        // 启动仿真
        startSimulation: async () => {
          const state = get();
          
          if (!state.currentSession) {
            throw new Error('没有活跃的仿真会话');
          }
          
          try {
            set({ isLoading: true, error: null, currentState: SimulationState.STARTING });
            
            await apiService.startSimulation(state.currentSession.session_id);
            
            set({ 
              currentState: SimulationState.RUNNING, 
              isLoading: false 
            });
            
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : '启动仿真失败';
            set({ 
              error: errorMessage, 
              isLoading: false, 
              currentState: SimulationState.ERROR 
            });
            
            get().actions.addError({
              type: 'simulation',
              severity: 'high',
              message: errorMessage,
              details: error
            });
            
            throw error;
          }
        },
        
        // 暂停仿真
        pauseSimulation: async () => {
          const state = get();
          
          if (!state.currentSession) {
            throw new Error('没有活跃的仿真会话');
          }
          
          try {
            set({ isLoading: true, error: null });
            
            await apiService.pauseSimulation(state.currentSession.session_id);
            
            set({ 
              currentState: SimulationState.PAUSED, 
              isLoading: false 
            });
            
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : '暂停仿真失败';
            set({ error: errorMessage, isLoading: false });
            throw error;
          }
        },
        
        // 恢复仿真
        resumeSimulation: async () => {
          const state = get();
          
          if (!state.currentSession) {
            throw new Error('没有活跃的仿真会话');
          }
          
          try {
            set({ isLoading: true, error: null });
            
            await apiService.resumeSimulation(state.currentSession.session_id);
            
            set({ 
              currentState: SimulationState.RUNNING, 
              isLoading: false 
            });
            
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : '恢复仿真失败';
            set({ error: errorMessage, isLoading: false });
            throw error;
          }
        },
        
        // 停止仿真
        stopSimulation: async () => {
          const state = get();
          
          if (!state.currentSession) {
            throw new Error('没有活跃的仿真会话');
          }
          
          try {
            set({ isLoading: true, error: null, currentState: SimulationState.STOPPING });
            
            await apiService.stopSimulation(state.currentSession.session_id);
            
            // 断开WebSocket连接
            get().actions.disconnectWebSocket();
            
            set({ 
              currentState: SimulationState.STOPPED, 
              isLoading: false,
              currentSession: null
            });
            
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : '停止仿真失败';
            set({ error: errorMessage, isLoading: false });
            throw error;
          }
        },
        
        // 连接WebSocket
        connectWebSocket: async () => {
          const state = get();
          
          if (!state.currentSession) {
            throw new Error('没有活跃的仿真会话');
          }
          
          try {
            // 断开现有连接
            if (state.wsManager) {
              state.wsManager.destroy();
            }
            
            // 创建新的WebSocket管理器
            const wsManager = WebSocketManagerFactory.getManager(
              state.currentSession.session_id,
              'ws://localhost:8000'
            );
            
            // 设置事件监听器
            wsManager.on('connected', () => {
              set({ connectionState: ConnectionState.CONNECTED });
            });
            
            wsManager.on('disconnected', () => {
              set({ connectionState: ConnectionState.DISCONNECTED });
            });
            
            wsManager.on('reconnecting', (attempts) => {
              set({ connectionState: ConnectionState.RECONNECTING });
            });
            
            wsManager.on('error', (error) => {
              set({ connectionState: ConnectionState.ERROR });
              get().actions.addError({
                type: 'connection',
                severity: 'medium',
                message: 'WebSocket连接错误',
                details: error
              });
            });
            
            wsManager.on('simulationData', (data: SimulationData) => {
              get().actions.updateRealtimeData(data);
            });
            
            wsManager.on('simulationState', (state) => {
              // 根据后端状态更新前端状态
              if (state.status === 'running') {
                set({ currentState: SimulationState.RUNNING });
              } else if (state.status === 'paused') {
                set({ currentState: SimulationState.PAUSED });
              } else if (state.status === 'stopped') {
                set({ currentState: SimulationState.STOPPED });
              }
            });
            
            // 连接WebSocket
            await wsManager.connect();
            
            set({ 
              wsManager, 
              connectionState: ConnectionState.CONNECTING 
            });
            
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'WebSocket连接失败';
            set({ connectionState: ConnectionState.ERROR });
            
            get().actions.addError({
              type: 'connection',
              severity: 'high',
              message: errorMessage,
              details: error
            });
            
            throw error;
          }
        },
        
        // 断开WebSocket
        disconnectWebSocket: () => {
          const state = get();
          
          if (state.wsManager) {
            state.wsManager.destroy();
            set({ 
              wsManager: null, 
              connectionState: ConnectionState.DISCONNECTED 
            });
          }
        },
        
        // 更新实时数据
        updateRealtimeData: (data: SimulationData) => {
          const state = get();
          
          // 更新组件数据
          const components = new Map(state.realtimeData?.components || []);
          components.set(data.id, data);
          
          // 计算统计信息
          const componentArray = Array.from(components.values());
          const statistics = {
            totalComponents: componentArray.length,
            activeComponents: componentArray.filter(c => c.water_level !== undefined).length,
            averageWaterLevel: componentArray.reduce((sum, c) => sum + (c.water_level || 0), 0) / componentArray.length,
            totalFlowRate: componentArray.reduce((sum, c) => sum + (c.flow_rate || 0), 0),
            maxPressure: Math.max(...componentArray.map(c => c.pressure || 0)),
            minPressure: Math.min(...componentArray.map(c => c.pressure || 0))
          };
          
          // 更新实时数据
          set({
            realtimeData: {
              timestamp: data.timestamp,
              components,
              statistics
            }
          });
          
          // 更新历史数据
          const historicalData = state.historicalData || {
            timeRange: [data.timestamp, data.timestamp],
            data: [],
            aggregatedData: { hourly: [], daily: [] }
          };
          
          historicalData.data.push(data);
          historicalData.timeRange[1] = data.timestamp;
          
          // 限制历史数据大小（保留最近1000条记录）
          if (historicalData.data.length > 1000) {
            historicalData.data = historicalData.data.slice(-1000);
            historicalData.timeRange[0] = historicalData.data[0].timestamp;
          }
          
          set({ historicalData });
        },
        
        // 清除历史数据
        clearHistoricalData: () => {
          set({ historicalData: null });
        },
        
        // 导出数据
        exportData: async (format: 'json' | 'csv' | 'excel') => {
          const state = get();
          
          if (!state.historicalData) {
            throw new Error('没有可导出的数据');
          }
          
          const data = state.historicalData.data;
          
          switch (format) {
            case 'json':
              return new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
              
            case 'csv':
              const headers = Object.keys(data[0] || {});
              const csvContent = [
                headers.join(','),
                ...data.map(row => headers.map(header => row[header] || '').join(','))
              ].join('\n');
              return new Blob([csvContent], { type: 'text/csv' });
              
            case 'excel':
              // 简化的Excel导出（实际项目中可能需要使用专门的库）
              const excelContent = [
                headers.join('\t'),
                ...data.map(row => headers.map(header => row[header] || '').join('\t'))
              ].join('\n');
              return new Blob([excelContent], { type: 'application/vnd.ms-excel' });
              
            default:
              throw new Error(`不支持的导出格式: ${format}`);
          }
        },
        
        // 添加错误
        addError: (error: Omit<ErrorInfo, 'id' | 'timestamp'>) => {
          const newError: ErrorInfo = {
            ...error,
            id: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            timestamp: Date.now(),
            resolved: false
          };
          
          set(state => ({
            errors: [...state.errors, newError]
          }));
        },
        
        // 解决错误
        resolveError: (errorId: string) => {
          set(state => ({
            errors: state.errors.map(error => 
              error.id === errorId ? { ...error, resolved: true } : error
            )
          }));
        },
        
        // 清除错误
        clearErrors: () => {
          set({ errors: [] });
        },
        
        // 更新性能指标
        updatePerformance: (metrics: Partial<PerformanceMetrics>) => {
          set(state => ({
            performance: {
              ...state.performance,
              ...metrics,
              lastUpdated: Date.now()
            }
          }));
        },
        
        // 更新配置
        updateConfig: (config: Partial<SimulationRequest>) => {
          set(state => ({
            simulationConfig: state.simulationConfig ? {
              ...state.simulationConfig,
              ...config
            } : null
          }));
        },
        
        // 重置配置
        resetConfig: () => {
          set({ simulationConfig: null });
        },
        
        // 重置状态
        reset: () => {
          const state = get();
          
          // 断开WebSocket连接
          if (state.wsManager) {
            state.wsManager.destroy();
          }
          
          // 重置状态
          set({
            ...initialState,
            actions: state.actions // 保留actions
          });
        }
      }
    })),
    {
      name: 'simulation-store',
      partialize: (state) => ({
        sessionHistory: state.sessionHistory,
        simulationConfig: state.simulationConfig
      })
    }
  ));

// 选择器函数
export const simulationSelectors = {
  // 基本状态选择器
  getCurrentState: (state: SimulationStoreState) => state.currentState,
  getIsLoading: (state: SimulationStoreState) => state.isLoading,
  getError: (state: SimulationStoreState) => state.error,
  
  // 会话选择器
  getCurrentSession: (state: SimulationStoreState) => state.currentSession,
  getSessionHistory: (state: SimulationStoreState) => state.sessionHistory,
  
  // 连接状态选择器
  getConnectionState: (state: SimulationStoreState) => state.connectionState,
  getIsConnected: (state: SimulationStoreState) => 
    state.connectionState === ConnectionState.CONNECTED,
  
  // 数据选择器
  getRealtimeData: (state: SimulationStoreState) => state.realtimeData,
  getHistoricalData: (state: SimulationStoreState) => state.historicalData,
  getComponentData: (componentId: string) => (state: SimulationStoreState) => 
    state.realtimeData?.components.get(componentId),
  
  // 错误选择器
  getErrors: (state: SimulationStoreState) => state.errors,
  getUnresolvedErrors: (state: SimulationStoreState) => 
    state.errors.filter(error => !error.resolved),
  getCriticalErrors: (state: SimulationStoreState) => 
    state.errors.filter(error => error.severity === 'critical' && !error.resolved),
  
  // 性能选择器
  getPerformance: (state: SimulationStoreState) => state.performance,
  
  // 配置选择器
  getSimulationConfig: (state: SimulationStoreState) => state.simulationConfig,
  
  // 复合选择器
  getCanStart: (state: SimulationStoreState) => 
    state.currentSession && 
    state.currentState === SimulationState.IDLE && 
    !state.isLoading,
  
  getCanPause: (state: SimulationStoreState) => 
    state.currentSession && 
    state.currentState === SimulationState.RUNNING && 
    !state.isLoading,
  
  getCanResume: (state: SimulationStoreState) => 
    state.currentSession && 
    state.currentState === SimulationState.PAUSED && 
    !state.isLoading,
  
  getCanStop: (state: SimulationStoreState) => 
    state.currentSession && 
    [SimulationState.RUNNING, SimulationState.PAUSED].includes(state.currentState) && 
    !state.isLoading
};

// 导出类型
export type SimulationStore = typeof useSimulationStore;