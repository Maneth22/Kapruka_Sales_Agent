import { useState } from 'react';
import { Card, Image, Text, Badge, Group, Modal, Anchor, Stack } from '@mantine/core';

export default function ProductCard({ name, price, currency, in_stock, image_url, product_url, description, category, rating }) {
  const [opened, setOpened] = useState(false);
  const [imgError, setImgError] = useState(false);

  return (
    <>
      <Card
        shadow="sm"
        radius="md"
        withBorder
        padding="sm"
        className="product-card"
        style={{ height: '100%' }}
      >
        <Card.Section
          style={{ cursor: 'pointer', overflow: 'hidden' }}
          onClick={() => setOpened(true)}
        >
          <Image
            src={imgError ? null : image_url}
            height={120}
            fallbackSrc="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 width=%27400%27 height=%27300%27 fill=%27%23dee2e6%27%3E%3Crect width=%27400%27 height=%27300%27/%3E%3Ctext x=%27200%27 y=%27150%27 text-anchor=%27middle%27 fill=%27%23868e96%27 font-size=%2716%27 font-family=%27sans-serif%27%3ENo Image%3C/text%3E%3C/svg%3E"
            onError={() => setImgError(true)}
            style={{ objectFit: 'cover' }}
            alt={name}
          />
        </Card.Section>

        <Stack gap={4} mt="xs">
          <Group justify="space-between" wrap="wrap" gap={4}>
            <Text fw={600} size="xs" lineClamp={2} style={{ flex: 1 }}>
              {name}
            </Text>
            <Badge
              size="xs"
              color={in_stock ? 'deepPurple' : 'red'}
              variant="light"
              style={{ flexShrink: 0 }}
            >
              {in_stock ? 'In Stock' : 'Out of Stock'}
            </Badge>
          </Group>

          {category && (
            <Badge size="xs" color="yellow" variant="filled" style={{ alignSelf: 'flex-start' }}>
              {category}
            </Badge>
          )}

          <Text size="sm" fw={700} style={{ color: '#432a72' }}>
            {price != null ? `${price} ${currency || 'LKR'}` : ''}
          </Text>

          {rating != null && (
            <Text size="xs" c="dimmed">
              {'★'.repeat(Math.round(rating))}{'☆'.repeat(5 - Math.round(rating))} {rating}
            </Text>
          )}

          {description && (
            <Text size="xs" c="dimmed" lineClamp={1}>
              {description}
            </Text>
          )}

          {product_url && (
            <Anchor
              href={product_url}
              target="_blank"
              rel="noopener noreferrer"
              size="xs"
              style={{ color: '#432a72', display: 'inline-flex', alignItems: 'center', minHeight: 44 }}
            >
              View Product &rarr;
            </Anchor>
          )}
        </Stack>
      </Card>

      <style>{`
        .product-card {
          transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .product-card:hover {
          transform: scale(1.03);
          box-shadow: 0 8px 24px rgba(67, 42, 114, 0.15);
        }
        @media (max-width: 576px) {
          .product-card:hover {
            transform: none;
          }
        }
      `}</style>

      <Modal
        opened={opened}
        onClose={() => setOpened(false)}
        title={name}
        size="lg"
        centered
        fullScreen={{ base: true, sm: false }}
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
