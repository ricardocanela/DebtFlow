import { Badge, Tooltip } from 'antd';

interface PriorityBadgeProps {
  priority: number;
}

function getPriorityColor(priority: number): string {
  if (priority >= 8) return '#f5222d';
  if (priority >= 5) return '#fa8c16';
  if (priority >= 3) return '#fadb14';
  return '#52c41a';
}

export function PriorityBadge({ priority }: PriorityBadgeProps) {
  return (
    <Tooltip title={`Priority: ${priority}`}>
      <Badge color={getPriorityColor(priority)} text={priority} />
    </Tooltip>
  );
}
