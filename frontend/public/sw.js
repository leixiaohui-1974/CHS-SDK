// CHS仿真平台 Service Worker
// 版本号
const CACHE_VERSION = 'chs-v1.0.0';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const DYNAMIC_CACHE = `${CACHE_VERSION}-dynamic`;
const API_CACHE = `${CACHE_VERSION}-api`;

// 需要缓存的静态资源
const STATIC_ASSETS = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png',
  // 添加其他重要的静态资源
];

// 需要缓存的API路径模式
const API_PATTERNS = [
  /\/api\/simulation\/templates/,
  /\/api\/user\/profile/,
  /\/api\/system\/config/,
];

// 离线页面
const OFFLINE_PAGE = '/offline.html';

// 安装事件 - 缓存静态资源
self.addEventListener('install', (event) => {
  console.log('[SW] Installing Service Worker');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('[SW] Static assets cached successfully');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('[SW] Failed to cache static assets:', error);
      })
  );
});

// 激活事件 - 清理旧缓存
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating Service Worker');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((cacheName) => {
              // 删除不是当前版本的缓存
              return cacheName.startsWith('chs-') && !cacheName.startsWith(CACHE_VERSION);
            })
            .map((cacheName) => {
              console.log('[SW] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            })
        );
      })
      .then(() => {
        console.log('[SW] Service Worker activated');
        return self.clients.claim();
      })
  );
});

// 获取事件 - 处理网络请求
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // 只处理同源请求
  if (url.origin !== location.origin) {
    return;
  }
  
  // 处理导航请求（页面请求）
  if (request.mode === 'navigate') {
    event.respondWith(handleNavigationRequest(request));
    return;
  }
  
  // 处理API请求
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(handleApiRequest(request));
    return;
  }
  
  // 处理静态资源请求
  event.respondWith(handleStaticRequest(request));
});

// 处理导航请求
async function handleNavigationRequest(request) {
  try {
    // 尝试从网络获取
    const networkResponse = await fetch(request);
    
    // 如果网络请求成功，缓存响应并返回
    if (networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, networkResponse.clone());
      return networkResponse;
    }
    
    throw new Error('Network response not ok');
  } catch (error) {
    console.log('[SW] Network failed for navigation, trying cache:', error);
    
    // 网络失败，尝试从缓存获取
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // 缓存中也没有，返回离线页面
    const offlineResponse = await caches.match(OFFLINE_PAGE);
    if (offlineResponse) {
      return offlineResponse;
    }
    
    // 如果连离线页面都没有，返回基本的离线响应
    return new Response(
      `
      <!DOCTYPE html>
      <html>
        <head>
          <title>CHS仿真平台 - 离线</title>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <style>
            body {
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              height: 100vh;
              margin: 0;
              background: #f5f5f5;
              color: #333;
            }
            .offline-container {
              text-align: center;
              padding: 2rem;
              background: white;
              border-radius: 8px;
              box-shadow: 0 2px 10px rgba(0,0,0,0.1);
              max-width: 400px;
            }
            .offline-icon {
              font-size: 4rem;
              margin-bottom: 1rem;
            }
            .offline-title {
              font-size: 1.5rem;
              margin-bottom: 1rem;
              color: #1976d2;
            }
            .offline-message {
              margin-bottom: 1.5rem;
              line-height: 1.5;
            }
            .retry-button {
              background: #1976d2;
              color: white;
              border: none;
              padding: 0.75rem 1.5rem;
              border-radius: 4px;
              cursor: pointer;
              font-size: 1rem;
            }
            .retry-button:hover {
              background: #1565c0;
            }
          </style>
        </head>
        <body>
          <div class="offline-container">
            <div class="offline-icon">📡</div>
            <h1 class="offline-title">网络连接中断</h1>
            <p class="offline-message">
              无法连接到CHS仿真平台服务器。<br>
              请检查您的网络连接并重试。
            </p>
            <button class="retry-button" onclick="window.location.reload()">
              重新连接
            </button>
          </div>
        </body>
      </html>
      `,
      {
        status: 200,
        headers: { 'Content-Type': 'text/html; charset=utf-8' }
      }
    );
  }
}

