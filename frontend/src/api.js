// Auth: Node backend only. Crop/calendar: Python (FastAPI) backend directly.
const AUTH_API = import.meta.env.VITE_AUTH_API || "https://team-fab-5-agritech-1.onrender.com";
const CROP_API = import.meta.env.VITE_CROP_API || "https://team-fab-5-agritech.onrender.com";

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

/** Upload image for disease analysis (research agent). Returns { analysis } */
export async function analyzeImage(file) {
  const url = `${CROP_API}/analyze-image`;
  if (DEBUG) console.log("[api] POST", url, file?.name);
  const form = new FormData();
  form.append("image", file);
  const res = await fetch(url, { method: "POST", body: form });
  const data = await res.json().catch(() => ({}));
  if (!res.ok)
    throw new Error(data.detail || data.message || "Image analysis failed");
  return data;
}

// --- Chatbot (Python FastAPI backend) ---
export async function sendChatMessage(message, sessionId = 'default') {
  const url = `${CROP_API}/chat`;
  if (DEBUG) console.log('[api] POST', url, { message, session_id: sessionId });
  const res = await fetch(url, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ message, session_id: sessionId }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || data.message || 'Chat failed');
  return data;
}

export async function getChatHistory(sessionId = 'default') {
  const url = `${CROP_API}/chat/history?session_id=${sessionId}`;
  if (DEBUG) console.log('[api] GET', url);
  const res = await fetch(url, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || data.message || 'Get chat history failed');
  return data;
}

export async function clearChatHistory(sessionId = 'default') {
  const url = `${CROP_API}/chat/history?session_id=${sessionId}`;
  if (DEBUG) console.log('[api] DELETE', url);
  const res = await fetch(url, {
    method: 'DELETE',
    headers: headers(),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || data.message || 'Clear chat history failed');
  return data;
}

export async function getChatSuggestions(sessionId = 'default') {
  const url = `${CROP_API}/chat/suggestions?session_id=${sessionId}`;
  if (DEBUG) console.log('[api] GET', url);
  const res = await fetch(url, { headers: headers() });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || data.message || 'Get suggestions failed');
  return data;
}

// --- Market Price Prediction ---
export async function predictMarketPrice(body) {
  const url = `${CROP_API}/predict-market-price`;
  if (DEBUG) console.log('[api] POST', url, body);
  const res = await fetch(url, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || data.message || 'Market price prediction failed');
  return data;
}

// --- Pest/Disease Risk Assessment ---
export async function assessPestRisk(body) {
  const url = `${CROP_API}/assess-pest-risk`;
  if (DEBUG) console.log('[api] POST', url, body);
  const res = await fetch(url, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || data.message || 'Pest risk assessment failed');
  return data;
}

/** Regenerate calendar with disease analysis (more weight to disease management) */
export async function generateCalendarWithDiseaseAnalysis(analysis) {
  const url = `${CROP_API}/generate-calendar`;
  if (DEBUG) console.log("[api] POST", url, "disease_analysis=...");
  const res = await fetch(url, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ disease_analysis: analysis || "" }),
  });
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
