// ─── API Configuration ────────────────────────────────────────────────────────

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ─── Auth Token Helper ────────────────────────────────────────────────────────

function getAuthToken() {
  return localStorage.getItem('euroshub_auth_token');
}

// ─── Core Request Helper ──────────────────────────────────────────────────────

async function request(path, options = {}) {
  const token = getAuthToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };

  const config = {
    ...options,
    headers,
  };

  // Remove Content-Type for FormData so browser sets multipart boundary
  if (options.body instanceof FormData) {
    delete config.headers['Content-Type'];
  }

  const url = `${API_BASE}${path}`;

  let response;
  try {
    response = await fetch(url, config);
  } catch (networkErr) {
    throw new Error(`Network error: Cannot reach the server. Is the backend running? (${networkErr.message})`);
  }

  if (!response.ok) {
    let errorPayload;
    try {
      errorPayload = await response.json();
    } catch {
      errorPayload = { message: response.statusText };
    }
    let message;
    if (typeof errorPayload?.detail === 'string') {
      message = errorPayload.detail;
    } else if (Array.isArray(errorPayload?.detail)) {
      message = errorPayload.detail
        .map((d) => (typeof d === 'string' ? d : d?.msg || JSON.stringify(d)))
        .join(', ');
    } else if (typeof errorPayload?.message === 'string') {
      message = errorPayload.message;
    } else if (typeof errorPayload?.error === 'string') {
      message = errorPayload.error;
    } else if (errorPayload?.details && Array.isArray(errorPayload.details)) {
      message = errorPayload.details
        .map((d) => (typeof d === 'string' ? d : d?.msg || JSON.stringify(d)))
        .join(', ');
    } else if (errorPayload && typeof errorPayload === 'object') {
      try {
        message = JSON.stringify(errorPayload);
      } catch {
        message = `Request failed with status ${response.status}`;
      }
    } else {
      message = `Request failed with status ${response.status}`;
    }
    const err = new Error(message);
    err.status = response.status;
    err.payload = errorPayload;
    throw err;
  }

  if (response.status === 204) return null;

  try {
    return await response.json();
  } catch {
    return null;
  }
}

// ─── URL Query Builder ────────────────────────────────────────────────────────

function buildQuery(params = {}) {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== '') {
      q.append(k, String(v));
    }
  }
  const s = q.toString();
  return s ? `?${s}` : '';
}

// ─── API Surface ──────────────────────────────────────────────────────────────

