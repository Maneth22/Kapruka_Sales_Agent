import { useState } from 'react';
import { Paper, Group, Text, Badge, Collapse, ActionIcon } from '@mantine/core';
import { IconChevronDown, IconChevronRight } from '@tabler/icons-react';

const STATUS_COLORS = {
  info: 'blue',
  success: 'green',
  retry: 'orange',
  failure: 'red',
};

export default function AgentOutputCard({ label, content, status = 'info' }) {
  const [opened, setOpened] = useState(false);
  const color = STATUS_COLORS[status] || 'gray';

  return (
    <Paper
      shadow="xs"
      p="xs"
      radius="md"
      withBorder
      style={{
        borderLeft: `4px solid var(--mantine-color-${color}-5)`,
        marginBottom: '8px',
        maxWidth: '90%',
      }}
    >
      <Group
        gap="xs"
        justify="space-between"
        style={{ cursor: 'pointer' }}
        onClick={() => setOpened((o) => !o)}
      >
        <Group gap="xs">
          <ActionIcon size="sm" variant="subtle" color={color}>
            {opened ? <IconChevronDown size={14} /> : <IconChevronRight size={14} />}
          </ActionIcon>
          <Text size="sm" fw={600} c={color}>
            {label}
          </Text>
          <Badge size="sm" color={color} variant="light">
            {status}
          </Badge>
        </Group>
      </Group>

      <Collapse in={opened}>
        <Text
          size="xs"
          style={{
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
            backgroundColor: 'var(--mantine-color-gray-0)',
            padding: '8px',
            borderRadius: '4px',
            marginTop: '4px',
            maxHeight: '300px',
            overflow: 'auto',
          }}
        >
          {content}
        </Text>
      </Collapse>
    </Paper>
  );
}
