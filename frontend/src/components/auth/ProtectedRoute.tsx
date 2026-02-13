import { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Spin } from 'antd';
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import { updateTokens, logout } from '@/store/authSlice';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, refreshToken, accessToken } = useAppSelector((state) => state.auth);
  const dispatch = useAppDispatch();
  const location = useLocation();
  const [bootstrapping, setBootstrapping] = useState(!isAuthenticated && !!refreshToken);

  useEffect(() => {
    if (!isAuthenticated && refreshToken && !accessToken) {
      // Try to refresh the token on app init
      const tryRefresh = async () => {
        try {
          const response = await fetch(
            `${import.meta.env.VITE_API_BASE_URL || '/api/v1'}/auth/token/refresh/`,
            {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ refresh: refreshToken }),
            },
          );
          if (response.ok) {
            const data = await response.json();
            dispatch(updateTokens(data));
          } else {
            dispatch(logout());
          }
        } catch {
          dispatch(logout());
        } finally {
          setBootstrapping(false);
        }
      };
      tryRefresh();
    } else {
      setBootstrapping(false);
    }
  }, [isAuthenticated, refreshToken, accessToken, dispatch]);

  if (bootstrapping) {
    return (
      <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Spin size="large" tip="Loading..." />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
