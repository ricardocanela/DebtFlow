import { Table, Button, Space, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { useNavigate } from 'react-router-dom';
import type { AccountListItem } from '@/types/account';
import { StatusTag } from '@/components/common/StatusTag';
import { CurrencyDisplay } from '@/components/common/CurrencyDisplay';
import { PriorityBadge } from '@/components/common/PriorityBadge';
import { RelativeTime } from '@/components/common/RelativeTime';
import { formatDate } from '@/utils/formatDate';
import { isOverdue } from '@/utils/formatDate';

const { Text } = Typography;

interface AccountTableProps {
  data: AccountListItem[];
  loading?: boolean;
  hasNext?: boolean;
  hasPrevious?: boolean;
  onLoadNext?: () => void;
  onLoadPrevious?: () => void;
  selectedRowKey?: string | null;
  onRowSelect?: (id: string) => void;
}

export function AccountTable({
  data,
  loading,
  hasNext,
  hasPrevious,
  onLoadNext,
  onLoadPrevious,
  selectedRowKey,
  onRowSelect,
}: AccountTableProps) {
  const navigate = useNavigate();

  const columns: ColumnsType<AccountListItem> = [
    {
      title: 'Priority',
      dataIndex: 'priority',
      key: 'priority',
      width: 80,
      render: (val: number) => <PriorityBadge priority={val} />,
    },
    {
      title: 'Ref',
      dataIndex: 'external_ref',
      key: 'external_ref',
      width: 130,
      render: (val: string, record) => (
        <Text
          code
          style={{ cursor: 'pointer' }}
          onClick={() => navigate(`/accounts/${record.id}`)}
        >
          {val}
        </Text>
      ),
    },
    {
      title: 'Debtor',
      dataIndex: 'debtor_name',
      key: 'debtor_name',
      width: 200,
      render: (val: string) => <Text strong>{val}</Text>,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (val: string) => <StatusTag status={val} />,
    },
    {
      title: 'Balance',
      dataIndex: 'current_balance',
      key: 'current_balance',
      width: 120,
      align: 'right',
      render: (val: string) => <CurrencyDisplay value={val} strong />,
    },
    {
      title: 'Original',
      dataIndex: 'original_amount',
      key: 'original_amount',
      width: 120,
      align: 'right',
      render: (val: string) => <CurrencyDisplay value={val} type="secondary" />,
    },
    {
      title: 'Collector',
      dataIndex: 'collector_name',
      key: 'collector_name',
      width: 150,
      render: (val: string | null) =>
        val ? <Text>{val}</Text> : <Text type="secondary">Unassigned</Text>,
    },
    {
      title: 'Due Date',
      dataIndex: 'due_date',
      key: 'due_date',
      width: 110,
      render: (val: string | null) =>
        val ? (
          <Text type={isOverdue(val) ? 'danger' : undefined}>{formatDate(val)}</Text>
        ) : (
          <Text type="secondary">—</Text>
        ),
    },
    {
      title: 'Last Contact',
      dataIndex: 'last_contact_at',
      key: 'last_contact_at',
      width: 130,
      render: (val: string | null) => <RelativeTime value={val} />,
    },
  ];

  return (
    <div>
      <Table<AccountListItem>
        dataSource={data}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={false}
        size="small"
        scroll={{ x: 1200 }}
        rowClassName={(record) => (record.id === selectedRowKey ? 'ant-table-row-selected' : '')}
        onRow={(record) => ({
          onClick: () => onRowSelect?.(record.id),
          onDoubleClick: () => navigate(`/accounts/${record.id}`),
          style: { cursor: 'pointer' },
        })}
      />
      <div style={{ display: 'flex', justifyContent: 'center', padding: '16px 0' }}>
        <Space>
          {hasPrevious && (
            <Button onClick={onLoadPrevious} disabled={loading}>
              Previous
            </Button>
          )}
          {hasNext && (
            <Button type="primary" onClick={onLoadNext} disabled={loading}>
              Load More
            </Button>
          )}
        </Space>
      </div>
    </div>
  );
}
