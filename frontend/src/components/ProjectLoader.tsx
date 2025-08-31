import React, { useEffect } from 'react';
import { Select, Spin, Alert } from 'antd';
import { useProjectStore } from '../store/projectStore';

const ProjectLoader: React.FC = () => {
  const {
    exampleList,
    isLoading,
    error,
    fetchExampleList,
    loadProject,
    selectedExamplePath,
  } = useProjectStore();

  useEffect(() => {
    fetchExampleList();
  }, [fetchExampleList]);

  const handleSelectProject = (examplePath: string) => {
    loadProject(examplePath);
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
      <span style={{ color: 'white' }}>Load Example:</span>
      {isLoading && !exampleList.length ? (
        <Spin size="small" />
      ) : error && !exampleList.length ? (
        <Alert message="Error" description={error} type="error" showIcon />
      ) : (
        <Select
          style={{ width: 250 }}
          placeholder="Select a project"
          onChange={handleSelectProject}
          value={selectedExamplePath || undefined}
          loading={isLoading}
          options={exampleList.map(name => ({ value: name, label: name }))}
        />
      )}
    </div>
  );
};

export default ProjectLoader;
