# Crop Calendar Frontend

React + Vite + Tailwind. Landing, Login/Register, Farmer Dashboard (crop selection, variable generation, calendar generation, daily tasks, full calendar).

## Run

```bash
npm install
npm run dev
```

Open http://localhost:5173. Ensure **Node backend** (port 3001) and **FastAPI** (port 8000) are running.

## Proxy

Vite proxies `/api` to the Node backend (3001). Node proxies `/api/crop` to FastAPI (8000).
