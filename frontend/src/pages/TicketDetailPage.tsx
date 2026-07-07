import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { useAuth } from "../stores/auth";

import {
  approveSuggestion,
  classifyTicketAI,
  editSuggestion,
  listReviewedSuggestions,
  listTicketAgentRuns,
  listTicketAgentRunsPage,
  listTicketSuggestions,
  rejectSuggestion,
  resumeMultiAgentProcess,
  resumeSingleAgentProcess,
  startMultiAgentProcess,
  startSingleAgentProcess,
  type AgentAuditTrailItem,
  type AgentRunLogPageParams,
  type AgentRunLogRead,
  type AIMultiAgentPendingReviewRead,
  type AIMultiAgentProcessRead,
  type AIReplyDraftRead,
  type AIReplySource,
  type AIWorkflowPendingReviewRead,
  type AIWorkflowProcessRead,
  type MultiAgentKnowledgeResult,
  type MultiAgentReplyResult,
  type MultiAgentRiskResult,
  type MultiAgentSimilarCaseResult,
  type MultiAgentSupervisorResult,
  type MultiAgentTriageResult,
  type MultiAgentWorkflowResult,
  type TicketClassification,
} from "../api/ai";
import {
  addTicketMessage,
  getTicket,
  listTicketMessages,
  TICKET_STATUSES,
  updateTicket,
  type TicketMessageRead,
  type TicketRead,
  type TicketStatus,
} from "../api/tickets";
import { formatDateTime } from "../utils/date";

type DisplayClassification = {
  category: TicketRead["category"];
  priority: TicketRead["priority"];
  sentiment: TicketRead["sentiment"];
  recommended_department: string | null;
  summary: string;
  need_human?: boolean;
};

type AgentOutputCard = {
  agentName: string;
  title: string;
  description: string;
  data: unknown;
};

function toLabel(value: string) {
  return value
    .split("_")
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}

function formatConfidence(value: number) {
  return `${Math.round(value * 100)}%`;
}

function buildStoredClassification(ticket: TicketRead): DisplayClassification | null {
  if (!ticket.ai_summary) {
    return null;
  }

  return {
    category: ticket.category,
    priority: ticket.priority,
    sentiment: ticket.sentiment,
    recommended_department: ticket.recommended_department,
    summary: ticket.ai_summary,
  };
}

