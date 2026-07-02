import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  listTicketsPage,
  TICKET_CATEGORIES,
  TICKET_PRIORITIES,
  TICKET_STATUSES,
  type TicketCategory,
  type TicketListPageParams,
  type TicketPriority,
  type TicketRead,
  type TicketStatus,
} from "../api/tickets";


type FilterValue<T extends string> = T | "all";

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

export default function TicketsPage() {
  const [tickets, setTickets] = useState<TicketRead[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<FilterValue<TicketStatus>>("all");
  const [priorityFilter, setPriorityFilter] = useState<FilterValue<TicketPriority>>("all");
  const [categoryFilter, setCategoryFilter] = useState<FilterValue<TicketCategory>>("all");

  // 筛选条件变化时，offset 重置为 0
  useEffect(() => {
    setOffset(0);
  }, [statusFilter, priorityFilter, categoryFilter]);

  useEffect(() => {
    let active = true;

    async function loadTickets() {
      setLoading(true);
      setErrorMessage(null);

      try {
        const params: TicketListPageParams = {
          limit: PAGE_SIZE,
          offset,
        };
        if (statusFilter !== "all") {
          params.status = statusFilter;
        }
        if (priorityFilter !== "all") {
          params.priority = priorityFilter;
        }
        if (categoryFilter !== "all") {
          params.category = categoryFilter;
        }
        const page = await listTicketsPage(params);
        if (!active) {
          return;
        }
        setTickets(page.items);
        setTotal(page.total);
      } catch {
        if (!active) {
          return;
        }
        setErrorMessage("Unable to load ticket records right now.");
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadTickets();

    return () => {
      active = false;
    };
  }, [statusFilter, priorityFilter, categoryFilter, offset]);

  const openCount = tickets.filter((ticket) =>
    ["open", "ai_processing", "waiting_review", "in_progress"].includes(ticket.status),
  ).length;

  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const canGoPrevious = offset > 0;
  const canGoNext = offset + PAGE_SIZE < total;
  const startItem = total === 0 ? 0 : offset + 1;
  const endItem = Math.min(offset + tickets.length, total);

  return (
    <section className="page-stack">
      <div className="section-hero">
        <div>
          <p className="panel-tag">Step 28 · Tickets</p>
          <h3>Ticket queue for operations teams</h3>
          <p>
            Review incoming cases, narrow the queue with lightweight filters, and jump into
            each record for detail and status handling.
          </p>
        </div>
        <Link to="/tickets/new" className="primary-button primary-button--link">
          Create ticket
        </Link>
      </div>

      <section className="content-grid content-grid--three">
        <article className="panel stat-panel">
          <span className="stat-panel__value">{total}</span>
          <span className="stat-panel__label">Matching tickets</span>
        </article>
        <article className="panel stat-panel">
          <span className="stat-panel__value">{openCount}</span>
          <span className="stat-panel__label">Open on current page</span>
        </article>
        <article className="panel stat-panel">
          <span className="stat-panel__value">{tickets.length}</span>
          <span className="stat-panel__label">Current page items</span>
        </article>
      </section>

      <article className="panel">
        <div className="panel-heading">
          <div>
            <p className="panel-tag">Filters</p>
            <h3>Queue controls</h3>
          </div>
        </div>

        <div className="filters-grid">
          <label className="field">
            <span>Status</span>
            <select
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value as FilterValue<TicketStatus>)}
            >
              <option value="all">All statuses</option>
              {TICKET_STATUSES.map((value) => (
                <option key={value} value={value}>
                  {toLabel(value)}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Priority</span>
            <select
              value={priorityFilter}
              onChange={(event) =>
                setPriorityFilter(event.target.value as FilterValue<TicketPriority>)
              }
            >
              <option value="all">All priorities</option>
              {TICKET_PRIORITIES.map((value) => (
                <option key={value} value={value}>
                  {toLabel(value)}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Category</span>
            <select
              value={categoryFilter}
              onChange={(event) =>
                setCategoryFilter(event.target.value as FilterValue<TicketCategory>)
              }
            >
              <option value="all">All categories</option>
              {TICKET_CATEGORIES.map((value) => (
                <option key={value} value={value}>
                  {toLabel(value)}
                </option>
              ))}
            </select>
          </label>
        </div>
      </article>

      <article className="panel">
        <div className="panel-heading">
          <div>
            <p className="panel-tag">Ticket List</p>
            <h3>Customer and internal requests</h3>
            <span className="ticket-link__meta">
              Page {currentPage} / {totalPages}
            </span>
          </div>
        </div>

        {loading ? <p className="panel-state">Loading ticket records...</p> : null}
        {errorMessage ? <p className="form-error">{errorMessage}</p> : null}
        {!loading && !errorMessage && tickets.length === 0 ? (
          <p className="panel-state">No tickets match the selected filters.</p>
        ) : null}

        {!loading && !errorMessage && tickets.length > 0 ? (
          <>
            <div className="ticket-table-wrapper">
              <table className="ticket-table">
                <thead>
                  <tr>
                    <th>Ticket</th>
                    <th>Customer</th>
                    <th>Category</th>
                    <th>Priority</th>
                    <th>Status</th>
                    <th>Updated</th>
                  </tr>
                </thead>
                <tbody>
                  {tickets.map((ticket) => (
                    <tr key={ticket.id}>
                      <td>
                        <Link to={`/tickets/${ticket.id}`} className="ticket-link">
                          <strong>{ticket.title}</strong>
                          <span className="ticket-link__meta">#{ticket.id}</span>
                        </Link>
                      </td>
                      <td>
                        <div className="ticket-cell-stack">
                          <span>{ticket.customer_name}</span>
                          <span className="ticket-link__meta">{ticket.customer_email}</span>
                        </div>
                      </td>
                      <td>
                        <span className="badge badge--category">{toLabel(ticket.category)}</span>
                      </td>
                      <td>
                        <span className={`badge badge--priority badge--${ticket.priority}`}>
                          {toLabel(ticket.priority)}
                        </span>
                      </td>
                      <td>
                        <span className={`badge badge--status badge--${ticket.status}`}>
                          {toLabel(ticket.status)}
                        </span>
                      </td>
                      <td>{formatDateTime(ticket.updated_at)}</td>
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
