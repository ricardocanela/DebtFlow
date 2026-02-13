import { Tag } from 'antd';
import type { AccountStatus } from '@/types/account';
import type { PaymentStatus } from '@/types/payment';
import type { ImportJobStatus } from '@/types/importJob';
import { ACCOUNT_STATUS_COLORS } from '@/utils/statusColors';
import { PAYMENT_STATUS_COLORS } from '@/utils/statusColors';
import { IMPORT_STATUS_COLORS } from '@/utils/statusColors';
import { ACCOUNT_STATUS_LABELS } from '@/utils/constants';
import { PAYMENT_STATUS_LABELS, IMPORT_STATUS_LABELS } from '@/utils/constants';

type StatusType = 'account' | 'payment' | 'import';

interface StatusTagProps {
  status: string;
  type?: StatusType;
}

export function StatusTag({ status, type = 'account' }: StatusTagProps) {
  let color: string;
  let label: string;

  switch (type) {
    case 'payment':
      color = PAYMENT_STATUS_COLORS[status as PaymentStatus] || 'default';
      label = PAYMENT_STATUS_LABELS[status as PaymentStatus] || status;
      break;
    case 'import':
      color = IMPORT_STATUS_COLORS[status as ImportJobStatus] || 'default';
      label = IMPORT_STATUS_LABELS[status as ImportJobStatus] || status;
      break;
    default:
      color = ACCOUNT_STATUS_COLORS[status as AccountStatus] || 'default';
      label = ACCOUNT_STATUS_LABELS[status as AccountStatus] || status;
  }

  return <Tag color={color}>{label}</Tag>;
}
