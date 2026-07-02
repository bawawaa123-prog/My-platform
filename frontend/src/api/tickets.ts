import { apiClient } from "./client";


export const TICKET_CATEGORIES = [
  "payment",
  "account",
  "product",
  "refund",
  "invoice",
  "technical",
  "hr",
  "it",
  "other",
] as const;

export const TICKET_PRIORITIES = ["low", "medium", "high", "urgent"] as const;

export const TICKET_STATUSES = [
  "open",
  "ai_processing",
  "waiting_review",
  "in_progress",
  "resolved",
  "closed",
] as const;

export type TicketCategory = (typeof TICKET_CATEGORIES)[number];
export type TicketPriority = (typeof TICKET_PRIORITIES)[number];
export type TicketStatus = (typeof TICKET_STATUSES)[number];

export type TicketRead = {
  id: number;
  title: string;
  content: string;
  customer_name: string;
  customer_email: string;
  category: TicketCategory;
  priority: TicketPriority;
  sentiment: "positive" | "neutral" | "negative" | "angry";
  status: TicketStatus;
  source: string;
  ai_summary: string | null;
  recommended_department: string | null;
  assigned_to: number | null;
  created_by: number;
  closed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type TicketCreatePayload = {
  title: string;
  content: string;
  customer_name: string;
  customer_email: string;
  category: TicketCategory;
  priority: TicketPriority;
  source?: string;
};

export type TicketUpdatePayload = {
  title?: string;
  content?: string;
  customer_name?: string;
  customer_email?: string;
  category?: TicketCategory;
  priority?: TicketPriority;
  status?: TicketStatus;
  source?: string;
  assigned_to?: number | null;
};

export type TicketMessageRead = {
  id: number;
  ticket_id: number;
  sender_type: "customer" | "agent" | "ai" | "system";
  sender_name: string;
  content: string;
  created_at: string;
  updated_at: string;
};

export type TicketMessageCreatePayload = {
  sender_type: "customer" | "agent" | "ai" | "system";
  content: string;
  sender_name?: string;
};

export type TicketListFilters = {
  status?: TicketStatus;
  priority?: TicketPriority;
  category?: TicketCategory;
};

export type TicketPage = {
  items: TicketRead[];
  total: number;
  limit: number;
  offset: number;
};

export type TicketListPageParams = {
  status?: TicketStatus;
  priority?: TicketPriority;
  category?: TicketCategory;
  limit?: number;
  offset?: number;
};

export async function listTickets(filters?: TicketListFilters) {
  const params: Record<string, string> = {};
  if (filters?.status) {
    params.status = filters.status;
  }
  if (filters?.priority) {
    params.priority = filters.priority;
  }
  if (filters?.category) {
    params.category = filters.category;
  }
  const response = await apiClient.get<TicketRead[]>("/tickets", { params });
  return response.data;
}

export async function listTicketsPage(params: TicketListPageParams = {}) {
  const response = await apiClient.get<TicketPage>("/tickets/page", { params });
  return response.data;
}

export async function getTicket(ticketId: number) {
  const response = await apiClient.get<TicketRead>(`/tickets/${ticketId}`);
  return response.data;
}

export async function createTicket(payload: TicketCreatePayload) {
  const response = await apiClient.post<TicketRead>("/tickets", payload);
  return response.data;
}

export async function updateTicket(ticketId: number, payload: TicketUpdatePayload) {
  const response = await apiClient.patch<TicketRead>(`/tickets/${ticketId}`, payload);
  return response.data;
}

export async function listTicketMessages(ticketId: number) {
  const response = await apiClient.get<TicketMessageRead[]>(`/tickets/${ticketId}/messages`);
  return response.data;
}

export async function addTicketMessage(ticketId: number, payload: TicketMessageCreatePayload) {
  const response = await apiClient.post<TicketMessageRead>(`/tickets/${ticketId}/messages`, payload);
  return response.data;
}
