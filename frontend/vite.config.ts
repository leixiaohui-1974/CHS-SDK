import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@components': resolve(__dirname, 'src/components'),
      '@pages': resolve(__dirname, 'src/pages'),
      '@services': resolve(__dirname, 'src/services'),
      '@utils': resolve(__dirname, 'src/utils'),
      '@stores': resolve(__dirname, 'src/stores'),
      '@assets': resolve(__dirname, 'src/assets'),
      '@i18n': resolve(__dirname, 'src/i18n')
    }
  },
  build: {
    target: 'es2022',
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.info']
      }
    },
    rollupOptions: {
      output: {
        manualChunks: {
          // 将React相关库分离到单独的chunk
          'react-vendor': ['react', 'react-dom'],
          // 将UI库分离到单独的chunk
          'ui-vendor': ['antd'],
          // 将工具库分离到单独的chunk
          'utils-vendor': ['axios', 'zustand', 'uuid'],
          // 将图表库分离到单独的chunk
          'chart-vendor': ['recharts', 'reactflow'],
          // 将路由库分离到单独的chunk
          'router-vendor': ['react-router-dom'],
          // 将网格布局库分离到单独的chunk
          'layout-vendor': ['react-grid-layout']
        },
        chunkFileNames: (chunkInfo) => {
          const facadeModuleId = chunkInfo.facadeModuleId
          if (facadeModuleId) {
            if (facadeModuleId.includes('node_modules')) {
              return 'vendor/[name]-[hash].js'
            }
            if (facadeModuleId.includes('src/pages')) {
              return 'pages/[name]-[hash].js'
            }
            if (facadeModuleId.includes('src/components')) {
              return 'components/[name]-[hash].js'
            }
          }
          return 'chunks/[name]-[hash].js'
        },
        entryFileNames: 'assets/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name?.split('.') || []
          const ext = info[info.length - 1]
          if (/\.(png|jpe?g|gif|svg|webp|ico)$/i.test(assetInfo.name || '')) {
            return 'images/[name]-[hash].[ext]'
          }
          if (/\.(woff2?|eot|ttf|otf)$/i.test(assetInfo.name || '')) {
            return 'fonts/[name]-[hash].[ext]'
          }
          if (/\.(css)$/i.test(assetInfo.name || '')) {
            return 'styles/[name]-[hash].[ext]'
          }
          return 'assets/[name]-[hash].[ext]'
        }
      }
    },
    // 启用gzip压缩
    reportCompressedSize: true,
    // 设置chunk大小警告限制
    chunkSizeWarningLimit: 1000,
    // 启用源码映射（生产环境可关闭）
    sourcemap: false
  },
  server: {
    port: 3000,
    host: true,
    open: true,
    cors: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true
      }
    }
  },
  preview: {
    port: 4173,
    host: true,
    cors: true
  },
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'antd',
      'axios',
      'zustand',
      'react-router-dom',
      'recharts',
      'reactflow',
      'react-grid-layout',
      'uuid'
    ],
    exclude: ['@types/react', '@types/react-dom']
  },
  esbuild: {
    // 移除生产环境的console和debugger
    drop: ['console', 'debugger']
  }
})
