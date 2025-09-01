import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  IconButton,
  Chip,
  Stack,
  Tabs,
  Tab,
  SwipeableDrawer,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Switch,
  Slider,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Grid,
  Paper,
  useTheme,
  useMediaQuery,
  Fab,
  SpeedDial,
  SpeedDialAction,
  SpeedDialIcon,
  Tooltip,
  CircularProgress,
  Alert,
  Collapse
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Fullscreen as FullscreenIcon,
  FullscreenExit as FullscreenExitIcon,
  Download as DownloadIcon,
  Share as ShareIcon,
  Refresh as RefreshIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  PanTool as PanIcon,
  Timeline as TimelineIcon,
  BarChart as BarChartIcon,
  PieChart as PieChartIcon,
  ShowChart as LineChartIcon,
  ScatterPlot as ScatterIcon,
  TableChart as TableIcon,
  Map as HeatmapIcon,
  Visibility as ViewIcon,
  VisibilityOff as HideIcon,
  FilterList as FilterIcon,
  Sort as SortIcon,
  Search as SearchIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  SkipNext as NextIcon,
  SkipPrevious as PrevIcon
} from '@mui/icons-material';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ReferenceLine
} from 'recharts';

interface DataPoint {
  x: number | string;
  y: number;
  label?: string;
  category?: string;
  [key: string]: any;
}

interface ChartConfig {
  type: 'line' | 'area' | 'bar' | 'scatter' | 'pie' | 'heatmap';
  title: string;
  xAxis?: string;
  yAxis?: string;
  color?: string;
  showGrid?: boolean;
  showLegend?: boolean;
  animated?: boolean;
}

interface MobileDataVisualizationProps {
  data: DataPoint[];
  charts: ChartConfig[];
  loading?: boolean;
  error?: string;
  onRefresh?: () => void;
  onExport?: (format: string) => void;
  onShare?: () => void;
  realTime?: boolean;
  compact?: boolean;
}

const chartIcons = {
  line: <LineChartIcon />,
  area: <LineChartIcon />,
  bar: <BarChartIcon />,
  scatter: <ScatterIcon />,
  pie: <PieChartIcon />,
  heatmap: <HeatmapIcon />
};

const colors = [
  '#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00ff00',
  '#ff0000', '#00ffff', '#ff00ff', '#ffff00', '#0000ff'
];

