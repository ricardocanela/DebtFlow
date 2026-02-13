import { Table, Card, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { useGetImportErrorsQuery } from '@/api/importsApi';
import type { ImportError } from '@/types/importJob';
import { useState } from 'react';

const { Text } = Typography;

interface ImportErrorListProps {
  jobId: string;
  totalErrors: number;
}

export function ImportErrorList({ jobId, totalErrors }: ImportErrorListProps) {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useGetImportErrorsQuery({ id: jobId, page });

  const columns: ColumnsType<ImportError> = [
    {
      title: 'Line',
      dataIndex: 'line',
      key: 'line',
      width: 80,
      render: (val: number) => <Text code>{val}</Text>,
    },
    {
      title: 'Error',
      dataIndex: 'error',
      key: 'error',
      render: (val: string) => <Text type="danger">{val}</Text>,
    },
    {
      title: 'Data',
      dataIndex: 'data',
      key: 'data',
      width: 300,
      render: (val: Record<string, unknown> | undefined) =>
        val ? (
          <Text code style={{ fontSize: 11 }}>
            {JSON.stringify(val).slice(0, 100)}
          </Text>
        ) : (
          '—'
        ),
    },
  ];

  if (totalErrors === 0) return null;

  return (
    <Card title={`Import Errors (${totalErrors})`} style={{ marginTop: 16 }}>
      <Table<ImportError>
        dataSource={data?.results || []}
        columns={columns}
        rowKey={(record) => `${record.line}-${record.error}`}
        loading={isLoading}
        size="small"
        pagination={{
          current: page,
          total: totalErrors,
          pageSize: 50,
          onChange: setPage,
          showSizeChanger: false,
        }}
      />
    </Card>
  );
}
