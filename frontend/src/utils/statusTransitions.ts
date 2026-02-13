import type { AccountStatus } from '@/types/account';

/** Mirrors Account.VALID_TRANSITIONS from accounts/models.py. */
export const VALID_TRANSITIONS: Record<AccountStatus, AccountStatus[]> = {
  new: ['assigned', 'closed'],
  assigned: ['in_contact', 'closed', 'disputed'],
  in_contact: ['negotiating', 'closed', 'disputed'],
  negotiating: ['payment_plan', 'settled', 'closed', 'disputed'],
  payment_plan: ['settled', 'closed', 'disputed'],
  settled: ['closed'],
  closed: [],
  disputed: ['in_contact', 'closed'],
};

export function canTransitionTo(current: AccountStatus, target: AccountStatus): boolean {
  return VALID_TRANSITIONS[current]?.includes(target) ?? false;
}
