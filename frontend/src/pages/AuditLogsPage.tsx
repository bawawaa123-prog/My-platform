import { useEffect, useState } from "react";

import {
  AUDIT_LOG_ACTIONS,
  AUDIT_LOG_TARGET_TYPES,
  listAuditLogs,
  type AuditLogQueryParams,
  type AuditLogRead,
} from "../api/auditLogs";
import { formatDateTime } from "../utils/date";


const PAGE_SIZE = 20;

function toLabel(value: string) {
  return value
    .split("_")
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}

// ---------------------------------------------------------------------------
// Helper: humanize key names
// ---------------------------------------------------------------------------

function humanizeKey(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

// ---------------------------------------------------------------------------
// Helper: format a single value for display
// ---------------------------------------------------------------------------

function formatValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "\u2014";
  }
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  if (typeof value === "object") {
    return JSON.stringify(value, null, 2);
  }
  return String(value);
}

// ---------------------------------------------------------------------------
// Helper: build a one-line summary for the detail column
// ---------------------------------------------------------------------------

function buildAuditSummary(log: AuditLogRead): string {
  const detail = log.detail_json ?? {};

  switch (log.action) {
    case "create_ticket":
      return typeof detail.title === "string"
        ? `Created ticket "${detail.title}"`
        : "Created ticket";

    case "update_ticket":
      if (typeof detail.status === "string") {
        return `Updated status to "${detail.status}"`;
      }
      if (typeof detail.priority === "string") {
        return `Updated priority to "${detail.priority}"`;
      }
      return "Updated ticket";

    case "delete_ticket":
      return typeof detail.title === "string"
        ? `Deleted ticket "${detail.title}"`
        : "Deleted ticket";

    case "create_message":
      return typeof detail.sender_type === "string"
        ? `Created ${detail.sender_type} message`
        : "Created message";

    case "create_knowledge_doc":
    case "update_knowledge_doc":
      return typeof detail.title === "string"
        ? `${humanizeKey(log.action)} "${detail.title}"`
        : humanizeKey(log.action);

    case "delete_knowledge_doc":
      return "Deleted knowledge document";

    case "upload_document":
      return typeof detail.filename === "string"
        ? `Uploaded "${detail.filename}"`
        : "Uploaded document";

    case "review_ai_suggestion":
    case "approve_reply":
      return "Approved AI suggestion";

    case "reject_reply":
      return "Rejected AI suggestion";

    default:
      return "View structured details";
  }
}

