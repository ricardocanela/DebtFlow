import { Timeline, Card, Button, Spin } from 'antd';
import { useGetTimelineQuery } from '@/api/accountsApi';
import { TimelineItemContent, getTimelineIcon } from './TimelineItem';
import { EmptyState } from '@/components/common/EmptyState';
import type { Activity } from '@/types/activity';

interface TimelinePanelProps {
  accountId: string;
  recentActivities?: Activity[];
}

export function TimelinePanel({ accountId, recentActivities }: TimelinePanelProps) {
  const { data, isLoading, isFetching } = useGetTimelineQuery({ id: accountId });

  const activities = data?.results || recentActivities || [];

  if (isLoading) {
    return (
      <Card title="Activity Timeline" size="small">
        <div style={{ textAlign: 'center', padding: 24 }}>
          <Spin />
        </div>
      </Card>
    );
  }

  return (
    <Card
      title="Activity Timeline"
      size="small"
      style={{ maxHeight: 500, overflow: 'auto' }}
    >
      {activities.length === 0 ? (
        <EmptyState description="No activity yet" />
      ) : (
        <>
          <Timeline
            items={activities.map((activity) => ({
              key: activity.id,
              dot: getTimelineIcon(activity.activity_type),
              children: <TimelineItemContent activity={activity} />,
            }))}
          />
          {data?.next && (
            <div style={{ textAlign: 'center' }}>
              <Button size="small" loading={isFetching}>
                Load More
              </Button>
            </div>
          )}
        </>
      )}
    </Card>
  );
}
