/**
 * CHS-SDK Extension for Trae AI IDE
 * 主扩展文件 - 实现核心功能和命令处理
 */

import * as vscode from 'vscode';
import { CHSSDKExplorer } from './explorer/chsExplorer';
import { KnowledgeBaseClient } from './services/knowledgeBaseClient';
import { AgentCreator } from './commands/agentCreator';
import { ScenarioCreator } from './commands/scenarioCreator';
import { ConfigurationValidator } from './services/configurationValidator';
import { SimulationRunner } from './services/simulationRunner';
import { RecommendationProvider } from './providers/recommendationProvider';
import { CompletionProvider } from './providers/completionProvider';
import { DiagnosticProvider } from './providers/diagnosticProvider';
import { StatusBarManager } from './ui/statusBarManager';
import { WelcomeManager } from './ui/welcomeManager';
import { TemplateManager } from './services/templateManager';
import { ProjectDetector } from './utils/projectDetector';
import { Logger } from './utils/logger';

/**
 * 扩展激活函数
 * @param context 扩展上下文
 */
export function activate(context: vscode.ExtensionContext) {
    const logger = new Logger('CHS-SDK Extension');
    logger.info('Activating CHS-SDK extension...');

    try {
        // 初始化核心服务
        const services = initializeServices(context);
        
        // 注册命令
        registerCommands(context, services);
        
        // 注册提供者
        registerProviders(context, services);
        
        // 初始化UI组件
        initializeUI(context, services);
        
        // 检测项目类型
        detectAndSetupProject(services);
        
        logger.info('CHS-SDK extension activated successfully');
        
        // 显示欢迎消息（如果是首次使用）
        services.welcomeManager.showWelcomeIfFirstTime();
        
    } catch (error) {
        logger.error('Failed to activate CHS-SDK extension:', error);
        vscode.window.showErrorMessage(`Failed to activate CHS-SDK extension: ${error}`);
    }
}

/**
 * 扩展停用函数
 */
export function deactivate() {
    const logger = new Logger('CHS-SDK Extension');
    logger.info('Deactivating CHS-SDK extension...');
    
    // 清理资源
    // 这里可以添加清理逻辑
}

/**
 * 初始化核心服务
 */
function initializeServices(context: vscode.ExtensionContext) {
    const config = vscode.workspace.getConfiguration('chs-sdk');
    
    // 知识库客户端
    const knowledgeBaseClient = new KnowledgeBaseClient(
        config.get('knowledgeBase.apiUrl', 'http://localhost:8080'),
        config.get('knowledgeBase.enabled', true)
    );
    
    // 配置验证器
    const configValidator = new ConfigurationValidator();
    
    // 模板管理器
    const templateManager = new TemplateManager(context);
    
    // 智能体创建器
    const agentCreator = new AgentCreator(templateManager, knowledgeBaseClient);
    
    // 场景创建器
    const scenarioCreator = new ScenarioCreator(templateManager, knowledgeBaseClient);
    
    // 仿真运行器
    const simulationRunner = new SimulationRunner();
    
    // 推荐提供者
    const recommendationProvider = new RecommendationProvider(knowledgeBaseClient);
    
    // 代码补全提供者
    const completionProvider = new CompletionProvider(knowledgeBaseClient, templateManager);
    
    // 诊断提供者
    const diagnosticProvider = new DiagnosticProvider(configValidator);
    
    // 资源管理器
    const chsExplorer = new CHSSDKExplorer(context, {
        agentCreator,
        scenarioCreator,
        simulationRunner,
        knowledgeBaseClient
    });
    
    // 状态栏管理器
    const statusBarManager = new StatusBarManager();
    
    // 欢迎管理器
    const welcomeManager = new WelcomeManager(context);
    
    // 项目检测器
    const projectDetector = new ProjectDetector();
    
    return {
        knowledgeBaseClient,
        configValidator,
        templateManager,
        agentCreator,
        scenarioCreator,
        simulationRunner,
        recommendationProvider,
        completionProvider,
        diagnosticProvider,
        chsExplorer,
        statusBarManager,
        welcomeManager,
        projectDetector
    };
}

