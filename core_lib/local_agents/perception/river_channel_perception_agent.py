# ... existing code ...
from core_lib.local_agents.prediction.forecasting_agent import ForecastingAgent
from core_lib.local_agents.perception.digital_twin_agent import DigitalTwinAgent

class RiverChannelPerceptionAgent(DigitalTwinAgent):
    """
    An enhanced perception agent for a river channel.
    It includes data cleaning, state evaluation, and predictive capabilities.
    """

    def __init__(self, agent_id: str, message_bus, config=None, simulated_object=None, state_topic=None, **kwargs):
        # Handle different parameter formats
        if config is None:
            config = kwargs.get('config', {})
        
        # Set default values if not provided
        if simulated_object is None:
            simulated_object = config.get('target_component', f'{agent_id}_object')
        if state_topic is None:
            state_topic = f'agent.{agent_id}.state'
            
        super().__init__(agent_id, simulated_object, message_bus, state_topic, **kwargs)
        
        # --- Enhanced Features Initialization ---

        # 1. Data Cleaner (simplified)
        self.cleaner_config = config.get('cleaner_config', None)
        self.cleaner = None  # Simplified for now

        # 2. State Evaluation
        self.evaluation_config = config.get('evaluation_config', None)
        if self.evaluation_config:
            self.control_target_level = None
            self._subscribe(self.evaluation_config['target_topic'], self._on_target_update)

        # 3. Prediction
        self.prediction_config = config.get('prediction_config', None)
        if self.prediction_config:
            # This could be expanded to include a dedicated forecaster for inflows
            self.prediction_horizon = self.prediction_config.get('horizon_steps', 12) # e.g., 12 steps of 5 mins = 1 hour
        
        # 4. Time step for prediction calculations
        self.time_step = config.get('time_step', kwargs.get('time_step', 1.0))  # Default to 1.0 seconds

    def _on_input_data(self, topic: str, data: any):
        """Override to clean data before processing."""
        # Data cleaning simplified for now
        # if self.cleaner:
        #     data = self.cleaner.clean(data)
        super()._on_input_data(topic, data)

    def _on_target_update(self, topic, data):
        self.control_target_level = data

    def step(self, t):
        super().step(t) # This will update the digital twin's state

        if self.evaluation_config:
            self._evaluate_state()
        
        if self.prediction_config:
            self._predict_future_state()

    def _evaluate_state(self):
        """
        Evaluates the current state of the channel against control targets.
        """
        if self.control_target_level is not None and hasattr(self.digital_twin, 'water_level'):
            current_level = self.digital_twin.water_level
            deviation = current_level - self.control_target_level
            
            evaluation_metrics = {
                'deviation': deviation,
                'absolute_deviation': abs(deviation),
                'deviation_percentage': (deviation / self.control_target_level) * 100 if self.control_target_level != 0 else 0
            }
            
            self._publish(f'agent.{self.name}.state_evaluation', evaluation_metrics)

    def _predict_future_state(self):
        """
        Predicts future water level, flow, and volume using the internal simplified model.
        """
        if not hasattr(self.digital_twin, 'step'):
            return 
            
        # Create a temporary copy of the model for prediction
        import copy
        prediction_model = copy.deepcopy(self.digital_twin)
        
        # Assume current inflow and outflow persist for a simple prediction
        # A more advanced version would use a ForecastingAgent for inflows
        last_inflow = self.input_data.get(self.input_topics[0], 0) if self.input_topics else 0
        
        predicted_levels = []
        predicted_flows = []
        
        for _ in range(self.prediction_horizon):
            prediction_model.step(last_inflow, self.time_step)
            predicted_levels.append(prediction_model.water_level)
            predicted_flows.append(prediction_model.outflow)

        prediction_output = {
            'water_levels': predicted_levels,
            'outflows': predicted_flows,
            'horizon_seconds': self.prediction_horizon * self.time_step
        }
        self._publish(f'agent.{self.name}.prediction', prediction_output)
