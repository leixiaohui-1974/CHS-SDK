#!/usr/bin/env python3
"""
Simulation Builder - A utility class to simplify simulation setup and reduce code duplication.

This module provides a high-level interface for creating common simulation patterns,
reducing the boilerplate code needed in individual examples.
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from core_lib.core_engine.testing.simulation_harness import SimulationHarness
from core_lib.physical_objects.reservoir import Reservoir
from core_lib.physical_objects.gate import Gate
from core_lib.physical_objects.pump import Pump, PumpStation
from core_lib.physical_objects.water_turbine import WaterTurbine
from core_lib.core.interfaces import Agent

class SimulationBuilder:
    """
    A builder class that simplifies the creation of common simulation patterns.
    
    This class encapsulates the repetitive setup code found across multiple examples,
    providing a cleaner API for simulation creation.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the simulation builder.
        
        Args:
            config: Simulation configuration dictionary. Must include 'end_time'.
        """
        # end_time is required - no default value
        if 'end_time' not in config:
            if 'duration' in config:
                # 支持 duration 作为 end_time 的备选参数
                config['end_time'] = config['duration']
            else:
                raise ValueError("'end_time' is required in simulation configuration")
        
        default_config = {
            'start_time': 0,
            'dt': 1.0
        }
        
        # Update with provided config
        default_config.update(config)
            
        self.config = default_config
        self.harness = SimulationHarness(self.config)
        self.components = {}
        self.agents = []
        
    def add_reservoir(self, 
                     component_id: str, 
                     water_level: float = 10.0, 
                     surface_area: float = 1e6,
                     volume: Optional[float] = None) -> Reservoir:
        """
        Add a reservoir component to the simulation.
        
        Args:
            component_id: Unique identifier for the reservoir
            water_level: Initial water level in meters
            surface_area: Surface area in square meters
            volume: Initial volume (calculated from water_level and surface_area if not provided)
            
        Returns:
            The created Reservoir object
        """
        if volume is None:
            volume = water_level * surface_area
            
        initial_state = {
            'water_level': water_level,
            'volume': volume,
            'outflow': 0
        }
        
        parameters = {'surface_area': surface_area}
        
        reservoir = Reservoir(component_id, initial_state, parameters)
        self.harness.add_component(component_id, reservoir)
        self.components[component_id] = reservoir
        
        return reservoir
    
    def add_gate(self, 
                 component_id: str,
                 opening: float = 0.5,
                 max_flow_rate: float = 100.0,
                 control_topic: Optional[str] = None) -> Gate:
        """
        Add a gate component to the simulation.
        
        Args:
            component_id: Unique identifier for the gate
            opening: Initial gate opening (0.0 to 1.0)
            max_flow_rate: Maximum flow rate in m³/s
            control_topic: Message bus topic for control signals
            
        Returns:
            The created Gate object
        """
        initial_state = {'opening': opening, 'outflow': 0}
        parameters = {'max_flow_rate': max_flow_rate}
        
        if control_topic:
            gate = Gate(component_id, initial_state, parameters, 
                       self.harness.message_bus, control_topic)
        else:
            gate = Gate(component_id, initial_state, parameters)
            
        self.harness.add_component(component_id, gate)
        self.components[component_id] = gate
        
        return gate
    
    def add_pump_station(self,
                        component_id: str,
                        num_pumps: int = 3,
                        pump_max_flow: float = 10.0,
                        pump_max_head: float = 20.0,
                        pump_power: float = 50.0,
                        control_topic_prefix: Optional[str] = None) -> PumpStation:
        """
        Add a pump station with multiple pumps to the simulation.
        
        Args:
            component_id: Unique identifier for the pump station
            num_pumps: Number of pumps in the station
            pump_max_flow: Maximum flow rate per pump in m³/s
            pump_max_head: Maximum head per pump in meters
            pump_power: Power consumption per pump in kW
            control_topic_prefix: Prefix for pump control topics
            
        Returns:
            The created PumpStation object
        """
        pump_params = {
            'max_flow_rate': pump_max_flow,
            'max_head': pump_max_head,
            'power_consumption_kw': pump_power
        }
        
        pumps = []
        for i in range(1, num_pumps + 1):
            pump_id = f"p{i}"
            if control_topic_prefix:
                control_topic = f"{control_topic_prefix}.{pump_id}"
                pump = Pump(pump_id, {}, pump_params, 
                           self.harness.message_bus, control_topic)
            else:
                pump = Pump(pump_id, {}, pump_params)
            pumps.append(pump)
        
        pump_station = PumpStation(component_id, {}, {}, pumps)
        self.harness.add_component(component_id, pump_station)
        self.components[component_id] = pump_station
        
        return pump_station
    
    def add_water_turbine(self,
                         component_id: str,
                         efficiency: float = 0.9,
                         max_flow_rate: float = 50.0,
                         target_outflow: Optional[float] = None) -> WaterTurbine:
        """
        Add a water turbine to the simulation.
        
        Args:
            component_id: Unique identifier for the turbine
            efficiency: Turbine efficiency (0.0 to 1.0)
            max_flow_rate: Maximum flow rate in m³/s
            target_outflow: Target outflow rate in m³/s
            
        Returns:
            The created WaterTurbine object
        """
        initial_state = {'power': 0, 'outflow': 0}
        parameters = {
            'efficiency': efficiency,
            'max_flow_rate': max_flow_rate
        }
        
        turbine = WaterTurbine(component_id, initial_state, parameters)
        
        if target_outflow is not None:
            turbine.target_outflow = target_outflow
            
        self.harness.add_component(component_id, turbine)
        self.components[component_id] = turbine
        
        return turbine
    
    def connect_components(self, connections: List[Tuple[str, str]]):
        """
        Add multiple connections between components.
        
        Args:
            connections: List of (upstream_id, downstream_id) tuples
        """
        for upstream_id, downstream_id in connections:
            self.harness.add_connection(upstream_id, downstream_id)
    
    def add_agent(self, agent: Agent):
        """
        Add an agent to the simulation.
        
        Args:
            agent: The agent to add
        """
        self.harness.add_agent(agent)
        self.agents.append(agent)
    
    def build(self):
        """
        Build the simulation harness and prepare for execution.
        """
        self.harness.build()
        print("Simulation builder setup complete.")
    
    def run_mas_simulation(self):
        """
        Run the multi-agent simulation using the harness.
        """
        self.harness.run_mas_simulation()
        # Export output data to CSV files if configured
        if hasattr(self.harness, '_output_configs'):
            self.harness.export_output_data()
    
    def run_simple_simulation(self):
        """
        Run a simple simulation without agents.
        """
        self.harness.run_simulation()
        # Export output data to CSV files if configured
        if hasattr(self.harness, '_output_configs'):
            self.harness.export_output_data()
    
    def get_component(self, component_id: str):
        """
        Get a component by its ID.
        
        Args:
            component_id: The component identifier
            
        Returns:
            The component object
        """
        return self.components.get(component_id)
    
    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get the simulation history.
        
        Returns:
            List of simulation step histories
        """
        return self.harness.history
    
    def print_final_states(self):
        """
        Print the final states of all components.
        """
        print("\n--- Final Component States ---")
        for component_id, component in self.components.items():
            state = component.get_state()
            print(f"{component_id}: {state}")


