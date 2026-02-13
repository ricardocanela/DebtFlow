import { Typography } from 'antd';
import { formatCurrency } from '@/utils/formatCurrency';

const { Text } = Typography;

interface CurrencyDisplayProps {
  value: string | number;
  type?: 'secondary' | 'success' | 'danger' | 'warning';
  strong?: boolean;
}

export function CurrencyDisplay({ value, type, strong }: CurrencyDisplayProps) {
  return (
    <Text type={type} strong={strong} style={{ fontVariantNumeric: 'tabular-nums' }}>
      {formatCurrency(value)}
    </Text>
  );
}
