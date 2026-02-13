import { Tag } from 'antd';

interface KeyboardHintProps {
  shortcut: string;
}

export function KeyboardHint({ shortcut }: KeyboardHintProps) {
  return (
    <Tag
      style={{
        fontSize: 11,
        padding: '0 4px',
        lineHeight: '18px',
        borderRadius: 4,
        color: '#8c8c8c',
        background: '#f5f5f5',
        border: '1px solid #d9d9d9',
      }}
    >
      {shortcut}
    </Tag>
  );
}
