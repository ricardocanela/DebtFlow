import { useState, useCallback } from 'react';
import { Typography } from 'antd';
import { useGetPaymentsQuery } from '@/api/paymentsApi';
import { PaymentTable } from '@/components/payments/PaymentTable';
import { RefundModal } from '@/components/payments/RefundModal';
import { ErrorFallback } from '@/components/common/ErrorFallback';
import type { Payment } from '@/types/payment';

const { Title } = Typography;

export function PaymentsPage() {
  const [cursor, setCursor] = useState<string | undefined>();
  const [refundTarget, setRefundTarget] = useState<Payment | null>(null);

  const { data, isLoading, isError, refetch } = useGetPaymentsQuery({ cursor });

  const extractCursor = useCallback((url: string | null) => {
    if (!url) return undefined;
    try {
      const u = new URL(url, window.location.origin);
      return u.searchParams.get('cursor') || undefined;
    } catch {
      return undefined;
    }
  }, []);

  if (isError) return <ErrorFallback onRetry={refetch} />;

  return (
    <div>
      <Title level={4} style={{ marginBottom: 16 }}>
        Payments
      </Title>
      <PaymentTable
        data={data?.results || []}
        loading={isLoading}
        hasNext={!!data?.next}
        hasPrevious={!!data?.previous}
        onLoadNext={() => setCursor(extractCursor(data?.next ?? null))}
        onLoadPrevious={() => setCursor(extractCursor(data?.previous ?? null))}
        onRefund={setRefundTarget}
      />
      <RefundModal
        open={!!refundTarget}
        onClose={() => setRefundTarget(null)}
        payment={refundTarget}
      />
    </div>
  );
}
