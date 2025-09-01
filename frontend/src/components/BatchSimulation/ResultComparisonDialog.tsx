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
  Alert,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  TextField,
  Checkbox,
  FormControlLabel,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Tooltip,
  Divider
} from '@mui/material';
import {
  Compare as CompareIcon,
  ExpandMore as ExpandMoreIcon,
  Download as DownloadIcon,
  Visibility as VisibilityIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Assessment as AssessmentIcon,
  Timeline as TimelineIcon,
  BarChart as BarChartIcon,
  ScatterPlot as ScatterPlotIcon,
  TrendingUp as TrendingUpIcon
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar
} from 'recharts';
import { useApi } from '../../hooks/useApi';
import { JsonViewer } from '../Common/JsonViewer';

interface ComparisonConfig {
  comparison_type: 'statistical' | 'trend' | 'distribution' | 'correlation' | 'performance' | 'sensitivity';
  metrics: string[];
  grouping_fields?: string[];
  statistical_tests?: string[];
  confidence_level?: number;
  chart_types?: string[];
  export_format?: string;
}

interface ComparisonResult {
  id: string;
  name: string;
  comparison_type: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_at: string;
  completed_at?: string;
  results?: {
    summary: Record<string, any>;
    charts: Array<{
      type: string;
      title: string;
      data: any[];
      config: Record<string, any>;
    }>;
    statistics: Record<string, any>;
    insights: string[];
  };
  error_message?: string;
}

interface ResultComparisonDialogProps {
  open: boolean;
  onClose: () => void;
  selectedJobs: string[];
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
      id={`comparison-tabpanel-${index}`}
      aria-labelledby={`comparison-tab-${index}`}
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
    id: `comparison-tab-${index}`,
    'aria-controls': `comparison-tabpanel-${index}`,
  };
}

const COMPARISON_TYPES = [
  { value: 'statistical', label: '统计分析', description: '比较均值、方差、分布等统计指标' },
  { value: 'trend', label: '趋势分析', description: '分析时间序列数据的趋势变化' },
  { value: 'distribution', label: '分布分析', description: '比较数据分布特征和概率密度' },
  { value: 'correlation', label: '相关性分析', description: '分析变量间的相关关系' },
  { value: 'performance', label: '性能分析', description: '比较执行性能和资源使用情况' },
  { value: 'sensitivity', label: '敏感性分析', description: '分析参数变化对结果的影响' }
];

const CHART_TYPES = [
  { value: 'line', label: '折线图', icon: <TimelineIcon /> },
  { value: 'bar', label: '柱状图', icon: <BarChartIcon /> },
  { value: 'scatter', label: '散点图', icon: <ScatterPlotIcon /> },
  { value: 'pie', label: '饼图', icon: <AssessmentIcon /> },
  { value: 'radar', label: '雷达图', icon: <TrendingUpIcon /> }
];

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00ff00', '#ff00ff', '#00ffff', '#ffff00'];

