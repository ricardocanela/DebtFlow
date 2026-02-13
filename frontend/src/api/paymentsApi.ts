import { baseApi } from './baseApi';
import type { CursorPaginatedResponse } from '@/types/common';
import type {
  Payment,
  PaymentCreatePayload,
  PaymentProcessor,
  RefundPayload,
} from '@/types/payment';

export const paymentsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getPayments: builder.query<CursorPaginatedResponse<Payment>, { account?: string; cursor?: string }>({
      query: (params) => ({
        url: '/payments/',
        params,
      }),
      providesTags: (result) =>
        result
          ? [
              ...result.results.map(({ id }) => ({ type: 'Payment' as const, id })),
              { type: 'Payment', id: 'LIST' },
            ]
          : [{ type: 'Payment', id: 'LIST' }],
    }),

    createPayment: builder.mutation<Payment, PaymentCreatePayload>({
      query: (body) => ({
        url: '/payments/',
        method: 'POST',
        body,
      }),
      invalidatesTags: [
        { type: 'Payment', id: 'LIST' },
        'Account',
        'AccountDetail',
        'Analytics',
      ],
    }),

    refundPayment: builder.mutation<Payment, { id: string; data: RefundPayload }>({
      query: ({ id, data }) => ({
        url: `/payments/${id}/refund/`,
        method: 'POST',
        body: data,
      }),
      invalidatesTags: [
        { type: 'Payment', id: 'LIST' },
        'Account',
        'AccountDetail',
        'Analytics',
      ],
    }),

    getPaymentProcessors: builder.query<PaymentProcessor[], void>({
      query: () => '/payment-processors/',
      transformResponse: (response: CursorPaginatedResponse<PaymentProcessor> | PaymentProcessor[]) => {
        if (Array.isArray(response)) return response;
        return response.results;
      },
    }),
  }),
});

export const {
  useGetPaymentsQuery,
  useCreatePaymentMutation,
  useRefundPaymentMutation,
  useGetPaymentProcessorsQuery,
} = paymentsApi;
