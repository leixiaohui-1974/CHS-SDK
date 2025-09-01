import { createTheme, Theme, ThemeOptions } from '@mui/material/styles';
import { Breakpoint } from '@mui/material/styles';

// 响应式断点配置
const breakpoints = {
  values: {
    xs: 0,      // 手机竖屏
    sm: 600,    // 手机横屏/小平板
    md: 900,    // 平板
    lg: 1200,   // 桌面
    xl: 1536,   // 大屏桌面
  },
};

// 移动端优化的间距系统
const spacing = (factor: number) => `${0.25 * factor}rem`;

// 响应式字体大小
const typography = {
  fontFamily: [
    '-apple-system',
    'BlinkMacSystemFont',
    '"Segoe UI"',
    'Roboto',
    '"Helvetica Neue"',
    'Arial',
    'sans-serif',
    '"Apple Color Emoji"',
    '"Segoe UI Emoji"',
    '"Segoe UI Symbol"',
  ].join(','),
  
  // 响应式字体大小
  h1: {
    fontSize: '2.125rem',
    fontWeight: 300,
    lineHeight: 1.167,
    '@media (max-width:600px)': {
      fontSize: '1.75rem',
    },
  },
  h2: {
    fontSize: '1.5rem',
    fontWeight: 400,
    lineHeight: 1.2,
    '@media (max-width:600px)': {
      fontSize: '1.25rem',
    },
  },
  h3: {
    fontSize: '1.25rem',
    fontWeight: 400,
    lineHeight: 1.167,
    '@media (max-width:600px)': {
      fontSize: '1.125rem',
    },
  },
  h4: {
    fontSize: '1.125rem',
    fontWeight: 400,
    lineHeight: 1.235,
    '@media (max-width:600px)': {
      fontSize: '1rem',
    },
  },
  h5: {
    fontSize: '1rem',
    fontWeight: 400,
    lineHeight: 1.334,
  },
  h6: {
    fontSize: '0.875rem',
    fontWeight: 500,
    lineHeight: 1.6,
  },
  body1: {
    fontSize: '1rem',
    lineHeight: 1.5,
    '@media (max-width:600px)': {
      fontSize: '0.875rem',
    },
  },
  body2: {
    fontSize: '0.875rem',
    lineHeight: 1.43,
    '@media (max-width:600px)': {
      fontSize: '0.8125rem',
    },
  },
  button: {
    fontSize: '0.875rem',
    fontWeight: 500,
    lineHeight: 1.75,
    textTransform: 'none' as const,
  },
  caption: {
    fontSize: '0.75rem',
    lineHeight: 1.66,
  },
  overline: {
    fontSize: '0.75rem',
    fontWeight: 400,
    lineHeight: 2.66,
    textTransform: 'uppercase' as const,
  },
};

