import { Form, Input, Button, Card, Typography, Alert, Space } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { Navigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { useRole } from '@/hooks/useRole';
import type { LoginCredentials } from '@/types/auth';

const { Title, Text } = Typography;

export function LoginPage() {
  const { isAuthenticated, login, isLoggingIn, loginError } = useAuth();
  const { isAdmin } = useRole();

  if (isAuthenticated) {
    return <Navigate to={isAdmin ? '/' : '/worklist'} replace />;
  }

  const onFinish = (values: LoginCredentials) => {
    login(values);
  };

  const errorMessage =
    loginError && 'status' in loginError
      ? loginError.status === 401
        ? 'Invalid username or password.'
        : 'An error occurred. Please try again.'
      : undefined;

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#f0f2f5',
      }}
    >
      <Card style={{ width: 400, boxShadow: '0 2px 8px rgba(0,0,0,0.09)' }}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div style={{ textAlign: 'center' }}>
            <Title level={2} style={{ marginBottom: 4, color: '#1677ff' }}>
              DebtFlow
            </Title>
            <Text type="secondary">Debt Collection Management Platform</Text>
          </div>

          {errorMessage && (
            <Alert message={errorMessage} type="error" showIcon />
          )}

          <Form<LoginCredentials>
            name="login"
            onFinish={onFinish}
            layout="vertical"
            size="large"
          >
            <Form.Item
              name="username"
              rules={[{ required: true, message: 'Please enter your username' }]}
            >
              <Input prefix={<UserOutlined />} placeholder="Username" autoFocus />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[{ required: true, message: 'Please enter your password' }]}
            >
              <Input.Password prefix={<LockOutlined />} placeholder="Password" />
            </Form.Item>

            <Form.Item style={{ marginBottom: 0 }}>
              <Button type="primary" htmlType="submit" loading={isLoggingIn} block>
                Sign In
              </Button>
            </Form.Item>
          </Form>
        </Space>
      </Card>
    </div>
  );
}
