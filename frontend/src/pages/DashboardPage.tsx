import { useState } from 'react';
import { Row, Col, Typography } from 'antd';
import {
  useGetDashboardQuery,
  useGetCollectorPerformanceQuery,
  useGetPaymentTrendsQuery,
  useGetAgingReportQuery,
} from '@/api/analyticsApi';
import { KpiCards } from '@/components/analytics/KpiCards';
import { StatusDistributionChart } from '@/components/analytics/StatusDistributionChart';
import { PaymentTrendsChart } from '@/components/analytics/PaymentTrendsChart';
import { GranularitySelector } from '@/components/analytics/GranularitySelector';
import { AgingReportTable } from '@/components/analytics/AgingReportTable';
import { CollectorLeaderboard } from '@/components/analytics/CollectorLeaderboard';
import { LoadingSkeleton } from '@/components/common/LoadingSkeleton';
import type { TrendGranularity } from '@/types/analytics';

const { Title } = Typography;

export function DashboardPage() {
  const [granularity, setGranularity] = useState<TrendGranularity>('day');

  const { data: dashboard, isLoading: dashLoading } = useGetDashboardQuery();
  const { data: collectors, isLoading: collectorsLoading } = useGetCollectorPerformanceQuery();
  const { data: trends, isLoading: trendsLoading } = useGetPaymentTrendsQuery({
    granularity,
    days: 30,
  });
  const { data: aging, isLoading: agingLoading } = useGetAgingReportQuery();

  if (dashLoading) return <LoadingSkeleton cards={4} />;

  return (
    <div>
      <Title level={4} style={{ marginBottom: 24 }}>
        Dashboard
      </Title>

      {dashboard && <KpiCards data={dashboard} loading={dashLoading} />}

      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col xs={24} lg={12}>
          <StatusDistributionChart
            data={dashboard?.accounts_by_status || {}}
            loading={dashLoading}
          />
        </Col>
        <Col xs={24} lg={12}>
          <PaymentTrendsChart
            data={trends || []}
            loading={trendsLoading}
            extra={<GranularitySelector value={granularity} onChange={setGranularity} />}
          />
        </Col>
      </Row>

      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col xs={24} lg={12}>
          <AgingReportTable data={aging || []} loading={agingLoading} />
        </Col>
        <Col xs={24} lg={12}>
          <CollectorLeaderboard data={collectors || []} loading={collectorsLoading} />
        </Col>
      </Row>
    </div>
  );
}
