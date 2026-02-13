import { Card, Descriptions, Typography } from 'antd';
import type { AccountDetail } from '@/types/account';
import { StatusTag } from '@/components/common/StatusTag';
import { CurrencyDisplay } from '@/components/common/CurrencyDisplay';
import { PriorityBadge } from '@/components/common/PriorityBadge';
import { formatDate, formatDateTime } from '@/utils/formatDate';

const { Text } = Typography;

interface AccountSummaryCardProps {
  account: AccountDetail;
}

export function AccountSummaryCard({ account }: AccountSummaryCardProps) {
  return (
    <Card size="small">
      <Descriptions column={{ xs: 1, sm: 2, lg: 3 }} size="small">
        <Descriptions.Item label="Original Amount">
          <CurrencyDisplay value={account.original_amount} type="secondary" />
        </Descriptions.Item>
        <Descriptions.Item label="Current Balance">
          <CurrencyDisplay value={account.current_balance} strong />
        </Descriptions.Item>
        <Descriptions.Item label="Status">
          <StatusTag status={account.status} />
        </Descriptions.Item>
        <Descriptions.Item label="Priority">
          <PriorityBadge priority={account.priority} />
        </Descriptions.Item>
        <Descriptions.Item label="Due Date">
          <Text>{formatDate(account.due_date)}</Text>
        </Descriptions.Item>
        <Descriptions.Item label="Last Contact">
          <Text>{formatDateTime(account.last_contact_at)}</Text>
        </Descriptions.Item>
        <Descriptions.Item label="Collector">
          {account.assigned_to ? (
            <Text>{account.assigned_to.full_name || account.assigned_to.username}</Text>
          ) : (
            <Text type="secondary">Unassigned</Text>
          )}
        </Descriptions.Item>
        <Descriptions.Item label="Ref">
          <Text code>{account.external_ref}</Text>
        </Descriptions.Item>
        <Descriptions.Item label="Agency">
          <Text>{account.agency.name}</Text>
        </Descriptions.Item>
      </Descriptions>
    </Card>
  );
}
