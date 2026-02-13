import { Table, Button, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { useNavigate } from 'react-router-dom';
import type { Payment, PaymentMethod } from '@/types/payment';
import { StatusTag } from '@/components/common/StatusTag';
import { CurrencyDisplay } from '@/components/common/CurrencyDisplay';
import { formatDateTime } from '@/utils/formatDate';
import { PAYMENT_METHOD_LABELS } from '@/utils/constants';
import { useRole } from '@/hooks/useRole';

const { Text } = Typography;

interface PaymentTableProps {
  data: Payment[];
  loading?: boolean;
  hasNext?: boolean;
  hasPrevious?: boolean;
  onLoadNext?: () => void;
  onLoadPrevious?: () => void;
  onRefund?: (payment: Payment) => void;
}

export function PaymentTable({
  data,
  loading,
  hasNext,
  hasPrevious,
  onLoadNext,
  onLoadPrevious,
  onRefund,
}: PaymentTableProps) {
  const navigate = useNavigate();
  const { isAdmin } = useRole();

  const columns: ColumnsType<Payment> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 100,
      render: (val: string) => <Text code>{val.slice(0, 8)}</Text>,
    },
    {
      title: 'Account',
      dataIndex: 'account',
      key: 'account',
      width: 100,
      render: (val: string) => (
        <Text
          code
          style={{ cursor: 'pointer' }}
          onClick={() => navigate(`/accounts/${val}`)}
        >
          {val.slice(0, 8)}
        </Text>
      ),
    },
    {
      title: 'Amount',
      dataIndex: 'amount',
      key: 'amount',
      width: 120,
      align: 'right',
      render: (val: string) => <CurrencyDisplay value={val} strong />,
    },
    {
      title: 'Method',
      dataIndex: 'payment_method',
      key: 'payment_method',
      width: 120,
      render: (val: PaymentMethod) => PAYMENT_METHOD_LABELS[val],
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 110,
      render: (val: string) => <StatusTag status={val} type="payment" />,
    },
    {
      title: 'Processor',
      dataIndex: 'processor_name',
      key: 'processor_name',
      width: 120,
    },
    {
      title: 'Date',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (val: string) => formatDateTime(val),
    },
    ...(isAdmin
      ? [
          {
            title: 'Actions',
            key: 'actions',
            width: 90,
            render: (_: unknown, record: Payment) =>
              record.status === 'completed' && onRefund ? (
                <Button size="small" danger onClick={() => onRefund(record)}>
                  Refund
                </Button>
              ) : null,
          },
        ]
      : []),
  ];

  return (
    <div>
      <Table<Payment>
        dataSource={data}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={false}
        size="small"
        scroll={{ x: 1000 }}
      />
      <div style={{ display: 'flex', justifyContent: 'center', padding: '16px 0', gap: 8 }}>
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
      </div>
    </div>
  );
}
