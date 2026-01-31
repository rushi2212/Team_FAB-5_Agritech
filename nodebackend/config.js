import dotenv from 'dotenv';
dotenv.config();

const DEBUG = process.env.DEBUG === '1' || process.env.CROP_DEBUG === '1';
const log = (...args) => DEBUG && console.log('[crop-node config]', ...args);

export const PORT = process.env.PORT || 3001;
export const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/crop_calendar';
export const JWT_SECRET = process.env.JWT_SECRET || 'dev-secret-change-in-production';
export const FASTAPI_URL = process.env.FASTAPI_URL || 'http://127.0.0.1:8000';

log('PORT', PORT, 'FASTAPI_URL', FASTAPI_URL);
