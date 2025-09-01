import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  IconButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Alert,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  Switch,
  FormControlLabel,
  Slider,
  Tooltip
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  ExpandMore as ExpandMoreIcon,
  Upload as UploadIcon,
  Download as DownloadIcon,
  Settings as SettingsIcon,
  PlayArrow as PlayIcon,
  FileCopy as CopyIcon
} from '@mui/icons-material';
import { useApi } from '../../hooks/useApi';
import { JsonEditor } from '../Common/JsonEditor';
import { FileUpload } from '../Common/FileUpload';

interface BatchTask {
  id: string;
  name: string;
  parameters: Record<string, any>;
  configuration: Record<string, any>;
}

interface Template {
  id: string;
  name: string;
  description: string;
  type: string;
  category: string;
  parameters: TemplateParameter[];
  configuration: Record<string, any>;
}

interface TemplateParameter {
  name: string;
  type: string;
  description: string;
  default_value: any;
  min_value?: number;
  max_value?: number;
  options?: string[];
  required: boolean;
  unit?: string;
}

interface BatchJobSubmissionDialogProps {
  open: boolean;
  onClose: () => void;
  onSubmitted: () => void;
}

const steps = [
  '基本信息',
  '任务配置',
  '高级设置',
  '确认提交'
];

export const BatchJobSubmissionDialog: React.FC<BatchJobSubmissionDialogProps> = ({
  open,
  onClose,
  onSubmitted
}) => {
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // 基本信息
  const [jobName, setJobName] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [priority, setPriority] = useState<'low' | 'normal' | 'high'>('normal');
  
  // 任务配置
  const [tasks, setTasks] = useState<BatchTask[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [useTemplate, setUseTemplate] = useState(false);
  
  // 高级设置
  const [maxParallelTasks, setMaxParallelTasks] = useState(4);
  const [timeoutMinutes, setTimeoutMinutes] = useState(60);
  const [retryCount, setRetryCount] = useState(3);
  const [notificationWebhook, setNotificationWebhook] = useState('');
  const [enableNotifications, setEnableNotifications] = useState(false);
  const [autoCleanup, setAutoCleanup] = useState(true);
  const [saveResults, setSaveResults] = useState(true);
  
  const api = useApi();

  // 获取模板列表
  const fetchTemplates = async () => {
    try {
      const response = await api.get('/templates');
      setTemplates(response.data.templates || []);
    } catch (err: any) {
      console.error('获取模板列表失败:', err);
    }
  };

  // 添加新任务
  const addTask = () => {
    const newTask: BatchTask = {
      id: `task_${Date.now()}`,
      name: `任务 ${tasks.length + 1}`,
      parameters: {},
      configuration: {
        solver: 'default',
        max_iterations: 1000,
        tolerance: 1e-6
      }
    };
    setTasks([...tasks, newTask]);
  };

  // 删除任务
  const removeTask = (taskId: string) => {
    setTasks(tasks.filter(task => task.id !== taskId));
  };

  // 更新任务
  const updateTask = (taskId: string, updates: Partial<BatchTask>) => {
    setTasks(tasks.map(task => 
      task.id === taskId ? { ...task, ...updates } : task
    ));
  };

  // 复制任务
  const duplicateTask = (taskId: string) => {
    const taskToDuplicate = tasks.find(task => task.id === taskId);
    if (taskToDuplicate) {
      const newTask: BatchTask = {
        ...taskToDuplicate,
        id: `task_${Date.now()}`,
        name: `${taskToDuplicate.name} (副本)`
      };
      setTasks([...tasks, newTask]);
    }
  };

  // 从模板创建任务
  const createTasksFromTemplate = async () => {
    if (!selectedTemplate) return;
    
    try {
      const response = await api.post(`/templates/${selectedTemplate.id}/apply`, {
        parameter_values: {}
      });
      
      const newTask: BatchTask = {
        id: `task_${Date.now()}`,
        name: `基于 ${selectedTemplate.name} 的任务`,
        parameters: response.data.parameters,
        configuration: response.data.configuration
      };
      
      setTasks([...tasks, newTask]);
    } catch (err: any) {
      setError(err.message || '应用模板失败');
    }
  };

  // 从文件导入任务
  const importTasksFromFile = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        const importedTasks = JSON.parse(content);
        
        if (Array.isArray(importedTasks)) {
          const newTasks = importedTasks.map((task, index) => ({
            id: `imported_task_${Date.now()}_${index}`,
            name: task.name || `导入任务 ${index + 1}`,
            parameters: task.parameters || {},
            configuration: task.configuration || {}
          }));
          
          setTasks([...tasks, ...newTasks]);
        } else {
          setError('导入文件格式不正确');
        }
      } catch (err) {
        setError('解析导入文件失败');
      }
    };
    reader.readAsText(file);
  };

  // 导出任务配置
  const exportTasks = () => {
    const dataStr = JSON.stringify(tasks, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `batch_tasks_${Date.now()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // 提交批量任务
  const submitBatchJob = async () => {
    if (!jobName.trim()) {
      setError('请输入任务名称');
      return;
    }
    
    if (tasks.length === 0) {
      setError('请至少添加一个任务');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      const jobData = {
        name: jobName,
        description: jobDescription,
        tasks: tasks.map(task => ({
          name: task.name,
          parameters: task.parameters,
          configuration: task.configuration
        })),
        priority,
        max_parallel_tasks: maxParallelTasks,
        timeout_minutes: timeoutMinutes,
        retry_count: retryCount,
        notification_webhook: enableNotifications ? notificationWebhook : undefined,
        auto_cleanup: autoCleanup,
        save_results: saveResults
      };
      
      await api.post('/batch/submit', jobData);
      onSubmitted();
      handleClose();
    } catch (err: any) {
      setError(err.message || '提交批量任务失败');
    } finally {
      setLoading(false);
    }
  };

  // 处理步骤切换
  const handleNext = () => {
    if (activeStep === 0) {
      if (!jobName.trim()) {
        setError('请输入任务名称');
        return;
      }
    } else if (activeStep === 1) {
      if (tasks.length === 0) {
        setError('请至少添加一个任务');
        return;
      }
    }
    
    setError(null);
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  // 重置表单
  const resetForm = () => {
    setActiveStep(0);
    setJobName('');
    setJobDescription('');
    setPriority('normal');
    setTasks([]);
    setSelectedTemplate(null);
    setUseTemplate(false);
    setMaxParallelTasks(4);
    setTimeoutMinutes(60);
    setRetryCount(3);
    setNotificationWebhook('');
    setEnableNotifications(false);
    setAutoCleanup(true);
    setSaveResults(true);
    setError(null);
  };

  // 关闭对话框
  const handleClose = () => {
    resetForm();
    onClose();
  };

  // 组件挂载时获取模板
  useEffect(() => {
    if (open) {
      fetchTemplates();
    }
  }, [open]);

  // 渲染基本信息步骤
  const renderBasicInfoStep = () => (
    <Box sx={{ mt: 2 }}>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="任务名称"
            value={jobName}
            onChange={(e) => setJobName(e.target.value)}
            required
            error={!jobName.trim() && error !== null}
            helperText={!jobName.trim() && error !== null ? '请输入任务名称' : ''}
          />
        </Grid>
        <Grid item xs={12}>
          <TextField
            fullWidth
            label="任务描述"
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            multiline
            rows={3}
            placeholder="描述这个批量仿真任务的目的和内容..."
          />
        </Grid>
        <Grid item xs={12}>
          <FormControl fullWidth>
            <InputLabel>优先级</InputLabel>
            <Select
              value={priority}
              label="优先级"
              onChange={(e) => setPriority(e.target.value as 'low' | 'normal' | 'high')}
            >
              <MenuItem value="low">低</MenuItem>
              <MenuItem value="normal">普通</MenuItem>
              <MenuItem value="high">高</MenuItem>
            </Select>
          </FormControl>
        </Grid>
      </Grid>
    </Box>
  );

  // 渲染任务配置步骤
  const renderTaskConfigStep = () => (
    <Box sx={{ mt: 2 }}>
      {/* 模板选择 */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">使用模板</Typography>
            <Switch
              checked={useTemplate}
              onChange={(e) => setUseTemplate(e.target.checked)}
            />
          </Box>
          
          {useTemplate && (
            <Box>
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>选择模板</InputLabel>
                <Select
                  value={selectedTemplate?.id || ''}
                  label="选择模板"
                  onChange={(e) => {
                    const template = templates.find(t => t.id === e.target.value);
                    setSelectedTemplate(template || null);
                  }}
                >
                  {templates.map((template) => (
                    <MenuItem key={template.id} value={template.id}>
                      <Box>
                        <Typography variant="subtitle2">{template.name}</Typography>
                        <Typography variant="caption" color="textSecondary">
                          {template.description}
                        </Typography>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              
              {selectedTemplate && (
                <Button
                  variant="outlined"
                  onClick={createTasksFromTemplate}
                  startIcon={<AddIcon />}
                >
                  从模板创建任务
                </Button>
              )}
            </Box>
          )}
        </CardContent>
      </Card>

      {/* 任务列表 */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">任务列表 ({tasks.length})</Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <FileUpload
                accept=".json"
                onFileSelect={importTasksFromFile}
                render={(onClick) => (
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<UploadIcon />}
                    onClick={onClick}
                  >
                    导入
                  </Button>
                )}
              />
              <Button
                variant="outlined"
                size="small"
                startIcon={<DownloadIcon />}
                onClick={exportTasks}
                disabled={tasks.length === 0}
              >
                导出
              </Button>
              <Button
                variant="contained"
                size="small"
                startIcon={<AddIcon />}
                onClick={addTask}
              >
                添加任务
              </Button>
            </Box>
          </Box>
          
          {tasks.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography color="textSecondary">
                还没有添加任务，点击"添加任务"开始配置
              </Typography>
            </Box>
          ) : (
            <List>
              {tasks.map((task, index) => (
                <React.Fragment key={task.id}>
                  <ListItem>
                    <Accordion sx={{ width: '100%' }}>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                          <Typography variant="subtitle1" sx={{ flexGrow: 1 }}>
                            {task.name}
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 1, mr: 2 }}>
                            <Chip
                              label={`${Object.keys(task.parameters).length} 参数`}
                              size="small"
                              variant="outlined"
                            />
                            <Chip
                              label={`${Object.keys(task.configuration).length} 配置`}
                              size="small"
                              variant="outlined"
                            />
                          </Box>
                        </Box>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Grid container spacing={2}>
                          <Grid item xs={12}>
                            <TextField
                              fullWidth
                              label="任务名称"
                              value={task.name}
                              onChange={(e) => updateTask(task.id, { name: e.target.value })}
                            />
                          </Grid>
                          <Grid item xs={12} md={6}>
                            <Typography variant="subtitle2" gutterBottom>
                              参数配置
                            </Typography>
                            <JsonEditor
                              value={task.parameters}
                              onChange={(value) => updateTask(task.id, { parameters: value })}
                              height="200px"
                            />
                          </Grid>
                          <Grid item xs={12} md={6}>
                            <Typography variant="subtitle2" gutterBottom>
                              仿真配置
                            </Typography>
                            <JsonEditor
                              value={task.configuration}
                              onChange={(value) => updateTask(task.id, { configuration: value })}
                              height="200px"
                            />
                          </Grid>
                          <Grid item xs={12}>
                            <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                              <Button
                                size="small"
                                startIcon={<CopyIcon />}
                                onClick={() => duplicateTask(task.id)}
                              >
                                复制
                              </Button>
                              <Button
                                size="small"
                                color="error"
                                startIcon={<DeleteIcon />}
                                onClick={() => removeTask(task.id)}
                              >
                                删除
                              </Button>
                            </Box>
                          </Grid>
                        </Grid>
                      </AccordionDetails>
                    </Accordion>
                  </ListItem>
                  {index < tasks.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          )}
        </CardContent>
      </Card>
    </Box>
  );

  // 渲染高级设置步骤
  const renderAdvancedSettingsStep = () => (
    <Box sx={{ mt: 2 }}>
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                执行设置
              </Typography>
              
              <Box sx={{ mb: 3 }}>
                <Typography gutterBottom>
                  最大并行任务数: {maxParallelTasks}
                </Typography>
                <Slider
                  value={maxParallelTasks}
                  onChange={(_, value) => setMaxParallelTasks(value as number)}
                  min={1}
                  max={16}
                  marks
                  valueLabelDisplay="auto"
                />
              </Box>
              
              <Box sx={{ mb: 3 }}>
                <Typography gutterBottom>
                  超时时间 (分钟): {timeoutMinutes}
                </Typography>
                <Slider
                  value={timeoutMinutes}
                  onChange={(_, value) => setTimeoutMinutes(value as number)}
                  min={5}
                  max={480}
                  step={5}
                  marks={[
                    { value: 5, label: '5分钟' },
                    { value: 60, label: '1小时' },
                    { value: 240, label: '4小时' },
                    { value: 480, label: '8小时' }
                  ]}
                  valueLabelDisplay="auto"
                />
              </Box>
              
              <Box sx={{ mb: 2 }}>
                <Typography gutterBottom>
                  重试次数: {retryCount}
                </Typography>
                <Slider
                  value={retryCount}
                  onChange={(_, value) => setRetryCount(value as number)}
                  min={0}
                  max={10}
                  marks
                  valueLabelDisplay="auto"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                通知设置
              </Typography>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={enableNotifications}
                    onChange={(e) => setEnableNotifications(e.target.checked)}
                  />
                }
                label="启用通知"
                sx={{ mb: 2 }}
              />
              
              {enableNotifications && (
                <TextField
                  fullWidth
                  label="Webhook URL"
                  value={notificationWebhook}
                  onChange={(e) => setNotificationWebhook(e.target.value)}
                  placeholder="https://your-webhook-url.com/notify"
                  helperText="任务完成或失败时将发送通知到此URL"
                  sx={{ mb: 2 }}
                />
              )}
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="h6" gutterBottom>
                其他设置
              </Typography>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={saveResults}
                    onChange={(e) => setSaveResults(e.target.checked)}
                  />
                }
                label="保存结果"
                sx={{ mb: 1 }}
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={autoCleanup}
                    onChange={(e) => setAutoCleanup(e.target.checked)}
                  />
                }
                label="自动清理临时文件"
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );

  // 渲染确认提交步骤
  const renderConfirmationStep = () => (
    <Box sx={{ mt: 2 }}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            任务摘要
          </Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="textSecondary">
                任务名称
              </Typography>
              <Typography variant="body1" gutterBottom>
                {jobName}
              </Typography>
              
              <Typography variant="subtitle2" color="textSecondary">
                任务描述
              </Typography>
              <Typography variant="body1" gutterBottom>
                {jobDescription || '无描述'}
              </Typography>
              
              <Typography variant="subtitle2" color="textSecondary">
                优先级
              </Typography>
              <Chip
                label={priority}
                color={priority === 'high' ? 'error' : priority === 'normal' ? 'primary' : 'default'}
                size="small"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="textSecondary">
                任务数量
              </Typography>
              <Typography variant="body1" gutterBottom>
                {tasks.length} 个任务
              </Typography>
              
              <Typography variant="subtitle2" color="textSecondary">
                最大并行数
              </Typography>
              <Typography variant="body1" gutterBottom>
                {maxParallelTasks}
              </Typography>
              
              <Typography variant="subtitle2" color="textSecondary">
                超时时间
              </Typography>
              <Typography variant="body1" gutterBottom>
                {timeoutMinutes} 分钟
              </Typography>
              
              <Typography variant="subtitle2" color="textSecondary">
                重试次数
              </Typography>
              <Typography variant="body1" gutterBottom>
                {retryCount}
              </Typography>
            </Grid>
          </Grid>
          
          {enableNotifications && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" color="textSecondary">
                通知设置
              </Typography>
              <Typography variant="body2">
                将发送通知到: {notificationWebhook}
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: { minHeight: '80vh' }
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <PlayIcon />
          新建批量仿真任务
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
        
        <Stepper activeStep={activeStep} orientation="vertical">
          {steps.map((label, index) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
              <StepContent>
                {index === 0 && renderBasicInfoStep()}
                {index === 1 && renderTaskConfigStep()}
                {index === 2 && renderAdvancedSettingsStep()}
                {index === 3 && renderConfirmationStep()}
                
                <Box sx={{ mb: 2, mt: 2 }}>
                  <Button
                    variant="contained"
                    onClick={index === steps.length - 1 ? submitBatchJob : handleNext}
                    sx={{ mr: 1 }}
                    disabled={loading}
                    startIcon={index === steps.length - 1 ? <PlayIcon /> : undefined}
                  >
                    {index === steps.length - 1 ? '提交任务' : '下一步'}
                  </Button>
                  <Button
                    disabled={index === 0 || loading}
                    onClick={handleBack}
                    sx={{ mr: 1 }}
                  >
                    上一步
                  </Button>
                </Box>
              </StepContent>
            </Step>
          ))}
        </Stepper>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          取消
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default BatchJobSubmissionDialog;