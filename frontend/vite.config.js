import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // No API proxy: auth → Node (VITE_AUTH_API), crop/calendar → Python (VITE_CROP_API) directly
  },
});
