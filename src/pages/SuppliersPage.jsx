import React, { useEffect, useState } from 'react';
import { suppliersApi } from '../api/client';
import { Spinner, Modal, ErrorBanner, StatusBadge } from '../components/ui/SharedComponents';
import toast from 'react-hot-toast';

const INITIAL_FORM = {
  supplier_name: '', company_name: '', email: '', phone: '',
  address: '', preferred_contact_method: 'email',
  average_delivery_days: 7, emergency_available: false,
};

export default function SuppliersPage() {
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState(INITIAL_FORM);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const load = async () => {
    try {
      const data = await suppliersApi.list();
      setSuppliers(data.items || []);
    } catch { toast.error('Failed to load suppliers'); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault(); setError(''); setSaving(true);
    try {
      await suppliersApi.create({ ...form, average_delivery_days: parseInt(form.average_delivery_days) });
      toast.success('Supplier created!');
      setShowModal(false); setForm(INITIAL_FORM); await load();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create supplier');
    } finally { setSaving(false); }
  };

  if (loading) return <Spinner />;

  return (
    <div>
      <div className="page-header">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="page-title">Suppliers</h1>
            <p className="page-subtitle">{suppliers.length} registered suppliers</p>
          </div>
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>
            + Add Supplier
          </button>
        </div>
      </div>

      <div className="page-body">
        <div className="table-wrapper">
          <table className="data-table">
            <thead><tr>
              <th>Supplier</th><th>Email</th><th>Phone</th>
              <th>Delivery Days</th><th>Emergency</th><th>Status</th>
            </tr></thead>
            <tbody>
              {suppliers.length === 0 ? (
                <tr><td colSpan={6} style={{ textAlign:'center',padding:40,color:'var(--text-muted)' }}>
                  No suppliers. Add your first supplier.
                </td></tr>
              ) : suppliers.map(s => (
                <tr key={s.id}>
                  <td>
                    <div style={{ fontWeight: 600 }}>{s.supplier_name}</div>
                    <div className="text-sm text-muted">{s.company_name}</div>
                  </td>
                  <td className="font-mono text-sm">{s.email}</td>
                  <td className="text-muted text-sm">{s.phone || '—'}</td>
                  <td style={{ textAlign: 'center' }}>{s.average_delivery_days}d</td>
                  <td style={{ textAlign: 'center' }}>{s.emergency_available ? '✅' : '—'}</td>
                  <td><StatusBadge status={s.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <Modal open={showModal} onClose={() => setShowModal(false)} title="Add New Supplier"
        footer={<>
          <button className="btn btn-ghost" onClick={() => setShowModal(false)}>Cancel</button>
          <button className="btn btn-primary" onClick={handleCreate} disabled={saving}>
            {saving ? 'Creating...' : 'Create Supplier'}
          </button>
        </>}>
        <ErrorBanner message={error} />
        <div className="form-grid">
          <div className="form-group">
            <label className="form-label">Supplier Name *</label>
            <input className="form-input" value={form.supplier_name}
              onChange={e => setForm(f => ({ ...f, supplier_name: e.target.value }))} required />
          </div>
          <div className="form-group">
            <label className="form-label">Company Name *</label>
            <input className="form-input" value={form.company_name}
              onChange={e => setForm(f => ({ ...f, company_name: e.target.value }))} required />
          </div>
        </div>
        <div className="form-grid">
          <div className="form-group">
            <label className="form-label">Email *</label>
            <input className="form-input" type="email" value={form.email}
              onChange={e => setForm(f => ({ ...f, email: e.target.value }))} required />
          </div>
          <div className="form-group">
            <label className="form-label">Phone</label>
            <input className="form-input" value={form.phone}
              onChange={e => setForm(f => ({ ...f, phone: e.target.value }))} />
          </div>
        </div>
        <div className="form-grid">
          <div className="form-group">
            <label className="form-label">Avg Delivery Days</label>
            <input className="form-input" type="number" min="1" value={form.average_delivery_days}
              onChange={e => setForm(f => ({ ...f, average_delivery_days: e.target.value }))} />
          </div>
          <div className="form-group">
            <label className="form-label">Emergency Available</label>
            <select className="form-select" value={form.emergency_available}
              onChange={e => setForm(f => ({ ...f, emergency_available: e.target.value === 'true' }))}>
              <option value="false">No</option>
              <option value="true">Yes</option>
            </select>
          </div>
        </div>
        <div className="form-group">
          <label className="form-label">Address</label>
          <textarea className="form-textarea" rows={2} value={form.address}
            onChange={e => setForm(f => ({ ...f, address: e.target.value }))} />
        </div>
      </Modal>
    </div>
  );
}
