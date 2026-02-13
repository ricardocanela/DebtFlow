/** Matches SFTPImportJob.Status choices. */
export type ImportJobStatus = 'pending' | 'processing' | 'completed' | 'failed';

/** Matches SFTPImportJobSerializer fields. */
export interface ImportJob {
  id: string;
  agency: string;
  source_host: string;
  file_name: string;
  file_path_s3: string | null;
  status: ImportJobStatus;
  total_records: number;
  processed_ok: number;
  processed_errors: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

/** Matches SFTPImportJobDetailSerializer (adds error_details). */
export interface ImportJobDetail extends ImportJob {
  error_details: ImportError[];
}

/** Matches ImportErrorSerializer fields. */
export interface ImportError {
  line: number;
  error: string;
  data?: Record<string, unknown>;
}

/** Paginated error response from the errors endpoint. */
export interface ImportErrorsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: ImportError[];
}
