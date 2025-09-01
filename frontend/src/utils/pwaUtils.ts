// PWA工具类
// 用于管理Service Worker注册、PWA安装提示、离线状态检测等功能

interface BeforeInstallPromptEvent extends Event {
  readonly platforms: string[];
  readonly userChoice: Promise<{
    outcome: 'accepted' | 'dismissed';
    platform: string;
  }>;
  prompt(): Promise<void>;
}

interface PWAInstallPrompt {
  event: BeforeInstallPromptEvent | null;
  isInstallable: boolean;
  isInstalled: boolean;
  showInstallPrompt: () => Promise<boolean>;
  dismissInstallPrompt: () => void;
}

interface NetworkStatus {
  isOnline: boolean;
  connectionType: string;
  effectiveType: string;
  downlink: number;
  rtt: number;
}

interface ServiceWorkerStatus {
  isSupported: boolean;
  isRegistered: boolean;
  isControlling: boolean;
  registration: ServiceWorkerRegistration | null;
  version: string | null;
}

class PWAManager {
  private installPromptEvent: BeforeInstallPromptEvent | null = null;
  private serviceWorkerRegistration: ServiceWorkerRegistration | null = null;
  private networkStatusCallbacks: ((status: NetworkStatus) => void)[] = [];
  private installPromptCallbacks: ((prompt: PWAInstallPrompt) => void)[] = [];
  private serviceWorkerCallbacks: ((status: ServiceWorkerStatus) => void)[] = [];

  constructor() {
    this.init();
  }

