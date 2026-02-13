import { Card, Table, Progress } from 'antd';
import type { AgingBucket } from '@/types/analytics';
import { formatCurrency } from '@/utils/formatCurrency';

interface AgingReportTableProps {
  data: AgingBucket[];
  loading?: boolean;
}

export function AgingReportTable({ data, loading }: AgingReportTableProps) {
  const total = data.reduce((sum, b) => sum + b.count, 0) || 1;

  const columns = [
    {
      title: 'Aging Bucket',
      dataIndex: 'bucket',
      key: 'bucket',
    },
    {
      title: 'Count',
      dataIndex: 'count',
      key: 'count',
      align: 'right' as const,
    },
    {
      title: 'Total Balance',
      dataIndex: 'total_balance',
      key: 'total_balance',
      align: 'right' as const,
      render: (val: string) => formatCurrency(val),
    },
    {
      title: 'Distribution',
      key: 'distribution',
      render: (_: unknown, record: AgingBucket) => (
        <Progress
          percent={Math.round((record.count / total) * 100)}
          size="small"
          strokeColor={
            record.bucket.includes('90') ? '#f5222d' : record.bucket.includes('61') ? '#fa8c16' : '#1677ff'
          }
        />
      ),
    },
  ];

  return (
    <Card title="Aging Report">
      <Table
        dataSource={data}
        columns={columns}
        rowKey="bucket"
        loading={loading}
        pagination={false}
        size="small"
      />
    </Card>
  );
}
