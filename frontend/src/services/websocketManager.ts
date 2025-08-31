import { EventEmitter } from 'events';

// WebSocket消息类型
export interface WebSocketMessage {
  type: 'data' | 'status' | 'error' | 'heartbeat' | 'simulation_state';
  payload: any;
  timestamp?: number;
}

// 仿真数据类型
export interface SimulationData {
  timestamp: number;
  id: string;
  water_level?: number;
  flow_rate?: number;
  pressure?: number;
  temperature?: number;
  volume?: number;
  [key: string]: any;
}

// 连接状态
export enum ConnectionState {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  RECONNECTING = 'reconnecting',
  ERROR = 'error'
}

// WebSocket配置
export interface WebSocketConfig {
  url: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
  timeout?: number;
}

// WebSocket管理器类
export class WebSocketManager extends EventEmitter {
  private ws: WebSocket | null = null;
  private config: WebSocketConfig;
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private connectionState: ConnectionState = ConnectionState.DISCONNECTED;
  private lastHeartbeat = 0;
  private messageQueue: WebSocketMessage[] = [];
  private isDestroyed = false;

  constructor(config: WebSocketConfig) {
    super();
    this.config = {
      reconnectInterval: 3000,
      maxReconnectAttempts: 10,
      heartbeatInterval: 30000,
      timeout: 10000,
      ...config
    };
  }

  // 连接WebSocket
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.isDestroyed) {
        reject(new Error('WebSocket manager has been destroyed'));
        return;
      }

      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      this.setConnectionState(ConnectionState.CONNECTING);
      
      try {
        this.ws = new WebSocket(this.config.url);
        
        const timeout = setTimeout(() => {
          if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
            this.ws.close();
            reject(new Error('Connection timeout'));
          }
        }, this.config.timeout);

        this.ws.onopen = () => {
          clearTimeout(timeout);
          this.setConnectionState(ConnectionState.CONNECTED);
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          this.flushMessageQueue();
          this.emit('connected');
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event);
        };

        this.ws.onerror = (error) => {
          clearTimeout(timeout);
          this.setConnectionState(ConnectionState.ERROR);
          this.emit('error', error);
          reject(error);
        };

        this.ws.onclose = (event) => {
          clearTimeout(timeout);
          this.handleClose(event);
        };

      } catch (error) {
        this.setConnectionState(ConnectionState.ERROR);
        reject(error);
      }
    });
  }

  // 断开连接
  disconnect(): void {
    this.stopReconnect();
    this.stopHeartbeat();
    
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
    
    this.setConnectionState(ConnectionState.DISCONNECTED);
    this.emit('disconnected');
  }

  // 销毁管理器
  destroy(): void {
    this.isDestroyed = true;
    this.disconnect();
    this.removeAllListeners();
    this.messageQueue = [];
  }

  // 发送消息
  send(message: WebSocketMessage): boolean {
    if (this.isDestroyed) {
      return false;
    }

    // 添加时间戳
    message.timestamp = Date.now();

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(message));
        this.emit('messageSent', message);
        return true;
      } catch (error) {
        console.error('Failed to send WebSocket message:', error);
        this.emit('error', error);
        return false;
      }
    } else {
      // 连接未就绪，加入队列
      this.messageQueue.push(message);
      return false;
    }
  }

  // 发送心跳
  sendHeartbeat(): void {
    this.send({
      type: 'heartbeat',
      payload: { timestamp: Date.now() }
    });
  }

  // 获取连接状态
  getConnectionState(): ConnectionState {
    return this.connectionState;
  }

  // 获取WebSocket就绪状态
  getReadyState(): number | null {
    return this.ws ? this.ws.readyState : null;
  }

  // 是否已连接
  isConnected(): boolean {
    return this.connectionState === ConnectionState.CONNECTED && 
           this.ws?.readyState === WebSocket.OPEN;
  }

  // 获取重连次数
  getReconnectAttempts(): number {
    return this.reconnectAttempts;
  }

  // 处理消息
  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      
      // 处理心跳响应
      if (message.type === 'heartbeat') {
        this.lastHeartbeat = Date.now();
        this.emit('heartbeat', message.payload);
        return;
      }

      // 处理仿真数据
      if (message.type === 'data') {
        this.emit('simulationData', message.payload as SimulationData);
      }

      // 处理状态消息
      if (message.type === 'status') {
        this.emit('statusMessage', message.payload);
      }

      // 处理错误消息
      if (message.type === 'error') {
        this.emit('errorMessage', message.payload);
      }

      // 处理仿真状态
      if (message.type === 'simulation_state') {
        this.emit('simulationState', message.payload);
      }

      // 发出通用消息事件
      this.emit('message', message);

    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
      this.emit('error', error);
    }
  }

  // 处理连接关闭
  private handleClose(event: CloseEvent): void {
    this.stopHeartbeat();
    
    if (event.code === 1000) {
      // 正常关闭
      this.setConnectionState(ConnectionState.DISCONNECTED);
      this.emit('disconnected', event);
    } else {
      // 异常关闭，尝试重连
      this.setConnectionState(ConnectionState.ERROR);
      this.emit('connectionLost', event);
      this.attemptReconnect();
    }
  }

  // 尝试重连
  private attemptReconnect(): void {
    if (this.isDestroyed || this.reconnectAttempts >= this.config.maxReconnectAttempts!) {
      this.setConnectionState(ConnectionState.ERROR);
      this.emit('reconnectFailed');
      return;
    }

    this.reconnectAttempts++;
    this.setConnectionState(ConnectionState.RECONNECTING);
    this.emit('reconnecting', this.reconnectAttempts);

    this.reconnectTimer = setTimeout(() => {
      this.connect().catch((error) => {
        console.error(`Reconnect attempt ${this.reconnectAttempts} failed:`, error);
        this.attemptReconnect();
      });
    }, this.config.reconnectInterval);
  }

  // 停止重连
  private stopReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  // 开始心跳
  private startHeartbeat(): void {
    this.stopHeartbeat();
    
    if (this.config.heartbeatInterval! > 0) {
      this.heartbeatTimer = setInterval(() => {
        if (this.isConnected()) {
          this.sendHeartbeat();
        }
      }, this.config.heartbeatInterval);
    }
  }

  // 停止心跳
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  // 设置连接状态
  private setConnectionState(state: ConnectionState): void {
    if (this.connectionState !== state) {
      const previousState = this.connectionState;
      this.connectionState = state;
      this.emit('stateChange', { from: previousState, to: state });
    }
  }

  // 刷新消息队列
  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0 && this.isConnected()) {
      const message = this.messageQueue.shift();
      if (message) {
        this.send(message);
      }
    }
  }
}

