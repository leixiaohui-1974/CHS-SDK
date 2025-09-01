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
  CardActions,
  TextField,
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
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  IconButton,
  Tooltip,
  Alert,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Avatar,
  Rating,
  Divider,
  Fab,
  Menu,
  MenuList,
  MenuItem as MenuItemComponent,
  ListItemAvatar,
  Badge
} from '@mui/material';
import {
  Template as TemplateIcon,
  ExpandMore as ExpandMoreIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Share as ShareIcon,
  Visibility as VisibilityIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon,
  Public as PublicIcon,
  Lock as LockIcon,
  Person as PersonIcon,
  Group as GroupIcon,
  Search as SearchIcon,
  FilterList as FilterListIcon,
  Sort as SortIcon,
  MoreVert as MoreVertIcon,
  ContentCopy as CopyIcon,
  History as HistoryIcon
} from '@mui/icons-material';
import { useApi } from '../../hooks/useApi';
import { formatDateTime } from '../../utils/dateUtils';
import { JsonViewer } from '../Common/JsonViewer';

interface TemplateMetadata {
  name: string;
  description: string;
  version: string;
  author: string;
  created_at: string;
  updated_at: string;
  tags: string[];
  category: string;
  type: 'simulation' | 'batch' | 'analysis';
  status: 'draft' | 'published' | 'archived';
  visibility: 'private' | 'team' | 'public';
  rating?: number;
  usage_count?: number;
}

interface TemplateParameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  description: string;
  default_value?: any;
  required: boolean;
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    options?: string[];
  };
}

interface SimulationTemplate {
  id: string;
  metadata: TemplateMetadata;
  parameters: TemplateParameter[];
  configuration: Record<string, any>;
  content: Record<string, any>;
  is_favorite?: boolean;
  can_edit?: boolean;
  can_delete?: boolean;
}

interface TemplateManagerDialogProps {
  open: boolean;
  onClose: () => void;
  onSelectTemplate?: (template: SimulationTemplate) => void;
  mode?: 'select' | 'manage';
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
      id={`template-tabpanel-${index}`}
      aria-labelledby={`template-tab-${index}`}
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
    id: `template-tab-${index}`,
    'aria-controls': `template-tabpanel-${index}`,
  };
}

const TEMPLATE_CATEGORIES = [
  { value: 'simulation', label: '仿真模板', color: 'primary' },
  { value: 'batch', label: '批量模板', color: 'secondary' },
  { value: 'analysis', label: '分析模板', color: 'success' },
  { value: 'custom', label: '自定义模板', color: 'warning' }
];

const TEMPLATE_TYPES = [
  { value: 'simulation', label: '仿真模板' },
  { value: 'batch', label: '批量模板' },
  { value: 'analysis', label: '分析模板' }
];

const VISIBILITY_OPTIONS = [
  { value: 'private', label: '私有', icon: <LockIcon />, description: '仅自己可见' },
  { value: 'team', label: '团队', icon: <GroupIcon />, description: '团队成员可见' },
  { value: 'public', label: '公开', icon: <PublicIcon />, description: '所有人可见' }
];

