import { Radio } from 'antd';
import type { TrendGranularity } from '@/types/analytics';

interface GranularitySelectorProps {
  value: TrendGranularity;
  onChange: (value: TrendGranularity) => void;
}

export function GranularitySelector({ value, onChange }: GranularitySelectorProps) {
  return (
    <Radio.Group
      value={value}
      onChange={(e) => onChange(e.target.value)}
      optionType="button"
      buttonStyle="solid"
      size="small"
    >
      <Radio.Button value="day">Day</Radio.Button>
      <Radio.Button value="week">Week</Radio.Button>
      <Radio.Button value="month">Month</Radio.Button>
    </Radio.Group>
  );
}
