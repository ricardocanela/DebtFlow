import { Button, message } from 'antd';
import { CloudSyncOutlined } from '@ant-design/icons';
import { useTriggerImportMutation } from '@/api/importsApi';
import { showConfirmModal } from '@/components/common/ConfirmModal';

export function TriggerImportButton() {
  const [trigger, { isLoading }] = useTriggerImportMutation();

  const handleClick = () => {
    showConfirmModal({
      title: 'Trigger SFTP Import',
      content: 'This will poll all configured SFTP servers for new files. Continue?',
      onConfirm: async () => {
        try {
          await trigger().unwrap();
          message.success('Import triggered. Check back shortly for results.');
        } catch {
          message.error('Failed to trigger import');
        }
      },
    });
  };

  return (
    <Button
      type="primary"
      icon={<CloudSyncOutlined />}
      onClick={handleClick}
      loading={isLoading}
    >
      Trigger Import
    </Button>
  );
}
