#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模态解析器
支持表格、图表、技术图纸等多种输入格式的信息提取
"""

import numpy as np
import pandas as pd
import cv2
import json
import logging
from typing import Dict, Any, List, Tuple, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import pytesseract
import re
from pathlib import Path
import matplotlib.pyplot as plt
from core_lib.utils import seaborn_support
from sklearn.cluster import DBSCAN
from scipy import ndimage
import xml.etree.ElementTree as ET
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class InputFormat(Enum):
    """输入格式类型"""
    TEXT = "text"
    TABLE = "table"
    IMAGE = "image"
    CHART = "chart"
    TECHNICAL_DRAWING = "technical_drawing"
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    XML = "xml"
    JSON = "json"

class ContentType(Enum):
    """内容类型"""
    COMPONENT_SPECS = "component_specs"
    PARAMETER_TABLE = "parameter_table"
    FLOW_DIAGRAM = "flow_diagram"
    SYSTEM_LAYOUT = "system_layout"
    PERFORMANCE_CHART = "performance_chart"
    TECHNICAL_SPECS = "technical_specs"
    CONFIGURATION_DATA = "configuration_data"

class ExtractionMethod(Enum):
    """提取方法"""
    OCR = "ocr"
    TEMPLATE_MATCHING = "template_matching"
    CONTOUR_DETECTION = "contour_detection"
    TEXT_ANALYSIS = "text_analysis"
    PATTERN_RECOGNITION = "pattern_recognition"
    ML_CLASSIFICATION = "ml_classification"
    HYBRID = "hybrid"

@dataclass
class ExtractionResult:
    """提取结果"""
    content_type: ContentType
    extracted_data: Dict[str, Any]
    confidence: float
    method_used: ExtractionMethod
    processing_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    raw_data: Optional[Any] = None

@dataclass
class ProcessingConfig:
    """处理配置"""
    ocr_language: str = 'chi_sim+eng'
    image_preprocessing: bool = True
    table_detection: bool = True
    chart_analysis: bool = True
    text_extraction: bool = True
    confidence_threshold: float = 0.7
    max_processing_time: float = 30.0
    output_format: str = 'structured'

class MultiModalParser:
    """
    多模态解析器
    支持表格、图表、技术图纸等多种输入格式的信息提取
    """
    
    def __init__(self, config: ProcessingConfig = None):
        self.config = config or ProcessingConfig()
        
        # 初始化OCR引擎
        self._initialize_ocr()
        
        # 初始化模板库
        self.templates = self._load_templates()
        
        # 初始化模式识别器
        self.pattern_recognizers = {
            ContentType.COMPONENT_SPECS: self._recognize_component_specs,
            ContentType.PARAMETER_TABLE: self._recognize_parameter_table,
            ContentType.FLOW_DIAGRAM: self._recognize_flow_diagram,
            ContentType.SYSTEM_LAYOUT: self._recognize_system_layout,
            ContentType.PERFORMANCE_CHART: self._recognize_performance_chart,
            ContentType.TECHNICAL_SPECS: self._recognize_technical_specs,
            ContentType.CONFIGURATION_DATA: self._recognize_configuration_data
        }
        
        # 初始化提取器
        self.extractors = {
            InputFormat.TEXT: self._extract_from_text,
            InputFormat.TABLE: self._extract_from_table,
            InputFormat.IMAGE: self._extract_from_image,
            InputFormat.CHART: self._extract_from_chart,
            InputFormat.TECHNICAL_DRAWING: self._extract_from_technical_drawing,
            InputFormat.PDF: self._extract_from_pdf,
            InputFormat.EXCEL: self._extract_from_excel,
            InputFormat.CSV: self._extract_from_csv,
            InputFormat.XML: self._extract_from_xml,
            InputFormat.JSON: self._extract_from_json
        }
        
        # 水利工程专业术语库
        self.hydraulic_terms = {
            'components': {
                '水库': ['reservoir', 'dam', '蓄水池', '水坝'],
                '泵站': ['pump station', 'pumping station', '提水站', '水泵'],
                '闸门': ['gate', 'sluice', 'valve', '阀门', '水闸'],
                '渠道': ['channel', 'canal', 'waterway', '水渠', '沟渠'],
                '管道': ['pipe', 'pipeline', 'conduit', '水管', '输水管'],
                '水塔': ['water tower', 'tank', '水箱', '蓄水塔']
            },
            'parameters': {
                '流量': ['flow rate', 'discharge', 'Q', '流速'],
                '水位': ['water level', 'elevation', 'H', '液位'],
                '压力': ['pressure', 'P', '水压', '压强'],
                '功率': ['power', 'P', '电功率', '马力'],
                '效率': ['efficiency', 'η', '效率', '效能'],
                '容量': ['capacity', 'volume', 'V', '容积']
            },
            'units': {
                '流量': ['m³/s', 'L/s', 'cms', 'cfs', '立方米每秒'],
                '水位': ['m', 'cm', 'mm', 'ft', '米'],
                '压力': ['Pa', 'kPa', 'MPa', 'bar', 'psi', '帕斯卡'],
                '功率': ['W', 'kW', 'MW', 'HP', '瓦特'],
                '容量': ['m³', 'L', 'ML', '立方米', '升']
            }
        }
        
        seaborn_support.ensure_matplotlib_style('seaborn-v0_8')
        seaborn_support.set_palette('husl')

        logger.info("多模态解析器初始化完成")
    
    def _initialize_ocr(self):
        """初始化OCR引擎"""
        try:
            # 配置tesseract
            self.ocr_config = f'--oem 3 --psm 6 -l {self.config.ocr_language}'
            
            # 测试OCR是否可用
            test_image = np.ones((100, 100, 3), dtype=np.uint8) * 255
            pytesseract.image_to_string(test_image, config=self.ocr_config)
            
            logger.info("OCR引擎初始化成功")
        except Exception as e:
            logger.warning(f"OCR引擎初始化失败: {e}")
            self.ocr_config = '--oem 3 --psm 6'
    
    def _load_templates(self) -> Dict[str, Any]:
        """加载模板库"""
        templates = {
            'table_headers': [
                ['组件', '参数', '数值', '单位'],
                ['设备', '规格', '值', '备注'],
                ['名称', '类型', '容量', '状态'],
                ['Component', 'Parameter', 'Value', 'Unit']
            ],
            'chart_patterns': {
                'line_chart': r'(时间|time).*(流量|压力|水位)',
                'bar_chart': r'(组件|设备).*(性能|效率|功率)',
                'pie_chart': r'(分配|比例|占比)'
            },
            'drawing_symbols': {
                'pump': ['⊕', '◉', 'P'],
                'valve': ['⊗', '◈', 'V'],
                'tank': ['□', '▭', 'T'],
                'pipe': ['—', '│', '┌', '┐', '└', '┘']
            }
        }
        return templates
    
    def parse(self, input_data: Union[str, bytes, np.ndarray, pd.DataFrame], 
             input_format: InputFormat = None, 
             content_type: ContentType = None) -> ExtractionResult:
        """解析多模态输入"""
        start_time = datetime.now()
        
        try:
            # 自动检测输入格式
            if input_format is None:
                input_format = self._detect_input_format(input_data)
            
            # 预处理输入数据
            processed_data = self._preprocess_input(input_data, input_format)
            
            # 自动检测内容类型
            if content_type is None:
                content_type = self._detect_content_type(processed_data, input_format)
            
            # 选择合适的提取方法
            extraction_method = self._select_extraction_method(input_format, content_type)
            
            # 执行提取
            extractor = self.extractors[input_format]
            extracted_data = extractor(processed_data, content_type, extraction_method)
            
            # 后处理和验证
            validated_data = self._validate_and_enhance(extracted_data, content_type)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 计算置信度
            confidence = self._calculate_confidence(validated_data, content_type)
            
            result = ExtractionResult(
                content_type=content_type,
                extracted_data=validated_data,
                confidence=confidence,
                method_used=extraction_method,
                processing_time=processing_time,
                metadata={
                    'input_format': input_format.value,
                    'data_size': self._get_data_size(input_data),
                    'processing_steps': self._get_processing_steps(input_format, content_type)
                },
                raw_data=processed_data if confidence < 0.9 else None
            )
            
            logger.info(f"解析完成: {content_type.value}, 置信度: {confidence:.3f}, 耗时: {processing_time:.2f}秒")
            
            return result
        
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"解析失败: {e}")
            
            return ExtractionResult(
                content_type=content_type or ContentType.CONFIGURATION_DATA,
                extracted_data={},
                confidence=0.0,
                method_used=ExtractionMethod.HYBRID,
                processing_time=processing_time,
                warnings=[f"解析失败: {str(e)}"]
            )
    
    def _detect_input_format(self, input_data: Any) -> InputFormat:
        """自动检测输入格式"""
        if isinstance(input_data, str):
            if input_data.strip().startswith('{') or input_data.strip().startswith('['):
                return InputFormat.JSON
            elif input_data.strip().startswith('<'):
                return InputFormat.XML
            elif ',' in input_data and '\n' in input_data:
                return InputFormat.CSV
            else:
                return InputFormat.TEXT
        
        elif isinstance(input_data, pd.DataFrame):
            return InputFormat.TABLE
        
        elif isinstance(input_data, np.ndarray):
            if len(input_data.shape) == 3:  # 彩色图像
                return InputFormat.IMAGE
            elif len(input_data.shape) == 2:  # 灰度图像或表格
                return InputFormat.IMAGE
        
        elif isinstance(input_data, bytes):
            # 尝试解析为图像
            try:
                Image.open(BytesIO(input_data))
                return InputFormat.IMAGE
            except:
                return InputFormat.PDF
        
        return InputFormat.TEXT
    
    def _detect_content_type(self, data: Any, input_format: InputFormat) -> ContentType:
        """自动检测内容类型"""
        if input_format == InputFormat.TABLE:
            if isinstance(data, pd.DataFrame):
                columns = [col.lower() for col in data.columns]
                if any(term in ' '.join(columns) for term in ['参数', 'parameter', '数值', 'value']):
                    return ContentType.PARAMETER_TABLE
                elif any(term in ' '.join(columns) for term in ['组件', 'component', '设备', 'equipment']):
                    return ContentType.COMPONENT_SPECS
        
        elif input_format == InputFormat.IMAGE:
            # 简化的图像内容检测
            return ContentType.TECHNICAL_SPECS
        
        elif input_format == InputFormat.TEXT:
            text = str(data).lower()
            if any(term in text for term in ['流量', 'flow', '压力', 'pressure']):
                return ContentType.PARAMETER_TABLE
            elif any(term in text for term in ['泵站', 'pump', '水库', 'reservoir']):
                return ContentType.COMPONENT_SPECS
        
        return ContentType.CONFIGURATION_DATA
    
    def _select_extraction_method(self, input_format: InputFormat, content_type: ContentType) -> ExtractionMethod:
        """选择提取方法"""
        method_matrix = {
            (InputFormat.TEXT, ContentType.PARAMETER_TABLE): ExtractionMethod.TEXT_ANALYSIS,
            (InputFormat.TABLE, ContentType.PARAMETER_TABLE): ExtractionMethod.TEXT_ANALYSIS,
            (InputFormat.IMAGE, ContentType.TECHNICAL_SPECS): ExtractionMethod.OCR,
            (InputFormat.CHART, ContentType.PERFORMANCE_CHART): ExtractionMethod.PATTERN_RECOGNITION,
            (InputFormat.TECHNICAL_DRAWING, ContentType.SYSTEM_LAYOUT): ExtractionMethod.CONTOUR_DETECTION
        }
        
        return method_matrix.get((input_format, content_type), ExtractionMethod.HYBRID)
    
    def _preprocess_input(self, input_data: Any, input_format: InputFormat) -> Any:
        """预处理输入数据"""
        if input_format == InputFormat.IMAGE and isinstance(input_data, (bytes, str)):
            # 处理图像数据
            if isinstance(input_data, str) and input_data.startswith('data:image'):
                # Base64编码的图像
                header, data = input_data.split(',', 1)
                image_data = base64.b64decode(data)
                image = Image.open(BytesIO(image_data))
                return np.array(image)
            elif isinstance(input_data, bytes):
                image = Image.open(BytesIO(input_data))
                return np.array(image)
        
        elif input_format == InputFormat.TEXT:
            # 文本预处理
            if isinstance(input_data, str):
                return input_data.strip()
        
        elif input_format == InputFormat.JSON:
            if isinstance(input_data, str):
                return json.loads(input_data)
        
        return input_data
    
    def _extract_from_text(self, data: str, content_type: ContentType, method: ExtractionMethod) -> Dict[str, Any]:
        """从文本提取信息"""
        extracted = {
            'components': [],
            'parameters': [],
            'connections': [],
            'metadata': {}
        }
        
        # 组件识别
        for comp_name, synonyms in self.hydraulic_terms['components'].items():
            pattern = '|'.join([re.escape(syn) for syn in [comp_name] + synonyms])
            matches = re.finditer(pattern, data, re.IGNORECASE)
            for match in matches:
                extracted['components'].append({
                    'name': match.group(),
                    'type': comp_name,
                    'position': match.span(),
                    'confidence': 0.9
                })
        
        # 参数提取
        for param_name, synonyms in self.hydraulic_terms['parameters'].items():
            for synonym in [param_name] + synonyms:
                # 匹配参数和数值
                pattern = rf'({re.escape(synonym)})\s*[:：=]?\s*([0-9]+\.?[0-9]*)\s*([a-zA-Z³/°%]+)?'
                matches = re.finditer(pattern, data, re.IGNORECASE)
                for match in matches:
                    value_str = match.group(2)
                    unit = match.group(3) or ''
                    
                    try:
                        value = float(value_str)
                        extracted['parameters'].append({
                            'name': param_name,
                            'value': value,
                            'unit': unit,
                            'original_text': match.group(),
                            'confidence': 0.85
                        })
                    except ValueError:
                        continue
        
        return extracted
    
    def _extract_from_table(self, data: pd.DataFrame, content_type: ContentType, method: ExtractionMethod) -> Dict[str, Any]:
        """从表格提取信息"""
        extracted = {
            'components': [],
            'parameters': [],
            'table_data': data.to_dict('records'),
            'metadata': {
                'rows': len(data),
                'columns': list(data.columns)
            }
        }
        
        # 分析表格结构
        columns = [col.lower() for col in data.columns]
        
        # 查找组件列
        component_col = None
        for col in data.columns:
            if any(term in col.lower() for term in ['组件', 'component', '设备', 'equipment', '名称', 'name']):
                component_col = col
                break
        
        # 查找参数列
        parameter_cols = []
        for col in data.columns:
            if any(term in col.lower() for term in ['参数', 'parameter', '数值', 'value', '值']):
                parameter_cols.append(col)
        
        # 提取组件信息
        if component_col:
            for idx, row in data.iterrows():
                comp_name = str(row[component_col])
                if comp_name and comp_name.lower() != 'nan':
                    # 识别组件类型
                    comp_type = self._identify_component_type(comp_name)
                    extracted['components'].append({
                        'name': comp_name,
                        'type': comp_type,
                        'row_index': idx,
                        'confidence': 0.9
                    })
        
        # 提取参数信息
        for idx, row in data.iterrows():
            for col in parameter_cols:
                value = row[col]
                if pd.notna(value):
                    # 尝试解析数值和单位
                    parsed = self._parse_parameter_value(str(value))
                    if parsed:
                        extracted['parameters'].append({
                            'name': col,
                            'value': parsed['value'],
                            'unit': parsed['unit'],
                            'row_index': idx,
                            'confidence': 0.85
                        })
        
        return extracted
    
    def _extract_from_image(self, data: np.ndarray, content_type: ContentType, method: ExtractionMethod) -> Dict[str, Any]:
        """从图像提取信息"""
        extracted = {
            'components': [],
            'parameters': [],
            'text_regions': [],
            'metadata': {
                'image_shape': data.shape,
                'processing_method': method.value
            }
        }
        
        if self.config.image_preprocessing:
            data = self._preprocess_image(data)
        
        if method == ExtractionMethod.OCR:
            # OCR文本提取
            try:
                text = pytesseract.image_to_string(data, config=self.ocr_config)
                if text.strip():
                    # 使用文本提取方法处理OCR结果
                    text_extracted = self._extract_from_text(text, content_type, ExtractionMethod.TEXT_ANALYSIS)
                    extracted.update(text_extracted)
                    extracted['text_regions'].append({
                        'text': text,
                        'confidence': 0.8
                    })
            except Exception as e:
                logger.warning(f"OCR提取失败: {e}")
        
        elif method == ExtractionMethod.CONTOUR_DETECTION:
            # 轮廓检测
            contours = self._detect_contours(data)
            for i, contour in enumerate(contours):
                extracted['components'].append({
                    'name': f'detected_component_{i}',
                    'type': 'unknown',
                    'contour': contour.tolist(),
                    'confidence': 0.6
                })
        
        elif method == ExtractionMethod.TEMPLATE_MATCHING:
            # 模板匹配
            matches = self._template_matching(data)
            extracted['components'].extend(matches)
        
        return extracted
    
    def _extract_from_chart(self, data: np.ndarray, content_type: ContentType, method: ExtractionMethod) -> Dict[str, Any]:
        """从图表提取信息"""
        # 图表分析逻辑
        return self._extract_from_image(data, content_type, method)
    
    def _extract_from_technical_drawing(self, data: np.ndarray, content_type: ContentType, method: ExtractionMethod) -> Dict[str, Any]:
        """从技术图纸提取信息"""
        extracted = self._extract_from_image(data, content_type, method)
        
        # 添加技术图纸特有的处理
        if method == ExtractionMethod.CONTOUR_DETECTION:
            # 检测管道连接
            connections = self._detect_pipe_connections(data)
            extracted['connections'] = connections
        
        return extracted
    
    def _extract_from_pdf(self, data: bytes, content_type: ContentType, method: ExtractionMethod) -> Dict[str, Any]:
        """从PDF提取信息"""
        # 简化的PDF处理
        return {'components': [], 'parameters': [], 'metadata': {'format': 'pdf'}}
    
    def _extract_from_excel(self, data: Any, content_type: ContentType, method: ExtractionMethod) -> Dict[str, Any]:
        """从Excel提取信息"""
        if isinstance(data, str):  # 文件路径
            df = pd.read_excel(data)
        else:
            df = data
        
        return self._extract_from_table(df, content_type, method)
    
    def _extract_from_csv(self, data: Any, content_type: ContentType, method: ExtractionMethod) -> Dict[str, Any]:
        """从CSV提取信息"""
        if isinstance(data, str):
            if '\n' in data:  # CSV内容
                from io import StringIO
                df = pd.read_csv(StringIO(data))
            else:  # 文件路径
                df = pd.read_csv(data)
        else:
            df = data
        
        return self._extract_from_table(df, content_type, method)
    
    def _extract_from_xml(self, data: Any, content_type: ContentType, method: ExtractionMethod) -> Dict[str, Any]:
        """从XML提取信息"""
        extracted = {
            'components': [],
            'parameters': [],
            'metadata': {}
        }
        
        try:
            if isinstance(data, str):
                root = ET.fromstring(data)
            else:
                root = data
            
            # 递归解析XML元素
            self._parse_xml_element(root, extracted)
        
        except Exception as e:
            logger.warning(f"XML解析失败: {e}")
        
        return extracted
    
    def _extract_from_json(self, data: Any, content_type: ContentType, method: ExtractionMethod) -> Dict[str, Any]:
        """从JSON提取信息"""
        extracted = {
            'components': [],
            'parameters': [],
            'metadata': {}
        }
        
        if isinstance(data, dict):
            self._parse_json_object(data, extracted)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    self._parse_json_object(item, extracted)
        
        return extracted
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """图像预处理"""
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image.copy()
        
        # 去噪
        denoised = cv2.medianBlur(gray, 3)
        
        # 增强对比度
        enhanced = cv2.equalizeHist(denoised)
        
        # 二值化
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return binary
    
    def _detect_contours(self, image: np.ndarray) -> List[np.ndarray]:
        """检测轮廓"""
        contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 过滤小轮廓
        min_area = 100
        filtered_contours = [c for c in contours if cv2.contourArea(c) > min_area]
        
        return filtered_contours
    
    def _template_matching(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """模板匹配"""
        matches = []
        
        # 简化的模板匹配实现
        # 实际应用中需要加载预定义的模板
        
        return matches
    
    def _detect_pipe_connections(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """检测管道连接"""
        connections = []
        
        # 使用霍夫变换检测直线
        edges = cv2.Canny(image, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=50, maxLineGap=10)
        
        if lines is not None:
            for i, line in enumerate(lines):
                x1, y1, x2, y2 = line[0]
                connections.append({
                    'type': 'pipe_segment',
                    'start': [int(x1), int(y1)],
                    'end': [int(x2), int(y2)],
                    'length': np.sqrt((x2-x1)**2 + (y2-y1)**2),
                    'confidence': 0.7
                })
        
        return connections
    
    def _identify_component_type(self, component_name: str) -> str:
        """识别组件类型"""
        name_lower = component_name.lower()
        
        for comp_type, synonyms in self.hydraulic_terms['components'].items():
            if any(syn.lower() in name_lower for syn in [comp_type] + synonyms):
                return comp_type
        
        return 'unknown'
    
    def _parse_parameter_value(self, value_str: str) -> Optional[Dict[str, Any]]:
        """解析参数值"""
        # 匹配数值和单位
        pattern = r'([0-9]+\.?[0-9]*)\s*([a-zA-Z³/°%]+)?'
        match = re.search(pattern, str(value_str))
        
        if match:
            try:
                value = float(match.group(1))
                unit = match.group(2) or ''
                return {'value': value, 'unit': unit}
            except ValueError:
                pass
        
        return None
    
    def _parse_xml_element(self, element: ET.Element, extracted: Dict[str, Any]):
        """解析XML元素"""
        # 检查是否是组件
        if any(term in element.tag.lower() for term in ['component', 'equipment', '组件', '设备']):
            comp_data = {'name': element.tag, 'type': 'unknown', 'confidence': 0.8}
            
            # 提取属性
            for attr, value in element.attrib.items():
                if attr.lower() in ['name', 'type', 'id']:
                    comp_data[attr] = value
            
            extracted['components'].append(comp_data)
        
        # 检查是否是参数
        if any(term in element.tag.lower() for term in ['parameter', 'value', '参数', '数值']):
            if element.text:
                parsed = self._parse_parameter_value(element.text)
                if parsed:
                    param_data = {
                        'name': element.tag,
                        'value': parsed['value'],
                        'unit': parsed['unit'],
                        'confidence': 0.8
                    }
                    extracted['parameters'].append(param_data)
        
        # 递归处理子元素
        for child in element:
            self._parse_xml_element(child, extracted)
    
    def _parse_json_object(self, obj: Dict[str, Any], extracted: Dict[str, Any]):
        """解析JSON对象"""
        for key, value in obj.items():
            key_lower = key.lower()
            
            # 检查是否是组件信息
            if any(term in key_lower for term in ['component', 'equipment', '组件', '设备']):
                if isinstance(value, dict):
                    comp_data = {'name': key, 'confidence': 0.8}
                    comp_data.update(value)
                    extracted['components'].append(comp_data)
                elif isinstance(value, str):
                    comp_type = self._identify_component_type(value)
                    extracted['components'].append({
                        'name': value,
                        'type': comp_type,
                        'confidence': 0.8
                    })
            
            # 检查是否是参数信息
            elif any(term in key_lower for term in ['parameter', 'value', '参数', '数值']):
                if isinstance(value, (int, float)):
                    extracted['parameters'].append({
                        'name': key,
                        'value': value,
                        'unit': '',
                        'confidence': 0.9
                    })
                elif isinstance(value, str):
                    parsed = self._parse_parameter_value(value)
                    if parsed:
                        extracted['parameters'].append({
                            'name': key,
                            'value': parsed['value'],
                            'unit': parsed['unit'],
                            'confidence': 0.8
                        })
            
            # 递归处理嵌套对象
            elif isinstance(value, dict):
                self._parse_json_object(value, extracted)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        self._parse_json_object(item, extracted)
    
    def _validate_and_enhance(self, data: Dict[str, Any], content_type: ContentType) -> Dict[str, Any]:
        """验证和增强提取的数据"""
        enhanced = data.copy()
        
        # 去重
        if 'components' in enhanced:
            enhanced['components'] = self._deduplicate_components(enhanced['components'])
        
        if 'parameters' in enhanced:
            enhanced['parameters'] = self._deduplicate_parameters(enhanced['parameters'])
        
        # 标准化单位
        if 'parameters' in enhanced:
            for param in enhanced['parameters']:
                if 'unit' in param:
                    param['unit'] = self._standardize_unit(param['unit'])
        
        # 增强组件类型识别
        if 'components' in enhanced:
            for comp in enhanced['components']:
                if comp.get('type') == 'unknown':
                    comp['type'] = self._identify_component_type(comp.get('name', ''))
        
        return enhanced
    
    def _deduplicate_components(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重组件"""
        seen = set()
        unique_components = []
        
        for comp in components:
            key = (comp.get('name', '').lower(), comp.get('type', ''))
            if key not in seen:
                seen.add(key)
                unique_components.append(comp)
        
        return unique_components
    
    def _deduplicate_parameters(self, parameters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重参数"""
        seen = set()
        unique_parameters = []
        
        for param in parameters:
            key = (param.get('name', '').lower(), param.get('value', 0), param.get('unit', ''))
            if key not in seen:
                seen.add(key)
                unique_parameters.append(param)
        
        return unique_parameters
    
    def _standardize_unit(self, unit: str) -> str:
        """标准化单位"""
        unit_mapping = {
            '立方米每秒': 'm³/s',
            '立方米/秒': 'm³/s',
            '升每秒': 'L/s',
            '升/秒': 'L/s',
            '米': 'm',
            '厘米': 'cm',
            '毫米': 'mm',
            '千瓦': 'kW',
            '瓦特': 'W',
            '马力': 'HP',
            '帕斯卡': 'Pa',
            '千帕': 'kPa',
            '兆帕': 'MPa'
        }
        
        return unit_mapping.get(unit, unit)
    
    def _calculate_confidence(self, data: Dict[str, Any], content_type: ContentType) -> float:
        """计算置信度"""
        scores = []
        
        # 基于提取的数据量
        total_items = len(data.get('components', [])) + len(data.get('parameters', []))
        if total_items > 0:
            scores.append(min(total_items / 10, 1.0))  # 最多10个项目得满分
        
        # 基于个别项目的置信度
        for comp in data.get('components', []):
            if 'confidence' in comp:
                scores.append(comp['confidence'])
        
        for param in data.get('parameters', []):
            if 'confidence' in param:
                scores.append(param['confidence'])
        
        # 基于内容类型匹配度
        if content_type == ContentType.PARAMETER_TABLE and data.get('parameters'):
            scores.append(0.9)
        elif content_type == ContentType.COMPONENT_SPECS and data.get('components'):
            scores.append(0.9)
        
        return np.mean(scores) if scores else 0.5
    
    def _get_data_size(self, data: Any) -> str:
        """获取数据大小信息"""
        if isinstance(data, str):
            return f"{len(data)} characters"
        elif isinstance(data, np.ndarray):
            return f"{data.shape} array"
        elif isinstance(data, pd.DataFrame):
            return f"{data.shape[0]}x{data.shape[1]} table"
        elif isinstance(data, bytes):
            return f"{len(data)} bytes"
        else:
            return "unknown"
    
    def _get_processing_steps(self, input_format: InputFormat, content_type: ContentType) -> List[str]:
        """获取处理步骤"""
        steps = ["format_detection", "content_type_detection"]
        
        if input_format == InputFormat.IMAGE:
            steps.extend(["image_preprocessing", "ocr_extraction"])
        elif input_format == InputFormat.TABLE:
            steps.extend(["table_analysis", "column_mapping"])
        elif input_format == InputFormat.TEXT:
            steps.extend(["text_parsing", "pattern_matching"])
        
        steps.extend(["data_validation", "enhancement", "confidence_calculation"])
        
        return steps
    
    # 内容识别器方法
    def _recognize_component_specs(self, data: Any) -> float:
        """识别组件规格"""
        return 0.8
    
    def _recognize_parameter_table(self, data: Any) -> float:
        """识别参数表格"""
        return 0.8
    
    def _recognize_flow_diagram(self, data: Any) -> float:
        """识别流程图"""
        return 0.7
    
    def _recognize_system_layout(self, data: Any) -> float:
        """识别系统布局"""
        return 0.7
    
    def _recognize_performance_chart(self, data: Any) -> float:
        """识别性能图表"""
        return 0.7
    
    def _recognize_technical_specs(self, data: Any) -> float:
        """识别技术规格"""
        return 0.8
    
    def _recognize_configuration_data(self, data: Any) -> float:
        """识别配置数据"""
        return 0.6
    
    def batch_parse(self, input_list: List[Tuple[Any, InputFormat, ContentType]]) -> List[ExtractionResult]:
        """批量解析"""
        results = []
        
        for input_data, input_format, content_type in input_list:
            try:
                result = self.parse(input_data, input_format, content_type)
                results.append(result)
            except Exception as e:
                logger.error(f"批量解析失败: {e}")
                results.append(ExtractionResult(
                    content_type=content_type,
                    extracted_data={},
                    confidence=0.0,
                    method_used=ExtractionMethod.HYBRID,
                    processing_time=0.0,
                    warnings=[f"解析失败: {str(e)}"]
                ))
        
        return results
    
    def export_results(self, results: List[ExtractionResult], output_file: str, format: str = 'json'):
        """导出结果"""
        if format.lower() == 'json':
            export_data = []
            for result in results:
                export_data.append({
                    'content_type': result.content_type.value,
                    'extracted_data': result.extracted_data,
                    'confidence': result.confidence,
                    'method_used': result.method_used.value,
                    'processing_time': result.processing_time,
                    'metadata': result.metadata,
                    'warnings': result.warnings
                })
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        
        elif format.lower() == 'excel':
            # 导出到Excel
            data_for_excel = []
            for result in results:
                row = {
                    'content_type': result.content_type.value,
                    'confidence': result.confidence,
                    'method_used': result.method_used.value,
                    'processing_time': result.processing_time,
                    'components_count': len(result.extracted_data.get('components', [])),
                    'parameters_count': len(result.extracted_data.get('parameters', [])),
                    'warnings': '; '.join(result.warnings)
                }
                data_for_excel.append(row)
            
            df = pd.DataFrame(data_for_excel)
            df.to_excel(output_file, index=False)
        
        logger.info(f"结果已导出到: {output_file}")

# 使用示例
if __name__ == "__main__":
    # 创建解析器
    parser = MultiModalParser()
    
    # 示例1: 解析文本
    text_input = "主水库容量为5000万立方米，1号泵站功率800kW，当前流量150m³/s"
    result1 = parser.parse(text_input, InputFormat.TEXT)
    print(f"文本解析结果: 置信度 {result1.confidence:.3f}")
    print(f"组件数量: {len(result1.extracted_data.get('components', []))}")
    print(f"参数数量: {len(result1.extracted_data.get('parameters', []))}")
    
    # 示例2: 解析表格
    table_data = pd.DataFrame({
        '组件名称': ['主水库', '1号泵站', '输水管道'],
        '类型': ['水库', '泵站', '管道'],
        '容量/功率': ['5000万m³', '800kW', 'DN1200'],
        '状态': ['正常', '运行', '正常']
    })
    result2 = parser.parse(table_data, InputFormat.TABLE)
    print(f"\n表格解析结果: 置信度 {result2.confidence:.3f}")
    
    # 示例3: 批量解析
    batch_inputs = [
        (text_input, InputFormat.TEXT, ContentType.PARAMETER_TABLE),
        (table_data, InputFormat.TABLE, ContentType.COMPONENT_SPECS)
    ]
    batch_results = parser.batch_parse(batch_inputs)
    print(f"\n批量解析完成，共处理 {len(batch_results)} 个输入")
    
    # 导出结果
    parser.export_results(batch_results, "multi_modal_results.json")
    print("结果已导出到 multi_modal_results.json")