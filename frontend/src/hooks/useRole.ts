import { useAppSelector } from '@/store/hooks';
import type { UserRole } from '@/types/auth';

export function useRole() {
  const user = useAppSelector((state) => state.auth.user);
  const role = user?.role;

  return {
    role,
    isAdmin: role === 'agency_admin' || role === 'superuser',
    isCollector: role === 'collector',
    isSuperuser: role === 'superuser',
    hasRole: (roles: UserRole[]) => !!role && roles.includes(role),
  };
}
