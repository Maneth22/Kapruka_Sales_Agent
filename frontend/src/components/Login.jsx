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
    <Container size="xs" py="xl" style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', backgroundColor: '#f3eff9' }}>
      <Paper shadow="md" p="xl" radius="md" style={{ width: '100%', border: '1px solid #432a72' }}>
        <Stack align="center" mb="lg">
          <img src="/kapruka.jpg" alt="Kapruka" height={56} style={{ borderRadius: 8 }} />
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
              size="lg"
            />
            <PasswordInput
              label="Password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.currentTarget.value)}
              required
              size="lg"
            />
            {error && <Alert color="red" variant="light">{error}</Alert>}
            <Button type="submit" fullWidth loading={loading}
              style={{ backgroundColor: '#f2d40a', color: '#000', border: '2px solid #000' }}>
              {isRegister ? 'Register' : 'Sign In'}
            </Button>
          </Stack>
        </form>

        <Text ta="center" size="sm" mt="md">
          {isRegister ? 'Already have an account? ' : "Don't have an account? "}
          <Button variant="subtle" size="sm" onClick={() => setIsRegister(!isRegister)}>
            {isRegister ? 'Sign In' : 'Register'}
          </Button>
        </Text>
      </Paper>
    </Container>
  );
}
