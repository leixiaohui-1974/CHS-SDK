# -*- coding: utf-8 -*-

"""
This package contains Agent prototypes for integrating Large Language Models (LLMs)
into the water management simulation system. Each agent corresponds to a specific
role defined in the LLM integration strategy, enabling capabilities like
natural language-based system building, scenario design, high-level command execution,
and automated data analysis.

These agents are designed to be extended with actual LLM API calls.
"""

from .llm_system_builder_agent import LLMSystemBuilderAgent
from .llm_scenario_designer_agent import LLMScenarioDesignerAgent
from .llm_dispatch_commander_agent import LLMDispatchCommanderAgent
from .llm_data_analyst_agent import LLMDataAnalystAgent

__all__ = [
    'LLMSystemBuilderAgent',
    'LLMScenarioDesignerAgent',
    'LLMDispatchCommanderAgent',
    'LLMDataAnalystAgent'
]
