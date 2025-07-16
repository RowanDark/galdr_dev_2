// galdr/interceptor/frontend/src/renderer/services/ReplayForgeManager.ts
// Service layer to handle all backend communication for Replay Forge.

const API_BASE_URL = 'http://localhost:8000';

export interface ReplayTab {
  id: string;
  name: string;
  original_request: any; // Define a more specific type later
}

export interface SendRequestData {
    method: string;
    url: string;
    headers: Record<string, string>;
    body: string;
}

export interface ReplayResult {
    request_id: string;
    response: {
        id: string;
        status_code: number;
        headers_json: Record<string, string>;
        body: string;
        response_time_ms: number;
        error: string | null;
    }
}

class ReplayForgeManager {
  async createTab(name: string, originalRequest: any): Promise<ReplayTab> {
    const response = await fetch(`${API_BASE_URL}/api/replay/tabs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, original_request: originalRequest }),
    });
    if (!response.ok) {
      throw new Error('Failed to create Replay Forge tab');
    }
    return response.json();
  }

  async sendRequest(tabId: string, data: SendRequestData): Promise<ReplayResult> {
    const response = await fetch(`${API_BASE_URL}/api/replay/tabs/${tabId}/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        throw new Error('Failed to send request');
      }
      return response.json();
  }

  // Add more methods here later, e.g., getTabs, getHistory, etc.
}

export const replayForgeManager = new ReplayForgeManager();