// 移动端优化的组件样式
const components = {
  // 应用栏
  MuiAppBar: {
    styleOverrides: {
      root: {
        '@media (max-width:600px)': {
          paddingLeft: 8,
          paddingRight: 8,
        },
      },
    },
  },
  
  // 工具栏
  MuiToolbar: {
    styleOverrides: {
      root: {
        '@media (max-width:600px)': {
          minHeight: 56,
          paddingLeft: 8,
          paddingRight: 8,
        },
      },
    },
  },
  
  // 抽屉
  MuiDrawer: {
    styleOverrides: {
      paper: {
        '@media (max-width:600px)': {
          width: '100%',
          maxWidth: 320,
        },
      },
    },
  },
  
  // 对话框
  MuiDialog: {
    styleOverrides: {
      paper: {
        '@media (max-width:600px)': {
          margin: 8,
          width: 'calc(100% - 16px)',
          maxHeight: 'calc(100% - 16px)',
        },
      },
    },
  },
  
  // 卡片
  MuiCard: {
    styleOverrides: {
      root: {
        '@media (max-width:600px)': {
          borderRadius: 8,
        },
      },
    },
  },
  
  // 按钮
  MuiButton: {
    styleOverrides: {
      root: {
        '@media (max-width:600px)': {
          minHeight: 44, // 移动端触摸友好的最小高度
          fontSize: '0.875rem',
        },
      },
      sizeSmall: {
        '@media (max-width:600px)': {
          minHeight: 36,
          fontSize: '0.8125rem',
        },
      },
      sizeLarge: {
        '@media (max-width:600px)': {
          minHeight: 52,
          fontSize: '1rem',
        },
      },
    },
  },
  
  // 图标按钮
  MuiIconButton: {
    styleOverrides: {
      root: {
        '@media (max-width:600px)': {
          padding: 12, // 增加触摸区域
        },
      },
      sizeSmall: {
        '@media (max-width:600px)': {
          padding: 8,
        },
      },
    },
  },
  
  // 输入框
  MuiTextField: {
    styleOverrides: {
      root: {
        '@media (max-width:600px)': {
          '& .MuiInputBase-root': {
            fontSize: '16px', // 防止iOS缩放
          },
        },
      },
    },
  },
  
  // 表格
  MuiTable: {
    styleOverrides: {
      root: {
        '@media (max-width:600px)': {
          '& .MuiTableCell-root': {
            padding: '8px 4px',
            fontSize: '0.8125rem',
          },
        },
      },
    },
  },
  
  // 标签页
  MuiTabs: {
    styleOverrides: {
      root: {
        '@media (max-width:600px)': {
          '& .MuiTab-root': {
            minWidth: 'auto',
            padding: '6px 8px',
            fontSize: '0.8125rem',
          },
        },
      },
      scrollButtons: {
        '@media (max-width:600px)': {
          '&.Mui-disabled': {
            opacity: 0.3,
          },
        },
      },
    },
  },
  
  // 芯片
  MuiChip: {
    styleOverrides: {
      root: {
        '@media (max-width:600px)': {
          height: 28,
          fontSize: '0.75rem',
        },
      },
      sizeSmall: {
        '@media (max-width:600px)': {
          height: 24,
          fontSize: '0.6875rem',
        },
      },
    },
  },
  
  // 列表项
  MuiListItem: {
    styleOverrides: {
      root: {
        '@media (max-width:600px)': {
          paddingTop: 12,
          paddingBottom: 12,
        },
      },
    },
  },
  
  // 菜单项
  MuiMenuItem: {
    styleOverrides: {
      root: {
        '@media (max-width:600px)': {
          minHeight: 44,
          fontSize: '0.875rem',
        },
      },
    },
  },
  
  // 底部导航
  MuiBottomNavigation: {
    styleOverrides: {
      root: {
        height: 64,
        '@media (max-width:600px)': {
          height: 56,
        },
      },
    },
  },
  
  // 底部导航动作
  MuiBottomNavigationAction: {
    styleOverrides: {
      root: {
        '@media (max-width:600px)': {
          minWidth: 'auto',
          paddingTop: 6,
          '& .MuiBottomNavigationAction-label': {
            fontSize: '0.75rem',
          },
        },
      },
    },
  },
  
  // 速度拨号
  MuiSpeedDial: {
    styleOverrides: {
      fab: {
        '@media (max-width:600px)': {
          width: 48,
          height: 48,
        },
      },
    },
  },
  
  // 网格容器
  MuiGrid: {
    styleOverrides: {
      container: {
        '@media (max-width:600px)': {
          '&.MuiGrid-spacing-xs-3 > .MuiGrid-item': {
            paddingTop: 12,
            paddingLeft: 12,
          },
        },
      },
    },
  },
};

