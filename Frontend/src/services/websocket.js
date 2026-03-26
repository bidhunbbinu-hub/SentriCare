let socket = null;
let reconnectTimer = null;

export function connectWebSocket(onMessage) {
  
  if (socket && socket.readyState === WebSocket.OPEN) {
    return;
  }

  socket = new WebSocket("ws://localhost:8000/ws/alerts");

  socket.onopen = () => {
    console.log("WebSocket connected");
    
    if (reconnectTimer) clearTimeout(reconnectTimer);
  };

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (error) {
      console.error("Failed to parse WebSocket message:", error);
    }
  };

  socket.onclose = () => {
    console.log("WebSocket disconnected. Attempting to reconnect...");
    
    reconnectTimer = setTimeout(() => {
      connectWebSocket(onMessage);
    }, 3000);
  };

  socket.onerror = (error) => {
    console.error("WebSocket encountered an error. Closing socket...");
    socket.close(); 
  };
}

export function disconnectWebSocket() {
  if (reconnectTimer) clearTimeout(reconnectTimer);
  if (socket) {
    
    socket.onclose = () => console.log("WebSocket intentionally disconnected");
    socket.close();
    socket = null;
  }
}