import { Table, Progress, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { useNavigate } from 'react-router-dom';
import type { ImportJob } from '@/types/importJob';
import { StatusTag } from '@/components/common/StatusTag';
import { formatDateTime } from '@/utils/formatDate';

const { Text } = Typography;

interface ImportJobTableProps {
  data: ImportJob[];
  loading?: boolean;
}

export function ImportJobTable({ data, loading }: ImportJobTableProps) {
  const navigate = useNavigate();

  const columns: ColumnsType<ImportJob> = [
    {
      title: 'File',
      dataIndex: 'file_name',
      key: 'file_name',
      render: (val: string, record) => (
        <Text
          style={{ cursor: 'pointer', color: '#1677ff' }}
          onClick={() => navigate(`/imports/${record.id}`)}
        >
          {val}
        </Text>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 110,
      render: (val: string) => <StatusTag status={val} type="import" />,
    },
    {
      title: 'Records',
      dataIndex: 'total_records',
      key: 'total_records',
      width: 80,
      align: 'right',
    },
    {
      title: 'OK',
      dataIndex: 'processed_ok',
      key: 'processed_ok',
      width: 60,
      align: 'right',
      render: (val: number) => <Text type="success">{val}</Text>,
    },
    {
      title: 'Errors',
      dataIndex: 'processed_errors',
      key: 'processed_errors',
      width: 70,
      align: 'right',
      render: (val: number) => (val > 0 ? <Text type="danger">{val}</Text> : <Text>{val}</Text>),
    },
    {
      title: 'Progress',
      key: 'progress',
      width: 150,
      render: (_: unknown, record: ImportJob) => {
        const pct = record.total_records > 0
          ? Math.round((record.processed_ok / record.total_records) * 100)
          : 0;
        return <Progress percent={pct} size="small" />;
      },
    },
    {
      title: 'Started',
      dataIndex: 'started_at',
      key: 'started_at',
      width: 160,
      render: (val: string | null) => (val ? formatDateTime(val) : '—'),
    },
    {
      title: 'Completed',
      dataIndex: 'completed_at',
      key: 'completed_at',
      width: 160,
      render: (val: string | null) => (val ? formatDateTime(val) : '—'),
    },
  ];

  return (
    <Table<ImportJob>
      dataSource={data}
      columns={columns}
      rowKey="id"
      loading={loading}
      pagination={false}
      size="small"
    />
  );
}
