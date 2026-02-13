import { useState } from 'react';
import { Modal, Input, Typography, message } from 'antd';
import { useRefundPaymentMutation } from '@/api/paymentsApi';
import { formatCurrency } from '@/utils/formatCurrency';
import type { Payment } from '@/types/payment';

const { TextArea } = Input;
const { Text } = Typography;

interface RefundModalProps {
  open: boolean;
  onClose: () => void;
  payment: Payment | null;
}

export function RefundModal({ open, onClose, payment }: RefundModalProps) {
  const [reason, setReason] = useState('');
  const [refund, { isLoading }] = useRefundPaymentMutation();

  const handleSubmit = async () => {
    if (!payment) return;
    try {
      await refund({ id: payment.id, data: { reason: reason || undefined } }).unwrap();
      message.success('Payment refunded');
      setReason('');
      onClose();
    } catch {
      message.error('Refund failed');
    }
  };

  return (
    <Modal
      title="Refund Payment"
      open={open}
      onOk={handleSubmit}
      onCancel={onClose}
      confirmLoading={isLoading}
      okText="Confirm Refund"
      okButtonProps={{ danger: true }}
    >
      {payment && (
        <div style={{ marginBottom: 16 }}>
          <Text>
            Refunding <Text strong>{formatCurrency(payment.amount)}</Text> for payment{' '}
            <Text code>{payment.id.slice(0, 8)}</Text>
          </Text>
        </div>
      )}
      <div>
        <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>Reason (optional)</label>
        <TextArea
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Reason for refund..."
          rows={3}
        />
      </div>
    </Modal>
  );
}
