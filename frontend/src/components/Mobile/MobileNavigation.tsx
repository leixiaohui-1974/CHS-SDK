import React, { useState, useEffect } from 'react';
import {
  BottomNavigation,
  BottomNavigationAction,
  AppBar,
  Toolbar,
  IconButton,
  Typography,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Divider,
  Box,
  Badge,
  Avatar,
  Collapse,
  useTheme,
  useMediaQuery,
  Fab,
  SpeedDial,
  SpeedDialAction,
  SpeedDialIcon,
  SwipeableDrawer,
  Paper,
  Chip
} from '@mui/material';
import {
  Menu as MenuIcon,
  Home as HomeIcon,
  Science as ScienceIcon,
  Analytics as AnalyticsIcon,
  Settings as SettingsIcon,
  Person as PersonIcon,
  Notifications as NotificationsIcon,
  Search as SearchIcon,
  Add as AddIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Pause as PauseIcon,
  ExpandLess,
  ExpandMore,
  Dashboard as DashboardIcon,
  History as HistoryIcon,
  CloudQueue as BatchIcon,
  Assessment as ReportIcon,
  Help as HelpIcon,
  Logout as LogoutIcon,
  Brightness4 as DarkModeIcon,
  Brightness7 as LightModeIcon,
  Language as LanguageIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Share as ShareIcon
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useNotifications } from '../../hooks/useNotifications';
import { useThemeMode } from '../../hooks/useThemeMode';

interface NavigationItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  path: string;
  badge?: number;
  children?: NavigationItem[];
}

interface MobileNavigationProps {
  title?: string;
  showBottomNav?: boolean;
  showTopBar?: boolean;
  showFab?: boolean;
  onMenuClick?: () => void;
}

const navigationItems: NavigationItem[] = [
  {
    id: 'home',
    label: '首页',
    icon: <HomeIcon />,
    path: '/'
  },
  {
    id: 'simulation',
    label: '仿真',
    icon: <ScienceIcon />,
    path: '/simulation',
    children: [
      {
        id: 'new-simulation',
        label: '新建仿真',
        icon: <AddIcon />,
        path: '/simulation/new'
      },
      {
        id: 'simulation-history',
        label: '仿真历史',
        icon: <HistoryIcon />,
        path: '/simulation/history'
      },
      {
        id: 'simulation-templates',
        label: '仿真模板',
        icon: <DashboardIcon />,
        path: '/simulation/templates'
      }
    ]
  },
  {
    id: 'batch',
    label: '批量仿真',
    icon: <BatchIcon />,
    path: '/batch'
  },
  {
    id: 'analysis',
    label: '分析',
    icon: <AnalyticsIcon />,
    path: '/analysis',
    children: [
      {
        id: 'data-analysis',
        label: '数据分析',
        icon: <AnalyticsIcon />,
        path: '/analysis/data'
      },
      {
        id: 'reports',
        label: '报告',
        icon: <ReportIcon />,
        path: '/analysis/reports'
      }
    ]
  },
  {
    id: 'settings',
    label: '设置',
    icon: <SettingsIcon />,
    path: '/settings'
  }
];

const quickActions = [
  {
    icon: <PlayIcon />,
    name: '开始仿真',
    action: 'start-simulation'
  },
  {
    icon: <UploadIcon />,
    name: '导入数据',
    action: 'import-data'
  },
  {
    icon: <DownloadIcon />,
    name: '导出结果',
    action: 'export-results'
  },
  {
    icon: <ShareIcon />,
    name: '分享',
    action: 'share'
  }
];

