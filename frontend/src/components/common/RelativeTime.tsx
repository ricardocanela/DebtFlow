import { Tooltip } from 'antd';
import { Typography } from 'antd';
import { formatRelativeTime, formatDateTime, daysSince } from '@/utils/formatDate';

const { Text } = Typography;

interface RelativeTimeProps {
  value: string | null | undefined;
  warnAfterDays?: number;
}

export function RelativeTime({ value, warnAfterDays = 7 }: RelativeTimeProps) {
  if (!value) {
    return <Text type="secondary">—</Text>;
  }

  const days = daysSince(value);
  const isWarning = days !== null && days > warnAfterDays;

  return (
    <Tooltip title={formatDateTime(value)}>
      <Text type={isWarning ? 'danger' : undefined}>{formatRelativeTime(value)}</Text>
    </Tooltip>
  );
}
