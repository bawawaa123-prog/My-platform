import { apiClient } from "./client";
import type { TicketCategory, TicketPriority, TicketRead } from "./tickets";

export type TicketSentiment = "positive" | "neutral" | "negative" | "angry";

export type TicketClassification = {
  category: TicketCategory;
  priority: TicketPriority;
  sentiment: TicketSentiment;
  need_human: boolean;
  summary: string;
  recommended_department: string;
};

export type AIReplySource = {
  doc_id: number;
  chunk_id: number;
  chunk_index: number;
  content_preview: string;
  score: number;
};

export type AIReplyDraftRead = {
  id: number;
  ticket_id: number;
  suggestion_type: string;
  source_workflow: "single_agent_rag" | "single_agent_workflow" | "multi_agent" | "manual" | string;
  source_run_id: string | null;
  suggested_content: string;
  reasoning_summary: string | null;
  sources_json: AIReplySource[];
  confidence: number;
  status: string;
  reviewed_by: number | null;
  reviewed_at: string | null;
  final_content: string | null;
  reject_reason: string | null;
  created_at: string;
  updated_at: string;
};

export function normalizeSourceWorkflow(value: string | undefined | null): string {
  if (!value || value === "single_agent") {
    return "single_agent_rag";
  }
  if (value === "workflow") {
    return "single_agent_workflow";
  }
  return value;
}

export type SuggestionApprovePayload = {
  final_content?: string;
};

export type SuggestionEditPayload = {
  final_content: string;
};

export type SuggestionRejectPayload = {
  reject_reason: string;
};

export type AgentAuditTrailItem = {
  agent_name: string;
  action: string;
  input_summary: string;
  output_summary: string;
  status: string;
  timestamp: string;
};

export type MultiAgentSupervisorResult = {
  agent_name: string;
  workflow_mode: string;
  planned_agents: string[];
  requires_human_review: boolean;
  summary: string;
};

export type MultiAgentTriageResult = {
  agent_name: string;
  classification: TicketClassification;
};

export type MultiAgentKnowledgeHit = AIReplySource & {
  embedding_id?: string | null;
};

export type MultiAgentKnowledgeResult = {
  agent_name: string;
  query: string;
  confidence: number;
  low_confidence_reason: string | null;
  hits: MultiAgentKnowledgeHit[];
};

export type MultiAgentSimilarCaseTicket = {
  ticket_id: number;
  title: string;
  similarity: number;
  resolution: string;
  content_preview?: string;
  [key: string]: unknown;
};

export type MultiAgentSimilarCaseResult = {
  agent_name: string;
  similar_tickets: MultiAgentSimilarCaseTicket[];
  historical_summary: string;
};

export type MultiAgentReplyResult = {
  agent_name: string;
  supplemental_context: string;
  reply_suggestion: AIReplyDraftRead;
};

export type MultiAgentRiskCheck = {
  risk_level: "low" | "medium" | "high" | string;
  requires_human_review: boolean;
  reasons: string[];
};

export type MultiAgentRiskResult = {
  agent_name: string;
  risk_check: MultiAgentRiskCheck;
};

export type MultiAgentWorkflowResult = {
  agent_name: string;
  next_status: string;
  assign_to_department: string;
  next_action: string;
  internal_note: string;
  updated_ticket: TicketRead;
};

export type AIMultiAgentPendingReviewRead = {
  run_id: string;
  thread_id: string;
  status: "pending_review";
  pending_node: string;
  interrupt_id: string | null;
  ticket: TicketRead;
  supervisor_result: MultiAgentSupervisorResult;
  triage_result: MultiAgentTriageResult;
  knowledge_result: MultiAgentKnowledgeResult;
  similar_case_result: MultiAgentSimilarCaseResult;
  reply_result: MultiAgentReplyResult;
  risk_result: MultiAgentRiskResult;
  workflow_result: MultiAgentWorkflowResult;
  draft_reply: AIReplyDraftRead;
  sources: AIReplySource[];
  confidence: number;
  audit_trail: AgentAuditTrailItem[];
};

export type MultiAgentResumePayload = {
  action: "approve" | "edit" | "reject";
  thread_id?: string;
  run_id?: string;
  final_content?: string;
  reject_reason?: string;
};

export type AIMultiAgentProcessRead = {
  ticket: Record<string, unknown>;
  supervisor_result: MultiAgentSupervisorResult;
  triage_result: MultiAgentTriageResult;
  knowledge_result: MultiAgentKnowledgeResult;
  similar_case_result: MultiAgentSimilarCaseResult;
  reply_result: MultiAgentReplyResult;
  risk_result: MultiAgentRiskResult;
  workflow_result: MultiAgentWorkflowResult;
  audit_trail: AgentAuditTrailItem[];
  review_decision: Record<string, unknown> | null;
  reviewed_suggestion: AIReplyDraftRead | null;
};

export type AgentRunLogRead = {
  id: number;
  ticket_id: number;
  run_id: string;
  run_type: "single_agent_rag" | "single_agent_workflow" | "multi_agent" | "workflow" | string;
  status: string;
  input_json: Record<string, unknown>;
  output_json: Record<string, unknown>;
  audit_trail_json: AgentAuditTrailItem[];
  error_message: string | null;
  created_by: number | null;
  created_at: string;
  updated_at: string;
};

