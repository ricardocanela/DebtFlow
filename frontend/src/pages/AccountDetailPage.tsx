import { useState, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Row, Col, Button, Typography, Space, Spin } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useGetAccountQuery } from '@/api/accountsApi';
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts';
import { DebtorCard } from '@/components/accounts/DebtorCard';
import { AccountSummaryCard } from '@/components/accounts/AccountSummaryCard';
import { AccountStatusFlow } from '@/components/accounts/AccountStatusFlow';
import { TimelinePanel } from '@/components/accounts/TimelinePanel';
import { AddNoteForm } from '@/components/accounts/AddNoteForm';
import { AccountQuickActions } from '@/components/accounts/AccountQuickActions';
import { TransitionModal } from '@/components/accounts/TransitionModal';
import { AssignCollectorModal } from '@/components/accounts/AssignCollectorModal';
import { RecordPaymentModal } from '@/components/payments/RecordPaymentModal';
import { PaymentSummary } from '@/components/payments/PaymentSummary';
import { StatusTag } from '@/components/common/StatusTag';
import { ErrorFallback } from '@/components/common/ErrorFallback';

const { Title, Text } = Typography;

export function AccountDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const noteRef = useRef<HTMLDivElement>(null);

  const { data: account, isLoading, isError, refetch } = useGetAccountQuery(id!);

  const [transitionOpen, setTransitionOpen] = useState(false);
  const [assignOpen, setAssignOpen] = useState(false);
  const [paymentOpen, setPaymentOpen] = useState(false);

  const handleTransitionFromFlow = useCallback(
    () => setTransitionOpen(true),
    [],
  );

  useKeyboardShortcuts({
    t: () => setTransitionOpen(true),
    a: () => setAssignOpen(true),
    p: () => setPaymentOpen(true),
    n: () => {
      noteRef.current?.querySelector('textarea')?.focus();
    },
    escape: () => {
      setTransitionOpen(false);
      setAssignOpen(false);
      setPaymentOpen(false);
    },
  });

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: 48 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (isError || !account) {
    return <ErrorFallback error={{ status: 404, message: 'Account not found' }} onRetry={refetch} />;
  }

  return (
    <div>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 16,
        }}
      >
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)} type="text" />
          <Title level={4} style={{ margin: 0 }}>
            Account <Text code>{account.external_ref}</Text>
          </Title>
          <StatusTag status={account.status} />
        </Space>
        <AccountQuickActions
          currentStatus={account.status}
          onTransition={() => setTransitionOpen(true)}
          onAssign={() => setAssignOpen(true)}
          onPayment={() => setPaymentOpen(true)}
        />
      </div>

      {/* Main Content */}
      <Row gutter={16}>
        {/* Left Column */}
        <Col xs={24} lg={8}>
          <Space direction="vertical" size={16} style={{ width: '100%' }}>
            <DebtorCard debtor={account.debtor} />
            <AccountStatusFlow
              currentStatus={account.status}
              onTransition={handleTransitionFromFlow}
            />
            <PaymentSummary accountId={account.id} />
          </Space>
        </Col>

        {/* Right Column */}
        <Col xs={24} lg={16}>
          <Space direction="vertical" size={16} style={{ width: '100%' }}>
            <AccountSummaryCard account={account} />
            <TimelinePanel
              accountId={account.id}
              recentActivities={account.recent_activities}
            />
            <div ref={noteRef}>
              <AddNoteForm accountId={account.id} />
            </div>
          </Space>
        </Col>
      </Row>

      {/* Modals */}
      <TransitionModal
        open={transitionOpen}
        onClose={() => setTransitionOpen(false)}
        accountId={account.id}
        currentStatus={account.status}
      />
      <AssignCollectorModal
        open={assignOpen}
        onClose={() => setAssignOpen(false)}
        accountId={account.id}
        currentCollectorId={account.assigned_to?.id}
      />
      <RecordPaymentModal
        open={paymentOpen}
        onClose={() => setPaymentOpen(false)}
        accountId={account.id}
      />
    </div>
  );
}
