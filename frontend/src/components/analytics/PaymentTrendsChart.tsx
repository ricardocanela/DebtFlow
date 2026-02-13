import { Card } from 'antd';
import { Line } from '@ant-design/charts';
import type { PaymentTrend } from '@/types/analytics';

interface PaymentTrendsChartProps {
  data: PaymentTrend[];
  loading?: boolean;
  extra?: React.ReactNode;
}

export function PaymentTrendsChart({ data, loading, extra }: PaymentTrendsChartProps) {
  const chartData = data.map((item) => ({
    period: item.period,
    amount: parseFloat(item.total_amount),
    count: item.count,
  }));

  return (
    <Card title="Payment Trends" loading={loading} extra={extra}>
      <Line
        data={chartData}
        xField="period"
        yField="amount"
        smooth
        point={{ shapeField: 'square', sizeField: 4 }}
        tooltip={{
          channel: 'y',
          valueFormatter: (v: number) => `$${v.toLocaleString()}`,
        }}
        height={300}
      />
    </Card>
  );
}