export const MobileNavigation: React.FC<MobileNavigationProps> = ({
  title = 'CHS仿真平台',
  showBottomNav = true,
  showTopBar = true,
  showFab = true,
  onMenuClick
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const { notifications, unreadCount } = useNotifications();
  const { mode, toggleMode } = useThemeMode();
  
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [expandedItems, setExpandedItems] = useState<string[]>([]);
  const [bottomNavValue, setBottomNavValue] = useState(0);
  const [fabOpen, setFabOpen] = useState(false);

  // 根据当前路径设置底部导航的值
  useEffect(() => {
    const currentPath = location.pathname;
    const index = navigationItems.findIndex(item => 
      currentPath.startsWith(item.path) && item.path !== '/'
    );
    if (index !== -1) {
      setBottomNavValue(index);
    } else if (currentPath === '/') {
      setBottomNavValue(0);
    }
  }, [location.pathname]);

  // 处理抽屉切换
  const handleDrawerToggle = () => {
    setDrawerOpen(!drawerOpen);
    onMenuClick?.();
  };

  // 处理导航项展开/收起
  const handleExpandClick = (itemId: string) => {
    setExpandedItems(prev => 
      prev.includes(itemId) 
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    );
  };

  // 处理导航
  const handleNavigation = (path: string) => {
    navigate(path);
    setDrawerOpen(false);
  };

  // 处理底部导航变化
  const handleBottomNavChange = (event: React.SyntheticEvent, newValue: number) => {
    setBottomNavValue(newValue);
    const item = navigationItems[newValue];
    if (item) {
      navigate(item.path);
    }
  };

  // 处理快速操作
  const handleQuickAction = (action: string) => {
    setFabOpen(false);
    
    switch (action) {
      case 'start-simulation':
        navigate('/simulation/new');
        break;
      case 'import-data':
        // 触发文件导入
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json,.csv,.xlsx';
        input.onchange = (e) => {
          const file = (e.target as HTMLInputElement).files?.[0];
          if (file) {
            // 处理文件导入
            console.log('导入文件:', file.name);
          }
        };
        input.click();
        break;
      case 'export-results':
        navigate('/analysis/export');
        break;
      case 'share':
        // 触发分享功能
        if (navigator.share) {
          navigator.share({
            title: 'CHS仿真平台',
            text: '专业的仿真建模与分析工具',
            url: window.location.href
          });
        }
        break;
    }
  };

  // 渲染导航项
  const renderNavigationItem = (item: NavigationItem, level = 0) => {
    const hasChildren = item.children && item.children.length > 0;
    const isExpanded = expandedItems.includes(item.id);
    const isActive = location.pathname === item.path || 
                    (item.children && item.children.some(child => location.pathname === child.path));

    return (
      <React.Fragment key={item.id}>
        <ListItem disablePadding>
          <ListItemButton
            onClick={() => {
              if (hasChildren) {
                handleExpandClick(item.id);
              } else {
                handleNavigation(item.path);
              }
            }}
            selected={isActive && !hasChildren}
            sx={{
              pl: 2 + level * 2,
              borderRadius: 1,
              mx: 1,
              mb: 0.5
            }}
          >
            <ListItemIcon sx={{ minWidth: 40 }}>
              {item.badge ? (
                <Badge badgeContent={item.badge} color="error">
                  {item.icon}
                </Badge>
              ) : (
                item.icon
              )}
            </ListItemIcon>
            <ListItemText 
              primary={item.label}
              primaryTypographyProps={{
                fontSize: '0.875rem',
                fontWeight: isActive ? 600 : 400
              }}
            />
            {hasChildren && (
              isExpanded ? <ExpandLess /> : <ExpandMore />
            )}
          </ListItemButton>
        </ListItem>
        
        {hasChildren && (
          <Collapse in={isExpanded} timeout="auto" unmountOnExit>
            <List component="div" disablePadding>
              {item.children!.map(child => renderNavigationItem(child, level + 1))}
            </List>
          </Collapse>
        )}
      </React.Fragment>
    );
  };

  // 抽屉内容
  const drawerContent = (
    <Box sx={{ width: 280, height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 用户信息 */}
      <Box sx={{ p: 2, bgcolor: 'primary.main', color: 'primary.contrastText' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Avatar sx={{ mr: 2, bgcolor: 'primary.dark' }}>
            {user?.name?.charAt(0) || 'U'}
          </Avatar>
          <Box>
            <Typography variant="subtitle1" noWrap>
              {user?.name || '未登录'}
            </Typography>
            <Typography variant="caption" sx={{ opacity: 0.8 }}>
              {user?.email || '请登录'}
            </Typography>
          </Box>
        </Box>
        
        {user?.role && (
          <Chip 
            label={user.role} 
            size="small" 
            sx={{ 
              bgcolor: 'primary.dark', 
              color: 'primary.contrastText',
              fontSize: '0.75rem'
            }} 
          />
        )}
      </Box>
      
      {/* 导航菜单 */}
      <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
        <List sx={{ pt: 1 }}>
          {navigationItems.map(item => renderNavigationItem(item))}
        </List>
      </Box>
      
      <Divider />
      
      {/* 底部操作 */}
      <List>
        <ListItem disablePadding>
          <ListItemButton onClick={toggleMode}>
            <ListItemIcon>
              {mode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
            </ListItemIcon>
            <ListItemText primary={mode === 'dark' ? '浅色模式' : '深色模式'} />
          </ListItemButton>
        </ListItem>
        
        <ListItem disablePadding>
          <ListItemButton>
            <ListItemIcon>
              <LanguageIcon />
            </ListItemIcon>
            <ListItemText primary="语言设置" />
          </ListItemButton>
        </ListItem>
        
        <ListItem disablePadding>
          <ListItemButton>
            <ListItemIcon>
              <HelpIcon />
            </ListItemIcon>
            <ListItemText primary="帮助" />
          </ListItemButton>
        </ListItem>
        
        {user && (
          <ListItem disablePadding>
            <ListItemButton onClick={logout}>
              <ListItemIcon>
                <LogoutIcon />
              </ListItemIcon>
              <ListItemText primary="退出登录" />
            </ListItemButton>
          </ListItem>
        )}
      </List>
    </Box>
  );

  if (!isMobile) {
    return null;
  }

  return (
    <>
      {/* 顶部应用栏 */}
      {showTopBar && (
        <AppBar 
          position="fixed" 
          sx={{ 
            zIndex: theme.zIndex.drawer + 1,
            bgcolor: 'background.paper',
            color: 'text.primary',
            boxShadow: 1
          }}
        >
          <Toolbar>
            <IconButton
              edge="start"
              color="inherit"
              aria-label="menu"
              onClick={handleDrawerToggle}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
            
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }} noWrap>
              {title}
            </Typography>
            
            <IconButton color="inherit">
              <SearchIcon />
            </IconButton>
            
            <IconButton color="inherit">
              <Badge badgeContent={unreadCount} color="error">
                <NotificationsIcon />
              </Badge>
            </IconButton>
          </Toolbar>
        </AppBar>
      )}
      
      {/* 侧边抽屉 */}
      <SwipeableDrawer
        anchor="left"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        onOpen={() => setDrawerOpen(true)}
        disableSwipeToOpen={false}
        ModalProps={{
          keepMounted: true, // 更好的移动端性能
        }}
      >
        {drawerContent}
      </SwipeableDrawer>
      
      {/* 底部导航 */}
      {showBottomNav && (
        <Paper 
          sx={{ 
            position: 'fixed', 
            bottom: 0, 
            left: 0, 
            right: 0, 
            zIndex: theme.zIndex.appBar,
            borderTop: 1,
            borderColor: 'divider'
          }} 
          elevation={3}
        >
          <BottomNavigation
            value={bottomNavValue}
            onChange={handleBottomNavChange}
            showLabels
          >
            {navigationItems.slice(0, 5).map((item, index) => (
              <BottomNavigationAction
                key={item.id}
                label={item.label}
                icon={
                  item.badge ? (
                    <Badge badgeContent={item.badge} color="error">
                      {item.icon}
                    </Badge>
                  ) : (
                    item.icon
                  )
                }
              />
            ))}
          </BottomNavigation>
        </Paper>
      )}
      
      {/* 浮动操作按钮 */}
      {showFab && (
        <SpeedDial
          ariaLabel="快速操作"
          sx={{ 
            position: 'fixed', 
            bottom: showBottomNav ? 80 : 16, 
            right: 16 
          }}
          icon={<SpeedDialIcon />}
          open={fabOpen}
          onClose={() => setFabOpen(false)}
          onOpen={() => setFabOpen(true)}
        >
          {quickActions.map((action) => (
            <SpeedDialAction
              key={action.action}
              icon={action.icon}
              tooltipTitle={action.name}
              onClick={() => handleQuickAction(action.action)}
            />
          ))}
        </SpeedDial>
      )}
      
      {/* 为顶部栏留出空间 */}
      {showTopBar && <Toolbar />}
      
      {/* 为底部导航留出空间 */}
      {showBottomNav && <Box sx={{ height: 56 }} />}
    </>
  );
};

export default MobileNavigation;