#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云服务API路由

提供阿里云资源管理的REST API接口，包括：
- ECS实例管理
- 负载均衡器管理
- RDS数据库管理
- OSS对象存储
- 资源监控和成本分析
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel, Field

from ..auth.dependencies import get_current_user
from ..services.aliyun_service import (
    get_aliyun_service, 
    get_oss_service, 
    AliyunService, 
    AliyunOSSService,
    AliyunServiceError
)

# 创建路由器
router = APIRouter(prefix="/api/aliyun", tags=["阿里云服务"])
logger = logging.getLogger(__name__)

# 数据模型
class ECSInstanceCreate(BaseModel):
    """ECS实例创建请求"""
    instance_name: str = Field(..., description="实例名称")
    image_id: str = Field(..., description="镜像ID")
    instance_type: str = Field(..., description="实例规格")
    security_group_id: str = Field(..., description="安全组ID")
    vswitch_id: str = Field(..., description="交换机ID")
    description: Optional[str] = Field(None, description="实例描述")
    internet_max_bandwidth_out: Optional[int] = Field(100, description="公网出带宽")
    instance_charge_type: Optional[str] = Field("PostPaid", description="计费方式")

class LoadBalancerCreate(BaseModel):
    """负载均衡器创建请求"""
    load_balancer_name: str = Field(..., description="负载均衡器名称")
    load_balancer_spec: str = Field("slb.s2.small", description="负载均衡器规格")
    internet_charge_type: Optional[str] = Field("PayByTraffic", description="计费方式")
    bandwidth: Optional[int] = Field(100, description="带宽")

class RDSInstanceCreate(BaseModel):
    """RDS实例创建请求"""
    db_instance_id: str = Field(..., description="数据库实例ID")
    engine: str = Field("MySQL", description="数据库引擎")
    engine_version: str = Field("8.0", description="引擎版本")
    db_instance_class: str = Field(..., description="实例规格")
    db_instance_storage: Optional[int] = Field(20, description="存储空间(GB)")
    security_ips: Optional[str] = Field("0.0.0.0/0", description="IP白名单")

class OSSUploadRequest(BaseModel):
    """OSS上传请求"""
    oss_key: str = Field(..., description="OSS对象键")
    local_file_path: Optional[str] = Field(None, description="本地文件路径")

class ResourceUsageResponse(BaseModel):
    """资源使用情况响应"""
    timestamp: str
    region: str
    ecs: Dict[str, int]
    slb: Dict[str, int]
    rds: Dict[str, int]
    error: Optional[str] = None

class CostAnalysisResponse(BaseModel):
    """成本分析响应"""
    period: Dict[str, Any]
    costs: Dict[str, Dict[str, Any]]
    note: str

class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str
    timestamp: str
    region: str
    sdk_available: bool
    error: Optional[str] = None

# ECS实例管理
@router.get("/ecs/instances", summary="列出ECS实例")
async def list_ecs_instances(
    instance_name: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """列出ECS实例"""
    try:
        aliyun_service = get_aliyun_service()
        instances = aliyun_service.list_ecs_instances(instance_name)
        return instances
    except AliyunServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"列出ECS实例失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")

@router.post("/ecs/instances", summary="创建ECS实例")
async def create_ecs_instance(
    request: ECSInstanceCreate,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, str]:
    """创建ECS实例"""
    try:
        aliyun_service = get_aliyun_service()
        instance_id = aliyun_service.create_ecs_instance(
            instance_name=request.instance_name,
            image_id=request.image_id,
            instance_type=request.instance_type,
            security_group_id=request.security_group_id,
            vswitch_id=request.vswitch_id,
            Description=request.description,
            InternetMaxBandwidthOut=request.internet_max_bandwidth_out,
            InstanceChargeType=request.instance_charge_type
        )
        return {"instance_id": instance_id, "message": "ECS实例创建成功"}
    except AliyunServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建ECS实例失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")

