/**
 * Agent Creator - 智能体创建器
 * 提供智能体的快速创建和配置功能
 */

import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { TemplateManager } from '../services/templateManager';
import { KnowledgeBaseClient } from '../services/knowledgeBaseClient';
import { Logger } from '../utils/logger';

/**
 * 智能体类型
 */
export enum AgentType {
    Control = 'control',
    Monitoring = 'monitoring',
    Analysis = 'analysis',
    Communication = 'communication',
    Scenario = 'scenario',
    Custom = 'custom'
}

/**
 * 智能体配置接口
 */
export interface AgentConfig {
    name: string;
    type: AgentType;
    description: string;
    className: string;
    baseClass: string;
    parameters: Record<string, any>;
    dependencies: string[];
    category: string;
    filePath: string;
}

/**
 * 智能体模板接口
 */
export interface AgentTemplate {
    name: string;
    type: AgentType;
    description: string;
    baseClass: string;
    defaultParameters: Record<string, any>;
    requiredDependencies: string[];
    templateContent: string;
}

/**
 * 智能体创建器
 */
export class AgentCreator {
    private logger: Logger;
    private workspaceRoot: string | undefined;
    
    constructor(
        private templateManager: TemplateManager,
        private knowledgeBaseClient: KnowledgeBaseClient
    ) {
        this.logger = new Logger('AgentCreator');
        this.workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    }
    
    /**
     * 创建智能体
     */
    async createAgent(): Promise<void> {
        if (!this.workspaceRoot) {
            vscode.window.showErrorMessage('No workspace folder open');
            return;
        }
        
        try {
            // 步骤1: 选择智能体类型
            const agentType = await this.selectAgentType();
            if (!agentType) {
                return;
            }
            
            // 步骤2: 获取智能体基本信息
            const basicInfo = await this.getBasicInfo(agentType);
            if (!basicInfo) {
                return;
            }
            
            // 步骤3: 选择模板或创建自定义智能体
            const template = await this.selectTemplate(agentType);
            if (!template) {
                return;
            }
            
            // 步骤4: 配置参数
            const parameters = await this.configureParameters(template);
            if (!parameters) {
                return;
            }
            
            // 步骤5: 选择目标目录
            const targetDir = await this.selectTargetDirectory();
            if (!targetDir) {
                return;
            }
            
            // 步骤6: 生成智能体代码
            const agentConfig: AgentConfig = {
                ...basicInfo,
                type: agentType,
                baseClass: template.baseClass,
                parameters,
                dependencies: template.requiredDependencies,
                filePath: path.join(targetDir, `${basicInfo.name.toLowerCase()}_agent.py`)
            };
            
            await this.generateAgentCode(agentConfig, template);
            
            // 步骤7: 更新知识库索引
            await this.knowledgeBaseClient.updateIndex();
            
            vscode.window.showInformationMessage(
                `Agent '${agentConfig.name}' created successfully!`,
                'Open File'
            ).then(selection => {
                if (selection === 'Open File') {
                    vscode.window.showTextDocument(vscode.Uri.file(agentConfig.filePath));
                }
            });
            
        } catch (error) {
            this.logger.error('Failed to create agent:', error);
            vscode.window.showErrorMessage(`Failed to create agent: ${error}`);
        }
    }
    
    /**
     * 选择智能体类型
     */
    private async selectAgentType(): Promise<AgentType | undefined> {
        const items = [
            {
                label: '$(gear) Control Agent',
                description: 'Controls system components and processes',
                detail: 'Manages pumps, valves, gates, and other control devices',
                type: AgentType.Control
            },
            {
                label: '$(eye) Monitoring Agent',
                description: 'Monitors system status and performance',
                detail: 'Tracks sensors, alarms, and system health indicators',
                type: AgentType.Monitoring
            },
            {
                label: '$(graph) Analysis Agent',
                description: 'Analyzes data and provides insights',
                detail: 'Performs calculations, predictions, and data analysis',
                type: AgentType.Analysis
            },
            {
                label: '$(radio-tower) Communication Agent',
                description: 'Handles inter-agent communication',
                detail: 'Manages message routing, protocols, and coordination',
                type: AgentType.Communication
            },
            {
                label: '$(play) Scenario Agent',
                description: 'Manages simulation scenarios',
                detail: 'Controls scenario execution and event management',
                type: AgentType.Scenario
            },
            {
                label: '$(tools) Custom Agent',
                description: 'Create a custom agent from scratch',
                detail: 'Define your own agent behavior and functionality',
                type: AgentType.Custom
            }
        ];
        
        const selected = await vscode.window.showQuickPick(items, {
            placeHolder: 'Select the type of agent to create',
            ignoreFocusOut: true
        });
        
        return selected?.type;
    }
    
