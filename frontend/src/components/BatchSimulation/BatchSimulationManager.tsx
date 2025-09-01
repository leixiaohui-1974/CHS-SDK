import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Alert,
  Snackbar,
  Tabs,
  Tab,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Divider
} from '@mui/material';
import {
  Add as AddIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  ExpandMore as ExpandMoreIcon,
  Settings as SettingsIcon,
  Assessment as AssessmentIcon,
  GetApp as ExportIcon
} from '@mui/icons-material';
import { useApi } from '../../hooks/useApi';
import { formatDateTime, formatDuration } from '../../utils/dateUtils';
import { BatchJobSubmissionDialog } from './BatchJobSubmissionDialog';
import { BatchJobDetailDialog } from './BatchJobDetailDialog';
import { ResultComparisonDialog } from './ResultComparisonDialog';
import { ResultExportDialog } from './ResultExportDialog';
import { TemplateManagerDialog } from './TemplateManagerDialog';

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
      id={`batch-tabpanel-${index}`}
      aria-labelledby={`batch-tab-${index}`}
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
    id: `batch-tab-${index}`,
    'aria-controls': `batch-tabpanel-${index}`,
  };
}

export const BatchSimulationManager: React.FC = () => {
  const [jobs, setJobs] = useState<BatchJob[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedJob, setSelectedJob] = useState<BatchJob | null>(null);
  const [tabValue, setTabValue] = useState(0);
  
  // 对话框状态
  const [submissionDialogOpen, setSubmissionDialogOpen] = useState(false);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [comparisonDialogOpen, setComparisonDialogOpen] = useState(false);
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [templateDialogOpen, setTemplateDialogOpen] = useState(false);
  
  // 通知状态
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success' as 'success' | 'error' | 'warning' | 'info'
  });
  
  const api = useApi();

  // 获取批量任务列表
  const fetchJobs = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get('/batch/jobs');
      setJobs(response.data.jobs || []);
    } catch (err: any) {
      setError(err.message || '获取任务列表失败');
      showSnackbar('获取任务列表失败', 'error');
    } finally {
      setLoading(false);
    }
  }, [api]);

  // 取消任务
  const cancelJob = async (jobId: string) => {
    try {
      await api.post(`/batch/jobs/${jobId}/cancel`);
      showSnackbar('任务已取消', 'success');
      fetchJobs();
    } catch (err: any) {
      showSnackbar(err.message || '取消任务失败', 'error');
    }
  };

  // 删除任务
  const deleteJob = async (jobId: string) => {
    try {
      await api.delete(`/batch/jobs/${jobId}`);
      showSnackbar('任务已删除', 'success');
      fetchJobs();
    } catch (err: any) {
      showSnackbar(err.message || '删除任务失败', 'error');
    }
  };

  // 下载结果
  const downloadResults = async (jobId: string) => {
    try {
      const response = await api.get(`/batch/jobs/${jobId}/download`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `batch_results_${jobId}.zip`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      showSnackbar('结果下载成功', 'success');
    } catch (err: any) {
      showSnackbar(err.message || '下载结果失败', 'error');
    }
  };

  // 显示通知
  const showSnackbar = (message: string, severity: 'success' | 'error' | 'warning' | 'info') => {
    setSnackbar({ open: true, message, severity });
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

  // 获取优先级颜色
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'error';
      case 'normal': return 'primary';
      case 'low': return 'default';
      default: return 'default';
    }
  };

  // 处理标签页切换
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  // 查看任务详情
  const viewJobDetail = (job: BatchJob) => {
    setSelectedJob(job);
    setDetailDialogOpen(true);
  };

  // 任务提交成功回调
  const handleJobSubmitted = () => {
    setSubmissionDialogOpen(false);
    showSnackbar('批量任务提交成功', 'success');
    fetchJobs();
  };

  // 组件挂载时获取数据
  useEffect(() => {
    fetchJobs();
    
    // 设置定时刷新
    const interval = setInterval(fetchJobs, 10000); // 每10秒刷新一次
    return () => clearInterval(interval);
  }, [fetchJobs]);

  // 渲染任务列表
  const renderJobList = () => (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>任务名称</TableCell>
            <TableCell>状态</TableCell>
            <TableCell>进度</TableCell>
            <TableCell>优先级</TableCell>
            <TableCell>创建时间</TableCell>
            <TableCell>作者</TableCell>
            <TableCell>操作</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {jobs.map((job) => (
            <TableRow key={job.id}>
              <TableCell>
                <Box>
                  <Typography variant="subtitle2">{job.name}</Typography>
                  {job.description && (
                    <Typography variant="caption" color="textSecondary">
                      {job.description}
                    </Typography>
                  )}
                </Box>
              </TableCell>
              <TableCell>
                <Chip
                  label={job.status}
                  color={getStatusColor(job.status) as any}
                  size="small"
                />
              </TableCell>
              <TableCell>
                <Box sx={{ width: '100%', mr: 1 }}>
                  <LinearProgress
                    variant="determinate"
                    value={job.progress}
                    sx={{ mb: 1 }}
                  />
                  <Typography variant="caption">
                    {job.completed_tasks}/{job.total_tasks} 任务
                    {job.failed_tasks > 0 && (
                      <span style={{ color: 'red' }}> ({job.failed_tasks} 失败)</span>
                    )}
                  </Typography>
                </Box>
              </TableCell>
              <TableCell>
                <Chip
                  label={job.priority}
                  color={getPriorityColor(job.priority) as any}
                  size="small"
                  variant="outlined"
                />
              </TableCell>
              <TableCell>
                <Typography variant="caption">
                  {formatDateTime(job.created_at)}
                </Typography>
              </TableCell>
              <TableCell>
                <Typography variant="caption">
                  {job.author}
                </Typography>
              </TableCell>
              <TableCell>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Tooltip title="查看详情">
                    <IconButton
                      size="small"
                      onClick={() => viewJobDetail(job)}
                    >
                      <ViewIcon />
                    </IconButton>
                  </Tooltip>
                  
                  {job.status === 'running' && (
                    <Tooltip title="取消任务">
                      <IconButton
                        size="small"
                        onClick={() => cancelJob(job.id)}
                        color="warning"
                      >
                        <StopIcon />
                      </IconButton>
                    </Tooltip>
                  )}
                  
                  {job.status === 'completed' && (
                    <Tooltip title="下载结果">
                      <IconButton
                        size="small"
                        onClick={() => downloadResults(job.id)}
                        color="primary"
                      >
                        <DownloadIcon />
                      </IconButton>
                    </Tooltip>
                  )}
                  
                  {['completed', 'failed', 'cancelled'].includes(job.status) && (
                    <Tooltip title="删除任务">
                      <IconButton
                        size="small"
                        onClick={() => deleteJob(job.id)}
                        color="error"
                      >
                        <DeleteIcon />
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
  );

  // 渲染统计信息
  const renderStatistics = () => {
    const totalJobs = jobs.length;
    const runningJobs = jobs.filter(job => job.status === 'running').length;
    const completedJobs = jobs.filter(job => job.status === 'completed').length;
    const failedJobs = jobs.filter(job => job.status === 'failed').length;

    return (
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                总任务数
              </Typography>
              <Typography variant="h4">
                {totalJobs}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                运行中
              </Typography>
              <Typography variant="h4" color="primary">
                {runningJobs}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                已完成
              </Typography>
              <Typography variant="h4" color="success.main">
                {completedJobs}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                失败
              </Typography>
              <Typography variant="h4" color="error.main">
                {failedJobs}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    );
  };

  return (
    <Box sx={{ width: '100%' }}>
      {/* 页面标题和操作按钮 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          批量仿真管理
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<SettingsIcon />}
            onClick={() => setTemplateDialogOpen(true)}
          >
            模板管理
          </Button>
          <Button
            variant="outlined"
            startIcon={<AssessmentIcon />}
            onClick={() => setComparisonDialogOpen(true)}
          >
            结果对比
          </Button>
          <Button
            variant="outlined"
            startIcon={<ExportIcon />}
            onClick={() => setExportDialogOpen(true)}
          >
            导出结果
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setSubmissionDialogOpen(true)}
          >
            新建批量任务
          </Button>
        </Box>
      </Box>

      {/* 错误提示 */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* 统计信息 */}
      {renderStatistics()}

      {/* 标签页 */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="批量仿真标签页">
          <Tab label="任务列表" {...a11yProps(0)} />
          <Tab label="运行中任务" {...a11yProps(1)} />
          <Tab label="已完成任务" {...a11yProps(2)} />
        </Tabs>
      </Box>

      {/* 标签页内容 */}
      <TabPanel value={tabValue} index={0}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">所有任务</Typography>
          <Button
            startIcon={<RefreshIcon />}
            onClick={fetchJobs}
            disabled={loading}
          >
            刷新
          </Button>
        </Box>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <LinearProgress sx={{ width: '50%' }} />
          </Box>
        ) : (
          renderJobList()
        )}
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">运行中任务</Typography>
          <Button
            startIcon={<RefreshIcon />}
            onClick={fetchJobs}
            disabled={loading}
          >
            刷新
          </Button>
        </Box>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <LinearProgress sx={{ width: '50%' }} />
          </Box>
        ) : (
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>任务名称</TableCell>
                  <TableCell>进度</TableCell>
                  <TableCell>预计完成时间</TableCell>
                  <TableCell>操作</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {jobs.filter(job => job.status === 'running').map((job) => (
                  <TableRow key={job.id}>
                    <TableCell>
                      <Box>
                        <Typography variant="subtitle2">{job.name}</Typography>
                        <Typography variant="caption" color="textSecondary">
                          {job.description}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ width: '100%', mr: 1 }}>
                        <LinearProgress
                          variant="determinate"
                          value={job.progress}
                          sx={{ mb: 1 }}
                        />
                        <Typography variant="caption">
                          {job.completed_tasks}/{job.total_tasks} 任务 ({job.progress.toFixed(1)}%)
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption">
                        {job.estimated_completion ? formatDateTime(job.estimated_completion) : '计算中...'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Tooltip title="查看详情">
                          <IconButton
                            size="small"
                            onClick={() => viewJobDetail(job)}
                          >
                            <ViewIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="取消任务">
                          <IconButton
                            size="small"
                            onClick={() => cancelJob(job.id)}
                            color="warning"
                          >
                            <StopIcon />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">已完成任务</Typography>
          <Button
            startIcon={<RefreshIcon />}
            onClick={fetchJobs}
            disabled={loading}
          >
            刷新
          </Button>
        </Box>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <LinearProgress sx={{ width: '50%' }} />
          </Box>
        ) : (
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>任务名称</TableCell>
                  <TableCell>状态</TableCell>
                  <TableCell>完成时间</TableCell>
                  <TableCell>耗时</TableCell>
                  <TableCell>操作</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {jobs.filter(job => ['completed', 'failed', 'cancelled'].includes(job.status)).map((job) => (
                  <TableRow key={job.id}>
                    <TableCell>
                      <Box>
                        <Typography variant="subtitle2">{job.name}</Typography>
                        <Typography variant="caption" color="textSecondary">
                          {job.description}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={job.status}
                        color={getStatusColor(job.status) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption">
                        {formatDateTime(job.updated_at)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption">
                        {formatDuration(new Date(job.created_at), new Date(job.updated_at))}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Tooltip title="查看详情">
                          <IconButton
                            size="small"
                            onClick={() => viewJobDetail(job)}
                          >
                            <ViewIcon />
                          </IconButton>
                        </Tooltip>
                        {job.status === 'completed' && (
                          <Tooltip title="下载结果">
                            <IconButton
                              size="small"
                              onClick={() => downloadResults(job.id)}
                              color="primary"
                            >
                              <DownloadIcon />
                            </IconButton>
                          </Tooltip>
                        )}
                        <Tooltip title="删除任务">
                          <IconButton
                            size="small"
                            onClick={() => deleteJob(job.id)}
                            color="error"
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </TabPanel>

      {/* 对话框组件 */}
      <BatchJobSubmissionDialog
        open={submissionDialogOpen}
        onClose={() => setSubmissionDialogOpen(false)}
        onSubmitted={handleJobSubmitted}
      />

      <BatchJobDetailDialog
        open={detailDialogOpen}
        onClose={() => setDetailDialogOpen(false)}
        job={selectedJob}
      />

      <ResultComparisonDialog
        open={comparisonDialogOpen}
        onClose={() => setComparisonDialogOpen(false)}
        jobs={jobs.filter(job => job.status === 'completed')}
      />

      <ResultExportDialog
        open={exportDialogOpen}
        onClose={() => setExportDialogOpen(false)}
        jobs={jobs.filter(job => job.status === 'completed')}
      />

      <TemplateManagerDialog
        open={templateDialogOpen}
        onClose={() => setTemplateDialogOpen(false)}
      />

      {/* 通知组件 */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default BatchSimulationManager;