import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  listPendingSuggestions,
  type PendingSuggestionRead,
} from "../api/reviews";


const PAGE_SIZE = 10;

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

export default function PendingReviewsPage() {
  const [items, setItems] = useState<PendingSuggestionRead[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadPending() {
      setLoading(true);
      setErrorMessage(null);

      try {
        const page = await listPendingSuggestions({
          limit: PAGE_SIZE,
          offset,
        });
        if (!active) {
          return;
        }
        setItems(page.items);
        setTotal(page.total);
      } catch {
        if (!active) {
          return;
        }
        setErrorMessage("Unable to load pending reviews right now.");
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadPending();

    return () => {
      active = false;
    };
  }, [offset]);

  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const canGoPrevious = offset > 0;
  const canGoNext = offset + PAGE_SIZE < total;
  const startItem = total === 0 ? 0 : offset + 1;
  const endItem = Math.min(offset + items.length, total);

  return (
    <section className="page-stack">
      <div className="section-hero">
        <div>
          <p className="panel-tag">Pending Reviews</p>
          <h3>待审核 AI 回复</h3>
          <p>
            Review AI-generated reply suggestions before they are sent to
            customers. Only draft suggestions awaiting review appear here.
          </p>
        </div>
      </div>

      <article className="panel">
        <div className="panel-heading">
          <div>
            <p className="panel-tag">Suggestion Queue</p>
            <h3>Pending AI suggestions</h3>
            <span className="ticket-link__meta">
              Page {currentPage} / {totalPages}
            </span>
          </div>
        </div>

        {loading ? <p className="panel-state">Loading pending suggestions...</p> : null}
        {errorMessage ? <p className="form-error">{errorMessage}</p> : null}
        {!loading && !errorMessage && items.length === 0 ? (
          <p className="panel-state">暂无待审核 AI 回复。</p>
        ) : null}

        {!loading && !errorMessage && items.length > 0 ? (
          <>
            <div className="ticket-table-wrapper">
              <table className="ticket-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Ticket</th>
                    <th>Priority</th>
                    <th>Category</th>
                    <th>Status</th>
                    <th>Customer</th>
                    <th>Suggested Reply</th>
                    <th>Confidence</th>
                    <th>Created</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={item.id}>
                      <td>
                        <span className="ticket-link__meta">#{item.id}</span>
                      </td>
                      <td>
                        <Link
                          to={`/tickets/${item.ticket_id}`}
                          className="ticket-link"
                        >
                          {item.ticket_title}
                        </Link>
                      </td>
                      <td>
                        <span
                          className={
                            item.ticket_priority === "urgent"
                              ? "badge badge--priority-urgent"
                              : "badge badge--category"
                          }
                        >
                          {toLabel(item.ticket_priority)}
                        </span>
                      </td>
                      <td>
                        <span className="badge badge--category">
                          {toLabel(item.ticket_category)}
                        </span>
                      </td>
                      <td>
                        <span className="badge badge--category">
                          {toLabel(item.ticket_status)}
                        </span>
                      </td>
                      <td>{item.customer_email}</td>
                      <td className="suggestion-content-cell">
                        <SuggestionPreview content={item.suggested_content} />
                      </td>
                      <td>
                        <span className="ticket-link__meta">
                          {(item.confidence * 100).toFixed(0)}%
                        </span>
                      </td>
                      <td>{formatDateTime(item.created_at)}</td>
                      <td>
                        <Link
                          to={`/tickets/${item.ticket_id}`}
                          className="primary-button"
                          style={{ whiteSpace: "nowrap" }}
                        >
                          View ticket
                        </Link>
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
                onClick={() =>
                  setOffset((value) => Math.max(0, value - PAGE_SIZE))
                }
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

function SuggestionPreview({ content }: { content: string }) {
  const [expanded, setExpanded] = useState(false);
  const maxLength = 120;
  const shouldTruncate = content.length > maxLength;

  if (!shouldTruncate) {
    return <span className="suggestion-text">{content}</span>;
  }

  return (
    <span className="suggestion-text">
      {expanded ? content : `${content.slice(0, maxLength)}...`}
      <button
        type="button"
        className="ghost-button"
        onClick={() => setExpanded((current) => !current)}
        style={{ marginLeft: 4 }}
      >
        {expanded ? "Less" : "More"}
      </button>
    </span>
  );
}
