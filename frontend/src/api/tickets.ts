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

export async function listTickets() {
  const response = await apiClient.get<TicketRead[]>("/tickets");
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
