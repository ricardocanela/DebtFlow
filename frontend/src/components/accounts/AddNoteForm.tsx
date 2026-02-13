import { useState } from 'react';
import { Input, Button, Space, message } from 'antd';
import { SendOutlined } from '@ant-design/icons';
import { useAddNoteMutation } from '@/api/accountsApi';
import { KeyboardHint } from '@/components/common/KeyboardHint';

const { TextArea } = Input;

interface AddNoteFormProps {
  accountId: string;
}

export function AddNoteForm({ accountId }: AddNoteFormProps) {
  const [text, setText] = useState('');
  const [addNote, { isLoading }] = useAddNoteMutation();

  const handleSubmit = async () => {
    if (!text.trim()) return;
    try {
      await addNote({ id: accountId, data: { text: text.trim() } }).unwrap();
      setText('');
      message.success('Note added');
    } catch {
      message.error('Failed to add note');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div style={{ borderTop: '1px solid #f0f0f0', padding: '12px 0 0' }}>
      <TextArea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Add a note... (Ctrl+Enter to submit)"
        autoSize={{ minRows: 2, maxRows: 4 }}
        style={{ marginBottom: 8 }}
      />
      <Space>
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={handleSubmit}
          loading={isLoading}
          disabled={!text.trim()}
          size="small"
        >
          Add Note
        </Button>
        <KeyboardHint shortcut="N" />
      </Space>
    </div>
  );
}
