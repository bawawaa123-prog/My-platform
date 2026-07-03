import { useEffect, useState } from "react";

import {
  AUDIT_LOG_ACTIONS,
  AUDIT_LOG_TARGET_TYPES,
  listAuditLogs,
  type AuditLogQueryParams,
  type AuditLogRead,
} from "../api/auditLogs";


const PAGE_SIZE = 20;

function formatDateTime(value: string) {
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

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLogRead[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

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
                        <DetailPopover detail={log.detail_json} />
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
    </section>
  );
}

function DetailPopover({ detail }: { detail: Record<string, unknown> }) {
  const [open, setOpen] = useState(false);
  const entries = Object.entries(detail);

  if (entries.length === 0) {
    return <span className="ticket-link__meta">—</span>;
  }

  return (
    <span className="detail-popover-wrapper">
      <button
        type="button"
        className="ghost-button"
        onClick={() => setOpen((current) => !current)}
      >
        {open ? "Hide" : "View"}
      </button>
      {open ? (
        <pre className="detail-json">
          {JSON.stringify(detail, null, 2)}
        </pre>
      ) : null}
    </span>
  );
}
