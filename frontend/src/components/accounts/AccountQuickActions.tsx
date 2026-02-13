import { Space, Button } from 'antd';
import {
  SwapOutlined,
  UserSwitchOutlined,
  DollarOutlined,
} from '@ant-design/icons';
import { useRole } from '@/hooks/useRole';
import { KeyboardHint } from '@/components/common/KeyboardHint';
import { VALID_TRANSITIONS } from '@/utils/statusTransitions';
import type { AccountStatus } from '@/types/account';

interface AccountQuickActionsProps {
  currentStatus: AccountStatus;
  onTransition: () => void;
  onAssign: () => void;
  onPayment: () => void;
}

export function AccountQuickActions({
  currentStatus,
  onTransition,
  onAssign,
  onPayment,
}: AccountQuickActionsProps) {
  const { isAdmin } = useRole();
  const hasTransitions = (VALID_TRANSITIONS[currentStatus] || []).length > 0;

  return (
    <Space>
      {hasTransitions && (
        <Button icon={<SwapOutlined />} onClick={onTransition}>
          Transition <KeyboardHint shortcut="T" />
        </Button>
      )}
      {isAdmin && (
        <Button icon={<UserSwitchOutlined />} onClick={onAssign}>
          Assign <KeyboardHint shortcut="A" />
        </Button>
      )}
      <Button icon={<DollarOutlined />} onClick={onPayment} type="primary">
        Payment <KeyboardHint shortcut="P" />
      </Button>
    </Space>
  );
}
