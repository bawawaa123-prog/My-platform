import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  approveSuggestion,
  classifyTicketAI,
  editSuggestion,
  generateTicketReply,
  listTicketAgentRuns,
  listTicketSuggestions,
  rejectSuggestion,
  resumeMultiAgentProcess,
  startMultiAgentProcess,
  type AgentAuditTrailItem,
  type AgentRunLogRead,
  type AIMultiAgentPendingReviewRead,
  type AIMultiAgentProcessRead,
  type AIReplyDraftRead,
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

function formatDateTime(value: string | null) {
  if (!value) {
    return "Not available";
  }

  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

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

function buildAgentCards(result: AIMultiAgentPendingReviewRead): AgentOutputCard[] {
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

export default function TicketDetailPage() {
  const params = useParams();
  const ticketId = Number(params.ticketId);
  const isMountedRef = useRef(true);

  const [ticket, setTicket] = useState<TicketRead | null>(null);
  const [messages, setMessages] = useState<TicketMessageRead[]>([]);
  const [classification, setClassification] = useState<TicketClassification | null>(null);
  const [suggestions, setSuggestions] = useState<AIReplyDraftRead[]>([]);
  const [multiAgentResult, setMultiAgentResult] = useState<AIMultiAgentPendingReviewRead | null>(null);
  const [latestAgentRun, setLatestAgentRun] = useState<AgentRunLogRead | null>(null);

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

  const [reviewDraftContent, setReviewDraftContent] = useState("");
  const [reviewRejectReason, setReviewRejectReason] = useState("");

  const [messageContent, setMessageContent] = useState("");
  const [messageSenderType, setMessageSenderType] = useState<"agent" | "customer" | "ai" | "system">("agent");
  const [isSendingMessage, setIsSendingMessage] = useState(false);
  const [sendMessageError, setSendMessageError] = useState<string | null>(null);
  const [sendMessageSuccess, setSendMessageSuccess] = useState<string | null>(null);

  const latestSuggestion = suggestions[0] ?? null;
  const agentCards = useMemo(
    () => (multiAgentResult ? buildAgentCards(multiAgentResult) : []),
    [multiAgentResult],
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

  async function loadAgentRuns(currentTicketId: number) {
    setLoadingAgentRuns(true);
    setAgentRunsErrorMessage(null);

    try {
      const runData = await listTicketAgentRuns(currentTicketId);
      if (!isMountedRef.current) {
        return;
      }

      const latestRun = runData[0] ?? null;
      setLatestAgentRun(latestRun);

      if (latestRun && isMultiAgentPendingReviewRead(latestRun.output_json)) {
        setMultiAgentResult(latestRun.output_json);
      } else if (!latestRun) {
        setMultiAgentResult(null);
      }
    } catch {
      if (!isMountedRef.current) {
        return;
      }
      setAgentRunsErrorMessage("Unable to load the multi-agent run history right now.");
    } finally {
      if (isMountedRef.current) {
        setLoadingAgentRuns(false);
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
      setLatestAgentRun(null);

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
        void Promise.all([loadSuggestions(ticketId), loadAgentRuns(ticketId)]);
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
    if (!latestSuggestion) {
      setReviewDraftContent("");
      setReviewRejectReason("");
      return;
    }

    setReviewDraftContent(latestSuggestion.final_content ?? latestSuggestion.suggested_content);
    setReviewRejectReason(latestSuggestion.reject_reason ?? "");
  }, [latestSuggestion?.id, latestSuggestion?.updated_at]);

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
    } catch {
      setAiActionErrorMessage("AI classification failed. Please retry in a moment.");
    } finally {
      setIsClassifying(false);
    }
  }

  async function handleGenerateReply() {
    if (!ticket) {
      return;
    }

    setIsGeneratingReply(true);
    setAiActionErrorMessage(null);
    setSuggestionsErrorMessage(null);
    setReviewSuccessMessage(null);
    setMultiAgentSuccessMessage(null);

    try {
      const suggestion = await generateTicketReply(ticket.id);
      setSuggestions((current) => upsertSuggestion(current, suggestion));
      setReviewDraftContent(suggestion.suggested_content);
      setReviewRejectReason("");
    } catch {
      setAiActionErrorMessage("Reply draft generation failed. Please try again.");
    } finally {
      setIsGeneratingReply(false);
    }
  }

  async function handleApproveSuggestion() {
    if (!latestSuggestion) {
      return;
    }

    setIsSubmittingReview(true);
    setAiActionErrorMessage(null);
    setSuggestionsErrorMessage(null);
    setReviewSuccessMessage(null);

    try {
      const reviewed = await approveSuggestion(latestSuggestion.id);
      setSuggestions((current) => upsertSuggestion(current, reviewed));
      setReviewSuccessMessage("AI draft approved and locked as the final reviewed reply.");
    } catch {
      setAiActionErrorMessage("Approve action failed. Please refresh and try again.");
    } finally {
      setIsSubmittingReview(false);
    }
  }

  async function handleEditSuggestion() {
    if (!latestSuggestion) {
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
      const reviewed = await editSuggestion(latestSuggestion.id, { final_content: finalContent });
      setSuggestions((current) => upsertSuggestion(current, reviewed));
      setReviewSuccessMessage("AI draft saved with human edits.");
    } catch {
      setAiActionErrorMessage("Edit action failed. Please try again.");
    } finally {
      setIsSubmittingReview(false);
    }
  }

  async function handleRejectSuggestion() {
    if (!latestSuggestion) {
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
      const reviewed = await rejectSuggestion(latestSuggestion.id, { reject_reason: rejectReason });
      setSuggestions((current) => upsertSuggestion(current, reviewed));
      setReviewSuccessMessage("AI draft rejected and the review reason has been recorded.");
    } catch {
      setAiActionErrorMessage("Reject action failed. Please try again.");
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

      await Promise.all([loadSuggestions(ticket.id), loadAgentRuns(ticket.id)]);
    } catch {
      setAgentRunsErrorMessage("Multi-agent analysis failed. Please try again.");
    } finally {
      setIsRunningMultiAgent(false);
    }
  }

  async function handleMultiAgentApprove() {
    if (!ticket || !multiAgentResult) {
      return;
    }

    setIsSubmittingMultiAgentReview(true);
    setMultiAgentReviewError(null);
    setMultiAgentReviewSuccess(null);

    try {
      const result = await resumeMultiAgentProcess(ticket.id, {
        action: "approve",
        run_id: multiAgentResult.run_id,
      });
      setMultiAgentResumeResult(result);
      setMultiAgentReviewSuccess("Multi-agent reply approved and finalized.");
      await Promise.all([loadSuggestions(ticket.id), loadAgentRuns(ticket.id)]);
    } catch {
      setMultiAgentReviewError("Approve action failed. Please try again.");
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
      await Promise.all([loadSuggestions(ticket.id), loadAgentRuns(ticket.id)]);
    } catch {
      setMultiAgentReviewError("Edit action failed. Please try again.");
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
      await Promise.all([loadSuggestions(ticket.id), loadAgentRuns(ticket.id)]);
    } catch {
      setMultiAgentReviewError("Reject action failed. Please try again.");
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

          <section className="content-grid content-grid--detail">
            <article className="panel panel--feature">
              <div className="panel-heading">
                <div>
                  <p className="panel-tag">AI Reply</p>
                  <h3>Draft and human review</h3>
                </div>
                <button
                  type="button"
                  className="primary-button"
                  onClick={handleGenerateReply}
                  disabled={isGeneratingReply}
                >
                  {isGeneratingReply ? "Generating..." : "Generate reply draft"}
                </button>
              </div>

              {aiActionErrorMessage ? <p className="form-error">{aiActionErrorMessage}</p> : null}
              {reviewSuccessMessage ? <p className="form-success">{reviewSuccessMessage}</p> : null}
              {loadingSuggestions ? <p className="panel-state">Loading AI suggestions...</p> : null}
              {suggestionsErrorMessage ? <p className="form-error">{suggestionsErrorMessage}</p> : null}

              {!loadingSuggestions && !suggestionsErrorMessage && !latestSuggestion ? (
                <p className="panel-state">
                  No AI reply draft exists for this ticket yet. Generate one to start the review
                  workflow.
                </p>
              ) : null}

              {!loadingSuggestions && latestSuggestion ? (
                <div className="ai-panel-stack">
                  <article className="suggestion-card">
                    <div className="suggestion-card__header">
                      <div>
                        <strong>Suggestion #{latestSuggestion.id}</strong>
                        <span>
                          Created {formatDateTime(latestSuggestion.created_at)} · Updated{" "}
                          {formatDateTime(latestSuggestion.updated_at)}
                        </span>
                      </div>
                      <div className="suggestion-card__badges">
                        <span
                          className={`badge badge--suggestion-status badge--${latestSuggestion.status}`}
                        >
                          {toLabel(latestSuggestion.status)}
                        </span>
                        <span className="badge badge--score">
                          Confidence {formatConfidence(latestSuggestion.confidence)}
                        </span>
                      </div>
                    </div>

                    <p className="suggestion-card__content">{latestSuggestion.suggested_content}</p>

                    <div className="detail-stack detail-stack--compact">
                      <div className="detail-row">
                        <span>Reasoning summary</span>
                        <strong>{latestSuggestion.reasoning_summary ?? "Not provided"}</strong>
                      </div>
                      <div className="detail-row">
                        <span>Review outcome</span>
                        <strong>
                          {latestSuggestion.status === "draft"
                            ? "Pending human review"
                            : `Reviewed at ${formatDateTime(latestSuggestion.reviewed_at)}`}
                        </strong>
                      </div>
                    </div>
                  </article>

                  <article className="panel panel--subtle">
                    <div className="panel-heading">
                      <div>
                        <p className="panel-tag">Sources</p>
                        <h3>RAG references</h3>
                      </div>
                    </div>

                    {latestSuggestion.sources_json.length === 0 ? (
                      <p className="panel-state">
                        No strong knowledge match was retrieved, so this draft should be reviewed
                        carefully before approval.
                      </p>
                    ) : (
                      <div className="source-list">
                        {latestSuggestion.sources_json.map((source) => (
                          <article key={source.chunk_id} className="source-card">
                            <div className="source-card__header">
                              <div>
                                <strong>Document #{source.doc_id}</strong>
                                <span>
                                  Chunk {source.chunk_index} · ID {source.chunk_id}
                                </span>
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

                  <article className="panel panel--subtle">
                    <div className="panel-heading">
                      <div>
                        <p className="panel-tag">Human Review</p>
                        <h3>Approve, edit, or reject</h3>
                      </div>
                    </div>

                    {latestSuggestion.status === "draft" ? (
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
                            {isSubmittingReview ? "Saving..." : "Approve as drafted"}
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
                    ) : (
                      <div className="review-outcome">
                        <div className="detail-stack detail-stack--compact">
                          <div className="detail-row">
                            <span>Reviewed at</span>
                            <strong>{formatDateTime(latestSuggestion.reviewed_at)}</strong>
                          </div>
                          <div className="detail-row">
                            <span>Reviewer</span>
                            <strong>
                              {latestSuggestion.reviewed_by
                                ? `User #${latestSuggestion.reviewed_by}`
                                : "Not available"}
                            </strong>
                          </div>
                        </div>

                        {latestSuggestion.final_content ? (
                          <div className="review-outcome__block">
                            <span>Final approved content</span>
                            <p>{latestSuggestion.final_content}</p>
                          </div>
                        ) : null}

                        {latestSuggestion.reject_reason ? (
                          <div className="review-outcome__block">
                            <span>Reject reason</span>
                            <p>{latestSuggestion.reject_reason}</p>
                          </div>
                        ) : null}
                      </div>
                    )}
                  </article>
                </div>
              ) : null}
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
              <button
                type="button"
                className="primary-button"
                onClick={handleRunMultiAgent}
                disabled={isRunningMultiAgent}
              >
                {isRunningMultiAgent ? "Running..." : "Run multi-agent analysis"}
              </button>
            </div>

            <p className="helper-copy">
              This runs the fixed-sequence workflow: Supervisor, Triage, Knowledge, Similar Case,
              Reply, Risk, Workflow, then pause at human review.
            </p>

            {multiAgentSuccessMessage ? <p className="form-success">{multiAgentSuccessMessage}</p> : null}
            {agentRunsErrorMessage ? <p className="form-error">{agentRunsErrorMessage}</p> : null}
            {loadingAgentRuns ? <p className="panel-state">Loading multi-agent runs...</p> : null}

            {!loadingAgentRuns && !agentRunsErrorMessage && !multiAgentResult ? (
              <p className="panel-state">
                No multi-agent run has been recorded for this ticket yet. Start one to inspect the
                execution trail and each agent output.
              </p>
            ) : null}

            {multiAgentResult ? (
              <div className="multi-agent-stack">
                <div className="multi-agent-summary-grid">
                  <article className="meta-card">
                    <span className="meta-card__label">Workflow status</span>
                    <strong>{toLabel(multiAgentResult.status)}</strong>
                    <span>Pending node: {toLabel(multiAgentResult.pending_node)}</span>
                  </article>
                  <article className="meta-card">
                    <span className="meta-card__label">Run ID</span>
                    <strong className="meta-card__value--mono">{multiAgentResult.run_id}</strong>
                    <span>Thread ID: {multiAgentResult.thread_id}</span>
                  </article>
                  <article className="meta-card">
                    <span className="meta-card__label">Audit entries</span>
                    <strong>{multiAgentResult.audit_trail.length}</strong>
                    <span>Draft confidence: {formatConfidence(multiAgentResult.confidence)}</span>
                  </article>
                  <article className="meta-card">
                    <span className="meta-card__label">Persisted run</span>
                    <strong>{latestAgentRun ? toLabel(latestAgentRun.status) : "Pending sync"}</strong>
                    <span>
                      {latestAgentRun
                        ? `Updated ${formatDateTime(latestAgentRun.updated_at)}`
                        : "Waiting for run-log refresh"}
                    </span>
                  </article>
                </div>

                <div className="multi-agent-card-grid">
                  {agentCards.map((card) => {
                    const auditEntry = findAuditEntry(multiAgentResult.audit_trail, card.agentName);
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
                    {multiAgentResult.audit_trail.map((entry, index) => (
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

                {!multiAgentResumeResult ? (
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
                          {isSubmittingMultiAgentReview ? "Processing..." : "Approve as drafted"}
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
                ) : (
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
                )}
              </div>
            ) : null}
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
        </>
      ) : null}
    </section>
  );
}
