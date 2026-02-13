import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { AuthUser, UserRole } from '@/types/auth';

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: AuthUser | null;
  isAuthenticated: boolean;
}

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join(''),
    );
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
}

function isTokenExpired(token: string): boolean {
  const payload = decodeJwtPayload(token);
  if (!payload || typeof payload.exp !== 'number') return true;
  return Date.now() >= payload.exp * 1000;
}

function extractUserFromToken(token: string): AuthUser | null {
  const payload = decodeJwtPayload(token);
  if (!payload) return null;

  let role: UserRole = 'collector';
  if (payload.is_superuser) {
    role = 'superuser';
  } else if (Array.isArray(payload.groups) && payload.groups.includes('agency_admin')) {
    role = 'agency_admin';
  }

  return {
    id: payload.user_id as number,
    username: (payload.username as string) || '',
    email: (payload.email as string) || '',
    first_name: (payload.first_name as string) || '',
    last_name: (payload.last_name as string) || '',
    role,
    agency_id: payload.agency_id as string | undefined,
    collector_id: payload.collector_id as string | undefined,
  };
}

function loadInitialState(): AuthState {
  const accessToken = localStorage.getItem('access_token');
  const refreshToken = localStorage.getItem('refresh_token');

  if (accessToken && !isTokenExpired(accessToken)) {
    const user = extractUserFromToken(accessToken);
    return { accessToken, refreshToken, user, isAuthenticated: !!user };
  }

  if (refreshToken && !isTokenExpired(refreshToken)) {
    return { accessToken: null, refreshToken, user: null, isAuthenticated: false };
  }

  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  return { accessToken: null, refreshToken: null, user: null, isAuthenticated: false };
}

const authSlice = createSlice({
  name: 'auth',
  initialState: loadInitialState(),
  reducers: {
    setCredentials(state, action: PayloadAction<{ access: string; refresh: string }>) {
      const { access, refresh } = action.payload;
      state.accessToken = access;
      state.refreshToken = refresh;
      state.user = extractUserFromToken(access);
      state.isAuthenticated = !!state.user;
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
    },
    updateTokens(state, action: PayloadAction<{ access: string; refresh?: string }>) {
      state.accessToken = action.payload.access;
      if (action.payload.refresh) {
        state.refreshToken = action.payload.refresh;
        localStorage.setItem('refresh_token', action.payload.refresh);
      }
      state.user = extractUserFromToken(action.payload.access);
      state.isAuthenticated = !!state.user;
      localStorage.setItem('access_token', action.payload.access);
    },
    logout(state) {
      state.accessToken = null;
      state.refreshToken = null;
      state.user = null;
      state.isAuthenticated = false;
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    },
  },
});

export const { setCredentials, updateTokens, logout } = authSlice.actions;
export default authSlice.reducer;
