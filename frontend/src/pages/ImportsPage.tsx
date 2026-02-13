import { Typography } from 'antd';
import { useGetImportJobsQuery } from '@/api/importsApi';
import { ImportJobTable } from '@/components/imports/ImportJobTable';
import { TriggerImportButton } from '@/components/imports/TriggerImportButton';
import { ErrorFallback } from '@/components/common/ErrorFallback';

const { Title } = Typography;

export function ImportsPage() {
  const { data, isLoading, isError, refetch } = useGetImportJobsQuery({});

  if (isError) return <ErrorFallback onRetry={refetch} />;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>
          SFTP Imports
        </Title>
        <TriggerImportButton />
      </div>
      <ImportJobTable data={data?.results || []} loading={isLoading} />
    </div>
  );
}
