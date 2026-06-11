import { apiClient } from "./client";

export type AnalyticsOverviewRead = {
  total_tickets: number;
  open_tickets: number;
  resolved_tickets: number;
  urgent_tickets: number;
  ai_suggestions_count: number;
  ai_approved_count: number;
  ai_adoption_rate: number;
  category_distribution: Record<string, number>;
  priority_distribution: Record<string, number>;
};

export async function getAnalyticsOverview() {
  const response = await apiClient.get<AnalyticsOverviewRead>("/analytics/overview");
  return response.data;
}