// 浅色主题配置
const lightThemeOptions: ThemeOptions = {
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
      light: '#42a5f5',
      dark: '#1565c0',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#dc004e',
      light: '#ff5983',
      dark: '#9a0036',
      contrastText: '#ffffff',
    },
    error: {
      main: '#f44336',
      light: '#e57373',
      dark: '#d32f2f',
      contrastText: '#ffffff',
    },
    warning: {
      main: '#ff9800',
      light: '#ffb74d',
      dark: '#f57c00',
      contrastText: 'rgba(0, 0, 0, 0.87)',
    },
    info: {
      main: '#2196f3',
      light: '#64b5f6',
      dark: '#1976d2',
      contrastText: '#ffffff',
    },
    success: {
      main: '#4caf50',
      light: '#81c784',
      dark: '#388e3c',
      contrastText: 'rgba(0, 0, 0, 0.87)',
    },
    background: {
      default: '#fafafa',
      paper: '#ffffff',
    },
    text: {
      primary: 'rgba(0, 0, 0, 0.87)',
      secondary: 'rgba(0, 0, 0, 0.6)',
      disabled: 'rgba(0, 0, 0, 0.38)',
    },
  },
  breakpoints,
  spacing,
  typography,
  components,
  shape: {
    borderRadius: 8,
  },
  shadows: [
    'none',
    '0px 2px 1px -1px rgba(0,0,0,0.2),0px 1px 1px 0px rgba(0,0,0,0.14),0px 1px 3px 0px rgba(0,0,0,0.12)',
    '0px 3px 1px -2px rgba(0,0,0,0.2),0px 2px 2px 0px rgba(0,0,0,0.14),0px 1px 5px 0px rgba(0,0,0,0.12)',
    '0px 3px 3px -2px rgba(0,0,0,0.2),0px 3px 4px 0px rgba(0,0,0,0.14),0px 1px 8px 0px rgba(0,0,0,0.12)',
    '0px 2px 4px -1px rgba(0,0,0,0.2),0px 4px 5px 0px rgba(0,0,0,0.14),0px 1px 10px 0px rgba(0,0,0,0.12)',
    '0px 3px 5px -1px rgba(0,0,0,0.2),0px 5px 8px 0px rgba(0,0,0,0.14),0px 1px 14px 0px rgba(0,0,0,0.12)',
    '0px 3px 5px -1px rgba(0,0,0,0.2),0px 6px 10px 0px rgba(0,0,0,0.14),0px 1px 18px 0px rgba(0,0,0,0.12)',
    '0px 4px 5px -2px rgba(0,0,0,0.2),0px 7px 10px 1px rgba(0,0,0,0.14),0px 2px 16px 1px rgba(0,0,0,0.12)',
    '0px 5px 5px -3px rgba(0,0,0,0.2),0px 8px 10px 1px rgba(0,0,0,0.14),0px 3px 14px 2px rgba(0,0,0,0.12)',
    '0px 5px 6px -3px rgba(0,0,0,0.2),0px 9px 12px 1px rgba(0,0,0,0.14),0px 3px 16px 2px rgba(0,0,0,0.12)',
    '0px 6px 6px -3px rgba(0,0,0,0.2),0px 10px 14px 1px rgba(0,0,0,0.14),0px 4px 18px 3px rgba(0,0,0,0.12)',
    '0px 6px 7px -4px rgba(0,0,0,0.2),0px 11px 15px 1px rgba(0,0,0,0.14),0px 4px 20px 3px rgba(0,0,0,0.12)',
    '0px 7px 8px -4px rgba(0,0,0,0.2),0px 12px 17px 2px rgba(0,0,0,0.14),0px 5px 22px 4px rgba(0,0,0,0.12)',
    '0px 7px 8px -4px rgba(0,0,0,0.2),0px 13px 19px 2px rgba(0,0,0,0.14),0px 5px 24px 4px rgba(0,0,0,0.12)',
    '0px 7px 9px -4px rgba(0,0,0,0.2),0px 14px 21px 2px rgba(0,0,0,0.14),0px 5px 26px 4px rgba(0,0,0,0.12)',
    '0px 8px 9px -5px rgba(0,0,0,0.2),0px 15px 22px 2px rgba(0,0,0,0.14),0px 6px 28px 5px rgba(0,0,0,0.12)',
    '0px 8px 10px -5px rgba(0,0,0,0.2),0px 16px 24px 2px rgba(0,0,0,0.14),0px 6px 30px 5px rgba(0,0,0,0.12)',
    '0px 8px 11px -5px rgba(0,0,0,0.2),0px 17px 26px 2px rgba(0,0,0,0.14),0px 6px 32px 5px rgba(0,0,0,0.12)',
    '0px 9px 11px -5px rgba(0,0,0,0.2),0px 18px 28px 2px rgba(0,0,0,0.14),0px 7px 34px 6px rgba(0,0,0,0.12)',
    '0px 9px 12px -6px rgba(0,0,0,0.2),0px 19px 29px 2px rgba(0,0,0,0.14),0px 7px 36px 6px rgba(0,0,0,0.12)',
    '0px 10px 13px -6px rgba(0,0,0,0.2),0px 20px 31px 3px rgba(0,0,0,0.14),0px 8px 38px 7px rgba(0,0,0,0.12)',
    '0px 10px 13px -6px rgba(0,0,0,0.2),0px 21px 33px 3px rgba(0,0,0,0.14),0px 8px 40px 7px rgba(0,0,0,0.12)',
    '0px 10px 14px -6px rgba(0,0,0,0.2),0px 22px 35px 3px rgba(0,0,0,0.14),0px 8px 42px 7px rgba(0,0,0,0.12)',
    '0px 11px 14px -7px rgba(0,0,0,0.2),0px 23px 36px 3px rgba(0,0,0,0.14),0px 9px 44px 8px rgba(0,0,0,0.12)',
    '0px 11px 15px -7px rgba(0,0,0,0.2),0px 24px 38px 3px rgba(0,0,0,0.14),0px 9px 46px 8px rgba(0,0,0,0.12)',
  ],
};

