import { Form, Input, Button, Card, Typography, Switch, message, Spin } from 'antd';
import { useAppSelector } from '@/store/hooks';
import { useGetAgencyQuery, useUpdateAgencyMutation } from '@/api/agenciesApi';

const { Title } = Typography;

interface SettingsFormValues {
  name: string;
  license_number: string;
  is_active: boolean;
}

export function SettingsPage() {
  const [form] = Form.useForm<SettingsFormValues>();
  const agencyId = useAppSelector((state) => state.auth.user?.agency_id);

  const { data: agency, isLoading } = useGetAgencyQuery(agencyId!, { skip: !agencyId });
  const [updateAgency, { isLoading: isUpdating }] = useUpdateAgencyMutation();

  const handleSubmit = async (values: SettingsFormValues) => {
    if (!agencyId) return;
    try {
      await updateAgency({ id: agencyId, data: values }).unwrap();
      message.success('Settings updated');
    } catch {
      message.error('Failed to update settings');
    }
  };

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: 48 }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      <Title level={4} style={{ marginBottom: 16 }}>
        Agency Settings
      </Title>
      <Card style={{ maxWidth: 600 }}>
        {agency ? (
          <Form
            form={form}
            layout="vertical"
            initialValues={{
              name: agency.name,
              license_number: agency.license_number || '',
              is_active: agency.is_active,
            }}
            onFinish={handleSubmit}
          >
            <Form.Item
              name="name"
              label="Agency Name"
              rules={[{ required: true, message: 'Name is required' }]}
            >
              <Input />
            </Form.Item>
            <Form.Item name="license_number" label="License Number">
              <Input />
            </Form.Item>
            <Form.Item name="is_active" label="Active" valuePropName="checked">
              <Switch />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={isUpdating}>
                Save Changes
              </Button>
            </Form.Item>
          </Form>
        ) : (
          <Typography.Text type="secondary">
            No agency configured. Contact your administrator.
          </Typography.Text>
        )}
      </Card>
    </div>
  );
}
