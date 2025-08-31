import React from 'react';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import SimulationApp from './components/SimulationApp';
import './App.css';

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <div className="App">
        <SimulationApp />
      </div>
    </ConfigProvider>
  );
}

export default App;
