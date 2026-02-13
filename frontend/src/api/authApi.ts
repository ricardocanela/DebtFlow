import { baseApi } from './baseApi';
import type { LoginCredentials, TokenPair } from '@/types/auth';

export interface UserProfile {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_superuser: boolean;
  groups: string[];
  collector_id: string | null;
  agency_id: string | null;
}

export const authApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    login: builder.mutation<TokenPair, LoginCredentials>({
      query: (credentials) => ({
        url: '/auth/token/',
        method: 'POST',
        body: credentials,
      }),
    }),
    refreshToken: builder.mutation<{ access: string; refresh?: string }, { refresh: string }>({
      query: (body) => ({
        url: '/auth/token/refresh/',
        method: 'POST',
        body,
      }),
    }),
    getMe: builder.query<UserProfile, void>({
      query: () => '/auth/me/',
    }),
  }),
});

export const { useLoginMutation, useGetMeQuery } = authApi;
