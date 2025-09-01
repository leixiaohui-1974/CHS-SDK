import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Checkbox,
  FormControlLabel,
  FormGroup,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  IconButton,
  Tooltip,
  Alert,
  CircularProgress,
  LinearProgress,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Switch,
  Slider,
  Divider
} from '@mui/material';
import {
  GetApp as ExportIcon,
  ExpandMore as ExpandMoreIcon,
  Description as DescriptionIcon,
  TableChart as TableChartIcon,
  PictureAsPdf as PdfIcon,
  Code as CodeIcon,
  Archive as ArchiveIcon,
  Security as SecurityIcon,
  Settings as SettingsIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Download as DownloadIcon,
  Visibility as VisibilityIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';
import { useApi } from '../../hooks/useApi';

interface ExportOptions {
  format: 'json' | 'csv' | 'excel' | 'pdf' | 'html' | 'xml' | 'matlab' | 'python' | 'zip';
  include_metadata: boolean;
  include_parameters: boolean;
  include_charts: boolean;
  chart_format?: 'png' | 'svg' | 'pdf';
  chart_resolution?: number;
  custom_template?: string;
  compression?: boolean;
  password_protection?: boolean;
  password?: string;
  file_naming?: 'default' | 'timestamp' | 'custom';
  custom_filename?: string;
  split_by_job?: boolean;
  max_file_size?: number;
}

interface ExportTask {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  created_at: string;
  completed_at?: string;
  file_size?: number;
  download_url?: string;
  error_message?: string;
  options: ExportOptions;
}

interface ResultExportDialogProps {
  open: boolean;
  onClose: () => void;
  selectedJobs: string[];
}

const EXPORT_FORMATS = [
  { 
    value: 'json', 
    label: 'JSON', 
    description: '结构化数据格式，适合程序处理',
    icon: <CodeIcon />,
    extensions: ['.json']
  },
  { 
    value: 'csv', 
    label: 'CSV', 
    description: '逗号分隔值，适合Excel等表格软件',
    icon: <TableChartIcon />,
    extensions: ['.csv']
  },
  { 
    value: 'excel', 
    label: 'Excel', 
    description: 'Excel工作簿，包含图表和格式',
    icon: <TableChartIcon />,
    extensions: ['.xlsx']
  },
  { 
    value: 'pdf', 
    label: 'PDF', 
    description: '便携式文档格式，适合报告',
    icon: <PdfIcon />,
    extensions: ['.pdf']
  },
  { 
    value: 'html', 
    label: 'HTML', 
    description: '网页格式，支持交互式图表',
    icon: <DescriptionIcon />,
    extensions: ['.html']
  },
  { 
    value: 'xml', 
    label: 'XML', 
    description: '可扩展标记语言',
    icon: <CodeIcon />,
    extensions: ['.xml']
  },
  { 
    value: 'matlab', 
    label: 'MATLAB', 
    description: 'MATLAB数据文件',
    icon: <CodeIcon />,
    extensions: ['.mat']
  },
  { 
    value: 'python', 
    label: 'Python', 
    description: 'Python脚本和数据',
    icon: <CodeIcon />,
    extensions: ['.py', '.pkl']
  },
  { 
    value: 'zip', 
    label: 'ZIP压缩包', 
    description: '包含所有格式的压缩包',
    icon: <ArchiveIcon />,
    extensions: ['.zip']
  }
];

const CHART_FORMATS = [
  { value: 'png', label: 'PNG', description: '位图格式，适合网页显示' },
  { value: 'svg', label: 'SVG', description: '矢量格式，可缩放' },
  { value: 'pdf', label: 'PDF', description: '便携式文档格式' }
];

const STEPS = [
  '选择格式',
  '配置选项',
  '高级设置',
  '确认导出'
];

export const ResultExportDialog: React.FC<ResultExportDialogProps> = ({
  open,
  onClose,
  selectedJobs
}) => {
  const [activeStep, setActiveStep] = useState(0);
  const [options, setOptions] = useState<ExportOptions>({
    format: 'json',
    include_metadata: true,
    include_parameters: true,
    include_charts: true,
    chart_format: 'png',
    chart_resolution: 300,
    compression: false,
    password_protection: false,
    file_naming: 'default',
    split_by_job: false,
    max_file_size: 100
  });
  const [exportTasks, setExportTasks] = useState<ExportTask[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const api = useApi();

  // 获取导出历史
  const fetchExportTasks = async () => {
    try {
      const response = await api.get('/batch/export/history');
      setExportTasks(response.data.tasks || []);
    } catch (err: any) {
      setError(err.message || '获取导出历史失败');
    }
  };

  // 创建导出任务
  const createExportTask = async () => {
    try {
      setLoading(true);
      const response = await api.post('/batch/export/create', {
        job_ids: selectedJobs,
        options: options,
        name: `导出任务_${new Date().toLocaleString()}`
      });
      
      const newTask = response.data.task;
      setExportTasks(prev => [newTask, ...prev]);
      
      // 开始轮询状态
      pollExportStatus(newTask.id);
      
      // 重置步骤
      setActiveStep(0);
    } catch (err: any) {
      setError(err.message || '创建导出任务失败');
    } finally {
      setLoading(false);
    }
  };

  // 轮询导出状态
  const pollExportStatus = async (taskId: string) => {
    const poll = async () => {
      try {
        const response = await api.get(`/batch/export/${taskId}`);
        const task = response.data.task;
        
        setExportTasks(prev => 
          prev.map(t => t.id === taskId ? task : t)
        );
        
        if (['completed', 'failed'].includes(task.status)) {
          return; // 停止轮询
        }
        
        setTimeout(poll, 2000); // 2秒后再次轮询
      } catch (err) {
        console.error('轮询导出状态失败:', err);
      }
    };
    
    poll();
  };

  // 下载导出文件
  const downloadExportFile = async (taskId: string, filename?: string) => {
    try {
      const response = await api.get(`/batch/export/${taskId}/download`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename || `export_${taskId}.zip`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message || '下载导出文件失败');
    }
  };

  // 删除导出任务
  const deleteExportTask = async (taskId: string) => {
    try {
      await api.delete(`/batch/export/${taskId}`);
      setExportTasks(prev => prev.filter(t => t.id !== taskId));
    } catch (err: any) {
      setError(err.message || '删除导出任务失败');
    }
  };

  // 处理选项变更
  const handleOptionChange = (field: keyof ExportOptions, value: any) => {
    setOptions(prev => ({ ...prev, [field]: value }));
  };

  // 下一步
  const handleNext = () => {
    setActiveStep(prev => prev + 1);
  };

  // 上一步
  const handleBack = () => {
    setActiveStep(prev => prev - 1);
  };

  // 重置
  const handleReset = () => {
    setActiveStep(0);
  };

  // 格式化文件大小
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // 初始化
  useEffect(() => {
    if (open) {
      fetchExportTasks();
    }
  }, [open]);

  // 渲染格式选择步骤
  const renderFormatStep = () => (
    <Grid container spacing={2}>
      {EXPORT_FORMATS.map((format) => (
        <Grid item xs={12} sm={6} md={4} key={format.value}>
          <Card 
            sx={{ 
              cursor: 'pointer',
              border: options.format === format.value ? 2 : 1,
              borderColor: options.format === format.value ? 'primary.main' : 'divider'
            }}
            onClick={() => handleOptionChange('format', format.value)}
          >
            <CardContent sx={{ textAlign: 'center' }}>
              <Box sx={{ mb: 1 }}>
                {format.icon}
              </Box>
              <Typography variant="h6" gutterBottom>
                {format.label}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                {format.description}
              </Typography>
              <Box sx={{ mt: 1 }}>
                {format.extensions.map((ext) => (
                  <Chip key={ext} label={ext} size="small" sx={{ mr: 0.5 }} />
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );

  // 渲染配置选项步骤
  const renderOptionsStep = () => (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Typography variant="h6" gutterBottom>
          包含内容
        </Typography>
        <FormGroup>
          <FormControlLabel
            control={
              <Checkbox
                checked={options.include_metadata}
                onChange={(e) => handleOptionChange('include_metadata', e.target.checked)}
              />
            }
            label="包含元数据（创建时间、作者等）"
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={options.include_parameters}
                onChange={(e) => handleOptionChange('include_parameters', e.target.checked)}
              />
            }
            label="包含仿真参数"
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={options.include_charts}
                onChange={(e) => handleOptionChange('include_charts', e.target.checked)}
              />
            }
            label="包含图表"
          />
        </FormGroup>
      </Grid>
      
      {options.include_charts && (
        <Grid item xs={12}>
          <Typography variant="h6" gutterBottom>
            图表设置
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>图表格式</InputLabel>
                <Select
                  value={options.chart_format}
                  onChange={(e) => handleOptionChange('chart_format', e.target.value)}
                >
                  {CHART_FORMATS.map((format) => (
                    <MenuItem key={format.value} value={format.value}>
                      <Box>
                        <Typography variant="subtitle2">{format.label}</Typography>
                        <Typography variant="caption" color="textSecondary">
                          {format.description}
                        </Typography>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography gutterBottom>
                图表分辨率 (DPI): {options.chart_resolution}
              </Typography>
              <Slider
                value={options.chart_resolution}
                onChange={(e, value) => handleOptionChange('chart_resolution', value)}
                min={72}
                max={600}
                step={72}
                marks={[
                  { value: 72, label: '72' },
                  { value: 150, label: '150' },
                  { value: 300, label: '300' },
                  { value: 600, label: '600' }
                ]}
              />
            </Grid>
          </Grid>
        </Grid>
      )}
      
      <Grid item xs={12}>
        <Typography variant="h6" gutterBottom>
          文件组织
        </Typography>
        <FormControlLabel
          control={
            <Switch
              checked={options.split_by_job}
              onChange={(e) => handleOptionChange('split_by_job', e.target.checked)}
            />
          }
          label="按任务分别导出文件"
        />
      </Grid>
    </Grid>
  );

  // 渲染高级设置步骤
  const renderAdvancedStep = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <Typography variant="h6" gutterBottom>
          文件命名
        </Typography>
        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel>命名方式</InputLabel>
          <Select
            value={options.file_naming}
            onChange={(e) => handleOptionChange('file_naming', e.target.value)}
          >
            <MenuItem value="default">默认命名</MenuItem>
            <MenuItem value="timestamp">时间戳命名</MenuItem>
            <MenuItem value="custom">自定义命名</MenuItem>
          </Select>
        </FormControl>
        
        {options.file_naming === 'custom' && (
          <TextField
            fullWidth
            label="自定义文件名"
            value={options.custom_filename || ''}
            onChange={(e) => handleOptionChange('custom_filename', e.target.value)}
            helperText="不包含扩展名"
          />
        )}
      </Grid>
      
      <Grid item xs={12} md={6}>
        <Typography variant="h6" gutterBottom>
          压缩和安全
        </Typography>
        <FormGroup>
          <FormControlLabel
            control={
              <Switch
                checked={options.compression}
                onChange={(e) => handleOptionChange('compression', e.target.checked)}
              />
            }
            label="启用压缩"
          />
          <FormControlLabel
            control={
              <Switch
                checked={options.password_protection}
                onChange={(e) => handleOptionChange('password_protection', e.target.checked)}
              />
            }
            label="密码保护"
          />
        </FormGroup>
        
        {options.password_protection && (
          <TextField
            fullWidth
            type="password"
            label="设置密码"
            value={options.password || ''}
            onChange={(e) => handleOptionChange('password', e.target.value)}
            sx={{ mt: 2 }}
            helperText="用于保护导出文件"
          />
        )}
      </Grid>
      
      <Grid item xs={12}>
        <Typography variant="h6" gutterBottom>
          文件大小限制
        </Typography>
        <Typography gutterBottom>
          最大文件大小: {options.max_file_size} MB
        </Typography>
        <Slider
          value={options.max_file_size}
          onChange={(e, value) => handleOptionChange('max_file_size', value)}
          min={10}
          max={1000}
          step={10}
          marks={[
            { value: 10, label: '10MB' },
            { value: 100, label: '100MB' },
            { value: 500, label: '500MB' },
            { value: 1000, label: '1GB' }
          ]}
        />
      </Grid>
    </Grid>
  );

  // 渲染确认步骤
  const renderConfirmStep = () => (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Alert severity="info" sx={{ mb: 2 }}>
          即将导出 {selectedJobs.length} 个批量任务的结果
        </Alert>
      </Grid>
      
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              导出配置摘要
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" color="textSecondary">
                导出格式
              </Typography>
              <Typography variant="body1">
                {EXPORT_FORMATS.find(f => f.value === options.format)?.label}
              </Typography>
            </Box>
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" color="textSecondary">
                包含内容
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {options.include_metadata && <Chip label="元数据" size="small" />}
                {options.include_parameters && <Chip label="参数" size="small" />}
                {options.include_charts && <Chip label="图表" size="small" />}
              </Box>
            </Box>
            
            {options.include_charts && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="textSecondary">
                  图表设置
                </Typography>
                <Typography variant="body2">
                  格式: {options.chart_format?.toUpperCase()}, 分辨率: {options.chart_resolution} DPI
                </Typography>
              </Box>
            )}
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" color="textSecondary">
                文件设置
              </Typography>
              <Typography variant="body2">
                命名: {options.file_naming}, 分割: {options.split_by_job ? '是' : '否'}
              </Typography>
            </Box>
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" color="textSecondary">
                安全设置
              </Typography>
              <Typography variant="body2">
                压缩: {options.compression ? '是' : '否'}, 密码保护: {options.password_protection ? '是' : '否'}
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              导出历史
            </Typography>
            
            <List sx={{ maxHeight: 300, overflow: 'auto' }}>
              {exportTasks.slice(0, 5).map((task) => (
                <ListItem key={task.id}>
                  <ListItemIcon>
                    {task.status === 'completed' ? (
                      <CheckCircleIcon color="success" />
                    ) : task.status === 'failed' ? (
                      <ErrorIcon color="error" />
                    ) : (
                      <CircularProgress size={20} />
                    )}
                  </ListItemIcon>
                  <ListItemText
                    primary={task.name}
                    secondary={
                      <Box>
                        <Typography variant="caption" display="block">
                          {task.created_at}
                        </Typography>
                        {task.file_size && (
                          <Typography variant="caption">
                            {formatFileSize(task.file_size)}
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                  <ListItemSecondaryAction>
                    {task.status === 'completed' && (
                      <Tooltip title="下载">
                        <IconButton
                          size="small"
                          onClick={() => downloadExportFile(task.id)}
                        >
                          <DownloadIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: { height: '80vh' }
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <ExportIcon />
          <Typography variant="h6">
            结果导出
          </Typography>
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
        
        <Stepper activeStep={activeStep} orientation="vertical">
          <Step>
            <StepLabel>选择导出格式</StepLabel>
            <StepContent>
              {renderFormatStep()}
              <Box sx={{ mb: 2, mt: 2 }}>
                <Button
                  variant="contained"
                  onClick={handleNext}
                  sx={{ mt: 1, mr: 1 }}
                >
                  下一步
                </Button>
              </Box>
            </StepContent>
          </Step>
          
          <Step>
            <StepLabel>配置导出选项</StepLabel>
            <StepContent>
              {renderOptionsStep()}
              <Box sx={{ mb: 2, mt: 2 }}>
                <Button
                  variant="contained"
                  onClick={handleNext}
                  sx={{ mt: 1, mr: 1 }}
                >
                  下一步
                </Button>
                <Button
                  onClick={handleBack}
                  sx={{ mt: 1, mr: 1 }}
                >
                  上一步
                </Button>
              </Box>
            </StepContent>
          </Step>
          
          <Step>
            <StepLabel>高级设置</StepLabel>
            <StepContent>
              {renderAdvancedStep()}
              <Box sx={{ mb: 2, mt: 2 }}>
                <Button
                  variant="contained"
                  onClick={handleNext}
                  sx={{ mt: 1, mr: 1 }}
                >
                  下一步
                </Button>
                <Button
                  onClick={handleBack}
                  sx={{ mt: 1, mr: 1 }}
                >
                  上一步
                </Button>
              </Box>
            </StepContent>
          </Step>
          
          <Step>
            <StepLabel>确认并导出</StepLabel>
            <StepContent>
              {renderConfirmStep()}
              <Box sx={{ mb: 2, mt: 2 }}>
                <Button
                  variant="contained"
                  onClick={createExportTask}
                  disabled={loading}
                  startIcon={loading ? <CircularProgress size={20} /> : <ExportIcon />}
                  sx={{ mt: 1, mr: 1 }}
                >
                  {loading ? '导出中...' : '开始导出'}
                </Button>
                <Button
                  onClick={handleBack}
                  sx={{ mt: 1, mr: 1 }}
                >
                  上一步
                </Button>
                <Button
                  onClick={handleReset}
                  sx={{ mt: 1, mr: 1 }}
                >
                  重新开始
                </Button>
              </Box>
            </StepContent>
          </Step>
        </Stepper>
        
        {activeStep === STEPS.length && (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="h6" gutterBottom>
              导出任务已创建
            </Typography>
            <Typography color="textSecondary" gutterBottom>
              您可以在导出历史中查看进度和下载文件
            </Typography>
            <Button onClick={handleReset} sx={{ mt: 2 }}>
              创建新的导出任务
            </Button>
          </Box>
        )}
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose}>
          关闭
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ResultExportDialog;