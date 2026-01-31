import express from 'express';
import cors from 'cors';
import { createProxyMiddleware } from 'http-proxy-middleware';
import mongoose from 'mongoose';
import authRoutes from './routes/auth.js';
import { authMiddleware } from './routes/auth.js';
import { PORT, MONGODB_URI, FASTAPI_URL } from './config.js';

const DEBUG = process.env.DEBUG === '1' || process.env.CROP_DEBUG === '1';
const log = (...args) => DEBUG && console.log('[crop-node]', ...args);

const app = express();
app.use(cors({ origin: true, credentials: true }));
app.use(express.json());

// Request logging (debug)
app.use((req, res, next) => {
  log(req.method, req.url);
  next();
});

// Health
app.get('/api/health', (req, res) => {
  log('GET /api/health');
  res.json({ ok: true, service: 'node-auth' });
});

// Auth
app.use('/api/auth', authRoutes);

// Protected route example (optional)
app.get('/api/protected', authMiddleware, (req, res) => {
  log('GET /api/protected userId=', req.userId);
  res.json({ message: 'Protected', userId: req.userId });
});

// Proxy to FastAPI for crop calendar (so frontend talks to one origin)
app.use(
  '/api/crop',
  createProxyMiddleware({
    target: FASTAPI_URL,
    changeOrigin: true,
    pathRewrite: { '^/api/crop': '' },
    onProxyReq: (proxyReq, req) => {
      log('proxy', req.method, req.url, '->', FASTAPI_URL + req.url.replace(/^\/api\/crop/, ''));
    },
    onError: (err, req, res) => {
      log('proxy error', err.message);
      res.status(502).json({ error: 'Crop API unavailable', detail: err.message });
    },
  })
);

async function start() {
  try {
    await mongoose.connect(MONGODB_URI);
    console.log('MongoDB connected');
    log('MongoDB URI', MONGODB_URI.replace(/\/\/[^:]+:[^@]+@/, '//***:***@'));
  } catch (e) {
    console.error('MongoDB connection failed:', e.message);
    log('MongoDB error', e.message);
  }
  app.listen(PORT, () => {
    console.log(`Node server on http://127.0.0.1:${PORT}`);
    log('FASTAPI_URL', FASTAPI_URL, 'DEBUG', DEBUG);
  });
}

start();
