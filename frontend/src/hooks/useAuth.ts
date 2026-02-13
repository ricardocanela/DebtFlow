import { useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { setCredentials, logout as logoutAction } from '@/store/authSlice';
import { baseApi } from '@/api/baseApi';
import { useLoginMutation } from '@/api/authApi';
import type { LoginCredentials } from '@/types/auth';

export function useAuth() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, user } = useAppSelector((state) => state.auth);
  const [loginMutation, { isLoading: isLoggingIn, error: loginError }] = useLoginMutation();

  const login = useCallback(
    async (credentials: LoginCredentials) => {
      const result = await loginMutation(credentials).unwrap();
      dispatch(setCredentials(result));

      // Redirect to original destination or role-based default
      const from = (location.state as { from?: { pathname: string } })?.from?.pathname;
      if (from && from !== '/login') {
        navigate(from);
        return;
      }

      // Navigate based on role from JWT claims
      const accessPayload = JSON.parse(atob(result.access.split('.')[1]));
      const isAdmin =
        accessPayload.is_superuser ||
        (Array.isArray(accessPayload.groups) && accessPayload.groups.includes('agency_admin'));
      navigate(isAdmin ? '/' : '/worklist');
    },
    [loginMutation, dispatch, navigate, location.state],
  );

  const logout = useCallback(() => {
    dispatch(logoutAction());
    dispatch(baseApi.util.resetApiState());
    navigate('/login');
  }, [dispatch, navigate]);

  return { isAuthenticated, user, login, logout, isLoggingIn, loginError };
}
