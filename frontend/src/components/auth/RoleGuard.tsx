import { Navigate } from 'react-router-dom';
import { useRole } from '@/hooks/useRole';
import type { UserRole } from '@/types/auth';

interface RoleGuardProps {
  roles: UserRole[];
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function RoleGuard({ roles, children, fallback }: RoleGuardProps) {
  const { hasRole } = useRole();

  if (!hasRole(roles)) {
    return fallback ? <>{fallback}</> : <Navigate to="/worklist" replace />;
  }

  return <>{children}</>;
}
