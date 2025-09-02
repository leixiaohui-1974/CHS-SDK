/**
 * CHS-SDK Explorer - 资源管理器组件
 * 提供CHS-SDK项目的可视化管理界面
 */

import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { AgentCreator } from '../commands/agentCreator';
import { ScenarioCreator } from '../commands/scenarioCreator';
import { SimulationRunner } from '../services/simulationRunner';
import { KnowledgeBaseClient } from '../services/knowledgeBaseClient';
import { Logger } from '../utils/logger';

/**
 * 树节点类型
 */
export enum CHSNodeType {
    Root = 'root',
    AgentsFolder = 'agents-folder',
    ScenariosFolder = 'scenarios-folder',
    ConfigsFolder = 'configs-folder',
    Agent = 'agent',
    Scenario = 'scenario',
    Config = 'config',
    Template = 'template',
    Instance = 'instance'
}

/**
 * 树节点数据
 */
export class CHSTreeItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly nodeType: CHSNodeType,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly resourceUri?: vscode.Uri,
        public readonly parent?: CHSTreeItem
    ) {
        super(label, collapsibleState);
        
        this.tooltip = this.getTooltip();
        this.iconPath = this.getIconPath();
        this.contextValue = nodeType;
        
        if (resourceUri) {
            this.command = {
                command: 'vscode.open',
                title: 'Open',
                arguments: [resourceUri]
            };
        }
    }
    
    private getTooltip(): string {
        switch (this.nodeType) {
            case CHSNodeType.Agent:
                return `Agent: ${this.label}`;
            case CHSNodeType.Scenario:
                return `Scenario: ${this.label}`;
            case CHSNodeType.Config:
                return `Configuration: ${this.label}`;
            case CHSNodeType.Template:
                return `Template: ${this.label}`;
            case CHSNodeType.Instance:
                return `Instance: ${this.label}`;
            default:
                return this.label;
        }
    }
    
    private getIconPath(): vscode.ThemeIcon {
        switch (this.nodeType) {
            case CHSNodeType.AgentsFolder:
                return new vscode.ThemeIcon('robot');
            case CHSNodeType.ScenariosFolder:
                return new vscode.ThemeIcon('play-circle');
            case CHSNodeType.ConfigsFolder:
                return new vscode.ThemeIcon('settings-gear');
            case CHSNodeType.Agent:
                return new vscode.ThemeIcon('symbol-class');
            case CHSNodeType.Scenario:
                return new vscode.ThemeIcon('play');
            case CHSNodeType.Config:
                return new vscode.ThemeIcon('gear');
            case CHSNodeType.Template:
                return new vscode.ThemeIcon('file-code');
            case CHSNodeType.Instance:
                return new vscode.ThemeIcon('file');
            default:
                return new vscode.ThemeIcon('folder');
        }
    }
}

/**
 * CHS-SDK 资源管理器
 */
