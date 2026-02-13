import { Skeleton, Card } from 'antd';

interface LoadingSkeletonProps {
  rows?: number;
  cards?: number;
}

export function LoadingSkeleton({ rows = 5, cards }: LoadingSkeletonProps) {
  if (cards) {
    return (
      <div style={{ display: 'flex', gap: 16 }}>
        {Array.from({ length: cards }).map((_, i) => (
          <Card key={i} style={{ flex: 1 }}>
            <Skeleton active paragraph={{ rows: 2 }} />
          </Card>
        ))}
      </div>
    );
  }

  return <Skeleton active paragraph={{ rows }} />;
}
