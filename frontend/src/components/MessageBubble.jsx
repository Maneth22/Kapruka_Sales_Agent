import { Container, Paper, Text } from '@mantine/core';

function stripJsonBlocks(text) {
  return text.replace(/```json[\s\S]*?```/g, '').trim();
}

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  const displayContent = stripJsonBlocks(message.content);

  return (
    <div style={{
      display: 'flex',
      justifyContent: isUser ? 'flex-end' : 'flex-start',
      marginBottom: '12px',
    }}>
      <Paper
        shadow="sm"
        p="sm"
        radius="lg"
        style={{
          maxWidth: '80%',
          backgroundColor: isUser ? 'var(--mantine-color-green-6)' : 'var(--mantine-color-gray-1)',
          color: isUser ? '#fff' : 'var(--mantine-color-dark-9)',
        }}
      >
        <Text size="sm" style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
          {displayContent}
        </Text>
      </Paper>
    </div>
  );
}
