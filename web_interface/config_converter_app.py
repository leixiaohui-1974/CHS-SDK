#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件与自然语言转换Web界面

这个模块提供了一个基于Flask的Web应用，用于：
1. 上传和解析配置文件
2. 生成自然语言描述
3. 从自然语言生成配置文件
4. 支持所有CHS-SDK配置文件类型
5. 提供实时预览和下载功能

作者: CHS-SDK Team
版本: 1.0.0
创建时间: 2024
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core_lib.nlp.config_to_language_converter import ConfigToLanguageConverter
from core_lib.nlp.language_to_config_converter import LanguageToConfigConverter
from core_lib.nlp.enhanced_language_to_config_converter import EnhancedLanguageToConfigConverter
from core_lib.config.unified_config_manager import ConfigType

# 创建Flask应用
app = Flask(__name__)
app.secret_key = 'chs-sdk-config-converter-secret-key'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 配置上传文件夹
UPLOAD_FOLDER = Path('uploads')
OUTPUT_FOLDER = Path('outputs')
UPLOAD_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'yml', 'yaml', 'json', 'py', 'txt', 'md'}

# 创建转换器实例
config_to_lang_converter = ConfigToLanguageConverter()
lang_to_config_converter = LanguageToConfigConverter()
enhanced_converter = EnhancedLanguageToConfigConverter()

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/config-to-language')
def config_to_language():
    """配置文件到自然语言页面"""
    return render_template('config_to_language.html')

@app.route('/language-to-config')
def language_to_config():
    """自然语言到配置文件页面"""
    return render_template('language_to_config.html')

@app.route('/api/upload-config', methods=['POST'])
def upload_config():
    """上传配置文件API"""
    try:
        if 'files' not in request.files:
            return jsonify({'error': '没有选择文件'}), 400
        
        files = request.files.getlist('files')
        if not files or all(file.filename == '' for file in files):
            return jsonify({'error': '没有选择有效文件'}), 400
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        uploaded_files = []
        
        # 保存上传的文件
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = Path(temp_dir) / filename
                file.save(str(file_path))
                uploaded_files.append(str(file_path))
        
        if not uploaded_files:
            return jsonify({'error': '没有有效的配置文件'}), 400
        
        # 确定配置路径（如果只有一个文件，使用文件路径；否则使用目录路径）
        if len(uploaded_files) == 1:
            config_path = uploaded_files[0]
        else:
            config_path = temp_dir
        
        # 转换为自然语言
        description = config_to_lang_converter.convert_config_to_language(config_path)
        
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir)
        
        return jsonify({
            'success': True,
            'description': {
                'modeling': description.modeling_description,
                'scenario': description.scenario_description,
                'query': description.query_description,
                'analysis': description.analysis_description,
                'summary': description.summary,
                'technical_details': description.technical_details
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'转换失败: {str(e)}'}), 500


@app.route('/api/convert-language-enhanced', methods=['POST'])
def convert_language_enhanced():
    """增强版自然语言转换为配置文件API"""
    try:
        data = request.get_json()
        if not data or 'description' not in data:
            return jsonify({'error': '缺少描述文本'}), 400
        
        description = data['description']
        config_type = data.get('config_type', 'universal')
        strategy = data.get('strategy', 'hybrid')  # llm, rule, hybrid
        
        # 配置类型映射
        config_type_map = {
            'traditional': ConfigType.TRADITIONAL_MULTI,
            'unified': ConfigType.UNIFIED_SINGLE,
            'universal': ConfigType.UNIVERSAL_CONFIG,
            'hardcoded': ConfigType.HARDCODED
        }
        
        if config_type not in config_type_map:
            return jsonify({'error': f'不支持的配置类型: {config_type}'}), 400
        
        if strategy not in ['llm', 'rule', 'hybrid']:
            return jsonify({'error': f'不支持的转换策略: {strategy}'}), 400
        
        target_config_type = config_type_map[config_type]
        
        # 创建临时输出目录
        temp_output_dir = tempfile.mkdtemp()
        
        # 使用增强版转换器
        result = enhanced_converter.convert_language_to_config(
            description, target_config_type, temp_output_dir, strategy
        )
        
        # 评估转换质量
        quality_metrics = enhanced_converter.evaluate_conversion_quality(
            description, result.config_data
        )
        
        # 读取生成的文件
        generated_files = {}
        for file_path in Path(temp_output_dir).rglob('*'):
            if file_path.is_file():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    relative_path = str(file_path.relative_to(temp_output_dir))
                    generated_files[relative_path] = content
        
        # 清理临时目录
        shutil.rmtree(temp_output_dir)
        
        return jsonify({
            'success': True,
            'files': generated_files,
            'conversion_info': {
                'strategy': result.source_method,
                'confidence_score': result.confidence_score,
                'llm_contribution': result.llm_contribution,
                'rule_contribution': result.rule_contribution,
                'validation_errors': result.validation_errors,
                'improvements': result.improvements,
                'quality_metrics': quality_metrics
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'转换失败: {str(e)}'}), 500

@app.route('/api/convert-language', methods=['POST'])
def convert_language():
    """自然语言转换为配置文件API"""
    try:
        data = request.get_json()
        if not data or 'description' not in data:
            return jsonify({'error': '缺少描述文本'}), 400
        
        description = data['description']
        config_type = data.get('config_type', 'unified')
        
        # 配置类型映射
        config_type_map = {
            'traditional': ConfigType.TRADITIONAL_MULTI,
            'unified': ConfigType.UNIFIED_SINGLE,
            'universal': ConfigType.UNIVERSAL_CONFIG,
            'hardcoded': ConfigType.HARDCODED
        }
        
        if config_type not in config_type_map:
            return jsonify({'error': f'不支持的配置类型: {config_type}'}), 400
        
        target_config_type = config_type_map[config_type]
        
        # 创建临时输出目录
        temp_output_dir = tempfile.mkdtemp()
        
        # 转换为配置文件
        config_data = lang_to_config_converter.convert_language_to_config(
            description, target_config_type, temp_output_dir
        )
        
        # 读取生成的文件
        generated_files = {}
        for file_path in Path(temp_output_dir).rglob('*'):
            if file_path.is_file():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                relative_path = file_path.relative_to(temp_output_dir)
                generated_files[str(relative_path)] = content
        
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_output_dir)
        
        return jsonify({
            'success': True,
            'config_type': config_type,
            'files': generated_files
        })
        
    except Exception as e:
        return jsonify({'error': f'转换失败: {str(e)}'}), 500

@app.route('/api/download-config', methods=['POST'])
def download_config():
    """下载生成的配置文件API"""
    try:
        data = request.get_json()
        if not data or 'files' not in data:
            return jsonify({'error': '没有文件数据'}), 400
        
        files_data = data['files']
        config_type = data.get('config_type', 'unified')
        
        # 创建临时zip文件
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        
        with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for filename, content in files_data.items():
                zipf.writestr(filename, content)
        
        # 生成下载文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        download_filename = f'chs_sdk_config_{config_type}_{timestamp}.zip'
        
        return send_file(
            temp_zip.name,
            as_attachment=True,
            download_name=download_filename,
            mimetype='application/zip'
        )
        
    except Exception as e:
        return jsonify({'error': f'下载失败: {str(e)}'}), 500

@app.route('/api/validate-config', methods=['POST'])
def validate_config():
    """验证配置文件API"""
    try:
        data = request.get_json()
        if not data or 'files' not in data:
            return jsonify({'error': '没有文件数据'}), 400
        
        files_data = data['files']
        
        # 创建临时目录并写入文件
        temp_dir = tempfile.mkdtemp()
        
        for filename, content in files_data.items():
            file_path = Path(temp_dir) / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # 使用配置管理器验证
        config_manager = config_to_lang_converter.config_manager
        
        # 检测配置类型
        config_info = config_manager.detect_config_type(temp_dir)
        
        # 验证配置
        is_valid = config_manager.validate_config(config_info)
        
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir)
        
        return jsonify({
            'success': True,
            'valid': is_valid,
            'config_type': config_info.config_type.value if config_info.config_type else 'unknown',
            'description': config_info.description
        })
        
    except Exception as e:
        return jsonify({'error': f'验证失败: {str(e)}'}), 500

