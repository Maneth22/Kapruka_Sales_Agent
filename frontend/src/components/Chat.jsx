import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Container, AppShell, Group, Button, Text, Loader, ScrollArea, Stack, Center, SimpleGrid, Popover, ActionIcon } from '@mantine/core';
import { IconLogout, IconInfoCircle } from '@tabler/icons-react';
import { useChat } from '../hooks/useChat';
import MessageBubble from './MessageBubble';
import ProductCard from './ProductCard';
import ChatInput from './ChatInput';

export default function Chat() {
  const navigate = useNavigate();
  const token = localStorage.getItem('token');
  const { messages, agentOutputs, isThinking, statusDetail, connected, sendMessage } = useChat(token);
  const viewport = useRef(null);
  const [infoOpened, setInfoOpened] = useState(false);

  useEffect(() => {
    if (!token) navigate('/login');
  }, [token, navigate]);

  useEffect(() => {
    if (viewport.current) {
      viewport.current.scrollTo({ top: viewport.current.scrollHeight, behavior: 'smooth' });
    }
  }, [messages, agentOutputs, isThinking]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <AppShell header={{ height: 60 }} padding={0}>
      <AppShell.Header style={{ backgroundColor: '#432a72', borderBottom: 'none' }}>
        <Group h="100%" px="md" justify="space-between">
          <Group gap="xs">
            <img src="/kapruka.jpg" alt="Kapruka" height={32} style={{ borderRadius: 4 }} />
            <Text size="sm" fw={600} c="white">Sales Agent</Text>
          </Group>
          <Group>
            <Text size="xs" c={connected ? '#4ade80' : '#f87171'}>
              {connected ? '\u25cf Connected' : '\u25cb Disconnected'}
            </Text>
            <Popover opened={infoOpened} onChange={setInfoOpened} width={220} position="bottom-end" shadow="md">
              <Popover.Target>
                <ActionIcon variant="subtle" color="white" size="sm" onClick={() => setInfoOpened((o) => !o)}>
                  <IconInfoCircle size={18} />
                </ActionIcon>
              </Popover.Target>
              <Popover.Dropdown>
                <Text size="xs" fw={600}>Application No: 3V8UW</Text>
                <Text size="xs" c="dimmed" mt={4}>Developed by: Sanjula Subhawickrama</Text>
              </Popover.Dropdown>
            </Popover>
            <Button variant="subtle" color="white" onClick={handleLogout} leftSection={<IconLogout size={16} />}>
              Logout
            </Button>
          </Group>
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
              {messages.map((msg, i) => (
                <div key={i}>
                  <MessageBubble message={msg} />
                  {msg.role === 'assistant' && msg.products?.length > 0 && (
                    <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="sm" mt="sm" mb="md">
                      {msg.products.map((product) => (
                        <ProductCard key={product.id} {...product} />
                      ))}
                    </SimpleGrid>
                  )}
                </div>
              ))}
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
