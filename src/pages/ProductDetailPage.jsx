import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { productsApi, inventoryApi, suppliersApi } from '../api/client';
import { StatusBadge, DaysBar, Spinner, Modal, ErrorBanner } from '../components/ui/SharedComponents';
import toast from 'react-hot-toast';

export default function ProductDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [product, setProduct] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modals
  const [showTxnModal, setShowTxnModal] = useState(false);
  const [showBatchModal, setShowBatchModal] = useState(false);

  // Form states
  const [txnForm, setTxnForm] = useState({
    transaction_type: 'IN', quantity: '', reason: '', reference_id: ''
  });
  const [batchForm, setBatchForm] = useState({
    batch_number: '', quantity: '', expiry_date: ''
  });

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const loadData = async () => {
    try {
      const [p, h] = await Promise.all([
        productsApi.get(id),
        inventoryApi.getHistory(id)
      ]);
      setProduct(p);
      setHistory(h);
    } catch {
      toast.error('Failed to load product details');
      navigate('/products');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [id]);

  const handleTxnSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSaving(true);
    try {
      await inventoryApi.createTransaction({
        product_id: parseInt(id),
        transaction_type: txnForm.transaction_type,
        quantity: parseFloat(txnForm.quantity),
        reason: txnForm.reason,
        reference_id: txnForm.reference_id || null,
      });
      toast.success('Stock transaction recorded!');
      setShowTxnModal(false);
      setTxnForm({ transaction_type: 'IN', quantity: '', reason: '', reference_id: '' });
      await loadData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to record transaction');
    } finally {
      setSaving(false);
    }
  };

  const handleBatchSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSaving(true);
    try {
      await inventoryApi.createBatch({
        product_id: parseInt(id),
        batch_number: batchForm.batch_number,
        quantity: parseFloat(batchForm.quantity),
        expiry_date: batchForm.expiry_date || null,
        received_date: new Date().toISOString().split('T')[0],
      });
      toast.success('Batch registered successfully!');
      setShowBatchModal(false);
      setBatchForm({ batch_number: '', quantity: '', expiry_date: '' });
      await loadData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create batch');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteProduct = async () => {
    if (!window.confirm('Are you sure you want to delete this product?')) return;
    try {
      await productsApi.delete(id);
      toast.success('Product deleted');
      navigate('/products');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete product');
    }
  };

  if (loading) return <Spinner />;
  if (!product) return <div>Product not found</div>;

  return (
    <div>
      <div className="page-header">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="page-title">{product.product_name}</h1>
            <p className="page-subtitle">Product Code: <span className="font-mono">{product.product_code}</span></p>
          </div>
          <div className="flex gap-2">
            <button className="btn btn-ghost" onClick={() => navigate('/products')}>
              Back to Products
            </button>
            <button className="btn btn-primary" onClick={() => setShowTxnModal(true)}>
              Record Stock Move
            </button>
            <button className="btn btn-violet" onClick={() => setShowBatchModal(true)}>
              Register Batch
            </button>
            <button className="btn btn-danger" onClick={handleDeleteProduct}>
              Delete
            </button>
          </div>
        </div>
      </div>

      <div className="page-body">
        <div className="form-grid-3 mb-6">
          <div className="card">
            <h3 style={{ fontSize: 13, textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Stock Status</h3>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 12 }}>
              <div style={{ fontSize: 24, fontWeight: 700 }}>
                {product.current_quantity} <span style={{ fontSize: 14, fontWeight: 400, color: 'var(--text-secondary)' }}>{product.unit}</span>
              </div>
              <StatusBadge status={product.status} />
            </div>
            <div className="mt-4">
              <DaysBar days={product.days_remaining} alertDays={product.alert_days} criticalDays={product.critical_days} />
              <div className="text-sm text-muted mt-2">Expected stock duration</div>
            </div>
          </div>

          <div className="card">
            <h3 style={{ fontSize: 13, textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Usage & Limits</h3>
            <div className="mt-2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px 16px' }}>
              <div>
                <span className="text-muted text-sm">Daily Usage:</span>
                <div style={{ fontWeight: 600 }}>{product.average_daily_usage} {product.unit}/d</div>
              </div>
              <div>
                <span className="text-muted text-sm">Min Stock:</span>
                <div style={{ fontWeight: 600 }}>{product.minimum_stock} {product.unit}</div>
              </div>
              <div>
                <span className="text-muted text-sm">Alert Threshold:</span>
                <div style={{ fontWeight: 600 }}>{product.alert_days} days</div>
              </div>
              <div>
                <span className="text-muted text-sm">Critical Threshold:</span>
                <div style={{ fontWeight: 600 }}>{product.critical_days} days</div>
              </div>
              <div>
                <span className="text-muted text-sm">Emergency Reserve:</span>
                <div style={{ fontWeight: 600 }}>{product.emergency_reserve} {product.unit}</div>
              </div>
              <div>
                <span className="text-muted text-sm">Expiry Date:</span>
                <div style={{ fontWeight: 600 }}>{product.expiry_date || 'N/A'}</div>
              </div>
            </div>
          </div>

          <div className="card">
            <h3 style={{ fontSize: 13, textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Procurement</h3>
            <div className="mt-2">
              <span className="text-muted text-sm">Primary Supplier:</span>
              <div style={{ fontWeight: 600, fontSize: 15, color: 'var(--accent-blue)', cursor: 'pointer' }}
                   onClick={() => product.primary_supplier_id && navigate(`/suppliers`)}>
                {product.primary_supplier ? product.primary_supplier.supplier_name : 'No Primary Supplier'}
              </div>
              {product.primary_supplier && (
                <div className="text-sm text-muted mt-2">
                  <div>Company: {product.primary_supplier.company_name}</div>
                  <div>Email: {product.primary_supplier.email}</div>
                  <div>Delivery Timeline: {product.primary_supplier.average_delivery_days} days</div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Description section */}
        {product.description && (
          <div className="card mb-6">
            <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 8 }}>Description</h3>
            <p className="text-secondary">{product.description}</p>
          </div>
        )}

        {/* Transaction History Table */}
        <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 12 }}>Stock History</h2>
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Type</th>
                <th>Quantity</th>
                <th>Stock After</th>
                <th>Reason / Ref</th>
                <th>Recorded By</th>
              </tr>
            </thead>
            <tbody>
              {history.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: 24, color: 'var(--text-muted)' }}>
                    No stock movements recorded yet.
                  </td>
                </tr>
              ) : (
                history.map(txn => (
                  <tr key={txn.id}>
                    <td className="text-sm">{new Date(txn.transaction_date).toLocaleString()}</td>
                    <td>
                      <span className={`badge ${
                        txn.transaction_type === 'IN' || txn.transaction_type === 'RETURN' ? 'badge-active' :
                        txn.transaction_type === 'OUT' || txn.transaction_type === 'DAMAGE' || txn.transaction_type === 'EXPIRED' ? 'badge-critical' :
                        'badge-draft'
                      }`}>
                        {txn.transaction_type}
                      </span>
                    </td>
                    <td style={{ fontWeight: 600 }}>
                      {txn.quantity > 0 ? `+${txn.quantity}` : txn.quantity}
                    </td>
                    <td>{txn.stock_after}</td>
                    <td>
                      <div>{txn.reason || '—'}</div>
                      {txn.reference_id && (
                        <div className="text-sm text-muted font-mono">Ref: {txn.reference_id}</div>
                      )}
                    </td>
                    <td className="text-muted text-sm">User #{txn.created_by || 'system'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal for Recording Stock Move */}
      <Modal open={showTxnModal} onClose={() => setShowTxnModal(false)} title="Record Stock Movement"
        footer={<>
          <button className="btn btn-ghost" onClick={() => setShowTxnModal(false)}>Cancel</button>
          <button className="btn btn-primary" onClick={handleTxnSubmit} disabled={saving}>
            {saving ? 'Saving...' : 'Record Transaction'}
          </button>
        </>}>
        <ErrorBanner message={error} />
        <div className="form-grid">
          <div className="form-group">
            <label className="form-label">Transaction Type</label>
            <select className="form-select" value={txnForm.transaction_type}
              onChange={e => setTxnForm(f => ({ ...f, transaction_type: e.target.value }))}>
              <option value="IN">IN (Stock Intake / Purchase)</option>
              <option value="OUT">OUT (Stock Consumption / FEFO)</option>
              <option value="ADJUSTMENT">ADJUSTMENT (Set absolute count)</option>
              <option value="DAMAGE">DAMAGE (Write-off damaged)</option>
              <option value="EXPIRED">EXPIRED (Write-off expired)</option>
              <option value="RETURN">RETURN (Customer return)</option>
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Quantity</label>
            <input className="form-input" type="number" min="0.01" step="0.01" value={txnForm.quantity}
              onChange={e => setTxnForm(f => ({ ...f, quantity: e.target.value }))} required />
          </div>
        </div>
        <div className="form-group">
          <label className="form-label">Reference ID (e.g. Invoice #, PO #)</label>
          <input className="form-input" placeholder="e.g. PO-12345" value={txnForm.reference_id}
            onChange={e => setTxnForm(f => ({ ...f, reference_id: e.target.value }))} />
        </div>
        <div className="form-group">
          <label className="form-label">Reason / Notes</label>
          <input className="form-input" placeholder="e.g. Monthly replenishment, laboratory usage" value={txnForm.reason}
            onChange={e => setTxnForm(f => ({ ...f, reason: e.target.value }))} />
        </div>
      </Modal>

      {/* Modal for Registering Batch */}
      <Modal open={showBatchModal} onClose={() => setShowBatchModal(false)} title="Register Product Batch (FEFO)"
        footer={<>
          <button className="btn btn-ghost" onClick={() => setShowBatchModal(false)}>Cancel</button>
          <button className="btn btn-primary" onClick={handleBatchSubmit} disabled={saving}>
            {saving ? 'Registering...' : 'Register Batch'}
          </button>
        </>}>
        <ErrorBanner message={error} />
        <div className="form-group">
          <label className="form-label">Batch Number / Lot Number *</label>
          <input className="form-input" placeholder="e.g. LOT-2026-A1" value={batchForm.batch_number}
            onChange={e => setBatchForm(f => ({ ...f, batch_number: e.target.value }))} required />
        </div>
        <div className="form-grid">
          <div className="form-group">
            <label className="form-label">Batch Quantity *</label>
            <input className="form-input" type="number" min="0.01" step="0.01" value={batchForm.quantity}
              onChange={e => setBatchForm(f => ({ ...f, quantity: e.target.value }))} required />
          </div>
          <div className="form-group">
            <label className="form-label">Expiry Date *</label>
            <input className="form-input" type="date" value={batchForm.expiry_date}
              onChange={e => setBatchForm(f => ({ ...f, expiry_date: e.target.value }))} required />
          </div>
        </div>
      </Modal>
    </div>
  );
}
