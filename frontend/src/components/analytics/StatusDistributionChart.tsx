import { Card } from 'antd';
import { Pie } from '@ant-design/charts';
import { ACCOUNT_STATUS_LABELS } from '@/utils/constants';
import type { AccountStatus } from '@/types/account';

interface StatusDistributionChartProps {
  data: Record<string, number>;
  loading?: boolean;
}

export function StatusDistributionChart({ data, loading }: StatusDistributionChartProps) {
  const chartData = Object.entries(data).map(([status, count]) => ({
    type: ACCOUNT_STATUS_LABELS[status as AccountStatus] || status,
    value: count,
  }));

  return (
    <Card title="Accounts by Status" loading={loading}>
      <Pie
        data={chartData}
        angleField="value"
        colorField="type"
        innerRadius={0.6}
        label={{
          text: 'value',
          style: { fontWeight: 'bold' },
        }}
        legend={{ color: { title: false, position: 'right', rowPadding: 5 } }}
        height={300}
      />
    </Card>
  );
}
