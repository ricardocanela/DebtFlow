/** Matches DRF CursorPagination response shape. */
export interface CursorPaginatedResponse<T> {
  next: string | null;
  previous: string | null;
  results: T[];
}

/** Standard DRF error response. */
export interface ApiError {
  detail?: string;
  [field: string]: string | string[] | undefined;
}
