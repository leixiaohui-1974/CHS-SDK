#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云服务集成模块

提供与阿里云各种服务的集成功能，包括：
- ECS实例管理
- OSS对象存储
- RDS数据库服务
- SLB负载均衡
- 监控和日志服务
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

try:
    from aliyunsdkcore.client import AcsClient
    from aliyunsdkcore.acs_exception.exceptions import ClientException, ServerException
    from aliyunsdkecs.request.v20140526 import DescribeInstancesRequest, CreateInstanceRequest
    from aliyunsdkslb.request.v20140515 import DescribeLoadBalancersRequest, CreateLoadBalancerRequest
    from aliyunsdkrds.request.v20140815 import DescribeDBInstancesRequest, CreateDBInstanceRequest
    ALIYUN_SDK_AVAILABLE = True
except ImportError:
    ALIYUN_SDK_AVAILABLE = False
    logging.warning("阿里云SDK未安装，相关功能将不可用")

class AliyunServiceError(Exception):
    """阿里云服务异常"""
    pass

class AliyunService:
    """阿里云服务管理器"""
    
    def __init__(self, access_key_id: str = None, access_key_secret: str = None, region: str = None):
        """
        初始化阿里云服务
        
        Args:
            access_key_id: 阿里云访问密钥ID
            access_key_secret: 阿里云访问密钥Secret
            region: 阿里云地域
        """
        self.access_key_id = access_key_id or os.getenv('ALIYUN_ACCESS_KEY_ID')
        self.access_key_secret = access_key_secret or os.getenv('ALIYUN_ACCESS_KEY_SECRET')
        self.region = region or os.getenv('ALIYUN_REGION', 'cn-hangzhou')
        
        if not ALIYUN_SDK_AVAILABLE:
            raise AliyunServiceError("阿里云SDK未安装，请安装 aliyun-python-sdk-core")
        
        if not self.access_key_id or not self.access_key_secret:
            raise AliyunServiceError("阿里云访问密钥未配置")
        
        self.client = AcsClient(self.access_key_id, self.access_key_secret, self.region)
        self.logger = logging.getLogger(__name__)
    
    def _make_request(self, request) -> Dict[str, Any]:
        """执行阿里云API请求"""
        try:
            response = self.client.do_action_with_exception(request)
            return json.loads(response.decode('utf-8'))
        except (ClientException, ServerException) as e:
            self.logger.error(f"阿里云API请求失败: {e}")
            raise AliyunServiceError(f"阿里云API请求失败: {e}")
    
    # ECS实例管理
    def list_ecs_instances(self, instance_name: str = None) -> List[Dict[str, Any]]:
        """列出ECS实例"""
        request = DescribeInstancesRequest.DescribeInstancesRequest()
        request.set_RegionId(self.region)
        
        if instance_name:
            request.set_InstanceName(instance_name)
        
        response = self._make_request(request)
        return response.get('Instances', {}).get('Instance', [])
    
    def create_ecs_instance(self, 
                           instance_name: str,
                           image_id: str,
                           instance_type: str,
                           security_group_id: str,
                           vswitch_id: str,
                           **kwargs) -> str:
        """创建ECS实例"""
        request = CreateInstanceRequest.CreateInstanceRequest()
        request.set_RegionId(self.region)
        request.set_InstanceName(instance_name)
        request.set_ImageId(image_id)
        request.set_InstanceType(instance_type)
        request.set_SecurityGroupId(security_group_id)
        request.set_VSwitchId(vswitch_id)
        
        # 设置其他参数
        for key, value in kwargs.items():
            if hasattr(request, f'set_{key}'):
                getattr(request, f'set_{key}')(value)
        
        response = self._make_request(request)
        return response.get('InstanceId')
    
    def get_ecs_instance_status(self, instance_id: str) -> Dict[str, Any]:
        """获取ECS实例状态"""
        request = DescribeInstancesRequest.DescribeInstancesRequest()
        request.set_RegionId(self.region)
        request.set_InstanceIds(json.dumps([instance_id]))
        
        response = self._make_request(request)
        instances = response.get('Instances', {}).get('Instance', [])
        
        if not instances:
            raise AliyunServiceError(f"实例 {instance_id} 不存在")
        
        return instances[0]
    
    # SLB负载均衡管理
    def list_load_balancers(self, load_balancer_name: str = None) -> List[Dict[str, Any]]:
        """列出负载均衡器"""
        request = DescribeLoadBalancersRequest.DescribeLoadBalancersRequest()
        request.set_RegionId(self.region)
        
        if load_balancer_name:
            request.set_LoadBalancerName(load_balancer_name)
        
        response = self._make_request(request)
        return response.get('LoadBalancers', {}).get('LoadBalancer', [])
    
    def create_load_balancer(self, 
                            load_balancer_name: str,
                            load_balancer_spec: str = 'slb.s2.small',
                            **kwargs) -> str:
        """创建负载均衡器"""
        request = CreateLoadBalancerRequest.CreateLoadBalancerRequest()
        request.set_RegionId(self.region)
        request.set_LoadBalancerName(load_balancer_name)
        request.set_LoadBalancerSpec(load_balancer_spec)
        
        # 设置其他参数
        for key, value in kwargs.items():
            if hasattr(request, f'set_{key}'):
                getattr(request, f'set_{key}')(value)
        
        response = self._make_request(request)
        return response.get('LoadBalancerId')
    
    # RDS数据库管理
    def list_rds_instances(self, db_instance_id: str = None) -> List[Dict[str, Any]]:
        """列出RDS实例"""
        request = DescribeDBInstancesRequest.DescribeDBInstancesRequest()
        request.set_RegionId(self.region)
        
        if db_instance_id:
            request.set_DBInstanceId(db_instance_id)
        
        response = self._make_request(request)
        return response.get('Items', {}).get('DBInstance', [])
    
    def create_rds_instance(self, 
                           db_instance_id: str,
                           engine: str,
                           engine_version: str,
                           db_instance_class: str,
                           **kwargs) -> str:
        """创建RDS实例"""
        request = CreateDBInstanceRequest.CreateDBInstanceRequest()
        request.set_RegionId(self.region)
        request.set_DBInstanceId(db_instance_id)
        request.set_Engine(engine)
        request.set_EngineVersion(engine_version)
        request.set_DBInstanceClass(db_instance_class)
        
        # 设置其他参数
        for key, value in kwargs.items():
            if hasattr(request, f'set_{key}'):
                getattr(request, f'set_{key}')(value)
        
        response = self._make_request(request)
        return response.get('DBInstanceId')
    
    # 监控和统计
    def get_resource_usage(self) -> Dict[str, Any]:
        """获取资源使用情况"""
        try:
            # 获取ECS实例统计
            ecs_instances = self.list_ecs_instances()
            ecs_stats = {
                'total': len(ecs_instances),
                'running': len([i for i in ecs_instances if i.get('Status') == 'Running']),
                'stopped': len([i for i in ecs_instances if i.get('Status') == 'Stopped'])
            }
            
            # 获取SLB统计
            slb_instances = self.list_load_balancers()
            slb_stats = {
                'total': len(slb_instances),
                'active': len([i for i in slb_instances if i.get('LoadBalancerStatus') == 'active'])
            }
            
            # 获取RDS统计
            rds_instances = self.list_rds_instances()
            rds_stats = {
                'total': len(rds_instances),
                'running': len([i for i in rds_instances if i.get('DBInstanceStatus') == 'Running'])
            }
            
            return {
                'timestamp': datetime.now().isoformat(),
                'region': self.region,
                'ecs': ecs_stats,
                'slb': slb_stats,
                'rds': rds_stats
            }
        
        except Exception as e:
            self.logger.error(f"获取资源使用情况失败: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'region': self.region,
                'error': str(e)
            }
    
    def get_cost_analysis(self, days: int = 30) -> Dict[str, Any]:
        """获取成本分析（模拟数据）"""
        # 注意：实际的成本分析需要使用阿里云的费用中心API
        # 这里提供一个模拟的实现
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        return {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': days
            },
            'costs': {
                'ecs': {'amount': 150.50, 'currency': 'CNY'},
                'slb': {'amount': 45.20, 'currency': 'CNY'},
                'rds': {'amount': 89.30, 'currency': 'CNY'},
                'oss': {'amount': 12.80, 'currency': 'CNY'},
                'total': {'amount': 297.80, 'currency': 'CNY'}
            },
            'note': '这是模拟数据，实际成本请查看阿里云控制台'
        }
    
    # 健康检查
    def health_check(self) -> Dict[str, Any]:
        """阿里云服务健康检查"""
        try:
            # 尝试列出ECS实例来验证连接
            self.list_ecs_instances()
            
            return {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'region': self.region,
                'sdk_available': ALIYUN_SDK_AVAILABLE
            }
        
        except Exception as e:
            return {
                'status': 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'region': self.region,
                'error': str(e),
                'sdk_available': ALIYUN_SDK_AVAILABLE
            }

