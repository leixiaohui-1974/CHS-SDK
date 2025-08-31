import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Card, Button, Progress, Statistic, Row, Col, Space, Alert, Divider, Select, InputNumber, Switch } from 'antd';
import { PlayCircleOutlined, PauseCircleOutlined, StopOutlined, StepForwardOutlined, ReloadOutlined, SettingOutlined } from '@ant-design/icons';
import { useModelingStore } from '../store/modelingStore';

interface SimulationState {
  isRunning: boolean;
  isPaused: boolean;
  currentTime: number;
  totalTime: number;
  timeStep: number;
  progress: number;
  iterationsPerSecond: number;
  lastError?: string;
}

interface SimulationConfig {
  totalTime: number;
  timeStep: number;
  realTimeMode: boolean;
  maxIterationsPerSecond: number;
  autoSave: boolean;
  saveInterval: number;
}

interface ComponentState {
  id: string;
  type: string;
  state: Record<string, number>;
  lastUpdated: number;
}

const SimulationEngine: React.FC = () => {
  const { nodes, edges, projectConfig } = useModelingStore();
  
  const [simulationState, setSimulationState] = useState<SimulationState>({
    isRunning: false,
    isPaused: false,
    currentTime: 0,
    totalTime: 3600, // 1 hour default
    timeStep: 1.0, // 1 second default
    progress: 0,
    iterationsPerSecond: 0
  });

  const [config, setConfig] = useState<SimulationConfig>({
    totalTime: 3600,
    timeStep: 1.0,
    realTimeMode: false,
    maxIterationsPerSecond: 100,
    autoSave: true,
    saveInterval: 300 // 5 minutes
  });

  const [componentStates, setComponentStates] = useState<ComponentState[]>([]);
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);
  
  const simulationWorkerRef = useRef<Worker | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const lastUpdateTimeRef = useRef<number>(Date.now());
  const iterationCountRef = useRef<number>(0);

  // Initialize component states from nodes
  useEffect(() => {
    const initialStates: ComponentState[] = nodes.map(node => ({
      id: node.id,
      type: node.type,
      state: getInitialStateForComponent(node.type, node.data?.parameters || {}),
      lastUpdated: Date.now()
    }));
    setComponentStates(initialStates);
  }, [nodes]);

  // Get initial state based on component type
  const getInitialStateForComponent = (type: string, parameters: Record<string, any>): Record<string, number> => {
    switch (type) {
      case 'reservoir':
        return {
          water_level: parameters.initial_level || 10.0,
          volume: parameters.initial_volume || 1000000,
          inflow: 0,
          outflow: 0
        };
      case 'pipe':
        return {
          flow_rate: 0,
          pressure_drop: 0,
          velocity: 0
        };
      case 'pump':
        return {
          flow_rate: 0,
          head: 0,
          power: 0,
          efficiency: parameters.efficiency || 0.85
        };
      case 'valve':
        return {
          opening: parameters.initial_opening || 0.5,
          flow_rate: 0,
          pressure_drop: 0
        };
      case 'gate':
        return {
          opening: parameters.initial_opening || 1.0,
          flow_rate: 0,
          upstream_level: 0,
          downstream_level: 0
        };
      default:
        return {};
    }
  };

  // Simulation step calculation
  const calculateSimulationStep = useCallback((states: ComponentState[], dt: number): ComponentState[] => {
    const newStates = [...states];
    const currentTime = simulationState.currentTime;

    // Build topology map from edges
    const topology = new Map<string, string[]>();
    const inverseTopology = new Map<string, string[]>();
    
    edges.forEach(edge => {
      if (!topology.has(edge.source)) topology.set(edge.source, []);
      if (!inverseTopology.has(edge.target)) inverseTopology.set(edge.target, []);
      
      topology.get(edge.source)!.push(edge.target);
      inverseTopology.get(edge.target)!.push(edge.source);
    });

    // Topological sort for correct update order
    const sortedIds = topologicalSort(Array.from(new Set([...nodes.map(n => n.id)])), topology);

    // Update each component in topological order
    sortedIds.forEach(nodeId => {
      const stateIndex = newStates.findIndex(s => s.id === nodeId);
      if (stateIndex === -1) return;

      const currentState = newStates[stateIndex];
      const node = nodes.find(n => n.id === nodeId);
      if (!node) return;

      // Calculate inflows from upstream components
      let totalInflow = 0;
      const upstreamIds = inverseTopology.get(nodeId) || [];
      upstreamIds.forEach(upstreamId => {
        const upstreamState = newStates.find(s => s.id === upstreamId);
        if (upstreamState) {
          totalInflow += upstreamState.state.flow_rate || upstreamState.state.outflow || 0;
        }
      });

      // Update component state based on type
      const updatedState = updateComponentState(
        currentState,
        node.type,
        node.data?.parameters || {},
        totalInflow,
        dt,
        currentTime
      );

      newStates[stateIndex] = {
        ...currentState,
        state: updatedState,
        lastUpdated: Date.now()
      };
    });

    return newStates;
  }, [nodes, edges, simulationState.currentTime]);

  // Update individual component state
  const updateComponentState = (
    componentState: ComponentState,
    type: string,
    parameters: Record<string, any>,
    inflow: number,
    dt: number,
    time: number
  ): Record<string, number> => {
    const state = { ...componentState.state };

    switch (type) {
      case 'reservoir':
        const area = parameters.surface_area || 1000000;
        const maxVolume = parameters.max_volume || 10000000;
        
        // Simple reservoir mass balance
        const netFlow = inflow - (state.outflow || 0);
        const newVolume = Math.max(0, Math.min(maxVolume, state.volume + netFlow * dt));
        const newLevel = newVolume / area;
        
        return {
          ...state,
          volume: newVolume,
          water_level: newLevel,
          inflow: inflow,
          outflow: Math.min(inflow, newVolume / dt) // Prevent negative volume
        };

      case 'pipe':
        const diameter = parameters.diameter || 1.0;
        const length = parameters.length || 1000;
        const roughness = parameters.roughness || 0.001;
        
        // Simplified pipe flow calculation
        const velocity = inflow / (Math.PI * Math.pow(diameter / 2, 2));
        const reynoldsNumber = velocity * diameter / 1e-6; // Assuming water kinematic viscosity
        const frictionFactor = 0.316 / Math.pow(reynoldsNumber, 0.25); // Blasius equation
        const pressureDrop = frictionFactor * (length / diameter) * (velocity * velocity / 2) * 1000; // Assuming water density
        
        return {
          ...state,
          flow_rate: inflow,
          velocity: velocity,
          pressure_drop: pressureDrop
        };

      case 'pump':
        const maxFlow = parameters.max_flow || 100;
        const maxHead = parameters.max_head || 50;
        const efficiency = parameters.efficiency || 0.85;
        
        // Simple pump curve (quadratic)
        const flowRatio = Math.min(1, inflow / maxFlow);
        const head = maxHead * (1 - flowRatio * flowRatio);
        const power = (inflow * head * 9.81 * 1000) / (efficiency * 1000); // kW
        
        return {
          ...state,
          flow_rate: inflow,
          head: head,
          power: power,
          efficiency: efficiency
        };

      case 'valve':
      case 'gate':
        const opening = state.opening || 0.5;
        const dischargeCoeff = parameters.discharge_coefficient || 0.6;
        const width = parameters.width || 2.0;
        
        // Orifice flow equation
        const upstreamLevel = parameters.upstream_level || 10;
        const downstreamLevel = parameters.downstream_level || 0;
        const head = Math.max(0, upstreamLevel - downstreamLevel);
        const flowRate = dischargeCoeff * width * opening * Math.sqrt(2 * 9.81 * head);
        
        return {
          ...state,
          flow_rate: flowRate,
          upstream_level: upstreamLevel,
          downstream_level: downstreamLevel
        };

      default:
        return state;
    }
  };

  // Topological sort implementation
  const topologicalSort = (nodeIds: string[], topology: Map<string, string[]>): string[] => {
    const inDegree = new Map<string, number>();
    const result: string[] = [];
    const queue: string[] = [];

    // Initialize in-degrees
    nodeIds.forEach(id => inDegree.set(id, 0));
    topology.forEach((targets, source) => {
      targets.forEach(target => {
        inDegree.set(target, (inDegree.get(target) || 0) + 1);
      });
    });

    // Find nodes with no incoming edges
    inDegree.forEach((degree, nodeId) => {
      if (degree === 0) queue.push(nodeId);
    });

    // Process queue
    while (queue.length > 0) {
      const current = queue.shift()!;
      result.push(current);

      const neighbors = topology.get(current) || [];
      neighbors.forEach(neighbor => {
        const newDegree = (inDegree.get(neighbor) || 0) - 1;
        inDegree.set(neighbor, newDegree);
        if (newDegree === 0) queue.push(neighbor);
      });
    }

    return result;
  };

  // Animation loop for real-time simulation
  const animationLoop = useCallback(() => {
    if (!simulationState.isRunning || simulationState.isPaused) return;

    const now = Date.now();
    const deltaTime = (now - lastUpdateTimeRef.current) / 1000; // Convert to seconds
    
    if (config.realTimeMode) {
      // Real-time mode: advance simulation time by real elapsed time
      if (deltaTime >= config.timeStep) {
        const newStates = calculateSimulationStep(componentStates, config.timeStep);
        setComponentStates(newStates);
        
        setSimulationState(prev => ({
          ...prev,
          currentTime: prev.currentTime + config.timeStep,
          progress: Math.min(100, (prev.currentTime + config.timeStep) / config.totalTime * 100)
        }));
        
        lastUpdateTimeRef.current = now;
        iterationCountRef.current++;
      }
    } else {
      // Fast mode: run as fast as possible up to max iterations per second
      const targetInterval = 1000 / config.maxIterationsPerSecond;
      if (deltaTime >= targetInterval) {
        const newStates = calculateSimulationStep(componentStates, config.timeStep);
        setComponentStates(newStates);
        
        setSimulationState(prev => ({
          ...prev,
          currentTime: prev.currentTime + config.timeStep,
          progress: Math.min(100, (prev.currentTime + config.timeStep) / config.totalTime * 100)
        }));
        
        lastUpdateTimeRef.current = now;
        iterationCountRef.current++;
      }
    }

    // Update iterations per second
    if (now - lastUpdateTimeRef.current >= 1000) {
      setSimulationState(prev => ({
        ...prev,
        iterationsPerSecond: iterationCountRef.current
      }));
      iterationCountRef.current = 0;
    }

    // Check if simulation is complete
    if (simulationState.currentTime >= config.totalTime) {
      handleStop();
      return;
    }

    animationFrameRef.current = requestAnimationFrame(animationLoop);
  }, [simulationState, config, componentStates, calculateSimulationStep]);

  // Start simulation
  const handleStart = () => {
    if (nodes.length === 0) {
      setSimulationState(prev => ({ ...prev, lastError: 'No components to simulate' }));
      return;
    }

    setSimulationState(prev => ({
      ...prev,
      isRunning: true,
      isPaused: false,
      lastError: undefined
    }));
    
    lastUpdateTimeRef.current = Date.now();
    iterationCountRef.current = 0;
    animationFrameRef.current = requestAnimationFrame(animationLoop);
  };

  // Pause simulation
  const handlePause = () => {
    setSimulationState(prev => ({ ...prev, isPaused: !prev.isPaused }));
  };

  // Stop simulation
  const handleStop = () => {
    setSimulationState(prev => ({
      ...prev,
      isRunning: false,
      isPaused: false
    }));
    
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
  };

  // Reset simulation
  const handleReset = () => {
    handleStop();
    setSimulationState(prev => ({
      ...prev,
      currentTime: 0,
      progress: 0,
      iterationsPerSecond: 0,
      lastError: undefined
    }));
    
    // Reset component states
    const resetStates: ComponentState[] = nodes.map(node => ({
      id: node.id,
      type: node.type,
      state: getInitialStateForComponent(node.type, node.data?.parameters || {}),
      lastUpdated: Date.now()
    }));
    setComponentStates(resetStates);
  };

  // Single step
  const handleStep = () => {
    if (simulationState.isRunning) return;
    
    const newStates = calculateSimulationStep(componentStates, config.timeStep);
    setComponentStates(newStates);
    
    setSimulationState(prev => ({
      ...prev,
      currentTime: prev.currentTime + config.timeStep,
      progress: Math.min(100, (prev.currentTime + config.timeStep) / config.totalTime * 100)
    }));
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  return (
    <Card title="仿真执行引擎" size="small">
      {simulationState.lastError && (
        <Alert
          message="仿真错误"
          description={simulationState.lastError}
          type="error"
          closable
          style={{ marginBottom: 16 }}
          onClose={() => setSimulationState(prev => ({ ...prev, lastError: undefined }))}
        />
      )}
      
      <Row gutter={16}>
        <Col span={12}>
          <Statistic
            title="仿真时间"
            value={simulationState.currentTime.toFixed(1)}
            suffix={`/ ${config.totalTime.toFixed(1)} s`}
          />
        </Col>
        <Col span={12}>
          <Statistic
            title="迭代速度"
            value={simulationState.iterationsPerSecond}
            suffix="iter/s"
          />
        </Col>
      </Row>
      
      <Progress
        percent={simulationState.progress}
        status={simulationState.isRunning ? 'active' : 'normal'}
        style={{ margin: '16px 0' }}
      />
      
      <Space wrap>
        <Button
          type="primary"
          icon={<PlayCircleOutlined />}
          onClick={handleStart}
          disabled={simulationState.isRunning && !simulationState.isPaused}
        >
          开始
        </Button>
        
        <Button
          icon={<PauseCircleOutlined />}
          onClick={handlePause}
          disabled={!simulationState.isRunning}
        >
          {simulationState.isPaused ? '继续' : '暂停'}
        </Button>
        
        <Button
          icon={<StopOutlined />}
          onClick={handleStop}
          disabled={!simulationState.isRunning}
        >
          停止
        </Button>
        
        <Button
          icon={<StepForwardOutlined />}
          onClick={handleStep}
          disabled={simulationState.isRunning}
        >
          单步
        </Button>
        
        <Button
          icon={<ReloadOutlined />}
          onClick={handleReset}
        >
          重置
        </Button>
        
        <Button
          icon={<SettingOutlined />}
          onClick={() => setShowAdvancedSettings(!showAdvancedSettings)}
        >
          设置
        </Button>
      </Space>
      
      {showAdvancedSettings && (
        <>
          <Divider />
          <Row gutter={16}>
            <Col span={6}>
              <div style={{ marginBottom: 8 }}>总时间 (s)</div>
              <InputNumber
                value={config.totalTime}
                onChange={(value) => setConfig(prev => ({ ...prev, totalTime: value || 3600 }))}
                min={1}
                max={86400}
                style={{ width: '100%' }}
              />
            </Col>
            <Col span={6}>
              <div style={{ marginBottom: 8 }}>时间步长 (s)</div>
              <InputNumber
                value={config.timeStep}
                onChange={(value) => setConfig(prev => ({ ...prev, timeStep: value || 1.0 }))}
                min={0.01}
                max={60}
                step={0.1}
                style={{ width: '100%' }}
              />
            </Col>
            <Col span={6}>
              <div style={{ marginBottom: 8 }}>最大迭代速度</div>
              <InputNumber
                value={config.maxIterationsPerSecond}
                onChange={(value) => setConfig(prev => ({ ...prev, maxIterationsPerSecond: value || 100 }))}
                min={1}
                max={1000}
                style={{ width: '100%' }}
              />
            </Col>
            <Col span={6}>
              <div style={{ marginBottom: 8 }}>实时模式</div>
              <Switch
                checked={config.realTimeMode}
                onChange={(checked) => setConfig(prev => ({ ...prev, realTimeMode: checked }))}
              />
            </Col>
          </Row>
        </>
      )}
      
      {componentStates.length > 0 && (
        <>
          <Divider />
          <div style={{ maxHeight: 200, overflowY: 'auto' }}>
            <Row gutter={[8, 8]}>
              {componentStates.map(component => (
                <Col span={8} key={component.id}>
                  <Card size="small" title={`${component.type} (${component.id})`}>
                    {Object.entries(component.state).map(([key, value]) => (
                      <div key={key} style={{ fontSize: '12px' }}>
                        <strong>{key}:</strong> {typeof value === 'number' ? value.toFixed(3) : value}
                      </div>
                    ))}
                  </Card>
                </Col>
              ))}
            </Row>
          </div>
        </>
      )}
    </Card>
  );
};

export default SimulationEngine;