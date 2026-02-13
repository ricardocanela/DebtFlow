import { useParams, useNavigate } from 'react-router-dom';
import { Button, Spin, Space } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useGetImportJobQuery } from '@/api/importsApi';
import { ImportJobDetailView } from '@/components/imports/ImportJobDetail';
import { ImportErrorList } from '@/components/imports/ImportErrorList';
import { ErrorFallback } from '@/components/common/ErrorFallback';

export function ImportDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: job, isLoading, isError, refetch } = useGetImportJobQuery(id!);

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: 48 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (isError || !job) {
    return <ErrorFallback error={{ status: 404, message: 'Import job not found' }} onRetry={refetch} />;
  }

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/imports')} type="text" />
      </Space>
      <ImportJobDetailView job={job} />
      <ImportErrorList jobId={job.id} totalErrors={job.processed_errors} />
    </div>
  );
}
