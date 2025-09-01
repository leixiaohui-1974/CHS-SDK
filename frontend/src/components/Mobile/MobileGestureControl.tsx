import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Typography,
  IconButton,
  Fab,
  Snackbar,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Switch,
  Slider,
  Divider,
  Chip,
  Paper,
  useTheme,
  useMediaQuery
} from '@mui/material';
import {
  TouchApp as TouchIcon,
  PanTool as PanIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  RotateRight as RotateIcon,
  Swipe as SwipeIcon,
  Vibration as VibrateIcon,
  Settings as SettingsIcon,
  Help as HelpIcon,
  Close as CloseIcon,
  Gesture as GestureIcon,
  TouchAppOutlined as TapIcon,
  OpenWith as DragIcon,
  PinchOutlined as PinchIcon
} from '@mui/icons-material';

interface GestureEvent {
  type: 'tap' | 'double-tap' | 'long-press' | 'swipe' | 'pinch' | 'rotate' | 'pan';
  data: {
    x?: number;
    y?: number;
    deltaX?: number;
    deltaY?: number;
    scale?: number;
    rotation?: number;
    direction?: 'up' | 'down' | 'left' | 'right';
    distance?: number;
    duration?: number;
    touches?: number;
  };
  target?: HTMLElement;
  timestamp: number;
}

interface GestureConfig {
  enabled: boolean;
  sensitivity: number;
  threshold: number;
  hapticFeedback: boolean;
  visualFeedback: boolean;
}

interface MobileGestureControlProps {
  onGesture?: (event: GestureEvent) => void;
  children?: React.ReactNode;
  disabled?: boolean;
  showIndicators?: boolean;
  enableHaptics?: boolean;
  className?: string;
}

const defaultGestureConfig: Record<string, GestureConfig> = {
  tap: {
    enabled: true,
    sensitivity: 1,
    threshold: 10,
    hapticFeedback: true,
    visualFeedback: true
  },
  doubleTap: {
    enabled: true,
    sensitivity: 1,
    threshold: 300,
    hapticFeedback: true,
    visualFeedback: true
  },
  longPress: {
    enabled: true,
    sensitivity: 1,
    threshold: 500,
    hapticFeedback: true,
    visualFeedback: true
  },
  swipe: {
    enabled: true,
    sensitivity: 1,
    threshold: 50,
    hapticFeedback: true,
    visualFeedback: true
  },
  pinch: {
    enabled: true,
    sensitivity: 1,
    threshold: 0.1,
    hapticFeedback: true,
    visualFeedback: true
  },
  rotate: {
    enabled: true,
    sensitivity: 1,
    threshold: 5,
    hapticFeedback: true,
    visualFeedback: true
  },
  pan: {
    enabled: true,
    sensitivity: 1,
    threshold: 10,
    hapticFeedback: false,
    visualFeedback: true
  }
};

