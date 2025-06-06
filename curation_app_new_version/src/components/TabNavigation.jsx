import React from 'react';
import { BarChart3, Wallet, Search, List } from 'lucide-react';

const tabs = [
  { id: 'summary', label: 'Summary', icon: BarChart3 },
  { id: 'signals', label: 'Your Signals', icon: Wallet },
  { id: 'opportunities', label: 'Opportunities', icon: Search },
  { id: 'subgraphs', label: 'All Subgraphs', icon: List }
];

export default function TabNavigation({ activeTab, onTabChange }) {
  return (
    <div className="neumorphic-subtle rounded-2xl p-2 mb-8">
      <div className="flex space-x-2">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          const Icon = tab.icon;
          
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`
                flex items-center space-x-3 px-6 py-4 rounded-xl font-medium
                transition-all duration-200 flex-1 justify-center
                ${isActive ? 'tab-active' : 'tab-inactive'}
              `}
            >
              <Icon className="w-5 h-5" />
              <span className="hidden md:inline">{tab.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}