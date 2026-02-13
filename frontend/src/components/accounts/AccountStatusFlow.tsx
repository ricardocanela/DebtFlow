import { Card, Steps, Tag } from 'antd';
import type { AccountStatus } from '@/types/account';
import { VALID_TRANSITIONS } from '@/utils/statusTransitions';
import { ACCOUNT_STATUS_LABELS } from '@/utils/constants';
import { ACCOUNT_STATUS_COLORS } from '@/utils/statusColors';

interface AccountStatusFlowProps {
  currentStatus: AccountStatus;
  onTransition?: (target: AccountStatus) => void;
}

const STATUS_ORDER: AccountStatus[] = [
  'new',
  'assigned',
  'in_contact',
  'negotiating',
  'payment_plan',
  'settled',
  'closed',
];

export function AccountStatusFlow({ currentStatus, onTransition }: AccountStatusFlowProps) {
  const validTargets = VALID_TRANSITIONS[currentStatus] || [];
  const currentIndex = STATUS_ORDER.indexOf(currentStatus);

  return (
    <Card title="Status Flow" size="small">
      <Steps
        current={currentIndex >= 0 ? currentIndex : 0}
        size="small"
        items={STATUS_ORDER.map((status) => ({
          title: ACCOUNT_STATUS_LABELS[status],
          status:
            status === currentStatus
              ? 'process'
              : STATUS_ORDER.indexOf(status) < currentIndex
                ? 'finish'
                : 'wait',
        }))}
        style={{ marginBottom: 16 }}
      />
      {validTargets.length > 0 && (
        <div>
          <span style={{ marginRight: 8, fontSize: 12, color: '#8c8c8c' }}>Available transitions:</span>
          {validTargets.map((target) => (
            <Tag
              key={target}
              color={ACCOUNT_STATUS_COLORS[target]}
              style={{ cursor: onTransition ? 'pointer' : 'default' }}
              onClick={() => onTransition?.(target)}
            >
              {ACCOUNT_STATUS_LABELS[target]}
            </Tag>
          ))}
        </div>
      )}
    </Card>
  );
}
