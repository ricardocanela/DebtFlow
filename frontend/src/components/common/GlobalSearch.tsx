import { useState, useCallback, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Modal, Input, List, Typography, Tag } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { useGetAccountsQuery } from '@/api/accountsApi';
import { useDebounce } from '@/hooks/useDebounce';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { setGlobalSearchVisible } from '@/store/uiSlice';
import { formatCurrency } from '@/utils/formatCurrency';
import { StatusTag } from './StatusTag';

const { Text } = Typography;

export function GlobalSearch() {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounce(query, 300);
  const visible = useAppSelector((state) => state.ui.globalSearchVisible);
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);

  const { data, isFetching } = useGetAccountsQuery(
    { search: debouncedQuery },
    { skip: debouncedQuery.length < 2 },
  );

  useEffect(() => {
    if (visible) {
      setTimeout(() => inputRef.current?.focus(), 100);
    } else {
      setQuery('');
    }
  }, [visible]);

  const handleClose = useCallback(() => {
    dispatch(setGlobalSearchVisible(false));
  }, [dispatch]);

  const handleSelect = useCallback(
    (accountId: string) => {
      handleClose();
      navigate(`/accounts/${accountId}`);
    },
    [handleClose, navigate],
  );

  return (
    <Modal
      open={visible}
      onCancel={handleClose}
      footer={null}
      closable={false}
      width={600}
      styles={{ body: { padding: 0 } }}
      style={{ top: 80 }}
    >
      <div style={{ padding: '12px 16px', borderBottom: '1px solid #f0f0f0' }}>
        <Input
          ref={inputRef as never}
          prefix={<SearchOutlined />}
          placeholder="Search accounts by name, ref, email..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          size="large"
          variant="borderless"
          suffix={<Tag>ESC</Tag>}
        />
      </div>
      {debouncedQuery.length >= 2 && (
        <List
          loading={isFetching}
          dataSource={data?.results || []}
          locale={{ emptyText: isFetching ? 'Searching...' : 'No results found' }}
          style={{ maxHeight: 400, overflow: 'auto' }}
          renderItem={(item) => (
            <List.Item
              onClick={() => handleSelect(item.id)}
              style={{ cursor: 'pointer', padding: '8px 16px' }}
              className="search-result-item"
            >
              <List.Item.Meta
                title={
                  <span>
                    <Text strong>{item.debtor_name}</Text>
                    <Text type="secondary" style={{ marginLeft: 8, fontFamily: 'monospace' }}>
                      {item.external_ref}
                    </Text>
                  </span>
                }
                description={
                  <span>
                    <StatusTag status={item.status} />
                    <Text style={{ marginLeft: 8 }}>{formatCurrency(item.current_balance)}</Text>
                    {item.collector_name && (
                      <Text type="secondary" style={{ marginLeft: 8 }}>
                        {item.collector_name}
                      </Text>
                    )}
                  </span>
                }
              />
            </List.Item>
          )}
        />
      )}
    </Modal>
  );
}
