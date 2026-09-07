import React, { useEffect, useState } from 'react';
import { emailApi, aiApi } from '../api/client';
import { Spinner, StatusBadge, Modal, ErrorBanner } from '../components/ui/SharedComponents';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';

export default function EmailCenterPage() {
  const { isAdmin } = useAuth();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  // Review modal
  const [selectedLog, setSelectedLog] = useState(null);
  const [showReviewModal, setShowReviewModal] = useState(false);

  // Edit form states
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');

  const [saving, setSaving] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');

  const load = async () => {
    try {
      const data = await emailApi.logs();
      setLogs(data.items || []);
    } catch {
      toast.error('Failed to load email logs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleOpenReview = (log) => {
    setSelectedLog(log);
    setSubject(log.subject);
    setBody(log.body);
    setShowReviewModal(true);
  };

  const handleApprove = async () => {
    setError('');
    setSaving(true);
    try {
      await emailApi.approve(selectedLog.id, { subject, body });
      toast.success('Email draft approved!');
      await load();
      setShowReviewModal(false);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to approve email');
    } finally {
      setSaving(false);
    }
  };

  const handleSend = async () => {
    setError('');
    setSending(true);
    try {
      await emailApi.send(selectedLog.id);
      toast.success('Email sent successfully via Gmail API!');
      await load();
      setShowReviewModal(false);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send email. Check credentials.');
    } finally {
      setSending(false);
    }
  };

  const handleRegenerate = async () => {
    if (!window.confirm('This will create a new AI email draft. Proceed?')) return;
    toast.loading('Regenerating draft...', { id: 'ai-regen' });
    try {
      const data = await aiApi.regenerateEmail({ email_log_id: selectedLog.id });
      toast.success('New AI email draft generated!', { id: 'ai-regen' });
      await load();
      // Switch view to the new log
      setSelectedLog(data);
      setSubject(data.subject);
      setBody(data.body);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to regenerate email', { id: 'ai-regen' });
    }
  };

  if (loading) return <Spinner />;

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">AI Procurement Email Center</h1>
        <p className="page-subtitle">Human-in-the-loop review, editing, and transmission of reordering requests</p>
      </div>

      <div className="page-body">
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Log ID</th>
                <th>Recipient</th>
                <th>Subject</th>
                <th>Status</th>
                <th>Sent At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {logs.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                    No emails drafted or sent yet.
                  </td>
                </tr>
              ) : (
                logs.map(log => (
                  <tr key={log.id}>
                    <td className="font-mono text-sm">#EM-{log.id}</td>
                    <td>
                      <div style={{ fontWeight: 600 }}>{log.recipient_email}</div>
                      {log.purchase_order_id && (
                        <div className="text-sm text-muted">PO Ref: #{log.purchase_order_id}</div>
                      )}
                    </td>
                    <td>
                      <div className="truncate" style={{ maxWidth: 280 }} title={log.subject}>
                        {log.subject}
                      </div>
                    </td>
                    <td>
                      <StatusBadge status={log.status} />
                    </td>
                    <td className="text-sm text-secondary">
                      {log.sent_at ? new Date(log.sent_at).toLocaleString() : '—'}
                    </td>
                    <td>
                      <button className="btn btn-ghost btn-sm" onClick={() => handleOpenReview(log)}>
                        {log.status === 'DRAFT' ? 'Review & Edit' : 'View Details'}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Email Review & Approval Modal */}
      {selectedLog && (
        <Modal
          open={showReviewModal}
          onClose={() => setShowReviewModal(false)}
          title={`Review Reorder Email #EM-${selectedLog.id}`}
          footer={
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', width: '100%' }}>
              <button className="btn btn-ghost" onClick={() => setShowReviewModal(false)}>Close</button>
              {selectedLog.status === 'DRAFT' && isAdmin && (
                <>
                  <button className="btn btn-ghost" onClick={handleRegenerate}>🔄 Regenerate</button>
                  <button className="btn btn-primary" onClick={handleApprove} disabled={saving}>
                    {saving ? 'Saving...' : 'Approve Draft'}
                  </button>
                </>
              )}
              {selectedLog.status === 'APPROVED' && isAdmin && (
                <button className="btn btn-success" onClick={handleSend} disabled={sending}>
                  {sending ? '🚀 Sending...' : '🚀 Send Email'}
                </button>
              )}
            </div>
          }
        >
          <ErrorBanner message={error} />

          <div className="mb-4">
            <span className="text-muted text-sm">To:</span>
            <div style={{ fontWeight: 600, fontSize: 14 }}>{selectedLog.recipient_email}</div>
          </div>

          {selectedLog.status === 'DRAFT' ? (
            <>
              <div className="form-group">
                <label className="form-label">Subject Line</label>
                <input
                  className="form-input"
                  value={subject}
                  onChange={e => setSubject(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Email Body (Markdown/Text)</label>
                <textarea
                  className="form-textarea"
                  rows={12}
                  style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 13 }}
                  value={body}
                  onChange={e => setBody(e.target.value)}
                />
              </div>
            </>
          ) : (
            <>
              <div className="mb-4">
                <span className="text-muted text-sm">Subject:</span>
                <div style={{ fontWeight: 600 }}>{selectedLog.subject}</div>
              </div>
              <div>
                <span className="text-muted text-sm">Body:</span>
                <div className="email-preview">{selectedLog.body}</div>
              </div>
              {selectedLog.error_message && (
                <div className="alert-banner alert-error mt-4">
                  <strong>Delivery Failure:</strong> {selectedLog.error_message}
                </div>
              )}
            </>
          )}
        </Modal>
      )}
    </div>
  );
}
