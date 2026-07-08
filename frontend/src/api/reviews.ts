import { apiClient } from "./client";

export type PendingSuggestionRead = {
  id: number;
  ticket_id: number;
  ticket_title: string;
  ticket_priority: string;
  ticket_category: string;
  ticket_status: string;
  customer_email: string;
  suggestion_type: string;
  source_workflow: string;
  source_run_id: string | null;
  suggested_content: string;
  reasoning_summary: string | null;
  sources_json: Record<string, unknown>[];
  confidence: number;
  status: string;
  created_at: string;
  updated_at: string;
};

export type PendingSuggestionPage = {
  items: PendingSuggestionRead[];
  total: number;
  limit: number;
  offset: number;
};

export type PendingSuggestionParams = {
  ticket_id?: number;
  limit?: number;
  offset?: number;
};

export async function listPendingSuggestions(
  params: PendingSuggestionParams = {},
) {
  const response = await apiClient.get<PendingSuggestionPage>(
    "/reviews/pending-suggestions",
    { params },
  );
  return response.data;
}
