import React, { useEffect, useState } from 'react';
import { ordersApi, aiApi } from '../api/client';
import { Spinner, StatusBadge, Modal, ErrorBanner } from '../components/ui/SharedComponents';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';

export default function PurchaseOrdersPage() {
  const { user, isAdmin } = useAuth();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  // Selected order details modal
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [showDetailModal, setShowDetailModal] = useState(false);

  // Stock receiving modal
  const [showReceiveModal, setShowReceiveModal] = useState(false);
  const [receiveQtys, setReceiveQtys] = useState({}); // item_id -> quantity

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const load = async () => {
    try {
      const data = await ordersApi.list();
      setOrders(data.items || []);
    } catch {
      toast.error('Failed to load purchase orders');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleViewDetails = async (orderId) => {
    try {
      const order = await ordersApi.get(orderId);
      setSelectedOrder(order);
      setShowDetailModal(true);
    } catch {
      toast.error('Failed to load order details');
    }
  };

  const handleApprove = async (orderId) => {
    try {
      await ordersApi.approve(orderId);
      toast.success('Purchase order approved!');
      await load();
      setShowDetailModal(false);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to approve purchase order');
    }
  };

  const handleCancel = async (orderId) => {
    if (!window.confirm('Are you sure you want to cancel this order?')) return;
    try {
      await ordersApi.cancel(orderId);
      toast.success('Purchase order cancelled');
      await load();
      setShowDetailModal(false);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to cancel purchase order');
    }
  };

  const handleOpenReceive = (order) => {
    const qtys = {};
    order.items.forEach(item => {
      qtys[item.id] = item.requested_quantity;
    });
    setReceiveQtys(qtys);
    setSelectedOrder(order);
    setShowReceiveModal(true);
  };

  const handleReceiveSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSaving(true);
    try {
      const payload = {
        items: Object.entries(receiveQtys).map(([id, qty]) => ({
          item_id: parseInt(id),
          received_quantity: parseFloat(qty)
        }))
      };
      await ordersApi.receive(selectedOrder.id, payload);
      toast.success('Stock received and inventory updated!');
      setShowReceiveModal(false);
      setShowDetailModal(false);
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to receive stock');
    } finally {
      setSaving(false);
    }
  };

  const handleGenerateEmail = async (orderId) => {
    toast.loading('Drafting email using AI...', { id: 'ai-email' });
    try {
      await aiApi.generateEmail({ purchase_order_id: orderId });
      toast.success('AI Email draft created! Go to Email Center to approve it.', { id: 'ai-email' });
      await load();
      setShowDetailModal(false);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to draft AI email', { id: 'ai-email' });
    }
  };

  if (loading) return <Spinner />;

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Purchase Orders</h1>
        <p className="page-subtitle">Track supplier reordering processes and stock arrivals</p>
      </div>

      <div className="page-body">
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Order ID</th>
                <th>Supplier</th>
                <th>Priority</th>
                <th>Required Date</th>
                <th>Items Count</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {orders.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                    No purchase orders found.
                  </td>
                </tr>
              ) : (
                orders.map(order => (
                  <tr key={order.id}>
                    <td className="font-mono" style={{ fontWeight: 600 }}>PO #{order.id}</td>
                    <td>{order.supplier_name}</td>
                    <td>
                      <StatusBadge status={order.priority} />
                    </td>
                    <td>{order.required_by_date ? new Date(order.required_by_date).toLocaleDateString() : '—'}</td>
                    <td>{order.total_items} items</td>
                    <td>
                      <StatusBadge status={order.status} />
                    </td>
                    <td>
                      <div className="flex gap-2">
                        <button className="btn btn-ghost btn-sm" onClick={() => handleViewDetails(order.id)}>
                          Details
                        </button>
                        {order.status === 'APPROVED' && (
                          <button className="btn btn-violet btn-sm" onClick={() => handleGenerateEmail(order.id)}>
                            Draft AI Email
                          </button>
                        )}
                        {['APPROVED', 'EMAIL_GENERATED', 'EMAIL_SENT', 'CONFIRMED', 'DISPATCHED'].includes(order.status) && (
                          <button className="btn btn-success btn-sm" onClick={() => handleOpenReceive(order)}>
                            Receive Stock
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Purchase Order Details Modal */}
      {selectedOrder && (
        <Modal open={showDetailModal} onClose={() => setShowDetailModal(false)} title={`Purchase Order PO #${selectedOrder.id}`}
          footer={
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', width: '100%' }}>
              <button className="btn btn-ghost" onClick={() => setShowDetailModal(false)}>Close</button>
              {selectedOrder.status === 'PENDING_APPROVAL' && isAdmin && (
                <button className="btn btn-success" onClick={() => handleApprove(selectedOrder.id)}>
                  Approve Order
                </button>
              )}
              {['PENDING_APPROVAL', 'APPROVED', 'EMAIL_GENERATED', 'EMAIL_SENT'].includes(selectedOrder.status) && (
                <button className="btn btn-danger" onClick={() => handleCancel(selectedOrder.id)}>
                  Cancel Order
                </button>
              )}
            </div>
          }>
          <div className="mb-4">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px 16px' }}>
              <div>
                <span className="text-muted text-sm">Supplier:</span>
                <div style={{ fontWeight: 600 }}>{selectedOrder.supplier_name}</div>
              </div>
              <div>
                <span className="text-muted text-sm">Status:</span>
                <div><StatusBadge status={selectedOrder.status} /></div>
              </div>
              <div>
                <span className="text-muted text-sm">Required by:</span>
                <div style={{ fontWeight: 600 }}>
                  {selectedOrder.required_by_date ? new Date(selectedOrder.required_by_date).toLocaleDateString() : 'N/A'}
                </div>
              </div>
              <div>
                <span className="text-muted text-sm">Priority:</span>
                <div><StatusBadge status={selectedOrder.priority} /></div>
              </div>
            </div>
            {selectedOrder.notes && (
              <div className="mt-4" style={{ background: 'var(--bg-tertiary)', padding: 12, borderRadius: 6 }}>
                <span className="text-muted text-sm">Notes:</span>
                <p className="text-secondary" style={{ fontSize: 13, marginTop: 4 }}>{selectedOrder.notes}</p>
              </div>
            )}
          </div>

          <h4 style={{ fontSize: 14, fontWeight: 700, marginBottom: 8 }}>Order Items</h4>
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Code</th>
                  <th>Requested Qty</th>
                  <th>Received Qty</th>
                </tr>
              </thead>
              <tbody>
                {selectedOrder.items?.map(item => (
                  <tr key={item.id}>
                    <td style={{ fontWeight: 600 }}>{item.product_name}</td>
                    <td className="font-mono text-sm">{item.product_code}</td>
                    <td>{item.requested_quantity}</td>
                    <td className="text-muted">{item.received_quantity ?? 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Modal>
      )}

      {/* Receive Stock Modal */}
      {selectedOrder && (
        <Modal open={showReceiveModal} onClose={() => setShowReceiveModal(false)} title={`Receive Stock PO #${selectedOrder.id}`}
          footer={<>
            <button className="btn btn-ghost" onClick={() => setShowReceiveModal(false)}>Cancel</button>
            <button className="btn btn-success" onClick={handleReceiveSubmit} disabled={saving}>
              {saving ? 'Processing...' : 'Confirm Stock Intake'}
            </button>
          </>}>
          <ErrorBanner message={error} />
          <p className="text-secondary mb-4" style={{ fontSize: 13 }}>
            Verify the quantities physically delivered by the supplier. Leaving values as requested means full shipment intake.
          </p>
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Requested</th>
                  <th>Received Quantity *</th>
                </tr>
              </thead>
              <tbody>
                {selectedOrder.items?.map(item => (
                  <tr key={item.id}>
                    <td>
                      <div style={{ fontWeight: 600 }}>{item.product_name}</div>
                      <div className="text-sm text-muted">{item.product_code}</div>
                    </td>
                    <td>{item.requested_quantity}</td>
                    <td>
                      <input
                        className="form-input"
                        type="number"
                        min="0"
                        step="0.01"
                        style={{ width: 100 }}
                        value={receiveQtys[item.id] ?? ''}
                        onChange={e => setReceiveQtys(prev => ({
                          ...prev, [item.id]: e.target.value
                        }))}
                        required
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Modal>
      )}
    </div>
  );
}