@app.route('/api/examples')
def get_examples():
    """获取示例配置文件API"""
    try:
        # 使用配置管理器获取示例
        config_manager = config_to_lang_converter.config_manager
        examples = config_manager.list_available_examples()
        
        return jsonify({
            'success': True,
            'examples': examples
        })
        
    except Exception as e:
        return jsonify({'error': f'获取示例失败: {str(e)}'}), 500

@app.route('/api/load-example', methods=['POST'])
def load_example():
    """加载示例配置文件API"""
    try:
        data = request.get_json()
        if not data or 'example_path' not in data:
            return jsonify({'error': '缺少示例路径'}), 400
        
        example_path = data['example_path']
        
        # 转换示例配置为自然语言
        description = config_to_lang_converter.convert_config_to_language(example_path)
        
        return jsonify({
            'success': True,
            'description': {
                'modeling': description.modeling_description,
                'scenario': description.scenario_description,
                'query': description.query_description,
                'analysis': description.analysis_description,
                'summary': description.summary,
                'technical_details': description.technical_details
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'加载示例失败: {str(e)}'}), 500

@app.errorhandler(413)
def too_large(e):
    """文件过大错误处理"""
    return jsonify({'error': '文件过大，请选择小于16MB的文件'}), 413

@app.errorhandler(404)
def not_found(e):
    """404错误处理"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    """500错误处理"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    # 创建模板目录
    templates_dir = Path(__file__).parent / 'templates'
    templates_dir.mkdir(exist_ok=True)
    
    # 创建静态文件目录
    static_dir = Path(__file__).parent / 'static'
    static_dir.mkdir(exist_ok=True)
    
    print("CHS-SDK配置文件转换器Web界面")
    print("访问地址: http://localhost:5000")
    print("按Ctrl+C停止服务")
    
    app.run(debug=True, host='0.0.0.0', port=5000)