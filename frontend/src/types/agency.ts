/** Matches AgencySerializer fields. */
export interface Agency {
  id: string;
  name: string;
  license_number: string | null;
  settings: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
