/** Matches TokenObtainPairView response. */
export interface TokenPair {
  access: string;
  refresh: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export type UserRole = 'agency_admin' | 'collector' | 'superuser';

export interface AuthUser {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  agency_id?: string;
  collector_id?: string;
}
