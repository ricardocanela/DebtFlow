import type { AccountStatus } from '@/types/account';
import type { PaymentMethod, PaymentStatus } from '@/types/payment';
import type { ImportJobStatus } from '@/types/importJob';

export const ACCOUNT_STATUS_LABELS: Record<AccountStatus, string> = {
  new: 'New',
  assigned: 'Assigned',
  in_contact: 'In Contact',
  negotiating: 'Negotiating',
  payment_plan: 'Payment Plan',
  settled: 'Settled',
  closed: 'Closed',
  disputed: 'Disputed',
};

export const PAYMENT_METHOD_LABELS: Record<PaymentMethod, string> = {
  card: 'Card',
  bank_transfer: 'Bank Transfer',
  check: 'Check',
  cash: 'Cash',
};

export const PAYMENT_STATUS_LABELS: Record<PaymentStatus, string> = {
  pending: 'Pending',
  completed: 'Completed',
  failed: 'Failed',
  refunded: 'Refunded',
};

export const IMPORT_STATUS_LABELS: Record<ImportJobStatus, string> = {
  pending: 'Pending',
  processing: 'Processing',
  completed: 'Completed',
  failed: 'Failed',
};

export const ALL_ACCOUNT_STATUSES: AccountStatus[] = [
  'new',
  'assigned',
  'in_contact',
  'negotiating',
  'payment_plan',
  'settled',
  'closed',
  'disputed',
];

export const ALL_PAYMENT_METHODS: PaymentMethod[] = ['card', 'bank_transfer', 'check', 'cash'];
