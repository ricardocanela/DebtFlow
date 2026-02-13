import { useState } from 'react';
import { Modal, Select, Input, Space, message } from 'antd';
import { useTransitionAccountMutation } from '@/api/accountsApi';
import { VALID_TRANSITIONS } from '@/utils/statusTransitions';
import { ACCOUNT_STATUS_LABELS } from '@/utils/constants';
import type { AccountStatus } from '@/types/account';

const { TextArea } = Input;

interface TransitionModalProps {
  open: boolean;
  onClose: () => void;
  accountId: string;
  currentStatus: AccountStatus;
}

export function TransitionModal({ open, onClose, accountId, currentStatus }: TransitionModalProps) {
  const [targetStatus, setTargetStatus] = useState<AccountStatus | null>(null);
  const [note, setNote] = useState('');
  const [transition, { isLoading }] = useTransitionAccountMutation();

  const validTargets = VALID_TRANSITIONS[currentStatus] || [];

  const handleSubmit = async () => {
    if (!targetStatus) return;
    try {
      await transition({
        id: accountId,
        data: { new_status: targetStatus, note: note || undefined },
      }).unwrap();
      message.success(`Status changed to ${ACCOUNT_STATUS_LABELS[targetStatus]}`);
      setTargetStatus(null);
      setNote('');
      onClose();
    } catch {
      message.error('Transition failed');
    }
  };

  return (
    <Modal
      title="Change Account Status"
      open={open}
      onOk={handleSubmit}
      onCancel={onClose}
      confirmLoading={isLoading}
      okButtonProps={{ disabled: !targetStatus }}
      okText="Confirm Transition"
    >
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <div>
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>
            Current: {ACCOUNT_STATUS_LABELS[currentStatus]}
          </label>
          <Select
            placeholder="Select new status"
            value={targetStatus}
            onChange={setTargetStatus}
            style={{ width: '100%' }}
            options={validTargets.map((s) => ({
              value: s,
              label: ACCOUNT_STATUS_LABELS[s],
            }))}
          />
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>Note (optional)</label>
          <TextArea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Reason for status change..."
            rows={3}
          />
        </div>
      </Space>
    </Modal>
  );
}
