import { Card, Descriptions, Typography, Progress } from 'antd';
import type { ImportJobDetail as ImportJobDetailType } from '@/types/importJob';
import { StatusTag } from '@/components/common/StatusTag';
import { formatDateTime } from '@/utils/formatDate';

const { Text } = Typography;

interface ImportJobDetailProps {
  job: ImportJobDetailType;
}

export function ImportJobDetailView({ job }: ImportJobDetailProps) {
  const pct = job.total_records > 0
    ? Math.round((job.processed_ok / job.total_records) * 100)
    : 0;

  return (
    <Card title={`Import: ${job.file_name}`}>
      <Descriptions column={{ xs: 1, sm: 2, lg: 3 }} size="small">
        <Descriptions.Item label="Status">
          <StatusTag status={job.status} type="import" />
        </Descriptions.Item>
        <Descriptions.Item label="Source">
          <Text>{job.source_host}</Text>
        </Descriptions.Item>
        <Descriptions.Item label="S3 Path">
          <Text code>{job.file_path_s3 || '—'}</Text>
        </Descriptions.Item>
        <Descriptions.Item label="Total Records">
          <Text>{job.total_records}</Text>
        </Descriptions.Item>
        <Descriptions.Item label="Processed OK">
          <Text type="success">{job.processed_ok}</Text>
        </Descriptions.Item>
        <Descriptions.Item label="Errors">
          <Text type={job.processed_errors > 0 ? 'danger' : undefined}>{job.processed_errors}</Text>
        </Descriptions.Item>
        <Descriptions.Item label="Progress" span={3}>
          <Progress percent={pct} style={{ width: 300 }} />
        </Descriptions.Item>
        <Descriptions.Item label="Started">
          {formatDateTime(job.started_at)}
        </Descriptions.Item>
        <Descriptions.Item label="Completed">
          {formatDateTime(job.completed_at)}
        </Descriptions.Item>
        <Descriptions.Item label="Created">
          {formatDateTime(job.created_at)}
        </Descriptions.Item>
      </Descriptions>
    </Card>
  );
}
