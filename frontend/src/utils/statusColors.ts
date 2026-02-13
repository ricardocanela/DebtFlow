import type { AccountStatus } from '@/types/account';
import type { PaymentStatus } from '@/types/payment';
import type { ImportJobStatus } from '@/types/importJob';

export const ACCOUNT_STATUS_COLORS: Record<AccountStatus, string> = {
  new: 'blue',
  assigned: 'cyan',
  in_contact: 'geekblue',
  negotiating: 'orange',
  payment_plan: 'gold',
  settled: 'green',
  closed: 'default',
  disputed: 'red',
};

export const PAYMENT_STATUS_COLORS: Record<PaymentStatus, string> = {
  pending: 'orange',
  completed: 'green',
  failed: 'red',
  refunded: 'purple',
};

export const IMPORT_STATUS_COLORS: Record<ImportJobStatus, string> = {
  pending: 'default',
  processing: 'blue',
  completed: 'green',
  failed: 'red',
};
