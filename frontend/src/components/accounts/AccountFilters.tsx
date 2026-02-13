import { Space, Select, Input, Button, InputNumber } from 'antd';
import { ClearOutlined, SearchOutlined } from '@ant-design/icons';
import { useGetCollectorsQuery } from '@/api/collectorsApi';
import { useRole } from '@/hooks/useRole';
import { ACCOUNT_STATUS_LABELS, ALL_ACCOUNT_STATUSES } from '@/utils/constants';
import type { AccountFilterParams, AccountStatus } from '@/types/account';

interface AccountFiltersProps {
  filters: AccountFilterParams;
  onFilterChange: (filters: Partial<AccountFilterParams>) => void;
  onClear: () => void;
}

export function AccountFilters({ filters, onFilterChange, onClear }: AccountFiltersProps) {
  const { isAdmin } = useRole();
  const { data: collectors } = useGetCollectorsQuery(undefined, { skip: !isAdmin });

  return (
    <Space wrap size="small">
      <Input
        placeholder="Search name, ref, email..."
        prefix={<SearchOutlined />}
        value={filters.search || ''}
        onChange={(e) => onFilterChange({ search: e.target.value || undefined })}
        allowClear
        style={{ width: 220 }}
      />
      <Select
        placeholder="Status"
        value={filters.status}
        onChange={(val) => onFilterChange({ status: val as AccountStatus | undefined })}
        allowClear
        style={{ width: 140 }}
        options={ALL_ACCOUNT_STATUSES.map((s) => ({ value: s, label: ACCOUNT_STATUS_LABELS[s] }))}
      />
      {isAdmin && collectors && (
        <Select
          placeholder="Collector"
          value={filters.collector}
          onChange={(val) => onFilterChange({ collector: val })}
          allowClear
          style={{ width: 160 }}
          options={collectors.map((c) => ({ value: c.id, label: c.full_name || c.username }))}
        />
      )}
      <InputNumber
        placeholder="Min balance"
        value={filters.min_balance}
        onChange={(val) => onFilterChange({ min_balance: val ?? undefined })}
        prefix="$"
        style={{ width: 130 }}
      />
      <InputNumber
        placeholder="Max balance"
        value={filters.max_balance}
        onChange={(val) => onFilterChange({ max_balance: val ?? undefined })}
        prefix="$"
        style={{ width: 130 }}
      />
      <Button icon={<ClearOutlined />} onClick={onClear}>
        Clear
      </Button>
    </Space>
  );
}
