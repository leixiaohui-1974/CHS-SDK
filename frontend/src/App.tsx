import React from 'react';
import { Routes, Route, useNavigate, useLocation, Navigate } from 'react-router-dom';
import { Layout, Menu, Button, Space } from 'antd';
import { useProjectStore } from './store/projectStore';
import { exportProjectAsZip } from './utils/project-exporter';
import ModelingPage from './pages/ModelingPage';
import SimulationPage from './pages/SimulationPage';
import ProjectLoader from './components/ProjectLoader';

const { Header, Content } = Layout;

const App: React.FC = () => {
  const { projectConfig } = useProjectStore();
  const navigate = useNavigate();
  const location = useLocation();

  const handleExport = () => {
    exportProjectAsZip(projectConfig);
  };

  const handleMenuClick = (e: { key: string }) => {
    navigate(e.key);
  };

  // Determine the selected key from the current path
  const selectedKey = location.pathname;

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div className="logo" style={{ color: 'white', marginRight: '20px' }}>
            CHS-SDK Dashboard
          </div>
          <Menu
            theme="dark"
            mode="horizontal"
            selectedKeys={[selectedKey]}
            onClick={handleMenuClick}
            items={[
              { key: '/modeling', label: 'Modeling' },
              { key: '/simulation', label: 'Simulation' },
            ]}
            style={{ lineHeight: '64px' }}
          />
        </div>
        <Space>
          <ProjectLoader />
          <Button type="primary" onClick={handleExport} disabled={!projectConfig}>
            Export Project
          </Button>
        </Space>
      </Header>
      <Content style={{ padding: '24px' }}>
        <Routes>
          <Route path="/" element={<Navigate to="/modeling" replace />} />
          <Route path="/modeling" element={<ModelingPage />} />
          <Route path="/simulation"element={<SimulationPage />} />
        </Routes>
      </Content>
    </Layout>
  );
};

export default App;