    /**
     * 获取智能体基本信息
     */
    private async getBasicInfo(agentType: AgentType): Promise<{ name: string; description: string; className: string; category: string } | undefined> {
        // 获取智能体名称
        const name = await vscode.window.showInputBox({
            prompt: 'Enter the agent name',
            placeHolder: 'e.g., WaterLevelController',
            validateInput: (value) => {
                if (!value || value.trim().length === 0) {
                    return 'Agent name is required';
                }
                if (!/^[A-Za-z][A-Za-z0-9_]*$/.test(value)) {
                    return 'Agent name must be a valid identifier';
                }
                return null;
            },
            ignoreFocusOut: true
        });
        
        if (!name) {
            return undefined;
        }
        
        // 获取智能体描述
        const description = await vscode.window.showInputBox({
            prompt: 'Enter the agent description',
            placeHolder: 'e.g., Controls water level in reservoirs',
            ignoreFocusOut: true
        });
        
        if (!description) {
            return undefined;
        }
        
        // 生成类名
        const className = this.generateClassName(name);
        
        // 确定分类
        const category = this.getAgentCategory(agentType);
        
        return { name, description, className, category };
    }
    
    /**
     * 选择模板
     */
    private async selectTemplate(agentType: AgentType): Promise<AgentTemplate | undefined> {
        // 获取可用模板
        const templates = await this.getAvailableTemplates(agentType);
        
        if (templates.length === 0) {
            vscode.window.showWarningMessage('No templates available for this agent type');
            return this.createDefaultTemplate(agentType);
        }
        
        const items = templates.map(template => ({
            label: template.name,
            description: template.description,
            detail: `Base class: ${template.baseClass}`,
            template
        }));
        
        // 添加自定义选项
        items.push({
            label: '$(add) Create Custom Template',
            description: 'Create a custom agent template',
            detail: 'Define your own agent structure and behavior',
            template: await this.createDefaultTemplate(agentType)
        });
        
        const selected = await vscode.window.showQuickPick(items, {
            placeHolder: 'Select an agent template',
            ignoreFocusOut: true
        });
        
        return selected?.template;
    }
    
    /**
     * 配置参数
     */
    private async configureParameters(template: AgentTemplate): Promise<Record<string, any> | undefined> {
        const parameters = { ...template.defaultParameters };
        
        // 如果有默认参数，让用户配置
        if (Object.keys(parameters).length > 0) {
            const shouldConfigure = await vscode.window.showQuickPick(
                ['Use default parameters', 'Configure parameters'],
                {
                    placeHolder: 'Do you want to configure agent parameters?',
                    ignoreFocusOut: true
                }
            );
            
            if (shouldConfigure === 'Configure parameters') {
                for (const [key, defaultValue] of Object.entries(parameters)) {
                    const value = await vscode.window.showInputBox({
                        prompt: `Enter value for parameter '${key}'`,
                        value: String(defaultValue),
                        ignoreFocusOut: true
                    });
                    
                    if (value !== undefined) {
                        // 尝试解析为适当的类型
                        parameters[key] = this.parseParameterValue(value, defaultValue);
                    }
                }
            }
        }
        
        return parameters;
    }
    
    /**
     * 选择目标目录
     */
    private async selectTargetDirectory(): Promise<string | undefined> {
        const coreLibPath = path.join(this.workspaceRoot!, 'core_lib');
        
        // 获取core_lib下的目录
        const directories = this.getDirectories(coreLibPath);
        
        const items = directories.map(dir => ({
            label: dir,
            description: `core_lib/${dir}`,
            path: path.join(coreLibPath, dir)
        }));
        
        // 添加创建新目录选项
        items.push({
            label: '$(add) Create New Directory',
            description: 'Create a new directory in core_lib',
            path: ''
        });
        
        const selected = await vscode.window.showQuickPick(items, {
            placeHolder: 'Select target directory for the agent',
            ignoreFocusOut: true
        });
        
        if (!selected) {
            return undefined;
        }
        
        if (selected.path === '') {
            // 创建新目录
            const dirName = await vscode.window.showInputBox({
                prompt: 'Enter new directory name',
                placeHolder: 'e.g., water_control',
                validateInput: (value) => {
                    if (!value || value.trim().length === 0) {
                        return 'Directory name is required';
                    }
                    if (!/^[a-z][a-z0-9_]*$/.test(value)) {
                        return 'Directory name must be lowercase with underscores';
                    }
                    return null;
                },
                ignoreFocusOut: true
            });
            
            if (!dirName) {
                return undefined;
            }
            
            const newDirPath = path.join(coreLibPath, dirName);
            if (!fs.existsSync(newDirPath)) {
                fs.mkdirSync(newDirPath, { recursive: true });
                
                // 创建__init__.py文件
                const initFilePath = path.join(newDirPath, '__init__.py');
                fs.writeFileSync(initFilePath, `"""\n${dirName} module\n"""
`);
            }
            
            return newDirPath;
        }
        
        return selected.path;
    }
    
    /**
     * 生成智能体代码
     */
    private async generateAgentCode(config: AgentConfig, template: AgentTemplate): Promise<void> {
        // 替换模板中的占位符
        let code = template.templateContent;
        
        const replacements = {
            '{{AGENT_NAME}}': config.name,
            '{{CLASS_NAME}}': config.className,
            '{{DESCRIPTION}}': config.description,
            '{{BASE_CLASS}}': config.baseClass,
            '{{PARAMETERS}}': JSON.stringify(config.parameters, null, 4),
            '{{DEPENDENCIES}}': config.dependencies.map(dep => `from ${dep} import *`).join('\n'),
            '{{CATEGORY}}': config.category,
            '{{TIMESTAMP}}': new Date().toISOString()
        };
        
        for (const [placeholder, value] of Object.entries(replacements)) {
            code = code.replace(new RegExp(placeholder, 'g'), value);
        }
        
        // 确保目录存在
        const dir = path.dirname(config.filePath);
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
        
        // 写入文件
        fs.writeFileSync(config.filePath, code, 'utf8');
        
        this.logger.info(`Agent code generated: ${config.filePath}`);
    }
    
