/** Matches DebtorSerializer fields. */
export interface Debtor {
  id: string;
  external_ref: string;
  full_name: string;
  ssn_last4: string;
  email: string | null;
  phone: string | null;
  address_line1: string | null;
  address_city: string | null;
  address_state: string | null;
  address_zip: string | null;
  created_at: string;
}
