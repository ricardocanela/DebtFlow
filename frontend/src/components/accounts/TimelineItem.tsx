import { Typography } from 'antd';
import {
  MessageOutlined,
  SwapOutlined,
  DollarOutlined,
  UserSwitchOutlined,
  ImportOutlined,
} from '@ant-design/icons';
import type { Activity, ActivityType } from '@/types/activity';
import { formatDateTime } from '@/utils/formatDate';

const { Text, Paragraph } = Typography;

const ACTIVITY_ICONS: Record<ActivityType, React.ReactNode> = {
  note: <MessageOutlined style={{ color: '#1677ff' }} />,
  status_change: <SwapOutlined style={{ color: '#722ed1' }} />,
  payment: <DollarOutlined style={{ color: '#52c41a' }} />,
  assignment: <UserSwitchOutlined style={{ color: '#fa8c16' }} />,
  import: <ImportOutlined style={{ color: '#13c2c2' }} />,
};

interface TimelineItemContentProps {
  activity: Activity;
}

export function TimelineItemContent({ activity }: TimelineItemContentProps) {
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Text strong style={{ fontSize: 13 }}>
          {activity.user_name}
        </Text>
        <Text type="secondary" style={{ fontSize: 12 }}>
          {formatDateTime(activity.created_at)}
        </Text>
      </div>
      <Paragraph
        style={{ marginBottom: 0, marginTop: 4, fontSize: 13 }}
        ellipsis={{ rows: 3, expandable: true }}
      >
        {activity.description}
      </Paragraph>
    </div>
  );
}

export function getTimelineIcon(type: ActivityType): React.ReactNode {
  return ACTIVITY_ICONS[type] || <MessageOutlined />;
}