// 深色主题配置
const darkThemeOptions: ThemeOptions = {
  ...lightThemeOptions,
  palette: {
    mode: 'dark',
    primary: {
      main: '#90caf9',
      light: '#e3f2fd',
      dark: '#42a5f5',
      contrastText: 'rgba(0, 0, 0, 0.87)',
    },
    secondary: {
      main: '#f48fb1',
      light: '#fce4ec',
      dark: '#ad2d5f',
      contrastText: 'rgba(0, 0, 0, 0.87)',
    },
    error: {
      main: '#f44336',
      light: '#e57373',
      dark: '#d32f2f',
      contrastText: '#ffffff',
    },
    warning: {
      main: '#ffa726',
      light: '#ffb74d',
      dark: '#f57c00',
      contrastText: 'rgba(0, 0, 0, 0.87)',
    },
    info: {
      main: '#29b6f6',
      light: '#4fc3f7',
      dark: '#0288d1',
      contrastText: 'rgba(0, 0, 0, 0.87)',
    },
    success: {
      main: '#66bb6a',
      light: '#81c784',
      dark: '#388e3c',
      contrastText: 'rgba(0, 0, 0, 0.87)',
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
    text: {
      primary: '#ffffff',
      secondary: 'rgba(255, 255, 255, 0.7)',
      disabled: 'rgba(255, 255, 255, 0.5)',
    },
  },
};

// 创建主题
export const lightTheme = createTheme(lightThemeOptions);
export const darkTheme = createTheme(darkThemeOptions);

// 响应式工具函数
export const useResponsive = () => {
  const theme = lightTheme; // 可以根据需要切换主题
  
  return {
    // 断点检查
    isXs: (width: number) => width < theme.breakpoints.values.sm,
    isSm: (width: number) => width >= theme.breakpoints.values.sm && width < theme.breakpoints.values.md,
    isMd: (width: number) => width >= theme.breakpoints.values.md && width < theme.breakpoints.values.lg,
    isLg: (width: number) => width >= theme.breakpoints.values.lg && width < theme.breakpoints.values.xl,
    isXl: (width: number) => width >= theme.breakpoints.values.xl,
    
    // 移动端检查
    isMobile: (width: number) => width < theme.breakpoints.values.md,
    isTablet: (width: number) => width >= theme.breakpoints.values.sm && width < theme.breakpoints.values.lg,
    isDesktop: (width: number) => width >= theme.breakpoints.values.lg,
    
    // 获取响应式值
    getResponsiveValue: <T>(values: {
      xs?: T;
      sm?: T;
      md?: T;
      lg?: T;
      xl?: T;
    }, width: number): T | undefined => {
      if (width >= theme.breakpoints.values.xl && values.xl !== undefined) return values.xl;
      if (width >= theme.breakpoints.values.lg && values.lg !== undefined) return values.lg;
      if (width >= theme.breakpoints.values.md && values.md !== undefined) return values.md;
      if (width >= theme.breakpoints.values.sm && values.sm !== undefined) return values.sm;
      return values.xs;
    },
    
    // 获取网格列数
    getGridColumns: (width: number) => {
      if (width >= theme.breakpoints.values.xl) return 12;
      if (width >= theme.breakpoints.values.lg) return 12;
      if (width >= theme.breakpoints.values.md) return 8;
      if (width >= theme.breakpoints.values.sm) return 4;
      return 2;
    },
    
    // 获取容器最大宽度
    getContainerMaxWidth: (width: number) => {
      if (width >= theme.breakpoints.values.xl) return 1200;
      if (width >= theme.breakpoints.values.lg) return 960;
      if (width >= theme.breakpoints.values.md) return 720;
      return '100%';
    },
  };
};

// 移动端优化的CSS-in-JS样式
export const mobileOptimizedStyles = {
  // 触摸友好的按钮
  touchButton: {
    minHeight: 44,
    minWidth: 44,
    '@media (max-width:600px)': {
      minHeight: 48,
      minWidth: 48,
    },
  },
  
  // 移动端安全区域
  safeArea: {
    paddingTop: 'env(safe-area-inset-top)',
    paddingBottom: 'env(safe-area-inset-bottom)',
    paddingLeft: 'env(safe-area-inset-left)',
    paddingRight: 'env(safe-area-inset-right)',
  },
  
  // 移动端滚动容器
  mobileScrollContainer: {
    overflowX: 'auto',
    overflowY: 'auto',
    WebkitOverflowScrolling: 'touch',
    scrollbarWidth: 'thin',
    '&::-webkit-scrollbar': {
      width: 4,
      height: 4,
    },
    '&::-webkit-scrollbar-track': {
      background: 'transparent',
    },
    '&::-webkit-scrollbar-thumb': {
      background: 'rgba(0, 0, 0, 0.2)',
      borderRadius: 2,
    },
  },
  
  // 移动端表格
  mobileTable: {
    '@media (max-width:600px)': {
      '& .MuiTableCell-root': {
        padding: '8px 4px',
        fontSize: '0.75rem',
        '&:first-of-type': {
          paddingLeft: 8,
        },
        '&:last-of-type': {
          paddingRight: 8,
        },
      },
    },
  },
  
  // 移动端对话框
  mobileDialog: {
    '@media (max-width:600px)': {
      '& .MuiDialog-paper': {
        margin: 8,
        width: 'calc(100% - 16px)',
        maxHeight: 'calc(100% - 16px)',
        borderRadius: 8,
      },
    },
  },
  
  // 移动端输入框
  mobileInput: {
    '@media (max-width:600px)': {
      '& .MuiInputBase-input': {
        fontSize: '16px', // 防止iOS缩放
      },
    },
  },
};

export default {
  lightTheme,
  darkTheme,
  useResponsive,
  mobileOptimizedStyles,
};