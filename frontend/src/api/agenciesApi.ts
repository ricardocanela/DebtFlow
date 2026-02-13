import { baseApi } from './baseApi';
import type { CursorPaginatedResponse } from '@/types/common';
import type { Agency } from '@/types/agency';

export const agenciesApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getAgencies: builder.query<Agency[], void>({
      query: () => '/agencies/',
      transformResponse: (response: CursorPaginatedResponse<Agency> | Agency[]) => {
        if (Array.isArray(response)) return response;
        return response.results;
      },
      providesTags: ['Agency'],
    }),

    getAgency: builder.query<Agency, string>({
      query: (id) => `/agencies/${id}/`,
      providesTags: (_result, _error, id) => [{ type: 'Agency', id }],
    }),

    updateAgency: builder.mutation<Agency, { id: string; data: Partial<Agency> }>({
      query: ({ id, data }) => ({
        url: `/agencies/${id}/`,
        method: 'PATCH',
        body: data,
      }),
      invalidatesTags: (_result, _error, { id }) => [{ type: 'Agency', id }],
    }),
  }),
});

export const { useGetAgenciesQuery, useGetAgencyQuery, useUpdateAgencyMutation } = agenciesApi;