    /**
     * 获取可用模板
     */
    private async getAvailableTemplates(agentType: AgentType): Promise<AgentTemplate[]> {
        // 这里可以从模板管理器或知识库获取模板
        // 暂时返回内置模板
        return this.getBuiltinTemplates(agentType);
    }
    
    /**
     * 获取内置模板
     */
    private getBuiltinTemplates(agentType: AgentType): AgentTemplate[] {
        const templates: Record<AgentType, AgentTemplate[]> = {
            [AgentType.Control]: [
                {
                    name: 'Basic Control Agent',
                    type: AgentType.Control,
                    description: 'Basic control agent with PID controller',
                    baseClass: 'BaseAgent',
                    defaultParameters: {
                        control_interval: 1.0,
                        pid_kp: 1.0,
                        pid_ki: 0.1,
                        pid_kd: 0.01
                    },
                    requiredDependencies: ['core_lib.base.base_agent'],
                    templateContent: this.getControlAgentTemplate()
                }
            ],
            [AgentType.Monitoring]: [
                {
                    name: 'Basic Monitoring Agent',
                    type: AgentType.Monitoring,
                    description: 'Basic monitoring agent with threshold checking',
                    baseClass: 'BaseAgent',
                    defaultParameters: {
                        monitoring_interval: 5.0,
                        alert_threshold: 100.0
                    },
                    requiredDependencies: ['core_lib.base.base_agent'],
                    templateContent: this.getMonitoringAgentTemplate()
                }
            ],
            [AgentType.Analysis]: [
                {
                    name: 'Basic Analysis Agent',
                    type: AgentType.Analysis,
                    description: 'Basic analysis agent with data processing',
                    baseClass: 'BaseAgent',
                    defaultParameters: {
                        analysis_window: 60.0,
                        smoothing_factor: 0.1
                    },
                    requiredDependencies: ['core_lib.base.base_agent'],
                    templateContent: this.getAnalysisAgentTemplate()
                }
            ],
            [AgentType.Communication]: [
                {
                    name: 'Basic Communication Agent',
                    type: AgentType.Communication,
                    description: 'Basic communication agent with message handling',
                    baseClass: 'BaseAgent',
                    defaultParameters: {
                        message_timeout: 30.0,
                        retry_attempts: 3
                    },
                    requiredDependencies: ['core_lib.base.base_agent'],
                    templateContent: this.getCommunicationAgentTemplate()
                }
            ],
            [AgentType.Scenario]: [
                {
                    name: 'Basic Scenario Agent',
                    type: AgentType.Scenario,
                    description: 'Basic scenario agent with event management',
                    baseClass: 'BaseAgent',
                    defaultParameters: {
                        scenario_duration: 3600.0,
                        event_interval: 60.0
                    },
                    requiredDependencies: ['core_lib.base.base_agent'],
                    templateContent: this.getScenarioAgentTemplate()
                }
            ],
            [AgentType.Custom]: []
        };
        
        return templates[agentType] || [];
    }
    
    /**
     * 创建默认模板
     */
    private async createDefaultTemplate(agentType: AgentType): Promise<AgentTemplate> {
        return {
            name: 'Custom Agent',
            type: agentType,
            description: 'Custom agent template',
            baseClass: 'BaseAgent',
            defaultParameters: {},
            requiredDependencies: ['core_lib.base.base_agent'],
            templateContent: this.getCustomAgentTemplate()
        };
    }
    
    /**
     * 生成类名
     */
    private generateClassName(name: string): string {
        // 转换为PascalCase
        return name.split(/[_\s]+/)
            .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
            .join('') + 'Agent';
    }
    
    /**
     * 获取智能体分类
     */
    private getAgentCategory(agentType: AgentType): string {
        const categories: Record<AgentType, string> = {
            [AgentType.Control]: 'control',
            [AgentType.Monitoring]: 'monitoring',
            [AgentType.Analysis]: 'analysis',
            [AgentType.Communication]: 'communication',
            [AgentType.Scenario]: 'scenario',
            [AgentType.Custom]: 'custom'
        };
        
        return categories[agentType];
    }
    
    /**
     * 解析参数值
     */
    private parseParameterValue(value: string, defaultValue: any): any {
        if (typeof defaultValue === 'number') {
            const num = parseFloat(value);
            return isNaN(num) ? defaultValue : num;
        } else if (typeof defaultValue === 'boolean') {
            return value.toLowerCase() === 'true';
        } else {
            return value;
        }
    }
    
