const API = '/api';

function getToken() {
  return localStorage.getItem('token');
}

function headers(includeAuth = false) {
  const h = { 'Content-Type': 'application/json' };
  if (includeAuth && getToken()) h['Authorization'] = `Bearer ${getToken()}`;
  return h;
}

// Auth
export async function register(name, email, password) {
  const res = await fetch(`${API}/auth/register`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ name, email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || 'Registration failed');
  return data;
}

export async function login(email, password) {
  const res = await fetch(`${API}/auth/login`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || 'Login failed');
  return data;
}

export async function getMe() {
  const res = await fetch(`${API}/auth/me`, { headers: headers(true) });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || 'Unauthorized');
  return data;
}

// Crop API (proxied to FastAPI)
export async function generateVariable(body) {
  const res = await fetch(`${API}/crop/generate-variable`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || data.message || 'Generate variable failed');
  return data;
}

export async function getVariable() {
  const res = await fetch(`${API}/crop/variable`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || data.message || 'Variable not found');
  return data;
}

export async function updateDayOfCycle(day_of_cycle) {
  const res = await fetch(`${API}/crop/variable`, {
    method: 'PATCH',
    headers: headers(),
    body: JSON.stringify({ day_of_cycle }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || data.message || 'Update day_of_cycle failed');
  return data;
}

export async function getPersistent() {
  const res = await fetch(`${API}/crop/persistent`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || data.message || 'Persistent not found');
  return data;
}

export async function getCalendar() {
  const res = await fetch(`${API}/crop/calendar`, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || data.message || 'Calendar not found');
  return data;
}

export async function generateCalendar() {
  const res = await fetch(`${API}/crop/generate-calendar`, { method: 'POST', headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || data.message || 'Generate calendar failed');
  return data;
}

// Placeholder for future endpoint
export async function recommendCrops() {
  const res = await fetch(`${API}/crop/recommend-crops`, { headers: headers() });
  if (res.status === 404) return { crops: [] };
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || data.message || 'Recommend failed');
  return data;
}
