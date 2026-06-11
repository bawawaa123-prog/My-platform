import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  createTicket,
  TICKET_CATEGORIES,
  TICKET_PRIORITIES,
  type TicketCategory,
  type TicketPriority,
} from "../api/tickets";


type CreateFormState = {
  title: string;
  content: string;
  customer_name: string;
  customer_email: string;
  category: TicketCategory;
  priority: TicketPriority;
  source: string;
};

const INITIAL_FORM: CreateFormState = {
  title: "",
  content: "",
  customer_name: "",
  customer_email: "",
  category: "other",
  priority: "medium",
  source: "manual",
};

function toLabel(value: string) {
  return value
    .split("_")
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}

export default function TicketCreatePage() {
  const navigate = useNavigate();
  const [form, setForm] = useState<CreateFormState>(INITIAL_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  function updateField<Key extends keyof CreateFormState>(field: Key, value: CreateFormState[Key]) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setErrorMessage(null);

    try {
      const createdTicket = await createTicket(form);
      navigate(`/tickets/${createdTicket.id}`, { replace: true });
    } catch {
      setErrorMessage("Ticket creation failed. Please review the form and try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="page-stack">
      <div className="section-hero">
        <div>
          <p className="panel-tag">Create Ticket</p>
          <h3>Capture a new support request</h3>
          <p>
            Record the customer profile, describe the issue clearly, and route the case into
            the queue with the right initial category and priority.
          </p>
        </div>
      </div>

      <article className="panel">
        <div className="panel-heading">
          <div>
            <p className="panel-tag">New Case</p>
            <h3>Ticket intake form</h3>
          </div>
        </div>

        <form className="ticket-form" onSubmit={handleSubmit}>
          <div className="form-grid">
            <label className="field">
              <span>Title</span>
              <input
                type="text"
                value={form.title}
                onChange={(event) => updateField("title", event.target.value)}
                placeholder="Payment captured twice for the same order"
                required
              />
            </label>

            <label className="field">
              <span>Customer name</span>
              <input
                type="text"
                value={form.customer_name}
                onChange={(event) => updateField("customer_name", event.target.value)}
                placeholder="Wang Li"
                required
              />
            </label>

            <label className="field">
              <span>Customer email</span>
              <input
                type="email"
                value={form.customer_email}
                onChange={(event) => updateField("customer_email", event.target.value)}
                placeholder="customer@example.com"
                required
              />
            </label>

            <label className="field">
              <span>Source</span>
              <input
                type="text"
                value={form.source}
                onChange={(event) => updateField("source", event.target.value)}
                placeholder="manual"
                required
              />
            </label>

            <label className="field">
              <span>Category</span>
              <select
                value={form.category}
                onChange={(event) => updateField("category", event.target.value as TicketCategory)}
              >
                {TICKET_CATEGORIES.map((value) => (
                  <option key={value} value={value}>
                    {toLabel(value)}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Priority</span>
              <select
                value={form.priority}
                onChange={(event) => updateField("priority", event.target.value as TicketPriority)}
              >
                {TICKET_PRIORITIES.map((value) => (
                  <option key={value} value={value}>
                    {toLabel(value)}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <label className="field">
            <span>Description</span>
            <textarea
              value={form.content}
              onChange={(event) => updateField("content", event.target.value)}
              placeholder="Describe the customer issue, expected outcome, and any urgency signals."
              rows={8}
              required
            />
          </label>

          {errorMessage ? <p className="form-error">{errorMessage}</p> : null}

          <div className="form-actions">
            <button type="submit" className="primary-button" disabled={submitting}>
              {submitting ? "Creating..." : "Create ticket"}
            </button>
            <button
              type="button"
              className="ghost-button"
              onClick={() => navigate("/tickets")}
              disabled={submitting}
            >
              Back to list
            </button>
          </div>
        </form>
      </article>
    </section>
  );
}