    /**
     * 获取目录列表
     */
    private getDirectories(dirPath: string): string[] {
        try {
            if (!fs.existsSync(dirPath)) {
                return [];
            }
            
            return fs.readdirSync(dirPath, { withFileTypes: true })
                .filter(dirent => dirent.isDirectory())
                .map(dirent => dirent.name);
        } catch (error) {
            this.logger.error(`Error reading directories from ${dirPath}:`, error);
            return [];
        }
    }
    
    // 模板内容方法
    private getControlAgentTemplate(): string {
        return `"""
{{DESCRIPTION}}
Generated on: {{TIMESTAMP}}
"""

{{DEPENDENCIES}}
import time
from typing import Dict, Any, Optional


class {{CLASS_NAME}}({{BASE_CLASS}}):
    """
    {{DESCRIPTION}}
    
    Category: {{CATEGORY}}
    """
    
    def __init__(self, agent_id: str, message_bus, **kwargs):
        super().__init__(agent_id, message_bus)
        
        # Agent parameters
        self.parameters = {{PARAMETERS}}
        
        # Control state
        self.control_active = False
        self.setpoint = 0.0
        self.current_value = 0.0
        self.error_integral = 0.0
        self.last_error = 0.0
        self.last_update = time.time()
        
        self.logger.info(f"{{CLASS_NAME}} initialized with parameters: {self.parameters}")
    
    def start(self):
        """Start the control agent"""
        super().start()
        self.control_active = True
        self.logger.info("Control agent started")
    
    def stop(self):
        """Stop the control agent"""
        self.control_active = False
        super().stop()
        self.logger.info("Control agent stopped")
    
    def update(self):
        """Main update loop"""
        if not self.control_active:
            return
        
        current_time = time.time()
        dt = current_time - self.last_update
        
        if dt >= self.parameters['control_interval']:
            self.control_step()
            self.last_update = current_time
    
    def control_step(self):
        """Execute one control step"""
        # Calculate PID control output
        error = self.setpoint - self.current_value
        
        # Proportional term
        p_term = self.parameters['pid_kp'] * error
        
        # Integral term
        self.error_integral += error * self.parameters['control_interval']
        i_term = self.parameters['pid_ki'] * self.error_integral
        
        # Derivative term
        d_term = self.parameters['pid_kd'] * (error - self.last_error) / self.parameters['control_interval']
        
        # Control output
        control_output = p_term + i_term + d_term
        
        # Apply control action
        self.apply_control(control_output)
        
        self.last_error = error
        
        # Log control action
        self.logger.debug(f"Control step: setpoint={self.setpoint}, current={self.current_value}, output={control_output}")
    
    def apply_control(self, control_output: float):
        """Apply control output to the system"""
        # TODO: Implement actual control logic
        # This is where you would send commands to actuators, valves, etc.
        pass
    
    def set_setpoint(self, setpoint: float):
        """Set the control setpoint"""
        self.setpoint = setpoint
        self.logger.info(f"Setpoint set to {setpoint}")
    
    def update_measurement(self, value: float):
        """Update the current measurement value"""
        self.current_value = value
    
    def handle_message(self, message):
        """Handle incoming messages"""
        super().handle_message(message)
        
        if message.type == 'SET_SETPOINT':
            self.set_setpoint(message.data.get('setpoint', 0.0))
        elif message.type == 'UPDATE_MEASUREMENT':
            self.update_measurement(message.data.get('value', 0.0))
        elif message.type == 'START_CONTROL':
            self.control_active = True
        elif message.type == 'STOP_CONTROL':
            self.control_active = False
`;
    }
    
