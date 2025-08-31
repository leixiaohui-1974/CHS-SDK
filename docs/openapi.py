#!/usr/bin/env python3
"""
OpenAPI文档生成配置
用于自动生成CHS仿真平台的API文档
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.staticfiles import StaticFiles
import json
import os
from typing import Dict, Any


def custom_openapi(app: FastAPI) -> Dict[str, Any]:
    """
    自定义OpenAPI规范生成
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="CHS仿真平台API",
        version="1.0.0",
        description="""
        # CHS仿真平台API文档
        
        这是一个全面的仿真平台API，提供以下功能：
        
        ## 核心功能
        - 🔐 **用户认证与授权** - JWT令牌认证，基于角色的访问控制
        - 🎯 **仿真管理** - 创建、启动、停止、监控仿真任务
        - 📊 **数据管理** - 仿真数据的存储、查询和分析
        - 🔄 **实时通信** - WebSocket实时状态更新
        - 📈 **性能监控** - 系统性能指标和健康状态监控
        
        ## 技术特性
        - RESTful API设计
        - 异步处理支持
        - 数据验证和序列化
        - 错误处理和日志记录
        - 缓存优化
        - 速率限制
        
        ## 认证方式
        使用Bearer Token进行认证：
        ```
        Authorization: Bearer <your-jwt-token>
        ```
        
        ## 响应格式
        所有API响应都遵循统一的格式：
        ```json
        {
            "success": true,
            "data": {},
            "message": "操作成功",
            "timestamp": "2024-01-20T10:30:00Z"
        }
        ```
        
        ## 错误处理
        错误响应包含详细的错误信息：
        ```json
        {
            "success": false,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "输入数据验证失败",
                "details": {}
            },
            "timestamp": "2024-01-20T10:30:00Z"
        }
        ```
        """,
        routes=app.routes,
        servers=[
            {
                "url": "http://localhost:8000",
                "description": "开发环境"
            },
            {
                "url": "https://api-staging.chs-platform.com",
                "description": "测试环境"
            },
            {
                "url": "https://api.chs-platform.com",
                "description": "生产环境"
            }
        ]
    )
    
    # 添加安全定义
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT认证令牌"
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API密钥认证"
        }
    }
    
    # 添加全局安全要求
    openapi_schema["security"] = [
        {"BearerAuth": []}
    ]
    
    # 添加标签分组
    openapi_schema["tags"] = [
        {
            "name": "认证",
            "description": "用户认证和授权相关接口"
        },
        {
            "name": "用户管理",
            "description": "用户信息管理接口"
        },
        {
            "name": "仿真管理",
            "description": "仿真任务的创建、管理和控制"
        },
        {
            "name": "数据管理",
            "description": "仿真数据的存储和查询"
        },
        {
            "name": "文件管理",
            "description": "文件上传、下载和管理"
        },
        {
            "name": "性能监控",
            "description": "系统性能和健康状态监控"
        },
        {
            "name": "系统管理",
            "description": "系统配置和管理接口"
        }
    ]
    
    # 添加示例
    add_examples_to_schema(openapi_schema)
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def add_examples_to_schema(schema: Dict[str, Any]) -> None:
    """
    为API模式添加示例数据
    """
    # 用户登录示例
    if "paths" in schema and "/auth/login" in schema["paths"]:
        login_path = schema["paths"]["/auth/login"]
        if "post" in login_path:
            login_path["post"]["requestBody"]["content"]["application/json"]["example"] = {
                "username": "admin@example.com",
                "password": "password123"
            }
    
    # 仿真创建示例
    if "paths" in schema and "/simulations" in schema["paths"]:
        sim_path = schema["paths"]["/simulations"]
        if "post" in sim_path:
            sim_path["post"]["requestBody"]["content"]["application/json"]["example"] = {
                "name": "测试仿真",
                "description": "这是一个测试仿真任务",
                "config": {
                    "duration": 3600,
                    "step_size": 0.1,
                    "output_interval": 10
                },
                "parameters": {
                    "temperature": 25.0,
                    "pressure": 101325,
                    "flow_rate": 100.0
                }
            }


def generate_api_docs(app: FastAPI, output_dir: str = "docs/api") -> None:
    """
    生成API文档文件
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成OpenAPI JSON
    openapi_schema = custom_openapi(app)
    with open(f"{output_dir}/openapi.json", "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, ensure_ascii=False, indent=2)
    
    # 生成Swagger UI HTML
    swagger_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>CHS仿真平台API文档 - Swagger UI</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui.css" />
        <style>
            html {{
                box-sizing: border-box;
                overflow: -moz-scrollbars-vertical;
                overflow-y: scroll;
            }}
            *, *:before, *:after {{
                box-sizing: inherit;
            }}
            body {{
                margin:0;
                background: #fafafa;
            }}
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-bundle.js"></script>
        <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-standalone-preset.js"></script>
        <script>
            window.onload = function() {{
                const ui = SwaggerUIBundle({{
                    url: './openapi.json',
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIStandalonePreset
                    ],
                    plugins: [
                        SwaggerUIBundle.plugins.DownloadUrl
                    ],
                    layout: "StandaloneLayout"
                }});
            }};
        </script>
    </body>
    </html>
    """
    
    with open(f"{output_dir}/swagger.html", "w", encoding="utf-8") as f:
        f.write(swagger_html)
    
    # 生成ReDoc HTML
    redoc_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>CHS仿真平台API文档 - ReDoc</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
        <style>
            body {{
                margin: 0;
                padding: 0;
            }}
        </style>
    </head>
    <body>
        <redoc spec-url='./openapi.json'></redoc>
        <script src="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.js"></script>
    </body>
    </html>
    """
    
    with open(f"{output_dir}/redoc.html", "w", encoding="utf-8") as f:
        f.write(redoc_html)
    
    print(f"API文档已生成到 {output_dir} 目录")
    print(f"- OpenAPI规范: {output_dir}/openapi.json")
    print(f"- Swagger UI: {output_dir}/swagger.html")
    print(f"- ReDoc: {output_dir}/redoc.html")


def setup_docs_routes(app: FastAPI) -> None:
    """
    设置文档路由
    """
    # 挂载静态文件
    app.mount("/docs/static", StaticFiles(directory="docs/api"), name="docs-static")
    
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title="CHS仿真平台API文档",
            swagger_favicon_url="/docs/static/favicon.ico"
        )
    
    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        return get_redoc_html(
            openapi_url="/openapi.json",
            title="CHS仿真平台API文档",
            redoc_favicon_url="/docs/static/favicon.ico"
        )


if __name__ == "__main__":
    # 示例用法
    from fastapi import FastAPI
    
    app = FastAPI()
    
    # 设置自定义OpenAPI
    app.openapi = lambda: custom_openapi(app)
    
    # 生成文档文件
    generate_api_docs(app)
    
    # 设置文档路由
    setup_docs_routes(app)