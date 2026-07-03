import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../stores/auth";


const navItems = [
  { to: "/", label: "Dashboard" },
  { to: "/tickets", label: "Tickets" },
  { to: "/audit-logs", label: "Audit Logs" },
  { to: "/knowledge", label: "Knowledge" },
];

export default function AppLayout() {
  const { user, logout } = useAuth();
  const [isSidebarHidden, setIsSidebarHidden] = useState(() => {
    if (typeof window === "undefined") {
      return false;
    }

    return window.localStorage.getItem("ops-sidebar-hidden") === "true";
  });

  useEffect(() => {
    window.localStorage.setItem("ops-sidebar-hidden", String(isSidebarHidden));
  }, [isSidebarHidden]);

  return (
    <div className={isSidebarHidden ? "app-shell app-shell--sidebar-hidden" : "app-shell"}>
      <aside className={isSidebarHidden ? "sidebar sidebar--hidden" : "sidebar"}>
        <div className="brand-block">
          <p className="eyebrow">Enterprise Support Agent</p>
          <h1 className="brand-title">Ops Console</h1>
          <p className="brand-description">
            Ticket triage, knowledge search, and AI-assisted review in one control room.
          </p>
        </div>

        <nav className="sidebar-nav" aria-label="Primary">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                isActive ? "nav-item nav-item--active" : "nav-item"
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="identity-card">
            <p className="identity-name">{user?.username ?? "Unknown User"}</p>
            <p className="identity-meta">
              {user?.role ?? "viewer"} · {user?.email ?? "No email"}
            </p>
          </div>
          <button type="button" className="ghost-button" onClick={logout}>
            Sign out
          </button>
        </div>
      </aside>

      <div className="workspace">
        <header className="workspace-header">
          <div>
            <p className="workspace-label">Operations Workspace</p>
            <h2 className="workspace-title">Enterprise support back office</h2>
          </div>
          <div className="workspace-header-actions">
            <button
              type="button"
              className="ghost-button workspace-toggle"
              onClick={() => setIsSidebarHidden((current) => !current)}
            >
              {isSidebarHidden ? "Expand sidebar" : "Hide sidebar"}
            </button>
            <div className="status-pill">Authenticated session</div>
          </div>
        </header>

        <main className="workspace-main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
