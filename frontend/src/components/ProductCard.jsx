import { useState } from 'react';
import { Card, Image, Text, Badge, Group, Modal, Anchor, Stack } from '@mantine/core';

export default function ProductCard({ name, price, currency, in_stock, image_url, product_url, description, category, rating }) {
  const [opened, setOpened] = useState(false);
  const [imgError, setImgError] = useState(false);

  return (
    <>
      <Card shadow="sm" radius="md" withBorder padding="md" style={{ height: '100%' }}>
        <Card.Section
          style={{ cursor: 'pointer', overflow: 'hidden' }}
          onClick={() => setOpened(true)}
        >
          <Image
            src={imgError ? null : image_url}
            height={160}
            fallbackSrc="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 width=%27400%27 height=%27300%27 fill=%27%23dee2e6%27%3E%3Crect width=%27400%27 height=%27300%27/%3E%3Ctext x=%27200%27 y=%27150%27 text-anchor=%27middle%27 fill=%27%23868e96%27 font-size=%2716%27 font-family=%27sans-serif%27%3ENo Image%3C/text%3E%3C/svg%3E"
            onError={() => setImgError(true)}
            style={{ objectFit: 'cover' }}
            alt={name}
          />
        </Card.Section>

        <Stack gap="xs" mt="sm">
          <Group justify="space-between" wrap="nowrap" gap="xs">
            <Text fw={600} size="sm" lineClamp={2} style={{ flex: 1 }}>
              {name}
            </Text>
            <Badge
              size="sm"
              color={in_stock ? 'green' : 'red'}
              variant="light"
              style={{ flexShrink: 0 }}
            >
              {in_stock ? 'In Stock' : 'Out of Stock'}
            </Badge>
          </Group>

          {category && (
            <Badge size="xs" color="blue" variant="outline" style={{ alignSelf: 'flex-start' }}>
              {category}
            </Badge>
          )}

          <Text size="lg" fw={700} c="green">
            {price != null ? `${price} ${currency || 'LKR'}` : ''}
          </Text>

          {rating != null && (
            <Text size="xs" c="dimmed">
              {'★'.repeat(Math.round(rating))}{'☆'.repeat(5 - Math.round(rating))} {rating}
            </Text>
          )}

          {description && (
            <Text size="xs" c="dimmed" lineClamp={2}>
              {description}
            </Text>
          )}

          {product_url && (
            <Anchor
              href={product_url}
              target="_blank"
              rel="noopener noreferrer"
              size="sm"
              style={{ display: 'inline-block' }}
            >
              View Product &rarr;
            </Anchor>
          )}
        </Stack>
      </Card>

      <Modal
        opened={opened}
        onClose={() => setOpened(false)}
        title={name}
        size="lg"
        centered
      >
        <Image
          src={imgError ? null : image_url}
          fallbackSrc="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 width=%27400%27 height=%27300%27 fill=%27%23dee2e6%27%3E%3Crect width=%27400%27 height=%27300%27/%3E%3Ctext x=%27200%27 y=%27150%27 text-anchor=%27middle%27 fill=%27%23868e96%27 font-size=%2716%27 font-family=%27sans-serif%27%3ENo Image%3C/text%3E%3C/svg%3E"
          onError={() => setImgError(true)}
          style={{ width: '100%' }}
          alt={name}
        />
      </Modal>
    </>
  );
}