export const api = {
  // ── Auth / Profiles ──────────────────────────────────────────────────────

  auth: {
    getMe: () => request('/auth/me'),

    updateMe: (data) =>
      request('/auth/me', { method: 'PUT', body: JSON.stringify(data) }),

    getUsers: () => request('/auth/users'),

    createUser: (data) =>
      request('/auth/users', { method: 'POST', body: JSON.stringify(data) }),

    changeUserRole: (userId, role) =>
      request(`/auth/users/${userId}/role`, {
        method: 'PUT',
        body: JSON.stringify({ role }),
      }),
  },

  // ── Teams ────────────────────────────────────────────────────────────────

  teams: {
    list: () => request('/teams'),

    get: (teamId) => request(`/teams/${teamId}`),

    create: (data) =>
      request('/teams', { method: 'POST', body: JSON.stringify(data) }),

    update: (teamId, data) =>
      request(`/teams/${teamId}`, { method: 'PUT', body: JSON.stringify(data) }),

    delete: (teamId) =>
      request(`/teams/${teamId}`, { method: 'DELETE' }),

    listMembers: (teamId) => request(`/teams/${teamId}/members`),

    addMember: (teamId, userId) =>
      request(`/teams/${teamId}/members`, {
        method: 'POST',
        body: JSON.stringify({ user_id: userId }),
      }),

    removeMember: (teamId, userId) =>
      request(`/teams/${teamId}/members/${userId}`, { method: 'DELETE' }),

    getUserTeams: (userId) => request(`/teams/user/${userId}`),
  },

  // ── Leads ────────────────────────────────────────────────────────────────

  leads: {
    list: (params = {}) => request(`/leads${buildQuery(params)}`),

    get: (id) => request(`/leads/${id}`),

    create: (data) =>
      request('/leads', { method: 'POST', body: JSON.stringify(data) }),

    update: (id, data) =>
      request(`/leads/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

    delete: (id) => request(`/leads/${id}`, { method: 'DELETE' }),

    getHistory: (id) => request(`/leads/${id}/history`),

    checkDuplicate: (data) =>
      request('/leads/check-duplicates', {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    verify: (id) =>
      request(`/leads/${id}/verify`, { method: 'POST' }),

    verifyBatch: (leadIds) =>
      request('/leads/verify-batch', {
        method: 'POST',
        body: JSON.stringify({ lead_ids: leadIds }),
      }),

    promoteTocrm: (id) =>
      request(`/leads/${id}/promote`, { method: 'POST' }),

    discover: (params = {}) =>
      request(`/leads/discovery/search${buildQuery(params)}`),

    getVerified: (params = {}) =>
      request(`/leads/verified${buildQuery(params)}`),

    previewImport: (formData) =>
      request('/leads/import/preview', { method: 'POST', body: formData }),

    executeImport: (formData) =>
      request('/leads/import', { method: 'POST', body: formData }),

    getImportHistory: () => request('/leads/imports/history'),

    getVerificationDetails: (id) => request(`/leads/${id}/verification`),
  },

  // ── Sources ──────────────────────────────────────────────────────────────

  sources: {
    list: () => request('/leads/sources'),
    create: (name) =>
      request('/leads/sources', { method: 'POST', body: JSON.stringify({ name }) }),
    delete: (id) => request(`/leads/sources/${id}`, { method: 'DELETE' }),
  },

  // ── Activities ───────────────────────────────────────────────────────────

  activities: {
    list: (leadId) => request(`/activities/${leadId}`),
    create: (leadId, data) =>
      request(`/activities/${leadId}`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    update: (leadId, activityId, data) =>
      request(`/activities/${leadId}/${activityId}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    delete: (leadId, activityId) =>
      request(`/activities/${leadId}/${activityId}`, { method: 'DELETE' }),
  },

  // ── Tasks ────────────────────────────────────────────────────────────────

  tasks: {
    list: (params = {}) => request(`/tasks${buildQuery(params)}`),
    create: (data) =>
      request('/tasks', { method: 'POST', body: JSON.stringify(data) }),
    update: (id, data) =>
      request(`/tasks/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id) => request(`/tasks/${id}`, { method: 'DELETE' }),
  },

  // ── AI ───────────────────────────────────────────────────────────────────

  ai: {
    analyze: (leadId) =>
      request(`/ai/analyze/${leadId}`, { method: 'POST' }),
    generateProposal: (leadId, tone) =>
      request(`/ai/proposal/${leadId}`, {
        method: 'POST',
        body: JSON.stringify({ tone }),
      }),
    chat: (message, context) =>
      request('/ai/chat', {
        method: 'POST',
        body: JSON.stringify({ message, context }),
      }),
  },

  // ── Proposals ────────────────────────────────────────────────────────────

  proposals: {
    list: (leadId) => request(`/proposals/${leadId}`),
    create: (leadId, data) =>
      request(`/proposals/${leadId}`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    update: (id, data) =>
      request(`/proposals/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    delete: (id) => request(`/proposals/${id}`, { method: 'DELETE' }),
  },

  // ── Dashboard ────────────────────────────────────────────────────────────

  dashboard: {
    getStats: () => request('/dashboard/stats'),
  },

  // ── Settings ─────────────────────────────────────────────────────────────

  settings: {
    get: () => request('/settings'),
    update: (data) =>
      request('/settings', { method: 'PUT', body: JSON.stringify(data) }),
  },
};
