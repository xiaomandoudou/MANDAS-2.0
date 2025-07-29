const WS_BASE_URL = import.meta.env.VITE_WS_URL;

const ws = new WebSocket(`${WS_BASE_URL}/your-endpoint`);

// ...existing code...