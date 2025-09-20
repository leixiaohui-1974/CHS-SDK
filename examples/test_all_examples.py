#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量运行并验证 examples 目录下的全部示例."""
import argparse
import json
import os
import statistics
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence, Set, Tuple

# 设置环境变量强制UTF-8编码
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

# 设置标准输出/错误编码为UTF-8（尽量不更换底层文件对象，以免影响测试框架捕获）
for _stream_name in ("stdout", "stderr"):
    _stream = getattr(sys, _stream_name, None)
    if _stream is None:
        continue
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        # 某些类文件对象不支持 reconfigure（例如 StringIO 或已经关闭的流），忽略即可
        pass

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from examples.run_hardcoded import ExamplesHardcodedRunner  # noqa: E402

EXAMPLE_CATALOG: List[Tuple[str, str]] = [
    ("agent_based_03_event_driven_agents", "事件驱动智能体"),
    ("agent_based_06_centralized_emergency_override", "集中式紧急覆盖"),
    ("agent_based_09_agent_based_distributed_control", "基于智能体的分布式控制"),
    ("agent_based_12_pid_control_comparison", "PID控制比较"),
    ("canal_model_canal_model_comparison", "渠道模型对比"),
    ("canal_model_canal_mpc_pid_control", "运河MPC PID控制"),
    ("canal_model_canal_pid_control", "运河PID控制"),
    ("canal_model_complex_fault_scenario_example", "复杂故障场景"),
    ("canal_model_hierarchical_distributed_control_example", "分层分布式控制"),
    ("canal_model_structured_control_example", "结构化控制"),
    ("demo_simplified_reservoir_control", "简化水库控制演示"),
    ("distributed_digital_twin_simulation/run_simulation", "分布式数字孪生仿真"),
    ("distributed_digital_twin_simulation/run_disturbance_simulation", "分布式数字孪生干扰仿真"),
    ("distributed_digital_twin_simulation/run_comparison_experiment", "分布式数字孪生对比实验"),
    ("distributed_digital_twin_simulation/test_simple_inflow_disturbance", "简单入流干扰测试"),
    ("distributed_digital_twin_simulation/test_inflow_disturbance", "入流干扰测试"),
    ("distributed_digital_twin_simulation/test_network_disturbance", "网络干扰测试"),
    ("distributed_digital_twin_simulation/test_actuator_failure_disturbance", "执行器故障干扰测试"),
    ("distributed_digital_twin_simulation/test_comprehensive_disturbance", "综合干扰测试"),
    ("distributed_digital_twin_simulation/test_multiple_disturbance_types", "多种干扰类型测试"),
    ("distributed_digital_twin_simulation/comprehensive_disturbance_test_suite", "综合干扰测试套件"),
    ("distributed_digital_twin_simulation/parameter_identification_analysis", "参数辨识分析"),
    ("distributed_digital_twin_simulation/physical_digital_twin_comparison", "物理数字孪生对比"),
    ("distributed_digital_twin_simulation/robustness_validation", "鲁棒性验证"),
    ("distributed_digital_twin_simulation/optimized_control_validation", "优化控制验证"),
    ("identification_01_reservoir_storage_curve", "水库库容曲线辨识"),
    ("identification_02_gate_discharge_coefficient", "闸门流量系数辨识"),
    ("identification_03_pipe_roughness", "管道糙率辨识"),
    ("llm_integration", "LLM集成示例"),
    ("mission_example_1", "任务示例1"),
    ("mission_example_2", "任务示例2"),
    ("mission_example_3", "任务示例3"),
    ("mission_example_5", "任务示例5"),
    ("mission_scenarios", "Mission场景示例"),
    ("non_agent_based_01_getting_started", "入门示例"),
    ("non_agent_based_02_multi_component_systems", "多组件系统"),
    ("non_agent_based_07_pipe_and_valve", "管道与阀门"),
    ("non_agent_based_08_non_agent_simulation", "非智能体仿真"),
    ("notebooks_07_centralized_setpoint_optimization", "集中式设定点优化"),
    ("notebooks_10_canal_system", "渠道系统笔记本"),
    ("notebooks_11_control_and_agents", "控制与智能体笔记本"),
    ("watertank_01_simulation", "水箱仿真"),
    ("watertank_refactored_01_simple_simulation", "水箱简单仿真"),
    ("watertank_refactored_02_parameter_identification", "水箱参数辨识"),
    ("watertank_refactored_03_pid_control_inlet", "水箱PID入口控制"),
    ("watertank_refactored_04_pid_control_outlet", "水箱PID出口控制"),
    ("watertank_refactored_05_joint_control", "水箱联合控制"),
    ("watertank_refactored_06_sensor_disturbance", "水箱传感器干扰"),
    ("watertank_refactored_07_actuator_disturbance", "水箱执行器干扰"),
]