    private getMonitoringAgentTemplate(): string {
        return `"""
{{DESCRIPTION}}
Generated on: {{TIMESTAMP}}
"""

{{DEPENDENCIES}}
import time
from typing import Dict, Any, List, Optional


class {{CLASS_NAME}}({{BASE_CLASS}}):
    """
    {{DESCRIPTION}}
    
    Category: {{CATEGORY}}
    """
    
    def __init__(self, agent_id: str, message_bus, **kwargs):
        super().__init__(agent_id, message_bus)
        
        # Agent parameters
        self.parameters = {{PARAMETERS}}
        
        # Monitoring state
        self.monitoring_active = False
        self.monitored_values = {}
        self.alert_conditions = {}
        self.last_check = time.time()
        
        self.logger.info(f"{{CLASS_NAME}} initialized with parameters: {self.parameters}")
    
    def start(self):
        """Start the monitoring agent"""
        super().start()
        self.monitoring_active = True
        self.logger.info("Monitoring agent started")
    
    def stop(self):
        """Stop the monitoring agent"""
        self.monitoring_active = False
        super().stop()
        self.logger.info("Monitoring agent stopped")
    
    def update(self):
        """Main update loop"""
        if not self.monitoring_active:
            return
        
        current_time = time.time()
        dt = current_time - self.last_check
        
        if dt >= self.parameters['monitoring_interval']:
            self.check_conditions()
            self.last_check = current_time
    
    def check_conditions(self):
        """Check all monitoring conditions"""
        for key, value in self.monitored_values.items():
            if key in self.alert_conditions:
                condition = self.alert_conditions[key]
                if self.evaluate_condition(value, condition):
                    self.trigger_alert(key, value, condition)
    
    def evaluate_condition(self, value: float, condition: Dict[str, Any]) -> bool:
        """Evaluate if a condition is met"""
        condition_type = condition.get('type', 'threshold')
        
        if condition_type == 'threshold':
            threshold = condition.get('threshold', self.parameters['alert_threshold'])
            operator = condition.get('operator', '>')
            
            if operator == '>':
                return value > threshold
            elif operator == '<':
                return value < threshold
            elif operator == '>=':
                return value >= threshold
            elif operator == '<=':
                return value <= threshold
            elif operator == '==':
                return value == threshold
            elif operator == '!=':
                return value != threshold
        
        return False
    
    def trigger_alert(self, key: str, value: float, condition: Dict[str, Any]):
        """Trigger an alert for a condition"""
        alert_message = {
            'type': 'ALERT',
            'source': self.agent_id,
            'timestamp': time.time(),
            'data': {
                'parameter': key,
                'value': value,
                'condition': condition,
                'severity': condition.get('severity', 'warning')
            }
        }
        
        self.send_message(alert_message)
        self.logger.warning(f"Alert triggered for {key}: {value} (condition: {condition})")
    
    def add_monitoring_parameter(self, key: str, alert_condition: Optional[Dict[str, Any]] = None):
        """Add a parameter to monitor"""
        self.monitored_values[key] = 0.0
        
        if alert_condition:
            self.alert_conditions[key] = alert_condition
        
        self.logger.info(f"Added monitoring parameter: {key}")
    
    def update_value(self, key: str, value: float):
        """Update a monitored value"""
        if key in self.monitored_values:
            self.monitored_values[key] = value
            self.logger.debug(f"Updated {key} = {value}")
    
    def handle_message(self, message):
        """Handle incoming messages"""
        super().handle_message(message)
        
        if message.type == 'UPDATE_VALUE':
            key = message.data.get('parameter')
            value = message.data.get('value')
            if key and value is not None:
                self.update_value(key, value)
        elif message.type == 'ADD_MONITORING':
            key = message.data.get('parameter')
            condition = message.data.get('condition')
            if key:
                self.add_monitoring_parameter(key, condition)
        elif message.type == 'START_MONITORING':
            self.monitoring_active = True
        elif message.type == 'STOP_MONITORING':
            self.monitoring_active = False
`;
    }
    
    private getAnalysisAgentTemplate(): string {
        return `"""
{{DESCRIPTION}}
Generated on: {{TIMESTAMP}}
"""

{{DEPENDENCIES}}
import time
import numpy as np
from typing import Dict, Any, List, Optional
from collections import deque


class {{CLASS_NAME}}({{BASE_CLASS}}):
    """
    {{DESCRIPTION}}
    
    Category: {{CATEGORY}}
    """
    
    def __init__(self, agent_id: str, message_bus, **kwargs):
        super().__init__(agent_id, message_bus)
        
        # Agent parameters
        self.parameters = {{PARAMETERS}}
        
        # Analysis state
        self.analysis_active = False
        self.data_buffer = deque(maxlen=1000)  # Store last 1000 data points
        self.analysis_results = {}
        self.last_analysis = time.time()
        
        self.logger.info(f"{{CLASS_NAME}} initialized with parameters: {self.parameters}")
    
    def start(self):
        """Start the analysis agent"""
        super().start()
        self.analysis_active = True
        self.logger.info("Analysis agent started")
    
    def stop(self):
        """Stop the analysis agent"""
        self.analysis_active = False
        super().stop()
        self.logger.info("Analysis agent stopped")
    
    def update(self):
        """Main update loop"""
        if not self.analysis_active:
            return
        
        current_time = time.time()
        dt = current_time - self.last_analysis
        
        if dt >= self.parameters['analysis_window']:
            self.perform_analysis()
            self.last_analysis = current_time
    
    def perform_analysis(self):
        """Perform data analysis"""
        if len(self.data_buffer) < 2:
            return
        
        # Convert data to numpy array for analysis
        data = np.array(list(self.data_buffer))
        
        # Basic statistical analysis
        results = {
            'mean': np.mean(data),
            'std': np.std(data),
            'min': np.min(data),
            'max': np.max(data),
            'trend': self.calculate_trend(data),
            'smoothed': self.apply_smoothing(data)
        }
        
        self.analysis_results = results
        
        # Send analysis results
        self.send_analysis_results(results)
        
        self.logger.debug(f"Analysis completed: {results}")
    
    def calculate_trend(self, data: np.ndarray) -> str:
        """Calculate data trend"""
        if len(data) < 2:
            return 'unknown'
        
        # Simple linear regression to determine trend
        x = np.arange(len(data))
        slope = np.polyfit(x, data, 1)[0]
        
        if slope > 0.1:
            return 'increasing'
        elif slope < -0.1:
            return 'decreasing'
        else:
            return 'stable'
    
    def apply_smoothing(self, data: np.ndarray) -> float:
        """Apply exponential smoothing"""
        if len(data) == 0:
            return 0.0
        
        alpha = self.parameters['smoothing_factor']
        smoothed = data[0]
        
        for value in data[1:]:
            smoothed = alpha * value + (1 - alpha) * smoothed
        
        return smoothed
    
    def add_data_point(self, value: float, timestamp: Optional[float] = None):
        """Add a data point for analysis"""
        if timestamp is None:
            timestamp = time.time()
        
        self.data_buffer.append({
            'value': value,
            'timestamp': timestamp
        })
        
        self.logger.debug(f"Added data point: {value} at {timestamp}")
    
    def send_analysis_results(self, results: Dict[str, Any]):
        """Send analysis results to other agents"""
        message = {
            'type': 'ANALYSIS_RESULTS',
            'source': self.agent_id,
            'timestamp': time.time(),
            'data': results
        }
        
        self.send_message(message)
    
    def get_latest_results(self) -> Dict[str, Any]:
        """Get the latest analysis results"""
        return self.analysis_results.copy()
    
    def handle_message(self, message):
        """Handle incoming messages"""
        super().handle_message(message)
        
        if message.type == 'DATA_POINT':
            value = message.data.get('value')
            timestamp = message.data.get('timestamp')
            if value is not None:
                self.add_data_point(value, timestamp)
        elif message.type == 'REQUEST_ANALYSIS':
            self.perform_analysis()
        elif message.type == 'START_ANALYSIS':
            self.analysis_active = True
        elif message.type == 'STOP_ANALYSIS':
            self.analysis_active = False
`;
    }
    
