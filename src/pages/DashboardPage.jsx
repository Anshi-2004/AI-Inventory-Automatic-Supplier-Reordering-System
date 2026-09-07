import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { dashboardApi, inventoryApi } from '../api/client';
import { StatusBadge, DaysBar, Spinner } from '../components/ui/SharedComponents';
import toast from 'react-hot-toast';

const STAT_CARDS = [
  { key: 'total_products',   label: 'Total Products',   icon: '📦', color: 'var(--accent-blue)' },
  { key: 'total_suppliers',  label: 'Suppliers',        icon: '🏭', color: 'var(--accent-teal)' },
  { key: 'low_stock_count',  label: 'Low Stock',        icon: '⚠️', color: 'var(--accent-amber)' },
  { key: 'critical_count',   label: 'Critical',         icon: '🔴', color: 'var(--status-critical)' },
  { key: 'emergency_count',  label: 'Emergency',        icon: '🚨', color: 'var(--status-emergency)' },
  { key: 'expiring_soon_count', label: 'Expiring Soon', icon: '⏰', color: 'var(--status-expiring)' },
  { key: 'pending_orders',   label: 'Pending Orders',   icon: '📋', color: 'var(--accent-violet)' },
  { key: 'emails_sent',      label: 'Emails Sent',      icon: '✅', color: 'var(--accent-emerald)' },
];

export default function DashboardPage() {
  const [summary, setSummary] = useState(null);
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);
  const navigate = useNavigate();

  const load = async () => {
    try {
      const [sum, inv] = await Promise.all([
        dashboardApi.getSummary(),
        inventoryApi.getStatus(),
      ]);
      setSummary(sum);
      setInventory(inv.slice(0, 10)); // Top 10 for dashboard
    } catch { toast.error('Failed to load dashboard'); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleManualCheck = async () => {
    setChecking(true);
    try {
      const result = await inventoryApi.runCheck();
      toast.success(`✅ Check complete: ${result.summary?.alerts_created || 0} alerts, ${result.summary?.orders_created || 0} orders`);
      await load();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Inventory check failed');
    } finally { setChecking(false); }
  };

  if (loading) return <Spinner />;

  return (
    <div>
      <div className="page-header">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="page-title">Dashboard</h1>
            <p className="page-subtitle">Real-time inventory overview</p>
          </div>
          <button
            className="btn btn-primary"
            onClick={handleManualCheck}
            disabled={checking}
          >
            {checking ? '⏳ Checking...' : '🔄 Run Inventory Check'}
          </button>
        </div>
      </div>

      <div className="page-body">
        {/* ── Stat Cards ── */}
        <div className="stat-grid">
          {STAT_CARDS.map(({ key, label, icon, color }) => (
            <div
              key={key}
              className="stat-card"
              style={{ '--accent-color': color }}
            >
              <div className="stat-label">{label}</div>
              <div className="stat-value">{summary?.[key] ?? '—'}</div>
              <div className="stat-icon" style={{ fontSize: 36 }}>{icon}</div>
            </div>
          ))}
        </div>

        {/* ── Inventory Status Table ── */}
        <div className="flex items-center justify-between mb-4">
          <h2 style={{ fontSize: 16, fontWeight: 700 }}>Inventory Status</h2>
          <button className="btn btn-ghost btn-sm" onClick={() => navigate('/products')}>
            View All →
          </button>
        </div>
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Category</th>
                <th>Stock</th>
                <th>Daily Use</th>
                <th>Days Left</th>
                <th>Status</th>
                <th>Supplier</th>
              </tr>
            </thead>
            <tbody>
              {inventory.length === 0 ? (
                <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 32 }}>
                  No inventory data. <a href="#" onClick={handleManualCheck}>Run a check</a>.
                </td></tr>
              ) : inventory.map(item => (
                <tr
                  key={item.product_id}
                  onClick={() => navigate(`/products/${item.product_id}`)}
                  style={{ cursor: 'pointer' }}
                >
                  <td>
                    <div style={{ fontWeight: 600 }}>{item.product_name}</div>
                    <div className="text-sm text-muted">{item.product_code}</div>
                  </td>
                  <td><span className="badge badge-draft">{item.category}</span></td>
                  <td>{item.current_quantity} {item.unit}</td>
                  <td>{item.average_daily_usage} {item.unit}/d</td>
                  <td>
                    <DaysBar
                      days={item.days_remaining}
                      alertDays={item.alert_days}
                      criticalDays={item.critical_days}
                    />
                  </td>
                  <td><StatusBadge status={item.status} /></td>
                  <td className="text-muted">{item.primary_supplier_name || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
