# CHS仿真平台API参考文档

## 目录

1. [概述](#概述)
2. [认证](#认证)
3. [通用响应格式](#通用响应格式)
4. [错误处理](#错误处理)
5. [用户管理API](#用户管理api)
6. [仿真管理API](#仿真管理api)
7. [数据管理API](#数据管理api)
8. [文件管理API](#文件管理api)
9. [系统管理API](#系统管理api)
10. [WebSocket API](#websocket-api)
11. [SDK示例](#sdk示例)

## 概述

### 基本信息

- **API版本**: v1.0
- **基础URL**: `https://api.chs-platform.com/v1`
- **协议**: HTTPS
- **数据格式**: JSON
- **字符编码**: UTF-8

### 请求头

所有API请求都应包含以下请求头：

```http
Content-Type: application/json
Accept: application/json
Authorization: Bearer <access_token>
X-API-Version: v1
```

### 速率限制

- **认证用户**: 1000 请求/小时
- **未认证用户**: 100 请求/小时
- **管理员用户**: 5000 请求/小时

速率限制信息会在响应头中返回：

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## 认证

### JWT令牌认证

CHS平台使用JWT（JSON Web Token）进行身份认证。

#### 获取访问令牌

```http
POST /auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "your_password"
}
```

**响应示例**:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "username": "user@example.com",
    "role": "user"
  }
}
```

#### 刷新令牌

```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### 注销

```http
POST /auth/logout
Authorization: Bearer <access_token>
```

### API密钥认证

对于服务器到服务器的通信，可以使用API密钥：

```http
X-API-Key: your_api_key
```

## 通用响应格式

### 成功响应

```json
{
  "success": true,
  "data": {
    // 响应数据
  },
  "message": "操作成功",
  "timestamp": "2024-01-20T10:30:00Z",
  "request_id": "req_123456789"
}
```

### 分页响应

```json
{
  "success": true,
  "data": {
    "items": [
      // 数据项列表
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 100,
      "pages": 5,
      "has_next": true,
      "has_prev": false
    }
  },
  "message": "查询成功",
  "timestamp": "2024-01-20T10:30:00Z",
  "request_id": "req_123456789"
}
```

## 错误处理

### 错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "details": {
      "field": "email",
      "reason": "邮箱格式不正确"
    }
  },
  "timestamp": "2024-01-20T10:30:00Z",
  "request_id": "req_123456789"
}
```

### 常见错误码

| 状态码 | 错误码 | 描述 |
|--------|--------|------|
| 400 | VALIDATION_ERROR | 请求参数验证失败 |
| 401 | UNAUTHORIZED | 未授权访问 |
| 403 | FORBIDDEN | 权限不足 |
| 404 | NOT_FOUND | 资源不存在 |
| 409 | CONFLICT | 资源冲突 |
| 422 | UNPROCESSABLE_ENTITY | 无法处理的实体 |
| 429 | RATE_LIMIT_EXCEEDED | 超出速率限制 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |
| 503 | SERVICE_UNAVAILABLE | 服务不可用 |

## 用户管理API

### 用户注册

```http
POST /users/register
Content-Type: application/json

{
  "username": "newuser@example.com",
  "password": "secure_password",
  "full_name": "张三",
  "organization": "某某大学",
  "phone": "+86-13800138000"
}
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "user": {
      "id": 123,
      "username": "newuser@example.com",
      "full_name": "张三",
      "organization": "某某大学",
      "phone": "+86-13800138000",
      "role": "user",
      "is_active": true,
      "created_at": "2024-01-20T10:30:00Z",
      "updated_at": "2024-01-20T10:30:00Z"
    },
    "verification_required": true
  },
  "message": "用户注册成功，请检查邮箱进行验证"
}
```

### 获取用户信息

```http
GET /users/me
Authorization: Bearer <access_token>
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "id": 123,
    "username": "user@example.com",
    "full_name": "张三",
    "organization": "某某大学",
    "phone": "+86-13800138000",
    "role": "user",
    "is_active": true,
    "email_verified": true,
    "last_login": "2024-01-20T09:15:00Z",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-20T10:30:00Z",
    "preferences": {
      "language": "zh-CN",
      "timezone": "Asia/Shanghai",
      "theme": "light"
    },
    "quota": {
      "simulations_per_month": 100,
      "storage_limit_gb": 10,
      "concurrent_simulations": 3
    }
  }
}
```

### 更新用户信息

```http
PUT /users/me
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "full_name": "张三丰",
  "organization": "武当山",
  "phone": "+86-13900139000",
  "preferences": {
    "language": "en-US",
    "timezone": "UTC",
    "theme": "dark"
  }
}
```

### 修改密码

```http
POST /users/change-password
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "current_password": "old_password",
  "new_password": "new_secure_password"
}
```

## 仿真管理API

### 创建仿真

```http
POST /simulations
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "流体仿真测试",
  "description": "测试圆柱绕流的仿真",
  "type": "fluid_dynamics",
  "configuration": {
    "solver": "openfoam",
    "mesh_size": "medium",
    "time_step": 0.001,
    "end_time": 10.0,
    "turbulence_model": "k-epsilon",
    "boundary_conditions": {
      "inlet": {
        "type": "velocity",
        "value": [1.0, 0.0, 0.0]
      },
      "outlet": {
        "type": "pressure",
        "value": 0.0
      },
      "walls": {
        "type": "no_slip"
      }
    }
  },
  "geometry_file_id": "file_123456",
  "priority": "normal",
  "tags": ["test", "cylinder", "flow"]
}
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "id": "sim_789012",
    "name": "流体仿真测试",
    "description": "测试圆柱绕流的仿真",
    "type": "fluid_dynamics",
    "status": "created",
    "configuration": {
      // 配置信息
    },
    "geometry_file_id": "file_123456",
    "priority": "normal",
    "tags": ["test", "cylinder", "flow"],
    "created_at": "2024-01-20T10:30:00Z",
    "updated_at": "2024-01-20T10:30:00Z",
    "estimated_duration": 3600,
    "estimated_cost": 5.50
  },
  "message": "仿真创建成功"
}
```

### 启动仿真

```http
POST /simulations/{simulation_id}/start
Authorization: Bearer <access_token>
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "simulation_id": "sim_789012",
    "status": "queued",
    "queue_position": 3,
    "estimated_start_time": "2024-01-20T10:45:00Z",
    "execution_id": "exec_345678"
  },
  "message": "仿真已加入执行队列"
}
```

### 获取仿真状态

```http
GET /simulations/{simulation_id}/status
Authorization: Bearer <access_token>
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "simulation_id": "sim_789012",
    "status": "running",
    "progress": {
      "percentage": 45.5,
      "current_step": 4550,
      "total_steps": 10000,
      "elapsed_time": 1800,
      "estimated_remaining_time": 2160
    },
    "resources": {
      "cpu_cores": 8,
      "memory_gb": 16,
      "gpu_count": 1
    },
    "metrics": {
      "convergence": 0.001,
      "residuals": {
        "pressure": 1.2e-5,
        "velocity": 3.4e-6
      }
    },
    "started_at": "2024-01-20T10:45:00Z",
    "last_updated": "2024-01-20T11:15:00Z"
  }
}
```

### 停止仿真

```http
POST /simulations/{simulation_id}/stop
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "reason": "用户取消",
  "save_partial_results": true
}
```

### 获取仿真列表

```http
GET /simulations?page=1&per_page=20&status=completed&type=fluid_dynamics
Authorization: Bearer <access_token>
```

**查询参数**:

| 参数 | 类型 | 描述 | 默认值 |
|------|------|------|--------|
| page | integer | 页码 | 1 |
| per_page | integer | 每页数量 | 20 |
| status | string | 状态筛选 | all |
| type | string | 类型筛选 | all |
| sort | string | 排序字段 | created_at |
| order | string | 排序方向 | desc |
| search | string | 搜索关键词 | - |
| tags | string | 标签筛选 | - |

**响应示例**:

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "sim_789012",
        "name": "流体仿真测试",
        "type": "fluid_dynamics",
        "status": "completed",
        "progress": 100,
        "created_at": "2024-01-20T10:30:00Z",
        "completed_at": "2024-01-20T12:15:00Z",
        "duration": 6300,
        "cost": 5.25
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 45,
      "pages": 3,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

### 删除仿真

```http
DELETE /simulations/{simulation_id}
Authorization: Bearer <access_token>
```

## 数据管理API

### 获取仿真结果

```http
GET /simulations/{simulation_id}/results
Authorization: Bearer <access_token>
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "simulation_id": "sim_789012",
    "results": {
      "summary": {
        "total_iterations": 10000,
        "convergence_achieved": true,
        "final_residual": 1.2e-6,
        "computation_time": 6300
      },
      "fields": [
        {
          "name": "velocity",
          "type": "vector",
          "unit": "m/s",
          "file_id": "result_001",
          "size_mb": 125.6
        },
        {
          "name": "pressure",
          "type": "scalar",
          "unit": "Pa",
          "file_id": "result_002",
          "size_mb": 62.8
        }
      ],
      "monitoring_data": {
        "force_coefficients": {
          "file_id": "monitor_001",
          "format": "csv"
        },
        "residuals": {
          "file_id": "monitor_002",
          "format": "csv"
        }
      }
    },
    "visualization": {
      "preview_images": [
        {
          "name": "velocity_magnitude",
          "url": "/files/preview_001.png",
          "type": "contour"
        },
        {
          "name": "pressure_distribution",
          "url": "/files/preview_002.png",
          "type": "contour"
        }
      ],
      "interactive_viewer_url": "/viewer/sim_789012"
    }
  }
}
```

### 下载结果数据

```http
GET /simulations/{simulation_id}/results/download?format=vtk&fields=velocity,pressure
Authorization: Bearer <access_token>
```

**查询参数**:

| 参数 | 类型 | 描述 | 默认值 |
|------|------|------|--------|
| format | string | 文件格式 (vtk, csv, hdf5) | vtk |
| fields | string | 字段列表 (逗号分隔) | all |
| compression | string | 压缩格式 (zip, tar.gz) | zip |

### 获取监控数据

```http
GET /simulations/{simulation_id}/monitoring?metric=residuals&start_time=0&end_time=6300
Authorization: Bearer <access_token>
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "simulation_id": "sim_789012",
    "metric": "residuals",
    "time_range": {
      "start": 0,
      "end": 6300,
      "unit": "seconds"
    },
    "data_points": [
      {
        "time": 0,
        "values": {
          "pressure": 1.0e-3,
          "velocity_x": 5.2e-4,
          "velocity_y": 3.1e-4,
          "velocity_z": 2.8e-4
        }
      },
      {
        "time": 63,
        "values": {
          "pressure": 8.5e-4,
          "velocity_x": 4.1e-4,
          "velocity_y": 2.7e-4,
          "velocity_z": 2.3e-4
        }
      }
    ]
  }
}
```

## 文件管理API

### 上传文件

```http
POST /files/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file: <binary_data>
name: geometry.stl
type: geometry
description: 圆柱几何文件
tags: cylinder,3d,stl
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "file_id": "file_123456",
    "name": "geometry.stl",
    "original_name": "cylinder.stl",
    "type": "geometry",
    "size_bytes": 2048576,
    "mime_type": "application/octet-stream",
    "description": "圆柱几何文件",
    "tags": ["cylinder", "3d", "stl"],
    "checksum": "sha256:abc123...",
    "upload_url": "/files/file_123456",
    "preview_url": "/files/file_123456/preview",
    "created_at": "2024-01-20T10:30:00Z"
  },
  "message": "文件上传成功"
}
```

### 获取文件信息

```http
GET /files/{file_id}
Authorization: Bearer <access_token>
```

### 下载文件

```http
GET /files/{file_id}/download
Authorization: Bearer <access_token>
```

### 删除文件

```http
DELETE /files/{file_id}
Authorization: Bearer <access_token>
```

### 获取文件列表

```http
GET /files?page=1&per_page=20&type=geometry&search=cylinder
Authorization: Bearer <access_token>
```

## 系统管理API

### 获取系统状态

```http
GET /system/status
Authorization: Bearer <access_token>
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "system": {
      "status": "healthy",
      "version": "1.0.0",
      "uptime": 86400,
      "timestamp": "2024-01-20T10:30:00Z"
    },
    "services": {
      "api": {
        "status": "healthy",
        "response_time_ms": 45
      },
      "database": {
        "status": "healthy",
        "connections": 12,
        "max_connections": 100
      },
      "cache": {
        "status": "healthy",
        "memory_usage_mb": 256,
        "hit_rate": 0.95
      },
      "storage": {
        "status": "healthy",
        "used_space_gb": 1024,
        "total_space_gb": 10240
      }
    },
    "compute_resources": {
      "total_cores": 128,
      "available_cores": 64,
      "total_memory_gb": 512,
      "available_memory_gb": 256,
      "gpu_count": 8,
      "available_gpus": 4
    },
    "queue_status": {
      "pending_simulations": 5,
      "running_simulations": 12,
      "average_wait_time_minutes": 15
    }
  }
}
```

### 获取系统指标

```http
GET /system/metrics?start_time=2024-01-20T09:00:00Z&end_time=2024-01-20T10:00:00Z
Authorization: Bearer <access_token>
```

## WebSocket API

### 连接WebSocket

```javascript
// 连接WebSocket
const ws = new WebSocket('wss://api.chs-platform.com/v1/ws?token=<access_token>');

