import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { productsApi, suppliersApi } from '../api/client';
import { StatusBadge, DaysBar, Spinner, Modal, ErrorBanner } from '../components/ui/SharedComponents';
import toast from 'react-hot-toast';

const INITIAL_FORM = {
  product_name: '', product_code: '', category: '', description: '',
  current_quantity: 0, unit: 'units', minimum_stock: 0,
  average_daily_usage: 0, alert_days: 7, critical_days: 3,
  emergency_reserve: 0, storage_location: '', primary_supplier_id: '',
};

export default function ProductsPage() {
  const [products, setProducts] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState(INITIAL_FORM);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const load = async () => {
    try {
      const [p, s] = await Promise.all([productsApi.list(), suppliersApi.list()]);
      setProducts(p.items || []);
      setSuppliers(s.items || []);
    } catch { toast.error('Failed to load products'); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault(); setError(''); setSaving(true);
    try {
      const payload = { ...form,
        primary_supplier_id: form.primary_supplier_id ? parseInt(form.primary_supplier_id) : null,
        current_quantity: parseFloat(form.current_quantity),
        minimum_stock: parseFloat(form.minimum_stock),
        average_daily_usage: parseFloat(form.average_daily_usage),
        emergency_reserve: parseFloat(form.emergency_reserve),
      };
      await productsApi.create(payload);
      toast.success('Product created!');
      setShowModal(false); setForm(INITIAL_FORM); await load();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create product');
    } finally { setSaving(false); }
  };

  if (loading) return <Spinner />;

  return (
    <div>
      <div className="page-header">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="page-title">Products</h1>
            <p className="page-subtitle">{products.length} products in inventory</p>
          </div>
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>
            + Add Product
          </button>
        </div>
      </div>

      <div className="page-body">
        <div className="table-wrapper">
          <table className="data-table">
            <thead><tr>
              <th>Product</th><th>Category</th><th>Stock</th>
              <th>Daily Use</th><th>Days Left</th><th>Status</th>
              <th>Supplier</th><th>Actions</th>
            </tr></thead>
            <tbody>
              {products.length === 0 ? (
                <tr><td colSpan={8} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                  No products yet. Add your first product.
                </td></tr>
              ) : products.map(p => (
                <tr key={p.id}>
                  <td>
                    <div style={{ fontWeight: 600 }}>{p.product_name}</div>
                    <div className="text-sm text-muted font-mono">{p.product_code}</div>
                  </td>
                  <td><span className="badge badge-draft">{p.category}</span></td>
                  <td>{p.current_quantity} {p.unit}</td>
                  <td>{p.average_daily_usage} {p.unit}/d</td>
                  <td><DaysBar days={p.days_remaining} alertDays={p.alert_days} criticalDays={p.critical_days} /></td>
                  <td><StatusBadge status={p.status} /></td>
                  <td className="text-muted text-sm">{p.primary_supplier_id ? `ID #${p.primary_supplier_id}` : '—'}</td>
                  <td>
                    <button className="btn btn-ghost btn-sm" onClick={() => navigate(`/products/${p.id}`)}>
                      View →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <Modal open={showModal} onClose={() => setShowModal(false)} title="Add New Product"
        footer={<>
          <button className="btn btn-ghost" onClick={() => setShowModal(false)}>Cancel</button>
          <button className="btn btn-primary" onClick={handleCreate} disabled={saving}>
            {saving ? 'Creating...' : 'Create Product'}
          </button>
        </>}>
        <ErrorBanner message={error} />
        <div className="form-grid">
          <div className="form-group">
            <label className="form-label">Product Name *</label>
            <input className="form-input" value={form.product_name}
              onChange={e => setForm(f => ({ ...f, product_name: e.target.value }))} required />
          </div>
          <div className="form-group">
            <label className="form-label">Product Code *</label>
            <input className="form-input" value={form.product_code}
              onChange={e => setForm(f => ({ ...f, product_code: e.target.value }))} required />
          </div>
        </div>
        <div className="form-grid">
          <div className="form-group">
            <label className="form-label">Category *</label>
            <input className="form-input" value={form.category}
              onChange={e => setForm(f => ({ ...f, category: e.target.value }))} required />
          </div>
          <div className="form-group">
            <label className="form-label">Unit</label>
            <input className="form-input" value={form.unit}
              onChange={e => setForm(f => ({ ...f, unit: e.target.value }))} />
          </div>
        </div>
        <div className="form-grid-3">
          <div className="form-group">
            <label className="form-label">Current Qty</label>
            <input className="form-input" type="number" min="0" value={form.current_quantity}
              onChange={e => setForm(f => ({ ...f, current_quantity: e.target.value }))} />
          </div>
          <div className="form-group">
            <label className="form-label">Avg Daily Usage</label>
            <input className="form-input" type="number" min="0" step="0.1" value={form.average_daily_usage}
              onChange={e => setForm(f => ({ ...f, average_daily_usage: e.target.value }))} />
          </div>
          <div className="form-group">
            <label className="form-label">Min Stock</label>
            <input className="form-input" type="number" min="0" value={form.minimum_stock}
              onChange={e => setForm(f => ({ ...f, minimum_stock: e.target.value }))} />
          </div>
        </div>
        <div className="form-grid-3">
          <div className="form-group">
            <label className="form-label">Alert Days</label>
            <input className="form-input" type="number" min="1" value={form.alert_days}
              onChange={e => setForm(f => ({ ...f, alert_days: parseInt(e.target.value) }))} />
          </div>
          <div className="form-group">
            <label className="form-label">Critical Days</label>
            <input className="form-input" type="number" min="1" value={form.critical_days}
              onChange={e => setForm(f => ({ ...f, critical_days: parseInt(e.target.value) }))} />
          </div>
          <div className="form-group">
            <label className="form-label">Emergency Reserve</label>
            <input className="form-input" type="number" min="0" value={form.emergency_reserve}
              onChange={e => setForm(f => ({ ...f, emergency_reserve: e.target.value }))} />
          </div>
        </div>
        <div className="form-grid">
          <div className="form-group">
            <label className="form-label">Primary Supplier</label>
            <select className="form-select" value={form.primary_supplier_id}
              onChange={e => setForm(f => ({ ...f, primary_supplier_id: e.target.value }))}>
              <option value="">— None —</option>
              {suppliers.map(s => (
                <option key={s.id} value={s.id}>{s.supplier_name}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Storage Location</label>
            <input className="form-input" value={form.storage_location}
              onChange={e => setForm(f => ({ ...f, storage_location: e.target.value }))} />
          </div>
        </div>
        <div className="form-group">
          <label className="form-label">Description</label>
          <textarea className="form-textarea" rows={3} value={form.description}
            onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
        </div>
      </Modal>
    </div>
  );
}
