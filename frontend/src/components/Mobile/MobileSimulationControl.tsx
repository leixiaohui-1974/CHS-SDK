import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  IconButton,
  LinearProgress,
  Chip,
  Stack,
  Divider,
  Collapse,
  Alert,
  Snackbar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  SwipeableDrawer,
  useTheme,
  useMediaQuery,
  Fab,
  Slide,
  Paper,
  Grid,
  Avatar,
  CircularProgress,
  Tooltip
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Settings as SettingsIcon,
  Timeline as TimelineIcon,
  Speed as SpeedIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as SuccessIcon,
  Info as InfoIcon,
  Download as DownloadIcon,
  Share as ShareIcon,
  Fullscreen as FullscreenIcon,
  FullscreenExit as FullscreenExitIcon,
  Visibility as ViewIcon,
  VisibilityOff as HideIcon
} from '@mui/icons-material';
import { TransitionProps } from '@mui/material/transitions';

interface SimulationStatus {
  id: string;
  name: string;
  status: 'idle' | 'running' | 'paused' | 'completed' | 'error' | 'cancelled';
  progress: number;
  startTime?: Date;
  endTime?: Date;
  duration?: number;
  currentStep?: number;
  totalSteps?: number;
  parameters?: Record<string, any>;
  results?: any;
  error?: string;
}

interface SystemMetrics {
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
  networkSpeed: number;
  temperature?: number;
}

interface MobileSimulationControlProps {
  simulation?: SimulationStatus;
  metrics?: SystemMetrics;
  onStart?: () => void;
  onPause?: () => void;
  onStop?: () => void;
  onRestart?: () => void;
  onDownload?: () => void;
  onShare?: () => void;
  onSettings?: () => void;
  compact?: boolean;
}

const Transition = React.forwardRef(function Transition(
  props: TransitionProps & {
    children: React.ReactElement;
  },
  ref: React.Ref<unknown>,
) {
  return <Slide direction="up" ref={ref} {...props} />;
});

