import { baseApi } from './baseApi';
import type { CursorPaginatedResponse } from '@/types/common';
import type { ImportJob, ImportJobDetail, ImportErrorsResponse } from '@/types/importJob';

export const importsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getImportJobs: builder.query<CursorPaginatedResponse<ImportJob>, { cursor?: string }>({
      query: (params) => ({
        url: '/imports/',
        params,
      }),
      providesTags: (result) =>
        result
          ? [
              ...result.results.map(({ id }) => ({ type: 'ImportJob' as const, id })),
              { type: 'ImportJob', id: 'LIST' },
            ]
          : [{ type: 'ImportJob', id: 'LIST' }],
    }),

    getImportJob: builder.query<ImportJobDetail, string>({
      query: (id) => `/imports/${id}/`,
      providesTags: (_result, _error, id) => [{ type: 'ImportJob', id }],
    }),

    getImportErrors: builder.query<ImportErrorsResponse, { id: string; page?: number }>({
      query: ({ id, page = 1 }) => ({
        url: `/imports/${id}/errors/`,
        params: { page },
      }),
    }),

    triggerImport: builder.mutation<{ task_id: string; status: string }, void>({
      query: () => ({
        url: '/imports/trigger/',
        method: 'POST',
      }),
      invalidatesTags: [{ type: 'ImportJob', id: 'LIST' }],
    }),
  }),
});

export const {
  useGetImportJobsQuery,
  useGetImportJobQuery,
  useGetImportErrorsQuery,
  useTriggerImportMutation,
} = importsApi;
