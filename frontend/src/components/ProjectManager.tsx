import React, { useState } from 'react';
import { Modal, Form, Input, Button, Space, Upload, message, List, Card, Divider } from 'antd';
import { SaveOutlined, FolderOpenOutlined, UploadOutlined, DownloadOutlined, PlusOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';

interface ProjectInfo {
  id: string;
  name: string;
  description: string;
  lastModified: string;
  version: string;
}

interface ProjectManagerProps {
  visible: boolean;
  onClose: () => void;
  currentProject: any;
  onSaveProject: (projectData: any) => void;
  onLoadProject: (projectData: any) => void;
}

const ProjectManager: React.FC<ProjectManagerProps> = ({
  visible,
  onClose,
  currentProject,
  onSaveProject,
  onLoadProject
}) => {
  const [activeTab, setActiveTab] = useState<'save' | 'load' | 'import' | 'export'>('save');
  const [form] = Form.useForm();
  const [savedProjects, setSavedProjects] = useState<ProjectInfo[]>([
    {
      id: '1',
      name: 'Water Distribution Network',
      description: 'Basic water distribution system with pumps and tanks',
      lastModified: '2024-01-15 10:30:00',
      version: '1.0'
    },
    {
      id: '2',
      name: 'Irrigation System',
      description: 'Agricultural irrigation network design',
      lastModified: '2024-01-14 15:45:00',
      version: '1.2'
    }
  ]);

  const handleSaveProject = async (values: any) => {
    try {
      const projectData = {
        ...currentProject,
        name: values.name,
        description: values.description,
        version: values.version || '1.0',
        lastModified: new Date().toISOString()
      };
      
      // In a real implementation, this would call an API
      const newProject: ProjectInfo = {
        id: Date.now().toString(),
        name: values.name,
        description: values.description,
        lastModified: new Date().toLocaleString(),
        version: values.version || '1.0'
      };
      
      setSavedProjects(prev => [newProject, ...prev]);
      onSaveProject(projectData);
      message.success('Project saved successfully!');
      form.resetFields();
    } catch (error) {
      message.error('Failed to save project');
    }
  };

  const handleLoadProject = (project: ProjectInfo) => {
    // In a real implementation, this would load the full project data
    const mockProjectData = {
      id: project.id,
      name: project.name,
      description: project.description,
      nodes: [],
      edges: [],
      version: project.version
    };
    
    onLoadProject(mockProjectData);
    message.success(`Loaded project: ${project.name}`);
    onClose();
  };

  const handleExportProject = () => {
    if (!currentProject) {
      message.warning('No project to export');
      return;
    }

    const exportData = {
      ...currentProject,
      exportedAt: new Date().toISOString(),
      version: '1.0'
    };

    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `${currentProject.name || 'project'}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    message.success('Project exported successfully!');
  };

  const uploadProps: UploadProps = {
    name: 'file',
    accept: '.json',
    beforeUpload: (file) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const projectData = JSON.parse(e.target?.result as string);
          onLoadProject(projectData);
          message.success(`Imported project: ${projectData.name || 'Unnamed'}`);
          onClose();
        } catch (error) {
          message.error('Invalid project file format');
        }
      };
      reader.readAsText(file);
      return false; // Prevent upload
    },
  };

  const renderSaveTab = () => (
    <Form form={form} layout="vertical" onFinish={handleSaveProject}>
      <Form.Item
        name="name"
        label="Project Name"
        rules={[{ required: true, message: 'Please enter project name' }]}
      >
        <Input placeholder="Enter project name" />
      </Form.Item>
      
      <Form.Item
        name="description"
        label="Description"
      >
        <Input.TextArea rows={3} placeholder="Enter project description" />
      </Form.Item>
      
      <Form.Item
        name="version"
        label="Version"
        initialValue="1.0"
      >
        <Input placeholder="1.0" />
      </Form.Item>
      
      <Form.Item>
        <Button type="primary" htmlType="submit" icon={<SaveOutlined />} block>
          Save Project
        </Button>
      </Form.Item>
    </Form>
  );

  const renderLoadTab = () => (
    <div>
      <List
        dataSource={savedProjects}
        renderItem={(project) => (
          <List.Item
            actions={[
              <Button 
                key="load"
                type="link" 
                icon={<FolderOpenOutlined />}
                onClick={() => handleLoadProject(project)}
              >
                Load
              </Button>
            ]}
          >
            <List.Item.Meta
              title={project.name}
              description={
                <div>
                  <div>{project.description}</div>
                  <div style={{ fontSize: '12px', color: '#999', marginTop: '4px' }}>
                    Version: {project.version} | Last modified: {project.lastModified}
                  </div>
                </div>
              }
            />
          </List.Item>
        )}
      />
    </div>
  );

  const renderImportTab = () => (
    <div style={{ textAlign: 'center', padding: '40px 20px' }}>
      <Upload.Dragger {...uploadProps}>
        <p className="ant-upload-drag-icon">
          <UploadOutlined style={{ fontSize: '48px', color: '#1890ff' }} />
        </p>
        <p className="ant-upload-text">Click or drag file to this area to import</p>
        <p className="ant-upload-hint">
          Support for JSON project files. Select a previously exported project file.
        </p>
      </Upload.Dragger>
    </div>
  );

  const renderExportTab = () => (
    <div style={{ textAlign: 'center', padding: '40px 20px' }}>
      <div style={{ marginBottom: '24px' }}>
        <DownloadOutlined style={{ fontSize: '48px', color: '#1890ff' }} />
      </div>
      <h3>Export Current Project</h3>
      <p style={{ color: '#666', marginBottom: '24px' }}>
        Export your current project as a JSON file that can be imported later or shared with others.
      </p>
      <Button 
        type="primary" 
        size="large"
        icon={<DownloadOutlined />}
        onClick={handleExportProject}
        disabled={!currentProject}
      >
        Export Project
      </Button>
      {!currentProject && (
        <p style={{ color: '#999', marginTop: '12px', fontSize: '12px' }}>
          No project loaded to export
        </p>
      )}
    </div>
  );

  const tabs = [
    { key: 'save', label: 'Save', icon: <SaveOutlined /> },
    { key: 'load', label: 'Load', icon: <FolderOpenOutlined /> },
    { key: 'import', label: 'Import', icon: <UploadOutlined /> },
    { key: 'export', label: 'Export', icon: <DownloadOutlined /> }
  ];

  return (
    <Modal
      title="Project Manager"
      open={visible}
      onCancel={onClose}
      footer={null}
      width={600}
      destroyOnClose
    >
      <div style={{ marginBottom: '16px' }}>
        <Space>
          {tabs.map(tab => (
            <Button
              key={tab.key}
              type={activeTab === tab.key ? 'primary' : 'default'}
              icon={tab.icon}
              onClick={() => setActiveTab(tab.key as any)}
            >
              {tab.label}
            </Button>
          ))}
        </Space>
      </div>
      
      <Divider style={{ margin: '16px 0' }} />
      
      <div style={{ minHeight: '300px' }}>
        {activeTab === 'save' && renderSaveTab()}
        {activeTab === 'load' && renderLoadTab()}
        {activeTab === 'import' && renderImportTab()}
        {activeTab === 'export' && renderExportTab()}
      </div>
    </Modal>
  );
};

export default ProjectManager;