function upsertSuggestion(current: AIReplyDraftRead[], next: AIReplyDraftRead) {
  return [next, ...current.filter((item) => item.id !== next.id)];
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isMultiAgentPendingReviewRead(value: unknown): value is AIMultiAgentPendingReviewRead {
  return (
    isRecord(value) &&
    "run_id" in value &&
    "supervisor_result" in value &&
    "triage_result" in value &&
    "knowledge_result" in value &&
    "similar_case_result" in value &&
    "reply_result" in value &&
    "risk_result" in value &&
    "workflow_result" in value &&
    "audit_trail" in value
  );
}

function formatJson(value: unknown) {
  return JSON.stringify(value, null, 2);
}

function findAuditEntry(auditTrail: AgentAuditTrailItem[], agentName: string) {
  return auditTrail.find((item) => item.agent_name === agentName) ?? null;
}

function normalizeSourceWorkflow(source?: string | null): string {
  if (!source || source === "single_agent") return "single_agent_rag";
  if (source === "workflow") return "single_agent_workflow";
  return source;
}

function normalizeRunType(runType?: string | null): string {
  if (!runType) return "";
  if (runType === "workflow") return "single_agent_workflow";
  return runType;
}

function sourceWorkflowLabel(source: string): string {
  switch (source) {
    case "single_agent_rag": return "Single-Agent RAG";
    case "single_agent_workflow": return "Single-Agent Workflow";
    case "multi_agent": return "Multi-Agent";
    case "manual": return "Manual";
    default: return toLabel(source);
  }
}

function runTypeLabel(runType: string): string {
  if (runType === "workflow") return "Single-Agent Workflow (Legacy)";
  return sourceWorkflowLabel(normalizeRunType(runType));
}

function RagSourcesPanel({ sources }: { sources: AIReplySource[] }) {
  return (
    <article className="panel panel--subtle">
      <div className="panel-heading">
        <div>
          <p className="panel-tag">Sources</p>
          <h3>RAG references</h3>
        </div>
      </div>

      {sources.length === 0 ? (
        <p className="panel-state">
          No strong knowledge match was retrieved, so this draft should be reviewed carefully before approval.
        </p>
      ) : (
        <div className="source-list">
          {sources.map((source) => (
            <article key={source.chunk_id} className="source-card">
              <div className="source-card__header">
                <div>
                  <strong>Document #{source.doc_id}</strong>
                  <span>Chunk {source.chunk_index} · ID {source.chunk_id}</span>
                </div>
                <span className="badge badge--score">
                  Score {source.score.toFixed(3)}
                </span>
              </div>
              <p>{source.content_preview}</p>
              <Link to={`/knowledge/${source.doc_id}`} className="ghost-link">
                View knowledge document
              </Link>
            </article>
          ))}
        </div>
      )}
    </article>
  );
}

function getReviewTime(s: AIReplyDraftRead): string {
  return s.reviewed_at ?? s.updated_at ?? s.created_at;
}

function isFinalReviewVisible(s: AIReplyDraftRead): boolean {
  return s.status === "approved" || s.status === "edited";
}

function isSingleAgentReview(s: AIReplyDraftRead): boolean {
  const source = normalizeSourceWorkflow(s.source_workflow);
  return source === "single_agent_rag" || source === "single_agent_workflow";
}

function isMultiAgentReview(s: AIReplyDraftRead): boolean {
  return normalizeSourceWorkflow(s.source_workflow) === "multi_agent";
}

function pickLatestReview(items: AIReplyDraftRead[]): AIReplyDraftRead | null {
  return [...items]
    .filter(isFinalReviewVisible)
    .sort((a, b) => getReviewTime(b).localeCompare(getReviewTime(a)) || b.id - a.id)[0] ?? null;
}

function buildAgentCards(result: AIMultiAgentPendingReviewRead | AIMultiAgentProcessRead): AgentOutputCard[] {
  return [
    {
      agentName: "SupervisorAgent",
      title: "Supervisor Agent",
      description: "Workflow planning and execution intent",
      data: result.supervisor_result,
    },
    {
      agentName: "TriageAgent",
      title: "Triage Agent",
      description: "Classification, priority, sentiment, and department recommendation",
      data: result.triage_result,
    },
    {
      agentName: "KnowledgeAgent",
      title: "Knowledge Agent",
      description: "RAG retrieval query, confidence, and knowledge hits",
      data: result.knowledge_result,
    },
    {
      agentName: "SimilarCaseAgent",
      title: "Similar Case Agent",
      description: "Historical resolved ticket retrieval and handling summary",
      data: result.similar_case_result,
    },
    {
      agentName: "ReplyAgent",
      title: "Reply Agent",
      description: "Draft generation and customer-facing response proposal",
      data: result.reply_result,
    },
    {
      agentName: "RiskAgent",
      title: "Risk Agent",
      description: "Risk review and human-approval requirement assessment",
      data: result.risk_result,
    },
    {
      agentName: "WorkflowAgent",
      title: "Workflow Agent",
      description: "Ticket status routing, ownership, and follow-up action",
      data: result.workflow_result,
    },
  ];
}

function buildAgentHighlights(agentName: string, data: unknown): Array<{ label: string; value: string }> {
  if (!isRecord(data)) {
    return [];
  }

  if (agentName === "SupervisorAgent") {
    const result = data as MultiAgentSupervisorResult;
    return [
      { label: "Mode", value: result.workflow_mode },
      { label: "Planned agents", value: result.planned_agents.join(", ") },
      { label: "Human review", value: result.requires_human_review ? "Required" : "Optional" },
    ];
  }

  if (agentName === "TriageAgent") {
    const result = data as MultiAgentTriageResult;
    return [
      { label: "Category", value: toLabel(result.classification.category) },
      { label: "Priority", value: toLabel(result.classification.priority) },
      { label: "Sentiment", value: toLabel(result.classification.sentiment) },
      {
        label: "Department",
        value: result.classification.recommended_department,
      },
    ];
  }

  if (agentName === "KnowledgeAgent") {
    const result = data as MultiAgentKnowledgeResult;
    return [
      { label: "Confidence", value: formatConfidence(result.confidence) },
      { label: "Hits", value: String(result.hits.length) },
      {
        label: "Low-confidence note",
        value: result.low_confidence_reason ?? "None",
      },
    ];
  }

  if (agentName === "SimilarCaseAgent") {
    const result = data as MultiAgentSimilarCaseResult;
    return [
      { label: "Similar tickets", value: String(result.similar_tickets.length) },
      { label: "Historical summary", value: result.historical_summary },
    ];
  }

  if (agentName === "ReplyAgent") {
    const result = data as MultiAgentReplyResult;
    return [
      { label: "Draft status", value: toLabel(result.reply_suggestion.status) },
      { label: "Confidence", value: formatConfidence(result.reply_suggestion.confidence) },
      { label: "Source count", value: String(result.reply_suggestion.sources_json.length) },
    ];
  }

  if (agentName === "RiskAgent") {
    const result = data as MultiAgentRiskResult;
    return [
      { label: "Risk level", value: toLabel(result.risk_check.risk_level) },
      {
        label: "Human review",
        value: result.risk_check.requires_human_review ? "Required" : "Not required",
      },
      { label: "Risk reasons", value: String(result.risk_check.reasons.length) },
    ];
  }

  if (agentName === "WorkflowAgent") {
    const result = data as MultiAgentWorkflowResult;
    return [
      { label: "Next status", value: toLabel(result.next_status) },
      { label: "Department", value: result.assign_to_department },
      { label: "Next action", value: result.next_action },
    ];
  }

  return [];
}

function getApiErrorDetail(error: unknown, fallback: string): string {
  try {
    const data = (error as { response?: { data?: unknown } })?.response?.data;
    if (!data) {
      return fallback;
    }
    const detail = (data as { detail?: unknown })?.detail;
    if (typeof detail === "string") {
      return detail;
    }
    if (Array.isArray(detail)) {
      return detail.map((item: { msg?: string }) => item.msg ?? "").join("; ");
    }
    return fallback;
  } catch {
    return fallback;
  }
}


export default function TicketDetailPage() {
  const { user } = useAuth();

  const params = useParams();
  const ticketId = Number(params.ticketId);
  const isMountedRef = useRef(true);

  const canReview = user?.role === "admin" || user?.role === "agent";

  const [ticket, setTicket] = useState<TicketRead | null>(null);
  const [messages, setMessages] = useState<TicketMessageRead[]>([]);
  const [classification, setClassification] = useState<TicketClassification | null>(null);
  const [suggestions, setSuggestions] = useState<AIReplyDraftRead[]>([]);
  const [reviewedSuggestions, setReviewedSuggestions] = useState<AIReplyDraftRead[]>([]);
  const [multiAgentResult, setMultiAgentResult] = useState<AIMultiAgentPendingReviewRead | null>(null);
  const [latestSingleAgentRagRun, setLatestSingleAgentRagRun] = useState<AgentRunLogRead | null>(null);
  const [latestSingleAgentWorkflowRun, setLatestSingleAgentWorkflowRun] = useState<AgentRunLogRead | null>(null);
  const [latestMultiAgentRun, setLatestMultiAgentRun] = useState<AgentRunLogRead | null>(null);

  const [loading, setLoading] = useState(true);
  const [loadingSuggestions, setLoadingSuggestions] = useState(true);
  const [loadingAgentRuns, setLoadingAgentRuns] = useState(true);
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);
  const [isClassifying, setIsClassifying] = useState(false);
  const [isGeneratingReply, setIsGeneratingReply] = useState(false);
  const [isSubmittingReview, setIsSubmittingReview] = useState(false);
  const [isRunningMultiAgent, setIsRunningMultiAgent] = useState(false);

  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [statusErrorMessage, setStatusErrorMessage] = useState<string | null>(null);
  const [suggestionsErrorMessage, setSuggestionsErrorMessage] = useState<string | null>(null);
  const [agentRunsErrorMessage, setAgentRunsErrorMessage] = useState<string | null>(null);
  const [aiActionErrorMessage, setAiActionErrorMessage] = useState<string | null>(null);
  const [reviewSuccessMessage, setReviewSuccessMessage] = useState<string | null>(null);
  const [multiAgentSuccessMessage, setMultiAgentSuccessMessage] = useState<string | null>(null);
  const [isSubmittingMultiAgentReview, setIsSubmittingMultiAgentReview] = useState(false);
  const [multiAgentReviewError, setMultiAgentReviewError] = useState<string | null>(null);
  const [multiAgentReviewSuccess, setMultiAgentReviewSuccess] = useState<string | null>(null);
  const [multiAgentResumeResult, setMultiAgentResumeResult] = useState<AIMultiAgentProcessRead | null>(null);
  const [multiAgentReviewDraftContent, setMultiAgentReviewDraftContent] = useState("");
  const [multiAgentReviewRejectReason, setMultiAgentReviewRejectReason] = useState("");

  const [singleAgentResult, setSingleAgentResult] = useState<AIWorkflowPendingReviewRead | null>(null);
  const [singleAgentResumeResult, setSingleAgentResumeResult] = useState<AIWorkflowProcessRead | null>(null);
  const [isStartingSingleAgent, setIsStartingSingleAgent] = useState(false);
  const [isSubmittingSingleAgentReview, setIsSubmittingSingleAgentReview] = useState(false);
  const [singleAgentReviewDraftContent, setSingleAgentReviewDraftContent] = useState("");
  const [singleAgentReviewRejectReason, setSingleAgentReviewRejectReason] = useState("");
  const [singleAgentReviewError, setSingleAgentReviewError] = useState<string | null>(null);
  const [singleAgentReviewSuccess, setSingleAgentReviewSuccess] = useState<string | null>(null);

  const [reviewDraftContent, setReviewDraftContent] = useState("");
  const [reviewRejectReason, setReviewRejectReason] = useState("");

  const [messageContent, setMessageContent] = useState("");
  const [messageSenderType, setMessageSenderType] = useState<"agent" | "customer" | "ai" | "system">("agent");
  const [isSendingMessage, setIsSendingMessage] = useState(false);
  const [sendMessageError, setSendMessageError] = useState<string | null>(null);
  const [sendMessageSuccess, setSendMessageSuccess] = useState<string | null>(null);

  const AGENT_RUN_PAGE_SIZE = 5;

  const [agentRunHistory, setAgentRunHistory] = useState<AgentRunLogRead[]>([]);
  const [agentRunTotal, setAgentRunTotal] = useState(0);
  const [agentRunOffset, setAgentRunOffset] = useState(0);
  const [agentRunTypeFilter, setAgentRunTypeFilter] = useState("all");
  const [agentRunStatusFilter, setAgentRunStatusFilter] = useState("all");
  const [agentRunHistoryLoading, setAgentRunHistoryLoading] = useState(false);
  const [agentRunHistoryError, setAgentRunHistoryError] = useState<string | null>(null);
  const [expandedAgentRunId, setExpandedAgentRunId] = useState<string | null>(null);
  const [isSingleAgentPanelExpanded, setIsSingleAgentPanelExpanded] = useState(true);
  const [isMultiAgentPanelExpanded, setIsMultiAgentPanelExpanded] = useState(true);

  const singleAgentRagSuggestions = useMemo(
    () => suggestions.filter((s) => normalizeSourceWorkflow(s.source_workflow) === "single_agent_rag"),
    [suggestions],
  );
  const singleAgentWorkflowSuggestions = useMemo(
    () => suggestions.filter((s) => normalizeSourceWorkflow(s.source_workflow) === "single_agent_workflow"),
    [suggestions],
  );
  const multiAgentSuggestions = useMemo(
    () => suggestions.filter((s) => normalizeSourceWorkflow(s.source_workflow) === "multi_agent"),
    [suggestions],
  );
  const latestSingleAgentRagSuggestion = singleAgentRagSuggestions[0] ?? null;
  const latestSingleAgentWorkflowSuggestion = singleAgentWorkflowSuggestions[0] ?? null;
  const latestMultiAgentSuggestion = multiAgentSuggestions[0] ?? null;

  // For backward compat: the "latestSingleAgentSuggestion" used in old review UI
  const latestSingleAgentSuggestion = latestSingleAgentRagSuggestion;

  const multiAgentFinalReviewedSuggestion = useMemo(() => {
    if (multiAgentResumeResult?.reviewed_suggestion) {
      return multiAgentResumeResult.reviewed_suggestion;
    }
    if (latestMultiAgentRun?.status === "completed" && latestMultiAgentRun?.output_json?.reviewed_suggestion) {
      return latestMultiAgentRun.output_json.reviewed_suggestion as AIReplyDraftRead;
    }
    // Fallback to reviewed suggestions from DB
    const fromDb = reviewedSuggestions.find(
      (s) => normalizeSourceWorkflow(s.source_workflow) === "multi_agent" && s.status !== "rejected",
    );
    return fromDb ?? null;
  }, [multiAgentResumeResult, latestMultiAgentRun, reviewedSuggestions]);

  const singleAgentFinalReviewedSuggestion = useMemo(() => {
    if (singleAgentResumeResult?.reviewed_suggestion) {
      return singleAgentResumeResult.reviewed_suggestion;
    }
    // Fallback to DB reviewed suggestions
    const fromDb = reviewedSuggestions.find(
      (s) => normalizeSourceWorkflow(s.source_workflow) === "single_agent_workflow" && s.status !== "rejected",
    );
    return fromDb ?? null;
  }, [singleAgentResumeResult, reviewedSuggestions]);

  // Build the consolidated Final Review slots: at most two — latest SA + latest MA
  const finalReviewCandidates = useMemo(() => {
    const map = new Map<number, AIReplyDraftRead>();

    for (const s of reviewedSuggestions) {
      map.set(s.id, s);
    }

    if (singleAgentResumeResult?.reviewed_suggestion) {
      const s = singleAgentResumeResult.reviewed_suggestion;
      map.set(s.id, s);
    }

    if (multiAgentResumeResult?.reviewed_suggestion) {
      const s = multiAgentResumeResult.reviewed_suggestion;
      map.set(s.id, s);
    }

    return Array.from(map.values());
  }, [reviewedSuggestions, singleAgentResumeResult, multiAgentResumeResult]);

  const latestSingleAgentFinalReview = useMemo(
    () => pickLatestReview(finalReviewCandidates.filter(isSingleAgentReview)),
    [finalReviewCandidates],
  );

  const latestMultiAgentFinalReview = useMemo(
    () => pickLatestReview(finalReviewCandidates.filter(isMultiAgentReview)),
    [finalReviewCandidates],
  );

  const finalReviewSlots = useMemo(
    () => [
      latestSingleAgentFinalReview
        ? { key: "single-agent", label: "Latest Single-Agent result", review: latestSingleAgentFinalReview }
        : null,
      latestMultiAgentFinalReview
        ? { key: "multi-agent", label: "Latest Multi-Agent result", review: latestMultiAgentFinalReview }
        : null,
    ].filter(Boolean) as Array<{ key: string; label: string; review: AIReplyDraftRead }>,
    [latestSingleAgentFinalReview, latestMultiAgentFinalReview],
  );

  const singleAgentWorkflowSources = useMemo((): AIReplySource[] => {
    // Priority: reviewed_suggestion.sources_json > output_json.reviewed_suggestion.sources_json > output_json.reply_suggestion.sources_json
    if (singleAgentResumeResult?.reviewed_suggestion?.sources_json?.length) {
      return singleAgentResumeResult.reviewed_suggestion.sources_json;
    }
    const run = latestSingleAgentWorkflowRun;
    if (run?.output_json) {
      const output = run.output_json as Record<string, unknown>;
      const reviewedSuggestion = output.reviewed_suggestion as Record<string, unknown> | undefined;
      if (reviewedSuggestion?.sources_json) {
        return reviewedSuggestion.sources_json as AIReplySource[];
      }
      const replySuggestion = output.reply_suggestion as Record<string, unknown> | undefined;
      if (replySuggestion?.sources_json) {
        return replySuggestion.sources_json as AIReplySource[];
      }
    }
    return [];
  }, [singleAgentResumeResult, latestSingleAgentWorkflowRun]);

  const agentCards = useMemo(
    () => {
      const source = multiAgentResult ?? multiAgentResumeResult;
      return source ? buildAgentCards(source) : [];
    },
    [multiAgentResult, multiAgentResumeResult],
  );
  const displayedClassification = useMemo(() => {
    if (classification) {
      return classification;
    }

    if (multiAgentResult) {
      return multiAgentResult.triage_result.classification;
    }

    if (ticket) {
      return buildStoredClassification(ticket);
    }

    return null;
  }, [classification, multiAgentResult, ticket]);

  useEffect(() => {
    isMountedRef.current = true;

    return () => {
      isMountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    if (!sendMessageSuccess) {
      return;
    }

    const timer = setTimeout(() => {
      if (isMountedRef.current) {
        setSendMessageSuccess(null);
      }
    }, 3000);

    return () => clearTimeout(timer);
  }, [sendMessageSuccess]);

  async function loadSuggestions(currentTicketId: number) {
    setLoadingSuggestions(true);
    setSuggestionsErrorMessage(null);

    try {
      const suggestionData = await listTicketSuggestions(currentTicketId);
      if (!isMountedRef.current) {
        return;
      }
      setSuggestions(suggestionData);
    } catch {
      if (!isMountedRef.current) {
        return;
      }
      setSuggestionsErrorMessage("Unable to load AI suggestions right now.");
    } finally {
      if (isMountedRef.current) {
        setLoadingSuggestions(false);
      }
    }
  }

  async function loadReviewedSuggestions(currentTicketId: number) {
    try {
      const data = await listReviewedSuggestions(currentTicketId);
      if (!isMountedRef.current) {
        return;
      }
      setReviewedSuggestions(data);
    } catch {
      // Non-critical: Final Review will fall back to other sources.
    }
  }

  async function loadAgentRuns(currentTicketId: number) {
    setLoadingAgentRuns(true);
    setAgentRunsErrorMessage(null);

    try {
      const runData = await listTicketAgentRuns(currentTicketId);
      if (!isMountedRef.current) {
        return;
      }

      // Find the latest run of each type independently
      const latestRag = runData.find((r) => normalizeRunType(r.run_type) === "single_agent_rag") ?? null;
      const latestWorkflow = runData.find((r) => normalizeRunType(r.run_type) === "single_agent_workflow") ?? null;
      const latestMulti = runData.find((r) => normalizeRunType(r.run_type) === "multi_agent") ?? null;

      setLatestSingleAgentRagRun(latestRag);
      setLatestSingleAgentWorkflowRun(latestWorkflow);
      setLatestMultiAgentRun(latestMulti);

      // Restore single-agent workflow state only from its own run
      if (latestWorkflow) {
        if (latestWorkflow.status === "interrupted") {
          const output = latestWorkflow.output_json;
          if (output && typeof output === "object" && "run_id" in output) {
            setSingleAgentResult(output as unknown as AIWorkflowPendingReviewRead);
          }
        } else if (latestWorkflow.status === "completed") {
          // Clear pending if completed
          setSingleAgentResult(null);
          const output = latestWorkflow.output_json;
          if (output && typeof output === "object" && "reviewed_suggestion" in output) {
            setSingleAgentResumeResult(output as unknown as AIWorkflowProcessRead);
          }
        }
      }

      // Restore multi-agent state only from its own run
      if (latestMulti) {
        if (latestMulti.status === "interrupted" && isMultiAgentPendingReviewRead(latestMulti.output_json)) {
          setMultiAgentResult(latestMulti.output_json);
        } else if (latestMulti.status === "completed") {
          setMultiAgentResult(null);
          const output = latestMulti.output_json;
          if (output && typeof output === "object" && "reviewed_suggestion" in output) {
            setMultiAgentResumeResult(output as unknown as AIMultiAgentProcessRead);
          }
        }
      }
    } catch {
      if (!isMountedRef.current) {
        return;
      }
      setAgentRunsErrorMessage("Unable to load the agent run history right now.");
    } finally {
      if (isMountedRef.current) {
        setLoadingAgentRuns(false);
      }
    }
  }

  async function loadMessages() {
    if (!ticketId) {
      return;
    }
    try {
      const messageData = await listTicketMessages(ticketId);
      if (isMountedRef.current) {
        setMessages(messageData);
      }
    } catch {
      // Silently fail — messages will be stale but the page stays usable.
    }
  }

  async function loadAgentRunHistory(currentTicketId: number) {
    setAgentRunHistoryLoading(true);
    setAgentRunHistoryError(null);

    try {
      const page = await listTicketAgentRunsPage(currentTicketId, {
        run_type: agentRunTypeFilter === "all" ? undefined : agentRunTypeFilter,
        status: agentRunStatusFilter === "all" ? undefined : agentRunStatusFilter,
        limit: AGENT_RUN_PAGE_SIZE,
        offset: agentRunOffset,
      });

      if (!isMountedRef.current) {
        return;
      }

      setAgentRunHistory(page.items);
      setAgentRunTotal(page.total);
    } catch (error) {
      if (!isMountedRef.current) {
        return;
      }
      setAgentRunHistoryError("Unable to load agent run history.");
    } finally {
      if (isMountedRef.current) {
        setAgentRunHistoryLoading(false);
      }
    }
  }

  useEffect(() => {
    async function loadTicketDetail() {
      if (!Number.isFinite(ticketId)) {
        setErrorMessage("Invalid ticket id.");
        setLoading(false);
        setLoadingSuggestions(false);
        setLoadingAgentRuns(false);
        return;
      }

      setLoading(true);
      setErrorMessage(null);
      setAiActionErrorMessage(null);
      setReviewSuccessMessage(null);
      setMultiAgentSuccessMessage(null);
      setClassification(null);
      setMultiAgentResult(null);
      setMultiAgentResumeResult(null);
      setSingleAgentResult(null);
      setSingleAgentResumeResult(null);
      setLatestSingleAgentRagRun(null);
      setLatestSingleAgentWorkflowRun(null);
      setLatestMultiAgentRun(null);

      try {
        const [ticketData, messageData] = await Promise.all([
          getTicket(ticketId),
          listTicketMessages(ticketId),
        ]);

        if (!isMountedRef.current) {
          return;
        }

        setTicket(ticketData);
        setMessages(messageData);
        void Promise.all([loadSuggestions(ticketId), loadAgentRuns(ticketId), loadReviewedSuggestions(ticketId)]);
      } catch {
        if (!isMountedRef.current) {
          return;
        }
        setErrorMessage("Unable to load this ticket right now.");
        setLoadingSuggestions(false);
        setLoadingAgentRuns(false);
      } finally {
        if (isMountedRef.current) {
          setLoading(false);
        }
      }
    }

    void loadTicketDetail();
  }, [ticketId]);

  useEffect(() => {
    if (!latestSingleAgentSuggestion) {
      setReviewDraftContent("");
      setReviewRejectReason("");
      return;
    }

    setReviewDraftContent(latestSingleAgentSuggestion.final_content ?? latestSingleAgentSuggestion.suggested_content);
    setReviewRejectReason(latestSingleAgentSuggestion.reject_reason ?? "");
  }, [latestSingleAgentSuggestion?.id, latestSingleAgentSuggestion?.updated_at]);

  useEffect(() => {
    setAgentRunOffset(0);
  }, [agentRunTypeFilter, agentRunStatusFilter]);

  useEffect(() => {
    if (!ticketId) {
      return;
    }
    void loadAgentRunHistory(Number(ticketId));
  }, [ticketId, agentRunOffset, agentRunTypeFilter, agentRunStatusFilter]);

  const agentRunCurrentPage = Math.floor(agentRunOffset / AGENT_RUN_PAGE_SIZE) + 1;
  const agentRunTotalPages = Math.max(1, Math.ceil(agentRunTotal / AGENT_RUN_PAGE_SIZE));
  const canGoPreviousAgentRun = agentRunOffset > 0;
  const canGoNextAgentRun = agentRunOffset + AGENT_RUN_PAGE_SIZE < agentRunTotal;

  async function handleStatusChange(nextStatus: TicketStatus) {
    if (!ticket) {
      return;
    }

    setIsUpdatingStatus(true);
    setStatusErrorMessage(null);

    try {
      const updatedTicket = await updateTicket(ticket.id, { status: nextStatus });
      setTicket(updatedTicket);
    } catch {
      setStatusErrorMessage("Status update failed. Please try again.");
    } finally {
      setIsUpdatingStatus(false);
    }
  }

  async function handleClassifyTicket() {
    if (!ticket) {
      return;
    }

    setIsClassifying(true);
    setAiActionErrorMessage(null);
    setReviewSuccessMessage(null);
    setMultiAgentSuccessMessage(null);

    try {
      const result = await classifyTicketAI(ticket.id);
      setClassification(result);
      setTicket((current) =>
        current
          ? {
              ...current,
              category: result.category,
              priority: result.priority,
              sentiment: result.sentiment,
              ai_summary: result.summary,
              recommended_department: result.recommended_department,
            }
          : current,
      );
    } catch (error: unknown) {
      setAiActionErrorMessage(getApiErrorDetail(error, "AI classification failed. Please retry in a moment."));
    } finally {
      setIsClassifying(false);
    }
  }

  async function handleStartSingleAgentWorkflow() {
    if (!ticket) {
      return;
    }

    setIsStartingSingleAgent(true);
    setAiActionErrorMessage(null);
    setSuggestionsErrorMessage(null);
    setReviewSuccessMessage(null);
    setMultiAgentSuccessMessage(null);
    setSingleAgentReviewError(null);
    setSingleAgentReviewSuccess(null);
    setSingleAgentResumeResult(null);

    try {
      const result = await startSingleAgentProcess(ticket.id);
      setSingleAgentResult(result);
      setClassification(result.classification);
      setTicket(result.ticket);
      setSingleAgentReviewDraftContent(result.draft_reply.suggested_content);
      setSingleAgentReviewRejectReason("");
      setSingleAgentReviewSuccess("Single-agent workflow paused at human review. Review the draft below.");

      await loadAgentRuns(ticket.id);
    } catch (error: unknown) {
      setAiActionErrorMessage(getApiErrorDetail(error, "Single-agent workflow start failed. Please try again."));
    } finally {
      setIsStartingSingleAgent(false);
    }
  }

  async function handleSingleAgentApprove() {
    if (!ticket || !singleAgentResult) {
      return;
    }

    const finalContent = singleAgentReviewDraftContent.trim();
    if (!finalContent) {
      setSingleAgentReviewError("Edited final reply cannot be empty.");
      return;
    }

    setIsSubmittingSingleAgentReview(true);
    setSingleAgentReviewError(null);
    setSingleAgentReviewSuccess(null);

    try {
      const result = await resumeSingleAgentProcess(ticket.id, {
        action: "approve",
        run_id: singleAgentResult.run_id,
        final_content: finalContent,
      });
      setSingleAgentResumeResult(result);
      setSingleAgentReviewSuccess("Single-agent draft approved and finalized.");
      await Promise.all([loadSuggestions(ticket.id), loadAgentRuns(ticket.id), loadReviewedSuggestions(ticket.id)]);
    } catch (error: unknown) {
      setSingleAgentReviewError(getApiErrorDetail(error, "Approve action failed. Please try again."));
    } finally {
      setIsSubmittingSingleAgentReview(false);
    }
  }

  async function handleSingleAgentEdit() {
    if (!ticket || !singleAgentResult) {
      return;
    }

    const finalContent = singleAgentReviewDraftContent.trim();
    if (!finalContent) {
      setSingleAgentReviewError("Edited final reply cannot be empty.");
      return;
    }

    setIsSubmittingSingleAgentReview(true);
    setSingleAgentReviewError(null);
    setSingleAgentReviewSuccess(null);

    try {
      const result = await resumeSingleAgentProcess(ticket.id, {
        action: "edit",
        run_id: singleAgentResult.run_id,
        final_content: finalContent,
      });
      setSingleAgentResumeResult(result);
      setSingleAgentReviewSuccess("Single-agent draft saved with human edits.");
      await Promise.all([loadMessages(), loadSuggestions(ticket.id), loadAgentRuns(ticket.id), loadReviewedSuggestions(ticket.id)]);
    } catch (error: unknown) {
      setSingleAgentReviewError(getApiErrorDetail(error, "Edit action failed. Please try again."));
    } finally {
      setIsSubmittingSingleAgentReview(false);
    }
  }

  async function handleSingleAgentReject() {
    if (!ticket || !singleAgentResult) {
      return;
    }

    const rejectReason = singleAgentReviewRejectReason.trim();
    if (!rejectReason) {
      setSingleAgentReviewError("Please enter a reject reason before rejecting.");
      return;
    }

    setIsSubmittingSingleAgentReview(true);
    setSingleAgentReviewError(null);
    setSingleAgentReviewSuccess(null);

    try {
      const result = await resumeSingleAgentProcess(ticket.id, {
        action: "reject",
        run_id: singleAgentResult.run_id,
        reject_reason: rejectReason,
      });
      setSingleAgentResumeResult(result);
      setSingleAgentReviewSuccess("Single-agent draft rejected.");
      await Promise.all([loadSuggestions(ticket.id), loadAgentRuns(ticket.id), loadReviewedSuggestions(ticket.id)]);
    } catch (error: unknown) {
      setSingleAgentReviewError(getApiErrorDetail(error, "Reject action failed. Please try again."));
    } finally {
      setIsSubmittingSingleAgentReview(false);
    }
  }

  /* Backward-compat handlers for reviewing existing AISuggestion records via the review API */
  async function handleApproveSuggestion() {
    if (!latestSingleAgentSuggestion) {
      return;
    }

    const finalContent = reviewDraftContent.trim();
    if (!finalContent) {
      setAiActionErrorMessage("Edited final reply cannot be empty.");
      return;
    }

    setIsSubmittingReview(true);
    setAiActionErrorMessage(null);
    setSuggestionsErrorMessage(null);
    setReviewSuccessMessage(null);

    try {
      const reviewed = await approveSuggestion(latestSingleAgentSuggestion.id, { final_content: finalContent });
      setSuggestions((current) => upsertSuggestion(current, reviewed));
      setReviewSuccessMessage("AI draft approved and locked as the final reviewed reply.");
      await Promise.all([loadSuggestions(ticketId), loadReviewedSuggestions(ticketId), loadAgentRuns(ticketId)]);
    } catch (error: unknown) {
      const status = (error as { response?: { status?: number } })?.response?.status;
      if (status === 403) {
        setAiActionErrorMessage("当前角色无审核权限。");
      } else {
        setAiActionErrorMessage(getApiErrorDetail(error, "Approve action failed. Please refresh and try again."));
      }
    } finally {
      setIsSubmittingReview(false);
    }
  }

  async function handleEditSuggestion() {
    if (!latestSingleAgentSuggestion) {
      return;
    }

    const finalContent = reviewDraftContent.trim();
    if (!finalContent) {
      setAiActionErrorMessage("Edited final reply cannot be empty.");
      return;
    }

    setIsSubmittingReview(true);
    setAiActionErrorMessage(null);
    setSuggestionsErrorMessage(null);
    setReviewSuccessMessage(null);

    try {
      const reviewed = await editSuggestion(latestSingleAgentSuggestion.id, { final_content: finalContent });
      setSuggestions((current) => upsertSuggestion(current, reviewed));
      setReviewSuccessMessage("AI draft saved with human edits.");
      void loadMessages();
      void loadReviewedSuggestions(ticketId);
    } catch (error: unknown) {
      const status = (error as { response?: { status?: number } })?.response?.status;
      if (status === 403) {
        setAiActionErrorMessage("当前角色无审核权限。");
      } else {
        setAiActionErrorMessage(getApiErrorDetail(error, "Edit action failed. Please try again."));
      }
    } finally {
      setIsSubmittingReview(false);
    }
  }

  async function handleRejectSuggestion() {
    if (!latestSingleAgentSuggestion) {
      return;
    }

    const rejectReason = reviewRejectReason.trim();
    if (!rejectReason) {
      setAiActionErrorMessage("Please enter a reject reason before rejecting the draft.");
      return;
    }

    setIsSubmittingReview(true);
    setAiActionErrorMessage(null);
    setSuggestionsErrorMessage(null);
    setReviewSuccessMessage(null);

    try {
      const reviewed = await rejectSuggestion(latestSingleAgentSuggestion.id, { reject_reason: rejectReason });
      setSuggestions((current) => upsertSuggestion(current, reviewed));
      setReviewSuccessMessage("AI draft rejected and the review reason has been recorded.");
      await Promise.all([loadSuggestions(ticketId), loadReviewedSuggestions(ticketId), loadAgentRuns(ticketId)]);
    } catch (error: unknown) {
      const status = (error as { response?: { status?: number } })?.response?.status;
      if (status === 403) {
        setAiActionErrorMessage("当前角色无审核权限。");
      } else {
        setAiActionErrorMessage(getApiErrorDetail(error, "Reject action failed. Please try again."));
      }
    } finally {
      setIsSubmittingReview(false);
    }
  }

  async function handleSendMessage() {
    if (!ticket) {
      return;
    }

    const trimmedContent = messageContent.trim();
    if (!trimmedContent) {
      setSendMessageError("Message content cannot be empty.");
      return;
    }

    setIsSendingMessage(true);
    setSendMessageError(null);
    setSendMessageSuccess(null);

    try {
      await addTicketMessage(ticket.id, {
        sender_type: messageSenderType,
        content: trimmedContent,
      });
      setMessageContent("");
      setSendMessageSuccess("Message sent successfully.");
      const messageData = await listTicketMessages(ticket.id);
      if (isMountedRef.current) {
        setMessages(messageData);
      }
    } catch {
      setSendMessageError("Failed to send message. Please try again.");
    } finally {
      if (isMountedRef.current) {
        setIsSendingMessage(false);
      }
    }
  }

  function handleClearMessage() {
    setMessageContent("");
    setSendMessageError(null);
    setSendMessageSuccess(null);
  }

  async function handleRunMultiAgent() {
    if (!ticket) {
      return;
    }

    setIsRunningMultiAgent(true);
    setAgentRunsErrorMessage(null);
    setAiActionErrorMessage(null);
    setReviewSuccessMessage(null);
    setMultiAgentSuccessMessage(null);
    setMultiAgentReviewError(null);
    setMultiAgentReviewSuccess(null);
    setMultiAgentResumeResult(null);
    setMultiAgentReviewDraftContent("");
    setMultiAgentReviewRejectReason("");

    try {
      const result = await startMultiAgentProcess(ticket.id);
      setMultiAgentResult(result);
      setClassification(result.triage_result.classification);
      setTicket(result.ticket);
      setMultiAgentReviewDraftContent(result.draft_reply.suggested_content);
      setMultiAgentSuccessMessage(
        "Multi-agent analysis completed and paused at human review. The latest agent outputs are shown below.",
      );

      await Promise.all([loadSuggestions(ticket.id), loadAgentRuns(ticket.id), loadReviewedSuggestions(ticket.id)]);
    } catch (error: unknown) {
      setAgentRunsErrorMessage(getApiErrorDetail(error, "Multi-agent analysis failed. Please try again."));
    } finally {
      setIsRunningMultiAgent(false);
    }
  }

  async function handleMultiAgentApprove() {
    if (!ticket || !multiAgentResult) {
      return;
    }

    const finalContent = multiAgentReviewDraftContent.trim();
    if (!finalContent) {
      setMultiAgentReviewError("Edited final reply cannot be empty.");
      return;
    }

    setIsSubmittingMultiAgentReview(true);
    setMultiAgentReviewError(null);
    setMultiAgentReviewSuccess(null);

    try {
      const result = await resumeMultiAgentProcess(ticket.id, {
        action: "approve",
        run_id: multiAgentResult.run_id,
        final_content: finalContent,
      });
      setMultiAgentResumeResult(result);
      setMultiAgentReviewSuccess("Multi-agent reply approved and finalized.");
      await Promise.all([loadSuggestions(ticket.id), loadAgentRuns(ticket.id), loadReviewedSuggestions(ticket.id)]);
    } catch (error: unknown) {
      setMultiAgentReviewError(getApiErrorDetail(error, "Approve action failed. Please try again."));
    } finally {
      setIsSubmittingMultiAgentReview(false);
    }
  }

  async function handleMultiAgentEdit() {
    if (!ticket || !multiAgentResult) {
      return;
    }

    const finalContent = multiAgentReviewDraftContent.trim();
    if (!finalContent) {
      setMultiAgentReviewError("Edited final reply cannot be empty.");
      return;
    }

    setIsSubmittingMultiAgentReview(true);
    setMultiAgentReviewError(null);
    setMultiAgentReviewSuccess(null);

    try {
      const result = await resumeMultiAgentProcess(ticket.id, {
        action: "edit",
        run_id: multiAgentResult.run_id,
        final_content: finalContent,
      });
      setMultiAgentResumeResult(result);
      setMultiAgentReviewSuccess("Multi-agent reply saved with human edits.");
      await Promise.all([loadMessages(), loadSuggestions(ticket.id), loadAgentRuns(ticket.id), loadReviewedSuggestions(ticket.id)]);
    } catch (error: unknown) {
      setMultiAgentReviewError(getApiErrorDetail(error, "Edit action failed. Please try again."));
    } finally {
      setIsSubmittingMultiAgentReview(false);
    }
  }

  async function handleMultiAgentReject() {
    if (!ticket || !multiAgentResult) {
      return;
    }

    const rejectReason = multiAgentReviewRejectReason.trim();
    if (!rejectReason) {
      setMultiAgentReviewError("Please enter a reject reason before rejecting.");
      return;
    }

    setIsSubmittingMultiAgentReview(true);
    setMultiAgentReviewError(null);
    setMultiAgentReviewSuccess(null);

    try {
      const result = await resumeMultiAgentProcess(ticket.id, {
        action: "reject",
        run_id: multiAgentResult.run_id,
        reject_reason: rejectReason,
      });
      setMultiAgentResumeResult(result);
      setMultiAgentReviewSuccess("Multi-agent reply rejected.");
      await Promise.all([loadSuggestions(ticket.id), loadAgentRuns(ticket.id), loadReviewedSuggestions(ticket.id)]);
    } catch (error: unknown) {
      setMultiAgentReviewError(getApiErrorDetail(error, "Reject action failed. Please try again."));
    } finally {
      setIsSubmittingMultiAgentReview(false);
    }
  }

  return (
    <section className="page-stack">
      <div className="section-hero">
        <div>
          <p className="panel-tag">Steps 30-31 · AI Review + Multi-Agent</p>
          <h3>Case record, approval desk, and agent execution trail</h3>
          <p>
            Review customer context, manage AI reply approval, and run the fixed-sequence
            multi-agent workflow with a visible audit trail for demo-ready explainability.
          </p>
        </div>
        <Link to="/tickets" className="ghost-button ghost-button--link">
          Back to list
        </Link>
      </div>

      {loading ? (
        <article className="panel">
          <p className="panel-state">Loading ticket detail...</p>
        </article>
      ) : null}
      {errorMessage ? (
        <article className="panel">
          <p className="form-error">{errorMessage}</p>
        </article>
      ) : null}

      {!loading && !errorMessage && ticket ? (
        <>
          <section className="content-grid content-grid--detail">
            <article className="panel panel--feature">
              <div className="ticket-detail-header">
                <div>
                  <p className="panel-tag">Case #{ticket.id}</p>
                  <h3>{ticket.title}</h3>
                </div>
                <span className={`badge badge--status badge--${ticket.status}`}>
                  {toLabel(ticket.status)}
                </span>
              </div>

              <p className="ticket-description">{ticket.content}</p>

              <div className="meta-grid">
                <div className="meta-card">
                  <span className="meta-card__label">Customer</span>
                  <strong>{ticket.customer_name}</strong>
                  <span>{ticket.customer_email}</span>
                </div>
                <div className="meta-card">
                  <span className="meta-card__label">Category</span>
                  <strong>{toLabel(ticket.category)}</strong>
                  <span>Priority: {toLabel(ticket.priority)}</span>
                </div>
                <div className="meta-card">
                  <span className="meta-card__label">Sentiment</span>
                  <strong>{toLabel(ticket.sentiment)}</strong>
                  <span>Source: {ticket.source}</span>
                </div>
                <div className="meta-card">
                  <span className="meta-card__label">Routing</span>
                  <strong>{ticket.recommended_department ?? "Pending"}</strong>
                  <span>Assigned to: {ticket.assigned_to ?? "Unassigned"}</span>
                </div>
              </div>
            </article>

            <article className="panel">
              <div className="panel-heading">
                <div>
                  <p className="panel-tag">Workflow</p>
                  <h3>Status control</h3>
                </div>
              </div>

              <label className="field">
                <span>Update status</span>
                <select
                  value={ticket.status}
                  onChange={(event) => handleStatusChange(event.target.value as TicketStatus)}
                  disabled={isUpdatingStatus}
                >
                  {TICKET_STATUSES.map((value) => (
                    <option key={value} value={value}>
                      {toLabel(value)}
                    </option>
                  ))}
                </select>
              </label>

              {statusErrorMessage ? <p className="form-error">{statusErrorMessage}</p> : null}

              <div className="detail-stack">
                <div className="detail-row">
                  <span>Created</span>
                  <strong>{formatDateTime(ticket.created_at)}</strong>
                </div>
                <div className="detail-row">
                  <span>Last updated</span>
                  <strong>{formatDateTime(ticket.updated_at)}</strong>
                </div>
                <div className="detail-row">
                  <span>Closed at</span>
                  <strong>{formatDateTime(ticket.closed_at)}</strong>
                </div>
                <div className="detail-row">
                  <span>AI summary</span>
                  <strong>{ticket.ai_summary ?? "Not generated yet"}</strong>
                </div>
              </div>
            </article>
          </section>

          <article className="panel">
            <div className="panel-heading">
              <div>
                <p className="panel-tag">Final Review</p>
                <h3>Final human-reviewed replies</h3>
              </div>
            </div>

            {!finalReviewSlots.length ? (
              <p className="panel-state">No final human-reviewed reply yet.</p>
            ) : (
              <div className="ai-panel-stack">
                {finalReviewSlots.map((slot) => (
                  <article key={slot.key} className="suggestion-card">
                    <div className="suggestion-card__header">
                      <div>
                        <strong>{slot.label}</strong>
                        <span>
                          Reviewed at{" "}
                          {formatDateTime(slot.review.reviewed_at)}
                        </span>
                      </div>
                      <span
                        className={`badge badge--suggestion-status badge--${slot.review.status}`}
                      >
                        {toLabel(slot.review.status)}
                      </span>
                    </div>
                    <div className="detail-stack detail-stack--compact">
                      <div className="detail-row">
                        <span>Source</span>
                        <strong>{sourceWorkflowLabel(normalizeSourceWorkflow(slot.review.source_workflow))}</strong>
                      </div>
                      <div className="detail-row">
                        <span>Reviewer</span>
                        <strong>
                          {slot.review.reviewed_by
                            ? `User #${slot.review.reviewed_by}`
                            : "Not available"}
                        </strong>
                      </div>
                      <div className="detail-row">
                        <span>Run ID</span>
                        <strong className="meta-card__value--mono">
                          {slot.review.source_run_id ?? "N/A"}
                        </strong>
                      </div>
                    </div>
                    {slot.review.final_content ? (
                      <div className="review-outcome__block">
                        <span>Final approved content</span>
                        <p>{slot.review.final_content}</p>
                      </div>
                    ) : null}
                    {slot.review.reject_reason ? (
                      <div className="review-outcome__block" style={{ borderLeftColor: "var(--color-danger)" }}>
                        <span>Reject reason</span>
                        <p>{slot.review.reject_reason}</p>
                      </div>
                    ) : null}
                    <details className="json-disclosure" style={{ marginTop: "0.5rem" }}>
                      <summary>View original AI draft</summary>
                      <p className="suggestion-card__content suggestion-card__content--original">
                        {slot.review.suggested_content}
                      </p>
                    </details>
                  </article>
                ))}
              </div>
            )}
          </article>

          <section className="content-grid content-grid--detail">
            <article className="panel panel--feature">
              <div className="panel-heading">
                <div>
                  <p className="panel-tag">Single-Agent RAG</p>
                  <h3>Single-agent reply draft</h3>
                </div>

                <div className="panel-heading__actions">
                  <button
                    type="button"
                    className="ghost-button"
                    aria-expanded={isSingleAgentPanelExpanded}
                    onClick={() => setIsSingleAgentPanelExpanded((value) => !value)}
                  >
                    {isSingleAgentPanelExpanded ? "Collapse" : "Expand"}
                  </button>

                  <button
                    type="button"
                    className="primary-button"
                    onClick={handleStartSingleAgentWorkflow}
                    disabled={isStartingSingleAgent}
                  >
                    {isStartingSingleAgent ? "Starting..." : "Generate single-agent draft"}
                  </button>
                </div>
              </div>

              {isSingleAgentPanelExpanded ? (
                <>
              {aiActionErrorMessage ? <p className="form-error">{aiActionErrorMessage}</p> : null}
              {loadingSuggestions ? <p className="panel-state">Loading AI suggestions...</p> : null}
              {suggestionsErrorMessage ? <p className="form-error">{suggestionsErrorMessage}</p> : null}

              {/* Empty state — no workflow result and no existing suggestion */}
              {!loadingSuggestions && !suggestionsErrorMessage && !singleAgentResult && !singleAgentResumeResult && !latestSingleAgentSuggestion ? (
                <p className="panel-state">
                  No AI reply draft exists for this ticket yet. Generate one to start the review
                  workflow.
                </p>
              ) : null}

              {/* Workflow pending review state */}
              {singleAgentResult ? (
                <div className="ai-panel-stack">
                  {/* Workflow summary grid (mirrors Multi-Agent) */}
                  <div className="multi-agent-summary-grid">
                    <article className="meta-card">
                      <span className="meta-card__label">Workflow status</span>
                      <strong>{toLabel(singleAgentResult.status)}</strong>
                      <span>
                        Pending node: {toLabel(singleAgentResult.pending_node)}
                      </span>
                    </article>
                    <article className="meta-card">
                      <span className="meta-card__label">Run ID</span>
                      <strong className="meta-card__value--mono">{singleAgentResult.run_id}</strong>
                      <span>Thread ID: {singleAgentResult.thread_id}</span>
                    </article>
                    <article className="meta-card">
                      <span className="meta-card__label">Confidence</span>
                      <strong>{formatConfidence(singleAgentResult.confidence)}</strong>
                      <span>{singleAgentResult.sources.length} sources</span>
                    </article>
                    <article className="meta-card">
                      <span className="meta-card__label">Knowledge hits</span>
                      <strong>{singleAgentResult.knowledge_hits.length}</strong>
                      <span>{singleAgentResult.similar_tickets.length} similar tickets</span>
                    </article>
                  </div>

                  {/* Draft reply card */}
                  <article className="suggestion-card">
                    <div className="suggestion-card__header">
                      <div>
                        <strong>Draft reply</strong>
                        <span>
                          Confidence {formatConfidence(singleAgentResult.draft_reply.confidence)}
                        </span>
                      </div>
                      <span className="badge badge--suggestion-status badge--draft">
                        Pending Review
                      </span>
                    </div>
                    <p className="suggestion-card__label">Original AI draft</p>
                    <p className="suggestion-card__content">{singleAgentResult.draft_reply.suggested_content}</p>
                    <div className="detail-stack detail-stack--compact">
                      <div className="detail-row">
                        <span>Reasoning summary</span>
                        <strong>{singleAgentResult.draft_reply.reasoning_summary ?? "Not provided"}</strong>
                      </div>
                    </div>
                  </article>

                  <RagSourcesPanel sources={singleAgentResult.sources} />

                  {/* Review form */}
                  <article className="panel panel--subtle">
                    <div className="panel-heading">
                      <div>
                        <p className="panel-tag">Human Review</p>
                        <h3>Approve, edit, or reject</h3>
                      </div>
                    </div>

                    {singleAgentReviewSuccess ? (
                      <p className="form-success">{singleAgentReviewSuccess}</p>
                    ) : null}
                    {singleAgentReviewError ? (
                      <p className="form-error">{singleAgentReviewError}</p>
                    ) : null}

                    {canReview ? (
                      <div className="review-stack">
                        <label className="field">
                          <span>Editable final reply</span>
                          <textarea
                            value={singleAgentReviewDraftContent}
                            onChange={(event) => setSingleAgentReviewDraftContent(event.target.value)}
                            rows={7}
                          />
                        </label>

                        <label className="field">
                          <span>Reject reason</span>
                          <textarea
                            value={singleAgentReviewRejectReason}
                            onChange={(event) => setSingleAgentReviewRejectReason(event.target.value)}
                            placeholder="Explain why the AI draft is not safe or accurate enough."
                            rows={3}
                          />
                        </label>

                        <div className="review-actions">
                          <button
                            type="button"
                            className="primary-button"
                            onClick={handleSingleAgentApprove}
                            disabled={isSubmittingSingleAgentReview}
                          >
                            {isSubmittingSingleAgentReview ? "Saving..." : "Approve current reply"}
                          </button>
                          <button
                            type="button"
                            className="ghost-button"
                            onClick={handleSingleAgentEdit}
                            disabled={isSubmittingSingleAgentReview}
                          >
                            Save edited approval
                          </button>
                          <button
                            type="button"
                            className="ghost-button ghost-button--danger"
                            onClick={handleSingleAgentReject}
                            disabled={isSubmittingSingleAgentReview}
                          >
                            Reject draft
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="review-stack">
                        <p>当前角色仅可查看 AI 建议，不能执行审核操作。</p>
                      </div>
                    )}
                  </article>
                </div>
              ) : null}

              {/* Workflow completed state (resume result) */}
              {!singleAgentResult && singleAgentResumeResult ? (
                <div className="ai-panel-stack">
                  <div className="multi-agent-summary-grid">
                    <article className="meta-card">
                      <span className="meta-card__label">Workflow status</span>
                      <strong>Completed</strong>
                      <span>Workflow finalized</span>
                    </article>
                    <article className="meta-card">
                      <span className="meta-card__label">Run ID</span>
                      <strong className="meta-card__value--mono">
                        {latestSingleAgentWorkflowRun?.run_id ?? "N/A"}
                      </strong>
                      <span>Status: {toLabel(latestSingleAgentWorkflowRun?.status ?? "completed")}</span>
                    </article>
                  </div>

                  <article className="panel panel--subtle">
                    <div className="panel-heading">
                      <div>
                        <p className="panel-tag">Review Complete</p>
                        <h3>Single-agent workflow finalized</h3>
                      </div>
                      <span className="badge badge--score">
                        {singleAgentResumeResult.review_decision
                          ? toLabel(String((singleAgentResumeResult.review_decision as Record<string, unknown>).action ?? "completed"))
                          : "Completed"}
                      </span>
                    </div>

                    {singleAgentResumeResult.reviewed_suggestion ? (
                      <div className="panel-actions">
                        <div className="agent-card__summary">
                          <span>Status</span>
                          <strong>{singleAgentResumeResult.reviewed_suggestion.status}</strong>
                          <p>{singleAgentResumeResult.reviewed_suggestion.final_content
                            ?? singleAgentResumeResult.reviewed_suggestion.suggested_content}</p>
                        </div>
                      </div>
                    ) : null}

                    {singleAgentReviewSuccess ? (
                      <p className="form-success" style={{ marginTop: "0.5rem" }}>
                        {singleAgentReviewSuccess}
                      </p>
                    ) : null}

                    <RagSourcesPanel sources={singleAgentWorkflowSources} />
                  </article>
                </div>
              ) : null}

              {/* Fallback: display existing AISuggestion from DB (backward compat for previously-reviewed suggestions) */}
              {!singleAgentResult && !singleAgentResumeResult && !loadingSuggestions && latestSingleAgentSuggestion ? (
                <div className="ai-panel-stack">
                  <article className="suggestion-card">
                    <div className="suggestion-card__header">
                      <div>
                        <strong>Suggestion #{latestSingleAgentSuggestion.id}</strong>
                        <span>
                          Created {formatDateTime(latestSingleAgentSuggestion.created_at)} · Updated{" "}
                          {formatDateTime(latestSingleAgentSuggestion.updated_at)}
                        </span>
                      </div>
                      <div className="suggestion-card__badges">
                        <span
                          className={`badge badge--suggestion-status badge--${latestSingleAgentSuggestion.status}`}
                        >
                          {toLabel(latestSingleAgentSuggestion.status)}
                        </span>
                        <span className="badge badge--score">
                          Confidence {formatConfidence(latestSingleAgentSuggestion.confidence)}
                        </span>
                      </div>
                    </div>

                    {latestSingleAgentSuggestion.status === "draft" ? (
                      <>
                        <p className="suggestion-card__label">Original AI draft</p>
                        <p className="suggestion-card__content">{latestSingleAgentSuggestion.suggested_content}</p>
                      </>
                    ) : (
                      <>
                        <p className="suggestion-card__label">Final reviewed reply</p>
                        <p className="suggestion-card__content suggestion-card__content--final">
                          {latestSingleAgentSuggestion.final_content ?? latestSingleAgentSuggestion.suggested_content}
                        </p>
                        {latestSingleAgentSuggestion.final_content && latestSingleAgentSuggestion.final_content !== latestSingleAgentSuggestion.suggested_content ? (
                          <details className="json-disclosure" style={{ marginTop: "0.5rem" }}>
                            <summary>View Original AI draft (for comparison)</summary>
                            <p className="suggestion-card__content suggestion-card__content--original">
                              {latestSingleAgentSuggestion.suggested_content}
                            </p>
                          </details>
                        ) : null}
                      </>
                    )}

                    <div className="detail-stack detail-stack--compact">
                      <div className="detail-row">
                        <span>Reasoning summary</span>
                        <strong>{latestSingleAgentSuggestion.reasoning_summary ?? "Not provided"}</strong>
                      </div>
                      <div className="detail-row">
                        <span>Review outcome</span>
                        <strong>
                          {latestSingleAgentSuggestion.status === "draft"
                            ? "Pending human review"
                            : `Reviewed at ${formatDateTime(latestSingleAgentSuggestion.reviewed_at)}`}
                        </strong>
                      </div>
                    </div>
                  </article>

                  <RagSourcesPanel sources={latestSingleAgentSuggestion.sources_json} />

                  <article className="panel panel--subtle">
                    <div className="panel-heading">
                      <div>
                        <p className="panel-tag">Human Review</p>
                        <h3>Approve, edit, or reject</h3>
                      </div>
                    </div>

                    {latestSingleAgentSuggestion.status === "draft" && canReview ? (
                      <div className="review-stack">
                        <label className="field">
                          <span>Editable final reply</span>
                          <textarea
                            value={reviewDraftContent}
                            onChange={(event) => setReviewDraftContent(event.target.value)}
                            rows={7}
                          />
                        </label>

                        <label className="field">
                          <span>Reject reason</span>
                          <textarea
                            value={reviewRejectReason}
                            onChange={(event) => setReviewRejectReason(event.target.value)}
                            placeholder="Explain why the AI draft is not safe or accurate enough."
                            rows={3}
                          />
                        </label>

                        <div className="review-actions">
                          <button
                            type="button"
                            className="primary-button"
                            onClick={handleApproveSuggestion}
                            disabled={isSubmittingReview}
                          >
                            {isSubmittingReview ? "Saving..." : "Approve current reply"}
                          </button>
                          <button
                            type="button"
                            className="ghost-button"
                            onClick={handleEditSuggestion}
                            disabled={isSubmittingReview}
                          >
                            Save edited approval
                          </button>
                          <button
                            type="button"
                            className="ghost-button ghost-button--danger"
                            onClick={handleRejectSuggestion}
                            disabled={isSubmittingReview}
                          >
                            Reject draft
                          </button>
                        </div>
                      </div>
                    ) : latestSingleAgentSuggestion.status === "draft" && !canReview ? (
                      <div className="review-stack">
                        <p>当前角色仅可查看 AI 建议，不能执行审核操作。</p>
                      </div>
                    ) : (
                      <div className="review-outcome">
                        <div className="detail-stack detail-stack--compact">
                          <div className="detail-row">
                            <span>Reviewed at</span>
                            <strong>{formatDateTime(latestSingleAgentSuggestion.reviewed_at)}</strong>
                          </div>
                          <div className="detail-row">
                            <span>Reviewer</span>
                            <strong>
                              {latestSingleAgentSuggestion.reviewed_by
                                ? `User #${latestSingleAgentSuggestion.reviewed_by}`
                                : "Not available"}
                            </strong>
                          </div>
                        </div>

                        {latestSingleAgentSuggestion.final_content ? (
                          <div className="review-outcome__block">
                            <span>Final approved content</span>
                            <p>{latestSingleAgentSuggestion.final_content}</p>
                          </div>
                        ) : null}

                        {latestSingleAgentSuggestion.reject_reason ? (
                          <div className="review-outcome__block">
                            <span>Reject reason</span>
                            <p>{latestSingleAgentSuggestion.reject_reason}</p>
                          </div>
                        ) : null}
                      </div>
                    )}
                  </article>
                </div>
              ) : null}
                </> ) : (
                  <p className="panel-state panel-state--compact">
                    Single-agent details are collapsed.
                  </p>
                )}
            </article>

            <article className="panel">
              <div className="panel-heading">
                <div>
                  <p className="panel-tag">AI Classification</p>
                  <h3>Triage snapshot</h3>
                </div>
                <button
                  type="button"
                  className="ghost-button"
                  onClick={handleClassifyTicket}
                  disabled={isClassifying}
                >
                  {isClassifying ? "Classifying..." : "AI classify"}
                </button>
              </div>

              {displayedClassification ? (
                <div className="classification-grid">
                  <div className="meta-card">
                    <span className="meta-card__label">Category</span>
                    <strong>{toLabel(displayedClassification.category)}</strong>
                  </div>
                  <div className="meta-card">
                    <span className="meta-card__label">Priority</span>
                    <strong>{toLabel(displayedClassification.priority)}</strong>
                  </div>
                  <div className="meta-card">
                    <span className="meta-card__label">Sentiment</span>
                    <strong>{toLabel(displayedClassification.sentiment)}</strong>
                  </div>
                  <div className="meta-card">
                    <span className="meta-card__label">Department</span>
                    <strong>{displayedClassification.recommended_department ?? "Pending"}</strong>
                  </div>
                </div>
              ) : (
                <p className="panel-state">
                  No AI classification has been generated for this ticket yet.
                </p>
              )}

              {displayedClassification ? (
                <div className="detail-stack">
                  <div className="detail-row">
                    <span>AI summary</span>
                    <strong>{displayedClassification.summary}</strong>
                  </div>
                  <div className="detail-row">
                    <span>Need human review</span>
                    <strong>
                      {typeof displayedClassification.need_human === "boolean"
                        ? displayedClassification.need_human
                          ? "Yes"
                          : "No"
                        : "Stored ticket snapshot does not include this flag."}
                    </strong>
                  </div>
                </div>
              ) : null}
            </article>
          </section>

          <article className="panel panel--feature">
            <div className="panel-heading">
              <div>
                <p className="panel-tag">AI Agent Timeline</p>
                <h3>Multi-agent execution process</h3>
              </div>
              <div className="panel-heading__actions">
                <button
                  type="button"
                  className="ghost-button"
                  aria-expanded={isMultiAgentPanelExpanded}
                  onClick={() => setIsMultiAgentPanelExpanded((value) => !value)}
                >
                  {isMultiAgentPanelExpanded ? "Collapse" : "Expand"}
                </button>
                <button
                  type="button"
                  className="primary-button"
                  onClick={handleRunMultiAgent}
                  disabled={isRunningMultiAgent}
                >
                  {isRunningMultiAgent ? "Running..." : "Run multi-agent analysis"}
                </button>
              </div>
            </div>

            {isMultiAgentPanelExpanded ? (
            <>

            <p className="helper-copy">
              This runs the fixed-sequence workflow: Supervisor, Triage, Knowledge, Similar Case,
              Reply, Risk, Workflow, then pause at human review.
            </p>

            {multiAgentSuccessMessage ? <p className="form-success">{multiAgentSuccessMessage}</p> : null}
            {agentRunsErrorMessage ? <p className="form-error">{agentRunsErrorMessage}</p> : null}
            {loadingAgentRuns ? <p className="panel-state">Loading multi-agent runs...</p> : null}

            {!loadingAgentRuns && !agentRunsErrorMessage && !multiAgentResult && !multiAgentResumeResult ? (
              <p className="panel-state">
                No multi-agent run has been recorded for this ticket yet. Start one to inspect the
                execution trail and each agent output.
              </p>
            ) : null}

            {(multiAgentResult || multiAgentResumeResult) ? (
              <div className="multi-agent-stack">
                <div className="multi-agent-summary-grid">
                  <article className="meta-card">
                    <span className="meta-card__label">Workflow status</span>
                    <strong>{toLabel(multiAgentResult?.status ?? "completed")}</strong>
                    <span>
                      {multiAgentResult
                        ? `Pending node: ${toLabel(multiAgentResult.pending_node)}`
                        : "Workflow finalized"}
                    </span>
                  </article>
                  <article className="meta-card">
                    <span className="meta-card__label">Run ID</span>
                    <strong className="meta-card__value--mono">
                      {multiAgentResult?.run_id ?? latestMultiAgentRun?.run_id ?? "N/A"}
                    </strong>
                    <span>
                      {multiAgentResult
                        ? `Thread ID: ${multiAgentResult.thread_id}`
                        : `Status: ${toLabel(latestMultiAgentRun?.status ?? "completed")}`}
                    </span>
                  </article>
                  <article className="meta-card">
                    <span className="meta-card__label">Audit entries</span>
                    <strong>
                      {(multiAgentResult ?? multiAgentResumeResult)?.audit_trail.length ?? 0}
                    </strong>
                    <span>
                      {multiAgentResult
                        ? `Draft confidence: ${formatConfidence(multiAgentResult.confidence)}`
                        : "Workflow completed"}
                    </span>
                  </article>
                  <article className="meta-card">
                    <span className="meta-card__label">Persisted run</span>
                    <strong>{latestMultiAgentRun ? toLabel(latestMultiAgentRun.status) : "Pending sync"}</strong>
                    <span>
                      {latestMultiAgentRun
                        ? `Updated ${formatDateTime(latestMultiAgentRun.updated_at)}`
                        : "Waiting for run-log refresh"}
                    </span>
                  </article>
                </div>

                <div className="multi-agent-card-grid">
                  {agentCards.map((card) => {
                    const source = multiAgentResult ?? multiAgentResumeResult;
                    const auditEntry = source ? findAuditEntry(source.audit_trail, card.agentName) : null;
                    const highlights = buildAgentHighlights(card.agentName, card.data);

                    return (
                      <article key={card.agentName} className="agent-card">
                        <div className="agent-card__header">
                          <div>
                            <p className="panel-tag">{card.title}</p>
                            <h3>{card.description}</h3>
                          </div>
                          <span className="badge badge--score">
                            {auditEntry ? toLabel(auditEntry.status) : "Recorded"}
                          </span>
                        </div>

                        {auditEntry ? (
                          <div className="agent-card__summary">
                            <span>Action</span>
                            <strong>{auditEntry.action}</strong>
                            <p>{auditEntry.output_summary}</p>
                          </div>
                        ) : null}

                        {highlights.length > 0 ? (
                          <div className="agent-highlight-grid">
                            {highlights.map((item) => (
                              <div key={`${card.agentName}-${item.label}`} className="agent-highlight-card">
                                <span>{item.label}</span>
                                <strong>{item.value}</strong>
                              </div>
                            ))}
                          </div>
                        ) : null}

                        <details className="json-disclosure">
                          <summary>View raw payload</summary>
                          <pre className="json-block">{formatJson(card.data)}</pre>
                        </details>
                      </article>
                    );
                  })}
                </div>

                <article className="panel panel--subtle">
                  <div className="panel-heading">
                    <div>
                      <p className="panel-tag">Audit Trail</p>
                      <h3>Execution timeline</h3>
                    </div>
                  </div>

                  <div className="audit-trail-list">
                    {((multiAgentResult ?? multiAgentResumeResult)?.audit_trail ?? []).map((entry, index) => (
                      <article key={`${entry.agent_name}-${entry.timestamp}-${index}`} className="audit-entry">
                        <div className="audit-entry__step">{index + 1}</div>
                        <div className="audit-entry__body">
                          <div className="audit-entry__header">
                            <strong>{entry.agent_name}</strong>
                            <span>
                              {toLabel(entry.status)} · {formatDateTime(entry.timestamp)}
                            </span>
                          </div>
                          <p className="audit-entry__action">{entry.action}</p>
                          <p>{entry.output_summary}</p>
                        </div>
                      </article>
                    ))}
                  </div>
                </article>

                {multiAgentResumeResult ? (
                  <article className="panel panel--subtle">
                    <div className="panel-heading">
                      <div>
                        <p className="panel-tag">Review Complete</p>
                        <h3>Multi-agent workflow finalized</h3>
                      </div>
                      <span className="badge badge--score">
                        {multiAgentResumeResult.review_decision
                          ? toLabel(String(multiAgentResumeResult.review_decision.action ?? "completed"))
                          : "Completed"}
                      </span>
                    </div>

                    {multiAgentResumeResult.reviewed_suggestion ? (
                      <div className="panel-actions">
                        <div className="agent-card__summary">
                          <span>Status</span>
                          <strong>{multiAgentResumeResult.reviewed_suggestion.status}</strong>
                          <p>{multiAgentResumeResult.reviewed_suggestion.final_content
                            ?? multiAgentResumeResult.reviewed_suggestion.suggested_content}</p>
                        </div>
                      </div>
                    ) : null}

                    {multiAgentReviewSuccess ? (
                      <p className="form-success" style={{ marginTop: "0.5rem" }}>
                        {multiAgentReviewSuccess}
                      </p>
                    ) : null}
                  </article>
                ) : !canReview ? (
                  <article className="panel panel--subtle">
                    <div className="panel-heading">
                      <div>
                        <p className="panel-tag">Human Review</p>
                        <h3>Approve, edit, or reject the multi-agent draft</h3>
                      </div>
                    </div>
                    <div className="panel-actions">
                      <p>当前角色仅可查看 AI 建议，不能执行审核操作。</p>
                    </div>
                  </article>
                ) : (
                  <article className="panel panel--subtle">
                    <div className="panel-heading">
                      <div>
                        <p className="panel-tag">Human Review</p>
                        <h3>Approve, edit, or reject the multi-agent draft</h3>
                      </div>
                    </div>

                    <div className="panel-actions">
                      <div className="field">
                        <label htmlFor="ma-review-draft">Draft reply (edit before approving if needed)</label>
                        <textarea
                          id="ma-review-draft"
                          rows={4}
                          value={multiAgentReviewDraftContent}
                          onChange={(event_) => setMultiAgentReviewDraftContent(event_.target.value)}
                        />
                      </div>

                      <div className="field">
                        <label htmlFor="ma-reject-reason">Reject reason (required when rejecting)</label>
                        <textarea
                          id="ma-reject-reason"
                          rows={2}
                          placeholder="Enter a reason for rejecting this draft..."
                          value={multiAgentReviewRejectReason}
                          onChange={(event_) => setMultiAgentReviewRejectReason(event_.target.value)}
                        />
                      </div>

                      {multiAgentReviewError ? (
                        <p className="form-error">{multiAgentReviewError}</p>
                      ) : null}
                      {multiAgentReviewSuccess ? (
                        <p className="form-success">{multiAgentReviewSuccess}</p>
                      ) : null}

                      <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.25rem" }}>
                        <button
                          type="button"
                          className="primary-button"
                          disabled={isSubmittingMultiAgentReview}
                          onClick={handleMultiAgentApprove}
                        >
                          {isSubmittingMultiAgentReview ? "Processing..." : "Approve current reply"}
                        </button>
                        <button
                          type="button"
                          className="ghost-button"
                          disabled={isSubmittingMultiAgentReview}
                          onClick={handleMultiAgentEdit}
                        >
                          {isSubmittingMultiAgentReview ? "Saving..." : "Save edits"}
                        </button>
                        <button
                          type="button"
                          className="ghost-button ghost-button--danger"
                          disabled={isSubmittingMultiAgentReview}
                          onClick={handleMultiAgentReject}
                        >
                          {isSubmittingMultiAgentReview ? "Rejecting..." : "Reject"}
                        </button>
                      </div>
                    </div>
                  </article>
                )}
              </div>
            ) : null}
              </>
            ) : (
              <p className="panel-state panel-state--compact">
                Multi-agent details are collapsed.
              </p>
            )}
          </article>

          <article className="panel">
            <div className="panel-heading">
              <div>
                <p className="panel-tag">Messages</p>
                <h3>Add communication record</h3>
              </div>
            </div>

            <div className="panel-actions">
              <div className="field">
                <label htmlFor="msg-sender-type">Sender type</label>
                <select
                  id="msg-sender-type"
                  value={messageSenderType}
                  onChange={(event_) =>
                    setMessageSenderType(
                      event_.target.value as "agent" | "customer" | "ai" | "system",
                    )
                  }
                >
                  <option value="agent">Agent</option>
                  <option value="customer">Customer</option>
                  <option value="ai">AI</option>
                  <option value="system">System</option>
                </select>
              </div>
              <div className="field">
                <label htmlFor="msg-content">Message content</label>
                <textarea
                  id="msg-content"
                  rows={3}
                  placeholder="Enter the communication record..."
                  value={messageContent}
                  onChange={(event_) => setMessageContent(event_.target.value)}
                />
              </div>
              {sendMessageError ? (
                <p className="form-error">{sendMessageError}</p>
              ) : null}
              {sendMessageSuccess ? (
                <p className="form-success">{sendMessageSuccess}</p>
              ) : null}
              <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.25rem", justifyContent: "flex-end" }}>
                <button
                  type="button"
                  className="primary-button"
                  disabled={isSendingMessage}
                  onClick={() => void handleSendMessage()}
                >
                  {isSendingMessage ? "Sending..." : "Send"}
                </button>
                <button
                  type="button"
                  className="ghost-button"
                  onClick={() => handleClearMessage()}
                  disabled={isSendingMessage}
                >
                  Clear
                </button>
              </div>
            </div>

            <div className="panel-heading" style={{ marginTop: "1.5rem" }}>
              <div>
                <h3>Conversation history</h3>
              </div>
            </div>

            {messages.length === 0 ? (
              <p className="panel-state">No messages have been recorded for this ticket yet.</p>
            ) : (
              <div className="timeline-list">
                {messages.map((message) => (
                  <article key={message.id} className="timeline-item">
                    <div className="timeline-item__header">
                      <strong>{message.sender_name}</strong>
                      <span>
                        {toLabel(message.sender_type)} · {formatDateTime(message.created_at)}
                      </span>
                    </div>
                    <p>{message.content}</p>
                  </article>
                ))}
              </div>
            )}
          </article>

          <article className="panel">
            <div className="panel-heading">
              <div>
                <p className="panel-tag">Agent Run History</p>
                <h3>View all agent runs</h3>
              </div>
            </div>

            <div className="filter-bar" style={{ display: "flex", gap: "1rem", marginBottom: "1rem" }}>
              <label className="field" style={{ flex: 1 }}>
                <span>Run Type</span>
                <select
                  value={agentRunTypeFilter}
                  onChange={(event_) => setAgentRunTypeFilter(event_.target.value)}
                >
                  <option value="all">All</option>
                  <option value="single_agent_workflow">Single-Agent Workflow</option>
                  <option value="multi_agent">Multi-Agent</option>
                </select>
              </label>
              <label className="field" style={{ flex: 1 }}>
                <span>Status</span>
                <select
                  value={agentRunStatusFilter}
                  onChange={(event_) => setAgentRunStatusFilter(event_.target.value)}
                >
                  <option value="all">All</option>
                  <option value="interrupted">Interrupted</option>
                  <option value="completed">Completed</option>
                  <option value="failed">Failed</option>
                </select>
              </label>
            </div>

            {agentRunHistoryLoading ? (
              <p className="panel-state">Loading agent run history...</p>
            ) : agentRunHistoryError ? (
              <p className="form-error">{agentRunHistoryError}</p>
            ) : agentRunHistory.length === 0 ? (
              agentRunTypeFilter === "single_agent_workflow" ? (
                <p className="panel-state">
                  No Single-Agent Workflow runs found for this ticket. Generate a single-agent reply
                  draft from the Single-Agent RAG section above to create one.
                </p>
              ) : (
                <p className="panel-state">No agent runs found for the selected filters.</p>
              )
            ) : (
              <div className="run-history-list">
                {agentRunHistory.map((run) => (
                  <article key={run.run_id} className="source-card" style={{ marginBottom: "0.5rem" }}>
                    <div className="source-card__header">
                      <div>
                        <strong>Run: {run.run_id.substring(0, 12)}…</strong>
                        <span>
                          {run.run_type} · {toLabel(run.status)} ·{" "}
                          {formatDateTime(run.created_at)}
                        </span>
                      </div>
                      <span className="badge badge--score">
                        {run.audit_trail_json.length} audit entries
                      </span>
                    </div>

                    {run.error_message ? (
                      <p className="form-error" style={{ marginTop: "0.25rem" }}>
                        {run.error_message}
                      </p>
                    ) : null}

                    <details
                      className="json-disclosure"
                      style={{ marginTop: "0.5rem" }}
                      open={expandedAgentRunId === run.run_id}
                      onToggle={(event_) => {
                        if (event_.currentTarget.open) {
                          setExpandedAgentRunId(run.run_id);
                        } else if (expandedAgentRunId === run.run_id) {
                          setExpandedAgentRunId(null);
                        }
                      }}
                    >
                      <summary>View details</summary>
                      <pre className="json-block" style={{ maxHeight: "300px", overflow: "auto" }}>
{JSON.stringify(run, null, 2)}
                      </pre>
                    </details>
                  </article>
                ))}
              </div>
            )}

            <div className="pagination-bar" style={{ display: "flex", gap: "0.5rem", alignItems: "center", justifyContent: "flex-end", marginTop: "1rem" }}>
              <span style={{ fontSize: "0.875rem", color: "var(--color-text-soft)" }}>
                Page {agentRunCurrentPage} of {agentRunTotalPages}
              </span>
              <button
                type="button"
                className="ghost-button"
                disabled={!canGoPreviousAgentRun}
                onClick={() => setAgentRunOffset((value) => Math.max(0, value - AGENT_RUN_PAGE_SIZE))}
              >
                Previous
              </button>
              <button
                type="button"
                className="ghost-button"
                disabled={!canGoNextAgentRun}
                onClick={() => setAgentRunOffset((value) => value + AGENT_RUN_PAGE_SIZE)}
              >
                Next
              </button>
            </div>
          </article>
        </>
      ) : null}
    </section>
  );
}
