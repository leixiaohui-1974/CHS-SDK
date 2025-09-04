#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模态解析器
支持从表格、图表、技术图纸等多种输入格式中提取信息
"""

import re
import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime

class InputFormat(Enum):
    """输入格式"""
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
    COMPONENT_SPECS = "component_specs"        # 组件规格
    PARAMETER_TABLE = "parameter_table"        # 参数表格
    FLOW_DIAGRAM = "flow_diagram"              # 流程图
    TECHNICAL_SPECS = "technical_specs"        # 技术规格
    MEASUREMENT_DATA = "measurement_data"      # 测量数据
    CONFIGURATION = "configuration"            # 配置信息

class ExtractionMethod(Enum):
    """提取方法"""
    OCR = "ocr"                               # 光学字符识别
    TEMPLATE_MATCHING = "template_matching"    # 模板匹配
    PATTERN_RECOGNITION = "pattern_recognition" # 模式识别
    STRUCTURED_PARSING = "structured_parsing"  # 结构化解析
    AI_EXTRACTION = "ai_extraction"           # AI提取

@dataclass
class ExtractionResult:
    """提取结果"""
    format_type: InputFormat
    content_type: ContentType
    extraction_method: ExtractionMethod
    extracted_data: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    processing_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

@dataclass
class ProcessingConfig:
    """处理配置"""
    enable_ocr: bool = True
    enable_template_matching: bool = True
    enable_pattern_recognition: bool = True
    confidence_threshold: float = 0.8
    max_processing_time: float = 30.0
    output_format: str = "json"
    language: str = "zh-cn"

class MultiModalParser:
    """多模态解析器"""
    
    def __init__(self, config: Optional[ProcessingConfig] = None):
        """初始化解析器"""
        self.config = config or ProcessingConfig()
        self.logger = logging.getLogger(__name__)
        
        # OCR引擎（模拟）
        self.ocr_engine = OCREngine()
        
        # 模板库
        self.template_library = TemplateLibrary()
        
        # 模式识别器
        self.pattern_recognizer = PatternRecognizer()
        
        # 提取器映射
        self.extractors = {
            InputFormat.TEXT: TextExtractor(),
            InputFormat.TABLE: TableExtractor(),
            InputFormat.IMAGE: ImageExtractor(),
            InputFormat.CHART: ChartExtractor(),
            InputFormat.TECHNICAL_DRAWING: TechnicalDrawingExtractor(),
            InputFormat.PDF: PDFExtractor(),
            InputFormat.EXCEL: ExcelExtractor(),
            InputFormat.CSV: CSVExtractor(),
            InputFormat.XML: XMLExtractor(),
            InputFormat.JSON: JSONExtractor()
        }
        
        # 水利工程专业术语库
        self.terminology_db = {
            "components": {
                "水库": ["reservoir", "水库", "蓄水池", "水库容量"],
                "渠道": ["channel", "渠道", "明渠", "水渠", "输水渠"],
                "管道": ["pipe", "管道", "管线", "输水管", "压力管"],
                "闸门": ["gate", "闸门", "水闸", "控制闸", "调节闸"],
                "泵站": ["pump", "泵站", "水泵", "提升泵", "排水泵"]
            },
            "parameters": {
                "容量": ["capacity", "容量", "库容", "蓄水量"],
                "流量": ["flow", "流量", "流速", "discharge"],
                "水位": ["level", "水位", "液位", "高程"],
                "压力": ["pressure", "压力", "水压", "压强"],
                "直径": ["diameter", "直径", "管径", "口径"]
            },
            "units": {
                "体积": ["立方米", "m³", "m3", "万立方米", "亿立方米"],
                "流量": ["立方米每秒", "m³/s", "m3/s", "升每秒"],
                "长度": ["米", "m", "公里", "km", "毫米", "mm", "厘米", "cm"],
                "压力": ["MPa", "kPa", "Pa", "bar", "atm"]
            }
        }
        
        # 处理统计
        self.processing_stats = {
            "total_processed": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "average_confidence": 0.0,
            "processing_times": []
        }
    
    def parse(self, input_data: Union[str, bytes, Dict], format_hint: Optional[InputFormat] = None) -> ExtractionResult:
        """解析输入数据"""
        start_time = datetime.now()
        
        try:
            # 1. 自动检测输入格式
            detected_format = self._detect_input_format(input_data, format_hint)
            
            # 2. 检测内容类型
            content_type = self._detect_content_type(input_data, detected_format)
            
            # 3. 选择提取方法
            extraction_method = self._select_extraction_method(detected_format, content_type)
            
            # 4. 执行提取
            extracted_data = self._extract_data(input_data, detected_format, extraction_method)
            
            # 5. 数据预处理
            processed_data = self._preprocess_data(extracted_data)
            
            # 6. 数据验证
            validated_data = self._validate_data(processed_data)
            
            # 7. 数据增强
            enhanced_data = self._enhance_data(validated_data)
            
            # 8. 计算置信度
            confidence = self._calculate_confidence(enhanced_data, extraction_method)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = ExtractionResult(
                format_type=detected_format,
                content_type=content_type,
                extraction_method=extraction_method,
                extracted_data=enhanced_data,
                confidence=confidence,
                processing_time=processing_time
            )
            
            # 更新统计
            self._update_stats(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"解析过程中发生错误: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = ExtractionResult(
                format_type=format_hint or InputFormat.TEXT,
                content_type=ContentType.COMPONENT_SPECS,
                extraction_method=ExtractionMethod.PATTERN_RECOGNITION,
                processing_time=processing_time,
                errors=[str(e)]
            )
            
            self.processing_stats["failed_extractions"] += 1
            return result
    
    def _detect_input_format(self, input_data: Union[str, bytes, Dict], format_hint: Optional[InputFormat]) -> InputFormat:
        """检测输入格式"""
        if format_hint:
            return format_hint
        
        if isinstance(input_data, dict):
            return InputFormat.JSON
        elif isinstance(input_data, str):
            # 检查是否为XML
            if input_data.strip().startswith('<') and input_data.strip().endswith('>'):
                return InputFormat.XML
            # 检查是否为CSV格式的文本
            elif ',' in input_data and '\n' in input_data:
                return InputFormat.CSV
            else:
                return InputFormat.TEXT
        elif isinstance(input_data, bytes):
            # 检查文件头判断格式
            if input_data.startswith(b'%PDF'):
                return InputFormat.PDF
            elif input_data.startswith(b'\x89PNG') or input_data.startswith(b'\xff\xd8\xff'):
                return InputFormat.IMAGE
            else:
                return InputFormat.TEXT
        
        return InputFormat.TEXT
    
    def _detect_content_type(self, input_data: Union[str, bytes, Dict], format_type: InputFormat) -> ContentType:
        """检测内容类型"""
        if isinstance(input_data, str):
            text = input_data.lower()
            
            # 检查是否包含参数表格关键词
            if any(keyword in text for keyword in ['参数', '规格', '技术指标', '性能参数']):
                return ContentType.PARAMETER_TABLE
            
            # 检查是否包含组件规格关键词
            elif any(keyword in text for keyword in ['组件', '设备', '构件', '部件']):
                return ContentType.COMPONENT_SPECS
            
            # 检查是否包含流程图关键词
            elif any(keyword in text for keyword in ['流程', '工艺', '系统图', '连接']):
                return ContentType.FLOW_DIAGRAM
            
            # 检查是否包含测量数据关键词
            elif any(keyword in text for keyword in ['测量', '监测', '数据', '记录']):
                return ContentType.MEASUREMENT_DATA
        
        return ContentType.COMPONENT_SPECS
    
    def _select_extraction_method(self, format_type: InputFormat, content_type: ContentType) -> ExtractionMethod:
        """选择提取方法"""
        if format_type in [InputFormat.JSON, InputFormat.XML, InputFormat.CSV]:
            return ExtractionMethod.STRUCTURED_PARSING
        elif format_type == InputFormat.IMAGE:
            return ExtractionMethod.OCR
        elif format_type == InputFormat.TABLE:
            return ExtractionMethod.TEMPLATE_MATCHING
        else:
            return ExtractionMethod.PATTERN_RECOGNITION
    
    def _extract_data(self, input_data: Union[str, bytes, Dict], format_type: InputFormat, method: ExtractionMethod) -> Dict[str, Any]:
        """提取数据"""
        extractor = self.extractors.get(format_type)
        if extractor:
            return extractor.extract(input_data, method)
        else:
            # 默认文本提取
            return self.extractors[InputFormat.TEXT].extract(input_data, method)
    
    def _preprocess_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """数据预处理"""
        processed_data = {}
        
        for key, value in data.items():
            # 清理文本
            if isinstance(value, str):
                # 去除多余空格
                value = re.sub(r'\s+', ' ', value.strip())
                # 标准化术语
                value = self._standardize_terminology(value)
            
            processed_data[key] = value
        
        return processed_data
    
    def _standardize_terminology(self, text: str) -> str:
        """标准化术语"""
        # 组件术语标准化
        for standard_term, variants in self.terminology_db["components"].items():
            for variant in variants:
                if variant != standard_term:
                    text = re.sub(rf'\b{re.escape(variant)}\b', standard_term, text, flags=re.IGNORECASE)
        
        # 参数术语标准化
        for standard_term, variants in self.terminology_db["parameters"].items():
            for variant in variants:
                if variant != standard_term:
                    text = re.sub(rf'\b{re.escape(variant)}\b', standard_term, text, flags=re.IGNORECASE)
        
        return text
    
    def _validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """数据验证"""
        validated_data = {}
        
        for key, value in data.items():
            # 验证数值参数
            if self._is_numeric_parameter(key, value):
                validated_value = self._validate_numeric_value(value)
                validated_data[key] = validated_value
            else:
                validated_data[key] = value
        
        return validated_data
    
    def _is_numeric_parameter(self, key: str, value: Any) -> bool:
        """判断是否为数值参数"""
        numeric_keywords = ['容量', '流量', '水位', '压力', '直径', '长度', '高度', '宽度']
        return any(keyword in str(key) for keyword in numeric_keywords)
    
    def _validate_numeric_value(self, value: Any) -> Any:
        """验证数值"""
        if isinstance(value, str):
            # 提取数值和单位
            match = re.search(r'([\d.]+)\s*([^\d\s]*)', value)
            if match:
                number = float(match.group(1))
                unit = match.group(2).strip()
                
                # 验证数值合理性
                if number < 0:
                    return f"0{unit}"  # 负数修正为0
                elif number > 1e12:  # 过大的数值
                    return f"1e12{unit}"
                else:
                    return value
        
        return value
    
    def _enhance_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """数据增强"""
        enhanced_data = data.copy()
        
        # 1. 去重
        enhanced_data = self._remove_duplicates(enhanced_data)
        
        # 2. 单位标准化
        enhanced_data = self._standardize_units(enhanced_data)
        
        # 3. 补充缺失信息
        enhanced_data = self._fill_missing_info(enhanced_data)
        
        # 4. 关系推理
        enhanced_data = self._infer_relationships(enhanced_data)
        
        return enhanced_data
    
    def _remove_duplicates(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """去重"""
        # 简化实现：移除值相同的键
        seen_values = set()
        deduplicated = {}
        
        for key, value in data.items():
            value_str = str(value)
            if value_str not in seen_values:
                deduplicated[key] = value
                seen_values.add(value_str)
        
        return deduplicated
    
    def _standardize_units(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """单位标准化"""
        standardized = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                # 长度单位标准化
                value = re.sub(r'(\d+)\s*公里', r'\1000米', value)
                value = re.sub(r'(\d+)\s*千米', r'\1000米', value)
                value = re.sub(r'(\d+)\s*毫米', lambda m: f"{float(m.group(1))/1000}米", value)
                value = re.sub(r'(\d+)\s*厘米', lambda m: f"{float(m.group(1))/100}米", value)
                
                # 容量单位标准化
                value = re.sub(r'(\d+)\s*万立方米', lambda m: f"{float(m.group(1))*10000}立方米", value)
                value = re.sub(r'(\d+)\s*千立方米', lambda m: f"{float(m.group(1))*1000}立方米", value)
            
            standardized[key] = value
        
        return standardized
    
    def _fill_missing_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """补充缺失信息"""
        # 基于已有信息推断缺失信息
        enhanced = data.copy()
        
        # 如果有组件但没有类型，尝试推断类型
        if 'components' in enhanced:
            for comp_name in enhanced['components']:
                if isinstance(enhanced['components'][comp_name], str):
                    # 转换为字典格式并添加类型信息
                    comp_type = self._infer_component_type(comp_name)
                    enhanced['components'][comp_name] = {
                        'name': comp_name,
                        'type': comp_type
                    }
        
        return enhanced
    
    def _infer_component_type(self, component_name: str) -> str:
        """推断组件类型"""
        name_lower = component_name.lower()
        
        if any(keyword in name_lower for keyword in ['水库', '蓄水池']):
            return 'reservoir'
        elif any(keyword in name_lower for keyword in ['渠道', '明渠']):
            return 'channel'
        elif any(keyword in name_lower for keyword in ['管道', '管线']):
            return 'pipe'
        elif any(keyword in name_lower for keyword in ['闸门', '水闸']):
            return 'gate'
        elif any(keyword in name_lower for keyword in ['泵站', '水泵']):
            return 'pump'
        else:
            return 'unknown'
    
    def _infer_relationships(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """推理关系"""
        enhanced = data.copy()
        
        # 如果有多个组件，尝试推断连接关系
        if 'components' in enhanced and len(enhanced['components']) > 1:
            connections = self._infer_component_connections(enhanced['components'])
            if connections:
                enhanced['connections'] = connections
        
        return enhanced
    
    def _infer_component_connections(self, components: Dict[str, Any]) -> List[Dict[str, Any]]:
        """推断组件连接"""
        connections = []
        
        # 简化的连接推理逻辑
        comp_names = list(components.keys())
        
        # 如果有水库和渠道，假设水库向渠道供水
        if any('水库' in name for name in comp_names) and any('渠道' in name for name in comp_names):
            reservoir = next(name for name in comp_names if '水库' in name)
            channel = next(name for name in comp_names if '渠道' in name)
            connections.append({
                'from': reservoir,
                'to': channel,
                'type': '供水',
                'confidence': 0.8
            })
        
        return connections
    
    def _calculate_confidence(self, data: Dict[str, Any], method: ExtractionMethod) -> float:
        """计算置信度"""
        base_confidence = {
            ExtractionMethod.STRUCTURED_PARSING: 0.95,
            ExtractionMethod.PATTERN_RECOGNITION: 0.85,
            ExtractionMethod.TEMPLATE_MATCHING: 0.90,
            ExtractionMethod.OCR: 0.75,
            ExtractionMethod.AI_EXTRACTION: 0.88
        }.get(method, 0.8)
        
        # 基于数据完整性调整置信度
        completeness_factor = min(len(data) / 5, 1.0)  # 假设5个字段为完整
        
        # 基于数据质量调整置信度
        quality_factor = self._assess_data_quality(data)
        
        final_confidence = base_confidence * completeness_factor * quality_factor
        return min(final_confidence, 1.0)
    
    def _assess_data_quality(self, data: Dict[str, Any]) -> float:
        """评估数据质量"""
        quality_score = 1.0
        
        for key, value in data.items():
            if isinstance(value, str):
                # 检查是否包含无效字符
                if re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', value):
                    quality_score *= 0.9
                
                # 检查是否为空或只有空格
                if not value.strip():
                    quality_score *= 0.8
        
        return quality_score
    
    def _update_stats(self, result: ExtractionResult):
        """更新统计信息"""
        self.processing_stats["total_processed"] += 1
        
        if result.confidence >= self.config.confidence_threshold:
            self.processing_stats["successful_extractions"] += 1
        
        self.processing_stats["processing_times"].append(result.processing_time)
        
        # 更新平均置信度
        total = self.processing_stats["total_processed"]
        current_avg = self.processing_stats["average_confidence"]
        new_confidence = result.confidence
        
        self.processing_stats["average_confidence"] = (
            (current_avg * (total - 1) + new_confidence) / total
        )
    
    def batch_parse(self, input_list: List[Union[str, bytes, Dict]], format_hints: Optional[List[InputFormat]] = None) -> List[ExtractionResult]:
        """批量解析"""
        results = []
        
        for i, input_data in enumerate(input_list):
            format_hint = format_hints[i] if format_hints and i < len(format_hints) else None
            result = self.parse(input_data, format_hint)
            results.append(result)
        
        return results
    
    def export_results(self, results: List[ExtractionResult], output_format: str = "json") -> str:
        """导出结果"""
        if output_format.lower() == "json":
            return json.dumps([result.__dict__ for result in results], ensure_ascii=False, indent=2, default=str)
        elif output_format.lower() == "csv":
            # 简化的CSV导出
            csv_lines = ["format_type,content_type,confidence,processing_time"]
            for result in results:
                csv_lines.append(f"{result.format_type.value},{result.content_type.value},{result.confidence},{result.processing_time}")
            return "\n".join(csv_lines)
        else:
            return str(results)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """获取处理统计"""
        stats = self.processing_stats.copy()
        
        if stats["processing_times"]:
            stats["average_processing_time"] = np.mean(stats["processing_times"])
            stats["max_processing_time"] = np.max(stats["processing_times"])
            stats["min_processing_time"] = np.min(stats["processing_times"])
        
        stats["success_rate"] = (
            stats["successful_extractions"] / max(stats["total_processed"], 1)
        )
        
        return stats

# 提取器基类和具体实现
class BaseExtractor:
    """提取器基类"""
    
    def extract(self, input_data: Union[str, bytes, Dict], method: ExtractionMethod) -> Dict[str, Any]:
        """提取数据"""
        raise NotImplementedError

class TextExtractor(BaseExtractor):
    """文本提取器"""
    
    def extract(self, input_data: Union[str, bytes, Dict], method: ExtractionMethod) -> Dict[str, Any]:
        if isinstance(input_data, bytes):
            text = input_data.decode('utf-8', errors='ignore')
        else:
            text = str(input_data)
        
        # 基础的文本解析
        result = {
            "raw_text": text,
            "components": self._extract_components(text),
            "parameters": self._extract_parameters(text)
        }
        
        return result
    
    def _extract_components(self, text: str) -> Dict[str, Any]:
        """提取组件"""
        components = {}
        
        # 水库
        if re.search(r'水库|蓄水池', text, re.IGNORECASE):
            components["水库"] = {"type": "reservoir"}
        
        # 渠道
        if re.search(r'渠道|明渠', text, re.IGNORECASE):
            components["渠道"] = {"type": "channel"}
        
        # 管道
        if re.search(r'管道|管线', text, re.IGNORECASE):
            components["管道"] = {"type": "pipe"}
        
        return components
    
    def _extract_parameters(self, text: str) -> Dict[str, Any]:
        """提取参数"""
        parameters = {}
        
        # 容量
        capacity_match = re.search(r'容量[为是]?([\d.]+)([万千]?)立方米', text)
        if capacity_match:
            value = float(capacity_match.group(1))
            unit = capacity_match.group(2)
            if unit == '万':
                value *= 10000
            elif unit == '千':
                value *= 1000
            parameters["容量"] = f"{value}立方米"
        
        # 水位
        level_match = re.search(r'水位[为是]?([\d.]+)米', text)
        if level_match:
            parameters["水位"] = f"{level_match.group(1)}米"
        
        return parameters

class TableExtractor(BaseExtractor):
    """表格提取器"""
    
    def extract(self, input_data: Union[str, bytes, Dict], method: ExtractionMethod) -> Dict[str, Any]:
        # 模拟表格数据提取
        return {
            "table_data": "模拟表格数据",
            "rows": 10,
            "columns": 5
        }

class ImageExtractor(BaseExtractor):
    """图像提取器"""
    
    def extract(self, input_data: Union[str, bytes, Dict], method: ExtractionMethod) -> Dict[str, Any]:
        # 模拟图像OCR提取
        return {
            "ocr_text": "模拟OCR识别文本",
            "confidence": 0.85
        }

class ChartExtractor(BaseExtractor):
    """图表提取器"""
    
    def extract(self, input_data: Union[str, bytes, Dict], method: ExtractionMethod) -> Dict[str, Any]:
        # 模拟图表数据提取
        return {
            "chart_type": "line_chart",
            "data_points": [(1, 10), (2, 20), (3, 15)]
        }

class TechnicalDrawingExtractor(BaseExtractor):
    """技术图纸提取器"""
    
    def extract(self, input_data: Union[str, bytes, Dict], method: ExtractionMethod) -> Dict[str, Any]:
        # 模拟技术图纸信息提取
        return {
            "drawing_type": "hydraulic_system",
            "components": ["水库", "渠道", "闸门"],
            "dimensions": {"长度": "1000米", "宽度": "500米"}
        }

class PDFExtractor(BaseExtractor):
    """PDF提取器"""
    
    def extract(self, input_data: Union[str, bytes, Dict], method: ExtractionMethod) -> Dict[str, Any]:
        # 模拟PDF文本提取
        return {
            "extracted_text": "模拟PDF提取文本",
            "page_count": 5
        }

class ExcelExtractor(BaseExtractor):
    """Excel提取器"""
    
    def extract(self, input_data: Union[str, bytes, Dict], method: ExtractionMethod) -> Dict[str, Any]:
        # 模拟Excel数据提取
        return {
            "sheets": ["Sheet1", "Sheet2"],
            "data": {"A1": "组件名称", "B1": "参数值"}
        }

class CSVExtractor(BaseExtractor):
    """CSV提取器"""
    
    def extract(self, input_data: Union[str, bytes, Dict], method: ExtractionMethod) -> Dict[str, Any]:
        if isinstance(input_data, str):
            lines = input_data.strip().split('\n')
            if lines:
                headers = lines[0].split(',')
                data_rows = [line.split(',') for line in lines[1:]]
                return {
                    "headers": headers,
                    "rows": data_rows,
                    "row_count": len(data_rows)
                }
        
        return {"error": "无法解析CSV数据"}

class XMLExtractor(BaseExtractor):
    """XML提取器"""
    
    def extract(self, input_data: Union[str, bytes, Dict], method: ExtractionMethod) -> Dict[str, Any]:
        # 简化的XML解析
        if isinstance(input_data, str):
            # 提取标签内容
            tags = re.findall(r'<(\w+)>([^<]+)</\1>', input_data)
            return {tag: content for tag, content in tags}
        
        return {"error": "无法解析XML数据"}

class JSONExtractor(BaseExtractor):
    """JSON提取器"""
    
    def extract(self, input_data: Union[str, bytes, Dict], method: ExtractionMethod) -> Dict[str, Any]:
        if isinstance(input_data, dict):
            return input_data
        elif isinstance(input_data, str):
            try:
                return json.loads(input_data)
            except json.JSONDecodeError:
                return {"error": "无法解析JSON数据"}
        
        return {"error": "无效的JSON输入"}

# 辅助类
class OCREngine:
    """OCR引擎（模拟）"""
    
    def recognize(self, image_data: bytes) -> str:
        """识别图像中的文字"""
        # 模拟OCR识别
        return "模拟OCR识别结果：水库容量1000万立方米，设计水位150米"

class TemplateLibrary:
    """模板库"""
    
    def __init__(self):
        self.templates = {
            "parameter_table": {
                "pattern": r"参数\s*值\s*单位",
                "extraction_rules": []
            },
            "component_specs": {
                "pattern": r"组件\s*规格\s*说明",
                "extraction_rules": []
            }
        }
    
    def match_template(self, content: str) -> Optional[str]:
        """匹配模板"""
        for template_name, template_data in self.templates.items():
            if re.search(template_data["pattern"], content, re.IGNORECASE):
                return template_name
        return None

class PatternRecognizer:
    """模式识别器"""
    
    def __init__(self):
        self.patterns = {
            "numeric_with_unit": r"([\d.]+)\s*([a-zA-Z\u4e00-\u9fff]+)",
            "component_definition": r"([\u4e00-\u9fff]+)[:：]\s*([^\n]+)",
            "parameter_value": r"([\u4e00-\u9fff]+)[为是]([\d.]+)([\u4e00-\u9fff]*)"
        }
    
    def recognize_patterns(self, text: str) -> Dict[str, List[Tuple]]:
        """识别模式"""
        results = {}
        
        for pattern_name, pattern in self.patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                results[pattern_name] = matches
        
        return results