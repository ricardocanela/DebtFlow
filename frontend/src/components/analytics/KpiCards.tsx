import { Row, Col, Card, Statistic } from 'antd';
import {
  TeamOutlined,
  DollarOutlined,
  PercentageOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import type { DashboardKpis } from '@/types/analytics';
import { formatCurrency } from '@/utils/formatCurrency';

interface KpiCardsProps {
  data: DashboardKpis;
  loading?: boolean;
}

export function KpiCards({ data, loading }: KpiCardsProps) {
  return (
    <Row gutter={16}>
      <Col xs={24} sm={12} lg={6}>
        <Card loading={loading}>
          <Statistic
            title="Total Accounts"
            value={data.total_accounts}
            prefix={<TeamOutlined />}
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card loading={loading}>
          <Statistic
            title="Total Collected"
            value={formatCurrency(data.total_collected)}
            prefix={<DollarOutlined />}
            valueStyle={{ color: '#3f8600' }}
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card loading={loading}>
          <Statistic
            title="Collection Rate"
            value={data.collection_rate}
            precision={1}
            suffix="%"
            prefix={<PercentageOutlined />}
            valueStyle={{ color: data.collection_rate > 50 ? '#3f8600' : '#cf1322' }}
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card loading={loading}>
          <Statistic
            title="Avg Days to Settle"
            value={data.avg_days_to_settle}
            precision={0}
            suffix=" days"
            prefix={<ClockCircleOutlined />}
          />
        </Card>
      </Col>
    </Row>
  );
}
