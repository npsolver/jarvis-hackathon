const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

class ApiError extends Error {
  constructor(message, status, body) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

function getToken() {
  return localStorage.getItem('token');
}

async function request(path, { method = 'GET', body, token } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  const authToken = token ?? getToken();
  if (authToken) headers.Authorization = `Token ${authToken}`;

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  let data = null;
  const text = await res.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!res.ok) {
    const message = (data && (data.detail || data.reasons?.join?.('; '))) || `Request failed (${res.status})`;
    throw new ApiError(message, res.status, data);
  }
  return data;
}

export const api = {
  login: (username, password) => request('/auth/login/', { method: 'POST', body: { username, password } }),
  logout: () => request('/auth/logout/', { method: 'POST' }),
  me: () => request('/auth/me/'),

  listAccounts: () => request('/accounts/'),
  getAccount: (accountId) => request(`/accounts/${accountId}/`),

  listTransactions: () => request('/transactions/'),
  createTransaction: (payload) => request('/transactions/', { method: 'POST', body: payload }),

  listReviews: (status) => request(`/reviews/${status ? `?status=${status}` : ''}`),
  addReview: (id, overrides, resolvedBy) =>
    request(`/reviews/${id}/add/`, { method: 'POST', body: { overrides, resolved_by: resolvedBy } }),
  removeReview: (id, resolvedBy) =>
    request(`/reviews/${id}/remove/`, { method: 'POST', body: { resolved_by: resolvedBy } }),
};

export { ApiError };
