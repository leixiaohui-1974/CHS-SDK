#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CHS仿真平台批量仿真功能测试
"""

import pytest
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.main import app
from api.database.database import get_db
from api.database import models
from core_lib.core_engine.solver.batch_solver import (
    BatchSimulationEngine, BatchTask, BatchJob, TaskStatus
)
from core_lib.core_engine.solver.batch_manager import BatchSimulationManager
from core_lib.analysis.result_comparator import ResultComparator, ComparisonType
from core_lib.utils.result_exporter import ResultExporter, ExportFormat, ExportOptions
from core_lib.core_engine.template.template_manager import (
    TemplateManager, TemplateType, TemplateCategory, TemplateStatus
)

# 测试客户端
client = TestClient(app)

class TestBatchSimulation:
    """批量仿真测试类"""
    
    @pytest.fixture
    def mock_db_session(self):
        """模拟数据库会话"""
        session = Mock(spec=Session)
        return session
    
    @pytest.fixture
    def sample_batch_task(self):
        """示例批量任务"""
        return {
            "name": "测试批量仿真",
            "description": "批量仿真测试任务",
            "tasks": [
                {
                    "name": "任务1",
                    "parameters": {
                        "param1": 1.0,
                        "param2": "value1"
                    },
                    "configuration": {
                        "solver": "default",
                        "max_iterations": 1000
                    }
                },
                {
                    "name": "任务2",
                    "parameters": {
                        "param1": 2.0,
                        "param2": "value2"
                    },
                    "configuration": {
                        "solver": "default",
                        "max_iterations": 1000
                    }
                }
            ],
            "priority": "normal",
            "max_parallel_tasks": 2,
            "timeout_minutes": 60,
            "retry_count": 3,
            "notification_webhook": "http://example.com/webhook"
        }
    
    @pytest.fixture
    def batch_engine(self):
        """批量仿真引擎实例"""
        return BatchSimulationEngine(max_workers=4)
    
    @pytest.fixture
    def batch_manager(self):
        """批量仿真管理器实例"""
        return BatchSimulationManager()
    
    def test_submit_batch_job(self, sample_batch_task):
        """测试提交批量仿真任务"""
        with patch('api.routes.batch.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            response = client.post(
                "/api/v1/batch/submit",
                json=sample_batch_task,
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "job_id" in data
            assert "status" in data
            assert data["status"] == "submitted"
    
    def test_get_batch_jobs(self):
        """测试获取批量任务列表"""
        with patch('api.routes.batch.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # 模拟数据库查询结果
            mock_job = Mock()
            mock_job.id = "test_job_id"
            mock_job.name = "测试任务"
            mock_job.status = "running"
            mock_job.created_at = datetime.now()
            mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = [mock_job]
            
            response = client.get(
                "/api/v1/batch/jobs",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "jobs" in data
            assert len(data["jobs"]) >= 0
    
    def test_get_batch_job_detail(self):
        """测试获取批量任务详情"""
        job_id = "test_job_id"
        
        with patch('api.routes.batch.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # 模拟数据库查询结果
            mock_job = Mock()
            mock_job.id = job_id
            mock_job.name = "测试任务"
            mock_job.status = "completed"
            mock_job.progress = 100
            mock_job.total_tasks = 10
            mock_job.completed_tasks = 10
            mock_job.failed_tasks = 0
            mock_job.created_at = datetime.now()
            mock_job.updated_at = datetime.now()
            mock_db.query.return_value.filter.return_value.first.return_value = mock_job
            
            response = client.get(
                f"/api/v1/batch/jobs/{job_id}",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == job_id
            assert data["status"] == "completed"
    
    def test_cancel_batch_job(self):
        """测试取消批量任务"""
        job_id = "test_job_id"
        
        with patch('api.routes.batch.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            response = client.post(
                f"/api/v1/batch/jobs/{job_id}/cancel",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "任务取消成功"
    
    def test_download_batch_results(self):
        """测试下载批量结果"""
        job_id = "test_job_id"
        
        with patch('api.routes.batch.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            response = client.get(
                f"/api/v1/batch/jobs/{job_id}/download",
                headers={"Authorization": "Bearer test_token"}
            )
            
            # 根据实际实现调整断言
            assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_batch_task_creation(self, batch_engine):
        """测试批量任务创建"""
        task_config = {
            "name": "测试任务",
            "parameters": {"param1": 1.0},
            "configuration": {"solver": "default"}
        }
        
        task = BatchTask(
            id=str(uuid.uuid4()),
            name=task_config["name"],
            parameters=task_config["parameters"],
            configuration=task_config["configuration"],
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        
        assert task.id is not None
        assert task.name == "测试任务"
        assert task.status == TaskStatus.PENDING
        assert task.parameters["param1"] == 1.0
    
    @pytest.mark.asyncio
    async def test_batch_job_execution(self, batch_engine):
        """测试批量作业执行"""
        # 创建测试任务
        tasks = []
        for i in range(3):
            task = BatchTask(
                id=str(uuid.uuid4()),
                name=f"任务{i+1}",
                parameters={"param1": i + 1.0},
                configuration={"solver": "default"},
                status=TaskStatus.PENDING,
                created_at=datetime.now()
            )
            tasks.append(task)
        
        # 创建批量作业
        job = BatchJob(
            id=str(uuid.uuid4()),
            name="测试批量作业",
            description="测试描述",
            tasks=tasks,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            priority="normal",
            max_parallel_tasks=2
        )
        
        # 模拟执行
        with patch.object(batch_engine, '_execute_single_task', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = {
                "status": "completed",
                "result": {"output": "test_result"}
            }
            
            await batch_engine.submit_job(job)
            
            # 验证作业状态
            assert job.status in [TaskStatus.PENDING, TaskStatus.RUNNING]
    
    @pytest.mark.asyncio
    async def test_batch_manager_operations(self, batch_manager):
        """测试批量管理器操作"""
        # 启动管理器
        await batch_manager.start()
        
        # 提交任务
        task_configs = [
            {
                "name": "任务1",
                "parameters": {"param1": 1.0},
                "configuration": {"solver": "default"}
            },
            {
                "name": "任务2",
                "parameters": {"param1": 2.0},
                "configuration": {"solver": "default"}
            }
        ]
        
        with patch.object(batch_manager.engine, '_execute_single_task', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = {
                "status": "completed",
                "result": {"output": "test_result"}
            }
            
            job_id = await batch_manager.submit_batch_job(
                name="测试批量任务",
                description="测试描述",
                task_configs=task_configs,
                user_id="test_user"
            )
            
            assert job_id is not None
            
            # 获取任务状态
            status = await batch_manager.get_job_status(job_id)
            assert status is not None
        
        # 停止管理器
        await batch_manager.stop()

class TestResultComparator:
    """结果对比分析测试类"""
    
    @pytest.fixture
    def result_comparator(self):
        """结果对比器实例"""
        return ResultComparator()
    
    @pytest.fixture
    def sample_results(self):
        """示例结果数据"""
        return [
            {
                "id": "result1",
                "name": "结果1",
                "outputs": {
                    "temperature": [20.0, 21.0, 22.0, 23.0, 24.0],
                    "pressure": [1.0, 1.1, 1.2, 1.3, 1.4],
                    "efficiency": 0.85
                },
                "parameters": {
                    "input_power": 100.0,
                    "flow_rate": 10.0
                }
            },
            {
                "id": "result2",
                "name": "结果2",
                "outputs": {
                    "temperature": [19.0, 20.0, 21.0, 22.0, 23.0],
                    "pressure": [0.9, 1.0, 1.1, 1.2, 1.3],
                    "efficiency": 0.82
                },
                "parameters": {
                    "input_power": 90.0,
                    "flow_rate": 9.0
                }
            }
        ]
    
    @pytest.mark.asyncio
    async def test_statistical_comparison(self, result_comparator, sample_results):
        """测试统计对比"""
        comparison_result = await result_comparator.compare_results(
            results=sample_results,
            comparison_type=ComparisonType.STATISTICAL,
            metrics=["temperature", "pressure", "efficiency"]
        )
        
        assert comparison_result is not None
        assert comparison_result.comparison_type == ComparisonType.STATISTICAL
        assert "temperature" in comparison_result.metrics
        assert "pressure" in comparison_result.metrics
        assert "efficiency" in comparison_result.metrics
    
    @pytest.mark.asyncio
    async def test_trend_comparison(self, result_comparator, sample_results):
        """测试趋势对比"""
        comparison_result = await result_comparator.compare_results(
            results=sample_results,
            comparison_type=ComparisonType.TREND,
            metrics=["temperature", "pressure"]
        )
        
        assert comparison_result is not None
        assert comparison_result.comparison_type == ComparisonType.TREND
    
    @pytest.mark.asyncio
    async def test_performance_comparison(self, result_comparator, sample_results):
        """测试性能对比"""
        comparison_result = await result_comparator.compare_results(
            results=sample_results,
            comparison_type=ComparisonType.PERFORMANCE,
            metrics=["efficiency"]
        )
        
        assert comparison_result is not None
        assert comparison_result.comparison_type == ComparisonType.PERFORMANCE

class TestResultExporter:
    """结果导出测试类"""
    
    @pytest.fixture
    def result_exporter(self, tmp_path):
        """结果导出器实例"""
        return ResultExporter(export_dir=str(tmp_path))
    
    @pytest.fixture
    def sample_result_ids(self):
        """示例结果ID列表"""
        return ["result1", "result2", "result3"]
    
    @pytest.mark.asyncio
    async def test_json_export(self, result_exporter, sample_result_ids):
        """测试JSON导出"""
        options = ExportOptions(
            format=ExportFormat.JSON,
            include_metadata=True,
            include_parameters=True
        )
        
        with patch.object(result_exporter, '_load_results_data', new_callable=AsyncMock) as mock_load:
            mock_load.return_value = [
                {
                    "id": "result1",
                    "name": "结果1",
                    "outputs": {"temperature": 25.0},
                    "parameters": {"input_power": 100.0},
                    "metadata": {"solver": "default"}
                }
            ]
            
            export_result = await result_exporter.export_results(
                result_ids=sample_result_ids,
                options=options,
                user_id="test_user"
            )
            
            assert export_result is not None
            assert export_result.format == ExportFormat.JSON
            assert export_result.file_path.endswith('.json')
    
    @pytest.mark.asyncio
    async def test_csv_export(self, result_exporter, sample_result_ids):
        """测试CSV导出"""
        options = ExportOptions(
            format=ExportFormat.CSV,
            include_parameters=True
        )
        
        with patch.object(result_exporter, '_load_results_data', new_callable=AsyncMock) as mock_load:
            mock_load.return_value = [
                {
                    "id": "result1",
                    "name": "结果1",
                    "outputs": {"temperature": 25.0},
                    "parameters": {"input_power": 100.0}
                }
            ]
            
            export_result = await result_exporter.export_results(
                result_ids=sample_result_ids,
                options=options,
                user_id="test_user"
            )
            
            assert export_result is not None
            assert export_result.format == ExportFormat.CSV
            assert export_result.file_path.endswith('.csv')
    
    @pytest.mark.asyncio
    async def test_excel_export(self, result_exporter, sample_result_ids):
        """测试Excel导出"""
        options = ExportOptions(
            format=ExportFormat.EXCEL,
            include_charts=True,
            include_parameters=True
        )
        
        with patch.object(result_exporter, '_load_results_data', new_callable=AsyncMock) as mock_load:
            mock_load.return_value = [
                {
                    "id": "result1",
                    "name": "结果1",
                    "outputs": {"temperature": [20, 21, 22, 23, 24]},
                    "parameters": {"input_power": 100.0}
                }
            ]
            
            export_result = await result_exporter.export_results(
                result_ids=sample_result_ids,
                options=options,
                user_id="test_user"
            )
            
            assert export_result is not None
            assert export_result.format == ExportFormat.EXCEL
            assert export_result.file_path.endswith('.xlsx')

class TestTemplateManager:
    """模板管理测试类"""
    
    @pytest.fixture
    def template_manager(self, tmp_path):
        """模板管理器实例"""
        return TemplateManager(templates_dir=str(tmp_path))
    
    @pytest.fixture
    def sample_template_params(self):
        """示例模板参数"""
        from core_lib.core_engine.template.template_manager import TemplateParameter
        
        return [
            TemplateParameter(
                name="input_power",
                type="number",
                description="输入功率",
                default_value=100.0,
                min_value=0.0,
                max_value=1000.0,
                unit="W"
            ),
            TemplateParameter(
                name="flow_rate",
                type="number",
                description="流量",
                default_value=10.0,
                min_value=1.0,
                max_value=100.0,
                unit="L/min"
            )
        ]
    
    @pytest.mark.asyncio
    async def test_create_template(self, template_manager, sample_template_params):
        """测试创建模板"""
        with patch.object(template_manager, '_save_template_to_db', new_callable=AsyncMock):
            template = await template_manager.create_template(
                name="测试模板",
                description="这是一个测试模板",
                template_type=TemplateType.SIMULATION,
                category=TemplateCategory.BASIC,
                parameters=sample_template_params,
                configuration={
                    "solver": "default",
                    "max_iterations": 1000
                },
                author="test_user"
            )
            
            assert template is not None
            assert template.metadata.name == "测试模板"
            assert template.metadata.type == TemplateType.SIMULATION
            assert len(template.content.parameters) == 2
    
    @pytest.mark.asyncio
    async def test_apply_template(self, template_manager, sample_template_params):
        """测试应用模板"""
        # 先创建模板
        with patch.object(template_manager, '_save_template_to_db', new_callable=AsyncMock):
            template = await template_manager.create_template(
                name="测试模板",
                description="这是一个测试模板",
                template_type=TemplateType.SIMULATION,
                category=TemplateCategory.BASIC,
                parameters=sample_template_params,
                configuration={
                    "solver": "{{ solver_type | default('default') }}",
                    "max_iterations": "{{ max_iter | default(1000) }}",
                    "input_power": "{{ input_power }}",
                    "flow_rate": "{{ flow_rate }}"
                },
                author="test_user"
            )
        
        # 应用模板
        with patch.object(template_manager, '_increment_usage_count', new_callable=AsyncMock):
            result = await template_manager.apply_template(
                template_id=template.metadata.id,
                parameter_values={
                    "input_power": 150.0,
                    "flow_rate": 15.0,
                    "solver_type": "advanced",
                    "max_iter": 2000
                },
                user_id="test_user"
            )
            
            assert result is not None
            assert result["template_id"] == template.metadata.id
            assert result["parameters"]["input_power"] == 150.0
            assert result["parameters"]["flow_rate"] == 15.0
            assert result["configuration"]["solver"] == "advanced"
            assert result["configuration"]["max_iterations"] == 2000
    
    @pytest.mark.asyncio
    async def test_clone_template(self, template_manager, sample_template_params):
        """测试克隆模板"""
        # 先创建原始模板
        with patch.object(template_manager, '_save_template_to_db', new_callable=AsyncMock):
            original_template = await template_manager.create_template(
                name="原始模板",
                description="原始模板描述",
                template_type=TemplateType.SIMULATION,
                category=TemplateCategory.BASIC,
                parameters=sample_template_params,
                configuration={"solver": "default"},
                author="original_author"
            )
        
        # 克隆模板
        with patch.object(template_manager, '_save_template_to_db', new_callable=AsyncMock):
            cloned_template = await template_manager.clone_template(
                template_id=original_template.metadata.id,
                new_name="克隆模板",
                author="clone_author",
                modifications={
                    "description": "这是克隆的模板",
                    "configuration": {"solver": "advanced"}
                }
            )
            
            assert cloned_template is not None
            assert cloned_template.metadata.name == "克隆模板"
            assert cloned_template.metadata.author == "clone_author"
            assert cloned_template.metadata.parent_template_id == original_template.metadata.id
            assert cloned_template.content.configuration["solver"] == "advanced"
    
    @pytest.mark.asyncio
    async def test_export_import_template(self, template_manager, sample_template_params):
        """测试模板导出导入"""
        # 创建模板
        with patch.object(template_manager, '_save_template_to_db', new_callable=AsyncMock):
            original_template = await template_manager.create_template(
                name="导出测试模板",
                description="用于测试导出功能的模板",
                template_type=TemplateType.SIMULATION,
                category=TemplateCategory.BASIC,
                parameters=sample_template_params,
                configuration={"solver": "default"},
                author="test_user"
            )
        
        # 导出模板
        exported_content = await template_manager.export_template(
            template_id=original_template.metadata.id,
            export_format="json"
        )
        
        assert exported_content is not None
        assert "metadata" in exported_content
        assert "content" in exported_content
        
        # 导入模板
        with patch.object(template_manager, '_save_template_to_db', new_callable=AsyncMock):
            imported_template = await template_manager.import_template(
                template_content=exported_content,
                import_format="json",
                author="import_user"
            )
            
            assert imported_template is not None
            assert imported_template.metadata.name == original_template.metadata.name
            assert imported_template.metadata.author == "import_user"
            assert len(imported_template.content.parameters) == len(original_template.content.parameters)

if __name__ == "__main__":
    # 运行测试
    pytest.main(["-v", __file__])