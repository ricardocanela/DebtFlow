import { Space, Button, Dropdown, Typography, Tag } from 'antd';
import { SearchOutlined, UserOutlined, LogoutOutlined } from '@ant-design/icons';
import { useAppDispatch } from '@/store/hooks';
import { setGlobalSearchVisible } from '@/store/uiSlice';
import { useAuth } from '@/hooks/useAuth';
import { KeyboardHint } from '@/components/common/KeyboardHint';
import type { MenuProps } from 'antd';

const { Text } = Typography;

export function AppHeader() {
  const dispatch = useAppDispatch();
  const { user, logout } = useAuth();

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'user-info',
      label: (
        <div>
          <div>
            <Text strong>
              {user?.first_name} {user?.last_name}
            </Text>
          </div>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {user?.username}
          </Text>
        </div>
      ),
      disabled: true,
    },
    { type: 'divider' },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
      onClick: logout,
    },
  ];

  return (
    <Space size="middle">
      <Button
        icon={<SearchOutlined />}
        onClick={() => dispatch(setGlobalSearchVisible(true))}
      >
        Search <KeyboardHint shortcut="⌘K" />
      </Button>
      {user && (
        <Tag color={user.role === 'agency_admin' || user.role === 'superuser' ? 'blue' : 'green'}>
          {user.role === 'superuser' ? 'Super Admin' : user.role === 'agency_admin' ? 'Admin' : 'Collector'}
        </Tag>
      )}
      <Dropdown menu={{ items: userMenuItems }} trigger={['click']}>
        <Button icon={<UserOutlined />} type="text">
          {user?.first_name || user?.username}
        </Button>
      </Dropdown>
    </Space>
  );
}
