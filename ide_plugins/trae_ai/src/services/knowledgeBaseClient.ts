/**
 * Knowledge Base Client - 知识库客户端服务
 * 与CHS-SDK知识库API进行通信
 */

import * as vscode from 'vscode';
import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { Logger } from '../utils/logger';

/**
 * 搜索结果接口
 */
export interface SearchResult {
    title: string;
    content: string;
    doc_type: string;
    file_path?: string;
    score: number;
    metadata?: Record<string, any>;
}

/**
 * 推荐结果接口
 */
export interface RecommendationResult {
    type: 'agent' | 'template' | 'config' | 'best_practice';
    name: string;
    description: string;
    file_path?: string;
    score: number;
    reason: string;
    metadata?: Record<string, any>;
}

/**
 * 智能体信息接口
 */
export interface AgentInfo {
    name: string;
    class_name: string;
    file_path: string;
    description?: string;
    parameters?: Record<string, any>;
    dependencies?: string[];
    category?: string;
}

/**
 * 配置模板接口
 */
export interface ConfigTemplate {
    name: string;
    file_path: string;
    description?: string;
    schema?: Record<string, any>;
    example?: Record<string, any>;
    category?: string;
}

/**
 * 文档信息接口
 */
export interface DocumentInfo {
    title: string;
    file_path: string;
    content: string;
    doc_type: string;
    last_modified?: string;
    tags?: string[];
}

/**
 * 知识库统计信息接口
 */
export interface KnowledgeBaseStats {
    total_documents: number;
    total_agents: number;
    total_templates: number;
    total_configs: number;
    last_updated: string;
    index_size: number;
}

/**
 * 知识库客户端配置
 */
export interface KnowledgeBaseConfig {
    apiUrl: string;
    enabled: boolean;
    timeout?: number;
    retryAttempts?: number;
    cacheEnabled?: boolean;
}

/**
 * 知识库客户端
 */
export class KnowledgeBaseClient {
    private client: AxiosInstance;
    private logger: Logger;
    private config: KnowledgeBaseConfig;
    private cache: Map<string, any> = new Map();
    private cacheTimeout = 5 * 60 * 1000; // 5分钟缓存
    
    constructor(apiUrl: string, enabled: boolean = true) {
        this.logger = new Logger('KnowledgeBaseClient');
        this.config = {
            apiUrl,
            enabled,
            timeout: 30000,
            retryAttempts: 3,
            cacheEnabled: true
        };
        
        this.client = axios.create({
            baseURL: this.config.apiUrl,
            timeout: this.config.timeout,
            headers: {
                'Content-Type': 'application/json',
                'User-Agent': 'CHS-SDK-VSCode-Extension'
            }
        });
        
        this.setupInterceptors();
    }
    
    /**
     * 更新配置
     */
    updateConfig(newConfig: Partial<KnowledgeBaseConfig>): void {
        this.config = { ...this.config, ...newConfig };
        
        if (newConfig.apiUrl) {
            this.client.defaults.baseURL = newConfig.apiUrl;
        }
        
        if (newConfig.timeout) {
            this.client.defaults.timeout = newConfig.timeout;
        }
        
        this.logger.info('Knowledge base client config updated');
    }
    
    /**
     * 初始化知识库
     */
    async initialize(projectPath: string): Promise<void> {
        if (!this.config.enabled) {
            this.logger.info('Knowledge base client is disabled');
            return;
        }
        
        try {
            await this.client.post('/initialize', { project_path: projectPath });
            this.logger.info('Knowledge base initialized successfully');
        } catch (error) {
            this.logger.error('Failed to initialize knowledge base:', error);
            this.handleError(error);
        }
    }
    
    /**
     * 语义搜索
     */
    async search(query: string, limit: number = 10): Promise<SearchResult[]> {
        if (!this.config.enabled) {
            return [];
        }
        
        const cacheKey = `search:${query}:${limit}`;
        if (this.config.cacheEnabled && this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < this.cacheTimeout) {
                return cached.data;
            }
        }
        
