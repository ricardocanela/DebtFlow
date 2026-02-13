/** Matches CollectorSerializer fields. */
export interface Collector {
  id: string;
  username: string;
  full_name: string;
  agency: string;
  commission_rate: string;
  is_active: boolean;
  max_accounts: number;
}
