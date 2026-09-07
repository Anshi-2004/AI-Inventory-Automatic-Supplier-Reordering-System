import React from 'react';

// ── Status badge helpers ─────────────────────────────────────
const STATUS_BADGE = {
  ACTIVE:           'badge badge-active',
  LOW_STOCK:        'badge badge-low',
  CRITICAL:         'badge badge-critical',
  OUT_OF_STOCK:     'badge badge-out',
  EMERGENCY_STOCK:  'badge badge-emergency',
  EXPIRING_SOON:    'badge badge-expiring',
  EXPIRED:          'badge badge-expired',
  NO_CONSUMPTION_DATA: 'badge badge-draft',
  // Order status
  DRAFT:             'badge badge-draft',
  PENDING_APPROVAL:  'badge badge-low',
  APPROVED:          'badge badge-approved',
  EMAIL_GENERATED:   'badge badge-approved',
  EMAIL_SENT:        'badge badge-sent',
  CONFIRMED:         'badge badge-sent',
  DISPATCHED:        'badge badge-approved',
  DELIVERED:         'badge badge-active',
  CANCELLED:         'badge badge-expired',
  // Email status
  SENT:    'badge badge-sent',
  FAILED:  'badge badge-critical',
  // Severity
  LOW:      'badge badge-active',
  MEDIUM:   'badge badge-low',
  HIGH:     'badge badge-critical',
  // Priority
  NORMAL:    'badge badge-approved',
  EMERGENCY: 'badge badge-emergency',
};

export function StatusBadge({ status }) {
  const cls = STATUS_BADGE[status] || 'badge badge-draft';
  return <span className={cls}>{status?.replace(/_/g, ' ')}</span>;
}

export function DaysBar({ days, alertDays = 7, criticalDays = 3 }) {
  if (days === null || days === undefined) return <span className="text-muted text-sm">N/A</span>;
  const pct = Math.min((days / Math.max(alertDays * 2, 14)) * 100, 100);
  const color = days <= criticalDays ? 'var(--status-critical)'
              : days <= alertDays    ? 'var(--status-low)'
              : 'var(--status-active)';
  return (
    <div className="days-bar">
      <span style={{ color, fontWeight: 700, minWidth: 36, fontSize: 13 }}>
        {days.toFixed(1)}d
      </span>
      <div className="days-bar-track" style={{ width: 60 }}>
        <div className="days-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
}

export function Spinner() {
  return (
    <div className="loading-spinner">
      <div className="spinner" />
      Loading...
    </div>
  );
}

export function EmptyState({ icon = '📭', title, description }) {
  return (
    <div className="empty-state">
      <div className="empty-state-icon">{icon}</div>
      <div className="empty-state-title">{title}</div>
      {description && <div className="empty-state-desc">{description}</div>}
    </div>
  );
}

export function ErrorBanner({ message }) {
  if (!message) return null;
  return (
    <div className="alert-banner alert-error">
      ⚠️ {message}
    </div>
  );
}

export function Modal({ open, onClose, title, children, footer }) {
  if (!open) return null;
  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <h3 className="modal-title">{title}</h3>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>
  );
}
