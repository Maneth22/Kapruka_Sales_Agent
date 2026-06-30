import { useState } from 'react';
import { TextInput, ActionIcon, Paper } from '@mantine/core';
import { IconSend } from '@tabler/icons-react';

export default function ChatInput({ onSend, disabled }) {
  const [value, setValue] = useState('');

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue('');
  };

  return (
      <Paper shadow="md" p="sm" withBorder style={{ backgroundColor: '#432a72', borderColor: '#432a72' }}>
      <form
        onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}
        style={{ display: 'flex', gap: '8px' }}
      >
        <TextInput
          placeholder="Type your message..."
          value={value}
          onChange={(e) => setValue(e.currentTarget.value)}
          disabled={disabled}
          style={{ flex: 1 }}
          size="md"
        />
        <ActionIcon
          size="lg"
          variant="filled"
          style={{ backgroundColor: '#f2d40a', color: '#000', border: '2px solid #000' }}
          onClick={handleSubmit}
          disabled={disabled || !value.trim()}
          type="submit"
        >
          <IconSend size={20} />
        </ActionIcon>
      </form>
    </Paper>
  );
}
