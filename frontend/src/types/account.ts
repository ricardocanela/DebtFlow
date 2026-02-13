import type { Activity } from './activity';
import type { Agency } from './agency';
import type { Collector } from './collector';
import type { Debtor } from './debtor';

/** Matches Account.Status choices. */
export type AccountStatus =
  | 'new'
  | 'assigned'
  | 'in_contact'
  | 'negotiating'
  | 'payment_plan'
  | 'settled'
  | 'closed'
  | 'disputed';

/** Matches AccountListSerializer fields. */
export interface AccountListItem {
  id: string;
  external_ref: string;
  debtor_name: string;
  status: AccountStatus;
  original_amount: string;
  current_balance: string;
  priority: number;
  collector_name: string | null;
  due_date: string | null;
  last_contact_at: string | null;
  created_at: string;
}

/** Matches AccountDetailSerializer fields (nested). */
export interface AccountDetail {
  id: string;
  agency: Agency;
  debtor: Debtor;
  assigned_to: Collector | null;
  external_ref: string;
  original_amount: string;
  current_balance: string;
  status: AccountStatus;
  priority: number;
  due_date: string | null;
  last_contact_at: string | null;
  created_at: string;
  updated_at: string;
  recent_activities: Activity[];
}

/** Filter params matching AccountFilter from django-filter. */
export interface AccountFilterParams {
  status?: AccountStatus;
  collector?: string;
  agency?: string;
  min_balance?: number;
  max_balance?: number;
  created_after?: string;
  created_before?: string;
  due_after?: string;
  due_before?: string;
  priority?: number;
  search?: string;
  ordering?: string;
  cursor?: string;
}

/** Matches AssignAccountSerializer. */
export interface AssignAccountPayload {
  collector_id: string;
}

/** Matches TransitionSerializer. */
export interface TransitionPayload {
  new_status: AccountStatus;
  note?: string;
}

/** Matches AddNoteSerializer. */
export interface AddNotePayload {
  text: string;
}

/** Matches AccountCreateSerializer fields. */
export interface AccountCreatePayload {
  agency: string;
  debtor: string;
  external_ref: string;
  original_amount: number;
  current_balance?: number;
  status?: AccountStatus;
  priority?: number;
  due_date?: string;
}
