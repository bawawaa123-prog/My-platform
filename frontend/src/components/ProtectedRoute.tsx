import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "../stores/auth";


export default function ProtectedRoute() {
  const { isAuthenticated, isInitializing } = useAuth();
  const location = useLocation();

  if (isInitializing) {
    return (
      <div className="auth-shell">
        <div className="auth-card auth-card--status">
          <p className="eyebrow">Enterprise Support Agent</p>
          <h1>Loading workspace</h1>
          <p className="auth-helper">
            Checking your saved session and preparing the operations dashboard.
          </p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}
