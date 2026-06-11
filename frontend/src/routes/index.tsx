import { createBrowserRouter, Navigate } from "react-router-dom";

import AppLayout from "../components/AppLayout";
import ProtectedRoute from "../components/ProtectedRoute";
import DashboardPage from "../pages/DashboardPage";
import HomePage from "../pages/HomePage";
import KnowledgeDetailPage from "../pages/KnowledgeDetailPage";
import KnowledgePage from "../pages/KnowledgePage";
import LoginPage from "../pages/LoginPage";
import TicketCreatePage from "../pages/TicketCreatePage";
import TicketDetailPage from "../pages/TicketDetailPage";
import TicketsPage from "../pages/TicketsPage";

export const router = createBrowserRouter([
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/",
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          {
            index: true,
            element: <DashboardPage />,
          },
          {
            path: "home",
            element: <HomePage />,
          },
          {
            path: "tickets",
            element: <TicketsPage />,
          },
          {
            path: "tickets/new",
            element: <TicketCreatePage />,
          },
          {
            path: "tickets/:ticketId",
            element: <TicketDetailPage />,
          },
          {
            path: "knowledge",
            element: <KnowledgePage />,
          },
          {
            path: "knowledge/:docId",
            element: <KnowledgeDetailPage />,
          },
        ],
      },
    ],
  },
  {
    path: "*",
    element: <Navigate to="/" replace />,
  },
]);