def create_simple_reservoir_gate_system(config: Optional[Dict[str, Any]] = None) -> SimulationBuilder:
    """
    Create a simple reservoir-gate system - a common pattern in examples.
    
    Args:
        config: Simulation configuration
        
    Returns:
        Configured SimulationBuilder with reservoir and gate
    """
    builder = SimulationBuilder(config)
    
    # Add components
    builder.add_reservoir("reservoir_1", water_level=10.0)
    builder.add_gate("gate_1", opening=0.5, control_topic="action.gate_1")
    
    # Connect components
    builder.connect_components([("reservoir_1", "gate_1")])
    
    return builder


def create_hydropower_system(config: Optional[Dict[str, Any]] = None) -> SimulationBuilder:
    """
    Create a hydropower system - upstream reservoir, turbine, downstream reservoir.
    
    Args:
        config: Simulation configuration
        
    Returns:
        Configured SimulationBuilder with hydropower components
    """
    builder = SimulationBuilder(config)
    
    # Add components
    builder.add_reservoir("source_res", water_level=100.0, surface_area=1e5)
    builder.add_reservoir("downstream_res", water_level=20.0, surface_area=1e5)
    builder.add_water_turbine("turbine_1", target_outflow=30.0)
    
    # Connect components
    builder.connect_components([
        ("source_res", "turbine_1"),
        ("turbine_1", "downstream_res")
    ])
    
    return builder


def create_pump_station_system(config: Optional[Dict[str, Any]] = None) -> SimulationBuilder:
    """
    Create a pump station system - source reservoir, pump station, downstream reservoir.
    
    Args:
        config: Simulation configuration
        
    Returns:
        Configured SimulationBuilder with pump station components
    """
    builder = SimulationBuilder(config)
    
    # Add components
    builder.add_reservoir("source_res", water_level=10.0)
    builder.add_reservoir("downstream_res", water_level=25.0)
    builder.add_pump_station("ps1", num_pumps=3, control_topic_prefix="action.pump")
    
    # Connect components
    builder.connect_components([
        ("source_res", "ps1"),
        ("ps1", "downstream_res")
    ])
    
    return builder