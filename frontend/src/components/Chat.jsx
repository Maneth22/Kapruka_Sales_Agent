import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Container, AppShell, Group, Title, Button, Text, Loader, ScrollArea, Stack, Center, SimpleGrid } from '@mantine/core';
import { IconLogout } from '@tabler/icons-react';
import { useChat } from '../hooks/useChat';
import MessageBubble from './MessageBubble';
import AgentOutputCard from './AgentOutputCard';
import ProductCard from './ProductCard';
import ChatInput from './ChatInput';

export default function Chat() {
  const navigate = useNavigate();
  const token = localStorage.getItem('token');
  const { messages, agentOutputs, isThinking, statusDetail, connected, sendMessage, productCards } = useChat(token);
  const viewport = useRef(null);

  useEffect(() => {
    if (!token) navigate('/login');
  }, [token, navigate]);

  useEffect(() => {
    if (viewport.current) {
      viewport.current.scrollTo({ top: viewport.current.scrollHeight, behavior: 'smooth' });
    }
  }, [messages, agentOutputs, isThinking, productCards]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  const renderMessages = () => {
    let productIdx = 0;
    return messages.map((msg, i) => {
      const showProducts = msg.role === 'assistant' && productCards.length > productIdx;
      const batch = showProducts ? productCards[productIdx] : [];
      if (showProducts) productIdx++;
      return (
        <div key={i}>
          <MessageBubble message={msg} />
          {showProducts && (
            <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md" mt="sm" mb="md">
              {batch.map((product) => (
                <ProductCard key={product.id} {...product} />
              ))}
            </SimpleGrid>
          )}
        </div>
      );
    });
  };

  return (
    <AppShell header={{ height: 60 }} padding={0}>
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group>
            <Title order={4}>Kapruka Agent</Title>
            <Text size="xs" c={connected ? 'green' : 'red'}>
              {connected ? '\u25cf Connected' : '\u25cb Disconnected'}
            </Text>
          </Group>
          <Button variant="subtle" color="gray" onClick={handleLogout} leftSection={<IconLogout size={16} />}>
            Logout
          </Button>
        </Group>
      </AppShell.Header>

      <AppShell.Main>
        <Container size="md" style={{ height: 'calc(100vh - 60px)', display: 'flex', flexDirection: 'column' }}>
          <ScrollArea style={{ flex: 1 }} viewportRef={viewport} offsetScrollbars>
            <Stack p="md">
              {messages.length === 0 && !isThinking && (
                <Center py="xl">
                  <Text c="dimmed" ta="center">
                    Welcome! Ask me about products, check delivery, or place an order.
                  </Text>
                </Center>
              )}
              {renderMessages()}
              {agentOutputs.length > 0 && (
                <Stack gap={0} pl="sm" style={{ borderLeft: '2px solid var(--mantine-color-gray-3)' }}>
                  {agentOutputs.map((ao, i) => (
                    <AgentOutputCard key={i} label={ao.label} content={ao.content} status={ao.status} />
                  ))}
                </Stack>
              )}
              {isThinking && (
                <Group gap="xs" ml="sm">
                  <Loader size="xs" />
                  <Text size="sm" c="dimmed">{statusDetail || 'Thinking...'}</Text>
                </Group>
              )}
            </Stack>
          </ScrollArea>

          <div style={{ padding: '12px 16px' }}>
            <ChatInput onSend={sendMessage} disabled={!connected || isThinking} />
          </div>
        </Container>
      </AppShell.Main>
    </AppShell>
  );
}
