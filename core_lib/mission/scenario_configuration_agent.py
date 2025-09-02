"""ScenarioConfigurationAgent - 动态情景配置与管理智能体

该智能体负责：
1. 动态场景切换和配置管理
2. 场景模板库管理
3. 配置验证和智能体响应机制
4. 实时场景参数调整
"""

import yaml
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from core_lib.core.interfaces import Agent
from core_lib.central_coordination.collaboration.message_bus import MessageBus
from core_lib.io.yaml_loader import YamlLoader
from core_lib.io.yaml_writer import YamlWriter


@dataclass
class ScenarioTemplate:
    """场景模板数据结构"""
    name: str
    description: str
    category: str  # 'flood_control', 'drought_management', 'normal_operation', etc.
    parameters: Dict[str, Any]
    agents_config: Dict[str, Any]
    disturbances: List[Dict[str, Any]]
    objectives: Dict[str, Any]
    constraints: Dict[str, Any]
    created_at: datetime
    version: str = "1.0"


@dataclass
class ScenarioInstance:
    """场景实例数据结构"""
    scenario_id: str
    template_name: str
    parameters: Dict[str, Any]
    status: str  # 'active', 'inactive', 'pending'
    created_at: datetime
    last_modified: datetime


class ScenarioConfigurationAgent(Agent):
    """情景配置智能体
    
    功能特性：
    - 动态场景切换
    - 场景模板管理
    - 配置验证
    - 智能体响应机制
    - 参数化配置
    """
    
    def __init__(self, 
                 agent_id: str, 
                 message_bus: MessageBus,
                 template_directory: str = "scenarios/templates",
                 instance_directory: str = "scenarios/instances",
                 config_file: str = "scenarios.yml"):
        """初始化情景配置智能体
        
        Args:
            agent_id: 智能体唯一标识
            message_bus: 消息总线
            template_directory: 场景模板目录
            instance_directory: 场景实例目录
            config_file: 场景配置文件
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.template_dir = Path(template_directory)
        self.instance_dir = Path(instance_directory)
        self.config_file = config_file
        
        # 创建必要的目录
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.instance_dir.mkdir(parents=True, exist_ok=True)
        
        # 内部状态
        self.templates: Dict[str, ScenarioTemplate] = {}
        self.instances: Dict[str, ScenarioInstance] = {}
        self.current_scenario: Optional[str] = None
        self.yaml_loader = YamlLoader()
        self.yaml_writer = YamlWriter()
        
        # 订阅相关主题
        self.bus.subscribe("scenario/switch_request", self.handle_scenario_switch)
        self.bus.subscribe("scenario/parameter_update", self.handle_parameter_update)
        self.bus.subscribe("scenario/template_request", self.handle_template_request)
        self.bus.subscribe("scenario/validation_request", self.handle_validation_request)
        
        # 初始化
        self._load_templates()
        self._load_instances()
        
        print(f"ScenarioConfigurationAgent '{self.agent_id}' 初始化完成")
        print(f"已加载 {len(self.templates)} 个场景模板")
        print(f"已加载 {len(self.instances)} 个场景实例")
    
    def run(self, current_time: float):
        """智能体运行逻辑"""
        # 定期检查场景状态和配置一致性
        if int(current_time) % 10 == 0:  # 每10个时间单位检查一次
            self._validate_current_scenario()
    
    def _load_templates(self):
        """加载场景模板"""
        try:
            for template_file in self.template_dir.glob("*.yml"):
                template_data = self.yaml_loader.load(str(template_file))
                template = ScenarioTemplate(
                    name=template_data['name'],
                    description=template_data.get('description', ''),
                    category=template_data.get('category', 'general'),
                    parameters=template_data.get('parameters', {}),
                    agents_config=template_data.get('agents_config', {}),
                    disturbances=template_data.get('disturbances', []),
                    objectives=template_data.get('objectives', {}),
                    constraints=template_data.get('constraints', {}),
                    created_at=datetime.fromisoformat(template_data.get('created_at', datetime.now().isoformat())),
                    version=template_data.get('version', '1.0')
                )
                self.templates[template.name] = template
        except Exception as e:
            print(f"加载场景模板时出错: {e}")
    
    def _load_instances(self):
        """加载场景实例"""
        try:
            for instance_file in self.instance_dir.glob("*.yml"):
                instance_data = self.yaml_loader.load(str(instance_file))
                instance = ScenarioInstance(
                    scenario_id=instance_data['scenario_id'],
                    template_name=instance_data['template_name'],
                    parameters=instance_data.get('parameters', {}),
                    status=instance_data.get('status', 'inactive'),
                    created_at=datetime.fromisoformat(instance_data['created_at']),
                    last_modified=datetime.fromisoformat(instance_data.get('last_modified', instance_data['created_at']))
                )
                self.instances[instance.scenario_id] = instance
        except Exception as e:
            print(f"加载场景实例时出错: {e}")
    
    def handle_scenario_switch(self, message: Dict[str, Any]):
        """处理场景切换请求"""
        scenario_id = message.get('scenario_id')
        parameters = message.get('parameters', {})
        
        if scenario_id not in self.instances:
            self.bus.publish("scenario/switch_response", {
                "success": False,
                "error": f"场景实例 {scenario_id} 不存在"
            })
            return
        
        try:
            # 验证场景配置
            if self._validate_scenario(scenario_id, parameters):
                # 执行场景切换
                self._switch_scenario(scenario_id, parameters)
                self.bus.publish("scenario/switch_response", {
                    "success": True,
                    "scenario_id": scenario_id,
                    "message": f"成功切换到场景 {scenario_id}"
                })
            else:
                self.bus.publish("scenario/switch_response", {
                    "success": False,
                    "error": "场景配置验证失败"
                })
        except Exception as e:
            self.bus.publish("scenario/switch_response", {
                "success": False,
                "error": f"场景切换失败: {str(e)}"
            })
    
    def handle_parameter_update(self, message: Dict[str, Any]):
        """处理参数更新请求"""
        scenario_id = message.get('scenario_id', self.current_scenario)
        parameters = message.get('parameters', {})
        
        if not scenario_id or scenario_id not in self.instances:
            self.bus.publish("scenario/parameter_response", {
                "success": False,
                "error": "无效的场景ID"
            })
            return
        
        try:
            # 更新参数
            self._update_scenario_parameters(scenario_id, parameters)
            self.bus.publish("scenario/parameter_response", {
                "success": True,
                "scenario_id": scenario_id,
                "updated_parameters": parameters
            })
        except Exception as e:
            self.bus.publish("scenario/parameter_response", {
                "success": False,
                "error": f"参数更新失败: {str(e)}"
            })
    
    def handle_template_request(self, message: Dict[str, Any]):
        """处理模板请求"""
        request_type = message.get('type', 'list')
        
        if request_type == 'list':
            template_list = [
                {
                    'name': name,
                    'description': template.description,
                    'category': template.category,
                    'version': template.version
                }
                for name, template in self.templates.items()
            ]
            self.bus.publish("scenario/template_response", {
                "success": True,
                "templates": template_list
            })
        
        elif request_type == 'get':
            template_name = message.get('template_name')
            if template_name in self.templates:
                template = self.templates[template_name]
                self.bus.publish("scenario/template_response", {
                    "success": True,
                    "template": {
                        'name': template.name,
                        'description': template.description,
                        'category': template.category,
                        'parameters': template.parameters,
                        'agents_config': template.agents_config,
                        'disturbances': template.disturbances,
                        'objectives': template.objectives,
                        'constraints': template.constraints,
                        'version': template.version
                    }
                })
            else:
                self.bus.publish("scenario/template_response", {
                    "success": False,
                    "error": f"模板 {template_name} 不存在"
                })
    
    def handle_validation_request(self, message: Dict[str, Any]):
        """处理配置验证请求"""
        scenario_id = message.get('scenario_id')
        parameters = message.get('parameters', {})
        
        validation_result = self._validate_scenario(scenario_id, parameters)
        
        self.bus.publish("scenario/validation_response", {
            "success": validation_result['valid'],
            "scenario_id": scenario_id,
            "validation_details": validation_result
        })
    
    def _validate_scenario(self, scenario_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """验证场景配置"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # 检查场景实例是否存在
        if scenario_id not in self.instances:
            validation_result['valid'] = False
            validation_result['errors'].append(f"场景实例 {scenario_id} 不存在")
            return validation_result
        
        instance = self.instances[scenario_id]
        
        # 检查模板是否存在
        if instance.template_name not in self.templates:
            validation_result['valid'] = False
            validation_result['errors'].append(f"场景模板 {instance.template_name} 不存在")
            return validation_result
        
        template = self.templates[instance.template_name]
        
        # 验证参数
        for param_name, param_config in template.parameters.items():
            if param_config.get('required', False) and param_name not in parameters:
                validation_result['valid'] = False
                validation_result['errors'].append(f"缺少必需参数: {param_name}")
            
            if param_name in parameters:
                param_value = parameters[param_name]
                param_type = param_config.get('type')
                
                # 类型检查
                if param_type and not self._check_parameter_type(param_value, param_type):
                    validation_result['valid'] = False
                    validation_result['errors'].append(f"参数 {param_name} 类型错误，期望 {param_type}")
                
                # 范围检查
                if 'min' in param_config and param_value < param_config['min']:
                    validation_result['valid'] = False
                    validation_result['errors'].append(f"参数 {param_name} 小于最小值 {param_config['min']}")
                
                if 'max' in param_config and param_value > param_config['max']:
                    validation_result['valid'] = False
                    validation_result['errors'].append(f"参数 {param_name} 大于最大值 {param_config['max']}")
        
        return validation_result
    
    def _check_parameter_type(self, value: Any, expected_type: str) -> bool:
        """检查参数类型"""
        type_mapping = {
            'int': int,
            'float': (int, float),
            'str': str,
            'bool': bool,
            'list': list,
            'dict': dict
        }
        
        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)
        
        return True  # 未知类型默认通过
    
    def _switch_scenario(self, scenario_id: str, parameters: Dict[str, Any]):
        """执行场景切换"""
        instance = self.instances[scenario_id]
        template = self.templates[instance.template_name]
        
        # 合并参数
        merged_parameters = {**instance.parameters, **parameters}
        
        # 更新当前场景
        self.current_scenario = scenario_id
        
        # 通知其他智能体场景已切换
        self.bus.publish("scenario/switched", {
            "scenario_id": scenario_id,
            "template_name": instance.template_name,
            "parameters": merged_parameters,
            "agents_config": template.agents_config,
            "disturbances": template.disturbances,
            "objectives": template.objectives,
            "constraints": template.constraints
        })
        
        # 更新实例状态
        instance.status = 'active'
        instance.last_modified = datetime.now()
        
        # 保存实例
        self._save_instance(instance)
        
        print(f"场景切换完成: {scenario_id}")
    
    def _update_scenario_parameters(self, scenario_id: str, parameters: Dict[str, Any]):
        """更新场景参数"""
        instance = self.instances[scenario_id]
        
        # 更新参数
        instance.parameters.update(parameters)
        instance.last_modified = datetime.now()
        
        # 如果是当前活跃场景，通知其他智能体
        if scenario_id == self.current_scenario:
            self.bus.publish("scenario/parameters_updated", {
                "scenario_id": scenario_id,
                "updated_parameters": parameters,
                "all_parameters": instance.parameters
            })
        
        # 保存实例
        self._save_instance(instance)
    
    def _save_instance(self, instance: ScenarioInstance):
        """保存场景实例"""
        instance_data = {
            'scenario_id': instance.scenario_id,
            'template_name': instance.template_name,
            'parameters': instance.parameters,
            'status': instance.status,
            'created_at': instance.created_at.isoformat(),
            'last_modified': instance.last_modified.isoformat()
        }
        
        instance_file = self.instance_dir / f"{instance.scenario_id}.yml"
        self.yaml_writer.write(instance_data, str(instance_file))
    
    def _validate_current_scenario(self):
        """验证当前场景状态"""
        if self.current_scenario:
            instance = self.instances.get(self.current_scenario)
            if instance and instance.status != 'active':
                print(f"警告: 当前场景 {self.current_scenario} 状态异常: {instance.status}")
    
    def create_scenario_instance(self, 
                               scenario_id: str, 
                               template_name: str, 
                               parameters: Dict[str, Any]) -> bool:
        """创建新的场景实例"""
        if scenario_id in self.instances:
            print(f"场景实例 {scenario_id} 已存在")
            return False
        
        if template_name not in self.templates:
            print(f"场景模板 {template_name} 不存在")
            return False
        
        # 验证参数
        validation_result = self._validate_scenario_parameters(template_name, parameters)
        if not validation_result['valid']:
            print(f"参数验证失败: {validation_result['errors']}")
            return False
        
        # 创建实例
        instance = ScenarioInstance(
            scenario_id=scenario_id,
            template_name=template_name,
            parameters=parameters,
            status='inactive',
            created_at=datetime.now(),
            last_modified=datetime.now()
        )
        
        self.instances[scenario_id] = instance
        self._save_instance(instance)
        
        print(f"场景实例 {scenario_id} 创建成功")
        return True
    
    def _validate_scenario_parameters(self, template_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """验证场景参数（基于模板）"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        if template_name not in self.templates:
            validation_result['valid'] = False
            validation_result['errors'].append(f"模板 {template_name} 不存在")
            return validation_result
        
        template = self.templates[template_name]
        
        # 验证参数
        for param_name, param_config in template.parameters.items():
            if param_config.get('required', False) and param_name not in parameters:
                validation_result['valid'] = False
                validation_result['errors'].append(f"缺少必需参数: {param_name}")
        
        return validation_result
    
    def get_scenario_status(self) -> Dict[str, Any]:
        """获取场景状态信息"""
        return {
            'current_scenario': self.current_scenario,
            'total_templates': len(self.templates),
            'total_instances': len(self.instances),
            'active_instances': len([i for i in self.instances.values() if i.status == 'active'])
        }