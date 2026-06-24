import { useState, useEffect, useCallback, useRef } from 'react';
import { io } from 'socket.io-client';

export function useChat(token) {
  const [messages, setMessages] = useState([]);
  const [isThinking, setIsThinking] = useState(false);
  const [statusDetail, setStatusDetail] = useState('');
  const [connected, setConnected] = useState(false);
  const socketRef = useRef(null);

  useEffect(() => {
    if (!token) return;
    const socket = io('/', {
      query: { token },
      transports: ['websocket', 'polling'],
    });

    socket.on('connect', () => setConnected(true));
    socket.on('disconnect', () => setConnected(false));
    socket.on('connect_error', () => setConnected(false));

    socket.on('message', (data) => {
      setMessages((prev) => [...prev, data]);
      setIsThinking(false);
      setStatusDetail('');
    });

    socket.on('status', (data) => {
      const s = data?.status;
      const detail = data?.detail || '';
      if (s === 'thinking' || s === 'interacting' || s === 'building_request' || s === 'searching' || s === 'validating' || s === 'retrying') {
        setIsThinking(true);
        setStatusDetail(detail);
      } else if (s === 'done') {
        setIsThinking(true);
        setStatusDetail(detail);
      } else {
        setIsThinking(false);
        setStatusDetail('');
      }
    });

    socketRef.current = socket;

    return () => { socket.disconnect(); };
  }, [token]);

  const sendMessage = useCallback((content) => {
    const socket = socketRef.current;
    if (!socket || !socket.connected) return;
    setMessages((prev) => [...prev, { role: 'user', content }]);
    socket.emit('message', { content });
  }, []);

  return { messages, isThinking, statusDetail, connected, sendMessage };
}
