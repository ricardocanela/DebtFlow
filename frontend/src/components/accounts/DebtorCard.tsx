import { Card, Descriptions, Typography } from 'antd';
import { PhoneOutlined, MailOutlined, EnvironmentOutlined, IdcardOutlined } from '@ant-design/icons';
import type { Debtor } from '@/types/debtor';

const { Text } = Typography;

interface DebtorCardProps {
  debtor: Debtor;
}

export function DebtorCard({ debtor }: DebtorCardProps) {
  const address = [debtor.address_line1, debtor.address_city, debtor.address_state, debtor.address_zip]
    .filter(Boolean)
    .join(', ');

  return (
    <Card title="Debtor Information" size="small">
      <Descriptions column={1} size="small" labelStyle={{ width: 32, padding: '4px 8px' }}>
        <Descriptions.Item label={<IdcardOutlined />}>
          <Text strong>{debtor.full_name}</Text>
          {debtor.ssn_last4 && (
            <Text type="secondary" style={{ marginLeft: 8 }}>
              SSN: ***{debtor.ssn_last4}
            </Text>
          )}
        </Descriptions.Item>
        <Descriptions.Item label={<PhoneOutlined />}>
          {debtor.phone ? (
            <a href={`tel:${debtor.phone}`}>{debtor.phone}</a>
          ) : (
            <Text type="secondary">—</Text>
          )}
        </Descriptions.Item>
        <Descriptions.Item label={<MailOutlined />}>
          {debtor.email ? (
            <a href={`mailto:${debtor.email}`}>{debtor.email}</a>
          ) : (
            <Text type="secondary">—</Text>
          )}
        </Descriptions.Item>
        {address && (
          <Descriptions.Item label={<EnvironmentOutlined />}>
            <Text>{address}</Text>
          </Descriptions.Item>
        )}
      </Descriptions>
    </Card>
  );
}