class AliyunOSSService:
    """阿里云OSS对象存储服务"""
    
    def __init__(self, access_key_id: str = None, access_key_secret: str = None, 
                 endpoint: str = None, bucket_name: str = None):
        """
        初始化OSS服务
        
        Args:
            access_key_id: 阿里云访问密钥ID
            access_key_secret: 阿里云访问密钥Secret
            endpoint: OSS端点
            bucket_name: 存储桶名称
        """
        self.access_key_id = access_key_id or os.getenv('ALIYUN_ACCESS_KEY_ID')
        self.access_key_secret = access_key_secret or os.getenv('ALIYUN_ACCESS_KEY_SECRET')
        self.endpoint = endpoint or os.getenv('ALIYUN_OSS_ENDPOINT', 'oss-cn-hangzhou.aliyuncs.com')
        self.bucket_name = bucket_name or os.getenv('ALIYUN_OSS_BUCKET_NAME')
        
        try:
            import oss2
            self.auth = oss2.Auth(self.access_key_id, self.access_key_secret)
            self.bucket = oss2.Bucket(self.auth, self.endpoint, self.bucket_name)
            self.oss_available = True
        except ImportError:
            self.oss_available = False
            logging.warning("阿里云OSS SDK未安装，OSS功能将不可用")
        
        self.logger = logging.getLogger(__name__)
    
    def upload_file(self, local_file_path: str, oss_key: str) -> bool:
        """上传文件到OSS"""
        if not self.oss_available:
            raise AliyunServiceError("OSS SDK未安装")
        
        try:
            self.bucket.put_object_from_file(oss_key, local_file_path)
            self.logger.info(f"文件上传成功: {local_file_path} -> {oss_key}")
            return True
        except Exception as e:
            self.logger.error(f"文件上传失败: {e}")
            return False
    
    def download_file(self, oss_key: str, local_file_path: str) -> bool:
        """从OSS下载文件"""
        if not self.oss_available:
            raise AliyunServiceError("OSS SDK未安装")
        
        try:
            self.bucket.get_object_to_file(oss_key, local_file_path)
            self.logger.info(f"文件下载成功: {oss_key} -> {local_file_path}")
            return True
        except Exception as e:
            self.logger.error(f"文件下载失败: {e}")
            return False
    
    def list_objects(self, prefix: str = '') -> List[str]:
        """列出OSS对象"""
        if not self.oss_available:
            raise AliyunServiceError("OSS SDK未安装")
        
        try:
            objects = []
            for obj in self.bucket.list_objects(prefix=prefix).object_list:
                objects.append(obj.key)
            return objects
        except Exception as e:
            self.logger.error(f"列出对象失败: {e}")
            return []
    
    def delete_object(self, oss_key: str) -> bool:
        """删除OSS对象"""
        if not self.oss_available:
            raise AliyunServiceError("OSS SDK未安装")
        
        try:
            self.bucket.delete_object(oss_key)
            self.logger.info(f"对象删除成功: {oss_key}")
            return True
        except Exception as e:
            self.logger.error(f"对象删除失败: {e}")
            return False

# 全局实例
_aliyun_service = None
_oss_service = None

def get_aliyun_service() -> AliyunService:
    """获取阿里云服务实例"""
    global _aliyun_service
    if _aliyun_service is None:
        _aliyun_service = AliyunService()
    return _aliyun_service

def get_oss_service() -> AliyunOSSService:
    """获取OSS服务实例"""
    global _oss_service
    if _oss_service is None:
        _oss_service = AliyunOSSService()
    return _oss_service