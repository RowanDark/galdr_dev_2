// galdr/interceptor/frontend/src/renderer/services/RaiderManager.ts
// The dedicated service for all Raider API communications.

const API_BASE_URL = 'http://localhost:8000';

export interface AttackConfig {
  payloads: string[];
  // Future options like throttling, threads, etc., will go here.
}

export interface RaiderAttackRequest {
  attack_type: 'sniper'; // Only sniper is supported for now
  base_request_template: any;
  config: AttackConfig;
}

class RaiderManager {
    async launchAttack(attackData: RaiderAttackRequest): Promise<{ attack_id: string }> {
        const response = await fetch(`${API_BASE_URL}/api/raider/attacks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(attackData),
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Failed to launch attack.');
        }
        return response.json();
    }

    async stopAttack(attackId: string): Promise<{ message: string }> {
        const response = await fetch(`${API_BASE_URL}/api/raider/attacks/${attackId}`, {
            method: 'DELETE',
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Failed to stop attack.');
        }
        return response.json();
    }
}

export const raiderManager = new RaiderManager();
