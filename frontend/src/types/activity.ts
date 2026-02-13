/** Matches Activity.ActivityType choices. */
export type ActivityType = 'note' | 'status_change' | 'payment' | 'assignment' | 'import';

/** Matches ActivitySerializer fields. */
export interface Activity {
  id: string;
  activity_type: ActivityType;
  description: string;
  metadata: Record<string, unknown>;
  user_name: string;
  created_at: string;
}