export const MobileDataVisualization: React.FC<MobileDataVisualizationProps> = ({
  data,
  charts,
  loading = false,
  error,
  onRefresh,
  onExport,
  onShare,
  realTime = false,
  compact = false
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const containerRef = useRef<HTMLDivElement>(null);
  
  const [activeTab, setActiveTab] = useState(0);
  const [fullscreen, setFullscreen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [chartSettings, setChartSettings] = useState<Record<string, any>>({});
  const [zoomLevel, setZoomLevel] = useState(1);
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const [showControls, setShowControls] = useState(true);
  const [animationSpeed, setAnimationSpeed] = useState(1000);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [filterExpanded, setFilterExpanded] = useState(false);
  const [filters, setFilters] = useState<Record<string, any>>({});
  const [sortBy, setSortBy] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState('');

  // 过滤和排序数据
  const processedData = React.useMemo(() => {
    let result = [...data];
    
    // 搜索过滤
    if (searchTerm) {
      result = result.filter(item => 
        Object.values(item).some(value => 
          String(value).toLowerCase().includes(searchTerm.toLowerCase())
        )
      );
    }
    
    // 自定义过滤
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== '') {
        result = result.filter(item => item[key] === value);
      }
    });
    
    // 排序
    if (sortBy) {
      result.sort((a, b) => {
        const aVal = a[sortBy];
        const bVal = b[sortBy];
        if (typeof aVal === 'number' && typeof bVal === 'number') {
          return aVal - bVal;
        }
        return String(aVal).localeCompare(String(bVal));
      });
    }
    
    return result;
  }, [data, searchTerm, filters, sortBy]);

  // 动画播放
  useEffect(() => {
    if (isPlaying && realTime) {
      const interval = setInterval(() => {
        setCurrentFrame(prev => (prev + 1) % processedData.length);
      }, animationSpeed);
      return () => clearInterval(interval);
    }
  }, [isPlaying, animationSpeed, processedData.length, realTime]);

  // 渲染图表
  const renderChart = (config: ChartConfig, index: number) => {
    const chartData = realTime ? processedData.slice(0, currentFrame + 1) : processedData;
    
    const commonProps = {
      data: chartData,
      margin: { top: 5, right: 5, left: 5, bottom: 5 }
    };

    switch (config.type) {
      case 'line':
        return (
          <LineChart {...commonProps}>
            {config.showGrid && <CartesianGrid strokeDasharray="3 3" />}
            <XAxis 
              dataKey={config.xAxis || 'x'} 
              tick={{ fontSize: 10 }}
              interval="preserveStartEnd"
            />
            <YAxis tick={{ fontSize: 10 }} />
            <RechartsTooltip />
            {config.showLegend && <Legend />}
            <Line 
              type="monotone" 
              dataKey={config.yAxis || 'y'} 
              stroke={config.color || colors[index % colors.length]}
              strokeWidth={2}
              dot={{ r: 2 }}
              animationDuration={config.animated ? 1000 : 0}
            />
          </LineChart>
        );
        
      case 'area':
        return (
          <AreaChart {...commonProps}>
            {config.showGrid && <CartesianGrid strokeDasharray="3 3" />}
            <XAxis dataKey={config.xAxis || 'x'} tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} />
            <RechartsTooltip />
            {config.showLegend && <Legend />}
            <Area 
              type="monotone" 
              dataKey={config.yAxis || 'y'} 
              stroke={config.color || colors[index % colors.length]}
              fill={config.color || colors[index % colors.length]}
              fillOpacity={0.3}
              animationDuration={config.animated ? 1000 : 0}
            />
          </AreaChart>
        );
        
      case 'bar':
        return (
          <BarChart {...commonProps}>
            {config.showGrid && <CartesianGrid strokeDasharray="3 3" />}
            <XAxis dataKey={config.xAxis || 'x'} tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} />
            <RechartsTooltip />
            {config.showLegend && <Legend />}
            <Bar 
              dataKey={config.yAxis || 'y'} 
              fill={config.color || colors[index % colors.length]}
              animationDuration={config.animated ? 1000 : 0}
            />
          </BarChart>
        );
        
      case 'scatter':
        return (
          <ScatterChart {...commonProps}>
            {config.showGrid && <CartesianGrid strokeDasharray="3 3" />}
            <XAxis dataKey={config.xAxis || 'x'} tick={{ fontSize: 10 }} />
            <YAxis dataKey={config.yAxis || 'y'} tick={{ fontSize: 10 }} />
            <RechartsTooltip />
            {config.showLegend && <Legend />}
            <Scatter 
              data={chartData} 
              fill={config.color || colors[index % colors.length]}
            />
          </ScatterChart>
        );
        
      case 'pie':
        return (
          <PieChart {...commonProps}>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              outerRadius={60}
              fill={config.color || colors[index % colors.length]}
              dataKey={config.yAxis || 'y'}
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              labelLine={false}
              animationDuration={config.animated ? 1000 : 0}
            >
              {chartData.map((entry, i) => (
                <Cell key={`cell-${i}`} fill={colors[i % colors.length]} />
              ))}
            </Pie>
            <RechartsTooltip />
          </PieChart>
        );
        
      default:
        return (
          <Box sx={{ 
            height: 200, 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center' 
          }}>
            <Typography color="text.secondary">
              不支持的图表类型: {config.type}
            </Typography>
          </Box>
        );
    }
  };

  // 渲染控制面板
  const renderControls = () => (
    <SwipeableDrawer
      anchor="bottom"
      open={settingsOpen}
      onClose={() => setSettingsOpen(false)}
      onOpen={() => setSettingsOpen(true)}
      disableSwipeToOpen={false}
      PaperProps={{
        sx: {
          maxHeight: '80vh',
          borderTopLeftRadius: 16,
          borderTopRightRadius: 16
        }
      }}
    >
      <Box sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          图表设置
        </Typography>
        
        {/* 搜索和过滤 */}
        <Box sx={{ mb: 2 }}>
          <TextField
            fullWidth
            size="small"
            placeholder="搜索数据..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
            }}
            sx={{ mb: 1 }}
          />
          
          <Button
            startIcon={filterExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            onClick={() => setFilterExpanded(!filterExpanded)}
            size="small"
          >
            高级过滤
          </Button>
          
          <Collapse in={filterExpanded}>
            <Box sx={{ mt: 1 }}>
              <FormControl fullWidth size="small" sx={{ mb: 1 }}>
                <InputLabel>排序字段</InputLabel>
                <Select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                >
                  <MenuItem value="">无</MenuItem>
                  <MenuItem value="x">X轴</MenuItem>
                  <MenuItem value="y">Y轴</MenuItem>
                  <MenuItem value="category">类别</MenuItem>
                </Select>
              </FormControl>
            </Box>
          </Collapse>
        </Box>
        
        {/* 实时播放控制 */}
        {realTime && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              实时播放
            </Typography>
            
            <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
              <IconButton 
                onClick={() => setCurrentFrame(Math.max(0, currentFrame - 1))}
                disabled={currentFrame === 0}
              >
                <PrevIcon />
              </IconButton>
              
              <IconButton onClick={() => setIsPlaying(!isPlaying)}>
                {isPlaying ? <PauseIcon /> : <PlayIcon />}
              </IconButton>
              
              <IconButton 
                onClick={() => setCurrentFrame(Math.min(processedData.length - 1, currentFrame + 1))}
                disabled={currentFrame === processedData.length - 1}
              >
                <NextIcon />
              </IconButton>
              
              <Typography variant="caption">
                {currentFrame + 1} / {processedData.length}
              </Typography>
            </Stack>
            
            <Typography variant="caption" gutterBottom>
              播放速度 (ms)
            </Typography>
            <Slider
              value={animationSpeed}
              onChange={(_, value) => setAnimationSpeed(value as number)}
              min={100}
              max={3000}
              step={100}
              valueLabelDisplay="auto"
            />
          </Box>
        )}
        
        {/* 缩放控制 */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            缩放级别
          </Typography>
          <Stack direction="row" spacing={1} alignItems="center">
            <IconButton onClick={() => setZoomLevel(Math.max(0.5, zoomLevel - 0.1))}>
              <ZoomOutIcon />
            </IconButton>
            <Slider
              value={zoomLevel}
              onChange={(_, value) => setZoomLevel(value as number)}
              min={0.5}
              max={3}
              step={0.1}
              sx={{ flexGrow: 1 }}
            />
            <IconButton onClick={() => setZoomLevel(Math.min(3, zoomLevel + 0.1))}>
              <ZoomInIcon />
            </IconButton>
          </Stack>
        </Box>
        
        {/* 图表选项 */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            显示选项
          </Typography>
          
          <List dense>
            <ListItem>
              <ListItemIcon>
                <ViewIcon />
              </ListItemIcon>
              <ListItemText primary="显示控制栏" />
              <Switch
                checked={showControls}
                onChange={(e) => setShowControls(e.target.checked)}
              />
            </ListItem>
          </List>
        </Box>
      </Box>
    </SwipeableDrawer>
  );

  if (!isMobile) {
    return null;
  }

  if (loading) {
    return (
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: 200 
      }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 1 }}>
        {error}
      </Alert>
    );
  }

  return (
    <>
      <Box ref={containerRef} sx={{ position: 'relative' }}>
        {/* 图表标签页 */}
        {charts.length > 1 && (
          <Tabs
            value={activeTab}
            onChange={(_, newValue) => setActiveTab(newValue)}
            variant="scrollable"
            scrollButtons="auto"
            sx={{ borderBottom: 1, borderColor: 'divider' }}
          >
            {charts.map((chart, index) => (
              <Tab
                key={index}
                icon={chartIcons[chart.type]}
                label={chart.title}
                iconPosition="start"
                sx={{ minHeight: 48 }}
              />
            ))}
          </Tabs>
        )}
        
        {/* 图表内容 */}
        <Card sx={{ m: 1 }}>
          <CardContent sx={{ p: 1 }}>
            {charts[activeTab] && (
              <>
                <Box sx={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'space-between',
                  mb: 1
                }}>
                  <Typography variant="subtitle1" noWrap>
                    {charts[activeTab].title}
                  </Typography>
                  
                  {showControls && (
                    <Stack direction="row" spacing={0.5}>
                      <IconButton size="small" onClick={onRefresh}>
                        <RefreshIcon />
                      </IconButton>
                      
                      <IconButton 
                        size="small" 
                        onClick={() => setSettingsOpen(true)}
                      >
                        <SettingsIcon />
                      </IconButton>
                      
                      <IconButton 
                        size="small" 
                        onClick={() => setFullscreen(true)}
                      >
                        <FullscreenIcon />
                      </IconButton>
                    </Stack>
                  )}
                </Box>
                
                <Box 
                  sx={{ 
                    height: compact ? 200 : 300,
                    transform: `scale(${zoomLevel})`,
                    transformOrigin: 'top left'
                  }}
                >
                  <ResponsiveContainer width="100%" height="100%">
                    {renderChart(charts[activeTab], activeTab)}
                  </ResponsiveContainer>
                </Box>
                
                {/* 数据统计 */}
                <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  <Chip 
                    label={`数据点: ${processedData.length}`} 
                    size="small" 
                    variant="outlined"
                  />
                  
                  {realTime && (
                    <Chip 
                      label={`帧: ${currentFrame + 1}/${processedData.length}`} 
                      size="small" 
                      color="primary"
                      variant="outlined"
                    />
                  )}
                </Box>
              </>
            )}
          </CardContent>
        </Card>
      </Box>
      
      {/* 快速操作按钮 */}
      <SpeedDial
        ariaLabel="图表操作"
        sx={{ position: 'fixed', bottom: 80, right: 16 }}
        icon={<SpeedDialIcon />}
      >
        <SpeedDialAction
          icon={<DownloadIcon />}
          tooltipTitle="导出"
          onClick={() => onExport?.('png')}
        />
        
        <SpeedDialAction
          icon={<ShareIcon />}
          tooltipTitle="分享"
          onClick={onShare}
        />
        
        <SpeedDialAction
          icon={<RefreshIcon />}
          tooltipTitle="刷新"
          onClick={onRefresh}
        />
        
        <SpeedDialAction
          icon={<SettingsIcon />}
          tooltipTitle="设置"
          onClick={() => setSettingsOpen(true)}
        />
      </SpeedDial>
      
      {/* 全屏模式 */}
      <Dialog
        fullScreen
        open={fullscreen}
        onClose={() => setFullscreen(false)}
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Typography variant="h6" sx={{ flexGrow: 1 }}>
              {charts[activeTab]?.title}
            </Typography>
            <IconButton onClick={() => setFullscreen(false)}>
              <FullscreenExitIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        
        <DialogContent sx={{ p: 0 }}>
          <Box sx={{ height: '100%', p: 1 }}>
            <ResponsiveContainer width="100%" height="100%">
              {charts[activeTab] && renderChart(charts[activeTab], activeTab)}
            </ResponsiveContainer>
          </Box>
        </DialogContent>
      </Dialog>
      
      {/* 控制面板 */}
      {renderControls()}
    </>
  );
};

export default MobileDataVisualization;