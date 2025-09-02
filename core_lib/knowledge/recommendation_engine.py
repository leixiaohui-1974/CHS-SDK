# -*- coding: utf-8 -*-
"""
Recommendation Engine for CHS-SDK Knowledge Base
智能推荐引擎模块

Provides intelligent recommendations for agents, configurations,
and templates based on development context and user behavior.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re


class RecommendationEngine:
    """
    智能推荐引擎
    
    基于开发上下文、历史使用记录和相似性分析，
    为用户推荐合适的智能体、配置模板和最佳实践。
    """
    
    def __init__(self, kb_path: Path, config: Dict[str, Any]):
        """
        初始化推荐引擎
        
        Args:
            kb_path: 知识库存储路径
            config: 配置参数
        """
        self.kb_path = kb_path
        self.config = config
        self.logger = logging.getLogger("CHS-SDK.RecommendationEngine")
        
        # 推荐数据
        self.agent_registry = {}
        self.config_templates = {}
        self.usage_history = []
        self.similarity_matrix = {}
        
        # 配置参数
        self.recommendation_threshold = config.get("recommendation_threshold", 0.7)
        self.max_recommendations = config.get("max_recommendations", 5)
        self.context_weight = config.get("context_weight", 0.6)
        self.popularity_weight = config.get("popularity_weight", 0.3)
        self.similarity_weight = config.get("similarity_weight", 0.1)
        
        # 文件路径
        self.agent_registry_file = self.kb_path / "agent_registry.json"
        self.templates_file = self.kb_path / "config_templates.json"
        self.usage_history_file = self.kb_path / "usage_history.json"
        self.recommendations_cache_file = self.kb_path / "recommendations_cache.json"
        
        self.is_initialized = False
    
    async def initialize(self) -> bool:
        """
        初始化推荐引擎
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            self.logger.info("Initializing recommendation engine...")
            
            # 加载智能体注册表
            await self._load_agent_registry()
            
            # 加载配置模板
            await self._load_config_templates()
            
            # 加载使用历史
            await self._load_usage_history()
            
            # 构建相似性矩阵
            await self._build_similarity_matrix()
            
            self.is_initialized = True
            self.logger.info("Recommendation engine initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize recommendation engine: {str(e)}")
            return False
    
    async def _load_agent_registry(self):
        """加载智能体注册表"""
        if self.agent_registry_file.exists():
            try:
                with open(self.agent_registry_file, 'r', encoding='utf-8') as f:
                    self.agent_registry = json.load(f)
                self.logger.info(f"Loaded {len(self.agent_registry)} agents from registry")
            except Exception as e:
                self.logger.warning(f"Failed to load agent registry: {str(e)}")
                self.agent_registry = {}
        else:
            # 创建默认的智能体注册表
            await self._create_default_agent_registry()
    
    async def _create_default_agent_registry(self):
        """创建默认智能体注册表"""
        default_agents = {
            "WaterUseAgent": {
                "type": "disturbance",
                "category": "water_management",
                "description": "水资源使用智能体，模拟用水需求变化",
                "required_params": ["topic", "start_time", "duration", "demand_rate"],
                "optional_params": ["disturbance_type", "target_components", "demand_patterns"],
                "use_cases": ["drought_simulation", "peak_demand_analysis", "water_allocation"],
                "tags": ["water", "demand", "disturbance"],
                "complexity": "medium",
                "popularity_score": 0.8
            },
            "FloodControlAgent": {
                "type": "control",
                "category": "flood_management",
                "description": "洪水控制智能体，实现自动化洪水防控",
                "required_params": ["agent_id", "message_bus", "control_targets"],
                "optional_params": ["control_strategy", "safety_margins", "response_time"],
                "use_cases": ["flood_prevention", "emergency_response", "dam_control"],
                "tags": ["flood", "control", "emergency"],
                "complexity": "high",
                "popularity_score": 0.9
            },
            "MonitoringAgent": {
                "type": "monitoring",
                "category": "system_monitoring",
                "description": "系统监控智能体，实时监测系统状态",
                "required_params": ["agent_id", "message_bus", "monitoring_targets"],
                "optional_params": ["alert_thresholds", "sampling_rate", "data_storage"],
                "use_cases": ["real_time_monitoring", "anomaly_detection", "performance_analysis"],
                "tags": ["monitoring", "real_time", "analysis"],
                "complexity": "low",
                "popularity_score": 0.7
            },
            "ScenarioConfigurationAgent": {
                "type": "configuration",
                "category": "scenario_management",
                "description": "情景配置智能体，动态管理仿真场景",
                "required_params": ["agent_id", "message_bus", "scenario_manager"],
                "optional_params": ["auto_switch", "validation_rules", "backup_scenarios"],
                "use_cases": ["scenario_switching", "parameter_tuning", "batch_simulation"],
                "tags": ["scenario", "configuration", "management"],
                "complexity": "medium",
                "popularity_score": 0.6
            }
        }
        
        self.agent_registry = default_agents
        await self._save_agent_registry()
    
    async def _load_config_templates(self):
        """加载配置模板"""
        if self.templates_file.exists():
            try:
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    self.config_templates = json.load(f)
                self.logger.info(f"Loaded {len(self.config_templates)} config templates")
            except Exception as e:
                self.logger.warning(f"Failed to load config templates: {str(e)}")
                self.config_templates = {}
        else:
            await self._create_default_templates()
    
    async def _create_default_templates(self):
        """创建默认配置模板"""
        default_templates = {
            "flood_control_scenario": {
                "name": "洪水控制场景",
                "description": "标准洪水控制仿真场景配置",
                "category": "flood_management",
                "agents": ["FloodControlAgent", "MonitoringAgent", "WaterUseAgent"],
                "parameters": {
                    "simulation_duration": 24,
                    "time_step": 0.1,
                    "rainfall_intensity": "high",
                    "initial_water_level": 0.7
                },
                "use_cases": ["emergency_response", "flood_prevention"],
                "complexity": "high",
                "popularity_score": 0.9
            },
            "drought_management_scenario": {
                "name": "干旱管理场景",
                "description": "干旱条件下的水资源管理场景",
                "category": "water_management",
                "agents": ["WaterUseAgent", "MonitoringAgent"],
                "parameters": {
                    "simulation_duration": 168,
                    "time_step": 1.0,
                    "water_availability": "low",
                    "demand_priority": "critical_first"
                },
                "use_cases": ["water_allocation", "drought_response"],
                "complexity": "medium",
                "popularity_score": 0.7
            },
            "normal_operation_scenario": {
                "name": "正常运行场景",
                "description": "系统正常运行状态的基础配置",
                "category": "normal_operation",
                "agents": ["MonitoringAgent"],
                "parameters": {
                    "simulation_duration": 72,
                    "time_step": 0.5,
                    "operation_mode": "normal",
                    "maintenance_schedule": "weekly"
                },
                "use_cases": ["baseline_testing", "performance_monitoring"],
                "complexity": "low",
                "popularity_score": 0.8
            }
        }
        
        self.config_templates = default_templates
        await self._save_config_templates()
    
    async def _load_usage_history(self):
        """加载使用历史"""
        if self.usage_history_file.exists():
            try:
                with open(self.usage_history_file, 'r', encoding='utf-8') as f:
                    self.usage_history = json.load(f)
                self.logger.info(f"Loaded {len(self.usage_history)} usage records")
            except Exception as e:
                self.logger.warning(f"Failed to load usage history: {str(e)}")
                self.usage_history = []
        else:
            self.usage_history = []
    
    async def _build_similarity_matrix(self):
        """构建相似性矩阵"""
        self.logger.info("Building similarity matrix...")
        
        # 智能体相似性
        agent_names = list(self.agent_registry.keys())
        for i, agent1 in enumerate(agent_names):
            for j, agent2 in enumerate(agent_names[i+1:], i+1):
                similarity = self._calculate_agent_similarity(
                    self.agent_registry[agent1],
                    self.agent_registry[agent2]
                )
                self.similarity_matrix[f"{agent1}:{agent2}"] = similarity
        
        # 模板相似性
        template_names = list(self.config_templates.keys())
        for i, template1 in enumerate(template_names):
            for j, template2 in enumerate(template_names[i+1:], i+1):
                similarity = self._calculate_template_similarity(
                    self.config_templates[template1],
                    self.config_templates[template2]
                )
                self.similarity_matrix[f"{template1}:{template2}"] = similarity
    
    def _calculate_agent_similarity(self, agent1: Dict, agent2: Dict) -> float:
        """计算智能体相似性"""
        similarity = 0.0
        
        # 类型相似性
        if agent1.get("type") == agent2.get("type"):
            similarity += 0.3
        
        # 类别相似性
        if agent1.get("category") == agent2.get("category"):
            similarity += 0.2
        
        # 标签相似性
        tags1 = set(agent1.get("tags", []))
        tags2 = set(agent2.get("tags", []))
        if tags1 and tags2:
            tag_similarity = len(tags1.intersection(tags2)) / len(tags1.union(tags2))
            similarity += tag_similarity * 0.3
        
        # 用例相似性
        use_cases1 = set(agent1.get("use_cases", []))
        use_cases2 = set(agent2.get("use_cases", []))
        if use_cases1 and use_cases2:
            use_case_similarity = len(use_cases1.intersection(use_cases2)) / len(use_cases1.union(use_cases2))
            similarity += use_case_similarity * 0.2
        
        return min(similarity, 1.0)
    
    def _calculate_template_similarity(self, template1: Dict, template2: Dict) -> float:
        """计算模板相似性"""
        similarity = 0.0
        
        # 类别相似性
        if template1.get("category") == template2.get("category"):
            similarity += 0.4
        
        # 智能体重叠度
        agents1 = set(template1.get("agents", []))
        agents2 = set(template2.get("agents", []))
        if agents1 and agents2:
            agent_similarity = len(agents1.intersection(agents2)) / len(agents1.union(agents2))
            similarity += agent_similarity * 0.4
        
        # 用例相似性
        use_cases1 = set(template1.get("use_cases", []))
        use_cases2 = set(template2.get("use_cases", []))
        if use_cases1 and use_cases2:
            use_case_similarity = len(use_cases1.intersection(use_cases2)) / len(use_cases1.union(use_cases2))
            similarity += use_case_similarity * 0.2
        
        return min(similarity, 1.0)
    
    async def get_recommendations(self, 
                                 context: Dict[str, Any],
                                 recommendation_type: str = "agent") -> List[Dict[str, Any]]:
        """
        获取智能推荐
        
        Args:
            context: 当前开发上下文
            recommendation_type: 推荐类型 (agent, config, template)
            
        Returns:
            List[Dict]: 推荐结果列表
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            if recommendation_type == "agent":
                return await self._recommend_agents(context)
            elif recommendation_type == "config":
                return await self._recommend_configs(context)
            elif recommendation_type == "template":
                return await self._recommend_templates(context)
            else:
                raise ValueError(f"Unsupported recommendation type: {recommendation_type}")
                
        except Exception as e:
            self.logger.error(f"Recommendation failed: {str(e)}")
            return []
    
    async def _recommend_agents(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """推荐智能体"""
        recommendations = []
        
        # 提取上下文信息
        current_scenario = context.get("scenario", "")
        current_agents = context.get("current_agents", [])
        project_type = context.get("project_type", "")
        keywords = context.get("keywords", [])
        
        for agent_name, agent_info in self.agent_registry.items():
            if agent_name in current_agents:
                continue  # 跳过已使用的智能体
            
            score = self._calculate_agent_recommendation_score(
                agent_info, current_scenario, project_type, keywords, current_agents
            )
            
            if score >= self.recommendation_threshold:
                recommendation = {
                    "name": agent_name,
                    "type": "agent",
                    "score": score,
                    "reason": self._generate_recommendation_reason(agent_info, context),
                    "metadata": agent_info,
                    "suggested_params": self._suggest_agent_params(agent_info, context)
                }
                recommendations.append(recommendation)
        
        # 按分数排序
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:self.max_recommendations]
    
    async def _recommend_templates(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """推荐配置模板"""
        recommendations = []
        
        # 提取上下文信息
        current_scenario = context.get("scenario", "")
        project_type = context.get("project_type", "")
        keywords = context.get("keywords", [])
        required_agents = context.get("required_agents", [])
        
        for template_name, template_info in self.config_templates.items():
            score = self._calculate_template_recommendation_score(
                template_info, current_scenario, project_type, keywords, required_agents
            )
            
            if score >= self.recommendation_threshold:
                recommendation = {
                    "name": template_name,
                    "type": "template",
                    "score": score,
                    "reason": self._generate_template_recommendation_reason(template_info, context),
                    "metadata": template_info,
                    "customization_suggestions": self._suggest_template_customizations(template_info, context)
                }
                recommendations.append(recommendation)
        
        # 按分数排序
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:self.max_recommendations]
    
    async def _recommend_configs(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """推荐配置参数"""
        # 基于当前智能体和场景推荐最佳配置参数
        recommendations = []
        
        current_agents = context.get("current_agents", [])
        scenario_type = context.get("scenario_type", "")
        
        for agent_name in current_agents:
            if agent_name in self.agent_registry:
                agent_info = self.agent_registry[agent_name]
                config_suggestions = self._generate_config_suggestions(agent_info, context)
                
                if config_suggestions:
                    recommendation = {
                        "name": f"{agent_name}_config",
                        "type": "config",
                        "score": 0.8,  # 基础分数
                        "reason": f"基于{scenario_type}场景的{agent_name}最佳配置建议",
                        "metadata": {
                            "agent_name": agent_name,
                            "scenario_type": scenario_type
                        },
                        "config_suggestions": config_suggestions
                    }
                    recommendations.append(recommendation)
        
        return recommendations
    
    def _calculate_agent_recommendation_score(self, 
                                            agent_info: Dict[str, Any],
                                            scenario: str,
                                            project_type: str,
                                            keywords: List[str],
                                            current_agents: List[str]) -> float:
        """计算智能体推荐分数"""
        score = 0.0
        
        # 上下文匹配分数
        context_score = 0.0
        
        # 场景匹配
        use_cases = agent_info.get("use_cases", [])
        for use_case in use_cases:
            if scenario and use_case.lower() in scenario.lower():
                context_score += 0.3
                break
        
        # 项目类型匹配
        category = agent_info.get("category", "")
        if project_type and category.lower() in project_type.lower():
            context_score += 0.2
        
        # 关键词匹配
        agent_tags = agent_info.get("tags", [])
        keyword_matches = sum(1 for keyword in keywords if any(keyword.lower() in tag.lower() for tag in agent_tags))
        if keywords:
            context_score += (keyword_matches / len(keywords)) * 0.3
        
        # 智能体协同性
        synergy_score = 0.0
        for current_agent in current_agents:
            similarity_key = f"{current_agent}:{agent_info.get('name', '')}"
            reverse_key = f"{agent_info.get('name', '')}:{current_agent}"
            
            if similarity_key in self.similarity_matrix:
                synergy_score += self.similarity_matrix[similarity_key]
            elif reverse_key in self.similarity_matrix:
                synergy_score += self.similarity_matrix[reverse_key]
        
        if current_agents:
            synergy_score /= len(current_agents)
        
        # 流行度分数
        popularity_score = agent_info.get("popularity_score", 0.5)
        
        # 综合分数
        score = (context_score * self.context_weight + 
                synergy_score * self.similarity_weight + 
                popularity_score * self.popularity_weight)
        
        return min(score, 1.0)
    
    def _calculate_template_recommendation_score(self,
                                               template_info: Dict[str, Any],
                                               scenario: str,
                                               project_type: str,
                                               keywords: List[str],
                                               required_agents: List[str]) -> float:
        """计算模板推荐分数"""
        score = 0.0
        
        # 上下文匹配
        context_score = 0.0
        
        # 场景匹配
        use_cases = template_info.get("use_cases", [])
        for use_case in use_cases:
            if scenario and use_case.lower() in scenario.lower():
                context_score += 0.4
                break
        
        # 项目类型匹配
        category = template_info.get("category", "")
        if project_type and category.lower() in project_type.lower():
            context_score += 0.3
        
        # 智能体需求匹配
        template_agents = set(template_info.get("agents", []))
        required_agents_set = set(required_agents)
        if required_agents_set:
            agent_match_score = len(template_agents.intersection(required_agents_set)) / len(required_agents_set)
            context_score += agent_match_score * 0.3
        
        # 流行度分数
        popularity_score = template_info.get("popularity_score", 0.5)
        
        # 综合分数
        score = (context_score * self.context_weight + 
                popularity_score * self.popularity_weight)
        
        return min(score, 1.0)
    
    def _generate_recommendation_reason(self, agent_info: Dict[str, Any], context: Dict[str, Any]) -> str:
        """生成推荐理由"""
        reasons = []
        
        # 基于用例匹配
        scenario = context.get("scenario", "")
        use_cases = agent_info.get("use_cases", [])
        for use_case in use_cases:
            if scenario and use_case.lower() in scenario.lower():
                reasons.append(f"适用于{scenario}场景")
                break
        
        # 基于类别匹配
        project_type = context.get("project_type", "")
        category = agent_info.get("category", "")
        if project_type and category.lower() in project_type.lower():
            reasons.append(f"专门用于{category}类型项目")
        
        # 基于复杂度
        complexity = agent_info.get("complexity", "medium")
        reasons.append(f"复杂度{complexity}，易于集成")
        
        # 基于流行度
        popularity = agent_info.get("popularity_score", 0.5)
        if popularity > 0.8:
            reasons.append("社区广泛使用，稳定可靠")
        
        return "；".join(reasons) if reasons else "基于当前上下文的智能推荐"
    
    def _generate_template_recommendation_reason(self, template_info: Dict[str, Any], context: Dict[str, Any]) -> str:
        """生成模板推荐理由"""
        reasons = []
        
        # 基于场景匹配
        scenario = context.get("scenario", "")
        use_cases = template_info.get("use_cases", [])
        for use_case in use_cases:
            if scenario and use_case.lower() in scenario.lower():
                reasons.append(f"针对{scenario}场景优化")
                break
        
        # 基于智能体配置
        agents = template_info.get("agents", [])
        if agents:
            reasons.append(f"预配置{len(agents)}个相关智能体")
        
        # 基于复杂度
        complexity = template_info.get("complexity", "medium")
        reasons.append(f"配置复杂度{complexity}")
        
        return "；".join(reasons) if reasons else "基于当前需求的模板推荐"
    
    def _suggest_agent_params(self, agent_info: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """建议智能体参数"""
        suggestions = {}
        
        # 基于场景类型建议参数
        scenario = context.get("scenario", "").lower()
        
        if "flood" in scenario:
            if "duration" in agent_info.get("required_params", []):
                suggestions["duration"] = 24  # 24小时洪水仿真
            if "response_time" in agent_info.get("optional_params", []):
                suggestions["response_time"] = 0.5  # 快速响应
        
        elif "drought" in scenario:
            if "duration" in agent_info.get("required_params", []):
                suggestions["duration"] = 168  # 7天干旱仿真
            if "demand_rate" in agent_info.get("required_params", []):
                suggestions["demand_rate"] = 0.7  # 降低需求
        
        return suggestions
    
    def _suggest_template_customizations(self, template_info: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        """建议模板定制化"""
        suggestions = []
        
        # 基于项目特点建议定制
        project_type = context.get("project_type", "")
        
        if "real_time" in project_type.lower():
            suggestions.append("建议减小时间步长以提高实时性")
            suggestions.append("启用实时数据接口")
        
        if "large_scale" in project_type.lower():
            suggestions.append("考虑增加分布式计算配置")
            suggestions.append("优化内存使用参数")
        
        # 基于当前智能体建议
        current_agents = context.get("current_agents", [])
        template_agents = template_info.get("agents", [])
        
        missing_agents = set(current_agents) - set(template_agents)
        if missing_agents:
            suggestions.append(f"考虑添加智能体：{', '.join(missing_agents)}")
        
        return suggestions
    
    def _generate_config_suggestions(self, agent_info: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """生成配置建议"""
        suggestions = {}
        
        # 基于智能体类型和场景生成配置建议
        agent_type = agent_info.get("type", "")
        scenario_type = context.get("scenario_type", "")
        
        if agent_type == "monitoring" and "real_time" in scenario_type:
            suggestions["sampling_rate"] = 0.1  # 高频采样
            suggestions["alert_thresholds"] = {"high": 0.9, "critical": 0.95}
        
        elif agent_type == "control" and "emergency" in scenario_type:
            suggestions["response_time"] = 0.5  # 快速响应
            suggestions["safety_margins"] = {"min": 0.1, "max": 0.9}
        
        return suggestions
    
    async def record_usage(self, item_name: str, item_type: str, context: Dict[str, Any]):
        """记录使用历史"""
        usage_record = {
            "item_name": item_name,
            "item_type": item_type,
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "success": True  # 可以后续更新
        }
        
        self.usage_history.append(usage_record)
        
        # 保持历史记录在合理范围内
        if len(self.usage_history) > 1000:
            self.usage_history = self.usage_history[-1000:]
        
        await self._save_usage_history()
    
    async def _save_agent_registry(self):
        """保存智能体注册表"""
        try:
            with open(self.agent_registry_file, 'w', encoding='utf-8') as f:
                json.dump(self.agent_registry, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save agent registry: {str(e)}")
    
    async def _save_config_templates(self):
        """保存配置模板"""
        try:
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_templates, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save config templates: {str(e)}")
    
    async def _save_usage_history(self):
        """保存使用历史"""
        try:
            with open(self.usage_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.usage_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save usage history: {str(e)}")
    
    async def update_config_templates(self, templates: Optional[Dict[str, Any]] = None):
        """
        更新配置模板
        
        Args:
            templates: 新的配置模板字典，如果为None则重新扫描生成
        """
        try:
            if templates:
                self.config_templates.update(templates)
            else:
                # 重新扫描和生成配置模板
                await self._create_default_templates()
            
            # 保存更新后的模板
            await self._save_config_templates()
            
            # 重新构建相似性矩阵
            await self._build_similarity_matrix()
            
            self.logger.info("Configuration templates updated successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to update config templates: {str(e)}")
    
    async def reload_index(self):
        """重新加载推荐数据"""
        self.logger.info("Reloading recommendation data...")
        await self._load_agent_registry()
        await self._load_config_templates()
        await self._load_usage_history()
        await self._build_similarity_matrix()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取推荐引擎统计信息"""
        return {
            "is_initialized": self.is_initialized,
            "total_agents": len(self.agent_registry),
            "total_templates": len(self.config_templates),
            "usage_records": len(self.usage_history),
            "similarity_pairs": len(self.similarity_matrix),
            "recommendation_threshold": self.recommendation_threshold,
            "max_recommendations": self.max_recommendations
        }
    
    async def cleanup(self):
        """清理资源"""
        self.logger.info("Cleaning up recommendation engine...")
        
        # 保存当前状态
        await self._save_agent_registry()
        await self._save_config_templates()
        await self._save_usage_history()
        
        # 清理内存
        self.agent_registry.clear()
        self.config_templates.clear()
        self.usage_history.clear()
        self.similarity_matrix.clear()
        
        self.is_initialized = False