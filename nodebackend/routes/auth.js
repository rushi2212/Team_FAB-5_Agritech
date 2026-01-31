import express from 'express';
import jwt from 'jsonwebtoken';
import { body, validationResult } from 'express-validator';
import User from '../models/User.js';
import { JWT_SECRET } from '../config.js';

const DEBUG = process.env.DEBUG === '1' || process.env.CROP_DEBUG === '1';
const log = (...args) => DEBUG && console.log('[crop-node auth]', ...args);

const router = express.Router();

const validate = (req, res, next) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    log('validate errors', errors.array());
    return res.status(400).json({ success: false, errors: errors.array() });
  }
  next();
};

// Register
router.post(
  '/register',
  [
    body('name').trim().notEmpty().withMessage('Name is required'),
    body('email').isEmail().normalizeEmail().withMessage('Valid email is required'),
    body('password').isLength({ min: 6 }).withMessage('Password must be at least 6 characters'),
  ],
  validate,
  async (req, res) => {
    try {
      const { name, email, password } = req.body;
      log('register', { name, email });
      const existing = await User.findOne({ email });
      if (existing) {
        log('register 400 email exists');
        return res.status(400).json({ success: false, message: 'Email already registered' });
      }
      const user = await User.create({ name, email, password });
      const token = jwt.sign({ id: user._id, email: user.email }, JWT_SECRET, { expiresIn: '7d' });
      log('register 201', user._id, user.email);
      res.status(201).json({
        success: true,
        message: 'Registered successfully',
        token,
        user: { id: user._id, name: user.name, email: user.email, role: user.role },
      });
    } catch (err) {
      log('register 500', err.message);
      res.status(500).json({ success: false, message: err.message || 'Registration failed' });
    }
  }
);

// Login
router.post(
  '/login',
  [
    body('email').isEmail().normalizeEmail(),
    body('password').notEmpty(),
  ],
  validate,
  async (req, res) => {
    try {
      const { email, password } = req.body;
      log('login', { email });
      const user = await User.findOne({ email });
      if (!user || !(await user.comparePassword(password))) {
        log('login 401 invalid');
        return res.status(401).json({ success: false, message: 'Invalid email or password' });
      }
      const token = jwt.sign({ id: user._id, email: user.email }, JWT_SECRET, { expiresIn: '7d' });
      log('login 200', user._id, user.email);
      res.json({
        success: true,
        token,
        user: { id: user._id, name: user.name, email: user.email, role: user.role },
      });
    } catch (err) {
      log('login 500', err.message);
      res.status(500).json({ success: false, message: err.message || 'Login failed' });
    }
  }
);

// Get current user (protected)
export const authMiddleware = (req, res, next) => {
  const authHeader = req.headers.authorization;
  const token = authHeader?.startsWith('Bearer ') ? authHeader.slice(7) : null;
  if (!token) {
    log('authMiddleware 401 no token');
    return res.status(401).json({ success: false, message: 'Token required' });
  }
  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    req.userId = decoded.id;
    req.userEmail = decoded.email;
    log('authMiddleware ok', decoded.id);
    next();
  } catch (e) {
    log('authMiddleware 401 invalid token', e.message);
    return res.status(401).json({ success: false, message: 'Invalid or expired token' });
  }
};

router.get('/me', authMiddleware, async (req, res) => {
  try {
    log('GET /me', req.userId);
    const user = await User.findById(req.userId).select('-password');
    if (!user) {
      log('/me 404');
      return res.status(404).json({ success: false, message: 'User not found' });
    }
    res.json({ success: true, user: { id: user._id, name: user.name, email: user.email, role: user.role } });
  } catch (err) {
    log('/me 500', err.message);
    res.status(500).json({ success: false, message: err.message });
  }
});

export default router;
