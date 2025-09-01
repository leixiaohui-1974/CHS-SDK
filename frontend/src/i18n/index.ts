import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import Backend from 'i18next-http-backend';

// 导入语言资源
import zhCN from './locales/zh-CN.json';
import enUS from './locales/en-US.json';
import jaJP from './locales/ja-JP.json';
import koKR from './locales/ko-KR.json';
import frFR from './locales/fr-FR.json';
import deDE from './locales/de-DE.json';
import esES from './locales/es-ES.json';
import ruRU from './locales/ru-RU.json';

// 支持的语言列表
export const supportedLanguages = [
  { code: 'zh-CN', name: '简体中文', nativeName: '简体中文' },
  { code: 'en-US', name: 'English', nativeName: 'English' },
  { code: 'ja-JP', name: 'Japanese', nativeName: '日本語' },
  { code: 'ko-KR', name: 'Korean', nativeName: '한국어' },
  { code: 'fr-FR', name: 'French', nativeName: 'Français' },
  { code: 'de-DE', name: 'German', nativeName: 'Deutsch' },
  { code: 'es-ES', name: 'Spanish', nativeName: 'Español' },
  { code: 'ru-RU', name: 'Russian', nativeName: 'Русский' }
];

// 语言资源
const resources = {
  'zh-CN': { translation: zhCN },
  'en-US': { translation: enUS },
  'ja-JP': { translation: jaJP },
  'ko-KR': { translation: koKR },
  'fr-FR': { translation: frFR },
  'de-DE': { translation: deDE },
  'es-ES': { translation: esES },
  'ru-RU': { translation: ruRU }
};

// 语言检测配置
const detectionOptions = {
  // 检测顺序
  order: [
    'localStorage',
    'sessionStorage',
    'navigator',
    'htmlTag',
    'path',
    'subdomain'
  ],
  
  // 缓存用户语言选择
  caches: ['localStorage', 'sessionStorage'],
  
  // 排除的路径
  excludeCacheFor: ['cimode'],
  
  // 检查白名单
  checkWhitelist: true
};

// 初始化 i18n
i18n
  .use(Backend)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    
    // 默认语言
    fallbackLng: 'zh-CN',
    
    // 支持的语言白名单
    supportedLngs: supportedLanguages.map(lang => lang.code),
    
    // 语言检测
    detection: detectionOptions,
    
    // 调试模式
    debug: process.env.NODE_ENV === 'development',
    
    // 插值配置
    interpolation: {
      escapeValue: false, // React 已经安全处理了
      formatSeparator: ','
    },
    
    // 后端配置
    backend: {
      loadPath: '/locales/{{lng}}/{{ns}}.json',
      addPath: '/locales/add/{{lng}}/{{ns}}',
      allowMultiLoading: false,
      crossDomain: false,
      withCredentials: false,
      overrideMimeType: false,
      requestOptions: {
        mode: 'cors',
        credentials: 'same-origin',
        cache: 'default'
      }
    },
    
    // React 配置
    react: {
      useSuspense: true,
      bindI18n: 'languageChanged',
      bindI18nStore: '',
      transEmptyNodeValue: '',
      transSupportBasicHtmlNodes: true,
      transKeepBasicHtmlNodesFor: ['br', 'strong', 'i', 'p']
    },
    
    // 命名空间
    ns: ['translation'],
    defaultNS: 'translation',
    
    // 键分隔符
    keySeparator: '.',
    nsSeparator: ':',
    
    // 复数规则
    pluralSeparator: '_',
    contextSeparator: '_',
    
    // 缺失键处理
    saveMissing: process.env.NODE_ENV === 'development',
    saveMissingTo: 'fallback',
    missingKeyHandler: (lng, ns, key, fallbackValue) => {
      if (process.env.NODE_ENV === 'development') {
        console.warn(`Missing translation key: ${key} for language: ${lng}`);
      }
    },
    
    // 后处理器
    postProcess: ['interval', 'plural'],
    
    // 清理代码
    cleanCode: true,
    
    // 加载超时
    load: 'languageOnly',
    preload: ['zh-CN', 'en-US'],
    
    // 更新缺失
    updateMissing: false,
    
    // 返回对象
    returnObjects: false,
    returnEmptyString: true,
    returnNull: true,
    
    // 加入空值
    joinArrays: false,
    
    // 忽略 JSON 结构
    ignoreJSONStructure: true
  });