// WebSocket管理器工厂
export class WebSocketManagerFactory {
  private static managers: Map<string, WebSocketManager> = new Map();

  // 创建或获取管理器
  static getManager(sessionId: string, baseUrl: string = 'ws://localhost:8000'): WebSocketManager {
    if (!this.managers.has(sessionId)) {
      const config: WebSocketConfig = {
        url: `${baseUrl}/ws/simulations/${sessionId}`,
        reconnectInterval: 3000,
        maxReconnectAttempts: 10,
        heartbeatInterval: 30000,
        timeout: 10000
      };
      
      const manager = new WebSocketManager(config);
      this.managers.set(sessionId, manager);
      
      // 监听管理器销毁事件
      manager.on('destroyed', () => {
        this.managers.delete(sessionId);
      });
    }
    
    return this.managers.get(sessionId)!;
  }

  // 销毁管理器
  static destroyManager(sessionId: string): void {
    const manager = this.managers.get(sessionId);
    if (manager) {
      manager.destroy();
      this.managers.delete(sessionId);
    }
  }

  // 销毁所有管理器
  static destroyAllManagers(): void {
    this.managers.forEach((manager) => {
      manager.destroy();
    });
    this.managers.clear();
  }

  // 获取所有活跃的会话ID
  static getActiveSessions(): string[] {
    return Array.from(this.managers.keys());
  }

  // 获取管理器统计信息
  static getManagerStats(sessionId: string): any {
    const manager = this.managers.get(sessionId);
    if (!manager) {
      return null;
    }

    return {
      sessionId,
      connectionState: manager.getConnectionState(),
      readyState: manager.getReadyState(),
      reconnectAttempts: manager.getReconnectAttempts(),
      isConnected: manager.isConnected()
    };
  }
}

// 导出默认实例
export default WebSocketManagerFactory;