    private getCommunicationAgentTemplate(): string {
        return `"""
{{DESCRIPTION}}
Generated on: {{TIMESTAMP}}
"""

{{DEPENDENCIES}}
import time
import threading
from typing import Dict, Any, List, Optional, Callable
from queue import Queue, Empty


class {{CLASS_NAME}}({{BASE_CLASS}}):
    """
    {{DESCRIPTION}}
    
    Category: {{CATEGORY}}
    """
    
    def __init__(self, agent_id: str, message_bus, **kwargs):
        super().__init__(agent_id, message_bus)
        
        # Agent parameters
        self.parameters = {{PARAMETERS}}
        
        # Communication state
        self.communication_active = False
        self.message_queue = Queue()
        self.pending_messages = {}
        self.message_handlers = {}
        self.routing_table = {}
        
        # Threading
        self.worker_thread = None
        self.stop_event = threading.Event()
        
        self.logger.info(f"{{CLASS_NAME}} initialized with parameters: {self.parameters}")
    
    def start(self):
        """Start the communication agent"""
        super().start()
        self.communication_active = True
        self.stop_event.clear()
        
        # Start worker thread
        self.worker_thread = threading.Thread(target=self._worker_loop)
        self.worker_thread.start()
        
        self.logger.info("Communication agent started")
    
    def stop(self):
        """Stop the communication agent"""
        self.communication_active = False
        self.stop_event.set()
        
        # Wait for worker thread to finish
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5.0)
        
        super().stop()
        self.logger.info("Communication agent stopped")
    
    def _worker_loop(self):
        """Main worker loop for message processing"""
        while not self.stop_event.is_set():
            try:
                # Process pending messages
                self._process_pending_messages()
                
                # Process message queue
                try:
                    message = self.message_queue.get(timeout=1.0)
                    self._route_message(message)
                    self.message_queue.task_done()
                except Empty:
                    continue
                    
            except Exception as e:
                self.logger.error(f"Error in worker loop: {e}")
                time.sleep(1.0)
    
    def _process_pending_messages(self):
        """Process messages waiting for acknowledgment"""
        current_time = time.time()
        timeout = self.parameters['message_timeout']
        
        expired_messages = []
        for msg_id, msg_info in self.pending_messages.items():
            if current_time - msg_info['timestamp'] > timeout:
                expired_messages.append(msg_id)
        
        for msg_id in expired_messages:
            msg_info = self.pending_messages.pop(msg_id)
            self._handle_message_timeout(msg_info['message'])
    
    def _route_message(self, message: Dict[str, Any]):
        """Route message to appropriate destination"""
        target = message.get('target')
        
        if target in self.routing_table:
            # Route through registered handler
            handler = self.routing_table[target]
            try:
                handler(message)
            except Exception as e:
                self.logger.error(f"Error routing message to {target}: {e}")
        else:
            # Default routing through message bus
            self.send_message(message)
    
    def _handle_message_timeout(self, message: Dict[str, Any]):
        """Handle message timeout"""
        retry_count = message.get('retry_count', 0)
        max_retries = self.parameters['retry_attempts']
        
        if retry_count < max_retries:
            # Retry sending the message
            message['retry_count'] = retry_count + 1
            self.queue_message(message)
            self.logger.warning(f"Retrying message (attempt {retry_count + 1}/{max_retries})")
        else:
            # Give up on the message
            self.logger.error(f"Message failed after {max_retries} attempts: {message}")
            self._send_delivery_failure_notification(message)
    
    def queue_message(self, message: Dict[str, Any]):
        """Queue a message for sending"""
        message_id = message.get('id', f"msg_{int(time.time() * 1000)}")
        message['id'] = message_id
        message['timestamp'] = time.time()
        
        self.message_queue.put(message)
        
        # Track pending message if acknowledgment is required
        if message.get('require_ack', False):
            self.pending_messages[message_id] = {
                'message': message,
                'timestamp': time.time()
            }
    
    def register_route(self, target: str, handler: Callable):
        """Register a message route handler"""
        self.routing_table[target] = handler
        self.logger.info(f"Registered route for {target}")
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """Register a message type handler"""
        self.message_handlers[message_type] = handler
        self.logger.info(f"Registered handler for message type: {message_type}")
    
    def acknowledge_message(self, message_id: str):
        """Acknowledge receipt of a message"""
        if message_id in self.pending_messages:
            del self.pending_messages[message_id]
            self.logger.debug(f"Message acknowledged: {message_id}")
    
    def _send_delivery_failure_notification(self, message: Dict[str, Any]):
        """Send notification about delivery failure"""
        notification = {
            'type': 'DELIVERY_FAILURE',
            'source': self.agent_id,
            'timestamp': time.time(),
            'data': {
                'failed_message': message,
                'reason': 'timeout_after_retries'
            }
        }
        
        self.send_message(notification)
    
    def handle_message(self, message):
        """Handle incoming messages"""
        super().handle_message(message)
        
        message_type = message.type
        
        if message_type in self.message_handlers:
            try:
                self.message_handlers[message_type](message)
            except Exception as e:
                self.logger.error(f"Error handling message type {message_type}: {e}")
        elif message_type == 'QUEUE_MESSAGE':
            self.queue_message(message.data.get('message', {}))
        elif message_type == 'ACKNOWLEDGE':
            self.acknowledge_message(message.data.get('message_id', ''))
        elif message_type == 'REGISTER_ROUTE':
            target = message.data.get('target')
            # Note: In a real implementation, you'd need to handle handler registration differently
            self.logger.info(f"Route registration request for {target}")
`;
    }
    
