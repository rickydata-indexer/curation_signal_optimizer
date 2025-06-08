import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/curation_signal_optimizer/', // Correct repo name with underscores
  server: {
    port: 5174,
    host: '0.0.0.0', // Allow external connections
    allowedHosts: true,
    proxy: {
      '/api/supabase': {
        target: 'http://supabasekong-so4w8gock004k8kw8ck84o80.94.130.17.180.sslip.io',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/supabase/, '/api/pg-meta/default/query'),
        configure: (proxy, options) => {
          proxy.on('proxyReq', (proxyReq, req, res) => {
            // Add CORS headers
            proxyReq.setHeader('Access-Control-Allow-Origin', '*');
            proxyReq.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
            proxyReq.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
          });
        }
      }
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
    extensions: ['.mjs', '.js', '.jsx', '.ts', '.tsx', '.json']
  },
  optimizeDeps: {
    esbuildOptions: {
      loader: {
        '.js': 'jsx',
      },
    },
  },
}) 