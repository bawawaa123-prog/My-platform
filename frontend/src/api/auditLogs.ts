import { apiClient } from "./client";


export type AuditLogRead = {
  id: number;
  user_id: number;
  action: string;
  target_type: string;
  target_id: number;
  detail_json: Record<string, unknown>;
  created_at: string;
};

export type AuditLogPage = {
  items: AuditLogRead[];
  total: number;
  limit: number | null;
  offset: number | null;
};

export type AuditLogQueryParams = {
  action?: string;
  target_type?: string;
  target_id?: number;
  user_id?: number;
  limit?: number;
  offset?: number;
};

const AUDIT_LOG_ACTIONS = [
  "create_ticket",
  "update_ticket",
  "delete_ticket",
  "create_message",
  "create_knowledge_doc",
  "update_knowledge_doc",
  "delete_knowledge_doc",
  "upload_document",
  "review_ai_suggestion",
  "approve_reply",
  "reject_reply",
] as const;

const AUDIT_LOG_TARGET_TYPES = [
  "ticket",
  "message",
  "knowledge_doc",
  "knowledge_chunk",
  "ai_suggestion",
  "user",
] as const;

export { AUDIT_LOG_ACTIONS, AUDIT_LOG_TARGET_TYPES };

export async function listAuditLogs(params: AuditLogQueryParams = {}) {
  const response = await apiClient.get<AuditLogPage>("/audit-logs", { params });
  return response.data;
}
