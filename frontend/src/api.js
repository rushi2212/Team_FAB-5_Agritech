// Auth: Node backend only. Crop/calendar: Python (FastAPI) backend directly.
const AUTH_API = import.meta.env.VITE_AUTH_API || "http://127.0.0.1:3001";
const CROP_API = import.meta.env.VITE_CROP_API || "http://127.0.0.1:8000";

const DEBUG = import.meta.env.VITE_DEBUG === "1";

function getToken() {
  return localStorage.getItem("token");
}

function headers(includeAuth = false) {
  const h = { "Content-Type": "application/json" };
  if (includeAuth && getToken()) h["Authorization"] = `Bearer ${getToken()}`;
  return h;
}

// --- Auth (Node backend) ---
export async function register(name, email, password) {
  const url = `${AUTH_API}/api/auth/register`;
  if (DEBUG) console.log("[api] POST", url);
  const res = await fetch(url, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ name, email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Registration failed");
  return data;
}

export async function login(email, password) {
  const url = `${AUTH_API}/api/auth/login`;
  if (DEBUG) console.log("[api] POST", url);
  const res = await fetch(url, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Login failed");
  return data;
}

export async function getMe() {
  const url = `${AUTH_API}/api/auth/me`;
  if (DEBUG) console.log("[api] GET", url);
  const res = await fetch(url, { headers: headers(true) });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Unauthorized");
  return data;
}

// --- Crop / calendar (Python FastAPI backend directly) ---
export async function generateVariable(body) {
  const url = `${CROP_API}/generate-variable`;
  if (DEBUG) console.log("[api] POST", url, body);
  const res = await fetch(url, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok)
    throw new Error(data.detail || data.message || "Generate variable failed");
  return data;
}

export async function getVariable() {
  const url = `${CROP_API}/variable`;
  if (DEBUG) console.log("[api] GET", url);
  const res = await fetch(url, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok)
    throw new Error(data.detail || data.message || "Variable not found");
  return data;
}

export async function updateDayOfCycle(day_of_cycle) {
  const url = `${CROP_API}/variable`;
  if (DEBUG) console.log("[api] PATCH", url, { day_of_cycle });
  const res = await fetch(url, {
    method: "PATCH",
    headers: headers(),
    body: JSON.stringify({ day_of_cycle }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok)
    throw new Error(
      data.detail || data.message || "Update day_of_cycle failed",
    );
  return data;
}

export async function getPersistent() {
  const url = `${CROP_API}/persistent`;
  if (DEBUG) console.log("[api] GET", url);
  const res = await fetch(url, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok)
    throw new Error(data.detail || data.message || "Persistent not found");
  return data;
}

export async function getCalendar() {
  const url = `${CROP_API}/calendar`;
  if (DEBUG) console.log("[api] GET", url);
  const res = await fetch(url, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok)
    throw new Error(data.detail || data.message || "Calendar not found");
  return data;
}

export async function generateCalendar() {
  const url = `${CROP_API}/generate-calendar`;
  if (DEBUG) console.log("[api] POST", url);
  const res = await fetch(url, { method: "POST", headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok)
    throw new Error(data.detail || data.message || "Generate calendar failed");
  return data;
}

export async function recommendCrops({ city, soil_type }) {
  const url = `${CROP_API}/recommend-crops`;
  if (DEBUG) console.log("[api] POST", url, { city, soil_type });
  const res = await fetch(url, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ city, soil_type }),
  });
  if (res.status === 404) return { crops: [] };
  const data = await res.json().catch(() => ({}));
  if (!res.ok)
    throw new Error(data.detail || data.message || "Recommend failed");
  return {
    ...data,
    crops: data.recommended_crops || data.crops || [],
    rationale: data.recommendation_rationale || data.rationale || "",
  };
}