// 监听消息
ws.onmessage = function(event) {
  const message = JSON.parse(event.data);
  console.log('收到消息:', message);
};

// 发送消息
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'simulation_updates',
  simulation_id: 'sim_789012'
}));
```

### 消息格式

#### 订阅仿真更新

```json
{
  "type": "subscribe",
  "channel": "simulation_updates",
  "simulation_id": "sim_789012"
}
```

#### 仿真状态更新

```json
{
  "type": "simulation_update",
  "simulation_id": "sim_789012",
  "data": {
    "status": "running",
    "progress": 67.5,
    "current_step": 6750,
    "elapsed_time": 2430,
    "estimated_remaining_time": 1170
  },
  "timestamp": "2024-01-20T11:30:00Z"
}
```

#### 仿真完成通知

```json
{
  "type": "simulation_completed",
  "simulation_id": "sim_789012",
  "data": {
    "status": "completed",
    "duration": 6300,
    "results_available": true,
    "cost": 5.25
  },
  "timestamp": "2024-01-20T12:15:00Z"
}
```

## SDK示例

### Python SDK

```python
from chs_sdk import CHSClient

# 初始化客户端
client = CHSClient(
    base_url="https://api.chs-platform.com/v1",
    api_key="your_api_key"
)

# 用户认证
auth_result = client.auth.login(
    username="user@example.com",
    password="your_password"
)
print(f"登录成功: {auth_result.user.username}")