export const TemplateManagerDialog: React.FC<TemplateManagerDialogProps> = ({
  open,
  onClose,
  onSelectTemplate,
  mode = 'manage'
}) => {
  const [tabValue, setTabValue] = useState(0);
  const [templates, setTemplates] = useState<SimulationTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<SimulationTemplate | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('updated_at');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [menuTemplate, setMenuTemplate] = useState<SimulationTemplate | null>(null);
  
  const api = useApi();

  // 获取模板列表
  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const response = await api.get('/templates', {
        params: {
          search: searchQuery,
          category: filterCategory !== 'all' ? filterCategory : undefined,
          sort_by: sortBy
        }
      });
      setTemplates(response.data.templates || []);
    } catch (err: any) {
      setError(err.message || '获取模板列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 创建模板
  const createTemplate = async (templateData: Partial<SimulationTemplate>) => {
    try {
      const response = await api.post('/templates', templateData);
      const newTemplate = response.data.template;
      setTemplates(prev => [newTemplate, ...prev]);
      setShowCreateDialog(false);
    } catch (err: any) {
      setError(err.message || '创建模板失败');
    }
  };

  // 更新模板
  const updateTemplate = async (templateId: string, updates: Partial<SimulationTemplate>) => {
    try {
      const response = await api.put(`/templates/${templateId}`, updates);
      const updatedTemplate = response.data.template;
      setTemplates(prev => 
        prev.map(t => t.id === templateId ? updatedTemplate : t)
      );
    } catch (err: any) {
      setError(err.message || '更新模板失败');
    }
  };

  // 删除模板
  const deleteTemplate = async (templateId: string) => {
    try {
      await api.delete(`/templates/${templateId}`);
      setTemplates(prev => prev.filter(t => t.id !== templateId));
      if (selectedTemplate?.id === templateId) {
        setSelectedTemplate(null);
      }
    } catch (err: any) {
      setError(err.message || '删除模板失败');
    }
  };

  // 收藏/取消收藏模板
  const toggleFavorite = async (templateId: string) => {
    try {
      const template = templates.find(t => t.id === templateId);
      if (!template) return;
      
      const response = await api.post(`/templates/${templateId}/favorite`, {
        is_favorite: !template.is_favorite
      });
      
      setTemplates(prev => 
        prev.map(t => 
          t.id === templateId 
            ? { ...t, is_favorite: response.data.is_favorite }
            : t
        )
      );
    } catch (err: any) {
      setError(err.message || '操作失败');
    }
  };

  // 复制模板
  const duplicateTemplate = async (templateId: string) => {
    try {
      const response = await api.post(`/templates/${templateId}/duplicate`);
      const newTemplate = response.data.template;
      setTemplates(prev => [newTemplate, ...prev]);
    } catch (err: any) {
      setError(err.message || '复制模板失败');
    }
  };

  // 导出模板
  const exportTemplate = async (templateId: string) => {
    try {
      const response = await api.get(`/templates/${templateId}/export`, {
        responseType: 'blob'
      });
      
      const template = templates.find(t => t.id === templateId);
      const filename = `${template?.metadata.name || 'template'}.json`;
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message || '导出模板失败');
    }
  };

  // 导入模板
  const importTemplate = async (file: File) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await api.post('/templates/import', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      const importedTemplate = response.data.template;
      setTemplates(prev => [importedTemplate, ...prev]);
    } catch (err: any) {
      setError(err.message || '导入模板失败');
    }
  };

  // 处理标签页切换
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  // 处理菜单
  const handleMenuClick = (event: React.MouseEvent<HTMLElement>, template: SimulationTemplate) => {
    setAnchorEl(event.currentTarget);
    setMenuTemplate(template);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setMenuTemplate(null);
  };

  // 获取状态颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft': return 'warning';
      case 'published': return 'success';
      case 'archived': return 'default';
      default: return 'default';
    }
  };

  // 过滤和排序模板
  const filteredTemplates = templates
    .filter(template => {
      const matchesSearch = searchQuery === '' || 
        template.metadata.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        template.metadata.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        template.metadata.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
      
      const matchesCategory = filterCategory === 'all' || 
        template.metadata.category === filterCategory;
      
      return matchesSearch && matchesCategory;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.metadata.name.localeCompare(b.metadata.name);
        case 'created_at':
          return new Date(b.metadata.created_at).getTime() - new Date(a.metadata.created_at).getTime();
        case 'updated_at':
          return new Date(b.metadata.updated_at).getTime() - new Date(a.metadata.updated_at).getTime();
        case 'rating':
          return (b.metadata.rating || 0) - (a.metadata.rating || 0);
        case 'usage_count':
          return (b.metadata.usage_count || 0) - (a.metadata.usage_count || 0);
        default:
          return 0;
      }
    });

  // 初始化
  useEffect(() => {
    if (open) {
      fetchTemplates();
    }
  }, [open, searchQuery, filterCategory, sortBy]);

  // 渲染模板卡片
  const renderTemplateCard = (template: SimulationTemplate) => (
    <Card 
      key={template.id}
      sx={{ 
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        cursor: mode === 'select' ? 'pointer' : 'default',
        '&:hover': mode === 'select' ? { boxShadow: 4 } : {}
      }}
      onClick={mode === 'select' ? () => onSelectTemplate?.(template) : undefined}
    >
      <CardContent sx={{ flexGrow: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
          <Typography variant="h6" component="div" noWrap>
            {template.metadata.name}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            {template.is_favorite && (
              <StarIcon color="warning" fontSize="small" />
            )}
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                handleMenuClick(e, template);
              }}
            >
              <MoreVertIcon />
            </IconButton>
          </Box>
        </Box>
        
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2, minHeight: 40 }}>
          {template.metadata.description}
        </Typography>
        
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
          <Chip 
            label={template.metadata.type} 
            size="small" 
            color="primary" 
            variant="outlined"
          />
          <Chip 
            label={template.metadata.status} 
            size="small" 
            color={getStatusColor(template.metadata.status) as any}
          />
          {template.metadata.visibility === 'public' && (
            <Chip 
              icon={<PublicIcon />}
              label="公开" 
              size="small" 
              color="info"
              variant="outlined"
            />
          )}
        </Box>
        
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
          {template.metadata.tags.slice(0, 3).map((tag) => (
            <Chip key={tag} label={tag} size="small" variant="outlined" />
          ))}
          {template.metadata.tags.length > 3 && (
            <Chip label={`+${template.metadata.tags.length - 3}`} size="small" variant="outlined" />
          )}
        </Box>
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Avatar sx={{ width: 24, height: 24, fontSize: 12 }}>
              {template.metadata.author.charAt(0).toUpperCase()}
            </Avatar>
            <Typography variant="caption" color="text.secondary">
              {template.metadata.author}
            </Typography>
          </Box>
          
          {template.metadata.rating && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Rating value={template.metadata.rating} readOnly size="small" />
              <Typography variant="caption" color="text.secondary">
                ({template.metadata.usage_count || 0})
              </Typography>
            </Box>
          )}
        </Box>
        
        <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
          更新于 {formatDateTime(template.metadata.updated_at)}
        </Typography>
      </CardContent>
      
      {mode === 'manage' && (
        <CardActions>
          <Button 
            size="small" 
            onClick={(e) => {
              e.stopPropagation();
              setSelectedTemplate(template);
            }}
          >
            查看详情
          </Button>
          {template.can_edit && (
            <Button size="small" startIcon={<EditIcon />}>
              编辑
            </Button>
          )}
        </CardActions>
      )}
    </Card>
  );

  // 渲染模板列表标签页
  const renderTemplatesTab = () => (
    <Box>
      {/* 搜索和过滤 */}
      <Box sx={{ mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              size="small"
              placeholder="搜索模板..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
              }}
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>分类</InputLabel>
              <Select
                value={filterCategory}
                onChange={(e) => setFilterCategory(e.target.value)}
                startAdornment={<FilterListIcon sx={{ mr: 1, color: 'text.secondary' }} />}
              >
                <MenuItem value="all">全部分类</MenuItem>
                {TEMPLATE_CATEGORIES.map((category) => (
                  <MenuItem key={category.value} value={category.value}>
                    {category.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>排序</InputLabel>
              <Select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                startAdornment={<SortIcon sx={{ mr: 1, color: 'text.secondary' }} />}
              >
                <MenuItem value="updated_at">最近更新</MenuItem>
                <MenuItem value="created_at">创建时间</MenuItem>
                <MenuItem value="name">名称</MenuItem>
                <MenuItem value="rating">评分</MenuItem>
                <MenuItem value="usage_count">使用次数</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={2}>
            <Button
              fullWidth
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setShowCreateDialog(true)}
            >
              新建模板
            </Button>
          </Grid>
        </Grid>
      </Box>
      
      {/* 模板网格 */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : filteredTemplates.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography color="textSecondary">
            {searchQuery || filterCategory !== 'all' ? '没有找到匹配的模板' : '暂无模板'}
          </Typography>
        </Box>
      ) : (
        <Grid container spacing={3}>
          {filteredTemplates.map((template) => (
            <Grid item xs={12} sm={6} md={4} key={template.id}>
              {renderTemplateCard(template)}
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );

  // 渲染模板详情标签页
  const renderDetailTab = () => (
    <Box>
      {selectedTemplate ? (
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
                    模板名称
                  </Typography>
                  <Typography variant="body1">{selectedTemplate.metadata.name}</Typography>
                </Box>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="textSecondary">
                    描述
                  </Typography>
                  <Typography variant="body1">{selectedTemplate.metadata.description}</Typography>
                </Box>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="textSecondary">
                    版本
                  </Typography>
                  <Typography variant="body1">{selectedTemplate.metadata.version}</Typography>
                </Box>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="textSecondary">
                    作者
                  </Typography>
                  <Typography variant="body1">{selectedTemplate.metadata.author}</Typography>
                </Box>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="textSecondary">
                    标签
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {selectedTemplate.metadata.tags.map((tag) => (
                      <Chip key={tag} label={tag} size="small" />
                    ))}
                  </Box>
                </Box>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="textSecondary">
                    创建时间
                  </Typography>
                  <Typography variant="body1">{formatDateTime(selectedTemplate.metadata.created_at)}</Typography>
                </Box>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="textSecondary">
                    更新时间
                  </Typography>
                  <Typography variant="body1">{formatDateTime(selectedTemplate.metadata.updated_at)}</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          {/* 参数配置 */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  参数配置 ({selectedTemplate.parameters.length})
                </Typography>
                
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>参数名</TableCell>
                        <TableCell>类型</TableCell>
                        <TableCell>必需</TableCell>
                        <TableCell>默认值</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {selectedTemplate.parameters.map((param) => (
                        <TableRow key={param.name}>
                          <TableCell>
                            <Typography variant="subtitle2">{param.name}</Typography>
                            <Typography variant="caption" color="textSecondary">
                              {param.description}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip label={param.type} size="small" variant="outlined" />
                          </TableCell>
                          <TableCell>
                            {param.required ? (
                              <Chip label="必需" size="small" color="error" />
                            ) : (
                              <Chip label="可选" size="small" color="default" />
                            )}
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {param.default_value !== undefined 
                                ? JSON.stringify(param.default_value) 
                                : '-'
                              }
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
          
          {/* 配置内容 */}
          <Grid item xs={12}>
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6">配置内容</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <JsonViewer data={selectedTemplate.configuration} />
              </AccordionDetails>
            </Accordion>
          </Grid>
          
          {/* 模板内容 */}
          <Grid item xs={12}>
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6">模板内容</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <JsonViewer data={selectedTemplate.content} />
              </AccordionDetails>
            </Accordion>
          </Grid>
        </Grid>
      ) : (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography color="textSecondary">
            请选择一个模板查看详情
          </Typography>
        </Box>
      )}
    </Box>
  );

  return (
    <>
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
              <TemplateIcon />
              <Typography variant="h6">
                {mode === 'select' ? '选择模板' : '模板管理'}
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', gap: 1 }}>
              <input
                accept=".json"
                style={{ display: 'none' }}
                id="import-template-file"
                type="file"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) {
                    importTemplate(file);
                  }
                }}
              />
              <label htmlFor="import-template-file">
                <Button
                  component="span"
                  startIcon={<UploadIcon />}
                  size="small"
                >
                  导入
                </Button>
              </label>
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
                label="模板列表" 
                icon={<TemplateIcon />} 
                iconPosition="start"
                {...a11yProps(0)} 
              />
              {mode === 'manage' && (
                <Tab 
                  label="模板详情" 
                  icon={<VisibilityIcon />} 
                  iconPosition="start"
                  {...a11yProps(1)} 
                />
              )}
            </Tabs>
          </Box>
          
          <TabPanel value={tabValue} index={0}>
            {renderTemplatesTab()}
          </TabPanel>
          
          {mode === 'manage' && (
            <TabPanel value={tabValue} index={1}>
              {renderDetailTab()}
            </TabPanel>
          )}
        </DialogContent>
        
        <DialogActions>
          <Button onClick={onClose}>
            {mode === 'select' ? '取消' : '关闭'}
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* 模板操作菜单 */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItemComponent onClick={() => {
          if (menuTemplate) {
            toggleFavorite(menuTemplate.id);
          }
          handleMenuClose();
        }}>
          <ListItemIcon>
            {menuTemplate?.is_favorite ? <StarIcon /> : <StarBorderIcon />}
          </ListItemIcon>
          <ListItemText>
            {menuTemplate?.is_favorite ? '取消收藏' : '收藏'}
          </ListItemText>
        </MenuItemComponent>
        
        <MenuItemComponent onClick={() => {
          if (menuTemplate) {
            duplicateTemplate(menuTemplate.id);
          }
          handleMenuClose();
        }}>
          <ListItemIcon>
            <CopyIcon />
          </ListItemIcon>
          <ListItemText>复制</ListItemText>
        </MenuItemComponent>
        
        <MenuItemComponent onClick={() => {
          if (menuTemplate) {
            exportTemplate(menuTemplate.id);
          }
          handleMenuClose();
        }}>
          <ListItemIcon>
            <DownloadIcon />
          </ListItemIcon>
          <ListItemText>导出</ListItemText>
        </MenuItemComponent>
        
        {menuTemplate?.can_edit && (
          <MenuItemComponent onClick={() => {
            // TODO: 打开编辑对话框
            handleMenuClose();
          }}>
            <ListItemIcon>
              <EditIcon />
            </ListItemIcon>
            <ListItemText>编辑</ListItemText>
          </MenuItemComponent>
        )}
        
        {menuTemplate?.can_delete && (
          <>
            <Divider />
            <MenuItemComponent 
              onClick={() => {
                if (menuTemplate && window.confirm('确定要删除这个模板吗？')) {
                  deleteTemplate(menuTemplate.id);
                }
                handleMenuClose();
              }}
              sx={{ color: 'error.main' }}
            >
              <ListItemIcon>
                <DeleteIcon color="error" />
              </ListItemIcon>
              <ListItemText>删除</ListItemText>
            </MenuItemComponent>
          </>
        )}
      </Menu>
    </>
  );
};

export default TemplateManagerDialog;