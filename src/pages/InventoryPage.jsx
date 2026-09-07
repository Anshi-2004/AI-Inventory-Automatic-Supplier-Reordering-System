import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { inventoryApi } from '../api/client';
import { Spinner, StatusBadge, DaysBar } from '../components/ui/SharedComponents';
import toast from 'react-hot-toast';

export default function InventoryPage() {
  const [items, setItems] = useState([]);
  const [filteredItems, setFilteredItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [search, setSearch] = useState('');
  const navigate = useNavigate();

  const load = async () => {
    try {
      const data = await inventoryApi.getStatus();
      setItems(data);
      setFilteredItems(data);
    } catch {
      toast.error('Failed to load inventory status');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    let result = items;

    if (filterStatus !== 'ALL') {
      result = result.filter(item => item.status === filterStatus);
    }

    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(item =>
        item.product_name.toLowerCase().includes(q) ||
        item.product_code.toLowerCase().includes(q) ||
        item.category.toLowerCase().includes(q)
      );
    }

    setFilteredItems(result);
  }, [filterStatus, search, items]);

  if (loading) return <Spinner />;

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Inventory Control</h1>
        <p className="page-subtitle">Manage stock levels, batch dates, and FEFO expiry rules</p>
      </div>

      <div className="page-body">
        {/* Filter Toolbar */}
        <div className="card mb-6" style={{ padding: '16px 20px' }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', gap: 8, overflowX: 'auto', paddingBottom: 4 }}>
              {['ALL', 'ACTIVE', 'LOW_STOCK', 'CRITICAL', 'OUT_OF_STOCK', 'EXPIRING_SOON', 'EXPIRED'].map(status => (
                <button
                  key={status}
                  className={`btn btn-sm ${filterStatus === status ? 'btn-primary' : 'btn-ghost'}`}
                  onClick={() => setFilterStatus(status)}
                >
                  {status.replace(/_/g, ' ')}
                </button>
              ))}
            </div>
            <div style={{ width: '100%', maxWidth: 280 }}>
              <input
                className="form-input"
                placeholder="🔍 Search name, code, category..."
                value={search}
                onChange={e => setSearch(e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Inventory Status Table */}
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Category</th>
                <th>Current Stock</th>
                <th>Daily Usage</th>
                <th>Days Remaining</th>
                <th>Status</th>
                <th>Primary Supplier</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                    No products match the selected filters.
                  </td>
                </tr>
              ) : (
                filteredItems.map(item => (
                  <tr
                    key={item.product_id}
                    onClick={() => navigate(`/products/${item.product_id}`)}
                    style={{ cursor: 'pointer' }}
                  >
                    <td>
                      <div style={{ fontWeight: 600 }}>{item.product_name}</div>
                      <div className="text-sm text-muted font-mono">{item.product_code}</div>
                    </td>
                    <td>
                      <span className="badge badge-draft">{item.category}</span>
                    </td>
                    <td style={{ fontWeight: 600 }}>
                      {item.current_quantity} {item.unit}
                    </td>
                    <td>
                      {item.average_daily_usage} {item.unit}/day
                    </td>
                    <td>
                      <DaysBar
                        days={item.days_remaining}
                        alertDays={item.alert_days}
                        criticalDays={item.critical_days}
                      />
                    </td>
                    <td>
                      <StatusBadge status={item.status} />
                    </td>
                    <td className="text-muted text-sm">
                      {item.primary_supplier_name || '—'}
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