        try {
            const response: AxiosResponse<SearchResult[]> = await this.client.post('/search', {
                query,
                limit
            });
            
            const results = response.data;
            
            if (this.config.cacheEnabled) {
                this.cache.set(cacheKey, {
                    data: results,
                    timestamp: Date.now()
                });
            }
            
            return results;
        } catch (error) {
            this.logger.error('Search failed:', error);
            this.handleError(error);
            return [];
        }
    }
    
    /**
     * 获取推荐
     */
    async getRecommendations(context: Record<string, any>, limit: number = 5): Promise<RecommendationResult[]> {
        if (!this.config.enabled) {
            return [];
        }
        
        try {
            const response: AxiosResponse<RecommendationResult[]> = await this.client.post('/recommendations', {
                context,
                limit
            });
            
            return response.data;
        } catch (error) {
            this.logger.error('Failed to get recommendations:', error);
            this.handleError(error);
            return [];
        }
    }
    
    /**
     * 获取智能体列表
     */
    async getAgents(): Promise<AgentInfo[]> {
        if (!this.config.enabled) {
            return [];
        }
        
        const cacheKey = 'agents';
        if (this.config.cacheEnabled && this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < this.cacheTimeout) {
                return cached.data;
            }
        }
        
        try {
            const response: AxiosResponse<AgentInfo[]> = await this.client.get('/agents');
            const agents = response.data;
            
            if (this.config.cacheEnabled) {
                this.cache.set(cacheKey, {
                    data: agents,
                    timestamp: Date.now()
                });
            }
            
            return agents;
        } catch (error) {
            this.logger.error('Failed to get agents:', error);
            this.handleError(error);
            return [];
        }
    }
    
    /**
     * 获取配置模板列表
     */
    async getConfigTemplates(): Promise<ConfigTemplate[]> {
        if (!this.config.enabled) {
            return [];
        }
        
        const cacheKey = 'config_templates';
        if (this.config.cacheEnabled && this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < this.cacheTimeout) {
                return cached.data;
            }
        }
        
        try {
            const response: AxiosResponse<ConfigTemplate[]> = await this.client.get('/config-templates');
            const templates = response.data;
            
            if (this.config.cacheEnabled) {
                this.cache.set(cacheKey, {
                    data: templates,
                    timestamp: Date.now()
                });
            }
            
            return templates;
        } catch (error) {
            this.logger.error('Failed to get config templates:', error);
            this.handleError(error);
            return [];
        }
    }
    
    /**
     * 获取文档列表
     */
    async getDocuments(): Promise<DocumentInfo[]> {
        if (!this.config.enabled) {
            return [];
        }
        
        try {
            const response: AxiosResponse<DocumentInfo[]> = await this.client.get('/documents');
            return response.data;
        } catch (error) {
            this.logger.error('Failed to get documents:', error);
            this.handleError(error);
            return [];
        }
    }
    
    /**
     * 更新索引
     */
    async updateIndex(): Promise<void> {
        if (!this.config.enabled) {
            return;
        }
        
        try {
            await this.client.post('/update-index');
            this.clearCache();
            this.logger.info('Knowledge base index updated');
        } catch (error) {
            this.logger.error('Failed to update index:', error);
            this.handleError(error);
        }
    }
    
    /**
     * 重建索引
     */
    async rebuildIndex(): Promise<void> {
        if (!this.config.enabled) {
            return;
        }
        
        try {
            await this.client.post('/rebuild-index');
            this.clearCache();
            this.logger.info('Knowledge base index rebuilt');
        } catch (error) {
            this.logger.error('Failed to rebuild index:', error);
            this.handleError(error);
        }
    }
    
    /**
     * 获取统计信息
     */
    async getStats(): Promise<KnowledgeBaseStats | null> {
        if (!this.config.enabled) {
            return null;
        }
        
        try {
            const response: AxiosResponse<KnowledgeBaseStats> = await this.client.get('/stats');
            return response.data;
        } catch (error) {
            this.logger.error('Failed to get stats:', error);
            this.handleError(error);
            return null;
        }
    }
    
    /**
     * 检查服务状态
     */
    async checkHealth(): Promise<boolean> {
        if (!this.config.enabled) {
            return false;
        }
        
        try {
            const response = await this.client.get('/health');
            return response.status === 200;
        } catch (error) {
            this.logger.warn('Knowledge base service is not available');
            return false;
        }
    }
    
    /**
     * 设置拦截器
     */
    private setupInterceptors(): void {
        // 请求拦截器
        this.client.interceptors.request.use(
            (config) => {
                this.logger.debug(`Making request to ${config.url}`);
                return config;
            },
            (error) => {
                this.logger.error('Request error:', error);
                return Promise.reject(error);
            }
        );
        
        // 响应拦截器
        this.client.interceptors.response.use(
            (response) => {
                this.logger.debug(`Response from ${response.config.url}: ${response.status}`);
                return response;
            },
            (error) => {
                this.logger.error('Response error:', error);
                return Promise.reject(error);
            }
        );
    }
    
    /**
     * 处理错误
     */
    private handleError(error: any): void {
        if (axios.isAxiosError(error)) {
            if (error.code === 'ECONNREFUSED') {
                vscode.window.showWarningMessage(
                    'Knowledge base service is not running. Some features may be limited.',
                    'Start Service'
                ).then(selection => {
                    if (selection === 'Start Service') {
                        vscode.commands.executeCommand('chs-sdk.startKnowledgeBaseService');
                    }
                });
            } else if (error.response?.status === 404) {
                this.logger.warn('Knowledge base endpoint not found');
            } else if (error.response?.status >= 500) {
                vscode.window.showErrorMessage('Knowledge base service error. Please try again later.');
            }
        }
    }
    
    /**
     * 清除缓存
     */
    private clearCache(): void {
        this.cache.clear();
        this.logger.debug('Cache cleared');
    }
    
    /**
     * 销毁客户端
     */
    dispose(): void {
        this.clearCache();
        this.logger.info('Knowledge base client disposed');
    }
}