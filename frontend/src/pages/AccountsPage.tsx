import { useCallback } from 'react';
import { Card, Typography, Button, Space } from 'antd';
import { ExportOutlined } from '@ant-design/icons';
import { useGetAccountsQuery, useExportAccountsMutation } from '@/api/accountsApi';
import { useAccountFilters } from '@/hooks/useAccountFilters';
import { useDebounce } from '@/hooks/useDebounce';
import { AccountTable } from '@/components/accounts/AccountTable';
import { AccountFilters } from '@/components/accounts/AccountFilters';
import { ErrorFallback } from '@/components/common/ErrorFallback';
import { message } from 'antd';

const { Title } = Typography;

export function AccountsPage() {
  const { filters, setFilters, clearFilters } = useAccountFilters();
  const debouncedFilters = useDebounce(filters, 300);

  const { data, isLoading, isError, refetch } = useGetAccountsQuery(debouncedFilters);
  const [exportAccounts, { isLoading: isExporting }] = useExportAccountsMutation();

  const extractCursor = useCallback((url: string | null) => {
    if (!url) return undefined;
    try {
      const u = new URL(url, window.location.origin);
      return u.searchParams.get('cursor') || undefined;
    } catch {
      return undefined;
    }
  }, []);

  const handleExport = async () => {
    try {
      await exportAccounts(debouncedFilters).unwrap();
      message.success('Export started. You will be notified when ready.');
    } catch {
      message.error('Export failed.');
    }
  };

  if (isError) return <ErrorFallback onRetry={refetch} />;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>
          All Accounts
        </Title>
        <Space>
          <Button
            icon={<ExportOutlined />}
            onClick={handleExport}
            loading={isExporting}
          >
            Export CSV
          </Button>
        </Space>
      </div>
      <Card bodyStyle={{ padding: '12px 16px' }} style={{ marginBottom: 16 }}>
        <AccountFilters filters={filters} onFilterChange={setFilters} onClear={clearFilters} />
      </Card>
      <AccountTable
        data={data?.results || []}
        loading={isLoading}
        hasNext={!!data?.next}
        hasPrevious={!!data?.previous}
        onLoadNext={() => {
          const cursor = extractCursor(data?.next ?? null);
          if (cursor) setFilters({ cursor });
        }}
        onLoadPrevious={() => {
          const cursor = extractCursor(data?.previous ?? null);
          if (cursor) setFilters({ cursor });
        }}
      />
    </div>
  );
}
