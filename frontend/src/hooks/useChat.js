import { useState, useEffect, useCallback, useRef } from 'react';
import { io } from 'socket.io-client';

const HEARTBEAT_INTERVAL = 30000;

export function useChat(token) {
  const [messages, setMessages] = useState([]);
  const [agentOutputs, setAgentOutputs] = useState([]);
  const [isThinking, setIsThinking] = useState(false);
  const [statusDetail, setStatusDetail] = useState('');
  const [connected, setConnected] = useState(false);
  const [sessionTimedOut, setSessionTimedOut] = useState(false);
  const socketRef = useRef(null);
  const heartbeatRef = useRef(null);
  const activityRef = useRef(null);

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

    socket.on('agent_output', (data) => {
      setAgentOutputs((prev) => [...prev, data]);
    });

    socket.on('session_timeout', () => {
      setSessionTimedOut(true);
      localStorage.removeItem('token');
      socket.disconnect();
    });

    socket.on('history_cleared', () => {
      setMessages([]);
      setAgentOutputs([]);
    });

    socketRef.current = socket;

    const sendHeartbeat = () => {
      if (socket.connected) {
        socket.emit('heartbeat');
      }
    };

    const handleActivity = () => {
      if (!activityRef.current) {
        activityRef.current = true;
        sendHeartbeat();
        setTimeout(() => { activityRef.current = false; }, HEARTBEAT_INTERVAL);
      }
    };

    heartbeatRef.current = setInterval(sendHeartbeat, HEARTBEAT_INTERVAL);

    window.addEventListener('mousemove', handleActivity);
    window.addEventListener('keydown', handleActivity);
    window.addEventListener('click', handleActivity);

    return () => {
      socket.disconnect();
      clearInterval(heartbeatRef.current);
      window.removeEventListener('mousemove', handleActivity);
      window.removeEventListener('keydown', handleActivity);
      window.removeEventListener('click', handleActivity);
    };
  }, [token]);

  const sendMessage = useCallback((content) => {
    const socket = socketRef.current;
    if (!socket || !socket.connected) return;
    setMessages((prev) => [...prev, { role: 'user', content }]);
    setAgentOutputs([]);
    socket.emit('message', { content });
  }, []);

  const clearHistory = useCallback(() => {
    const socket = socketRef.current;
    if (!socket || !socket.connected) return;
    socket.emit('clear_history');
  }, []);

  return { messages, agentOutputs, isThinking, statusDetail, connected, sessionTimedOut, sendMessage, clearHistory };
}
