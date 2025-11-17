import { useEffect, useRef } from 'react';
import { websocketService } from '@/services';
import { GenerationProgress } from '@/types';
import { WEBSOCKET_EVENTS } from '@/utils/constants';
import { useAuth } from './useAuth';

interface UseWebSocketOptions {
  sessionId: string;
  onStarted?: (data: GenerationProgress) => void;
  onProgress?: (data: GenerationProgress) => void;
  onCompleted?: (data: GenerationProgress) => void;
  onFailed?: (data: GenerationProgress) => void;
}

export const useWebSocket = (options: UseWebSocketOptions) => {
  const { sessionId, onStarted, onProgress, onCompleted, onFailed } = options;
  const { getAccessToken } = useAuth();
  const isConnectedRef = useRef(false);

  useEffect(() => {
    const connect = async () => {
      if (isConnectedRef.current) return;

      const token = await getAccessToken();
      if (!token) {
        console.error('No access token available for WebSocket connection');
        return;
      }

      websocketService.connect(sessionId, token);
      isConnectedRef.current = true;

      // Set up event listeners
      const unsubscribers: (() => void)[] = [];

      if (onStarted) {
        const unsub = websocketService.on(WEBSOCKET_EVENTS.GENERATION_STARTED, onStarted);
        unsubscribers.push(unsub);
      }

      if (onProgress) {
        const unsub = websocketService.on(WEBSOCKET_EVENTS.GENERATION_PROGRESS, onProgress);
        unsubscribers.push(unsub);
      }

      if (onCompleted) {
        const unsub = websocketService.on(WEBSOCKET_EVENTS.GENERATION_COMPLETED, onCompleted);
        unsubscribers.push(unsub);
      }

      if (onFailed) {
        const unsub = websocketService.on(WEBSOCKET_EVENTS.GENERATION_FAILED, onFailed);
        unsubscribers.push(unsub);
      }

      // Handle reconnection requests
      const handleReconnect = () => {
        connect();
      };
      window.addEventListener('websocket:reconnect-needed', handleReconnect);

      // Cleanup
      return () => {
        unsubscribers.forEach((unsub) => unsub());
        window.removeEventListener('websocket:reconnect-needed', handleReconnect);
        websocketService.disconnect();
        isConnectedRef.current = false;
      };
    };

    connect();
  }, [sessionId, onStarted, onProgress, onCompleted, onFailed, getAccessToken]);

  return {
    isConnected: websocketService.isConnected(),
  };
};
