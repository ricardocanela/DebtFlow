import { Modal } from 'antd';
import { ExclamationCircleOutlined } from '@ant-design/icons';

interface ConfirmModalProps {
  title: string;
  content: string;
  onConfirm: () => void;
  onCancel?: () => void;
  confirmLoading?: boolean;
  danger?: boolean;
}

export function showConfirmModal({
  title,
  content,
  onConfirm,
  onCancel,
  danger = false,
}: ConfirmModalProps) {
  Modal.confirm({
    title,
    icon: <ExclamationCircleOutlined />,
    content,
    okText: 'Confirm',
    okType: danger ? 'primary' : 'default',
    okButtonProps: danger ? { danger: true } : {},
    cancelText: 'Cancel',
    onOk: onConfirm,
    onCancel,
  });
}
