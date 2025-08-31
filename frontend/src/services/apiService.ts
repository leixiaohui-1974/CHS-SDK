import axios, { AxiosInstance, AxiosResponse } from 'axios';

// API配置
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

// 请求和响应类型定义
export interface ComponentModel {
  name: string;
  type: string;
  parameters: Record<string, any>;
  position?: { x: number; y: number };
}

export interface ConnectionModel {
  upstream: string;
  downstream: string;
}

export interface AgentModel {
  id: string;
  class_name: string;
  params: Record<string, any>;
}

export interface SimulationRequest {
  components: {
    reservoirs: ComponentModel[];
    gates: ComponentModel[];
    pipes: ComponentModel[];
    unified_canals: ComponentModel[];
  };
  topology: {
    connections: ConnectionModel[];
  };
  agents: {
    agents: AgentModel[];
  };
}

export interface SimulationSession {
  session_id: string;
}

export interface SimulationData {
  timestamp: number;
  id: string;
  water_level?: number;
  flow_rate?: number;
  pressure?: number;
  [key: string]: any;
}

export interface WebSocketMessage {
  type: 'data' | 'status' | 'error';
  payload: any;
}

export interface ExampleConfig {
  components: any;
  topology: any;
  agents?: any;
}

// API服务类
class ApiService {
  private api: AxiosInstance;
  private wsConnections: Map<string, WebSocket> = new Map();

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 请求拦截器
    this.api.interceptors.request.use(
      (config) => {
        console.log('API Request:', config.method?.toUpperCase(), config.url);
        return config;
      },
      (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
      }
    );

    // 响应拦截器
    this.api.interceptors.response.use(
      (response: AxiosResponse) => {
        console.log('API Response:', response.status, response.config.url);
        return response;
      },
      (error) => {
        console.error('API Response Error:', error.response?.status, error.response?.data);
        return Promise.reject(error);
      }
    );
  }

  // 健康检查
  async getStatus(): Promise<{ status: string; message: string }> {
    const response = await this.api.get('/api/status');
    return response.data;
  }

  // 获取示例列表
  async getExamples(): Promise<string[]> {
    const response = await this.api.get('/api/examples');
    return response.data;
  }

  // 获取示例配置
  async getExampleConfig(examplePath: string): Promise<ExampleConfig> {
    const response = await this.api.get(`/api/examples/${examplePath}`);
    return response.data;
  }

  // 创建仿真会话
  async createSimulationSession(request: SimulationRequest): Promise<SimulationSession> {
    const response = await this.api.post('/api/simulations', request);
    return response.data;
  }

  // 启动仿真
  async startSimulation(sessionId: string): Promise<{ message: string }> {
    const response = await this.api.post(`/api/simulations/${sessionId}/start`);
    return response.data;
  }

  // 停止仿真
  async stopSimulation(sessionId: string): Promise<{ message: string }> {
    const response = await this.api.post(`/api/simulations/${sessionId}/stop`);
    return response.data;
  }

  // 暂停仿真
  async pauseSimulation(sessionId: string): Promise<void> {
    await this.api.post(`/api/simulations/${sessionId}/pause`);
  }

  // 恢复仿真
  async resumeSimulation(sessionId: string): Promise<void> {
    await this.api.post(`/api/simulations/${sessionId}/resume`);
  }

  // WebSocket连接管理
  connectWebSocket(
    sessionId: string,
    onMessage: (data: WebSocketMessage) => void,
    onError?: (error: Event) => void,
    onClose?: (event: CloseEvent) => void
  ): WebSocket {
    // 如果已存在连接，先关闭
    if (this.wsConnections.has(sessionId)) {
      this.disconnectWebSocket(sessionId);
    }

    const wsUrl = `${WS_BASE_URL}/ws/simulations/${sessionId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log(`WebSocket connected for session: ${sessionId}`);
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        onMessage(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error(`WebSocket error for session ${sessionId}:`, error);
      if (onError) {
        onError(error);
      }
    };

    ws.onclose = (event) => {
      console.log(`WebSocket closed for session ${sessionId}:`, event.code, event.reason);
      this.wsConnections.delete(sessionId);
      if (onClose) {
        onClose(event);
      }
    };

    this.wsConnections.set(sessionId, ws);
    return ws;
  }

  // 断开WebSocket连接
  disconnectWebSocket(sessionId: string): void {
    const ws = this.wsConnections.get(sessionId);
    if (ws) {
      ws.close();
      this.wsConnections.delete(sessionId);
    }
  }

  // 断开所有WebSocket连接
  disconnectAllWebSockets(): void {
    this.wsConnections.forEach((ws, sessionId) => {
      ws.close();
    });
    this.wsConnections.clear();
  }

  // 获取WebSocket连接状态
  getWebSocketState(sessionId: string): number | null {
    const ws = this.wsConnections.get(sessionId);
    return ws ? ws.readyState : null;
  }

  // 发送WebSocket消息
  sendWebSocketMessage(sessionId: string, message: any): boolean {
    const ws = this.wsConnections.get(sessionId);
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message));
      return true;
    }
    return false;
  }
}

// 创建单例实例
const apiService = new ApiService();

export default apiService;

// 导出常用的API方法
export const {
  getStatus,
  getExamples,
  getExampleConfig,
  createSimulationSession,
  startSimulation,
  stopSimulation,
  pauseSimulation,
  resumeSimulation,
  connectWebSocket,
  disconnectWebSocket,
  disconnectAllWebSockets,
  getWebSocketState,
  sendWebSocketMessage,
} = apiService;

// WebSocket状态常量
export const WebSocketState = {
  CONNECTING: 0,
  OPEN: 1,
  CLOSING: 2,
  CLOSED: 3,
} as const;

// 错误处理工具函数
export const handleApiError = (error: any): string => {
  if (error.response) {
    // 服务器响应错误
    const status = error.response.status;
    const message = error.response.data?.detail || error.response.data?.message || error.message;
    
    switch (status) {
      case 400:
        return `请求参数错误: ${message}`;
      case 401:
        return '未授权访问，请检查认证信息';
      case 403:
        return '访问被禁止，权限不足';
      case 404:
        return '请求的资源不存在';
      case 422:
        return `数据验证失败: ${message}`;
      case 500:
        return '服务器内部错误，请稍后重试';
      default:
        return `请求失败 (${status}): ${message}`;
    }
  } else if (error.request) {
    // 网络错误
    return '网络连接失败，请检查网络设置';
  } else {
    // 其他错误
    return error.message || '未知错误';
  }
};

// 数据转换工具函数
export const convertNodeToComponent = (node: any): ComponentModel => {
  return {
    name: node.id,
    type: node.type,
    parameters: node.data?.parameters || {},
    position: node.position,
  };
};

export const convertEdgeToConnection = (edge: any): ConnectionModel => {
  return {
    upstream: edge.source,
    downstream: edge.target,
  };
};

// 构建仿真请求
export const buildSimulationRequest = (nodes: any[], edges: any[], agents: AgentModel[] = []): SimulationRequest => {
  const components = {
    reservoirs: nodes.filter(n => n.type === 'reservoir').map(convertNodeToComponent),
    gates: nodes.filter(n => n.type === 'gate').map(convertNodeToComponent),
    pipes: nodes.filter(n => n.type === 'pipe').map(convertNodeToComponent),
    unified_canals: nodes.filter(n => n.type === 'canal').map(convertNodeToComponent),
  };

  const topology = {
    connections: edges.map(convertEdgeToConnection),
  };

  return {
    components,
    topology,
    agents: { agents },
  };
};