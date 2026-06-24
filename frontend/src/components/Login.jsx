import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Container, Paper, Title, TextInput, PasswordInput, Button, Text, Stack, Alert } from '@mantine/core';
import { login, register } from '../api/client';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [isRegister, setIsRegister] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const fn = isRegister ? register : login;
      const data = await fn(username, password);
      localStorage.setItem('token', data.access_token);
      navigate('/chat');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container size="xs" py="xl" style={{ minHeight: '100vh', display: 'flex', alignItems: 'center' }}>
      <Paper shadow="md" p="xl" radius="md" style={{ width: '100%' }}>
        <Stack align="center" mb="lg">
          <Title order={2}>{isRegister ? 'Create Account' : 'Sign In'}</Title>
          <Text c="dimmed" size="sm">Kapruka Sales Agent</Text>
        </Stack>

        <form onSubmit={handleSubmit}>
          <Stack>
            <TextInput
              label="Username"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.currentTarget.value)}
              required
            />
            <PasswordInput
              label="Password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.currentTarget.value)}
              required
            />
            {error && <Alert color="red" variant="light">{error}</Alert>}
            <Button type="submit" fullWidth loading={loading}>
              {isRegister ? 'Register' : 'Sign In'}
            </Button>
          </Stack>
        </form>

        <Text ta="center" size="sm" mt="md">
          {isRegister ? 'Already have an account? ' : "Don't have an account? "}
          <Button variant="subtle" size="compact-sm" onClick={() => setIsRegister(!isRegister)}>
            {isRegister ? 'Sign In' : 'Register'}
          </Button>
        </Text>
      </Paper>
    </Container>
  );
}
