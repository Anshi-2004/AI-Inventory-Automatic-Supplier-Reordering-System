import React, { useEffect, useState } from 'react';
import { alertsApi } from '../api/client';
import { Spinner, StatusBadge } from '../components/ui/SharedComponents';
import toast from 'react-hot-toast';

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterActive, setFilterActive] = useState(true);

  const load = async () => {
    try {
      const data = filterActive
        ? await alertsApi.active()
        : await alertsApi.list();
      // If active only, data is an array directly. If list, it's an object with items/total.
      setAlerts(Array.isArray(data) ? data : (data.items || []));
    } catch {
      toast.error('Failed to load alerts');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [filterActive]);

  const handleResolve = async (id) => {
    try {
      await alertsApi.resolve(id);
      toast.success('Alert resolved!');
      await load();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to resolve alert');
    }
  };

  const handleDismiss = async (id) => {
    try {
      await alertsApi.dismiss(id);
      toast.success('Alert dismissed');
      await load();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to dismiss alert');
    }
  };

  if (loading) return <Spinner />;

  return (
    <div>
      <div className="page-header">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="page-title">Procurement & Expiry Alerts</h1>
            <p className="page-subtitle">Immediate notifications regarding low stock, safety breaches, and batch expiry</p>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button
              className={`btn btn-sm ${filterActive ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => setFilterActive(true)}
            >
              Active Only
            </button>
            <button
              className={`btn btn-sm ${!filterActive ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => setFilterActive(false)}
            >
              All History
            </button>
          </div>
        </div>
      </div>

      <div className="page-body">
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Alert Info</th>
                <th>Type</th>
                <th>Current Stock</th>
                <th>Severity</th>
                <th>Created At</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {alerts.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                    No alerts found.
                  </td>
                </tr>
              ) : (
                alerts.map(alert => (
                  <tr key={alert.id}>
                    <td style={{ maxWidth: 300 }}>
                      <div style={{ fontWeight: 600, fontSize: 13.5 }}>{alert.message}</div>
                      {alert.product_name && (
                        <div className="text-sm text-muted">Product: {alert.product_name}</div>
                      )}
                    </td>
                    <td>
                      <span className="badge badge-draft">
                        {alert.alert_type?.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td>
                      {alert.current_stock}
                    </td>
                    <td>
                      <StatusBadge status={alert.severity} />
                    </td>
                    <td className="text-sm text-secondary">
                      {new Date(alert.created_at).toLocaleString()}
                    </td>
                    <td>
                      <StatusBadge status={alert.status} />
                    </td>
                    <td>
                      {alert.status === 'ACTIVE' ? (
                        <div className="flex gap-2">
                          <button className="btn btn-success btn-sm" onClick={() => handleResolve(alert.id)}>
                            Resolve
                          </button>
                          <button className="btn btn-ghost btn-sm" onClick={() => handleDismiss(alert.id)}>
                            Dismiss
                          </button>
                        </div>
                      ) : (
                        <span className="text-muted text-sm">
                          Resolved {alert.resolved_at ? new Date(alert.resolved_at).toLocaleDateString() : ''}
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