    private getScenarioAgentTemplate(): string {
        return `"""
{{DESCRIPTION}}
Generated on: {{TIMESTAMP}}
"""

{{DEPENDENCIES}}
import time
import threading
from typing import Dict, Any, List, Optional
from enum import Enum


class ScenarioState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class {{CLASS_NAME}}({{BASE_CLASS}}):
    """
    {{DESCRIPTION}}
    
    Category: {{CATEGORY}}
    """
    
    def __init__(self, agent_id: str, message_bus, **kwargs):
        super().__init__(agent_id, message_bus)
        
        # Agent parameters
        self.parameters = {{PARAMETERS}}
        
        # Scenario state
        self.scenario_state = ScenarioState.IDLE
        self.scenario_events = []
        self.current_event_index = 0
        self.scenario_start_time = None
        self.scenario_duration = self.parameters['scenario_duration']
        
        # Event scheduling
        self.event_timer = None
        self.event_lock = threading.Lock()
        
        self.logger.info(f"{{CLASS_NAME}} initialized with parameters: {self.parameters}")
    
    def start(self):
        """Start the scenario agent"""
        super().start()
        self.logger.info("Scenario agent started")
    
    def stop(self):
        """Stop the scenario agent"""
        self.stop_scenario()
        super().stop()
        self.logger.info("Scenario agent stopped")
    
    def load_scenario(self, scenario_config: Dict[str, Any]):
        """Load a scenario configuration"""
        self.scenario_events = scenario_config.get('events', [])
        self.scenario_duration = scenario_config.get('duration', self.parameters['scenario_duration'])
        
        # Sort events by timestamp
        self.scenario_events.sort(key=lambda x: x.get('timestamp', 0))
        
        self.current_event_index = 0
        self.scenario_state = ScenarioState.IDLE
        
        self.logger.info(f"Loaded scenario with {len(self.scenario_events)} events")
    
    def start_scenario(self):
        """Start scenario execution"""
        if self.scenario_state != ScenarioState.IDLE:
            self.logger.warning("Cannot start scenario: not in idle state")
            return
        
        self.scenario_state = ScenarioState.RUNNING
        self.scenario_start_time = time.time()
        self.current_event_index = 0
        
        # Schedule first event
        self._schedule_next_event()
        
        self.logger.info("Scenario started")
        self._send_scenario_status()
    
    def pause_scenario(self):
        """Pause scenario execution"""
        if self.scenario_state == ScenarioState.RUNNING:
            self.scenario_state = ScenarioState.PAUSED
            
            # Cancel current event timer
            if self.event_timer:
                self.event_timer.cancel()
                self.event_timer = None
            
            self.logger.info("Scenario paused")
            self._send_scenario_status()
    
    def resume_scenario(self):
        """Resume scenario execution"""
        if self.scenario_state == ScenarioState.PAUSED:
            self.scenario_state = ScenarioState.RUNNING
            self._schedule_next_event()
            
            self.logger.info("Scenario resumed")
            self._send_scenario_status()
    
    def stop_scenario(self):
        """Stop scenario execution"""
        if self.scenario_state in [ScenarioState.RUNNING, ScenarioState.PAUSED]:
            self.scenario_state = ScenarioState.COMPLETED
            
            # Cancel current event timer
            if self.event_timer:
                self.event_timer.cancel()
                self.event_timer = None
            
            self.logger.info("Scenario stopped")
            self._send_scenario_status()
    
    def _schedule_next_event(self):
        """Schedule the next event in the scenario"""
        with self.event_lock:
            if (self.current_event_index >= len(self.scenario_events) or 
                self.scenario_state != ScenarioState.RUNNING):
                return
            
            event = self.scenario_events[self.current_event_index]
            event_time = event.get('timestamp', 0)
            
            # Calculate delay until event
            current_scenario_time = time.time() - self.scenario_start_time
            delay = max(0, event_time - current_scenario_time)
            
            # Schedule event execution
            self.event_timer = threading.Timer(delay, self._execute_event, [event])
            self.event_timer.start()
            
            self.logger.debug(f"Scheduled event {self.current_event_index} in {delay:.2f} seconds")
    
    def _execute_event(self, event: Dict[str, Any]):
        """Execute a scenario event"""
        try:
            event_type = event.get('type', 'unknown')
            event_data = event.get('data', {})
            
            self.logger.info(f"Executing event: {event_type}")
            
            # Send event message
            message = {
                'type': 'SCENARIO_EVENT',
                'source': self.agent_id,
                'timestamp': time.time(),
                'data': {
                    'event_type': event_type,
                    'event_data': event_data,
                    'scenario_time': time.time() - self.scenario_start_time
                }
            }
            
            self.send_message(message)
            
            # Move to next event
            self.current_event_index += 1
            
            # Check if scenario is complete
            if self.current_event_index >= len(self.scenario_events):
                self._complete_scenario()
            else:
                # Schedule next event
                self._schedule_next_event()
                
        except Exception as e:
            self.logger.error(f"Error executing event: {e}")
            self.scenario_state = ScenarioState.FAILED
            self._send_scenario_status()
    
    def _complete_scenario(self):
        """Complete the scenario"""
        self.scenario_state = ScenarioState.COMPLETED
        
        completion_message = {
            'type': 'SCENARIO_COMPLETED',
            'source': self.agent_id,
            'timestamp': time.time(),
            'data': {
                'duration': time.time() - self.scenario_start_time,
                'events_executed': self.current_event_index
            }
        }
        
        self.send_message(completion_message)
        self.logger.info("Scenario completed")
    
    def _send_scenario_status(self):
        """Send scenario status update"""
        status_message = {
            'type': 'SCENARIO_STATUS',
            'source': self.agent_id,
            'timestamp': time.time(),
            'data': {
                'state': self.scenario_state.value,
                'current_event': self.current_event_index,
                'total_events': len(self.scenario_events),
                'elapsed_time': time.time() - self.scenario_start_time if self.scenario_start_time else 0
            }
        }
        
        self.send_message(status_message)
    
    def get_scenario_status(self) -> Dict[str, Any]:
        """Get current scenario status"""
        return {
            'state': self.scenario_state.value,
            'current_event': self.current_event_index,
            'total_events': len(self.scenario_events),
            'elapsed_time': time.time() - self.scenario_start_time if self.scenario_start_time else 0
        }
    
    def handle_message(self, message):
        """Handle incoming messages"""
        super().handle_message(message)
        
        if message.type == 'LOAD_SCENARIO':
            scenario_config = message.data.get('scenario', {})
            self.load_scenario(scenario_config)
        elif message.type == 'START_SCENARIO':
            self.start_scenario()
        elif message.type == 'PAUSE_SCENARIO':
            self.pause_scenario()
        elif message.type == 'RESUME_SCENARIO':
            self.resume_scenario()
        elif message.type == 'STOP_SCENARIO':
            self.stop_scenario()
        elif message.type == 'GET_SCENARIO_STATUS':
            status = self.get_scenario_status()
            response = {
                'type': 'SCENARIO_STATUS_RESPONSE',
                'source': self.agent_id,
                'target': message.source,
                'timestamp': time.time(),
                'data': status
            }
            self.send_message(response)
`;
    }
    
