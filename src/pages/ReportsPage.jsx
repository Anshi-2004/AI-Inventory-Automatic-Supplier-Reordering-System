import React, { useEffect, useState } from 'react';
import { inventoryApi } from '../api/client';
import { Spinner } from '../components/ui/SharedComponents';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';
import toast from 'react-hot-toast';

const COLORS = {
  ACTIVE:           '#10b981', // green
  LOW_STOCK:        '#f59e0b', // amber
  CRITICAL:         '#ef4444', // red
  OUT_OF_STOCK:     '#dc2626', // dark red
  EXPIRING_SOON:    '#f97316', // orange
  EXPIRED:          '#6b7280', // gray
  NO_CONSUMPTION_DATA: '#475569',
};

export default function ReportsPage() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const status = await inventoryApi.getStatus();
        setData(status);
      } catch {
        toast.error('Failed to load report metrics');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) return <Spinner />;

  // ── Transform Data for Pie Chart ──
  const statusCounts = {};
  data.forEach(item => {
    statusCounts[item.status] = (statusCounts[item.status] || 0) + 1;
  });

  const pieData = Object.entries(statusCounts).map(([status, count]) => ({
    name: status.replace(/_/g, ' '),
    value: count,
    color: COLORS[status] || '#ccc'
  }));

  // ── Transform Data for Bar Chart (Days Remaining) ──
  const barData = data
    .filter(item => item.days_remaining !== null)
    .map(item => ({
      name: item.product_name,
      days: item.days_remaining,
      status: item.status
    }))
    .slice(0, 15); // limit to top 15 for readable chart

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Analytics & Stock Reports</h1>
        <p className="page-subtitle">Visual summaries of expiry pipelines and reordering triggers</p>
      </div>

      <div className="page-body">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: 24, marginBottom: 24 }}>
          {/* Pie Chart: Status Distribution */}
          <div className="card">
            <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16 }}>Inventory Status Distribution</h3>
            <div style={{ width: '100%', height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ background: 'var(--bg-secondary)', borderColor: 'var(--border)' }}
                    itemStyle={{ color: 'var(--text-primary)' }}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Bar Chart: Days Remaining */}
          <div className="card">
            <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16 }}>Expected Stock Life (Days Remaining)</h3>
            <div style={{ width: '100%', height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={barData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="name" stroke="var(--text-muted)" tick={{ fontSize: 11 }} />
                  <YAxis label={{ value: 'Days', angle: -90, position: 'insideLeft', fill: 'var(--text-muted)' }} stroke="var(--text-muted)" />
                  <Tooltip
                    contentStyle={{ background: 'var(--bg-secondary)', borderColor: 'var(--border)' }}
                    itemStyle={{ color: 'var(--text-primary)' }}
                  />
                  <Bar dataKey="days" radius={[4, 4, 0, 0]}>
                    {barData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[entry.status] || 'var(--accent-blue)'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Category breakdown report table */}
        <div className="card">
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Stock Pipeline Summary</h3>
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Category</th>
                  <th>Quantity Available</th>
                  <th>Daily Consumption</th>
                  <th>Days Remaining</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {data.map(p => (
                  <tr key={p.product_id}>
                    <td style={{ fontWeight: 600 }}>{p.product_name}</td>
                    <td><span className="badge badge-draft">{p.category}</span></td>
                    <td style={{ fontWeight: 600 }}>{p.current_quantity} {p.unit}</td>
                    <td>{p.average_daily_usage} {p.unit}/day</td>
                    <td style={{ fontWeight: 700, color: COLORS[p.status] }}>
                      {p.days_remaining !== null ? `${p.days_remaining.toFixed(1)} days` : 'N/A'}
                    </td>
                    <td>
                      <span
                        className="badge"
                        style={{
                          background: `${COLORS[p.status]}20`,
                          color: COLORS[p.status]
                        }}
                      >
                        {p.status.replace(/_/g, ' ')}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
