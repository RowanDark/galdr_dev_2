// galdr/interceptor/frontend/src/renderer/components/replay_forge/RequestTabs.tsx
// This component renders the interactive tab bar at the top of the Replay Forge UI.

import React from 'react';
import { Plus, X } from 'lucide-react';
import { ReplayTab } from '../../services/ReplayForgeManager'; // Import the type

interface RequestTabsProps {
  tabs: ReplayTab[];
  activeTabId: string | null;
  onTabChange: (tabId: string) => void;
  onTabClose: (tabId: string) => void;
  onCreateTab: () => void;
}

export const RequestTabs: React.FC<RequestTabsProps> = ({ tabs, activeTabId, onTabChange, onTabClose, onCreateTab }) => {
  return (
    <div className="flex items-center border-b border-gray-700 bg-gray-900 pr-2">
      <div className="flex-grow flex items-center overflow-x-auto">
        {tabs.map(tab => (
          <div
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`flex items-center gap-2 px-4 py-3 cursor-pointer border-r border-gray-700 text-sm whitespace-nowrap ${
              activeTabId === tab.id
                ? 'bg-gray-800 text-white border-b-2 border-blue-500'
                : 'text-gray-400 hover:bg-gray-700/50'
            }`}
          >
            <span>{tab.name}</span>
            <button
              onClick={(e) => {
                e.stopPropagation(); // Prevent tab selection when closing
                onTabClose(tab.id);
              }}
              className="p-0.5 rounded-full hover:bg-gray-600"
            >
              <X size={14} />
            </button>
          </div>
        ))}
      </div>
      <button 
        onClick={onCreateTab} 
        className="ml-2 p-2 flex-shrink-0 bg-gray-700 rounded-md hover:bg-blue-600"
        title="New Tab"
      >
        <Plus size={16} />
      </button>
    </div>
  );
};
