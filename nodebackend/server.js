import express from 'express';
import cors from 'cors';
import mongoose from 'mongoose';
import authRoutes from './routes/auth.js';
import { authMiddleware } from './routes/auth.js';
import { PORT, MONGODB_URI } from './config.js';
import { sendPestAlert, verifyEmailConfig } from './emailService.js';

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

// Email service endpoints
app.post('/api/send-pest-alert', async (req, res) => {
  log('POST /api/send-pest-alert');
  try {
    const { riskData, recipientEmail } = req.body;
    
    if (!recipientEmail) {
      return res.status(400).json({ success: false, error: 'Recipient email is required' });
    }
    
    if (!riskData) {
      return res.status(400).json({ success: false, error: 'Risk data is required' });
    }
    
    const success = await sendPestAlert(riskData, recipientEmail);
    
    if (success) {
      res.json({ success: true, message: 'Alert email sent successfully' });
    } else {
      res.status(500).json({ success: false, error: 'Failed to send email' });
    }
  } catch (error) {
    log('Email send error:', error.message);
    res.status(500).json({ success: false, error: error.message });
  }
});

app.get('/api/verify-email-config', async (req, res) => {
  log('GET /api/verify-email-config');
  try {
    const isConfigured = await verifyEmailConfig();
    res.json({ configured: isConfigured });
  } catch (error) {
    log('Email verify error:', error.message);
    res.json({ configured: false, error: error.message });
  }
});

// Crop/calendar: frontend calls Python backend directly (no proxy)

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
    console.log(`Node server on http://127.0.0.1:${PORT} (auth only)`);
    log('DEBUG', DEBUG);
  });
}

start();
