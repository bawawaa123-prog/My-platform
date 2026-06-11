import { useEffect, useState } from "react";

import { getAnalyticsOverview, type AnalyticsOverviewRead } from "../api/analytics";

const CATEGORY_LABELS: Record<string, string> = {
  payment: "Payment",
  account: "Account",
  product: "Product",
  refund: "Refund",
  invoice: "Invoice",
  technical: "Technical",
  hr: "HR",
  it: "IT",
  other: "Other",
};

const PRIORITY_LABELS: Record<string, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
  urgent: "Urgent",
};

type DistributionChartProps = {
  title: string;
  tag: string;
  emptyCopy: string;
  data: Record<string, number>;
  labels: Record<string, string>;
  tone: "category" | "priority";
};

function formatPercentage(value: number) {
  return `${Math.round(value * 100)}%`;
}

function DistributionChart({ title, tag, emptyCopy, data, labels, tone }: DistributionChartProps) {
  const entries = Object.entries(data);
  const maxValue = Math.max(0, ...entries.map(([, value]) => value));
  const total = entries.reduce((sum, [, value]) => sum + value, 0);

  return (
    <article className="panel">
      <div className="panel-heading">
        <div>
          <p className="panel-tag">{tag}</p>
          <h3>{title}</h3>
        </div>
      </div>

      {total === 0 ? (
        <p className="panel-state">{emptyCopy}</p>
      ) : (
        <div className="distribution-list">
          {entries.map(([key, value]) => {
            const width = maxValue > 0 ? `${Math.max((value / maxValue) * 100, value > 0 ? 8 : 0)}%` : "0%";
            return (
              <article className="distribution-row" key={key}>
                <div className="distribution-row__meta">
                  <strong>{labels[key] ?? key}</strong>
                  <span>{value}</span>
                </div>
                <div className="distribution-row__track" aria-hidden="true">
                  <div
                    className={`distribution-row__bar distribution-row__bar--${tone}`}
                    style={{ width }}
                  />
                </div>
              </article>
            );
          })}
        </div>
      )}
    </article>
  );
}

export default function DashboardPage() {
  const [overview, setOverview] = useState<AnalyticsOverviewRead | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadOverview() {
      setIsLoading(true);
      setError(null);

      try {
        const response = await getAnalyticsOverview();
        if (!isMounted) {
          return;
        }
        setOverview(response);
      } catch {
        if (!isMounted) {
          return;
        }
        setError("Unable to load the analytics dashboard right now.");
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    void loadOverview();

    return () => {
      isMounted = false;
    };
  }, []);

  const adoptionRate = overview?.ai_adoption_rate ?? 0;
  const adoptionPercentage = Math.round(adoptionRate * 100);
  const adoptionWidth = `${adoptionPercentage > 0 ? Math.max(adoptionPercentage, 4) : 0}%`;

  return (
    <section className="page-stack">
      <div className="section-hero">
        <div>
          <p className="panel-tag">Step 32 · Analytics</p>
          <h3>Operations analytics command center</h3>
          <p>
            Track queue pressure, ticket mix, and AI review adoption from one dashboard so the
            support team can explain both operational health and AI value during demos.
          </p>
        </div>
      </div>

      {isLoading ? (
        <article className="panel">
          <p className="panel-state">Loading dashboard analytics...</p>
        </article>
      ) : null}

      {error ? (
        <article className="panel">
          <p className="form-error">{error}</p>
        </article>
      ) : null}

      {!isLoading && !error && overview ? (
        <>
          <section className="content-grid content-grid--analytics-stats">
            <article className="panel analytics-stat-card analytics-stat-card--total">
              <span className="analytics-stat-card__label">Total tickets</span>
              <strong className="analytics-stat-card__value">{overview.total_tickets}</strong>
              <p>All tickets currently stored in the platform.</p>
            </article>

            <article className="panel analytics-stat-card analytics-stat-card--open">
              <span className="analytics-stat-card__label">Open workload</span>
              <strong className="analytics-stat-card__value">{overview.open_tickets}</strong>
              <p>Tickets still in progress, waiting review, or pending action.</p>
            </article>

            <article className="panel analytics-stat-card analytics-stat-card--resolved">
              <span className="analytics-stat-card__label">Resolved tickets</span>
              <strong className="analytics-stat-card__value">{overview.resolved_tickets}</strong>
              <p>Cases that have reached a resolved or closed outcome.</p>
            </article>

            <article className="panel analytics-stat-card analytics-stat-card--urgent">
              <span className="analytics-stat-card__label">Urgent tickets</span>
              <strong className="analytics-stat-card__value">{overview.urgent_tickets}</strong>
              <p>Highest-priority cases that deserve rapid operational attention.</p>
            </article>
          </section>

          <section className="content-grid content-grid--detail">
            <article className="panel panel--feature analytics-adoption-card">
              <div className="panel-heading">
                <div>
                  <p className="panel-tag">AI Adoption</p>
                  <h3>Review acceptance at a glance</h3>
                </div>
                <span className="badge badge--score">{formatPercentage(adoptionRate)}</span>
              </div>

              <div className="analytics-adoption-card__hero">
                <div>
                  <strong>{overview.ai_approved_count}</strong>
                  <span>approved or edited suggestions</span>
                </div>
                <div>
                  <strong>{overview.ai_suggestions_count}</strong>
                  <span>total AI reply drafts</span>
                </div>
              </div>

              <div className="adoption-meter" aria-hidden="true">
                <div className="adoption-meter__fill" style={{ width: adoptionWidth }} />
              </div>

              <p className="analytics-adoption-card__copy">
                AI adoption rate is calculated in the service layer as approved-or-edited
                suggestions divided by total generated suggestions.
              </p>
            </article>

            <article className="panel">
              <div className="panel-heading">
                <div>
                  <p className="panel-tag">Signal Summary</p>
                  <h3>What this snapshot says</h3>
                </div>
              </div>

              <div className="detail-stack detail-stack--compact">
                <div className="detail-row">
                  <span>Queue pressure</span>
                  <strong>
                    {overview.total_tickets === 0
                      ? "No queue data yet"
                      : `${overview.open_tickets} of ${overview.total_tickets} tickets still need work`}
                  </strong>
                </div>
                <div className="detail-row">
                  <span>Urgency share</span>
                  <strong>
                    {overview.total_tickets === 0
                      ? "0% of queue marked urgent"
                      : `${Math.round((overview.urgent_tickets / overview.total_tickets) * 100)}% of tickets are urgent`}
                  </strong>
                </div>
                <div className="detail-row">
                  <span>AI throughput</span>
                  <strong>
                    {overview.ai_suggestions_count === 0
                      ? "No AI drafts reviewed yet"
                      : `${overview.ai_approved_count} reviewed drafts reached an accepted outcome`}
                  </strong>
                </div>
              </div>
            </article>
          </section>

          <section className="content-grid">
            <DistributionChart
              title="Category distribution"
              tag="Ticket Mix"
              emptyCopy="No tickets are available yet, so category distribution is empty."
              data={overview.category_distribution}
              labels={CATEGORY_LABELS}
              tone="category"
            />

            <DistributionChart
              title="Priority distribution"
              tag="Priority Mix"
              emptyCopy="No tickets are available yet, so priority distribution is empty."
              data={overview.priority_distribution}
              labels={PRIORITY_LABELS}
              tone="priority"
            />
          </section>
        </>
      ) : null}
    </section>
  );
}
