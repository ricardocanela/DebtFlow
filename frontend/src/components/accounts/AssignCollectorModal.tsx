import { useState } from 'react';
import { Modal, Select, message } from 'antd';
import { useAssignAccountMutation } from '@/api/accountsApi';
import { useGetCollectorsQuery } from '@/api/collectorsApi';

interface AssignCollectorModalProps {
  open: boolean;
  onClose: () => void;
  accountId: string;
  currentCollectorId?: string;
}

export function AssignCollectorModal({
  open,
  onClose,
  accountId,
  currentCollectorId,
}: AssignCollectorModalProps) {
  const [collectorId, setCollectorId] = useState<string | null>(currentCollectorId || null);
  const { data: collectors, isLoading: collectorsLoading } = useGetCollectorsQuery();
  const [assign, { isLoading }] = useAssignAccountMutation();

  const handleSubmit = async () => {
    if (!collectorId) return;
    try {
      await assign({ id: accountId, data: { collector_id: collectorId } }).unwrap();
      message.success('Account assigned');
      onClose();
    } catch {
      message.error('Assignment failed');
    }
  };

  return (
    <Modal
      title="Assign Collector"
      open={open}
      onOk={handleSubmit}
      onCancel={onClose}
      confirmLoading={isLoading}
      okButtonProps={{ disabled: !collectorId }}
      okText="Assign"
    >
      <Select
        placeholder="Select collector"
        value={collectorId}
        onChange={setCollectorId}
        style={{ width: '100%' }}
        loading={collectorsLoading}
        showSearch
        optionFilterProp="label"
        options={(collectors || [])
          .filter((c) => c.is_active)
          .map((c) => ({
            value: c.id,
            label: `${c.full_name || c.username} (${c.max_accounts} max)`,
          }))}
      />
    </Modal>
  );
}
