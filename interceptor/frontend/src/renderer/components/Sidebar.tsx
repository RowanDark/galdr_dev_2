// galdr/interceptor/frontend/src/renderer/components/Sidebar.tsx
// --- REFACTORED ---
// Removed `Cartographer` and added placeholders for our real module suite.

import React from 'react';
import { 
  Home, 
  Globe, 
  Repeat, 
  Search,
  Activity,
  Settings, 
  Bug,       // Raider
  GitCompare, // Mirror Mirror
  ALargeSmall, // Mystic Cipher
  ScatterChart, // Entropy
  Share2,     // Accomplice
  BrainCircuit, // Portal AI
  Shield,
  Zap       // Placeholder for Spider
} from 'lucide-react';

type ViewType = 'dashboard' | 'traffic' | 'recon' | 'crawler' | 'spider' | 'replay_forge' | 'raider' | 'mirror' | 'entropy' | 'cipher' | 'accomplice' | 'portal' | 'config';
type ProxyStatus = 'stopped' | 'starting' | 'running' | 'error';

interface SidebarProps {
  currentView: ViewType;
  onViewChange: (view: ViewType) => void;
  proxyStatus: ProxyStatus;
  trafficCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ 
  currentView, 
  onViewChange, 
  proxyStatus,
  trafficCount
}) => {
    // New, comprehensive menu reflecting your Galdr 3.0 vision
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Home },
    { id: 'traffic', label: 'Traffic', icon: Globe, badge: trafficCount > 0 ? trafficCount : undefined },
    { id: 'portal', label: 'Portal AI', icon: BrainCircuit, section: 'Core Tools' },
    { id: 'replay_forge', label: 'Replay Forge', icon: Repeat },
    { id: 'raider', label: 'Raider', icon: Bug },
    { id: 'recon', label: "Mimir's Recon", icon: Search, section: 'Discovery' },
    { id: 'crawler', label: 'Passive Crawler', icon: Activity },
    { id: 'spider', label: 'Active Spider', icon: Zap },
    { id: 'accomplice', label: 'Accomplice', icon: Share2, section: 'Analysis' },
    { id: 'mirror', label: 'Mirror Mirror', icon: GitCompare },
    { id: 'entropy', label: 'Entropy', icon: ScatterChart },
    { id: 'cipher', label: 'Mystic Cipher', icon: ALargeSmall },
    { id: 'config', label: 'Configuration', icon: Settings, section: 'System' },
  ];

  const getStatusColor = () => {
    if (proxyStatus === 'running') return 'text-green-400';
    if (proxyStatus === 'starting') return 'text-yellow-400';
    return 'text-red-400';
  };

  const sections: { [key: string]: ViewType[] } = {};
  menuItems.forEach(item => {
    const sectionName = item.section || 'Main';
    if (!sections[sectionName]) {
      sections[sectionName] = [];
    }
    sections[sectionName].push(item.id as ViewType);
  });

  return (
    <div className="w-64 bg-gray-900 text-white flex flex-col flex-shrink-0">
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center space-x-3">
          <Shield className="w-8 h-8 text-blue-500" />
          <h1 className="text-2xl font-bold tracking-wider">GALDR</h1>
        </div>
        <div className={`flex items-center space-x-2 mt-3 text-sm ${getStatusColor()}`}>
          <div className="w-2.5 h-2.5 rounded-full bg-current" />
          <span>Proxy: <span className="font-semibold capitalize">{proxyStatus}</span></span>
        </div>
      </div>

      <nav className="flex-1 p-2 overflow-y-auto">
        {Object.entries(sections).map(([sectionName, items]) => (
            <div key={sectionName} className="mb-4">
                {sectionName !== 'Main' && <h3 className="px-3 py-2 text-xs font-bold uppercase text-gray-500 tracking-wider">{sectionName}</h3>}
                <ul className="space-y-1">
                    {items.map((itemId) => {
                        const item = menuItems.find(m => m.id === itemId)!;
                        const Icon = item.icon;
                        const isActive = currentView === item.id;
                        
                        return (
                        <li key={item.id}>
                            <button
                            onClick={() => onViewChange(item.id as ViewType)}
                            className={`w-full flex items-center justify-between p-3 rounded-lg text-sm transition-colors ${
                                isActive 
                                ? 'bg-blue-600 font-semibold text-white' 
                                : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                            }`}
                            >
                            <div className="flex items-center space-x-3">
                                <Icon className="w-5 h-5" />
                                <span>{item.label}</span>
                            </div>
                            {item.badge && (
                                <span className="bg-red-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">
                                {item.badge > 999 ? '999+' : item.badge}
                                </span>
                            )}
                            </button>
                        </li>
                        );
                    })}
                </ul>
            </div>
        ))}
      </nav>

      <div className="p-4 border-t border-gray-700 text-center text-xs text-gray-500">
        <p>Galdr 3.0 Dev</p>
      </div>
    </div>
  );
};
