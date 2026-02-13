import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Typography } from 'antd';
import { useGetAccountsQuery } from '@/api/accountsApi';
import { useAccountFilters } from '@/hooks/useAccountFilters';
import { useDebounce } from '@/hooks/useDebounce';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { setSelectedAccount, setSelectedRowIndex } from '@/store/worklistSlice';
import { AccountTable } from '@/components/accounts/AccountTable';
import { AccountFilters } from '@/components/accounts/AccountFilters';
import { ErrorFallback } from '@/components/common/ErrorFallback';

const { Title } = Typography;

export function WorklistPage() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { filters, setFilters, clearFilters } = useAccountFilters();
  const debouncedFilters = useDebounce(filters, 300);
  const { selectedAccountId, selectedRowIndex } = useAppSelector((s) => s.worklist);

  const { data, isLoading, isError, refetch } = useGetAccountsQuery(debouncedFilters);

  const results = data?.results || [];

  const extractCursor = useCallback((url: string | null) => {
    if (!url) return undefined;
    try {
      const u = new URL(url, window.location.origin);
      return u.searchParams.get('cursor') || undefined;
    } catch {
      return undefined;
    }
  }, []);

  const handleLoadNext = useCallback(() => {
    const cursor = extractCursor(data?.next ?? null);
    if (cursor) setFilters({ cursor });
  }, [data?.next, extractCursor, setFilters]);

  const handleLoadPrevious = useCallback(() => {
    const cursor = extractCursor(data?.previous ?? null);
    if (cursor) setFilters({ cursor });
  }, [data?.previous, extractCursor, setFilters]);

  useKeyboardShortcuts({
    j: () => {
      const next = Math.min(selectedRowIndex + 1, results.length - 1);
      dispatch(setSelectedRowIndex(next));
      if (results[next]) dispatch(setSelectedAccount(results[next].id));
    },
    k: () => {
      const prev = Math.max(selectedRowIndex - 1, 0);
      dispatch(setSelectedRowIndex(prev));
      if (results[prev]) dispatch(setSelectedAccount(results[prev].id));
    },
    enter: () => {
      if (selectedAccountId) navigate(`/accounts/${selectedAccountId}`);
    },
    r: () => refetch(),
  });

  if (isError) return <ErrorFallback onRetry={refetch} />;

  return (
    <div>
      <Title level={4} style={{ marginBottom: 16 }}>
        My Queue
      </Title>
      <Card bodyStyle={{ padding: '12px 16px' }} style={{ marginBottom: 16 }}>
        <AccountFilters filters={filters} onFilterChange={setFilters} onClear={clearFilters} />
      </Card>
      <AccountTable
        data={results}
        loading={isLoading}
        hasNext={!!data?.next}
        hasPrevious={!!data?.previous}
        onLoadNext={handleLoadNext}
        onLoadPrevious={handleLoadPrevious}
        selectedRowKey={selectedAccountId}
        onRowSelect={(id) => {
          dispatch(setSelectedAccount(id));
          const idx = results.findIndex((r) => r.id === id);
          dispatch(setSelectedRowIndex(idx));
        }}
      />
    </div>
  );
}