export async function classifyTicketAI(ticketId: number) {
  const response = await apiClient.post<TicketClassification>(`/ai/tickets/${ticketId}/classify`);
  return response.data;
}

export async function generateTicketReply(ticketId: number) {
  const response = await apiClient.post<AIReplyDraftRead>(`/ai/tickets/${ticketId}/generate-reply`);
  return response.data;
}

export async function listTicketSuggestions(ticketId: number) {
  const response = await apiClient.get<AIReplyDraftRead[]>(`/ai/tickets/${ticketId}/suggestions`);
  return response.data;
}

export async function approveSuggestion(suggestionId: number, payload: SuggestionApprovePayload = {}) {
  const response = await apiClient.post<AIReplyDraftRead>(`/reviews/${suggestionId}/approve`, payload);
  return response.data;
}

export async function editSuggestion(suggestionId: number, payload: SuggestionEditPayload) {
  const response = await apiClient.post<AIReplyDraftRead>(`/reviews/${suggestionId}/edit`, payload);
  return response.data;
}

export async function rejectSuggestion(suggestionId: number, payload: SuggestionRejectPayload) {
  const response = await apiClient.post<AIReplyDraftRead>(`/reviews/${suggestionId}/reject`, payload);
  return response.data;
}

export async function startMultiAgentProcess(ticketId: number) {
  const response = await apiClient.post<AIMultiAgentPendingReviewRead>(
    `/ai/tickets/${ticketId}/multi-agent-process/start`,
  );
  return response.data;
}

export async function resumeMultiAgentProcess(
  ticketId: number,
  payload: MultiAgentResumePayload,
) {
  const response = await apiClient.post<AIMultiAgentProcessRead>(
    `/ai/tickets/${ticketId}/multi-agent-process/resume`,
    payload,
  );
  return response.data;
}

export async function listTicketAgentRuns(ticketId: number) {
  const response = await apiClient.get<AgentRunLogRead[]>(`/ai/tickets/${ticketId}/agent-runs`);
  return response.data;
}

export type AgentRunLogPage = {
  items: AgentRunLogRead[];
  total: number;
  limit: number;
  offset: number;
};

export type AgentRunLogPageParams = {
  run_type?: string;
  status?: string;
  limit?: number;
  offset?: number;
};

export async function listTicketAgentRunsPage(
  ticketId: number,
  params: AgentRunLogPageParams = {},
) {
  const response = await apiClient.get<AgentRunLogPage>(
    `/ai/tickets/${ticketId}/agent-runs/page`,
    { params },
  );
  return response.data;
}

export type LatestAgentRunsByType = {
  single_agent_rag: AgentRunLogRead | null;
  single_agent_workflow: AgentRunLogRead | null;
  multi_agent: AgentRunLogRead | null;
};

export async function getLatestTicketAgentRunsByType(
  ticketId: number,
): Promise<LatestAgentRunsByType> {
  const response = await apiClient.get<LatestAgentRunsByType>(
    `/ai/tickets/${ticketId}/agent-runs/latest-by-type`,
  );
  return response.data;
}

export type AIWorkflowPendingReviewRead = {
  run_id: string;
  thread_id: string;
  status: "pending_review";
  pending_node: string;
  interrupt_id: string | null;
  ticket: TicketRead;
  classification: TicketClassification;
  knowledge_hits: Record<string, unknown>[];
  similar_tickets: Record<string, unknown>[];
  draft_reply: AIReplyDraftRead;
  sources: AIReplySource[];
  confidence: number;
  risk_check: Record<string, unknown>;
};

export type AIWorkflowProcessRead = {
  ticket: Record<string, unknown>;
  classification: Record<string, unknown>;
  knowledge_hits: Record<string, unknown>[];
  similar_tickets: Record<string, unknown>[];
  reply_suggestion: Record<string, unknown>;
  risk_check: Record<string, unknown>;
  reviewed_suggestion: AIReplyDraftRead | null;
  review_decision: Record<string, unknown> | null;
};

export type AIWorkflowResumePayload = {
  action: "approve" | "edit" | "reject";
  thread_id?: string;
  run_id?: string;
  final_content?: string;
  reject_reason?: string;
};

export async function startSingleAgentProcess(ticketId: number) {
  const response = await apiClient.post<AIWorkflowPendingReviewRead>(
    `/ai/tickets/${ticketId}/process/start`,
  );
  return response.data;
}

export async function resumeSingleAgentProcess(
  ticketId: number,
  payload: AIWorkflowResumePayload,
) {
  const response = await apiClient.post<AIWorkflowProcessRead>(
    `/ai/tickets/${ticketId}/process/resume`,
    payload,
  );
  return response.data;
}

export async function listReviewedSuggestions(ticketId: number) {
  const response = await apiClient.get<AIReplyDraftRead[]>(
    `/ai/tickets/${ticketId}/reviewed-suggestions`,
  );
  return response.data;
}
