#!/usr/bin/env python3
"""
Common Agent Classes - Reusable agent implementations for typical simulation patterns.

This module provides commonly used agent types that appear across multiple examples,
reducing code duplication and providing consistent implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
from core_lib.core.interfaces import Agent

class ScheduledEventAgent(Agent):
    """
    An agent that triggers events at scheduled times.
    
    This is useful for simulating external disturbances, demand changes,
    or other time-based events in simulations.
    """
    
    def __init__(self, agent_id: str, message_bus, events: Dict[float, Dict[str, Any]]):
        """
        Initialize the scheduled event agent.
        
        Args:
            agent_id: Unique identifier for the agent
            message_bus: Message bus for publishing events
            events: Dictionary mapping time -> event data
                   Format: {time: {'topic': 'topic_name', 'data': {...}}}
        """
        super().__init__(agent_id)
        self.bus = message_bus
        self.events = events
        self.triggered_events = set()
    
    def run(self, current_time: float):
        """
        Check for and trigger any scheduled events at the current time.
        
        Args:
            current_time: Current simulation time
        """
        # Check for events at this time (with small tolerance for floating point)
        for event_time, event_data in self.events.items():
            if (abs(current_time - event_time) < 0.01 and 
                event_time not in self.triggered_events):
                
                topic = event_data.get('topic')
                data = event_data.get('data', {})
                
                if topic:
                    self.bus.publish(topic, data)
                    print(f"--- {self.agent_id}: Event triggered at t={current_time}s on topic '{topic}' ---")
                    self.triggered_events.add(event_time)

class DemandAgent(ScheduledEventAgent):
    """
    A specialized agent for simulating demand changes over time.
    
    This agent publishes demand values at scheduled times, commonly used
    in pump station and flow control simulations.
    """
    
    def __init__(self, agent_id: str, message_bus, demand_topic: str, 
                 demand_schedule: Dict[float, float]):
        """
        Initialize the demand agent.
        
        Args:
            agent_id: Unique identifier for the agent
            message_bus: Message bus for publishing demand changes
            demand_topic: Topic name for demand publications
            demand_schedule: Dictionary mapping time -> demand value
        """
        # Convert demand schedule to event format
        events = {
            time: {
                'topic': demand_topic,
                'data': {'value': demand}
            }
            for time, demand in demand_schedule.items()
        }
        
        super().__init__(agent_id, message_bus, events)
        self.demand_topic = demand_topic
    
    def run(self, current_time: float):
        """
        Check for and publish demand changes.
        
        Args:
            current_time: Current simulation time
        """
        super().run(current_time)

class DisturbanceAgent(ScheduledEventAgent):
    """
    A specialized agent for simulating external disturbances.
    
    This agent can simulate rainfall, equipment failures, or other
    external events that affect the simulation.
    """
    
    def __init__(self, agent_id: str, message_bus, disturbance_topic: str,
                 disturbance_schedule: Dict[float, Dict[str, Any]]):
        """
        Initialize the disturbance agent.
        
        Args:
            agent_id: Unique identifier for the agent
            message_bus: Message bus for publishing disturbances
            disturbance_topic: Topic name for disturbance publications
            disturbance_schedule: Dictionary mapping time -> disturbance data
        """
        # Convert disturbance schedule to event format
        events = {
            time: {
                'topic': disturbance_topic,
                'data': disturbance_data
            }
            for time, disturbance_data in disturbance_schedule.items()
        }
        
        super().__init__(agent_id, message_bus, events)
        self.disturbance_topic = disturbance_topic

class MonitoringAgent(Agent):
    """
    An agent that monitors component states and logs information.
    
    This agent can be used to track system performance, detect anomalies,
    or simply log simulation data at regular intervals.
    """
    
    def __init__(self, agent_id: str, components: Dict[str, Any], 
                 monitoring_interval: float = 10.0,
                 log_callback: Optional[Callable] = None):
        """
        Initialize the monitoring agent.
        
        Args:
            agent_id: Unique identifier for the agent
            components: Dictionary of component_id -> component to monitor
            monitoring_interval: Time interval between monitoring checks
            log_callback: Optional callback function for custom logging
        """
        super().__init__(agent_id)
        self.components = components
        self.monitoring_interval = monitoring_interval
        self.log_callback = log_callback
        self.last_check_time = 0
        self.monitoring_data = []
    
    def run(self, current_time: float):
        """
        Check if it's time to monitor components and log their states.
        
        Args:
            current_time: Current simulation time
        """
        if current_time - self.last_check_time >= self.monitoring_interval:
            self._monitor_components(current_time)
            self.last_check_time = current_time
    
    def _monitor_components(self, current_time: float):
        """
        Monitor all registered components and log their states.
        
        Args:
            current_time: Current simulation time
        """
        monitoring_entry = {'time': current_time}
        
        for component_id, component in self.components.items():
            try:
                state = component.get_state()
                monitoring_entry[component_id] = state
                
                # Log key metrics
                if hasattr(component, 'get_state'):
                    self._log_component_metrics(component_id, state, current_time)
                    
            except Exception as e:
                print(f"Warning: Could not monitor component {component_id}: {e}")
        
        self.monitoring_data.append(monitoring_entry)
        
        # Call custom log callback if provided
        if self.log_callback:
            self.log_callback(monitoring_entry)
    
    def _log_component_metrics(self, component_id: str, state: Dict[str, Any], 
                              current_time: float):
        """
        Log key metrics for a component.
        
        Args:
            component_id: Component identifier
            state: Component state dictionary
            current_time: Current simulation time
        """
        # Log common metrics based on component type
        if 'water_level' in state:
            level = state['water_level']
            print(f"[{current_time:.1f}s] {component_id} water level: {level:.2f} m")
        
        if 'outflow' in state:
            outflow = state['outflow']
            print(f"[{current_time:.1f}s] {component_id} outflow: {outflow:.2f} m³/s")
        
        if 'power' in state:
            power = state['power']
            print(f"[{current_time:.1f}s] {component_id} power: {power:.2f} MW")
        
        if 'active_pumps' in state:
            active = state['active_pumps']
            total_flow = state.get('total_outflow', 0)
            print(f"[{current_time:.1f}s] {component_id} active pumps: {active}, "
                  f"total flow: {total_flow:.2f} m³/s")
    
    def get_monitoring_data(self) -> list:
        """
        Get all collected monitoring data.
        
        Returns:
            List of monitoring entries
        """
        return self.monitoring_data

class ThresholdAlarmAgent(MonitoringAgent):
    """
    An agent that monitors components and triggers alarms when thresholds are exceeded.
    
    This agent extends the monitoring agent to provide alarm functionality
    for safety-critical applications.
    """
    
    def __init__(self, agent_id: str, components: Dict[str, Any],
                 thresholds: Dict[str, Dict[str, tuple]],
                 message_bus=None, alarm_topic: str = "system.alarms",
                 monitoring_interval: float = 1.0):
        """
        Initialize the threshold alarm agent.
        
        Args:
            agent_id: Unique identifier for the agent
            components: Dictionary of component_id -> component to monitor
            thresholds: Dictionary of component_id -> {metric: (min, max)}
            message_bus: Message bus for publishing alarms
            alarm_topic: Topic for alarm publications
            monitoring_interval: Time interval between checks
        """
        super().__init__(agent_id, components, monitoring_interval)
        self.thresholds = thresholds
        self.message_bus = message_bus
        self.alarm_topic = alarm_topic
        self.active_alarms = set()
    
    def _monitor_components(self, current_time: float):
        """
        Monitor components and check for threshold violations.
        
        Args:
            current_time: Current simulation time
        """
        super()._monitor_components(current_time)
        
        # Check thresholds
        for component_id, component in self.components.items():
            if component_id in self.thresholds:
                self._check_thresholds(component_id, component, current_time)
    
    def _check_thresholds(self, component_id: str, component: Any, 
                         current_time: float):
        """
        Check if component metrics exceed defined thresholds.
        
        Args:
            component_id: Component identifier
            component: Component object
            current_time: Current simulation time
        """
        try:
            state = component.get_state()
            component_thresholds = self.thresholds[component_id]
            
            for metric, (min_val, max_val) in component_thresholds.items():
                if metric in state:
                    value = state[metric]
                    alarm_key = f"{component_id}.{metric}"
                    
                    # Check for violations
                    if value < min_val or value > max_val:
                        if alarm_key not in self.active_alarms:
                            self._trigger_alarm(component_id, metric, value, 
                                              min_val, max_val, current_time)
                            self.active_alarms.add(alarm_key)
                    else:
                        # Clear alarm if value is back in range
                        if alarm_key in self.active_alarms:
                            self._clear_alarm(component_id, metric, current_time)
                            self.active_alarms.remove(alarm_key)
                            
        except Exception as e:
            print(f"Error checking thresholds for {component_id}: {e}")
    
    def _trigger_alarm(self, component_id: str, metric: str, value: float,
                      min_val: float, max_val: float, current_time: float):
        """
        Trigger an alarm for a threshold violation.
        
        Args:
            component_id: Component identifier
            metric: Metric name
            value: Current value
            min_val: Minimum threshold
            max_val: Maximum threshold
            current_time: Current simulation time
        """
        alarm_data = {
            'component_id': component_id,
            'metric': metric,
            'value': value,
            'min_threshold': min_val,
            'max_threshold': max_val,
            'time': current_time,
            'severity': 'HIGH' if value < min_val * 0.5 or value > max_val * 1.5 else 'MEDIUM'
        }
        
        print(f"*** ALARM *** [{current_time:.1f}s] {component_id}.{metric} = {value:.2f} "
              f"(thresholds: {min_val:.2f} - {max_val:.2f})")
        
        if self.message_bus:
            self.message_bus.publish(self.alarm_topic, alarm_data)
    
    def _clear_alarm(self, component_id: str, metric: str, current_time: float):
        """
        Clear an alarm when the value returns to normal range.
        
        Args:
            component_id: Component identifier
            metric: Metric name
            current_time: Current simulation time
        """
        print(f"--- ALARM CLEARED --- [{current_time:.1f}s] {component_id}.{metric}")
        
        if self.message_bus:
            clear_data = {
                'component_id': component_id,
                'metric': metric,
                'time': current_time,
                'status': 'CLEARED'
            }
            self.message_bus.publish(self.alarm_topic, clear_data)