import { Result, Button } from 'antd';
import { useNavigate } from 'react-router-dom';

export function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <Result
      status="404"
      title="404"
      subTitle="The page you're looking for doesn't exist."
      extra={
        <Button type="primary" onClick={() => navigate('/')}>
          Back to Home
        </Button>
      }
    />
  );
}