/**
 * 注册命令
 */
function registerCommands(context: vscode.ExtensionContext, services: any) {
    const commands = [
        // 智能体相关命令
        vscode.commands.registerCommand('chs-sdk.createAgent', async () => {
            await services.agentCreator.createAgent();
        }),
        
        vscode.commands.registerCommand('chs-sdk.debugAgent', async (agentPath?: string) => {
            await services.simulationRunner.debugAgent(agentPath);
        }),
        
        // 场景相关命令
        vscode.commands.registerCommand('chs-sdk.createScenario', async () => {
            await services.scenarioCreator.createScenario();
        }),
        
        vscode.commands.registerCommand('chs-sdk.configureScenario', async (scenarioPath?: string) => {
            await services.scenarioCreator.configureScenario(scenarioPath);
        }),
        
        // 仿真相关命令
        vscode.commands.registerCommand('chs-sdk.runSimulation', async (scenarioPath?: string) => {
            await services.simulationRunner.runSimulation(scenarioPath);
        }),
        
        // 配置验证命令
        vscode.commands.registerCommand('chs-sdk.validateConfiguration', async () => {
            const activeEditor = vscode.window.activeTextEditor;
            if (activeEditor) {
                await services.configValidator.validateFile(activeEditor.document.uri);
            }
        }),
        
        // 知识库相关命令
        vscode.commands.registerCommand('chs-sdk.searchKnowledge', async () => {
            await showKnowledgeSearchDialog(services.knowledgeBaseClient);
        }),
        
        vscode.commands.registerCommand('chs-sdk.getRecommendations', async () => {
            await services.recommendationProvider.showRecommendations();
        }),
        
        // 资源管理器命令
        vscode.commands.registerCommand('chs-sdk.refreshExplorer', () => {
            services.chsExplorer.refresh();
        }),
        
        // 文档命令
        vscode.commands.registerCommand('chs-sdk.openDocumentation', () => {
            vscode.env.openExternal(vscode.Uri.parse('https://chs-sdk.readthedocs.io'));
        })
    ];
    
    // 注册所有命令
    commands.forEach(command => context.subscriptions.push(command));
}

/**
 * 注册提供者
 */
function registerProviders(context: vscode.ExtensionContext, services: any) {
    // 代码补全提供者
    const pythonCompletionProvider = vscode.languages.registerCompletionItemProvider(
        { scheme: 'file', language: 'python' },
        services.completionProvider,
        '.', '(', '"', "'"
    );
    
    const yamlCompletionProvider = vscode.languages.registerCompletionItemProvider(
        { scheme: 'file', language: 'yaml' },
        services.completionProvider,
        ':', ' ', '-'
    );
    
    // 诊断提供者
    const diagnosticCollection = vscode.languages.createDiagnosticCollection('chs-sdk');
    services.diagnosticProvider.setDiagnosticCollection(diagnosticCollection);
    
    // 文档变更监听
    const documentChangeListener = vscode.workspace.onDidChangeTextDocument(async (event) => {
        if (event.document.languageId === 'yaml' || event.document.languageId === 'python') {
            await services.diagnosticProvider.updateDiagnostics(event.document);
        }
    });
    
    // 文档保存监听
    const documentSaveListener = vscode.workspace.onDidSaveTextDocument(async (document) => {
        if (document.languageId === 'yaml' || document.languageId === 'python') {
            await services.diagnosticProvider.updateDiagnostics(document);
            
            // 如果启用了自动索引，更新知识库
            const config = vscode.workspace.getConfiguration('chs-sdk');
            if (config.get('knowledgeBase.autoIndex', true)) {
                await services.knowledgeBaseClient.updateIndex();
            }
        }
    });
    
    // 注册提供者
    context.subscriptions.push(
        pythonCompletionProvider,
        yamlCompletionProvider,
        diagnosticCollection,
        documentChangeListener,
        documentSaveListener
    );
}