@router.get("/ecs/instances/{instance_id}", summary="获取ECS实例状态")
async def get_ecs_instance_status(
    instance_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取ECS实例状态"""
    try:
        aliyun_service = get_aliyun_service()
        instance = aliyun_service.get_ecs_instance_status(instance_id)
        return instance
    except AliyunServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取ECS实例状态失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")

# 负载均衡器管理
@router.get("/slb/load-balancers", summary="列出负载均衡器")
async def list_load_balancers(
    load_balancer_name: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """列出负载均衡器"""
    try:
        aliyun_service = get_aliyun_service()
        load_balancers = aliyun_service.list_load_balancers(load_balancer_name)
        return load_balancers
    except AliyunServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"列出负载均衡器失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")

@router.post("/slb/load-balancers", summary="创建负载均衡器")
async def create_load_balancer(
    request: LoadBalancerCreate,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, str]:
    """创建负载均衡器"""
    try:
        aliyun_service = get_aliyun_service()
        load_balancer_id = aliyun_service.create_load_balancer(
            load_balancer_name=request.load_balancer_name,
            load_balancer_spec=request.load_balancer_spec,
            InternetChargeType=request.internet_charge_type,
            Bandwidth=request.bandwidth
        )
        return {"load_balancer_id": load_balancer_id, "message": "负载均衡器创建成功"}
    except AliyunServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建负载均衡器失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")

# RDS数据库管理
@router.get("/rds/instances", summary="列出RDS实例")
async def list_rds_instances(
    db_instance_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """列出RDS实例"""
    try:
        aliyun_service = get_aliyun_service()
        instances = aliyun_service.list_rds_instances(db_instance_id)
        return instances
    except AliyunServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"列出RDS实例失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")

@router.post("/rds/instances", summary="创建RDS实例")
async def create_rds_instance(
    request: RDSInstanceCreate,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, str]:
    """创建RDS实例"""
    try:
        aliyun_service = get_aliyun_service()
        db_instance_id = aliyun_service.create_rds_instance(
            db_instance_id=request.db_instance_id,
            engine=request.engine,
            engine_version=request.engine_version,
            db_instance_class=request.db_instance_class,
            DBInstanceStorage=request.db_instance_storage,
            SecurityIPList=request.security_ips
        )
        return {"db_instance_id": db_instance_id, "message": "RDS实例创建成功"}
    except AliyunServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建RDS实例失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")

# OSS对象存储
@router.get("/oss/objects", summary="列出OSS对象")
async def list_oss_objects(
    prefix: str = "",
    current_user: dict = Depends(get_current_user)
) -> List[str]:
    """列出OSS对象"""
    try:
        oss_service = get_oss_service()
        objects = oss_service.list_objects(prefix)
        return objects
    except AliyunServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"列出OSS对象失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")

@router.post("/oss/upload", summary="上传文件到OSS")
async def upload_file_to_oss(
    file: UploadFile = File(...),
    oss_key: str = None,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, str]:
    """上传文件到OSS"""
    try:
        oss_service = get_oss_service()
        
        # 如果没有指定oss_key，使用文件名
        if not oss_key:
            oss_key = file.filename
        
        # 保存临时文件
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # 上传到OSS
            success = oss_service.upload_file(temp_file_path, oss_key)
            if success:
                return {"oss_key": oss_key, "message": "文件上传成功"}
            else:
                raise HTTPException(status_code=500, detail="文件上传失败")
        finally:
            # 清理临时文件
            os.unlink(temp_file_path)
            
    except AliyunServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"上传文件到OSS失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")

@router.delete("/oss/objects/{oss_key:path}", summary="删除OSS对象")
async def delete_oss_object(
    oss_key: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, str]:
    """删除OSS对象"""
    try:
        oss_service = get_oss_service()
        success = oss_service.delete_object(oss_key)
        if success:
            return {"message": "对象删除成功"}
        else:
            raise HTTPException(status_code=500, detail="对象删除失败")
    except AliyunServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"删除OSS对象失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")

# 监控和统计
@router.get("/monitoring/resource-usage", response_model=ResourceUsageResponse, summary="获取资源使用情况")
async def get_resource_usage(
    current_user: dict = Depends(get_current_user)
) -> ResourceUsageResponse:
    """获取阿里云资源使用情况"""
    try:
        aliyun_service = get_aliyun_service()
        usage = aliyun_service.get_resource_usage()
        return ResourceUsageResponse(**usage)
    except AliyunServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取资源使用情况失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")

@router.get("/monitoring/cost-analysis", response_model=CostAnalysisResponse, summary="获取成本分析")
async def get_cost_analysis(
    days: int = 30,
    current_user: dict = Depends(get_current_user)
) -> CostAnalysisResponse:
    """获取阿里云成本分析"""
    try:
        aliyun_service = get_aliyun_service()
        cost_analysis = aliyun_service.get_cost_analysis(days)
        return CostAnalysisResponse(**cost_analysis)
    except AliyunServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取成本分析失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")

@router.get("/health", response_model=HealthCheckResponse, summary="阿里云服务健康检查")
async def aliyun_health_check() -> HealthCheckResponse:
    """阿里云服务健康检查"""
    try:
        aliyun_service = get_aliyun_service()
        health = aliyun_service.health_check()
        return HealthCheckResponse(**health)
    except Exception as e:
        logger.error(f"阿里云健康检查失败: {e}")
        return HealthCheckResponse(
            status="unhealthy",
            timestamp="",
            region="",
            sdk_available=False,
            error=str(e)
        )