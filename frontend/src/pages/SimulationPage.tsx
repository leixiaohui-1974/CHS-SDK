import React, { useState, useEffect, useRef } from 'react';
import { useProjectStore } from '../store/projectStore';
import { Empty, Button, Card, Spin, message } from 'antd';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';
const WS_BASE_URL = 'ws://localhost:8000/ws';

type SimulationDataPoint = {
  timestamp: number;
  water_level: number;
};

const SimulationPage: React.FC = () => {
  const { projectConfig } = useProjectStore();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [simulationData, setSimulationData] = useState<SimulationDataPoint[]>([]);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Cleanup WebSocket on component unmount
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);

  const handleStart = async () => {
    if (!projectConfig) {
      message.error("No project is loaded!");
      return;
    }
    setIsLoading(true);
    setSimulationData([]);

    try {
      // 1. Create simulation session
      const createResponse = await axios.post(`${API_BASE_URL}/simulations`, projectConfig);
      const newSessionId = createResponse.data.session_id;
      setSessionId(newSessionId);

      // 2. Open WebSocket connection
      ws.current = new WebSocket(`${WS_BASE_URL}/simulations/${newSessionId}`);
      ws.current.onmessage = (event) => {
        const message = JSON.parse(event.data);
        if (message.type === 'data') {
          setSimulationData(prevData => [...prevData, message.payload]);
        } else if (message.type === 'status') {
          console.log('Simulation status:', message.payload);
          if (message.payload.includes('finished')) {
            setIsRunning(false);
          }
        } else if (message.type === 'error') {
            console.error('Simulation error:', message.payload);
            message.error(`Simulation error: ${message.payload}`);
            setIsRunning(false);
        }
      };
      ws.current.onopen = async () => {
        // 3. Start the simulation
        await axios.post(`${API_BASE_URL}/simulations/${newSessionId}/start`);
        setIsRunning(true);
        setIsLoading(false);
        message.success("Simulation started!");
      };
       ws.current.onerror = (err) => {
        console.error("WebSocket error:", err);
        message.error("Failed to connect to simulation server.");
        setIsLoading(false);
      };

    } catch (error) {
      console.error("Failed to start simulation:", error);
      message.error("Failed to start simulation.");
      setIsLoading(false);
    }
  };

  const handleStop = async () => {
    if (!sessionId) return;
    try {
      await axios.post(`${API_BASE_URL}/simulations/${sessionId}/stop`);
      ws.current?.close();
      setIsRunning(false);
      message.info("Simulation stopped.");
    } catch (error) {
      console.error("Failed to stop simulation:", error);
      message.error("Failed to stop simulation.");
    }
  };

  if (!projectConfig) {
    return <Empty description="Please load a project from the Modeling page first." />;
  }

  return (
    <Card title="Simulation Control & Visualization">
      <div style={{ marginBottom: '20px' }}>
        <Spin spinning={isLoading}>
          <Button type="primary" onClick={handleStart} disabled={isRunning || isLoading} style={{ marginRight: '10px' }}>
            Start Simulation
          </Button>
          <Button type="default" danger onClick={handleStop} disabled={!isRunning}>
            Stop Simulation
          </Button>
        </Spin>
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={simulationData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="timestamp" label={{ value: 'Time (s)', position: 'insideBottom', offset: -5 }}/>
          <YAxis label={{ value: 'Water Level (m)', angle: -90, position: 'insideLeft' }}/>
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="water_level" stroke="#8884d8" isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
};

export default SimulationPage;
