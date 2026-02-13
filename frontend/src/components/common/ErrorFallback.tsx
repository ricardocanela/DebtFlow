import { Result, Button } from 'antd';

interface ErrorFallbackProps {
  error?: { status?: number; message?: string };
  onRetry?: () => void;
}

export function ErrorFallback({ error, onRetry }: ErrorFallbackProps) {
  const status = error?.status;
  const message =
    error?.message || (status === 403 ? 'You do not have permission to view this.' : 'Something went wrong.');

  return (
    <Result
      status={status === 403 ? '403' : status === 404 ? '404' : 'error'}
      title={status || 'Error'}
      subTitle={message}
      extra={
        onRetry && (
          <Button type="primary" onClick={onRetry}>
            Try Again
          </Button>
        )
      }
    />
  );
}
