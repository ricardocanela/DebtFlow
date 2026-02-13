import {
  DashboardOutlined,
  UnorderedListOutlined,
  FolderOutlined,
  DollarOutlined,
  CloudUploadOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { useRole } from '@/hooks/useRole';

export interface MenuRoute {
  path: string;
  name: string;
  icon: React.ReactNode;
}

export function useMenuRoutes(): MenuRoute[] {
  const { isAdmin } = useRole();

  const routes: MenuRoute[] = [];

  if (isAdmin) {
    routes.push({ path: '/', name: 'Dashboard', icon: <DashboardOutlined /> });
  }

  routes.push({ path: '/worklist', name: 'My Queue', icon: <UnorderedListOutlined /> });

  if (isAdmin) {
    routes.push({ path: '/accounts', name: 'All Accounts', icon: <FolderOutlined /> });
  }

  routes.push({ path: '/payments', name: 'Payments', icon: <DollarOutlined /> });

  if (isAdmin) {
    routes.push({ path: '/imports', name: 'Imports', icon: <CloudUploadOutlined /> });
    routes.push({ path: '/settings', name: 'Settings', icon: <SettingOutlined /> });
  }

  return routes;
}