    private getCustomAgentTemplate(): string {
        return `"""
{{DESCRIPTION}}
Generated on: {{TIMESTAMP}}
"""

{{DEPENDENCIES}}
import time
from typing import Dict, Any, Optional


class {{CLASS_NAME}}({{BASE_CLASS}}):
    """
    {{DESCRIPTION}}
    
    Category: {{CATEGORY}}
    """
    
    def __init__(self, agent_id: str, message_bus, **kwargs):
        super().__init__(agent_id, message_bus)
        
        # Agent parameters
        self.parameters = {{PARAMETERS}}
        
        # Agent state
        self.active = False
        
        self.logger.info(f"{{CLASS_NAME}} initialized with parameters: {self.parameters}")
    
    def start(self):
        """Start the agent"""
        super().start()
        self.active = True
        self.logger.info("Agent started")
    
    def stop(self):
        """Stop the agent"""
        self.active = False
        super().stop()
        self.logger.info("Agent stopped")
    
    def update(self):
        """Main update loop"""
        if not self.active:
            return
        
        # TODO: Implement your agent logic here
        pass
    
    def handle_message(self, message):
        """Handle incoming messages"""
        super().handle_message(message)
        
        # TODO: Implement message handling logic
        if message.type == 'CUSTOM_MESSAGE':
            self.logger.info(f"Received custom message: {message.data}")
`;
    }
}