SUMMARY_FORMAT_CHOICES = {"none", "json", "tsv", "markdown", "both", "all"}
DEFAULT_SUMMARY_DIR = project_root / "reports" / "test_runs" / "examples"

CATEGORY_SOLUTION_TEMPLATES: Dict[str, str] = {
    "agent_based": "通过消息驱动的分布式智能体协调执行感知、决策与控制，以实现对复杂水利系统的自适应管理。",
    "non_agent_based": "依托高精度物理模型直接求解系统动力学方程，评估结构性变化对水力学行为的影响。",
    "canal_model": "综合渠道水力学方程与控制算法，对比不同调度策略下的水位与流量响应。",
    "identification": "结合仿真与测量数据，通过参数辨识与优化算法反推模型关键参数，提高数字孪生准确度。",
    "demo": "借助精简化的控制闭环演示核心仿真引擎与调度策略的基本协同机理。",
    "mission": "面向工程场景整合多源对象与控制策略，验证系统级联动与应急能力。",
    "distributed_digital_twin_simulation": "搭建跨节点数字孪生协同框架，验证网络、干扰与控制策略对整体鲁棒性的影响。",
    "notebooks": "利用交互式笔记本串联建模、仿真与分析流程，帮助快速探索系统行为。",
    "watertank": "围绕典型水箱实验平台，验证液位控制与扰动抑制策略的表现。",
    "watertank_refactored": "以重构后的水箱模块验证多控制策略与故障场景的鲁棒性。",
    "llm_integration": "引入大语言模型辅助场景构建、调度与结果分析，实现智能化建模工作流。",
}

CATEGORY_MODELING_TEMPLATES: Dict[str, str] = {
    "agent_based": "建模时通过 SimulationBuilder 构建物理水体、控制闸门及智能体，再由 MessageBus 驱动事件流转。",
    "non_agent_based": "直接配置水库、渠道等物理组件，基于质量与动量守恒方程进行数值积分。",
    "canal_model": "采用分段渠道与调控单元的组合模型，叠加 PID/MPC 等控制器模拟不同调度策略。",
    "identification": "设置待辨识参数的搜索空间，使用最小二乘或启发式算法迭代逼近观测数据。",
    "demo": "聚焦核心环节，选取最小化组件组合演示监测-决策-执行闭环。",
    "mission": "组合多水工建筑物、调度策略与外部扰动脚本，构建接近真实工程的复杂工况。",
    "distributed_digital_twin_simulation": "划分多个数字孪生节点并设定通信延迟、失效模式，验证跨域协同仿真。",
    "notebooks": "通过逐步代码单元构建模型、运行仿真并即时可视化结果。",
    "watertank": "以单水箱或多水箱物理模型为核心，配置传感器与阀门响应曲线。",
    "watertank_refactored": "采用模块化水箱组件与可插拔控制器，便于在统一框架下切换策略。",
    "llm_integration": "结合自然语言描述生成配置草稿，再由仿真核对并校正模型。",
}

DEFAULT_SOLUTION_DESCRIPTION = (
    "该示例依托 CHS-SDK 仿真引擎完成物理过程求解，并结合自动化控制策略评估系统表现。"
)
DEFAULT_MODELING_DESCRIPTION = (
    "使用统一的 SimulationBuilder 管理物理组件、控制器与消息流，确保模型结构清晰且可复现。"
)


def _resolve_summary_formats(summary_format: str) -> Set[str]:
    if not summary_format or summary_format == "none":
        return set()
    if summary_format == "json":
        return {"json"}
    if summary_format == "tsv":
        return {"tsv"}
    if summary_format == "markdown":
        return {"markdown"}
    if summary_format == "both":
        return {"json", "tsv"}
    if summary_format == "all":
        return {"json", "tsv", "markdown"}
    raise ValueError(f"Unsupported summary format: {summary_format}")


def _select_category_text(mapping: Mapping[str, str], category: Any, default: str) -> str:
    if not isinstance(category, str):
        return default
    key = category.strip().lower()
    if not key:
        return default
    return mapping.get(key, default)


def _format_bool(value: Any, true_text: str = "是", false_text: str = "否", none_text: str = "未知") -> str:
    if value is True:
        return true_text
    if value is False:
        return false_text
    return none_text


