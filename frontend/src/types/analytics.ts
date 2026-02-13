/** Matches DashboardSerializer fields. */
export interface DashboardKpis {
  total_accounts: number;
  total_collected: string;
  collection_rate: number;
  avg_days_to_settle: number;
  accounts_by_status: Record<string, number>;
}

/** Matches CollectorPerformanceSerializer fields. */
export interface CollectorPerformance {
  collector_id: string;
  collector_name: string;
  total_accounts: number;
  total_collected: string;
  success_rate: number;
}

/** Matches PaymentTrendSerializer fields. */
export interface PaymentTrend {
  period: string;
  total_amount: string;
  count: number;
}

/** Matches AgingBucketSerializer fields. */
export interface AgingBucket {
  bucket: string;
  count: number;
  total_balance: string;
}

export type TrendGranularity = 'day' | 'week' | 'month';
