import { Card, Table, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { useGetPaymentsQuery } from '@/api/paymentsApi';
import { StatusTag } from '@/components/common/StatusTag';
import { CurrencyDisplay } from '@/components/common/CurrencyDisplay';
import { formatDateTime } from '@/utils/formatDate';
import { PAYMENT_METHOD_LABELS } from '@/utils/constants';
import type { Payment, PaymentMethod } from '@/types/payment';

const { Text } = Typography;

interface PaymentSummaryProps {
  accountId: string;
}

export function PaymentSummary({ accountId }: PaymentSummaryProps) {
  const { data, isLoading } = useGetPaymentsQuery({ account: accountId });
  const payments = data?.results || [];

  const columns: ColumnsType<Payment> = [
    {
      title: 'Amount',
      dataIndex: 'amount',
      key: 'amount',
      render: (val: string) => <CurrencyDisplay value={val} strong />,
    },
    {
      title: 'Method',
      dataIndex: 'payment_method',
      key: 'payment_method',
      render: (val: PaymentMethod) => <Text>{PAYMENT_METHOD_LABELS[val]}</Text>,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (val: string) => <StatusTag status={val} type="payment" />,
    },
    {
      title: 'Date',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (val: string) => <Text type="secondary">{formatDateTime(val)}</Text>,
    },
  ];

  return (
    <Card title="Payments" size="small">
      <Table<Payment>
        dataSource={payments}
        columns={columns}
        rowKey="id"
        loading={isLoading}
        pagination={false}
        size="small"
        locale={{ emptyText: 'No payments yet' }}
      />
    </Card>
  );
}
