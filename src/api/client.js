import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Handle 401 globally — redirect to login
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

export default api;

// ── Auth ─────────────────────────────────────────────────────
export const authApi = {
  login:    (data) => api.post('/auth/login', data).then(r => r.data),
  register: (data) => api.post('/auth/register', data).then(r => r.data),
  me:       ()     => api.get('/auth/me').then(r => r.data),
};

// ── Dashboard ─────────────────────────────────────────────────
export const dashboardApi = {
  getSummary: () => api.get('/dashboard/summary').then(r => r.data),
};

// ── Products ─────────────────────────────────────────────────
export const productsApi = {
  list:   (params) => api.get('/products', { params }).then(r => r.data),
  get:    (id)     => api.get(`/products/${id}`).then(r => r.data),
  create: (data)   => api.post('/products', data).then(r => r.data),
  update: (id, d)  => api.put(`/products/${id}`, d).then(r => r.data),
  delete: (id)     => api.delete(`/products/${id}`),
};

// ── Suppliers ─────────────────────────────────────────────────
export const suppliersApi = {
  list:        ()       => api.get('/suppliers').then(r => r.data),
  get:         (id)     => api.get(`/suppliers/${id}`).then(r => r.data),
  create:      (data)   => api.post('/suppliers', data).then(r => r.data),
  update:      (id, d)  => api.put(`/suppliers/${id}`, d).then(r => r.data),
  delete:      (id)     => api.delete(`/suppliers/${id}`),
  linkProduct: (id, d)  => api.post(`/suppliers/${id}/products`, d).then(r => r.data),
};

// ── Inventory ─────────────────────────────────────────────────
export const inventoryApi = {
  getStatus:      ()     => api.get('/inventory/status').then(r => r.data),
  getLowStock:    ()     => api.get('/inventory/low-stock').then(r => r.data),
  getCritical:    ()     => api.get('/inventory/critical').then(r => r.data),
  getHistory:     (id)   => api.get(`/inventory/history/${id}`).then(r => r.data),
  createTransaction: (d) => api.post('/inventory/transactions', d).then(r => r.data),
  createBatch:    (d)    => api.post('/inventory/batches', d).then(r => r.data),
  runCheck:       ()     => api.post('/inventory/check').then(r => r.data),
};

// ── Alerts ────────────────────────────────────────────────────
export const alertsApi = {
  list:    ()    => api.get('/alerts').then(r => r.data),
  active:  ()    => api.get('/alerts/active').then(r => r.data),
  resolve: (id)  => api.post(`/alerts/${id}/resolve`).then(r => r.data),
  dismiss: (id)  => api.post(`/alerts/${id}/dismiss`).then(r => r.data),
};

// ── Purchase Orders ────────────────────────────────────────────
export const ordersApi = {
  list:    ()        => api.get('/orders').then(r => r.data),
  get:     (id)      => api.get(`/orders/${id}`).then(r => r.data),
  create:  (data)    => api.post('/orders', data).then(r => r.data),
  approve: (id)      => api.post(`/orders/${id}/approve`).then(r => r.data),
  cancel:  (id)      => api.post(`/orders/${id}/cancel`).then(r => r.data),
  receive: (id, d)   => api.post(`/orders/${id}/receive`, d).then(r => r.data),
};

// ── AI Email ──────────────────────────────────────────────────
export const aiApi = {
  generateEmail:   (d) => api.post('/ai/generate-email', d).then(r => r.data),
  regenerateEmail: (d) => api.post('/ai/regenerate-email', d).then(r => r.data),
};

// ── Email Logs ────────────────────────────────────────────────
export const emailApi = {
  logs:      ()        => api.get('/email/logs').then(r => r.data),
  getLog:    (id)      => api.get(`/email/logs/${id}`).then(r => r.data),
  approve:   (id, d)   => api.post(`/email/logs/${id}/approve`, d).then(r => r.data),
  send:      (id)      => api.post(`/email/send/${id}`).then(r => r.data),
};
