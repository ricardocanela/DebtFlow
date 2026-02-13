import { Card, Table, Progress } from 'antd';
import type { CollectorPerformance } from '@/types/analytics';
import { formatCurrency } from '@/utils/formatCurrency';

interface CollectorLeaderboardProps {
  data: CollectorPerformance[];
  loading?: boolean;
}

export function CollectorLeaderboard({ data, loading }: CollectorLeaderboardProps) {
  const columns = [
    {
      title: '#',
      key: 'rank',
      width: 40,
      render: (_: unknown, __: unknown, index: number) => index + 1,
    },
    {
      title: 'Collector',
      dataIndex: 'collector_name',
      key: 'collector_name',
    },
    {
      title: 'Accounts',
      dataIndex: 'total_accounts',
      key: 'total_accounts',
      align: 'right' as const,
    },
    {
      title: 'Collected',
      dataIndex: 'total_collected',
      key: 'total_collected',
      align: 'right' as const,
      render: (val: string) => formatCurrency(val),
    },
    {
      title: 'Success Rate',
      dataIndex: 'success_rate',
      key: 'success_rate',
      render: (val: number) => (
        <Progress
          percent={Math.round(val)}
          size="small"
          strokeColor={val > 70 ? '#52c41a' : val > 40 ? '#faad14' : '#f5222d'}
        />
      ),
    },
  ];

  const sorted = [...data].sort((a, b) => b.success_rate - a.success_rate);

  return (
    <Card title="Collector Leaderboard">
      <Table
        dataSource={sorted}
        columns={columns}
        rowKey="collector_id"
        loading={loading}
        pagination={false}
        size="small"
      />
    </Card>
  );
}
