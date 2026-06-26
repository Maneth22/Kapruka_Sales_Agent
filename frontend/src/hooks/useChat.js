import { useState, useEffect, useCallback, useRef } from 'react';
import { io } from 'socket.io-client';

export function useChat(token) {
  const [messages, setMessages] = useState([]);
  const [agentOutputs, setAgentOutputs] = useState([]);
  const [isThinking, setIsThinking] = useState(false);
  const [statusDetail, setStatusDetail] = useState('');
  const [connected, setConnected] = useState(false);
  const [productCards, setProductCards] = useState([]);
  const socketRef = useRef(null);
  const msgIndexRef = useRef(-1);

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
      msgIndexRef.current = data._index != null ? data._index : prev.length;
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

    socket.on('agent_output', (data) => {
      setAgentOutputs((prev) => [...prev, data]);
    });

    socket.on('products', (data) => {
      if (data?.products && data.products.length > 0) {
        setProductCards((prev) => [...prev, data.products]);
      }
    });

    socketRef.current = socket;

    return () => { socket.disconnect(); };
  }, [token]);

  const sendMessage = useCallback((content) => {
    const socket = socketRef.current;
    if (!socket || !socket.connected) return;
    setMessages((prev) => [...prev, { role: 'user', content }]);
    setAgentOutputs([]);
    setProductCards([]);
    socket.emit('message', { content });
  }, []);

  return { messages, agentOutputs, isThinking, statusDetail, connected, sendMessage, productCards };
}
