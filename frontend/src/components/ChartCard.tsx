import React from 'react';
import { Card, Button } from 'antd';
import { CloseOutlined } from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { ChartConfig, DataPoint, useSimulationStore } from '../store/simulationStore';

interface ChartCardProps {
  chart: ChartConfig;
  data: DataPoint[];
}

const getRandomColor = () => `#${Math.floor(Math.random()*16777215).toString(16).padStart(6, '0')}`;

const ChartCard: React.FC<ChartCardProps> = ({ chart, data }) => {
  const { removeChart } = useSimulationStore();

  return (
    <Card
      title={`Chart: ${chart.variables.join(', ')}`}
      size="small"
      extra={<Button icon={<CloseOutlined />} onClick={() => removeChart(chart.id)} size="small" />}
      style={{ height: '100%' }}
      bodyStyle={{ height: 'calc(100% - 40px)' }}
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="timestamp" />
          <YAxis />
          <Tooltip />
          <Legend />
          {chart.variables.map(variable => (
            <Line
              key={variable}
              type="monotone"
              dataKey={variable}
              stroke={getRandomColor()}
              isAnimationActive={false}
              dot={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
};

export default ChartCard;
