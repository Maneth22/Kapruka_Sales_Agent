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
    <Paper shadow="md" p="sm" withBorder>
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
          color="green"
          variant="filled"
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
