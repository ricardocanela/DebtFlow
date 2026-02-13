import { baseApi } from './baseApi';
import type { CursorPaginatedResponse } from '@/types/common';
import type { Collector } from '@/types/collector';

export const collectorsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getCollectors: builder.query<Collector[], void>({
      query: () => '/collectors/',
      transformResponse: (response: CursorPaginatedResponse<Collector> | Collector[]) => {
        if (Array.isArray(response)) return response;
        return response.results;
      },
      providesTags: ['Collector'],
    }),
  }),
});

export const { useGetCollectorsQuery } = collectorsApi;