export const MobileSimulationControl: React.FC<MobileSimulationControlProps> = ({
  simulation,
  metrics,
  onStart,
  onPause,
  onStop,
  onRestart,
  onDownload,
  onShare,
  onSettings,
  compact = false
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  const [expanded, setExpanded] = useState(false);
  const [metricsExpanded, setMetricsExpanded] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const [showAlert, setShowAlert] = useState(false);
  const [alertMessage, setAlertMessage] = useState('');
  const [alertSeverity, setAlertSeverity] = useState<'success' | 'error' | 'warning' | 'info'>('info');
  const [detailsOpen, setDetailsOpen] = useState(false);

  // 格式化时间
  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  // 获取状态颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'primary';
      case 'completed': return 'success';
      case 'error': return 'error';
      case 'paused': return 'warning';
      case 'cancelled': return 'default';
      default: return 'default';
    }
  };

  // 获取状态图标
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return <CircularProgress size={16} />;
      case 'completed': return <SuccessIcon />;
      case 'error': return <ErrorIcon />;
      case 'paused': return <PauseIcon />;
      case 'cancelled': return <StopIcon />;
      default: return <InfoIcon />;
    }
  };

  // 处理操作
  const handleAction = (action: string) => {
    switch (action) {
      case 'start':
        onStart?.();
        setAlertMessage('仿真已开始');
        setAlertSeverity('success');
        setShowAlert(true);
        break;
      case 'pause':
        onPause?.();
        setAlertMessage('仿真已暂停');
        setAlertSeverity('warning');
        setShowAlert(true);
        break;
      case 'stop':
        onStop?.();
        setAlertMessage('仿真已停止');
        setAlertSeverity('info');
        setShowAlert(true);
        break;
      case 'restart':
        onRestart?.();
        setAlertMessage('仿真已重启');
        setAlertSeverity('success');
        setShowAlert(true);
        break;
      case 'download':
        onDownload?.();
        setAlertMessage('开始下载结果');
        setAlertSeverity('info');
        setShowAlert(true);
        break;
      case 'share':
        onShare?.();
        break;
    }
  };

  // 渲染控制按钮
  const renderControlButtons = () => {
    if (!simulation) return null;

    const { status } = simulation;
    const isRunning = status === 'running';
    const isPaused = status === 'paused';
    const isCompleted = status === 'completed';
    const hasError = status === 'error';

    return (
      <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
        {!isRunning && !isCompleted && (
          <Button
            variant="contained"
            startIcon={<PlayIcon />}
            onClick={() => handleAction('start')}
            size="small"
            fullWidth={compact}
          >
            {isPaused ? '继续' : '开始'}
          </Button>
        )}
        
        {isRunning && (
          <Button
            variant="outlined"
            startIcon={<PauseIcon />}
            onClick={() => handleAction('pause')}
            size="small"
            fullWidth={compact}
          >
            暂停
          </Button>
        )}
        
        {(isRunning || isPaused) && (
          <Button
            variant="outlined"
            color="error"
            startIcon={<StopIcon />}
            onClick={() => handleAction('stop')}
            size="small"
          >
            停止
          </Button>
        )}
        
        {(hasError || isCompleted) && (
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => handleAction('restart')}
            size="small"
          >
            重启
          </Button>
        )}
        
        {isCompleted && (
          <>
            <IconButton
              size="small"
              onClick={() => handleAction('download')}
              color="primary"
            >
              <DownloadIcon />
            </IconButton>
            <IconButton
              size="small"
              onClick={() => handleAction('share')}
              color="primary"
            >
              <ShareIcon />
            </IconButton>
          </>
        )}
      </Stack>
    );
  };

  // 渲染系统指标
  const renderMetrics = () => {
    if (!metrics) return null;

    return (
      <Box sx={{ mt: 2 }}>
        <Box 
          sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            cursor: 'pointer',
            mb: 1
          }}
          onClick={() => setMetricsExpanded(!metricsExpanded)}
        >
          <Typography variant="subtitle2" sx={{ flexGrow: 1 }}>
            系统指标
          </Typography>
          {metricsExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </Box>
        
        <Collapse in={metricsExpanded}>
          <Grid container spacing={1}>
            <Grid item xs={6}>
              <Box sx={{ textAlign: 'center' }}>
                <MemoryIcon color="primary" />
                <Typography variant="caption" display="block">
                  CPU: {metrics.cpuUsage}%
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={metrics.cpuUsage} 
                  sx={{ mt: 0.5 }}
                />
              </Box>
            </Grid>
            
            <Grid item xs={6}>
              <Box sx={{ textAlign: 'center' }}>
                <StorageIcon color="secondary" />
                <Typography variant="caption" display="block">
                  内存: {metrics.memoryUsage}%
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={metrics.memoryUsage} 
                  color="secondary"
                  sx={{ mt: 0.5 }}
                />
              </Box>
            </Grid>
            
            <Grid item xs={6}>
              <Box sx={{ textAlign: 'center' }}>
                <StorageIcon color="warning" />
                <Typography variant="caption" display="block">
                  磁盘: {metrics.diskUsage}%
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={metrics.diskUsage} 
                  color="warning"
                  sx={{ mt: 0.5 }}
                />
              </Box>
            </Grid>
            
            <Grid item xs={6}>
              <Box sx={{ textAlign: 'center' }}>
                <SpeedIcon color="info" />
                <Typography variant="caption" display="block">
                  网络: {metrics.networkSpeed} MB/s
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </Collapse>
      </Box>
    );
  };

  // 渲染详细信息
  const renderDetails = () => {
    if (!simulation) return null;

    return (
      <SwipeableDrawer
        anchor="bottom"
        open={detailsOpen}
        onClose={() => setDetailsOpen(false)}
        onOpen={() => setDetailsOpen(true)}
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
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'space-between',
            mb: 2
          }}>
            <Typography variant="h6">
              仿真详情
            </Typography>
            <IconButton onClick={() => setDetailsOpen(false)}>
              <HideIcon />
            </IconButton>
          </Box>
          
          <List>
            <ListItem>
              <ListItemIcon>
                <InfoIcon />
              </ListItemIcon>
              <ListItemText 
                primary="仿真名称" 
                secondary={simulation.name}
              />
            </ListItem>
            
            <ListItem>
              <ListItemIcon>
                {getStatusIcon(simulation.status)}
              </ListItemIcon>
              <ListItemText 
                primary="状态" 
                secondary={
                  <Chip 
                    label={simulation.status} 
                    color={getStatusColor(simulation.status) as any}
                    size="small"
                  />
                }
              />
            </ListItem>
            
            {simulation.startTime && (
              <ListItem>
                <ListItemIcon>
                  <TimelineIcon />
                </ListItemIcon>
                <ListItemText 
                  primary="开始时间" 
                  secondary={simulation.startTime.toLocaleString()}
                />
              </ListItem>
            )}
            
            {simulation.duration && (
              <ListItem>
                <ListItemIcon>
                  <SpeedIcon />
                </ListItemIcon>
                <ListItemText 
                  primary="运行时长" 
                  secondary={formatDuration(simulation.duration)}
                />
              </ListItem>
            )}
            
            {simulation.currentStep && simulation.totalSteps && (
              <ListItem>
                <ListItemIcon>
                  <TimelineIcon />
                </ListItemIcon>
                <ListItemText 
                  primary="进度" 
                  secondary={`${simulation.currentStep} / ${simulation.totalSteps} 步`}
                />
              </ListItem>
            )}
            
            {simulation.error && (
              <ListItem>
                <ListItemIcon>
                  <ErrorIcon color="error" />
                </ListItemIcon>
                <ListItemText 
                  primary="错误信息" 
                  secondary={simulation.error}
                />
              </ListItem>
            )}
          </List>
          
          {simulation.parameters && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                参数配置
              </Typography>
              <Paper sx={{ p: 1, bgcolor: 'grey.50' }}>
                <Typography variant="caption" component="pre">
                  {JSON.stringify(simulation.parameters, null, 2)}
                </Typography>
              </Paper>
            </Box>
          )}
        </Box>
      </SwipeableDrawer>
    );
  };

  if (!isMobile) {
    return null;
  }

  return (
    <>
      <Card sx={{ m: 1, position: 'relative' }}>
        <CardContent sx={{ pb: 1 }}>
          {/* 标题和状态 */}
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <Avatar sx={{ mr: 1, width: 32, height: 32 }}>
              {getStatusIcon(simulation?.status || 'idle')}
            </Avatar>
            
            <Box sx={{ flexGrow: 1 }}>
              <Typography variant="subtitle1" noWrap>
                {simulation?.name || '未选择仿真'}
              </Typography>
              
              {simulation && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Chip 
                    label={simulation.status} 
                    color={getStatusColor(simulation.status) as any}
                    size="small"
                  />
                  
                  {simulation.currentStep && simulation.totalSteps && (
                    <Typography variant="caption" color="text.secondary">
                      {simulation.currentStep}/{simulation.totalSteps}
                    </Typography>
                  )}
                </Box>
              )}
            </Box>
            
            <IconButton 
              size="small" 
              onClick={() => setDetailsOpen(true)}
              disabled={!simulation}
            >
              <ViewIcon />
            </IconButton>
            
            <IconButton size="small" onClick={onSettings}>
              <SettingsIcon />
            </IconButton>
          </Box>
          
          {/* 进度条 */}
          {simulation && simulation.progress > 0 && (
            <Box sx={{ mb: 1 }}>
              <LinearProgress 
                variant="determinate" 
                value={simulation.progress} 
                sx={{ height: 6, borderRadius: 3 }}
              />
              <Typography variant="caption" color="text.secondary">
                {simulation.progress.toFixed(1)}%
              </Typography>
            </Box>
          )}
          
          {/* 控制按钮 */}
          {renderControlButtons()}
          
          {/* 系统指标 */}
          {!compact && renderMetrics()}
        </CardContent>
      </Card>
      
      {/* 详细信息抽屉 */}
      {renderDetails()}
      
      {/* 全屏浮动按钮 */}
      {simulation?.status === 'running' && (
        <Fab
          color="primary"
          size="small"
          sx={{ 
            position: 'fixed', 
            bottom: 80, 
            left: 16,
            zIndex: 1000
          }}
          onClick={() => setFullscreen(!fullscreen)}
        >
          {fullscreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
        </Fab>
      )}
      
      {/* 全屏模式对话框 */}
      <Dialog
        fullScreen
        open={fullscreen}
        onClose={() => setFullscreen(false)}
        TransitionComponent={Transition}
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Typography variant="h6" sx={{ flexGrow: 1 }}>
              {simulation?.name}
            </Typography>
            <IconButton onClick={() => setFullscreen(false)}>
              <FullscreenExitIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        
        <DialogContent>
          {/* 全屏模式下的详细监控界面 */}
          <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            {/* 这里可以添加更详细的监控图表和数据 */}
            <Typography variant="body1">
              全屏监控模式 - 可以在这里显示详细的仿真进度、图表和实时数据
            </Typography>
          </Box>
        </DialogContent>
      </Dialog>
      
      {/* 提示消息 */}
      <Snackbar
        open={showAlert}
        autoHideDuration={3000}
        onClose={() => setShowAlert(false)}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert 
          onClose={() => setShowAlert(false)} 
          severity={alertSeverity}
          variant="filled"
        >
          {alertMessage}
        </Alert>
      </Snackbar>
    </>
  );
};

export default MobileSimulationControl;