export const ResultComparisonDialog: React.FC<ResultComparisonDialogProps> = ({
  open,
  onClose,
  selectedJobs
}) => {
  const [tabValue, setTabValue] = useState(0);
  const [config, setConfig] = useState<ComparisonConfig>({
    comparison_type: 'statistical',
    metrics: [],
    chart_types: ['line', 'bar']
  });
  const [availableMetrics, setAvailableMetrics] = useState<string[]>([]);
  const [comparisons, setComparisons] = useState<ComparisonResult[]>([]);
  const [selectedComparison, setSelectedComparison] = useState<ComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const api = useApi();

  // 获取可用的指标
  const fetchAvailableMetrics = async () => {
    try {
      const response = await api.post('/batch/comparison/metrics', {
        job_ids: selectedJobs
      });
      setAvailableMetrics(response.data.metrics || []);
    } catch (err: any) {
      setError(err.message || '获取可用指标失败');
    }
  };

  // 获取对比历史
  const fetchComparisons = async () => {
    try {
      const response = await api.get('/batch/comparison/history');
      setComparisons(response.data.comparisons || []);
    } catch (err: any) {
      setError(err.message || '获取对比历史失败');
    }
  };

  // 创建对比分析
  const createComparison = async () => {
    if (config.metrics.length === 0) {
      setError('请至少选择一个指标');
      return;
    }

    try {
      setLoading(true);
      const response = await api.post('/batch/comparison/create', {
        job_ids: selectedJobs,
        config: config,
        name: `对比分析_${new Date().toLocaleString()}`
      });
      
      const newComparison = response.data.comparison;
      setComparisons(prev => [newComparison, ...prev]);
      setSelectedComparison(newComparison);
      setTabValue(1); // 切换到结果标签页
      
      // 开始轮询状态
      pollComparisonStatus(newComparison.id);
    } catch (err: any) {
      setError(err.message || '创建对比分析失败');
    } finally {
      setLoading(false);
    }
  };

  // 轮询对比状态
  const pollComparisonStatus = async (comparisonId: string) => {
    const poll = async () => {
      try {
        const response = await api.get(`/batch/comparison/${comparisonId}`);
        const comparison = response.data.comparison;
        
        setComparisons(prev => 
          prev.map(c => c.id === comparisonId ? comparison : c)
        );
        
        if (selectedComparison?.id === comparisonId) {
          setSelectedComparison(comparison);
        }
        
        if (['completed', 'failed'].includes(comparison.status)) {
          return; // 停止轮询
        }
        
        setTimeout(poll, 2000); // 2秒后再次轮询
      } catch (err) {
        console.error('轮询对比状态失败:', err);
      }
    };
    
    poll();
  };

  // 下载对比结果
  const downloadComparison = async (comparisonId: string) => {
    try {
      const response = await api.get(`/batch/comparison/${comparisonId}/download`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `comparison_result_${comparisonId}.json`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message || '下载对比结果失败');
    }
  };

  // 删除对比
  const deleteComparison = async (comparisonId: string) => {
    try {
      await api.delete(`/batch/comparison/${comparisonId}`);
      setComparisons(prev => prev.filter(c => c.id !== comparisonId));
      if (selectedComparison?.id === comparisonId) {
        setSelectedComparison(null);
      }
    } catch (err: any) {
      setError(err.message || '删除对比失败');
    }
  };

  // 处理标签页切换
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  // 处理配置变更
  const handleConfigChange = (field: keyof ComparisonConfig, value: any) => {
    setConfig(prev => ({ ...prev, [field]: value }));
  };

  // 渲染图表
  const renderChart = (chart: any) => {
    const { type, title, data, config: chartConfig } = chart;
    
    switch (type) {
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <RechartsTooltip />
              <Legend />
              {chartConfig.lines?.map((line: any, index: number) => (
                <Line
                  key={line.dataKey}
                  type="monotone"
                  dataKey={line.dataKey}
                  stroke={COLORS[index % COLORS.length]}
                  name={line.name}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        );
        
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <RechartsTooltip />
              <Legend />
              {chartConfig.bars?.map((bar: any, index: number) => (
                <Bar
                  key={bar.dataKey}
                  dataKey={bar.dataKey}
                  fill={COLORS[index % COLORS.length]}
                  name={bar.name}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );
        
      case 'scatter':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="x" />
              <YAxis dataKey="y" />
              <RechartsTooltip />
              <Scatter fill={COLORS[0]} />
            </ScatterChart>
          </ResponsiveContainer>
        );
        
      case 'pie':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={data}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={80}
                label
              >
                {data.map((entry: any, index: number) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <RechartsTooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        );
        
      case 'radar':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={data}>
              <PolarGrid />
              <PolarAngleAxis dataKey="subject" />
              <PolarRadiusAxis />
              {chartConfig.radars?.map((radar: any, index: number) => (
                <Radar
                  key={radar.dataKey}
                  name={radar.name}
                  dataKey={radar.dataKey}
                  stroke={COLORS[index % COLORS.length]}
                  fill={COLORS[index % COLORS.length]}
                  fillOpacity={0.6}
                />
              ))}
              <Legend />
            </RadarChart>
          </ResponsiveContainer>
        );
        
      default:
        return (
          <Box sx={{ p: 2, textAlign: 'center' }}>
            <Typography color="textSecondary">
              不支持的图表类型: {type}
            </Typography>
          </Box>
        );
    }
  };

  // 初始化
  useEffect(() => {
    if (open && selectedJobs.length > 0) {
      fetchAvailableMetrics();
      fetchComparisons();
    }
  }, [open, selectedJobs]);

  // 渲染配置标签页
  const renderConfigTab = () => (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Alert severity="info">
          已选择 {selectedJobs.length} 个批量任务进行对比分析
        </Alert>
      </Grid>
      
      <Grid item xs={12} md={6}>
        <FormControl fullWidth>
          <InputLabel>对比类型</InputLabel>
          <Select
            value={config.comparison_type}
            onChange={(e) => handleConfigChange('comparison_type', e.target.value)}
          >
            {COMPARISON_TYPES.map((type) => (
              <MenuItem key={type.value} value={type.value}>
                <Box>
                  <Typography variant="subtitle2">{type.label}</Typography>
                  <Typography variant="caption" color="textSecondary">
                    {type.description}
                  </Typography>
                </Box>
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Grid>
      
      <Grid item xs={12} md={6}>
        <FormControl fullWidth>
          <InputLabel>图表类型</InputLabel>
          <Select
            multiple
            value={config.chart_types || []}
            onChange={(e) => handleConfigChange('chart_types', e.target.value)}
            renderValue={(selected) => (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                {(selected as string[]).map((value) => {
                  const chartType = CHART_TYPES.find(t => t.value === value);
                  return (
                    <Chip
                      key={value}
                      label={chartType?.label}
                      size="small"
                      icon={chartType?.icon}
                    />
                  );
                })}
              </Box>
            )}
          >
            {CHART_TYPES.map((type) => (
              <MenuItem key={type.value} value={type.value}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {type.icon}
                  {type.label}
                </Box>
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Grid>
      
      <Grid item xs={12}>
        <Typography variant="h6" gutterBottom>
          选择对比指标
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {availableMetrics.map((metric) => (
            <FormControlLabel
              key={metric}
              control={
                <Checkbox
                  checked={config.metrics.includes(metric)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      handleConfigChange('metrics', [...config.metrics, metric]);
                    } else {
                      handleConfigChange('metrics', config.metrics.filter(m => m !== metric));
                    }
                  }}
                />
              }
              label={metric}
            />
          ))}
        </Box>
      </Grid>
      
      {config.comparison_type === 'statistical' && (
        <Grid item xs={12}>
          <TextField
            fullWidth
            type="number"
            label="置信水平"
            value={config.confidence_level || 0.95}
            onChange={(e) => handleConfigChange('confidence_level', parseFloat(e.target.value))}
            inputProps={{ min: 0.8, max: 0.99, step: 0.01 }}
            helperText="统计检验的置信水平 (0.8-0.99)"
          />
        </Grid>
      )}
      
      <Grid item xs={12}>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
          <Button
            variant="contained"
            onClick={createComparison}
            disabled={loading || config.metrics.length === 0}
            startIcon={loading ? <CircularProgress size={20} /> : <CompareIcon />}
          >
            {loading ? '创建中...' : '开始对比分析'}
          </Button>
        </Box>
      </Grid>
    </Grid>
  );

  // 渲染结果标签页
  const renderResultsTab = () => (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">
          对比结果 ({comparisons.length})
        </Typography>
      </Box>
      
      <Grid container spacing={2}>
        {/* 对比列表 */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ height: 400, overflow: 'auto' }}>
            <List>
              {comparisons.map((comparison) => (
                <ListItem
                  key={comparison.id}
                  button
                  selected={selectedComparison?.id === comparison.id}
                  onClick={() => setSelectedComparison(comparison)}
                >
                  <ListItemText
                    primary={comparison.name}
                    secondary={
                      <Box>
                        <Typography variant="caption" display="block">
                          {comparison.comparison_type} | {comparison.created_at}
                        </Typography>
                        <Chip
                          label={comparison.status}
                          size="small"
                          color={
                            comparison.status === 'completed' ? 'success' :
                            comparison.status === 'failed' ? 'error' :
                            comparison.status === 'running' ? 'primary' : 'default'
                          }
                        />
                      </Box>
                    }
                  />
                  <ListItemSecondaryAction>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      {comparison.status === 'completed' && (
                        <Tooltip title="下载结果">
                          <IconButton
                            size="small"
                            onClick={() => downloadComparison(comparison.id)}
                          >
                            <DownloadIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                      <Tooltip title="删除">
                        <IconButton
                          size="small"
                          onClick={() => deleteComparison(comparison.id)}
                          color="error"
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>
        
        {/* 对比详情 */}
        <Grid item xs={12} md={8}>
          {selectedComparison ? (
            <Box>
              {selectedComparison.status === 'running' && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <CircularProgress size={20} />
                  <Typography>对比分析进行中...</Typography>
                </Box>
              )}
              
              {selectedComparison.status === 'failed' && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  对比分析失败: {selectedComparison.error_message}
                </Alert>
              )}
              
              {selectedComparison.status === 'completed' && selectedComparison.results && (
                <Box>
                  {/* 摘要 */}
                  <Card sx={{ mb: 2 }}>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        分析摘要
                      </Typography>
                      <JsonViewer data={selectedComparison.results.summary} />
                    </CardContent>
                  </Card>
                  
                  {/* 图表 */}
                  {selectedComparison.results.charts?.map((chart, index) => (
                    <Card key={index} sx={{ mb: 2 }}>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          {chart.title}
                        </Typography>
                        {renderChart(chart)}
                      </CardContent>
                    </Card>
                  ))}
                  
                  {/* 统计信息 */}
                  <Card sx={{ mb: 2 }}>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        统计信息
                      </Typography>
                      <JsonViewer data={selectedComparison.results.statistics} />
                    </CardContent>
                  </Card>
                  
                  {/* 洞察 */}
                  {selectedComparison.results.insights && selectedComparison.results.insights.length > 0 && (
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          分析洞察
                        </Typography>
                        <List>
                          {selectedComparison.results.insights.map((insight, index) => (
                            <ListItem key={index}>
                              <ListItemText primary={insight} />
                            </ListItem>
                          ))}
                        </List>
                      </CardContent>
                    </Card>
                  )}
                </Box>
              )}
            </Box>
          ) : (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography color="textSecondary">
                请选择一个对比结果查看详情
              </Typography>
            </Box>
          )}
        </Grid>
      </Grid>
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
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CompareIcon />
          <Typography variant="h6">
            结果对比分析
          </Typography>
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
              label="配置分析" 
              icon={<SettingsIcon />} 
              iconPosition="start"
              {...a11yProps(0)} 
            />
            <Tab 
              label="分析结果" 
              icon={<AssessmentIcon />} 
              iconPosition="start"
              {...a11yProps(1)} 
            />
          </Tabs>
        </Box>
        
        <TabPanel value={tabValue} index={0}>
          {renderConfigTab()}
        </TabPanel>
        
        <TabPanel value={tabValue} index={1}>
          {renderResultsTab()}
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

export default ResultComparisonDialog;