/**
 * 初始化UI组件
 */
function initializeUI(context: vscode.ExtensionContext, services: any) {
    // 注册资源管理器
    vscode.window.registerTreeDataProvider('chs-sdk-explorer', services.chsExplorer);
    
    // 初始化状态栏
    services.statusBarManager.initialize();
    
    // 监听配置变更
    const configChangeListener = vscode.workspace.onDidChangeConfiguration((event) => {
        if (event.affectsConfiguration('chs-sdk')) {
            handleConfigurationChange(services);
        }
    });
    
    context.subscriptions.push(configChangeListener);
}

/**
 * 检测并设置项目
 */
async function detectAndSetupProject(services: any) {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders) {
        return;
    }
    
    for (const folder of workspaceFolders) {
        const isChsProject = await services.projectDetector.isChsProject(folder.uri);
        if (isChsProject) {
            services.statusBarManager.setProjectStatus('CHS-SDK Project Detected');
            
            // 初始化知识库
            const config = vscode.workspace.getConfiguration('chs-sdk');
            if (config.get('knowledgeBase.enabled', true)) {
                await services.knowledgeBaseClient.initialize(folder.uri.fsPath);
            }
            
            break;
        }
    }
}

/**
 * 处理配置变更
 */
function handleConfigurationChange(services: any) {
    const config = vscode.workspace.getConfiguration('chs-sdk');
    
    // 更新知识库客户端配置
    services.knowledgeBaseClient.updateConfig({
        apiUrl: config.get('knowledgeBase.apiUrl', 'http://localhost:8080'),
        enabled: config.get('knowledgeBase.enabled', true)
    });
    
    // 更新其他服务配置
    services.recommendationProvider.updateConfig({
        maxResults: config.get('recommendations.maxResults', 5),
        enabled: config.get('recommendations.enabled', true)
    });
    
    services.diagnosticProvider.updateConfig({
        enabled: config.get('validation.enabled', true),
        showWarnings: config.get('validation.showWarnings', true)
    });
}

/**
 * 显示知识库搜索对话框
 */
async function showKnowledgeSearchDialog(knowledgeBaseClient: KnowledgeBaseClient) {
    const query = await vscode.window.showInputBox({
        prompt: 'Search CHS-SDK Knowledge Base',
        placeHolder: 'Enter your search query...',
        ignoreFocusOut: true
    });
    
    if (!query) {
        return;
    }
    
    try {
        vscode.window.withProgress({
            location: vscode.ProgressLocation.Notification,
            title: 'Searching knowledge base...',
            cancellable: false
        }, async () => {
            const results = await knowledgeBaseClient.search(query);
            
            if (results.length === 0) {
                vscode.window.showInformationMessage('No results found for your query.');
                return;
            }
            
            // 显示搜索结果
            const items = results.map(result => ({
                label: result.title,
                description: result.doc_type,
                detail: result.content.substring(0, 100) + '...',
                result: result
            }));
            
            const selected = await vscode.window.showQuickPick(items, {
                placeHolder: 'Select a result to view',
                ignoreFocusOut: true
            });
            
            if (selected) {
                // 打开文件或显示内容
                if (selected.result.file_path) {
                    const uri = vscode.Uri.file(selected.result.file_path);
                    await vscode.window.showTextDocument(uri);
                } else {
                    // 在新文档中显示内容
                    const doc = await vscode.workspace.openTextDocument({
                        content: selected.result.content,
                        language: 'markdown'
                    });
                    await vscode.window.showTextDocument(doc);
                }
            }
        });
    } catch (error) {
        vscode.window.showErrorMessage(`Search failed: ${error}`);
    }
}