  // 初始化PWA管理器
  private init() {
    // 监听PWA安装提示事件
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      this.installPromptEvent = e as BeforeInstallPromptEvent;
      this.notifyInstallPromptCallbacks();
    });

    // 监听PWA安装完成事件
    window.addEventListener('appinstalled', () => {
      console.log('PWA安装完成');
      this.installPromptEvent = null;
      this.notifyInstallPromptCallbacks();
    });

    // 监听网络状态变化
    window.addEventListener('online', () => {
      this.notifyNetworkStatusCallbacks();
    });

    window.addEventListener('offline', () => {
      this.notifyNetworkStatusCallbacks();
    });

    // 监听连接变化（如果支持）
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      connection.addEventListener('change', () => {
        this.notifyNetworkStatusCallbacks();
      });
    }

    // 注册Service Worker
    this.registerServiceWorker();
  }

  // 注册Service Worker
  async registerServiceWorker(): Promise<boolean> {
    if (!('serviceWorker' in navigator)) {
      console.warn('Service Worker不受支持');
      return false;
    }

    try {
      const registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/'
      });

      this.serviceWorkerRegistration = registration;

      console.log('Service Worker注册成功:', registration.scope);

      // 监听Service Worker状态变化
      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;
        if (newWorker) {
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              // 有新版本可用
              this.notifyServiceWorkerUpdate();
            }
          });
        }
      });

      // 监听Service Worker消息
      navigator.serviceWorker.addEventListener('message', (event) => {
        this.handleServiceWorkerMessage(event);
      });

      this.notifyServiceWorkerCallbacks();
      return true;
    } catch (error) {
      console.error('Service Worker注册失败:', error);
      return false;
    }
  }

  // 获取Service Worker版本
  async getServiceWorkerVersion(): Promise<string | null> {
    if (!this.serviceWorkerRegistration) {
      return null;
    }

    return new Promise((resolve) => {
      const messageChannel = new MessageChannel();
      messageChannel.port1.onmessage = (event) => {
        resolve(event.data.version || null);
      };

      if (navigator.serviceWorker.controller) {
        navigator.serviceWorker.controller.postMessage(
          { type: 'GET_VERSION' },
          [messageChannel.port2]
        );
      } else {
        resolve(null);
      }
    });
  }

  // 更新Service Worker
  async updateServiceWorker(): Promise<boolean> {
    if (!this.serviceWorkerRegistration) {
      return false;
    }

    try {
      await this.serviceWorkerRegistration.update();
      return true;
    } catch (error) {
      console.error('Service Worker更新失败:', error);
      return false;
    }
  }

  // 跳过等待，立即激活新的Service Worker
  async skipWaiting(): Promise<void> {
    if (navigator.serviceWorker.controller) {
      navigator.serviceWorker.controller.postMessage({ type: 'SKIP_WAITING' });
    }
  }

  // 清理所有缓存
  async clearAllCaches(): Promise<boolean> {
    if (!navigator.serviceWorker.controller) {
      return false;
    }

    return new Promise((resolve) => {
      const messageChannel = new MessageChannel();
      messageChannel.port1.onmessage = (event) => {
        resolve(event.data.success || false);
      };

      navigator.serviceWorker.controller.postMessage(
        { type: 'CLEAR_CACHE' },
        [messageChannel.port2]
      );
    });
  }

  // 预缓存指定URLs
  async cacheUrls(urls: string[]): Promise<boolean> {
    if (!navigator.serviceWorker.controller) {
      return false;
    }

    return new Promise((resolve) => {
      const messageChannel = new MessageChannel();
      messageChannel.port1.onmessage = (event) => {
        resolve(event.data.success || false);
      };

      navigator.serviceWorker.controller.postMessage(
        { type: 'CACHE_URLS', payload: { urls } },
        [messageChannel.port2]
      );
    });
  }

  // 显示PWA安装提示
  async showInstallPrompt(): Promise<boolean> {
    if (!this.installPromptEvent) {
      return false;
    }

    try {
      await this.installPromptEvent.prompt();
      const choiceResult = await this.installPromptEvent.userChoice;
      
      if (choiceResult.outcome === 'accepted') {
        console.log('用户接受了PWA安装');
        return true;
      } else {
        console.log('用户拒绝了PWA安装');
        return false;
      }
    } catch (error) {
      console.error('显示PWA安装提示失败:', error);
      return false;
    } finally {
      this.installPromptEvent = null;
    }
  }

  // 检查是否可以安装PWA
  isInstallable(): boolean {
    return this.installPromptEvent !== null;
  }

  // 检查PWA是否已安装
  isInstalled(): boolean {
    // 检查是否在独立模式下运行
    return window.matchMedia('(display-mode: standalone)').matches ||
           (window.navigator as any).standalone === true;
  }

  // 获取网络状态
  getNetworkStatus(): NetworkStatus {
    const connection = (navigator as any).connection;
    
    return {
      isOnline: navigator.onLine,
      connectionType: connection?.type || 'unknown',
      effectiveType: connection?.effectiveType || 'unknown',
      downlink: connection?.downlink || 0,
      rtt: connection?.rtt || 0
    };
  }

  // 获取Service Worker状态
  getServiceWorkerStatus(): ServiceWorkerStatus {
    return {
      isSupported: 'serviceWorker' in navigator,
      isRegistered: this.serviceWorkerRegistration !== null,
      isControlling: navigator.serviceWorker.controller !== null,
      registration: this.serviceWorkerRegistration,
      version: null // 需要异步获取
    };
  }

  // 获取PWA安装提示状态
  getInstallPromptStatus(): PWAInstallPrompt {
    return {
      event: this.installPromptEvent,
      isInstallable: this.isInstallable(),
      isInstalled: this.isInstalled(),
      showInstallPrompt: () => this.showInstallPrompt(),
      dismissInstallPrompt: () => {
        this.installPromptEvent = null;
        this.notifyInstallPromptCallbacks();
      }
    };
  }

  // 订阅网络状态变化
  onNetworkStatusChange(callback: (status: NetworkStatus) => void): () => void {
    this.networkStatusCallbacks.push(callback);
    
    // 立即调用一次
    callback(this.getNetworkStatus());
    
    // 返回取消订阅函数
    return () => {
      const index = this.networkStatusCallbacks.indexOf(callback);
      if (index > -1) {
        this.networkStatusCallbacks.splice(index, 1);
      }
    };
  }

  // 订阅PWA安装提示变化
  onInstallPromptChange(callback: (prompt: PWAInstallPrompt) => void): () => void {
    this.installPromptCallbacks.push(callback);
    
    // 立即调用一次
    callback(this.getInstallPromptStatus());
    
    // 返回取消订阅函数
    return () => {
      const index = this.installPromptCallbacks.indexOf(callback);
      if (index > -1) {
        this.installPromptCallbacks.splice(index, 1);
      }
    };
  }

  // 订阅Service Worker状态变化
  onServiceWorkerStatusChange(callback: (status: ServiceWorkerStatus) => void): () => void {
    this.serviceWorkerCallbacks.push(callback);
    
    // 立即调用一次
    callback(this.getServiceWorkerStatus());
    
    // 返回取消订阅函数
    return () => {
      const index = this.serviceWorkerCallbacks.indexOf(callback);
      if (index > -1) {
        this.serviceWorkerCallbacks.splice(index, 1);
      }
    };
  }

  // 通知网络状态回调
  private notifyNetworkStatusCallbacks() {
    const status = this.getNetworkStatus();
    this.networkStatusCallbacks.forEach(callback => {
      try {
        callback(status);
      } catch (error) {
        console.error('网络状态回调执行失败:', error);
      }
    });
  }

  // 通知安装提示回调
  private notifyInstallPromptCallbacks() {
    const prompt = this.getInstallPromptStatus();
    this.installPromptCallbacks.forEach(callback => {
      try {
        callback(prompt);
      } catch (error) {
        console.error('安装提示回调执行失败:', error);
      }
    });
  }

  // 通知Service Worker状态回调
  private notifyServiceWorkerCallbacks() {
    const status = this.getServiceWorkerStatus();
    this.serviceWorkerCallbacks.forEach(callback => {
      try {
        callback(status);
      } catch (error) {
        console.error('Service Worker状态回调执行失败:', error);
      }
    });
  }

  // 通知Service Worker更新
  private notifyServiceWorkerUpdate() {
    // 可以在这里显示更新提示
    console.log('Service Worker有新版本可用');
    
    // 触发自定义事件
    window.dispatchEvent(new CustomEvent('sw-update-available'));
  }

  // 处理Service Worker消息
  private handleServiceWorkerMessage(event: MessageEvent) {
    const { type, payload } = event.data;
    
    switch (type) {
      case 'CACHE_UPDATED':
        console.log('缓存已更新:', payload);
        break;
        
      case 'OFFLINE_READY':
        console.log('离线功能已准备就绪');
        break;
        
      case 'UPDATE_AVAILABLE':
        this.notifyServiceWorkerUpdate();
        break;
        
      default:
        console.log('收到Service Worker消息:', event.data);
    }
  }

  // 请求通知权限
  async requestNotificationPermission(): Promise<NotificationPermission> {
    if (!('Notification' in window)) {
      console.warn('此浏览器不支持通知');
      return 'denied';
    }

    if (Notification.permission === 'granted') {
      return 'granted';
    }

    if (Notification.permission === 'denied') {
      return 'denied';
    }

    const permission = await Notification.requestPermission();
    return permission;
  }

  // 显示通知
  async showNotification(title: string, options?: NotificationOptions): Promise<boolean> {
    const permission = await this.requestNotificationPermission();
    
    if (permission !== 'granted') {
      return false;
    }

    if (this.serviceWorkerRegistration) {
      // 通过Service Worker显示通知
      await this.serviceWorkerRegistration.showNotification(title, {
        icon: '/icons/icon-192x192.png',
        badge: '/icons/badge-72x72.png',
        ...options
      });
    } else {
      // 直接显示通知
      new Notification(title, {
        icon: '/icons/icon-192x192.png',
        ...options
      });
    }

    return true;
  }

  // 获取设备信息
  getDeviceInfo() {
    const userAgent = navigator.userAgent;
    const platform = navigator.platform;
    const language = navigator.language;
    const cookieEnabled = navigator.cookieEnabled;
    const onLine = navigator.onLine;
    
    // 检测设备类型
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(userAgent);
    const isTablet = /iPad|Android(?!.*Mobile)/i.test(userAgent);
    const isDesktop = !isMobile && !isTablet;
    
    // 检测操作系统
    let os = 'Unknown';
    if (userAgent.includes('Windows')) os = 'Windows';
    else if (userAgent.includes('Mac')) os = 'macOS';
    else if (userAgent.includes('Linux')) os = 'Linux';
    else if (userAgent.includes('Android')) os = 'Android';
    else if (userAgent.includes('iOS')) os = 'iOS';
    
    // 检测浏览器
    let browser = 'Unknown';
    if (userAgent.includes('Chrome')) browser = 'Chrome';
    else if (userAgent.includes('Firefox')) browser = 'Firefox';
    else if (userAgent.includes('Safari')) browser = 'Safari';
    else if (userAgent.includes('Edge')) browser = 'Edge';
    
    return {
      userAgent,
      platform,
      language,
      cookieEnabled,
      onLine,
      isMobile,
      isTablet,
      isDesktop,
      os,
      browser,
      screenWidth: screen.width,
      screenHeight: screen.height,
      viewportWidth: window.innerWidth,
      viewportHeight: window.innerHeight
    };
  }
}

// 创建全局PWA管理器实例
export const pwaManager = new PWAManager();

// 导出类型
export type {
  PWAInstallPrompt,
  NetworkStatus,
  ServiceWorkerStatus,
  BeforeInstallPromptEvent
};

// 导出工具函数
export const {
  registerServiceWorker,
  updateServiceWorker,
  skipWaiting,
  clearAllCaches,
  cacheUrls,
  showInstallPrompt,
  isInstallable,
  isInstalled,
  getNetworkStatus,
  getServiceWorkerStatus,
  getInstallPromptStatus,
  onNetworkStatusChange,
  onInstallPromptChange,
  onServiceWorkerStatusChange,
  requestNotificationPermission,
  showNotification,
  getDeviceInfo
} = pwaManager;

export default pwaManager;