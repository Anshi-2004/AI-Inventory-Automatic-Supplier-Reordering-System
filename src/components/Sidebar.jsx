import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const NAV_ITEMS = [
  { to: '/',            icon: '📊', label: 'Dashboard' },
  { to: '/products',    icon: '📦', label: 'Products' },
  { to: '/inventory',   icon: '🏪', label: 'Inventory' },
  { to: '/suppliers',   icon: '🏭', label: 'Suppliers' },
  { to: '/orders',      icon: '📋', label: 'Purchase Orders' },
  { to: '/alerts',      icon: '🔔', label: 'Alerts' },
  { to: '/email-center',icon: '✉️', label: 'Email Center' },
  { to: '/reports',     icon: '📈', label: 'Reports' },
];

export default function Sidebar() {
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => { logout(); navigate('/login'); };

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-title">⚡ InventoryAI</div>
        <div className="logo-sub">Smart Reordering System</div>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section-label">Main Menu</div>
        {NAV_ITEMS.map(({ to, icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
          >
            <span style={{ fontSize: 15 }}>{icon}</span>
            {label}
          </NavLink>
        ))}

        {isAdmin && (
          <>
            <div className="nav-section-label" style={{ marginTop: 12 }}>Admin</div>
            <NavLink
              to="/settings"
              className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            >
              <span style={{ fontSize: 15 }}>⚙️</span>
              Settings
            </NavLink>
          </>
        )}
      </nav>

      <div className="sidebar-user">
        <div className="user-avatar">
          {user?.name?.charAt(0).toUpperCase()}
        </div>
        <div className="user-info">
          <div className="user-name">{user?.name}</div>
          <div className="user-role">{user?.role?.replace('_', ' ')}</div>
        </div>
        <button className="logout-btn" onClick={handleLogout} title="Logout">
          🚪
        </button>
      </div>
    </aside>
  );
}
