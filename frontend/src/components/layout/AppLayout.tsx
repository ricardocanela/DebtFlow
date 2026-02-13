import { useMemo } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, theme } from 'antd';
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import { setSidebarCollapsed, setGlobalSearchVisible } from '@/store/uiSlice';
import { useMenuRoutes } from './SideMenu';
import { AppHeader } from './AppHeader';
import { GlobalSearch } from '@/components/common/GlobalSearch';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';

const { Header, Sider, Content } = Layout;

export function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useAppDispatch();
  const collapsed = useAppSelector((state) => state.ui.sidebarCollapsed);
  const menuRoutes = useMenuRoutes();
  const { token } = theme.useToken();

  const menuItems = useMemo(
    () =>
      menuRoutes.map((route) => ({
        key: route.path,
        icon: route.icon,
        label: route.name,
      })),
    [menuRoutes],
  );

  const selectedKey = useMemo(() => {
    const match = menuRoutes.find((r) => {
      if (r.path === '/') return location.pathname === '/';
      return location.pathname.startsWith(r.path);
    });
    return match?.path || '/worklist';
  }, [location.pathname, menuRoutes]);

  useKeyboardShortcuts({
    'mod+k': () => dispatch(setGlobalSearchVisible(true)),
  });

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={(val) => dispatch(setSidebarCollapsed(val))}
        theme="light"
        style={{
          borderRight: `1px solid ${token.colorBorderSecondary}`,
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div
          style={{
            height: 48,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 700,
            fontSize: collapsed ? 16 : 20,
            color: token.colorPrimary,
            borderBottom: `1px solid ${token.colorBorderSecondary}`,
          }}
        >
          {collapsed ? 'DF' : 'DebtFlow'}
        </div>
        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ borderRight: 0 }}
        />
      </Sider>
      <Layout style={{ marginLeft: collapsed ? 80 : 200, transition: 'margin-left 0.2s' }}>
        <Header
          style={{
            background: token.colorBgContainer,
            padding: '0 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            borderBottom: `1px solid ${token.colorBorderSecondary}`,
            position: 'sticky',
            top: 0,
            zIndex: 10,
          }}
        >
          <AppHeader />
        </Header>
        <Content style={{ padding: 24, background: token.colorBgLayout }}>
          <Outlet />
        </Content>
      </Layout>
      <GlobalSearch />
    </Layout>
  );
}
