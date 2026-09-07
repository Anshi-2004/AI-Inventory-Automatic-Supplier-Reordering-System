import React, { useEffect, useState } from 'react';
import { suppliersApi, productsApi } from '../api/client';
import { Spinner, ErrorBanner } from '../components/ui/SharedComponents';
import toast from 'react-hot-toast';

export default function SettingsPage() {
  const [suppliers, setSuppliers] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  // Link Form
  const [linkForm, setLinkForm] = useState({
    supplier_id: '', product_id: '', unit_price: '', minimum_order_quantity: '1',
    delivery_days: '5', priority: '1', emergency_available: 'false'
  });
  const [savingLink, setSavingLink] = useState(false);
  const [linkError, setLinkError] = useState('');

  const load = async () => {
    try {
      const [s, p] = await Promise.all([suppliersApi.list(), productsApi.list()]);
      setSuppliers(s.items || []);
      setProducts(p.items || []);
    } catch {
      toast.error('Failed to load settings data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleLinkSubmit = async (e) => {
    e.preventDefault();
    setLinkError('');
    setSavingLink(true);
    try {
      await suppliersApi.linkProduct(parseInt(linkForm.supplier_id), {
        product_id: parseInt(linkForm.product_id),
        unit_price: linkForm.unit_price ? parseFloat(linkForm.unit_price) : null,
        minimum_order_quantity: parseFloat(linkForm.minimum_order_quantity),
        delivery_days: parseInt(linkForm.delivery_days),
        priority: parseInt(linkForm.priority),
        emergency_available: linkForm.emergency_available === 'true',
      });
      toast.success('Product linked to supplier successfully!');
      setLinkForm({
        supplier_id: '', product_id: '', unit_price: '', minimum_order_quantity: '1',
        delivery_days: '5', priority: '1', emergency_available: 'false'
      });
    } catch (err) {
      setLinkError(err.response?.data?.detail || 'Failed to link product to supplier');
    } finally {
      setSavingLink(false);
    }
  };

  if (loading) return <Spinner />;

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">System Settings</h1>
        <p className="page-subtitle">Configure supply relationships and general thresholds</p>
      </div>

      <div className="page-body" style={{ maxWidth: 720 }}>
        {/* Supplier Product Association Form */}
        <div className="card mb-6">
          <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 12 }}>Link Product to Supplier</h3>
          <p className="text-secondary mb-4" style={{ fontSize: 13 }}>
            Define supplier prices, lead times, priority levels, and emergency capabilities for specific inventory products.
          </p>

          <ErrorBanner message={linkError} />

          <form onSubmit={handleLinkSubmit}>
            <div className="form-grid">
              <div className="form-group">
                <label className="form-label">Select Supplier *</label>
                <select
                  className="form-select"
                  value={linkForm.supplier_id}
                  onChange={e => setLinkForm(f => ({ ...f, supplier_id: e.target.value }))}
                  required
                >
                  <option value="">— Select Supplier —</option>
                  {suppliers.map(s => (
                    <option key={s.id} value={s.id}>{s.supplier_name}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Select Product *</label>
                <select
                  className="form-select"
                  value={linkForm.product_id}
                  onChange={e => setLinkForm(f => ({ ...f, product_id: e.target.value }))}
                  required
                >
                  <option value="">— Select Product —</option>
                  {products.map(p => (
                    <option key={p.id} value={p.id}>{p.product_name} ({p.product_code})</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-grid-3">
              <div className="form-group">
                <label className="form-label">Unit Price ($)</label>
                <input
                  className="form-input"
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="e.g. 2.50"
                  value={linkForm.unit_price}
                  onChange={e => setLinkForm(f => ({ ...f, unit_price: e.target.value }))}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Min Order Qty (MOQ)</label>
                <input
                  className="form-input"
                  type="number"
                  min="1"
                  value={linkForm.minimum_order_quantity}
                  onChange={e => setLinkForm(f => ({ ...f, minimum_order_quantity: e.target.value }))}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Delivery Days</label>
                <input
                  className="form-input"
                  type="number"
                  min="1"
                  value={linkForm.delivery_days}
                  onChange={e => setLinkForm(f => ({ ...f, delivery_days: e.target.value }))}
                  required
                />
              </div>
            </div>

            <div className="form-grid">
              <div className="form-group">
                <label className="form-label">Supplier Priority (1=Highest, 5=Lowest)</label>
                <input
                  className="form-input"
                  type="number"
                  min="1"
                  max="5"
                  value={linkForm.priority}
                  onChange={e => setLinkForm(f => ({ ...f, priority: e.target.value }))}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Emergency Supply Support</label>
                <select
                  className="form-select"
                  value={linkForm.emergency_available}
                  onChange={e => setLinkForm(f => ({ ...f, emergency_available: e.target.value }))}
                >
                  <option value="false">No (Standard lead time only)</option>
                  <option value="true">Yes (Can deliver quickly in emergency)</option>
                </select>
              </div>
            </div>

            <button className="btn btn-primary mt-2" type="submit" disabled={savingLink}>
              {savingLink ? 'Linking relationship...' : '🔗 Create Supply Relationship'}
            </button>
          </form>
        </div>

        {/* Informative credentials status section */}
        <div className="card">
          <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 8 }}>API & Integration Credentials</h3>
          <p className="text-secondary mb-4" style={{ fontSize: 13 }}>
            To send emails and generate messages with OpenRouter, make sure the environment variables are active on your backend server.
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div style={{ background: 'rgba(255,255,255,0.02)', padding: 12, borderRadius: 8, border: '1px solid var(--border)' }}>
              <div style={{ fontWeight: 600 }}>OpenRouter Integration</div>
              <p className="text-muted text-sm mt-1">Status: Active</p>
            </div>
            <div style={{ background: 'rgba(255,255,255,0.02)', padding: 12, borderRadius: 8, border: '1px solid var(--border)' }}>
              <div style={{ fontWeight: 600 }}>Gmail API Consent</div>
              <p className="text-muted text-sm mt-1">Status: Setup required via scripts/gmail_auth.py</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
