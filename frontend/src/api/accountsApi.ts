import { baseApi } from './baseApi';
import type { CursorPaginatedResponse } from '@/types/common';
import type {
  AccountListItem,
  AccountDetail,
  AccountFilterParams,
  AssignAccountPayload,
  TransitionPayload,
  AddNotePayload,
  AccountCreatePayload,
} from '@/types/account';
import type { Activity } from '@/types/activity';

export const accountsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getAccounts: builder.query<CursorPaginatedResponse<AccountListItem>, AccountFilterParams>({
      query: (params) => ({
        url: '/accounts/',
        params,
      }),
      providesTags: (result) =>
        result
          ? [
              ...result.results.map(({ id }) => ({ type: 'Account' as const, id })),
              { type: 'Account', id: 'LIST' },
            ]
          : [{ type: 'Account', id: 'LIST' }],
    }),

    getAccount: builder.query<AccountDetail, string>({
      query: (id) => `/accounts/${id}/`,
      providesTags: (_result, _error, id) => [{ type: 'AccountDetail', id }],
    }),

    createAccount: builder.mutation<AccountDetail, AccountCreatePayload>({
      query: (body) => ({
        url: '/accounts/',
        method: 'POST',
        body,
      }),
      invalidatesTags: [{ type: 'Account', id: 'LIST' }],
    }),

    updateAccount: builder.mutation<AccountDetail, { id: string; data: Record<string, unknown> }>({
      query: ({ id, data }) => ({
        url: `/accounts/${id}/`,
        method: 'PATCH',
        body: data,
      }),
      invalidatesTags: (_result, _error, { id }) => [
        { type: 'Account', id },
        { type: 'AccountDetail', id },
      ],
    }),

    assignAccount: builder.mutation<AccountDetail, { id: string; data: AssignAccountPayload }>({
      query: ({ id, data }) => ({
        url: `/accounts/${id}/assign/`,
        method: 'POST',
        body: data,
      }),
      invalidatesTags: (_result, _error, { id }) => [
        { type: 'Account', id },
        { type: 'AccountDetail', id },
        { type: 'Account', id: 'LIST' },
        'Activity',
      ],
    }),

    addNote: builder.mutation<Activity, { id: string; data: AddNotePayload }>({
      query: ({ id, data }) => ({
        url: `/accounts/${id}/add-note/`,
        method: 'POST',
        body: data,
      }),
      invalidatesTags: (_result, _error, { id }) => [{ type: 'AccountDetail', id }, 'Activity'],
    }),

    getTimeline: builder.query<
      CursorPaginatedResponse<Activity>,
      { id: string; cursor?: string }
    >({
      query: ({ id, cursor }) => ({
        url: `/accounts/${id}/timeline/`,
        params: cursor ? { cursor } : {},
      }),
      providesTags: ['Activity'],
    }),

    transitionAccount: builder.mutation<
      AccountDetail,
      { id: string; data: TransitionPayload }
    >({
      query: ({ id, data }) => ({
        url: `/accounts/${id}/transition/`,
        method: 'POST',
        body: data,
      }),
      invalidatesTags: (_result, _error, { id }) => [
        { type: 'Account', id },
        { type: 'AccountDetail', id },
        { type: 'Account', id: 'LIST' },
        'Activity',
        'Analytics',
      ],
    }),

    exportAccounts: builder.mutation<{ task_id: string; status: string }, AccountFilterParams>({
      query: (params) => ({
        url: '/accounts/export/',
        params,
      }),
    }),
  }),
});

export const {
  useGetAccountsQuery,
  useGetAccountQuery,
  useCreateAccountMutation,
  useUpdateAccountMutation,
  useAssignAccountMutation,
  useAddNoteMutation,
  useGetTimelineQuery,
  useTransitionAccountMutation,
  useExportAccountsMutation,
} = accountsApi;
