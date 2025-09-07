"""
Main FastAPI application for the CHS-SDK Simulation API.

This server provides an endpoint to run hydraulic simulations based on
a JSON configuration that conforms to the Pydantic models defined
in `core_lib.models`.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import logging
import os
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# 导入路由模块
from api.routes.simulation import router as simulation_router
from api.routes.websocket import router as websocket_router, cleanup_websocket_resources
from api.routes.auth import router as auth_router
from api.routes.monitoring import router as monitoring_router, set_performance_middleware
from api.routes.analysis import router as analysis_router
from api.routes.scenario import router as scenario_router
from api.routes.validator import router as validator_router
from api.routes.configurator import router as configurator_router
from api.routes.runner import router as runner_router
from api.routes.monitor import router as monitor_router
from api.routes.aliyun import router as aliyun_router
from startup.monitor_startup import lifespan

# 导入性能和缓存模块
from middleware.performance import PerformanceMonitoringMiddleware, RateLimitingMiddleware
from core.cache_manager import cache_manager, start_cache_cleanup_task
from config import settings

# 导入模型
from models.api_models import SimulationRequest
from models.simulation_models import SimulationResponse
from models.websocket_models import WebSocketMessage

# Configure logging for the application
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format=settings.log_format
)
logger = logging.getLogger(__name__)

# Initialize the FastAPI app
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    openapi_url=settings.openapi_url,
    lifespan=lifespan
)

# 创建性能监控中间件实例
performance_middleware = PerformanceMonitoringMiddleware(app)

# Add middleware in order (last added = first executed)
# 1. Performance monitoring (should be first to capture all requests)
app.add_middleware(PerformanceMonitoringMiddleware)

# 2. Rate limiting
if not settings.is_development():
    app.add_middleware(RateLimitingMiddleware, requests_per_minute=120)

# 3. GZIP compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 4. CORS (should be last)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# Set performance middleware for monitoring routes
set_performance_middleware(performance_middleware)

# Include routers
app.include_router(simulation_router, prefix=settings.api_prefix)
app.include_router(websocket_router, prefix=settings.api_prefix)
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(monitoring_router, prefix=settings.api_prefix)
app.include_router(analysis_router, prefix=settings.api_prefix)
app.include_router(scenario_router, prefix=settings.api_prefix)
app.include_router(validator_router, prefix=settings.api_prefix)
app.include_router(configurator_router, prefix=settings.api_prefix)
app.include_router(runner_router, prefix=settings.api_prefix)
app.include_router(monitor_router, prefix=settings.api_prefix)
app.include_router(aliyun_router, prefix=settings.api_prefix)

EXAMPLES_DIR = Path("examples")

def find_example_dirs(base_dir: Path) -> List[str]:
    """Recursively finds directories containing 'components.yml' and returns their relative paths."""
    example_dirs = []
    for entry in base_dir.rglob('components.yml'):
        if entry.is_file():
            # Represent the path as a string with forward slashes for consistency
            example_dir = entry.parent.relative_to(base_dir).as_posix()
            example_dirs.append(example_dir)
    return sorted(example_dirs)

@app.get("/api/examples", tags=["Examples"], response_model=List[str])
async def list_examples():
    """Returns a list of available example scenario paths."""
    if not EXAMPLES_DIR.is_dir():
        raise HTTPException(status_code=404, detail="Examples directory not found.")
    try:
        return find_example_dirs(EXAMPLES_DIR)
    except Exception as e:
        logging.error(f"Error scanning examples directory: {e}")
        raise HTTPException(status_code=500, detail="Failed to scan examples directory.")

import json

@app.get("/api/examples/{example_path:path}", tags=["Examples"], response_model=Dict[str, Any])
async def get_example_config(example_path: str):
    """
    Loads a pre-processed example configuration from a generated JSON file.
    """
    # Basic security check
    if ".." in example_path:
        raise HTTPException(status_code=400, detail="Invalid example path.")

    # Construct the path to the pre-generated JSON file
    json_filename = example_path.replace('/', '_') + '.json'
    json_filepath = EXAMPLES_DIR / "generated_json" / json_filename

    if not json_filepath.is_file():
        logging.error(f"Pre-processed JSON file not found: {json_filepath}")
        raise HTTPException(status_code=404, detail=f"Example configuration '{example_path}' not found. Have you run the preprocessing script?")

    try:
        with open(json_filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load or parse JSON file {json_filepath}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load example configuration.")

# Main entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )




# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """
    Application startup event
    """
    logger.info("CHS-SDK API server starting")
    
    try:
        # 初始化缓存管理器
        await cache_manager.initialize()
        logger.info("Cache manager initialized")
        
        # 启动缓存清理任务
        asyncio.create_task(start_cache_cleanup_task())
        logger.info("Cache cleanup task started")
        
        logger.info("CHS-SDK API server starting up...")
        logger.info(f"API documentation available at: {settings.docs_url}")
        logger.info(f"Server running in {'development' if settings.is_development() else 'production'} mode")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event
    """
    logger.info("CHS-SDK API server shutting down...")
    
    try:
        # Clean up WebSocket resources
        await cleanup_websocket_resources()
        logger.info("WebSocket resources cleaned up")
        
        # Clean up simulation resources
        from api.routes.simulation import cleanup_simulation_resources
        await cleanup_simulation_resources()
        logger.info("Simulation resources cleaned up")
        
        # Close Redis connection if exists
        if cache_manager.redis_client:
            await cache_manager.redis_client.close()
            logger.info("Redis connection closed")
        
        logger.info("CHS-SDK API server shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
        raise