// ---------------------------------------------------------------------------
// Main page component
// ---------------------------------------------------------------------------

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLogRead[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [selectedLog, setSelectedLog] = useState<AuditLogRead | null>(null);

  // Filter state
  const [actionFilter, setActionFilter] = useState("all");
  const [targetTypeFilter, setTargetTypeFilter] = useState("all");
  const [targetIdFilter, setTargetIdFilter] = useState("");
  const [userIdFilter, setUserIdFilter] = useState("");

  // Reset offset when filters change
  useEffect(() => {
    setOffset(0);
  }, [actionFilter, targetTypeFilter, targetIdFilter, userIdFilter]);

  useEffect(() => {
    let active = true;

    async function loadLogs() {
      setLoading(true);
      setErrorMessage(null);

      try {
        const params: AuditLogQueryParams = {
          limit: PAGE_SIZE,
          offset,
        };
        if (actionFilter !== "all") {
          params.action = actionFilter;
        }
        if (targetTypeFilter !== "all") {
          params.target_type = targetTypeFilter;
        }
        if (targetIdFilter.trim() !== "") {
          const parsed = Number(targetIdFilter);
          if (!Number.isNaN(parsed) && parsed >= 1) {
            params.target_id = parsed;
          }
        }
        if (userIdFilter.trim() !== "") {
          const parsed = Number(userIdFilter);
          if (!Number.isNaN(parsed) && parsed >= 1) {
            params.user_id = parsed;
          }
        }
        const page = await listAuditLogs(params);
        if (!active) {
          return;
        }
        setLogs(page.items);
        setTotal(page.total);
      } catch {
        if (!active) {
          return;
        }
        setErrorMessage("Unable to load audit log records right now.");
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadLogs();

    return () => {
      active = false;
    };
  }, [actionFilter, targetTypeFilter, targetIdFilter, userIdFilter, offset]);

  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const canGoPrevious = offset > 0;
  const canGoNext = offset + PAGE_SIZE < total;
  const startItem = total === 0 ? 0 : offset + 1;
  const endItem = Math.min(offset + logs.length, total);

  return (
    <section className="page-stack">
      <div className="section-hero">
        <div>
          <p className="panel-tag">Audit Logs</p>
          <h3>System audit trail</h3>
          <p>
            Review all actions recorded across the platform — ticket operations,
            knowledge base changes, AI suggestions, and more.
          </p>
        </div>
        <button
          type="button"
          className="primary-button"
          disabled={loading}
          onClick={() => setOffset((value) => value)}
        >
          Refresh
        </button>
      </div>

      <article className="panel">
        <div className="panel-heading">
          <div>
            <p className="panel-tag">Filters</p>
            <h3>Search audit records</h3>
          </div>
        </div>

        <div className="filters-grid">
          <label className="field">
            <span>Action</span>
            <select
              value={actionFilter}
              onChange={(event) => setActionFilter(event.target.value)}
            >
              <option value="all">All actions</option>
              {AUDIT_LOG_ACTIONS.map((value) => (
                <option key={value} value={value}>
                  {toLabel(value)}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Target Type</span>
            <select
              value={targetTypeFilter}
              onChange={(event) => setTargetTypeFilter(event.target.value)}
            >
              <option value="all">All types</option>
              {AUDIT_LOG_TARGET_TYPES.map((value) => (
                <option key={value} value={value}>
                  {toLabel(value)}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Target ID</span>
            <input
              type="number"
              min="1"
              placeholder="e.g. 42"
              value={targetIdFilter}
              onChange={(event) => setTargetIdFilter(event.target.value)}
            />
          </label>

          <label className="field">
            <span>User ID</span>
            <input
              type="number"
              min="1"
              placeholder="e.g. 1"
              value={userIdFilter}
              onChange={(event) => setUserIdFilter(event.target.value)}
            />
          </label>
        </div>
      </article>

      <article className="panel">
        <div className="panel-heading">
          <div>
            <p className="panel-tag">Audit Log List</p>
            <h3>Recorded events</h3>
            <span className="ticket-link__meta">
              Page {currentPage} / {totalPages}
            </span>
          </div>
        </div>

        {loading ? <p className="panel-state">Loading audit log records...</p> : null}
        {errorMessage ? <p className="form-error">{errorMessage}</p> : null}
        {!loading && !errorMessage && logs.length === 0 ? (
          <p className="panel-state">No audit logs match the selected filters.</p>
        ) : null}

        {!loading && !errorMessage && logs.length > 0 ? (
          <>
            <div className="ticket-table-wrapper">
              <table className="ticket-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Action</th>
                    <th>Target Type</th>
                    <th>Target ID</th>
                    <th>User ID</th>
                    <th>Created At</th>
                    <th>Detail</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log) => (
                    <tr key={log.id}>
                      <td>
                        <span className="ticket-link__meta">#{log.id}</span>
                      </td>
                      <td>
                        <span className="badge badge--category">{toLabel(log.action)}</span>
                      </td>
                      <td>{toLabel(log.target_type)}</td>
                      <td>{log.target_id}</td>
                      <td>{log.user_id ?? "—"}</td>
                      <td>{formatDateTime(log.created_at)}</td>
                      <td>
                        <DetailCell
                          log={log}
                          onViewDetails={() => setSelectedLog(log)}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="pagination-bar">
              <button
                className="primary-button"
                disabled={!canGoPrevious}
                onClick={() => setOffset((value) => Math.max(0, value - PAGE_SIZE))}
              >
                Previous
              </button>
              <span className="pagination-info">
                Showing {startItem}-{endItem} of {total}
              </span>
              <button
                className="primary-button"
                disabled={!canGoNext}
                onClick={() => setOffset((value) => value + PAGE_SIZE)}
              >
                Next
              </button>
            </div>
          </>
        ) : null}
      </article>

      {selectedLog ? (
        <AuditLogDetailModal
          log={selectedLog}
          onClose={() => setSelectedLog(null)}
        />
      ) : null}
    </section>
  );
}

// ---------------------------------------------------------------------------
// DetailCell — summary + button in table
// ---------------------------------------------------------------------------

function DetailCell({
  log,
  onViewDetails,
}: {
  log: AuditLogRead;
  onViewDetails: () => void;
}) {
  const detail = log.detail_json;
  const hasDetail = detail && typeof detail === "object" && Object.keys(detail).length > 0;
  const summary = hasDetail ? buildAuditSummary(log) : null;

  if (!hasDetail) {
    return <span className="ticket-link__meta detail-summary--empty">No details</span>;
  }

  return (
    <div>
      <div className="detail-summary">{summary}</div>
      <button
        type="button"
        className="view-details-button"
        onClick={onViewDetails}
      >
        View details
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// AuditLogDetailModal — modal with structured key-value + raw JSON
// ---------------------------------------------------------------------------

function AuditLogDetailModal({
  log,
  onClose,
}: {
  log: AuditLogRead;
  onClose: () => void;
}) {
  const [showRaw, setShowRaw] = useState(false);
  const detail = log.detail_json ?? {};

  const handleOverlayClick = (event: React.MouseEvent<HTMLDivElement>) => {
    if (event.target === event.currentTarget) {
      onClose();
    }
  };

  // Close on Escape key
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  const entries = Object.entries(detail);

  return (
    <div className="modal-overlay" onClick={handleOverlayClick}>
      <div className="modal-panel" role="dialog" aria-modal="true">
        <div className="modal-header">
          <div>
            <p className="modal-header__title">Audit Log #{log.id}</p>
            <p className="modal-header__meta">
              Action: {log.action} &middot; Target: {log.target_type} #{log.target_id}
              &nbsp;&middot; Created: {formatDateTime(log.created_at)}
            </p>
          </div>
          <button
            type="button"
            className="modal-close-button"
            onClick={onClose}
            aria-label="Close"
          >
            &times;
          </button>
        </div>

        <div className="modal-body">
          {entries.length > 0 ? (
            <div className="detail-grid">
              {entries.map(([key, value]) => (
                <div key={key} style={{ display: "contents" }}>
                  <div className="detail-grid__key">{humanizeKey(key)}</div>
                  <div className="detail-grid__value">
                    {renderDetailValue(value)}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: "#8b9aab", fontStyle: "italic" }}>
              No structured details available.
            </p>
          )}

          <div className="raw-json-section">
            <button
              type="button"
              className="raw-json-toggle"
              onClick={() => setShowRaw((current) => !current)}
            >
              {showRaw ? "Hide raw JSON" : "Show raw JSON"}
            </button>
            {showRaw ? (
              <div className="raw-json-content">
                {JSON.stringify(detail, null, 2)}
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}

function renderDetailValue(value: unknown) {
  if (value === null || value === undefined) {
    return <span className="detail-grid__value--null">&mdash;</span>;
  }

  if (typeof value === "boolean") {
    return <span>{value ? "Yes" : "No"}</span>;
  }

  if (typeof value === "object") {
    return <pre>{JSON.stringify(value, null, 2)}</pre>;
  }

  return <span>{String(value)}</span>;
}