def _format_float(value: Any, precision: int = 3, suffix: str = "") -> str:
    if isinstance(value, (int, float)):
        return f"{float(value):.{precision}f}{suffix}"
    return "未知"


def _format_percentage(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{float(value) * 100:.2f}%"
    return "未知"


def _collect_penalty_details(penalties: Sequence[Mapping[str, Any]]) -> Tuple[List[str], Dict[str, int]]:
    lines: List[str] = []
    severity_counts = {"critical": 0, "major": 0, "minor": 0, "info": 0}
    for entry in penalties:
        if not isinstance(entry, Mapping):
            lines.append(str(entry))
            continue
        severity = str(entry.get("severity", "")).lower()
        if severity in severity_counts:
            severity_counts[severity] += 1
        code = entry.get("code")
        message = entry.get("message", "")
        label_parts = [part for part in (severity.upper() if severity else "", str(code) if code else "") if part]
        if label_parts and message:
            lines.append(f"[{"/".join(label_parts)}] {message}")
        elif message:
            lines.append(message)
        elif label_parts:
            lines.append(f"[{"/".join(label_parts)}]")
    return lines, severity_counts


def _build_markdown_metrics_table(rows: Sequence[Tuple[str, str]]) -> str:
    header = "| 指标 | 数值 |\n| --- | --- |"
    body = "\n".join(f"| {label} | {value} |" for label, value in rows)
    return f"{header}\n{body}" if body else header


def _build_mermaid_pie_chart(
    severity_counts: Mapping[str, int],
    success: bool,
    validation: Mapping[str, Any],
) -> str:
    total_penalties = sum(int(count or 0) for count in severity_counts.values())
    lines: List[str] = ["```mermaid", "pie showData"]
    if total_penalties > 0:
        for label, key in (("Critical", "critical"), ("Major", "major"), ("Minor", "minor"), ("Info", "info")):
            count = max(int(severity_counts.get(key, 0)), 0)
            value = count if count > 0 else 0.01
            lines.append(f'    "{label}" : {value:.2f}')
    else:
        def _weight(flag: bool) -> float:
            return 0.95 if flag else 0.05

        validated = bool(validation.get("validated"))
        valid = bool(validation.get("valid")) if validated else False
        skipped = not validated
        lines.append(f'    "仿真通过" : {_weight(success):.2f}')
        lines.append(f'    "仿真失败" : {_weight(not success):.2f}')
        if skipped:
            lines.append('    "验证跳过" : 0.60')
        else:
            lines.append(f'    "验证通过" : {_weight(valid):.2f}')
            lines.append(f'    "验证未通过" : {_weight(validated and not valid):.2f}')
    lines.append("```")
    return "\n".join(lines)


def _render_example_markdown(
    example_key: str,
    record: Mapping[str, Any],
    metadata: Mapping[str, Any],
    summary_stats: Mapping[str, Any],
) -> str:
    display_name = str(metadata.get("name") or record.get("name") or example_key)
    description = str(metadata.get("description") or "该示例展示了 CHS-SDK 的核心仿真能力。")
    category = metadata.get("category")
    path = metadata.get("path")

    success = bool(record.get("success"))
    validation = record.get("validation") or {}
    validated = validation.get("validated")
    valid = validation.get("valid")
    issues = [str(item) for item in (validation.get("issues") or []) if item]
    metrics = validation.get("metrics") or {}
    time_steps = metrics.get("time_steps")
    variables_checked = metrics.get("variables_checked")
    reason_metrics = metrics.get("reasonableness") or {}
    reason_score = reason_metrics.get("score") if isinstance(reason_metrics, Mapping) else None
    penalties = reason_metrics.get("penalties") if isinstance(reason_metrics, Mapping) else None
    penalties = penalties if isinstance(penalties, Sequence) else []
    penalty_lines, severity_counts = _collect_penalty_details(penalties)
    mass_balance = metrics.get("mass_balance") if isinstance(metrics, Mapping) else {}
    mass_balance = mass_balance if isinstance(mass_balance, Mapping) else {}
    mass_checked = mass_balance.get("checked")
    mass_pass = mass_balance.get("pass") if mass_checked else None
    mass_max = mass_balance.get("max_relative_error")
    mass_mean = mass_balance.get("mean_relative_error")
    mass_reason = mass_balance.get("issue") or mass_balance.get("reason")
    execution_time = record.get("execution_time")
    error_message = record.get("error")

    solution_text = _select_category_text(CATEGORY_SOLUTION_TEMPLATES, category, DEFAULT_SOLUTION_DESCRIPTION)
    modeling_text = _select_category_text(CATEGORY_MODELING_TEMPLATES, category, DEFAULT_MODELING_DESCRIPTION)

    scenario_lines = []
    if path:
        scenario_lines.append(f"- 示例路径：`{path}`")
    scenario_lines.append(f"- 仿真耗时：{_format_float(execution_time, precision=3, suffix=' 秒')}")
    scenario_lines.append(f"- 时间步数：{time_steps if time_steps is not None else '未知'}")
    scenario_lines.append(f"- 校验变量数量：{variables_checked if variables_checked is not None else '未知'}")
    scenario_lines.append(f"- 自动验证状态：{_format_bool(validated, '已执行', '未执行', '已跳过')}")
    if isinstance(valid, bool):
        scenario_lines.append(f"- 验证结论：{'通过' if valid else '存在问题'}")

    metrics_rows = [
        ("仿真结果", "通过" if success else "失败"),
        ("自动验证", "通过" if valid else ("失败" if validated and not valid else "已跳过")),
        ("合理性得分", _format_float(reason_score, precision=3)),
        ("质量守恒检查", _format_bool(mass_checked, "已执行", "未执行", "无数据")),
    ]
    if mass_checked:
        metrics_rows.extend(
            [
                ("质量守恒是否通过", _format_bool(mass_pass, "通过", "未通过", "无数据")),
                ("最大相对误差", _format_percentage(mass_max)),
                ("平均相对误差", _format_percentage(mass_mean)),
            ]
        )
    elif mass_reason:
        metrics_rows.append(("质量守恒检查说明", str(mass_reason)))

    analysis_lines = []
    analysis_lines.append(
        f"- 仿真{'成功' if success else '失败'}，自动验证"
        f"{'通过' if valid else ('发现问题' if validated else '未执行')}."
    )
    if isinstance(reason_score, (int, float)):
        analysis_lines.append(f"- 合理性得分为 {float(reason_score):.3f}，用于衡量数值稳定性与物理一致性。")
    if penalty_lines:
        analysis_lines.append("- 评分扣分项：")
        analysis_lines.extend(f"  - {line}" for line in penalty_lines)
    if issues:
        analysis_lines.append("- 自动校验识别到以下问题：")
        analysis_lines.extend(f"  - {issue}" for issue in issues)
    if error_message:
        analysis_lines.append(f"- 运行过程中捕获异常：{error_message}")
    if not penalty_lines and not issues and not error_message:
        analysis_lines.append("- 未检测到额外问题，结果表现与预期一致。")

    suggestions: List[str] = []
    if not success:
        suggestions.append("优先检查示例脚本与日志输出，定位导致仿真失败的根因。")
    if validated and not valid:
        suggestions.append("根据自动验证报告修复数据异常，再次运行示例确认修复效果。")
    if isinstance(reason_score, (int, float)) and float(reason_score) < 0.8:
        suggestions.append("针对低合理性得分，复核关键量纲、边界条件与时间步长设置。")
    if mass_checked and not mass_pass:
        suggestions.append("质量守恒未通过时，核对入出流量曲线与储量更新逻辑。")
    if penalty_lines:
        suggestions.append("逐项处理扣分项描述的问题，必要时扩展单元测试覆盖。")
    if not suggestions:
        suggestions.append("维持当前配置，并将本次结果纳入基线用于持续回归验证。")

    chart_block = _build_mermaid_pie_chart(severity_counts, success, validation)

    lines: List[str] = [
        f"# {display_name} ({example_key})",
        "",
        "## 问题描述",
        description,
        "",
        "## 求解原理",
        solution_text,
        "",
        "## 建模思路",
        modeling_text,
        "",
        "## 情景设置",
        "\n".join(scenario_lines),
        "",
        "## 结果分析",
        _build_markdown_metrics_table(metrics_rows),
        "",
        "\n".join(analysis_lines),
        "",
        "## 嵌入图表",
        chart_block,
        "",
        "## 讨论和建议",
        "\n".join(f"- {item}" for item in suggestions),
    ]

    if summary_stats:
        overall_success = summary_stats.get("success_count")
        total = summary_stats.get("executed_total") or summary_stats.get("planned_total")
        if isinstance(overall_success, int) and isinstance(total, int) and total:
            lines.extend(
                [
                    "",
                    f"> 本次批量测试共有 {total} 个示例执行，已有 {overall_success} 个通过。",
                ]
            )

    return "\n".join(lines).strip() + "\n"


def _normalize_keys(keys: Iterable[str]) -> List[str]:
    seen = set()
    normalized: List[str] = []
    for key in keys:
        trimmed = key.strip()
        if trimmed and trimmed not in seen:
            normalized.append(trimmed)
            seen.add(trimmed)
    return normalized


def _select_examples(only: Sequence[str] | None, skip: Sequence[str] | None) -> List[Tuple[str, str]]:
    catalog = OrderedDict(EXAMPLE_CATALOG)
    if only:
        subset = _normalize_keys(only)
        missing = [key for key in subset if key not in catalog]
        if missing:
            raise KeyError(f"Unknown example keys: {', '.join(missing)}")
        selected = [(key, catalog[key]) for key in subset]
    else:
        selected = list(catalog.items())

    if skip:
        excluded = set(_normalize_keys(skip))
        selected = [(key, name) for key, name in selected if key not in excluded]

    if not selected:
        raise ValueError("No examples selected for execution.")
    return selected


def _compute_summary(results: Mapping[str, Mapping[str, Any]], planned_total: int, fail_fast_triggered: bool) -> Dict[str, Any]:
    executed_total = len(results)
    success_count = sum(1 for r in results.values() if r.get("success"))
    failure_count = executed_total - success_count

    validated_total = 0
    validation_pass = 0
    validation_fail = 0
    validation_skipped = 0
    mass_balance_checked = 0
    mass_balance_failed = 0
    mass_balance_skipped = 0
    scored_reasonableness = 0
    reason_scores: List[float] = []
    reason_below_threshold = 0
    reason_missing = 0
    severity_tally = {
        "critical": 0,
        "major": 0,
        "minor": 0,
        "info": 0,
    }

    for record in results.values():
        validation = record.get("validation") or {}
        if validation.get("validated"):
            validated_total += 1
            if validation.get("valid"):
                validation_pass += 1
            else:
                validation_fail += 1
        else:
            validation_skipped += 1

        metrics = validation.get("metrics") or {}
        if isinstance(metrics, Mapping):
            mass_balance = metrics.get("mass_balance") or {}
            if mass_balance.get("checked"):
                mass_balance_checked += 1
                if not mass_balance.get("pass", False):
                    mass_balance_failed += 1
            elif mass_balance:
                mass_balance_skipped += 1

            reason_metrics = metrics.get("reasonableness") or {}
            if reason_metrics:
                scored_reasonableness += 1
                score = reason_metrics.get("score")
                if isinstance(score, (int, float)):
                    reason_scores.append(float(score))
                    if float(score) < 0.5:
                        reason_below_threshold += 1
                penalties = reason_metrics.get("penalties") or []
                for penalty in penalties:
                    severity = str(penalty.get("severity", "")).lower()
                    if severity in severity_tally:
                        severity_tally[severity] += 1
            else:
                reason_missing += 1

    return {
        "planned_total": planned_total,
        "executed_total": executed_total,
        "success_count": success_count,
        "failure_count": failure_count,
        "validation": {
            "validated_total": validated_total,
            "validation_pass": validation_pass,
            "validation_fail": validation_fail,
            "validation_skipped": validation_skipped,
        },
        "metrics": {
            "mass_balance": {
                "checked_total": mass_balance_checked,
                "failed": mass_balance_failed,
                "skipped": mass_balance_skipped,
            },
            "reasonableness": {
                "scored_total": scored_reasonableness,
                "missing": reason_missing,
                "average_score": statistics.fmean(reason_scores) if reason_scores else None,
                "min_score": min(reason_scores) if reason_scores else None,
                "below_threshold": reason_below_threshold,
                "penalty_counts": severity_tally,
            },
        },
        "fail_fast_triggered": fail_fast_triggered,
        "skipped_due_to_fail_fast": max(planned_total - executed_total, 0) if fail_fast_triggered else 0,
    }


def _persist_summary(
    results: Mapping[str, Mapping[str, Any]],
    summary_stats: Mapping[str, Any],
    runner_history: Sequence[MutableMapping[str, Any]],
    example_metadata: Mapping[str, Mapping[str, Any]],
    output_dir: Path,
    summary_format: str,
) -> Dict[str, Path]:
    formats = _resolve_summary_formats(summary_format)
    if not formats or not results:
        return {}

    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base_name = f"example_validation_{timestamp}"
    artifacts: Dict[str, Path] = {}

    if "json" in formats:
        json_path = output_dir / f"{base_name}.json"
        json_payload = {
            "generated_at": timestamp,
            "summary": summary_stats,
            "examples": [
                {
                    "key": key,
                    "name": record.get("name"),
                    "success": record.get("success"),
                    "error": record.get("error"),
                    "execution_time": record.get("execution_time"),
                    "validation": record.get("validation"),
                }
                for key, record in results.items()
            ],
            "runner_history": list(runner_history),
        }
        json_path.write_text(json.dumps(json_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        artifacts["json"] = json_path

    if "tsv" in formats:
        tsv_path = output_dir / f"{base_name}.tsv"
        headers = [
            "example_key",
            "name",
            "success",
            "execution_time_s",
            "validated",
            "valid",
            "issues",
            "time_steps",
            "variables_checked",
            "length_mismatches",
            "non_finite_values",
            "bounds_violations",
            "reasonableness_score",
            "reasonableness_penalties",
            "mass_balance_checked",
            "mass_balance_pass",
            "mass_balance_max_rel_error",
            "mass_balance_mean_rel_error",
            "mass_balance_reason",
        ]
        rows = ["\t".join(headers)]
        for key, record in results.items():
            validation = record.get("validation") or {}
            metrics = validation.get("metrics") or {}
            issues = validation.get("issues") or []
            mass_balance = metrics.get("mass_balance") or {}
            mass_checked = bool(mass_balance.get("checked"))
            mass_pass = mass_balance.get("pass") if mass_checked else None
            mass_max_rel = (
                f"{mass_balance.get('max_relative_error', 0.0):.6f}"
                if mass_checked
                else ""
            )
            mass_mean_rel = (
                f"{mass_balance.get('mean_relative_error', 0.0):.6f}"
                if mass_checked
                else ""
            )
            mass_reason = ""
            if mass_checked:
                mass_reason = mass_balance.get("issue", "")
            elif mass_balance:
                mass_reason = mass_balance.get("reason", "")
            reason_metrics = metrics.get("reasonableness") or {}
            reason_score = reason_metrics.get("score")
            penalties = reason_metrics.get("penalties") or []

            def _format_penalty(entry: Mapping[str, Any]) -> str:
                severity = str(entry.get("severity", "")).upper()
                code = entry.get("code")
                message = entry.get("message", "")
                label_parts = [part for part in (severity, str(code) if code else "") if part]
                label = "/".join(label_parts)
                if label and message:
                    return f"[{label}] {message}"
                if label:
                    return f"[{label}]"
                return message

            penalty_text = " | ".join(_format_penalty(p) for p in penalties if p)
            if reason_score is None or not isinstance(reason_score, (int, float)):
                reason_score_text = ""
            else:
                reason_score_text = f"{float(reason_score):.3f}"
            rows.append(
                "\t".join(
                    [
                        key,
                        str(record.get("name") or ""),
                        "PASS" if record.get("success") else "FAIL",
                        f"{record.get('execution_time'):.3f}" if isinstance(record.get("execution_time"), (int, float)) else "",
                        "yes" if validation.get("validated") else "no",
                        "yes" if validation.get("valid") else ("no" if validation.get("validated") else ""),
                        " | ".join(str(issue) for issue in issues),
                        str(metrics.get("time_steps", "")),
                        str(metrics.get("variables_checked", "")),
                        str(metrics.get("length_mismatches", "")),
                        str(metrics.get("non_finite_values", "")),
                        str(metrics.get("bounds_violations", "")),
                        reason_score_text,
                        penalty_text,
                        "yes" if mass_checked else ("no" if mass_balance else ""),
                        "yes" if mass_checked and mass_pass else ("no" if mass_checked else ""),
                        mass_max_rel,
                        mass_mean_rel,
                        mass_reason,
                    ]
                )
            )
        tsv_path.write_text("\n".join(rows), encoding="utf-8")
        artifacts["tsv"] = tsv_path

    if "markdown" in formats:
        reports_dir = output_dir / f"{base_name}_reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        index_lines = [
            "# 示例验证报告汇总",
            "",
            f"- 生成时间：{timestamp}",
            "",
            "| 示例 | 状态 | 合理性得分 | 报告 |",
            "| --- | --- | --- | --- |",
        ]

        for key, record in results.items():
            metadata = example_metadata.get(key, {}) if example_metadata else {}
            safe_key = key.replace("/", "_")
            report_path = reports_dir / f"{safe_key}.md"
            report_content = _render_example_markdown(key, record, metadata, summary_stats)
            report_path.write_text(report_content, encoding="utf-8")

            display_name = str(metadata.get("name") or record.get("name") or key)
            status_text = "通过" if record.get("success") else "失败"
            validation = record.get("validation") or {}
            metrics = validation.get("metrics") or {}
            reason_metrics = metrics.get("reasonableness") or {}
            reason_score = None
            if isinstance(reason_metrics, Mapping):
                candidate = reason_metrics.get("score")
                if isinstance(candidate, (int, float)):
                    reason_score = float(candidate)
            reason_display = f"{reason_score:.3f}" if isinstance(reason_score, float) else "-"
            relative_path = f"./{reports_dir.name}/{report_path.name}"
            index_lines.append(
                f"| {display_name} | {status_text} | {reason_display} | [查看报告]({relative_path}) |"
            )

        index_path = output_dir / f"{base_name}_summary.md"
        index_path.write_text("\n".join(index_lines), encoding="utf-8")
        artifacts["markdown"] = index_path

    return artifacts


def _print_summary(summary_stats: Mapping[str, Any]) -> None:
    print("=== TEST SUMMARY ===")
    print(f"Total planned: {summary_stats['planned_total']}")
    print(f"Executed: {summary_stats['executed_total']}")
    print(f"Successful: {summary_stats['success_count']}")
    print(f"Failed: {summary_stats['failure_count']}")
    success_rate = 0.0
    if summary_stats["executed_total"]:
        success_rate = summary_stats["success_count"] / summary_stats["executed_total"] * 100.0
    print(f"Success rate: {success_rate:.1f}%\n")

    validation = summary_stats["validation"]
    print(
        "Validation (auto checks): "
        f"{validation['validation_pass']}/{validation['validated_total']} passed, "
        f"{validation['validation_fail']} failed, "
        f"{validation['validation_skipped']} skipped\n"
    )
    metrics_summary = summary_stats.get("metrics") or {}
    mass_balance_summary = metrics_summary.get("mass_balance") or {}
    mass_checked = mass_balance_summary.get("checked_total", 0)
    mass_failed = mass_balance_summary.get("failed", 0)
    mass_skipped = mass_balance_summary.get("skipped", 0)
    if mass_checked or mass_skipped:
        print(
            "质量守恒检查: "
            f"已执行 {mass_checked} 个示例，其中 {mass_failed} 个失败，"
            f"{mass_skipped} 个跳过\n"
        )
    reason_summary = metrics_summary.get("reasonableness") or {}
    scored_total = reason_summary.get("scored_total", 0)
    missing_total = reason_summary.get("missing", 0)
    if scored_total or missing_total:
        avg_score = reason_summary.get("average_score")
        min_score = reason_summary.get("min_score")
        below_threshold = reason_summary.get("below_threshold", 0)
        print("合理性评分统计:")
        print(f"    已评估 {scored_total} 个示例，低于0.5的有 {below_threshold} 个")
        if isinstance(avg_score, (int, float)):
            print(f"    平均得分: {avg_score:.3f}")
        if isinstance(min_score, (int, float)):
            print(f"    最低得分: {min_score:.3f}")
        severity_counts = reason_summary.get("penalty_counts") or {}
        if any(severity_counts.values()):
            details = ", ".join(
                f"{level}: {count}"
                for level, count in severity_counts.items()
                if count
            )
            if details:
                print(f"    处罚级别统计: {details}")
        if missing_total:
            print(f"    有 {missing_total} 个示例缺少合理性评分数据")
        print("")
    if summary_stats.get("fail_fast_triggered"):
        print(
            "[WARN] Fail-fast triggered. "
            f"Skipped {summary_stats['skipped_due_to_fail_fast']} remaining examples.\n"
        )


def run_examples(
    runner: ExamplesHardcodedRunner,
    selected_examples: Sequence[Tuple[str, str]],
    *,
    fail_fast: bool = False,
) -> Tuple[OrderedDict[str, Dict[str, Any]], Dict[str, Any]]:
    runner.reset_history()
    planned_total = len(selected_examples)
    results: OrderedDict[str, Dict[str, Any]] = OrderedDict()
    fail_fast_triggered = False

    print("=== 开始自动测试所有示例 ===")
    print(f"总共需要测试 {planned_total} 个示例\n")

    for index, (example_key, example_name) in enumerate(selected_examples, 1):
        print(f"[{index}/{planned_total}] 测试示例: {example_name} ({example_key})")
        success = runner.run_example(example_key)
        summary = dict(runner.last_run_summary or {})
        validation_info = summary.get("validation", {}) if isinstance(summary, dict) else {}

        record = {
            "name": example_name,
            "success": success,
            "error": summary.get("error"),
            "validation": validation_info,
            "execution_time": summary.get("execution_time"),
            "summary": summary,
        }
        results[example_key] = record

        status = "[PASS]" if success else "[FAIL]"
        print(f"Result: {status}\n")

        if validation_info:
            if validation_info.get("validated"):
                if validation_info.get("valid"):
                    metrics = validation_info.get("metrics", {})
                    time_steps = metrics.get("time_steps", "n/a")
                    checked = metrics.get("variables_checked", 0)
                    print(f"    验证: [PASS] time_steps={time_steps}, variables_checked={checked}")
                else:
                    print("    验证: [FAIL]")
                    for issue in validation_info.get("issues", []):
                        print(f"      - {issue}")
            else:
                issues = validation_info.get("issues", [])
                reason = "; ".join(issues) if issues else "未提供原因"
                print(f"    验证: [SKIP] {reason}")

        if fail_fast and not success:
            remaining = planned_total - index
            if remaining > 0:
                print(f"Fail-fast 已触发，剩余 {remaining} 个示例被跳过。\n")
            fail_fast_triggered = True
            break

    summary_stats = _compute_summary(results, planned_total, fail_fast_triggered)
    _print_summary(summary_stats)

    print("Detailed results:")
    for example_key, record in results.items():
        status = "[PASS]" if record.get("success") else "[FAIL]"
        print(f"  {status} {record.get('name')} ({example_key})")
        if record.get("error"):
            print(f"    Error: {record['error']}")
        validation = record.get("validation") or {}
        if validation:
            if validation.get("validated"):
                v_status = "PASS" if validation.get("valid") else "FAIL"
                metrics = validation.get("metrics", {}) or {}
                details = []
                if metrics.get("time_steps") is not None:
                    details.append(f"time_steps={metrics.get('time_steps')}")
                if metrics.get("variables_checked") is not None:
                    details.append(f"variables_checked={metrics.get('variables_checked')}")
                if metrics.get("bounds_violations"):
                    details.append(f"bounds_violations={metrics.get('bounds_violations')}")
                mass_balance = metrics.get("mass_balance") or {}
                if mass_balance.get("checked"):
                    details.append(
                        "mass_balance_max_rel="
                        f"{mass_balance.get('max_relative_error', 0.0):.2%}"
                    )
                elif mass_balance.get("reason"):
                    details.append(f"mass_balance={mass_balance['reason']}")
                details_str = f" ({', '.join(details)})" if details else ""
                print(f"    Validation: {v_status}{details_str}")
                if validation.get("issues") and not validation.get("valid"):
                    for issue in validation["issues"]:
                        print(f"      Issue: {issue}")
            else:
                issues = validation.get("issues", [])
                reason = "; ".join(issues) if issues else "未提供原因"
                print(f"    Validation: SKIP - {reason}")

    return results, summary_stats


def test_all_examples() -> Mapping[str, Dict[str, Any]]:
    """测试所有示例并返回执行结果字典."""
    runner = ExamplesHardcodedRunner()
    results, _ = run_examples(runner, EXAMPLE_CATALOG)
    return results


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行并验证 CHS-SDK 全量示例")
    parser.add_argument("--list", action="store_true", help="仅列出可用示例并退出")
    parser.add_argument("--only", nargs="*", help="仅运行指定示例（使用示例键）")
    parser.add_argument("--skip", nargs="*", help="跳过指定示例（使用示例键）")
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="遇到首个失败后立即停止，剩余示例标记为未执行",
    )
    parser.add_argument(
        "--summary-format",
        choices=sorted(SUMMARY_FORMAT_CHOICES),
        default="all",
        help="生成结果摘要的格式（默认同时输出 JSON/TSV/Markdown）",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_SUMMARY_DIR,
        help="摘要文件输出目录 (默认: reports/test_runs/examples)",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    if args.list:
        print("可用示例列表：")
        for key, name in EXAMPLE_CATALOG:
            print(f"  - {key}: {name}")
        return 0

    selected_examples = _select_examples(args.only or [], args.skip or [])

    runner = ExamplesHardcodedRunner()
    results, summary_stats = run_examples(runner, selected_examples, fail_fast=args.fail_fast)

    artifacts = _persist_summary(
        results,
        summary_stats,
        runner.get_run_history(),
        runner.get_all_examples_metadata(),
        args.output_dir,
        args.summary_format,
    )

    if artifacts:
        print("\nSummary artifacts:")
        for fmt, path in artifacts.items():
            print(f"  {fmt.upper()}: {path}")

    return 0 if summary_stats["failure_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