export class CHSSDKExplorer implements vscode.TreeDataProvider<CHSTreeItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<CHSTreeItem | undefined | null | void> = new vscode.EventEmitter<CHSTreeItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<CHSTreeItem | undefined | null | void> = this._onDidChangeTreeData.event;
    
    private logger: Logger;
    private workspaceRoot: string | undefined;
    
    constructor(
        private context: vscode.ExtensionContext,
        private services: {
            agentCreator: AgentCreator;
            scenarioCreator: ScenarioCreator;
            simulationRunner: SimulationRunner;
            knowledgeBaseClient: KnowledgeBaseClient;
        }
    ) {
        this.logger = new Logger('CHSSDKExplorer');
        this.workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        
        // 监听文件系统变化
        this.setupFileWatcher();
    }
    
    /**
     * 刷新树视图
     */
    refresh(): void {
        this._onDidChangeTreeData.fire();
    }
    
    /**
     * 获取树节点
     */
    getTreeItem(element: CHSTreeItem): vscode.TreeItem {
        return element;
    }
    
    /**
     * 获取子节点
     */
    getChildren(element?: CHSTreeItem): Thenable<CHSTreeItem[]> {
        if (!this.workspaceRoot) {
            vscode.window.showInformationMessage('No workspace folder open');
            return Promise.resolve([]);
        }
        
        if (!element) {
            // 根节点
            return Promise.resolve(this.getRootNodes());
        } else {
            // 子节点
            return Promise.resolve(this.getChildNodes(element));
        }
    }
    
    /**
     * 获取根节点
     */
    private getRootNodes(): CHSTreeItem[] {
        const nodes: CHSTreeItem[] = [];
        
        // 智能体文件夹
        if (this.pathExists(path.join(this.workspaceRoot!, 'core_lib'))) {
            nodes.push(new CHSTreeItem(
                'Agents',
                CHSNodeType.AgentsFolder,
                vscode.TreeItemCollapsibleState.Expanded
            ));
        }
        
        // 场景文件夹
        if (this.pathExists(path.join(this.workspaceRoot!, 'scenarios'))) {
            nodes.push(new CHSTreeItem(
                'Scenarios',
                CHSNodeType.ScenariosFolder,
                vscode.TreeItemCollapsibleState.Expanded
            ));
        }
        
        // 配置文件夹
        if (this.pathExists(path.join(this.workspaceRoot!, 'configs'))) {
            nodes.push(new CHSTreeItem(
                'Configurations',
                CHSNodeType.ConfigsFolder,
                vscode.TreeItemCollapsibleState.Collapsed
            ));
        }
        
        return nodes;
    }
    
    /**
     * 获取子节点
     */
    private getChildNodes(element: CHSTreeItem): CHSTreeItem[] {
        switch (element.nodeType) {
            case CHSNodeType.AgentsFolder:
                return this.getAgentNodes();
            case CHSNodeType.ScenariosFolder:
                return this.getScenarioNodes();
            case CHSNodeType.ConfigsFolder:
                return this.getConfigNodes();
            default:
                return [];
        }
    }
    
    /**
     * 获取智能体节点
     */
    private getAgentNodes(): CHSTreeItem[] {
        const nodes: CHSTreeItem[] = [];
        const agentsPath = path.join(this.workspaceRoot!, 'core_lib');
        
        if (!this.pathExists(agentsPath)) {
            return nodes;
        }
        
        try {
            const agentDirs = this.getDirectories(agentsPath);
            
            for (const dir of agentDirs) {
                const agentPath = path.join(agentsPath, dir);
                const pythonFiles = this.getPythonFiles(agentPath);
                
                for (const file of pythonFiles) {
                    if (file.includes('agent')) {
                        const filePath = path.join(agentPath, file);
                        const uri = vscode.Uri.file(filePath);
                        
                        nodes.push(new CHSTreeItem(
                            `${dir}/${file}`,
                            CHSNodeType.Agent,
                            vscode.TreeItemCollapsibleState.None,
                            uri
                        ));
                    }
                }
            }
        } catch (error) {
            this.logger.error('Error loading agent nodes:', error);
        }
        
        return nodes;
    }
    
    /**
     * 获取场景节点
     */
    private getScenarioNodes(): CHSTreeItem[] {
        const nodes: CHSTreeItem[] = [];
        const scenariosPath = path.join(this.workspaceRoot!, 'scenarios');
        
        if (!this.pathExists(scenariosPath)) {
            return nodes;
        }
        
        try {
            // 模板文件夹
            const templatesPath = path.join(scenariosPath, 'templates');
            if (this.pathExists(templatesPath)) {
                const templateFolder = new CHSTreeItem(
                    'Templates',
                    CHSNodeType.Template,
                    vscode.TreeItemCollapsibleState.Expanded
                );
                nodes.push(templateFolder);
                
                const templateFiles = this.getYamlFiles(templatesPath);
                for (const file of templateFiles) {
                    const filePath = path.join(templatesPath, file);
                    const uri = vscode.Uri.file(filePath);
                    
                    nodes.push(new CHSTreeItem(
                        file,
                        CHSNodeType.Template,
                        vscode.TreeItemCollapsibleState.None,
                        uri,
                        templateFolder
                    ));
                }
            }
            
            // 实例文件夹
            const instancesPath = path.join(scenariosPath, 'instances');
            if (this.pathExists(instancesPath)) {
                const instanceFolder = new CHSTreeItem(
                    'Instances',
                    CHSNodeType.Instance,
                    vscode.TreeItemCollapsibleState.Expanded
                );
                nodes.push(instanceFolder);
                
                const instanceFiles = this.getYamlFiles(instancesPath);
                for (const file of instanceFiles) {
                    const filePath = path.join(instancesPath, file);
                    const uri = vscode.Uri.file(filePath);
                    
                    nodes.push(new CHSTreeItem(
                        file,
                        CHSNodeType.Instance,
                        vscode.TreeItemCollapsibleState.None,
                        uri,
                        instanceFolder
                    ));
                }
            }
        } catch (error) {
            this.logger.error('Error loading scenario nodes:', error);
        }
        
        return nodes;
    }
    
    /**
     * 获取配置节点
     */
    private getConfigNodes(): CHSTreeItem[] {
        const nodes: CHSTreeItem[] = [];
        const configsPath = path.join(this.workspaceRoot!, 'configs');
        
        if (!this.pathExists(configsPath)) {
            return nodes;
        }
        
        try {
            const configFiles = this.getYamlFiles(configsPath);
            
            for (const file of configFiles) {
                const filePath = path.join(configsPath, file);
                const uri = vscode.Uri.file(filePath);
                
                nodes.push(new CHSTreeItem(
                    file,
                    CHSNodeType.Config,
                    vscode.TreeItemCollapsibleState.None,
                    uri
                ));
            }
        } catch (error) {
            this.logger.error('Error loading config nodes:', error);
        }
        
        return nodes;
    }
    
    /**
     * 设置文件监听器
     */
    private setupFileWatcher(): void {
        if (!this.workspaceRoot) {
            return;
        }
        
        const watcher = vscode.workspace.createFileSystemWatcher(
            new vscode.RelativePattern(this.workspaceRoot, '**/*.{py,yml,yaml}')
        );
        
        watcher.onDidCreate(() => this.refresh());
        watcher.onDidDelete(() => this.refresh());
        watcher.onDidChange(() => this.refresh());
        
        this.context.subscriptions.push(watcher);
    }
    
    /**
     * 检查路径是否存在
     */
    private pathExists(filePath: string): boolean {
        try {
            return fs.existsSync(filePath);
        } catch (error) {
            return false;
        }
    }
    
    /**
     * 获取目录列表
     */
    private getDirectories(dirPath: string): string[] {
        try {
            return fs.readdirSync(dirPath, { withFileTypes: true })
                .filter(dirent => dirent.isDirectory())
                .map(dirent => dirent.name);
        } catch (error) {
            this.logger.error(`Error reading directories from ${dirPath}:`, error);
            return [];
        }
    }
    
    /**
     * 获取Python文件列表
     */
    private getPythonFiles(dirPath: string): string[] {
        try {
            return fs.readdirSync(dirPath)
                .filter(file => file.endsWith('.py'));
        } catch (error) {
            this.logger.error(`Error reading Python files from ${dirPath}:`, error);
            return [];
        }
    }
    
    /**
     * 获取YAML文件列表
     */
    private getYamlFiles(dirPath: string): string[] {
        try {
            return fs.readdirSync(dirPath)
                .filter(file => file.endsWith('.yml') || file.endsWith('.yaml'));
        } catch (error) {
            this.logger.error(`Error reading YAML files from ${dirPath}:`, error);
            return [];
        }
    }
}