# CHS-SDK 开发者指南

## 概述

本指南为 CHS-SDK 项目的开发者提供详细的开发环境搭建、代码规范、开发流程和最佳实践指导。CHS-SDK 是一个复杂的水利系统仿真平台，包含多智能体系统、实时监控、数据分析等功能模块。

## 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+ (前端开发)
- Docker (可选)
- Git

### 快速安装

```bash
# 克隆项目
git clone https://github.com/your-org/CHS-SDK.git
cd CHS-SDK

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-test.txt

# 启动开发服务器
uvicorn api.server:app --reload
```

## 目录

1. [开发环境搭建](#开发环境搭建)
2. [项目架构](#项目架构)
3. [API开发](#api开发)
4. [前端开发](#前端开发)
5. [数据库设计](#数据库设计)
6. [测试指南](#测试指南)
7. [部署指南](#部署指南)
8. [最佳实践](#最佳实践)
9. [故障排除](#故障排除)
10. [贡献指南](#贡献指南)

## 开发环境搭建

### 系统要求

- **操作系统**: Linux (Ubuntu 20.04+), macOS (10.15+), Windows (10+)
- **Python**: 3.9+
- **Node.js**: 16+
- **Docker**: 20.10+
- **Git**: 2.30+

### 环境配置

#### 1. 克隆项目

```bash
git clone https://github.com/your-org/chs-sdk.git
cd chs-sdk
```

#### 2. 后端环境

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 环境变量配置
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等
```

#### 3. 前端环境

```bash
cd frontend
npm install
# 或使用 yarn
yarn install
```

#### 4. 数据库设置

```bash
# 启动 PostgreSQL 和 Redis
docker-compose up -d postgres redis

# 运行数据库迁移
alembic upgrade head

# 创建初始数据
python scripts/init_data.py
```

#### 5. 开发服务器

```bash
# 后端服务 (终端1)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 前端服务 (终端2)
cd frontend
npm run dev
```

### IDE配置

#### VS Code 推荐插件

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.isort",
    "ms-python.flake8",
    "ms-python.mypy-type-checker",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "ms-vscode.vscode-typescript-next",
    "ms-vscode-remote.remote-containers"
  ]
}
```

#### 配置文件

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

## 项目架构

### 整体架构

```
CHS仿真平台
├── 前端层 (React + TypeScript)
│   ├── 用户界面组件
│   ├── 状态管理 (Redux Toolkit)
│   ├── 路由管理 (React Router)
│   └── API客户端 (Axios)
├── API网关层 (FastAPI)
│   ├── 认证授权中间件
│   ├── 请求验证
│   ├── 响应格式化
│   └── 错误处理
├── 业务逻辑层
│   ├── 用户管理服务
│   ├── 仿真管理服务
│   ├── 数据处理服务
│   └── 文件管理服务
├── 数据访问层
│   ├── ORM模型 (SQLAlchemy)
│   ├── 数据库操作
│   ├── 缓存管理 (Redis)
│   └── 文件存储
└── 基础设施层
    ├── 数据库 (PostgreSQL)
    ├── 缓存 (Redis)
    ├── 消息队列 (Celery)
    └── 文件存储 (MinIO)
```

### 目录结构

```
chs-sdk/
├── api/                    # API层
│   ├── __init__.py
│   ├── main.py            # FastAPI应用入口
│   ├── dependencies.py   # 依赖注入
│   ├── middleware/        # 中间件
│   ├── routes/           # 路由定义
│   └── schemas/          # Pydantic模型
├── core/                  # 核心业务逻辑
│   ├── __init__.py
│   ├── config.py         # 配置管理
│   ├── security.py       # 安全相关
│   ├── database.py       # 数据库连接
│   └── cache.py          # 缓存管理
├── models/               # 数据模型
│   ├── __init__.py
│   ├── user.py          # 用户模型
│   ├── simulation.py    # 仿真模型
│   └── base.py          # 基础模型
├── services/             # 业务服务
│   ├── __init__.py
│   ├── user_service.py
│   ├── simulation_service.py
│   └── file_service.py
├── utils/                # 工具函数
│   ├── __init__.py
│   ├── helpers.py
│   └── validators.py
├── tests/                # 测试代码
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── conftest.py
├── frontend/             # 前端代码
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── tsconfig.json
├── docs/                 # 文档
├── scripts/              # 脚本工具
├── docker/               # Docker配置
├── k8s/                  # Kubernetes配置
├── requirements.txt      # Python依赖
├── docker-compose.yml    # 开发环境
└── README.md
```

## API开发

### FastAPI基础

#### 路由定义

```python
# api/routes/simulations.py
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ..schemas.simulation import SimulationCreate, SimulationResponse
from ..services.simulation_service import SimulationService
from ..dependencies import get_current_user, get_simulation_service

router = APIRouter(prefix="/simulations", tags=["仿真管理"])

@router.post("/", response_model=SimulationResponse)
async def create_simulation(
    simulation_data: SimulationCreate,
    current_user = Depends(get_current_user),
    service: SimulationService = Depends(get_simulation_service)
):
    """
    创建新的仿真任务
    
    - **name**: 仿真名称
    - **description**: 仿真描述
    - **config**: 仿真配置参数
    """
    try:
        simulation = await service.create_simulation(
            user_id=current_user.id,
            simulation_data=simulation_data
        )
        return simulation
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[SimulationResponse])
async def list_simulations(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user),
    service: SimulationService = Depends(get_simulation_service)
):
    """
    获取用户的仿真列表
    """
    simulations = await service.get_user_simulations(
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return simulations
```

#### 数据验证

```python
# api/schemas/simulation.py
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class SimulationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class SimulationConfig(BaseModel):
    duration: float = Field(..., gt=0, description="仿真时长(秒)")
    step_size: float = Field(..., gt=0, le=1.0, description="时间步长")
    output_interval: float = Field(..., gt=0, description="输出间隔")
    solver: str = Field(..., description="求解器类型")
    
    @validator('output_interval')
    def validate_output_interval(cls, v, values):
        if 'step_size' in values and v < values['step_size']:
            raise ValueError('输出间隔不能小于时间步长')
        return v

class SimulationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    config: SimulationConfig
    parameters: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)

class SimulationResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: SimulationStatus
    config: SimulationConfig
    parameters: Dict[str, Any]
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    user_id: int
    
    class Config:
        orm_mode = True
```

#### 依赖注入

```python
# api/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .core.database import get_db
from .core.security import verify_token
from .services.user_service import UserService
from .services.simulation_service import SimulationService

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    获取当前认证用户
    """
    try:
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌"
            )
        
        user_service = UserService(db)
        user = await user_service.get_user_by_id(int(user_id))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在"
            )
        return user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败"
        )

def get_simulation_service(db: Session = Depends(get_db)):
    """
    获取仿真服务实例
    """
    return SimulationService(db)
```

### 错误处理

```python
# api/middleware/error_handler.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def http_exception_handler(request: Request, exc: HTTPException):
    """
    HTTP异常处理器
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "details": {}
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    数据验证异常处理器
    """
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "输入数据验证失败",
                "details": exc.errors()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    """
    通用异常处理器
    """
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "服务器内部错误",
                "details": {}
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

### 中间件

```python
# api/middleware/cors.py
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

def setup_cors(app: FastAPI):
    """
    配置CORS中间件
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",  # 开发环境
            "https://chs-platform.com",  # 生产环境
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# api/middleware/logging.py
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件
    """
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # 记录请求信息
        logger.info(
            f"请求开始: {request.method} {request.url} "
            f"客户端: {request.client.host if request.client else 'unknown'}"
        )
        
        response = await call_next(request)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 记录响应信息
        logger.info(
            f"请求完成: {request.method} {request.url} "
            f"状态码: {response.status_code} "
            f"处理时间: {process_time:.3f}s"
        )
        
        response.headers["X-Process-Time"] = str(process_time)
        return response
```

## 前端开发

### React + TypeScript

#### 组件开发

```typescript
// frontend/src/components/SimulationCard.tsx
import React from 'react';
import { Card, Badge, Button, Tooltip } from 'antd';
import { PlayCircleOutlined, PauseCircleOutlined, StopOutlined } from '@ant-design/icons';
import { Simulation, SimulationStatus } from '../types/simulation';
import { formatDateTime, formatDuration } from '../utils/formatters';

interface SimulationCardProps {
  simulation: Simulation;
  onStart: (id: number) => void;
  onPause: (id: number) => void;
  onStop: (id: number) => void;
  onView: (id: number) => void;
}

const statusColors: Record<SimulationStatus, string> = {
  pending: 'orange',
  running: 'blue',
  completed: 'green',
  failed: 'red',
  cancelled: 'gray',
};

const statusLabels: Record<SimulationStatus, string> = {
  pending: '等待中',
  running: '运行中',
  completed: '已完成',
  failed: '已失败',
  cancelled: '已取消',
};

export const SimulationCard: React.FC<SimulationCardProps> = ({
  simulation,
  onStart,
  onPause,
  onStop,
  onView,
}) => {
  const { id, name, description, status, config, created_at, updated_at } = simulation;

  const renderActions = () => {
    const actions = [];

    if (status === 'pending' || status === 'failed') {
      actions.push(
        <Tooltip title="启动仿真" key="start">
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={() => onStart(id)}
          >
            启动
          </Button>
        </Tooltip>
      );
    }

    if (status === 'running') {
      actions.push(
        <Tooltip title="暂停仿真" key="pause">
          <Button
            icon={<PauseCircleOutlined />}
            onClick={() => onPause(id)}
          >
            暂停
          </Button>
        </Tooltip>
      );
      actions.push(
        <Tooltip title="停止仿真" key="stop">
          <Button
            danger
            icon={<StopOutlined />}
            onClick={() => onStop(id)}
          >
            停止
          </Button>
        </Tooltip>
      );
    }

    actions.push(
      <Button key="view" onClick={() => onView(id)}>
        查看详情
      </Button>
    );

    return actions;
  };

  return (
    <Card
      title={
        <div className="flex justify-between items-center">
          <span className="font-semibold">{name}</span>
          <Badge
            color={statusColors[status]}
            text={statusLabels[status]}
          />
        </div>
      }
      actions={renderActions()}
      className="mb-4 hover:shadow-lg transition-shadow"
    >
      <div className="space-y-2">
        {description && (
          <p className="text-gray-600 text-sm">{description}</p>
        )}
        
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="font-medium">仿真时长:</span>
            <span className="ml-2">{formatDuration(config.duration)}</span>
          </div>
          <div>
            <span className="font-medium">时间步长:</span>
            <span className="ml-2">{config.step_size}s</span>
          </div>
          <div>
            <span className="font-medium">创建时间:</span>
            <span className="ml-2">{formatDateTime(created_at)}</span>
          </div>
          <div>
            <span className="font-medium">更新时间:</span>
            <span className="ml-2">{formatDateTime(updated_at)}</span>
          </div>
        </div>
      </div>
    </Card>
  );
};
```

#### 状态管理

```typescript
// frontend/src/store/slices/simulationSlice.ts
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { Simulation, SimulationCreate } from '../../types/simulation';
import { simulationApi } from '../../api/simulation';

interface SimulationState {
  simulations: Simulation[];
  currentSimulation: Simulation | null;
  loading: boolean;
  error: string | null;
  pagination: {
    current: number;
    pageSize: number;
    total: number;
  };
}

const initialState: SimulationState = {
  simulations: [],
  currentSimulation: null,
  loading: false,
  error: null,
  pagination: {
    current: 1,
    pageSize: 10,
    total: 0,
  },
};

// 异步操作
export const fetchSimulations = createAsyncThunk(
  'simulation/fetchSimulations',
  async (params: { page?: number; pageSize?: number } = {}) => {
    const { page = 1, pageSize = 10 } = params;
    const response = await simulationApi.getSimulations({
      skip: (page - 1) * pageSize,
      limit: pageSize,
    });
    return {
      data: response.data,
      pagination: {
        current: page,
        pageSize,
        total: response.total,
      },
    };
  }
);

export const createSimulation = createAsyncThunk(
  'simulation/createSimulation',
  async (simulationData: SimulationCreate) => {
    const response = await simulationApi.createSimulation(simulationData);
    return response.data;
  }
);

export const startSimulation = createAsyncThunk(
  'simulation/startSimulation',
  async (id: number) => {
    const response = await simulationApi.startSimulation(id);
    return response.data;
  }
);

// Slice定义
const simulationSlice = createSlice({
  name: 'simulation',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    setCurrentSimulation: (state, action: PayloadAction<Simulation | null>) => {
      state.currentSimulation = action.payload;
    },
    updateSimulationStatus: (state, action: PayloadAction<{ id: number; status: string }>) => {
      const { id, status } = action.payload;
      const simulation = state.simulations.find(s => s.id === id);
      if (simulation) {
        simulation.status = status as any;
        simulation.updated_at = new Date().toISOString();
      }
      if (state.currentSimulation?.id === id) {
        state.currentSimulation.status = status as any;
        state.currentSimulation.updated_at = new Date().toISOString();
      }
    },
  },
  extraReducers: (builder) => {
    builder
      // 获取仿真列表
      .addCase(fetchSimulations.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchSimulations.fulfilled, (state, action) => {
        state.loading = false;
        state.simulations = action.payload.data;
        state.pagination = action.payload.pagination;
      })
      .addCase(fetchSimulations.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || '获取仿真列表失败';
      })
      // 创建仿真
      .addCase(createSimulation.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createSimulation.fulfilled, (state, action) => {
        state.loading = false;
        state.simulations.unshift(action.payload);
      })
      .addCase(createSimulation.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || '创建仿真失败';
      })
      // 启动仿真
      .addCase(startSimulation.fulfilled, (state, action) => {
        const simulation = state.simulations.find(s => s.id === action.payload.id);
        if (simulation) {
          Object.assign(simulation, action.payload);
        }
      });
  },
});

export const { clearError, setCurrentSimulation, updateSimulationStatus } = simulationSlice.actions;
export default simulationSlice.reducer;
```

#### API客户端

```typescript
// frontend/src/api/simulation.ts
import { apiClient } from './client';
import { Simulation, SimulationCreate } from '../types/simulation';

export interface GetSimulationsParams {
  skip?: number;
  limit?: number;
  status?: string;
  search?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  total?: number;
}

export const simulationApi = {
  // 获取仿真列表
  async getSimulations(params: GetSimulationsParams = {}): Promise<ApiResponse<Simulation[]>> {
    const response = await apiClient.get('/simulations', { params });
    return response.data;
  },

  // 获取单个仿真
  async getSimulation(id: number): Promise<ApiResponse<Simulation>> {
    const response = await apiClient.get(`/simulations/${id}`);
    return response.data;
  },

  // 创建仿真
  async createSimulation(data: SimulationCreate): Promise<ApiResponse<Simulation>> {
    const response = await apiClient.post('/simulations', data);
    return response.data;
  },

  // 启动仿真
  async startSimulation(id: number): Promise<ApiResponse<Simulation>> {
    const response = await apiClient.post(`/simulations/${id}/start`);
    return response.data;
  },

  // 暂停仿真
  async pauseSimulation(id: number): Promise<ApiResponse<Simulation>> {
    const response = await apiClient.post(`/simulations/${id}/pause`);
    return response.data;
  },

  // 停止仿真
  async stopSimulation(id: number): Promise<ApiResponse<Simulation>> {
    const response = await apiClient.post(`/simulations/${id}/stop`);
    return response.data;
  },

  // 删除仿真
  async deleteSimulation(id: number): Promise<ApiResponse<void>> {
    const response = await apiClient.delete(`/simulations/${id}`);
    return response.data;
  },

  // 获取仿真结果
  async getSimulationResults(id: number): Promise<ApiResponse<any>> {
    const response = await apiClient.get(`/simulations/${id}/results`);
    return response.data;
  },
};
```

## 数据库设计

### 模型定义

```python
# models/simulation.py
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import BaseModel
import enum

class SimulationStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Simulation(BaseModel):
    __tablename__ = "simulations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    status = Column(Enum(SimulationStatus), default=SimulationStatus.PENDING, index=True)
    config = Column(JSON, nullable=False)
    parameters = Column(JSON, default={})
    tags = Column(JSON, default=[])
    
    # 时间字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # 外键关系
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True)
    
    # 关系
    user = relationship("User", back_populates="simulations")
    project = relationship("Project", back_populates="simulations")
    results = relationship("SimulationResult", back_populates="simulation", cascade="all, delete-orphan")
    files = relationship("SimulationFile", back_populates="simulation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Simulation(id={self.id}, name='{self.name}', status='{self.status}')>"

class SimulationResult(BaseModel):
    __tablename__ = "simulation_results"
    
    id = Column(Integer, primary_key=True, index=True)
    simulation_id = Column(Integer, ForeignKey("simulations.id"), nullable=False, index=True)
    
    # 结果数据
    data_type = Column(String(50), nullable=False)  # 'timeseries', 'field', 'scalar'
    variable_name = Column(String(100), nullable=False, index=True)
    data = Column(JSON, nullable=False)
    metadata = Column(JSON, default={})
    
    # 时间信息
    timestamp = Column(Float)  # 仿真时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    simulation = relationship("Simulation", back_populates="results")
    
    def __repr__(self):
        return f"<SimulationResult(id={self.id}, variable='{self.variable_name}')>"
```

### 数据库迁移

```python
# alembic/versions/001_create_simulations.py
"""创建仿真相关表

Revision ID: 001
Revises: 
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # 创建仿真状态枚举
    simulation_status = postgresql.ENUM(
        'pending', 'running', 'completed', 'failed', 'cancelled',
        name='simulationstatus'
    )
    simulation_status.create(op.get_bind())
    
    # 创建仿真表
    op.create_table(
        'simulations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', simulation_status, nullable=True),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('parameters', sa.JSON(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('ix_simulations_id', 'simulations', ['id'])
    op.create_index('ix_simulations_name', 'simulations', ['name'])
    op.create_index('ix_simulations_status', 'simulations', ['status'])
    op.create_index('ix_simulations_created_at', 'simulations', ['created_at'])
    op.create_index('ix_simulations_user_id', 'simulations', ['user_id'])
    op.create_index('ix_simulations_project_id', 'simulations', ['project_id'])
    
    # 创建仿真结果表
    op.create_table(
        'simulation_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('simulation_id', sa.Integer(), nullable=False),
        sa.Column('data_type', sa.String(length=50), nullable=False),
        sa.Column('variable_name', sa.String(length=100), nullable=False),
        sa.Column('data', sa.JSON(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['simulation_id'], ['simulations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('ix_simulation_results_id', 'simulation_results', ['id'])
    op.create_index('ix_simulation_results_simulation_id', 'simulation_results', ['simulation_id'])
    op.create_index('ix_simulation_results_variable_name', 'simulation_results', ['variable_name'])

def downgrade():
    op.drop_index('ix_simulation_results_variable_name', table_name='simulation_results')
    op.drop_index('ix_simulation_results_simulation_id', table_name='simulation_results')
    op.drop_index('ix_simulation_results_id', table_name='simulation_results')
    op.drop_table('simulation_results')
    
    op.drop_index('ix_simulations_project_id', table_name='simulations')
    op.drop_index('ix_simulations_user_id', table_name='simulations')
    op.drop_index('ix_simulations_created_at', table_name='simulations')
    op.drop_index('ix_simulations_status', table_name='simulations')
    op.drop_index('ix_simulations_name', table_name='simulations')
    op.drop_index('ix_simulations_id', table_name='simulations')
    op.drop_table('simulations')
    
    # 删除枚举类型
    simulation_status = postgresql.ENUM(
        'pending', 'running', 'completed', 'failed', 'cancelled',
        name='simulationstatus'
    )
    simulation_status.drop(op.get_bind())
```

## 测试指南

### 单元测试

```python
# tests/unit/test_simulation_service.py
import pytest
from unittest.mock import Mock, AsyncMock
from services.simulation_service import SimulationService
from models.simulation import Simulation, SimulationStatus
from schemas.simulation import SimulationCreate, SimulationConfig

class TestSimulationService:
    
    @pytest.fixture
    def mock_db(self):
        return Mock()
    
    @pytest.fixture
    def simulation_service(self, mock_db):
        return SimulationService(mock_db)
    
    @pytest.fixture
    def sample_simulation_data(self):
        return SimulationCreate(
            name="测试仿真",
            description="这是一个测试仿真",
            config=SimulationConfig(
                duration=3600,
                step_size=0.1,
                output_interval=10,
                solver="euler"
            ),
            parameters={"temperature": 25.0},
            tags=["test"]
        )
    
    @pytest.mark.asyncio
    async def test_create_simulation_success(self, simulation_service, sample_simulation_data):
        # 准备
        user_id = 1
        expected_simulation = Simulation(
            id=1,
            name=sample_simulation_data.name,
            description=sample_simulation_data.description,
            status=SimulationStatus.PENDING,
            config=sample_simulation_data.config.dict(),
            parameters=sample_simulation_data.parameters,
            tags=sample_simulation_data.tags,
            user_id=user_id
        )
        
        simulation_service._create_simulation_record = AsyncMock(return_value=expected_simulation)
        simulation_service._validate_simulation_config = Mock(return_value=True)
        
        # 执行
        result = await simulation_service.create_simulation(user_id, sample_simulation_data)
        
        # 验证
        assert result.id == expected_simulation.id
        assert result.name == sample_simulation_data.name
        assert result.status == SimulationStatus.PENDING
        simulation_service._validate_simulation_config.assert_called_once()
        simulation_service._create_simulation_record.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_simulation_invalid_config(self, simulation_service, sample_simulation_data):
        # 准备
        user_id = 1
        simulation_service._validate_simulation_config = Mock(
            side_effect=ValueError("无效的配置参数")
        )
        
        # 执行和验证
        with pytest.raises(ValueError, match="无效的配置参数"):
            await simulation_service.create_simulation(user_id, sample_simulation_data)
    
    def test_validate_simulation_config_valid(self, simulation_service):
        # 准备
        config = SimulationConfig(
            duration=3600,
            step_size=0.1,
            output_interval=10,
            solver="euler"
        )
        
        # 执行和验证
        assert simulation_service._validate_simulation_config(config) is True
    
    def test_validate_simulation_config_invalid_step_size(self, simulation_service):
        # 准备
        config = SimulationConfig(
            duration=3600,
            step_size=0,  # 无效的步长
            output_interval=10,
            solver="euler"
        )
        
        # 执行和验证
        with pytest.raises(ValueError, match="时间步长必须大于0"):
            simulation_service._validate_simulation_config(config)
```

### 集成测试

```python
# tests/integration/test_simulation_api.py
import pytest
from httpx import AsyncClient
from fastapi import status
from main import app
from tests.conftest import test_user, auth_headers

class TestSimulationAPI:
    
    @pytest.mark.asyncio
    async def test_create_simulation(self, client: AsyncClient, auth_headers):
        # 准备测试数据
        simulation_data = {
            "name": "集成测试仿真",
            "description": "这是一个集成测试",
            "config": {
                "duration": 3600,
                "step_size": 0.1,
                "output_interval": 10,
                "solver": "euler"
            },
            "parameters": {
                "temperature": 25.0,
                "pressure": 101325
            },
            "tags": ["integration", "test"]
        }
        
        # 发送请求
        response = await client.post(
            "/simulations",
            json=simulation_data,
            headers=auth_headers
        )
        
        # 验证响应
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == simulation_data["name"]
        assert data["data"]["status"] == "pending"
        assert "id" in data["data"]
    
    @pytest.mark.asyncio
    async def test_get_simulations(self, client: AsyncClient, auth_headers, test_simulation):
        # 发送请求
        response = await client.get(
            "/simulations",
            headers=auth_headers
        )
        
        # 验证响应
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0
    
    @pytest.mark.asyncio
    async def test_start_simulation(self, client: AsyncClient, auth_headers, test_simulation):
        # 发送请求
        response = await client.post(
            f"/simulations/{test_simulation.id}/start",
            headers=auth_headers
        )
        
        # 验证响应
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "running"
    
    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client: AsyncClient):
        # 发送未认证请求
        response = await client.get("/simulations")
        
        # 验证响应
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
```

### 端到端测试

```python
# tests/e2e/test_simulation_workflow.py
import pytest
from playwright.async_api import async_playwright, Page
import asyncio

class TestSimulationWorkflow:
    
    @pytest.mark.asyncio
    async def test_complete_simulation_workflow(self):
        async with async_playwright() as p:
            # 启动浏览器
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # 1. 登录
                await self._login(page)
                
                # 2. 创建仿真
                simulation_name = await self._create_simulation(page)
                
                # 3. 启动仿真
                await self._start_simulation(page, simulation_name)
                
                # 4. 监控仿真进度
                await self._monitor_simulation(page, simulation_name)
                
                # 5. 查看结果
                await self._view_results(page, simulation_name)
                
            finally:
                await browser.close()
    
    async def _login(self, page: Page):
        await page.goto("http://localhost:3000/login")
        await page.fill("input[name='username']", "test@example.com")
        await page.fill("input[name='password']", "password123")
        await page.click("button[type='submit']")
        await page.wait_for_url("**/dashboard")
    
    async def _create_simulation(self, page: Page) -> str:
        await page.click("text=创建仿真")
        
        simulation_name = f"E2E测试仿真_{int(asyncio.get_event_loop().time())}"
        await page.fill("input[name='name']", simulation_name)
        await page.fill("textarea[name='description']", "端到端测试仿真")
        
        # 配置参数
        await page.fill("input[name='duration']", "3600")
        await page.fill("input[name='step_size']", "0.1")
        await page.select_option("select[name='solver']", "euler")
        
        await page.click("button[type='submit']")
        await page.wait_for_selector("text=仿真创建成功")
        
        return simulation_name
    
    async def _start_simulation(self, page: Page, simulation_name: str):
        # 找到仿真卡片并启动
        simulation_card = page.locator(f"text={simulation_name}").locator("..").locator("..")
        await simulation_card.locator("button:has-text('启动')").click()
        
        # 等待状态变为运行中
        await page.wait_for_selector("text=运行中")
    
    async def _monitor_simulation(self, page: Page, simulation_name: str):
        # 等待仿真完成（最多等待60秒）
        try:
            await page.wait_for_selector("text=已完成", timeout=60000)
        except:
            # 如果超时，检查是否有错误
            error_element = page.locator("text=已失败")
            if await error_element.count() > 0:
                pytest.fail("仿真执行失败")
            else:
                pytest.fail("仿真执行超时")
    
    async def _view_results(self, page: Page, simulation_name: str):
        # 点击查看详情
        simulation_card = page.locator(f"text={simulation_name}").locator("..").locator("..")
        await simulation_card.locator("button:has-text('查看详情')").click()
        
        # 验证结果页面
        await page.wait_for_selector("text=仿真结果")
        await page.wait_for_selector("canvas")  # 等待图表加载
        
        # 验证数据表格
        table = page.locator("table")
        assert await table.count() > 0
```

## 部署指南

### Docker部署

```dockerfile
# Dockerfile
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes部署

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chs-api
  labels:
    app: chs-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: chs-api
  template:
    metadata:
      labels:
        app: chs-api
    spec:
      containers:
      - name: api
        image: chs-platform/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: chs-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: chs-secrets
              key: redis-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: chs-api-service
spec:
  selector:
    app: chs-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

## 最佳实践

### 代码规范

1. **Python代码规范**
   - 使用Black进行代码格式化
   - 使用isort整理导入语句
   - 使用flake8进行代码检查
   - 使用mypy进行类型检查
   - 遵循PEP 8规范

2. **TypeScript代码规范**
   - 使用Prettier进行代码格式化
   - 使用ESLint进行代码检查
   - 严格的TypeScript配置
   - 统一的命名约定

3. **Git提交规范**
   ```
   type(scope): description
   
   feat: 新功能
   fix: 修复bug
   docs: 文档更新
   style: 代码格式化
   refactor: 代码重构
   test: 测试相关
   chore: 构建工具或辅助工具的变动
   ```

### 性能优化

1. **数据库优化**
   - 合理使用索引
   - 避免N+1查询
   - 使用连接池
   - 定期分析查询性能

2. **缓存策略**
   - Redis缓存热点数据
   - 浏览器缓存静态资源
   - CDN加速
   - 合理设置缓存过期时间

3. **前端优化**
   - 代码分割和懒加载
   - 图片优化和压缩
   - 使用Web Workers处理计算密集任务
   - 虚拟滚动处理大数据集

### 安全最佳实践

1. **认证授权**
   - JWT令牌安全存储
   - 定期刷新令牌
   - 最小权限原则
   - 多因素认证

2. **数据保护**
   - 敏感数据加密
   - SQL注入防护
   - XSS攻击防护
   - CSRF保护

3. **网络安全**
   - HTTPS强制使用
   - 安全头设置
   - 速率限制
   - 防火墙配置

## 故障排除

### 常见问题

1. **数据库连接问题**
   ```bash
   # 检查数据库连接
   psql -h localhost -U postgres -d chs_db
   
   # 检查连接池状态
   SELECT * FROM pg_stat_activity;
   ```

2. **Redis连接问题**
   ```bash
   # 检查Redis连接
   redis-cli ping
   
   # 查看Redis信息
   redis-cli info
   ```

3. **性能问题**
   ```bash
   # 查看API响应时间
   curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8000/api/simulations"
   
   # 监控系统资源
   htop
   iotop
   ```

### 日志分析

```python
# utils/logging.py
import logging
import sys
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger

def setup_logging(app_name: str = "chs-platform", log_level: str = "INFO"):
    """
    配置应用日志
    """
    # 创建logger
    logger = logging.getLogger(app_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # JSON格式化器
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger
```

## 贡献指南

### 开发流程

1. **Fork项目**
   ```bash
   git clone https://github.com/your-username/chs-sdk.git
   cd chs-sdk
   git remote add upstream https://github.com/original-org/chs-sdk.git
   ```

2. **创建功能分支**
   ```bash
   git checkout -b feature/new-feature
   ```

3. **开发和测试**
   ```bash
   # 运行测试
   pytest
   
   # 代码检查
   black .
   isort .
   flake8
   mypy .
   ```

4. **提交代码**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   git push origin feature/new-feature
   ```

5. **创建Pull Request**
   - 详细描述变更内容
   - 关联相关Issue
   - 确保CI通过
   - 请求代码审查

### 代码审查

1. **审查要点**
   - 代码质量和规范
   - 测试覆盖率
   - 性能影响
   - 安全考虑
   - 文档完整性

2. **审查流程**
   - 至少2人审查
   - 所有评论必须解决
   - CI必须通过
   - 维护者最终批准

---

**文档版本**: v1.0.0  
**更新时间**: 2024年1月20日  
**维护团队**: CHS平台开发团队

> 本指南会随着项目发展持续更新，最新版本请查看项目仓库