# 创建仿真
simulation = client.simulations.create(
    name="Python SDK测试",
    type="fluid_dynamics",
    configuration={
        "solver": "openfoam",
        "mesh_size": "medium",
        "time_step": 0.001,
        "end_time": 10.0
    }
)
print(f"仿真创建成功: {simulation.id}")

# 上传几何文件
with open("geometry.stl", "rb") as f:
    file_info = client.files.upload(
        file=f,
        name="geometry.stl",
        type="geometry"
    )
print(f"文件上传成功: {file_info.file_id}")

# 关联几何文件到仿真
client.simulations.update(
    simulation.id,
    geometry_file_id=file_info.file_id
)

# 启动仿真
execution = client.simulations.start(simulation.id)
print(f"仿真启动成功: {execution.execution_id}")

# 监控仿真进度
import time
while True:
    status = client.simulations.get_status(simulation.id)
    print(f"进度: {status.progress.percentage}%")
    
    if status.status in ["completed", "failed", "cancelled"]:
        break
    
    time.sleep(30)

# 下载结果
if status.status == "completed":
    results = client.simulations.get_results(simulation.id)
    
    # 下载结果文件
    with open("results.zip", "wb") as f:
        client.simulations.download_results(
            simulation.id,
            format="vtk",
            output=f
        )
    print("结果下载完成")
