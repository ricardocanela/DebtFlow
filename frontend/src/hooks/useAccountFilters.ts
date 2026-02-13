import { useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import type { AccountFilterParams, AccountStatus } from '@/types/account';

export function useAccountFilters() {
  const [searchParams, setSearchParams] = useSearchParams();

  const filters: AccountFilterParams = useMemo(() => {
    const params: AccountFilterParams = {};
    const status = searchParams.get('status');
    if (status) params.status = status as AccountStatus;
    const collector = searchParams.get('collector');
    if (collector) params.collector = collector;
    const search = searchParams.get('search');
    if (search) params.search = search;
    const minBalance = searchParams.get('min_balance');
    if (minBalance) params.min_balance = Number(minBalance);
    const maxBalance = searchParams.get('max_balance');
    if (maxBalance) params.max_balance = Number(maxBalance);
    const ordering = searchParams.get('ordering');
    if (ordering) params.ordering = ordering;
    const cursor = searchParams.get('cursor');
    if (cursor) params.cursor = cursor;
    const priority = searchParams.get('priority');
    if (priority) params.priority = Number(priority);
    return params;
  }, [searchParams]);

  const setFilters = useCallback(
    (newFilters: Partial<AccountFilterParams>) => {
      const params = new URLSearchParams();
      const merged = { ...filters, ...newFilters };
      // Remove cursor when filters change (except explicit cursor set)
      if (!('cursor' in newFilters)) {
        delete merged.cursor;
      }
      Object.entries(merged).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.set(key, String(value));
        }
      });
      setSearchParams(params, { replace: true });
    },
    [filters, setSearchParams],
  );

  const clearFilters = useCallback(() => {
    setSearchParams({}, { replace: true });
  }, [setSearchParams]);

  return { filters, setFilters, clearFilters };
}
