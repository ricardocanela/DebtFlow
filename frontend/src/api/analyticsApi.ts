import { baseApi } from './baseApi';
import type {
  DashboardKpis,
  CollectorPerformance,
  PaymentTrend,
  AgingBucket,
  TrendGranularity,
} from '@/types/analytics';

export const analyticsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getDashboard: builder.query<DashboardKpis, void>({
      query: () => '/analytics/dashboard/',
      providesTags: ['Analytics'],
    }),

    getCollectorPerformance: builder.query<CollectorPerformance[], void>({
      query: () => '/analytics/collectors/',
      providesTags: ['Analytics'],
    }),

    getPaymentTrends: builder.query<
      PaymentTrend[],
      { granularity?: TrendGranularity; days?: number }
    >({
      query: (params) => ({
        url: '/analytics/payments/trends/',
        params,
      }),
      providesTags: ['Analytics'],
    }),

    getAgingReport: builder.query<AgingBucket[], void>({
      query: () => '/analytics/aging-report/',
      providesTags: ['Analytics'],
    }),
  }),
});

export const {
  useGetDashboardQuery,
  useGetCollectorPerformanceQuery,
  useGetPaymentTrendsQuery,
  useGetAgingReportQuery,
} = analyticsApi;
