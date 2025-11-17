import { WS_BASE_URL } from '@/utils/constants';
import { GenerationProgress } from '@/types';

type WebSocketCallback = (data: GenerationProgress) => void;

export class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private callbacks: Map<string, Set<WebSocketCallback>> = new Map();
  private sessionId: string | null = null;

  /**
   * Connect to WebSocket for a generation session
   */
  connect(sessionId: string, accessToken: string): void {
    this.sessionId = sessionId;
    const wsUrl = `${WS_BASE_URL}/ws/generations/${sessionId}?token=${accessToken}`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.attemptReconnect();
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
    }
  }

  /**
   * Disconnect WebSocket
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.sessionId = null;
    this.callbacks.clear();
    this.reconnectAttempts = 0;
  }

  /**
   * Subscribe to WebSocket events
   */
  on(event: string, callback: WebSocketCallback): () => void {
    if (!this.callbacks.has(event)) {
      this.callbacks.set(event, new Set());
    }
    this.callbacks.get(event)!.add(callback);

    // Return unsubscribe function
    return () => {
      const eventCallbacks = this.callbacks.get(event);
      if (eventCallbacks) {
        eventCallbacks.delete(callback);
      }
    };
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(data: { event: string; data: GenerationProgress }): void {
    const { event, data: progressData } = data;
    const eventCallbacks = this.callbacks.get(event);

    if (eventCallbacks) {
      eventCallbacks.forEach((callback) => {
        try {
          callback(progressData);
        } catch (error) {
          console.error('Error in WebSocket callback:', error);
        }
      });
    }
  }

  /**
   * Attempt to reconnect
   */
  private attemptReconnect(): void {
    if (
      this.reconnectAttempts < this.maxReconnectAttempts &&
      this.sessionId
    ) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

      console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);

      setTimeout(() => {
        // Note: We need to get a fresh token before reconnecting
        // This will be handled by the component using this service
        window.dispatchEvent(new CustomEvent('websocket:reconnect-needed'));
      }, delay);
    }
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

// Export singleton instance
export const websocketService = new WebSocketService();
