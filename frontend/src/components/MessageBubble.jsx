import { Anchor, Paper, Text } from '@mantine/core';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

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
          backgroundColor: isUser ? '#432a72' : '#f3eff9',
          color: isUser ? '#fff' : 'var(--mantine-color-dark-9)',
        }}
      >
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            p: ({ children }) => <Text size="sm" component="p" my={2}>{children}</Text>,
            strong: ({ children }) => <Text component="strong" fw={700} inherit>{children}</Text>,
            em: ({ children }) => <Text component="em" fs="italic" inherit>{children}</Text>,
            code: ({ children }) => (
              <Text
                component="code"
                size="xs"
                inherit
                style={{
                  backgroundColor: isUser ? 'rgba(255,255,255,0.15)' : 'var(--mantine-color-gray-2)',
                  padding: '1px 4px',
                  borderRadius: 3,
                }}
              >
                {children}
              </Text>
            ),
            ul: ({ children }) => <ul style={{ margin: 0, paddingLeft: 20 }}>{children}</ul>,
            ol: ({ children }) => <ol style={{ margin: 0, paddingLeft: 20 }}>{children}</ol>,
            li: ({ children }) => <li style={{ marginBottom: 2 }}>{children}</li>,
            a: ({ href, children }) => (
              <Anchor href={href} target="_blank" rel="noopener noreferrer" c={isUser ? 'white' : 'blue'}>
                {children}
              </Anchor>
            ),
          }}
        >
          {displayContent}
        </ReactMarkdown>
      </Paper>
    </div>
  );
}
