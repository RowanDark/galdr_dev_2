// galdr/interceptor/frontend/src/renderer/services/PortalManager.ts
// --- UPDATED ---
// This service now includes a method for sending contextual analysis requests.

const API_BASE_URL = 'http://localhost:8000';

export interface PortalConversation {
    id: string;
    title: string;
    created_at: string;
}

export interface PortalMessage {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: string;
}

class PortalManager {
    async getConversations(): Promise<PortalConversation[]> {
        const response = await fetch(`${API_BASE_URL}/api/portal/conversations`);
        if (!response.ok) throw new Error("Failed to fetch conversations");
        return response.json();
    }

    async startNewConversation(): Promise<PortalConversation> {
        const response = await fetch(`${API_BASE_URL}/api/portal/conversations`, { method: 'POST' });
        if (!response.ok) throw new Error("Failed to start conversation");
        return response.json();
    }
    
    async getMessages(conversationId: string): Promise<PortalMessage[]> {
        const response = await fetch(`${API_BASE_URL}/api/portal/conversations/${conversationId}/messages`);
        if (!response.ok) throw new Error("Failed to fetch messages");
        return response.json();
    }

    async sendMessage(conversationId: string, content: string): Promise<PortalMessage> {
        const response = await fetch(`${API_BASE_URL}/api/portal/conversations/${conversationId}/messages`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content }),
        });
        if (!response.ok) throw new Error("Failed to send message");
        return response.json();
    }
    
    // NEW METHOD: This sends the user's prompt AND a context object to the backend.
    async analyzeWithContext(
        conversationId: string, 
        content: string, 
        context: Record<string, any>
    ): Promise<PortalMessage> {
        const response = await fetch(`${API_BASE_URL}/api/portal/conversations/${conversationId}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content, context }),
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Failed to send analysis request");
        }
        return response.json();
    }
}

export const portalManager = new PortalManager();
