# Crop Calendar Node Backend

Auth (register/login) with MongoDB + JWT. Proxies `/api/crop` to FastAPI.

## Setup

1. Copy `.env.example` to `.env` and set `MONGODB_URI`, `JWT_SECRET`, `FASTAPI_URL`.
2. Ensure MongoDB is running and FastAPI is on `FASTAPI_URL` (default http://127.0.0.1:8000).

## Run

```bash
npm install
npm run dev
```

Server runs on http://127.0.0.1:3001. Frontend should proxy `/api` to this URL.
