import React, { DragEvent, useRef } from 'react';
import { useProjectStore } from '../store/projectStore';
import { useSimulationStore } from '../store/simulationStore';
import { Empty, Button, Spin, message, Layout as AntLayout, Row, Col, Card, Collapse } from 'antd';
import RGL, { WidthProvider } from 'react-grid-layout';
import ReactFlow, { MiniMap, Controls, Background } from 'reactflow';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import 'reactflow/dist/style.css';

import VariableSidebar from '../components/VariableSidebar';
import ChartCard from '../components/ChartCard';
import SceneDesigner, { SceneDesignerRef } from '../components/SceneDesigner';

const { Panel } = Collapse;
const ReactGridLayout = WidthProvider(RGL);
const { Sider, Content } = AntLayout;

const SimulationPage: React.FC = () => {
  const { projectConfig } = useProjectStore();
  const sceneDesignerRef = useRef<SceneDesignerRef>(null);
  const {
    startSimulation,
    stopSimulation,
    pauseSimulation,
    resumeSimulation,
    addChart,
    updateLayouts,
    isRunning,
    isPaused,
    isLoading,
    charts,
    layouts,
    data,
    liveNodes,
    liveEdges,
  } = useSimulationStore();

  const handleStart = () => {
    if (!projectConfig) {
      message.error("No project is loaded!");
      return;
    }
    const scenarioScript = sceneDesignerRef.current?.getScenarioScript();
    startSimulation(projectConfig, scenarioScript);
  };

  const onDrop = (event: DragEvent) => {
    event.preventDefault();
    const variableName = event.dataTransfer.getData('application/chs-sdk-variable');
    if (variableName) {
      addChart(variableName);
    }
  };

  const onDragOver = (event: DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'copy';
  };

  if (!projectConfig) {
    return <Empty description="Please load a project from the Modeling page first." />;
  }

  return (
    <AntLayout style={{ background: '#fff', height: 'calc(100vh - 112px)' }}>
      <Sider width={200} style={{ background: '#fff', padding: '10px', borderRight: '1px solid #f0f0f0', overflowY: 'auto' }}>
        <VariableSidebar />
        <Collapse ghost style={{ marginTop: '20px' }}>
          <Panel header="Scenario Designer" key="1">
            <SceneDesigner ref={sceneDesignerRef} />
          </Panel>
        </Collapse>
      </Sider>
      <Content style={{ padding: '0 24px', minHeight: 280, display: 'flex', flexDirection: 'column' }}>
        <Row justify="space-between" align="middle" style={{ padding: '10px 0', flexShrink: 0 }}>
          <Col>
            <Spin spinning={isLoading}>
              <Button type="primary" onClick={handleStart} disabled={isRunning || isLoading} style={{ marginRight: '10px' }}>
                Start
              </Button>
              {!isRunning ? null : isPaused ? (
                <Button onClick={resumeSimulation} style={{ marginRight: '10px' }}>Resume</Button>
              ) : (
                <Button onClick={pauseSimulation} style={{ marginRight: '10px' }}>Pause</Button>
              )}
              <Button type="default" danger onClick={stopSimulation} disabled={!isRunning}>
                Stop
              </Button>
            </Spin>
          </Col>
        </Row>

        <Row gutter={16} style={{ flex: 1, overflow: 'hidden' }}>
          <Col span={12} style={{ height: '100%'}}>
            <Card title="Live Topology" style={{ height: '100%' }} bodyStyle={{ height: 'calc(100% - 56px)'}}>
              <ReactFlow
                nodes={liveNodes}
                edges={liveEdges}
                nodesDraggable={false}
                nodesConnectable={false}
                elementsSelectable={false}
                fitView
              >
                <Controls showInteractive={false} />
                <MiniMap />
                <Background />
              </ReactFlow>
            </Card>
          </Col>
          <Col span={12} style={{ height: '100%', overflowY: 'auto' }}>
             <ReactGridLayout
              className="layout"
              layouts={layouts}
              onLayoutChange={(_layout, allLayouts) => updateLayouts(allLayouts)}
              isDroppable={true}
              onDrop={onDrop}
              onDragOver={onDragOver}
              cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
              rowHeight={30}
            >
              {charts.map(chart => (
                <div key={chart.id}>
                  <ChartCard chart={chart} data={data} />
                </div>
              ))}
            </ReactGridLayout>
          </Col>
        </Row>
      </Content>
    </AntLayout>
  );
};

export default SimulationPage;
