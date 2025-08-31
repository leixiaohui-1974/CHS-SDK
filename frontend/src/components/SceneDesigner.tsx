import React, { useState, useImperativeHandle, forwardRef } from 'react';
import { Card, List, Button, Form, Input, InputNumber, Modal, Typography } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { v4 as uuidv4 } from 'uuid';

const { Text } = Typography;
const { TextArea } = Input;

export interface ScenarioEvent {
  id: string;
  time: number;
  topic: string;
  message: any;
}

export interface SceneDesignerRef {
  getScenarioScript: () => Omit<ScenarioEvent, 'id'>[];
}

const SceneDesigner = forwardRef<SceneDesignerRef, {}>((_props, ref) => {
  const [events, setEvents] = useState<ScenarioEvent[]>([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingEvent, setEditingEvent] = useState<ScenarioEvent | null>(null);
  const [form] = Form.useForm();

  useImperativeHandle(ref, () => ({
    getScenarioScript() {
      return events.map(({ id, ...rest }) => rest);
    }
  }));

  const showModal = (event?: ScenarioEvent) => {
    setEditingEvent(event || null);
    form.setFieldsValue(event ? {
      ...event,
      message: JSON.stringify(event.message, null, 2)
    } : { time: 0, topic: '', message: '{}' });
    setIsModalVisible(true);
  };

  const handleCancel = () => {
    setIsModalVisible(false);
    setEditingEvent(null);
    form.resetFields();
  };

  const handleOk = () => {
    form.validateFields().then(values => {
      try {
        const messageObject = JSON.parse(values.message);
        const eventData = { ...values, message: messageObject };

        if (editingEvent) {
          setEvents(events.map(e => e.id === editingEvent.id ? { ...e, ...eventData } : e));
        } else {
          setEvents([...events, { ...eventData, id: uuidv4() }]);
        }
        handleCancel();
      } catch (e) {
        Modal.error({ title: 'Invalid JSON', content: 'The message field contains invalid JSON.' });
      }
    });
  };

  const handleDelete = (id: string) => {
    setEvents(events.filter(e => e.id !== id));
  };

  return (
    <Card
      title="Scenario Event Editor"
      size="small"
      extra={<Button icon={<PlusOutlined />} onClick={() => showModal()}>Add Event</Button>}
    >
      <List
        itemLayout="horizontal"
        dataSource={events}
        renderItem={event => (
          <List.Item
            actions={[
              <Button size="small" icon={<EditOutlined />} onClick={() => showModal(event)} />,
              <Button size="small" icon={<DeleteOutlined />} danger onClick={() => handleDelete(event.id)} />,
            ]}
          >
            <List.Item.Meta
              title={<Text strong>{`Time: ${event.time}s - Topic: ${event.topic}`}</Text>}
              description={<pre style={{ margin: 0, fontSize: '12px' }}>{JSON.stringify(event.message, null, 2)}</pre>}
            />
          </List.Item>
        )}
      />
      <Modal
        title={editingEvent ? 'Edit Event' : 'Add New Event'}
        visible={isModalVisible}
        onOk={handleOk}
        onCancel={handleCancel}
        destroyOnClose
      >
        <Form form={form} layout="vertical" name="event_form">
          <Form.Item name="time" label="Time (seconds)" rules={[{ required: true, message: 'Please input the time!' }]}>
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="topic" label="Topic" rules={[{ required: true, message: 'Please input the topic!' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="message" label="Message (JSON format)" rules={[{ required: true, message: 'Please input the message!' }]}>
            <TextArea rows={4} />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
});

export default SceneDesigner;
