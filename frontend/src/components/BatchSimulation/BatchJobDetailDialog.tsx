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
  LinearProgress,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Alert,
  IconButton,
  Tooltip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  CircularProgress
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  PlayArrow as PlayArrowIcon,
  Cancel as CancelIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Visibility as VisibilityIcon,
  ExpandMore as ExpandMoreIcon,
  Timeline as TimelineIcon,
  Assessment as AssessmentIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';
import { useApi } from '../../hooks/useApi';
import { formatDateTime, formatDuration } from '../../utils/dateUtils';
import { JsonViewer } from '../Common/JsonViewer';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';

interface BatchJob {
  id: string;
  name: string;
  description?: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  created_at: string;
  updated_at: string;
  estimated_completion?: string;
  priority: 'low' | 'normal' | 'high';
  author: string;
  configuration?: Record<string, any>;
}

interface TaskDetail {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  parameters: Record<string, any>;
  configuration: Record<string, any>;
  result?: Record<string, any>;
  execution_time?: number;
  retry_count: number;
  max_retries: number;
}

interface ProgressData {
  timestamp: string;
  completed_tasks: number;
  failed_tasks: number;
  progress_percentage: number;
}

interface BatchJobDetailDialogProps {
  open: boolean;
  onClose: () => void;
  job: BatchJob | null;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`job-detail-tabpanel-${index}`}
      aria-labelledby={`job-detail-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `job-detail-tab-${index}`,
    'aria-controls': `job-detail-tabpanel-${index}`,
  };
}

export const BatchJobDetailDialog: React.FC<BatchJobDetailDialogProps> = ({
  open,
  onClose,
  job
}) => {
  const [tabValue, setTabValue] = useState(0);
  const [tasks, setTasks] = useState<TaskDetail[]>([]);
  const [progressData, setProgressData] = useState<ProgressData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  
  const api = useApi();

  // 获取任务详情
  const fetchJobDetails = async () => {
    if (!job) return;
    
    try {
      setLoading(true);
      const response = await api.get(`/batch/jobs/${job.id}/details`);
      setTasks(response.data.tasks || []);
      setProgressData(response.data.progress_history || []);
    } catch (err: any) {
      setError(err.message || '获取任务详情失败');
    } finally {
      setLoading(false);
    }
  };

  // 下载任务结果
  const downloadTaskResult = async (taskId: string) => {
    try {
      const response = await api.get(`/batch/tasks/${taskId}/download`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `task_result_${taskId}.json`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message || '下载任务结果失败');
    }
  };

  // 重试失败的任务
  const retryTask = async (taskId: string) => {
    try {
      await api.post(`/batch/tasks/${taskId}/retry`);
      fetchJobDetails();
    } catch (err: any) {
      setError(err.message || '重试任务失败');
    }
  };

  // 获取状态图标
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <ScheduleIcon color="disabled" />;
      case 'running':
        return <CircularProgress size={20} />;
      case 'completed':
        return <CheckCircleIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      case 'cancelled':
        return <CancelIcon color="warning" />;
      default:
        return <ScheduleIcon color="disabled" />;
    }
  };

  // 获取状态颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'default';
      case 'running': return 'primary';
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'cancelled': return 'warning';
      default: return 'default';
    }
  };

  // 处理标签页切换
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  // 自动刷新
  useEffect(() => {
    if (open && job && autoRefresh && ['pending', 'running'].includes(job.status)) {
      const interval = setInterval(fetchJobDetails, 5000); // 每5秒刷新一次
      return () => clearInterval(interval);
    }
  }, [open, job, autoRefresh]);

  // 初始加载
  useEffect(() => {
    if (open && job) {
      fetchJobDetails();
    }
  }, [open, job]);

  if (!job) {
    return null;
  }

  // 渲染概览标签页
  const renderOverviewTab = () => (
    <Grid container spacing={3}>
      {/* 基本信息 */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              基本信息
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" color="textSecondary">
                任务名称
              </Typography>
              <Typography variant="body1">{job.name}</Typography>
            </Box>
            
            {job.description && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="textSecondary">
                  任务描述
                </Typography>
                <Typography variant="body1">{job.description}</Typography>
              </Box>
            )}
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" color="textSecondary">
                状态
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                {getStatusIcon(job.status)}
                <Chip
                  label={job.status}
                  color={getStatusColor(job.status) as any}
                  size="small"
                />
              </Box>
            </Box>
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" color="textSecondary">
                优先级
              </Typography>
              <Chip
                label={job.priority}
                color={job.priority === 'high' ? 'error' : job.priority === 'normal' ? 'primary' : 'default'}
                size="small"
                variant="outlined"
              />
            </Box>
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" color="textSecondary">
                创建者
              </Typography>
              <Typography variant="body1">{job.author}</Typography>
            </Box>
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" color="textSecondary">
                创建时间
              </Typography>
              <Typography variant="body1">{formatDateTime(job.created_at)}</Typography>
            </Box>
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" color="textSecondary">
                更新时间
              </Typography>
              <Typography variant="body1">{formatDateTime(job.updated_at)}</Typography>
            </Box>
            
            {job.estimated_completion && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="textSecondary">
                  预计完成时间
                </Typography>
                <Typography variant="body1">{formatDateTime(job.estimated_completion)}</Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid>
      
      {/* 执行统计 */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              执行统计
            </Typography>
            
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                总体进度
              </Typography>
              <LinearProgress
                variant="determinate"
                value={job.progress}
                sx={{ height: 8, borderRadius: 4, mb: 1 }}
              />
              <Typography variant="body2" color="textSecondary">
                {job.progress.toFixed(1)}% 完成
              </Typography>
            </Box>
            
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'primary.light', borderRadius: 1 }}>
                  <Typography variant="h4" color="primary.contrastText">
                    {job.total_tasks}
                  </Typography>
                  <Typography variant="caption" color="primary.contrastText">
                    总任务数
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6}>
                <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'success.light', borderRadius: 1 }}>
                  <Typography variant="h4" color="success.contrastText">
                    {job.completed_tasks}
                  </Typography>
                  <Typography variant="caption" color="success.contrastText">
                    已完成
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6}>
                <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'warning.light', borderRadius: 1 }}>
                  <Typography variant="h4" color="warning.contrastText">
                    {job.total_tasks - job.completed_tasks - job.failed_tasks}
                  </Typography>
                  <Typography variant="caption" color="warning.contrastText">
                    待执行
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6}>
                <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'error.light', borderRadius: 1 }}>
                  <Typography variant="h4" color="error.contrastText">
                    {job.failed_tasks}
                  </Typography>
                  <Typography variant="caption" color="error.contrastText">
                    失败
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>
      
      {/* 配置信息 */}
      {job.configuration && (
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                任务配置
              </Typography>
              <JsonViewer data={job.configuration} />
            </CardContent>
          </Card>
        </Grid>
      )}
    </Grid>
  );

  // 渲染任务列表标签页
  const renderTasksTab = () => (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">
          任务列表 ({tasks.length})
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            size="small"
            startIcon={<RefreshIcon />}
            onClick={fetchJobDetails}
            disabled={loading}
          >
            刷新
          </Button>
        </Box>
      </Box>
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>任务名称</TableCell>
                <TableCell>状态</TableCell>
                <TableCell>进度</TableCell>
                <TableCell>执行时间</TableCell>
                <TableCell>重试</TableCell>
                <TableCell>操作</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {tasks.map((task) => (
                <TableRow key={task.id}>
                  <TableCell>
                    <Typography variant="subtitle2">{task.name}</Typography>
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {getStatusIcon(task.status)}
                      <Chip
                        label={task.status}
                        color={getStatusColor(task.status) as any}
                        size="small"
                      />
                    </Box>
                  </TableCell>
                  <TableCell>
                    <LinearProgress
                      variant="determinate"
                      value={task.progress}
                      sx={{ width: 100 }}
                    />
                    <Typography variant="caption">
                      {task.progress.toFixed(1)}%
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="caption">
                      {task.execution_time ? `${task.execution_time.toFixed(2)}s` : '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="caption">
                      {task.retry_count}/{task.max_retries}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      {task.status === 'completed' && task.result && (
                        <Tooltip title="下载结果">
                          <IconButton
                            size="small"
                            onClick={() => downloadTaskResult(task.id)}
                          >
                            <DownloadIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                      {task.status === 'failed' && task.retry_count < task.max_retries && (
                        <Tooltip title="重试">
                          <IconButton
                            size="small"
                            onClick={() => retryTask(task.id)}
                            color="warning"
                          >
                            <RefreshIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
      
      {/* 任务详情手风琴 */}
      <Box sx={{ mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          任务详情
        </Typography>
        {tasks.map((task) => (
          <Accordion key={task.id}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                {getStatusIcon(task.status)}
                <Typography variant="subtitle1" sx={{ flexGrow: 1 }}>
                  {task.name}
                </Typography>
                <Chip
                  label={task.status}
                  color={getStatusColor(task.status) as any}
                  size="small"
                />
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    参数
                  </Typography>
                  <JsonViewer data={task.parameters} />
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    配置
                  </Typography>
                  <JsonViewer data={task.configuration} />
                </Grid>
                {task.result && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" gutterBottom>
                      结果
                    </Typography>
                    <JsonViewer data={task.result} />
                  </Grid>
                )}
                {task.error_message && (
                  <Grid item xs={12}>
                    <Alert severity="error">
                      <Typography variant="subtitle2">错误信息</Typography>
                      <Typography variant="body2">{task.error_message}</Typography>
                    </Alert>
                  </Grid>
                )}
                <Grid item xs={12}>
                  <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                    {task.started_at && (
                      <Typography variant="caption">
                        开始时间: {formatDateTime(task.started_at)}
                      </Typography>
                    )}
                    {task.completed_at && (
                      <Typography variant="caption">
                        完成时间: {formatDateTime(task.completed_at)}
                      </Typography>
                    )}
                    {task.execution_time && (
                      <Typography variant="caption">
                        执行时间: {task.execution_time.toFixed(2)}秒
                      </Typography>
                    )}
                  </Box>
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        ))}
      </Box>
    </Box>
  );

  // 渲染进度图表标签页
  const renderProgressTab = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        执行进度趋势
      </Typography>
      
      {progressData.length > 0 ? (
        <Box sx={{ height: 400, mt: 2 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={progressData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="timestamp" 
                tickFormatter={(value) => new Date(value).toLocaleTimeString()}
              />
              <YAxis />
              <RechartsTooltip 
                labelFormatter={(value) => formatDateTime(value)}
              />
              <Line 
                type="monotone" 
                dataKey="completed_tasks" 
                stroke="#4caf50" 
                name="已完成任务"
                strokeWidth={2}
              />
              <Line 
                type="monotone" 
                dataKey="failed_tasks" 
                stroke="#f44336" 
                name="失败任务"
                strokeWidth={2}
              />
              <Line 
                type="monotone" 
                dataKey="progress_percentage" 
                stroke="#2196f3" 
                name="完成百分比"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </Box>
      ) : (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography color="textSecondary">
            暂无进度数据
          </Typography>
        </Box>
      )}
    </Box>
  );

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="xl"
      fullWidth
      PaperProps={{
        sx: { height: '90vh' }
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AssessmentIcon />
            <Typography variant="h6">
              {job.name} - 任务详情
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title={autoRefresh ? '关闭自动刷新' : '开启自动刷新'}>
              <IconButton
                onClick={() => setAutoRefresh(!autoRefresh)}
                color={autoRefresh ? 'primary' : 'default'}
              >
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
        
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange}>
            <Tab 
              label="概览" 
              icon={<AssessmentIcon />} 
              iconPosition="start"
              {...a11yProps(0)} 
            />
            <Tab 
              label="任务列表" 
              icon={<SettingsIcon />} 
              iconPosition="start"
              {...a11yProps(1)} 
            />
            <Tab 
              label="进度图表" 
              icon={<TimelineIcon />} 
              iconPosition="start"
              {...a11yProps(2)} 
            />
          </Tabs>
        </Box>
        
        <TabPanel value={tabValue} index={0}>
          {renderOverviewTab()}
        </TabPanel>
        
        <TabPanel value={tabValue} index={1}>
          {renderTasksTab()}
        </TabPanel>
        
        <TabPanel value={tabValue} index={2}>
          {renderProgressTab()}
        </TabPanel>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose}>
          关闭
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default BatchJobDetailDialog;