```

### JavaScript SDK

```javascript
import { CHSClient } from '@chs-platform/sdk';

// 初始化客户端
const client = new CHSClient({
  baseURL: 'https://api.chs-platform.com/v1',
  apiKey: 'your_api_key'
});

// 用户认证
const authResult = await client.auth.login({
  username: 'user@example.com',
  password: 'your_password'
});
console.log(`登录成功: ${authResult.user.username}`);

// 创建仿真
const simulation = await client.simulations.create({
  name: 'JavaScript SDK测试',
  type: 'fluid_dynamics',
  configuration: {
    solver: 'openfoam',
    mesh_size: 'medium',
    time_step: 0.001,
    end_time: 10.0
  }
});
console.log(`仿真创建成功: ${simulation.id}`);

// 上传文件
const fileInput = document.getElementById('file-input');
const file = fileInput.files[0];

const fileInfo = await client.files.upload({
  file: file,
  name: 'geometry.stl',
  type: 'geometry'
});
console.log(`文件上传成功: ${fileInfo.file_id}`);

// 启动仿真
const execution = await client.simulations.start(simulation.id);
console.log(`仿真启动成功: ${execution.execution_id}`);

// WebSocket监控
const ws = client.websocket.connect();
ws.subscribe('simulation_updates', simulation.id, (update) => {
  console.log(`进度更新: ${update.data.progress}%`);
  
  if (update.type === 'simulation_completed') {
    console.log('仿真完成!');
    downloadResults();
  }
});

// 下载结果
async function downloadResults() {
  const blob = await client.simulations.downloadResults(
    simulation.id,
    { format: 'vtk' }
  );
  
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'results.zip';
  a.click();
  
  URL.revokeObjectURL(url);
}
```

---

**文档版本**: v1.0.0  
**创建时间**: 2024年1月20日  
**维护团队**: CHS平台API团队  
**审核状态**: 已审核

> 本API参考文档提供了CHS仿真平台所有API接口的详细说明，包括请求格式、响应格式、错误处理和SDK使用示例。如有疑问，请联系技术支持团队。