export const MobileGestureControl: React.FC<MobileGestureControlProps> = ({
  onGesture,
  children,
  disabled = false,
  showIndicators = true,
  enableHaptics = true,
  className
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const containerRef = useRef<HTMLDivElement>(null);
  
  const [gestureConfig, setGestureConfig] = useState(defaultGestureConfig);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const [activeGesture, setActiveGesture] = useState<string | null>(null);
  const [touchPoints, setTouchPoints] = useState<Array<{ x: number; y: number; id: number }>>([]);
  const [gestureHistory, setGestureHistory] = useState<GestureEvent[]>([]);
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState('');
  
  // 手势状态
  const gestureState = useRef({
    isTracking: false,
    startTime: 0,
    startX: 0,
    startY: 0,
    lastX: 0,
    lastY: 0,
    lastTapTime: 0,
    initialDistance: 0,
    initialAngle: 0,
    longPressTimer: null as NodeJS.Timeout | null,
    touches: [] as Touch[]
  });

  // 触觉反馈
  const triggerHapticFeedback = useCallback((intensity: 'light' | 'medium' | 'heavy' = 'light') => {
    if (!enableHaptics || !navigator.vibrate) return;
    
    const patterns = {
      light: [10],
      medium: [20],
      heavy: [30]
    };
    
    navigator.vibrate(patterns[intensity]);
  }, [enableHaptics]);

  // 视觉反馈
  const triggerVisualFeedback = useCallback((message: string) => {
    if (!showIndicators) return;
    
    setFeedbackMessage(message);
    setShowFeedback(true);
    
    setTimeout(() => {
      setShowFeedback(false);
    }, 1000);
  }, [showIndicators]);

  // 发送手势事件
  const emitGestureEvent = useCallback((type: GestureEvent['type'], data: GestureEvent['data'], target?: HTMLElement) => {
    const event: GestureEvent = {
      type,
      data,
      target,
      timestamp: Date.now()
    };
    
    // 添加到历史记录
    setGestureHistory(prev => [...prev.slice(-9), event]);
    
    // 触发回调
    onGesture?.(event);
    
    // 反馈
    const config = gestureConfig[type] || gestureConfig[type.replace('-', '')];
    if (config?.hapticFeedback) {
      triggerHapticFeedback();
    }
    if (config?.visualFeedback) {
      triggerVisualFeedback(`${type} 手势`);
    }
  }, [onGesture, gestureConfig, triggerHapticFeedback, triggerVisualFeedback]);

  // 计算两点距离
  const getDistance = (touch1: Touch, touch2: Touch) => {
    const dx = touch1.clientX - touch2.clientX;
    const dy = touch1.clientY - touch2.clientY;
    return Math.sqrt(dx * dx + dy * dy);
  };

  // 计算两点角度
  const getAngle = (touch1: Touch, touch2: Touch) => {
    const dx = touch1.clientX - touch2.clientX;
    const dy = touch1.clientY - touch2.clientY;
    return Math.atan2(dy, dx) * 180 / Math.PI;
  };

  // 获取滑动方向
  const getSwipeDirection = (deltaX: number, deltaY: number): 'up' | 'down' | 'left' | 'right' => {
    if (Math.abs(deltaX) > Math.abs(deltaY)) {
      return deltaX > 0 ? 'right' : 'left';
    } else {
      return deltaY > 0 ? 'down' : 'up';
    }
  };

  // 触摸开始
  const handleTouchStart = useCallback((e: TouchEvent) => {
    if (disabled) return;
    
    const touches = Array.from(e.touches);
    const touch = touches[0];
    
    gestureState.current = {
      ...gestureState.current,
      isTracking: true,
      startTime: Date.now(),
      startX: touch.clientX,
      startY: touch.clientY,
      lastX: touch.clientX,
      lastY: touch.clientY,
      touches
    };
    
    // 更新触摸点显示
    setTouchPoints(touches.map((t, index) => ({
      x: t.clientX,
      y: t.clientY,
      id: index
    })));
    
    // 长按检测
    if (gestureConfig.longPress.enabled) {
      gestureState.current.longPressTimer = setTimeout(() => {
        if (gestureState.current.isTracking) {
          emitGestureEvent('long-press', {
            x: touch.clientX,
            y: touch.clientY,
            duration: Date.now() - gestureState.current.startTime
          }, e.target as HTMLElement);
          setActiveGesture('long-press');
        }
      }, gestureConfig.longPress.threshold);
    }
    
    // 多点触控初始化
    if (touches.length === 2) {
      gestureState.current.initialDistance = getDistance(touches[0], touches[1]);
      gestureState.current.initialAngle = getAngle(touches[0], touches[1]);
    }
  }, [disabled, gestureConfig, emitGestureEvent]);

  // 触摸移动
  const handleTouchMove = useCallback((e: TouchEvent) => {
    if (disabled || !gestureState.current.isTracking) return;
    
    const touches = Array.from(e.touches);
    const touch = touches[0];
    
    // 更新触摸点显示
    setTouchPoints(touches.map((t, index) => ({
      x: t.clientX,
      y: t.clientY,
      id: index
    })));
    
    const deltaX = touch.clientX - gestureState.current.lastX;
    const deltaY = touch.clientY - gestureState.current.lastY;
    
    // 清除长按定时器
    if (gestureState.current.longPressTimer) {
      clearTimeout(gestureState.current.longPressTimer);
      gestureState.current.longPressTimer = null;
    }
    
    // 单点拖拽
    if (touches.length === 1 && gestureConfig.pan.enabled) {
      emitGestureEvent('pan', {
        x: touch.clientX,
        y: touch.clientY,
        deltaX,
        deltaY
      }, e.target as HTMLElement);
      setActiveGesture('pan');
    }
    
    // 双点缩放和旋转
    if (touches.length === 2) {
      const currentDistance = getDistance(touches[0], touches[1]);
      const currentAngle = getAngle(touches[0], touches[1]);
      
      // 缩放检测
      if (gestureConfig.pinch.enabled) {
        const scale = currentDistance / gestureState.current.initialDistance;
        if (Math.abs(scale - 1) > gestureConfig.pinch.threshold) {
          emitGestureEvent('pinch', {
            scale,
            x: (touches[0].clientX + touches[1].clientX) / 2,
            y: (touches[0].clientY + touches[1].clientY) / 2
          }, e.target as HTMLElement);
          setActiveGesture('pinch');
        }
      }
      
      // 旋转检测
      if (gestureConfig.rotate.enabled) {
        const rotation = currentAngle - gestureState.current.initialAngle;
        if (Math.abs(rotation) > gestureConfig.rotate.threshold) {
          emitGestureEvent('rotate', {
            rotation,
            x: (touches[0].clientX + touches[1].clientX) / 2,
            y: (touches[0].clientY + touches[1].clientY) / 2
          }, e.target as HTMLElement);
          setActiveGesture('rotate');
        }
      }
    }
    
    gestureState.current.lastX = touch.clientX;
    gestureState.current.lastY = touch.clientY;
  }, [disabled, gestureConfig, emitGestureEvent]);

  // 触摸结束
  const handleTouchEnd = useCallback((e: TouchEvent) => {
    if (disabled || !gestureState.current.isTracking) return;
    
    const endTime = Date.now();
    const duration = endTime - gestureState.current.startTime;
    const deltaX = gestureState.current.lastX - gestureState.current.startX;
    const deltaY = gestureState.current.lastY - gestureState.current.startY;
    const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
    
    // 清除长按定时器
    if (gestureState.current.longPressTimer) {
      clearTimeout(gestureState.current.longPressTimer);
      gestureState.current.longPressTimer = null;
    }
    
    // 清除触摸点显示
    setTouchPoints([]);
    setActiveGesture(null);
    
    // 滑动检测
    if (distance > gestureConfig.swipe.threshold && gestureConfig.swipe.enabled) {
      const direction = getSwipeDirection(deltaX, deltaY);
      emitGestureEvent('swipe', {
        direction,
        distance,
        deltaX,
        deltaY,
        duration
      }, e.target as HTMLElement);
    }
    // 点击检测
    else if (distance < gestureConfig.tap.threshold && duration < 300) {
      const currentTime = Date.now();
      const timeSinceLastTap = currentTime - gestureState.current.lastTapTime;
      
      // 双击检测
      if (timeSinceLastTap < gestureConfig.doubleTap.threshold && gestureConfig.doubleTap.enabled) {
        emitGestureEvent('double-tap', {
          x: gestureState.current.startX,
          y: gestureState.current.startY
        }, e.target as HTMLElement);
        gestureState.current.lastTapTime = 0; // 重置以避免三击
      }
      // 单击
      else if (gestureConfig.tap.enabled) {
        emitGestureEvent('tap', {
          x: gestureState.current.startX,
          y: gestureState.current.startY
        }, e.target as HTMLElement);
        gestureState.current.lastTapTime = currentTime;
      }
    }
    
    gestureState.current.isTracking = false;
  }, [disabled, gestureConfig, emitGestureEvent]);

  // 绑定事件监听器
  useEffect(() => {
    const container = containerRef.current;
    if (!container || !isMobile) return;
    
    container.addEventListener('touchstart', handleTouchStart, { passive: false });
    container.addEventListener('touchmove', handleTouchMove, { passive: false });
    container.addEventListener('touchend', handleTouchEnd, { passive: false });
    
    return () => {
      container.removeEventListener('touchstart', handleTouchStart);
      container.removeEventListener('touchmove', handleTouchMove);
      container.removeEventListener('touchend', handleTouchEnd);
    };
  }, [handleTouchStart, handleTouchMove, handleTouchEnd, isMobile]);

  // 渲染触摸点指示器
  const renderTouchIndicators = () => {
    if (!showIndicators || touchPoints.length === 0) return null;
    
    return (
      <>
        {touchPoints.map((point) => (
          <Box
            key={point.id}
            sx={{
              position: 'fixed',
              left: point.x - 15,
              top: point.y - 15,
              width: 30,
              height: 30,
              borderRadius: '50%',
              backgroundColor: 'primary.main',
              opacity: 0.6,
              pointerEvents: 'none',
              zIndex: 9999,
              transform: 'scale(1)',
              animation: 'pulse 0.3s ease-in-out'
            }}
          />
        ))}
      </>
    );
  };

  // 渲染设置对话框
  const renderSettingsDialog = () => (
    <Dialog
      open={settingsOpen}
      onClose={() => setSettingsOpen(false)}
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle>
        手势设置
      </DialogTitle>
      
      <DialogContent>
        <List>
          {Object.entries(gestureConfig).map(([key, config]) => (
            <React.Fragment key={key}>
              <ListItem>
                <ListItemIcon>
                  {key === 'tap' && <TapIcon />}
                  {key === 'doubleTap' && <TapIcon />}
                  {key === 'longPress' && <TouchIcon />}
                  {key === 'swipe' && <SwipeIcon />}
                  {key === 'pinch' && <PinchIcon />}
                  {key === 'rotate' && <RotateIcon />}
                  {key === 'pan' && <DragIcon />}
                </ListItemIcon>
                <ListItemText 
                  primary={key}
                  secondary={`阈值: ${config.threshold}`}
                />
                <Switch
                  checked={config.enabled}
                  onChange={(e) => {
                    setGestureConfig(prev => ({
                      ...prev,
                      [key]: { ...prev[key], enabled: e.target.checked }
                    }));
                  }}
                />
              </ListItem>
              
              {config.enabled && (
                <ListItem sx={{ pl: 4 }}>
                  <Box sx={{ width: '100%' }}>
                    <Typography variant="caption" gutterBottom>
                      灵敏度
                    </Typography>
                    <Slider
                      value={config.sensitivity}
                      onChange={(_, value) => {
                        setGestureConfig(prev => ({
                          ...prev,
                          [key]: { ...prev[key], sensitivity: value as number }
                        }));
                      }}
                      min={0.1}
                      max={2}
                      step={0.1}
                      valueLabelDisplay="auto"
                    />
                  </Box>
                </ListItem>
              )}
              
              <Divider />
            </React.Fragment>
          ))}
        </List>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={() => setGestureConfig(defaultGestureConfig)}>
          重置
        </Button>
        <Button onClick={() => setSettingsOpen(false)}>
          关闭
        </Button>
      </DialogActions>
    </Dialog>
  );

  // 渲染帮助对话框
  const renderHelpDialog = () => (
    <Dialog
      open={helpOpen}
      onClose={() => setHelpOpen(false)}
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle>
        手势帮助
      </DialogTitle>
      
      <DialogContent>
        <List>
          <ListItem>
            <ListItemIcon><TapIcon /></ListItemIcon>
            <ListItemText 
              primary="单击" 
              secondary="快速点击屏幕"
            />
          </ListItem>
          
          <ListItem>
            <ListItemIcon><TapIcon /></ListItemIcon>
            <ListItemText 
              primary="双击" 
              secondary="快速连续点击两次"
            />
          </ListItem>
          
          <ListItem>
            <ListItemIcon><TouchIcon /></ListItemIcon>
            <ListItemText 
              primary="长按" 
              secondary="按住屏幕不放"
            />
          </ListItem>
          
          <ListItem>
            <ListItemIcon><SwipeIcon /></ListItemIcon>
            <ListItemText 
              primary="滑动" 
              secondary="在屏幕上快速滑动"
            />
          </ListItem>
          
          <ListItem>
            <ListItemIcon><PinchIcon /></ListItemIcon>
            <ListItemText 
              primary="缩放" 
              secondary="两指捏合或分开"
            />
          </ListItem>
          
          <ListItem>
            <ListItemIcon><RotateIcon /></ListItemIcon>
            <ListItemText 
              primary="旋转" 
              secondary="两指旋转"
            />
          </ListItem>
          
          <ListItem>
            <ListItemIcon><DragIcon /></ListItemIcon>
            <ListItemText 
              primary="拖拽" 
              secondary="按住并移动"
            />
          </ListItem>
        </List>
        
        {gestureHistory.length > 0 && (
          <>
            <Typography variant="h6" sx={{ mt: 2, mb: 1 }}>
              最近手势
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {gestureHistory.slice(-5).map((gesture, index) => (
                <Chip
                  key={index}
                  label={gesture.type}
                  size="small"
                  variant="outlined"
                />
              ))}
            </Box>
          </>
        )}
      </DialogContent>
      
      <DialogActions>
        <Button onClick={() => setHelpOpen(false)}>
          关闭
        </Button>
      </DialogActions>
    </Dialog>
  );

  if (!isMobile) {
    return <>{children}</>;
  }

  return (
    <>
      <Box
        ref={containerRef}
        className={className}
        sx={{
          position: 'relative',
          width: '100%',
          height: '100%',
          touchAction: disabled ? 'auto' : 'none',
          userSelect: 'none'
        }}
      >
        {children}
        
        {/* 活跃手势指示器 */}
        {activeGesture && showIndicators && (
          <Paper
            sx={{
              position: 'absolute',
              top: 16,
              left: 16,
              px: 2,
              py: 1,
              backgroundColor: 'primary.main',
              color: 'primary.contrastText',
              borderRadius: 2,
              zIndex: 1000
            }}
          >
            <Typography variant="caption">
              {activeGesture}
            </Typography>
          </Paper>
        )}
      </Box>
      
      {/* 触摸点指示器 */}
      {renderTouchIndicators()}
      
      {/* 控制按钮 */}
      <Fab
        size="small"
        sx={{ position: 'fixed', bottom: 140, right: 16 }}
        onClick={() => setSettingsOpen(true)}
      >
        <SettingsIcon />
      </Fab>
      
      <Fab
        size="small"
        sx={{ position: 'fixed', bottom: 190, right: 16 }}
        onClick={() => setHelpOpen(true)}
      >
        <HelpIcon />
      </Fab>
      
      {/* 反馈消息 */}
      <Snackbar
        open={showFeedback}
        message={feedbackMessage}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        autoHideDuration={1000}
      />
      
      {/* 设置对话框 */}
      {renderSettingsDialog()}
      
      {/* 帮助对话框 */}
      {renderHelpDialog()}
      
      {/* CSS 动画 */}
      <style>
        {`
          @keyframes pulse {
            0% { transform: scale(1); opacity: 0.6; }
            50% { transform: scale(1.2); opacity: 0.8; }
            100% { transform: scale(1); opacity: 0.6; }
          }
        `}
      </style>
    </>
  );
};

export default MobileGestureControl;