// 语言切换函数
export const changeLanguage = (language: string) => {
  return i18n.changeLanguage(language);
};

// 获取当前语言
export const getCurrentLanguage = () => {
  return i18n.language;
};

// 获取语言信息
export const getLanguageInfo = (code: string) => {
  return supportedLanguages.find(lang => lang.code === code);
};

// 检查是否为 RTL 语言
export const isRTL = (language?: string) => {
  const lang = language || getCurrentLanguage();
  const rtlLanguages = ['ar', 'he', 'fa', 'ur'];
  return rtlLanguages.some(rtl => lang.startsWith(rtl));
};

// 格式化数字
export const formatNumber = (number: number, language?: string) => {
  const lang = language || getCurrentLanguage();
  return new Intl.NumberFormat(lang).format(number);
};

// 格式化货币
export const formatCurrency = (amount: number, currency = 'CNY', language?: string) => {
  const lang = language || getCurrentLanguage();
  return new Intl.NumberFormat(lang, {
    style: 'currency',
    currency
  }).format(amount);
};

// 格式化日期
export const formatDate = (date: Date | string | number, options?: Intl.DateTimeFormatOptions, language?: string) => {
  const lang = language || getCurrentLanguage();
  const dateObj = typeof date === 'string' || typeof date === 'number' ? new Date(date) : date;
  
  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  };
  
  return new Intl.DateTimeFormat(lang, { ...defaultOptions, ...options }).format(dateObj);
};

// 格式化相对时间
export const formatRelativeTime = (date: Date | string | number, language?: string) => {
  const lang = language || getCurrentLanguage();
  const dateObj = typeof date === 'string' || typeof date === 'number' ? new Date(date) : date;
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - dateObj.getTime()) / 1000);
  
  const rtf = new Intl.RelativeTimeFormat(lang, { numeric: 'auto' });
  
  if (diffInSeconds < 60) {
    return rtf.format(-diffInSeconds, 'second');
  } else if (diffInSeconds < 3600) {
    return rtf.format(-Math.floor(diffInSeconds / 60), 'minute');
  } else if (diffInSeconds < 86400) {
    return rtf.format(-Math.floor(diffInSeconds / 3600), 'hour');
  } else if (diffInSeconds < 2592000) {
    return rtf.format(-Math.floor(diffInSeconds / 86400), 'day');
  } else if (diffInSeconds < 31536000) {
    return rtf.format(-Math.floor(diffInSeconds / 2592000), 'month');
  } else {
    return rtf.format(-Math.floor(diffInSeconds / 31536000), 'year');
  }
};

// 获取浏览器语言
export const getBrowserLanguage = () => {
  return navigator.language || navigator.languages[0] || 'zh-CN';
};

// 语言匹配
export const matchLanguage = (requested: string) => {
  // 精确匹配
  if (supportedLanguages.some(lang => lang.code === requested)) {
    return requested;
  }
  
  // 语言代码匹配（忽略地区）
  const languageCode = requested.split('-')[0];
  const matched = supportedLanguages.find(lang => lang.code.startsWith(languageCode));
  
  return matched ? matched.code : 'zh-CN';
};

// 预加载语言
export const preloadLanguage = (language: string) => {
  return i18n.loadLanguages(language);
};

// 添加资源包
export const addResourceBundle = (language: string, namespace: string, resources: any) => {
  i18n.addResourceBundle(language, namespace, resources, true, true);
};

// 移除资源包
export const removeResourceBundle = (language: string, namespace: string) => {
  i18n.removeResourceBundle(language, namespace);
};

// 检查翻译是否存在
export const hasTranslation = (key: string, language?: string) => {
  const lang = language || getCurrentLanguage();
  return i18n.exists(key, { lng: lang });
};

// 获取翻译（不使用 React Hook）
export const getTranslation = (key: string, options?: any, language?: string) => {
  const lang = language || getCurrentLanguage();
  return i18n.t(key, { ...options, lng: lang });
};

// 语言变化监听器
export const onLanguageChange = (callback: (language: string) => void) => {
  i18n.on('languageChanged', callback);
  return () => i18n.off('languageChanged', callback);
};

// 初始化完成监听器
export const onInitialized = (callback: () => void) => {
  if (i18n.isInitialized) {
    callback();
  } else {
    i18n.on('initialized', callback);
  }
};

export default i18n;