// 处理API请求
async function handleApiRequest(request) {
  const url = new URL(request.url);
  
  try {
    // 尝试从网络获取
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      // 只缓存GET请求的成功响应
      if (request.method === 'GET' && shouldCacheApiRequest(url.pathname)) {
        const cache = await caches.open(API_CACHE);
        cache.put(request, networkResponse.clone());
      }
      return networkResponse;
    }
    
    throw new Error('Network response not ok');
  } catch (error) {
    console.log('[SW] Network failed for API request, trying cache:', error);
    
    // 网络失败，尝试从缓存获取（仅GET请求）
    if (request.method === 'GET') {
      const cachedResponse = await caches.match(request);
      if (cachedResponse) {
        // 添加离线标识头
        const headers = new Headers(cachedResponse.headers);
        headers.set('X-Served-From', 'cache');
        headers.set('X-Cache-Date', cachedResponse.headers.get('date') || 'unknown');
        
        return new Response(cachedResponse.body, {
          status: cachedResponse.status,
          statusText: cachedResponse.statusText,
          headers: headers
        });
      }
    }
    
    // 返回离线错误响应
    return new Response(
      JSON.stringify({
        error: 'offline',
        message: '网络连接中断，无法获取数据',
        timestamp: new Date().toISOString()
      }),
      {
        status: 503,
        headers: {
          'Content-Type': 'application/json',
          'X-Served-From': 'service-worker'
        }
      }
    );
  }
}

// 处理静态资源请求
async function handleStaticRequest(request) {
  try {
    // 先尝试从缓存获取
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // 缓存中没有，从网络获取
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      // 缓存成功的响应
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.log('[SW] Failed to fetch static resource:', error);
    
    // 网络和缓存都失败，返回404
    return new Response('Resource not found', {
      status: 404,
      statusText: 'Not Found'
    });
  }
}

// 判断是否应该缓存API请求
function shouldCacheApiRequest(pathname) {
  return API_PATTERNS.some(pattern => pattern.test(pathname));
}

// 消息事件 - 处理来自主线程的消息
self.addEventListener('message', (event) => {
  const { type, payload } = event.data;
  
  switch (type) {
    case 'SKIP_WAITING':
      self.skipWaiting();
      break;
      
    case 'GET_VERSION':
      event.ports[0].postMessage({ version: CACHE_VERSION });
      break;
      
    case 'CLEAR_CACHE':
      clearAllCaches().then(() => {
        event.ports[0].postMessage({ success: true });
      }).catch((error) => {
        event.ports[0].postMessage({ success: false, error: error.message });
      });
      break;
      
    case 'CACHE_URLS':
      if (payload && payload.urls) {
        cacheUrls(payload.urls).then(() => {
          event.ports[0].postMessage({ success: true });
        }).catch((error) => {
          event.ports[0].postMessage({ success: false, error: error.message });
        });
      }
      break;
      
    default:
      console.log('[SW] Unknown message type:', type);
  }
});

// 清理所有缓存
async function clearAllCaches() {
  const cacheNames = await caches.keys();
  await Promise.all(
    cacheNames
      .filter(name => name.startsWith('chs-'))
      .map(name => caches.delete(name))
  );
}

// 缓存指定的URLs
async function cacheUrls(urls) {
  const cache = await caches.open(DYNAMIC_CACHE);
  await cache.addAll(urls);
}

// 后台同步事件
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync:', event.tag);
  
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

// 执行后台同步
async function doBackgroundSync() {
  try {
    // 这里可以执行一些后台同步任务
    // 比如上传离线时产生的数据
    console.log('[SW] Performing background sync');
    
    // 示例：同步离线数据
    const offlineData = await getOfflineData();
    if (offlineData.length > 0) {
      await syncOfflineData(offlineData);
    }
  } catch (error) {
    console.error('[SW] Background sync failed:', error);
  }
}

// 获取离线数据（示例）
async function getOfflineData() {
  // 这里应该从IndexedDB或其他存储中获取离线数据
  return [];
}

// 同步离线数据（示例）
async function syncOfflineData(data) {
  // 这里应该将离线数据发送到服务器
  console.log('[SW] Syncing offline data:', data);
}

// 推送事件
self.addEventListener('push', (event) => {
  console.log('[SW] Push received:', event);
  
  let notificationData = {
    title: 'CHS仿真平台',
    body: '您有新的通知',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
    tag: 'chs-notification',
    requireInteraction: false,
    actions: [
      {
        action: 'open',
        title: '查看',
        icon: '/icons/action-open.png'
      },
      {
        action: 'dismiss',
        title: '忽略',
        icon: '/icons/action-dismiss.png'
      }
    ]
  };
  
  if (event.data) {
    try {
      const payload = event.data.json();
      notificationData = { ...notificationData, ...payload };
    } catch (error) {
      console.error('[SW] Failed to parse push payload:', error);
    }
  }
  
  event.waitUntil(
    self.registration.showNotification(notificationData.title, notificationData)
  );
});

// 通知点击事件
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification clicked:', event);
  
  event.notification.close();
  
  if (event.action === 'open') {
    event.waitUntil(
      clients.openWindow('/')
    );
  } else if (event.action === 'dismiss') {
    // 忽略通知，不做任何操作
  } else {
    // 默认行为：打开应用
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// 错误处理
self.addEventListener('error', (event) => {
  console.error('[SW] Service Worker error:', event.error);
});

self.addEventListener('unhandledrejection', (event) => {
  console.error('[SW] Unhandled promise rejection:', event.reason);
});

console.log('[SW] Service Worker script loaded');