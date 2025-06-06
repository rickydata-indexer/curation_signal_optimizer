import React, { useState } from 'react';
import { Wallet } from 'lucide-react';

export default function WalletInput({ value, onChange, className = "" }) {
  const [isFocused, setIsFocused] = useState(false);

  return (
    <div className={`relative ${className}`}>
      <div className="neumorphic-subtle rounded-2xl p-6">
        <label className="block text-sm font-medium text-neumorphic-dark mb-3">
          Wallet Address
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <Wallet className="h-5 w-5 text-gray-500" />
          </div>
          <input
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder="0x..."
            className={`
              input-neumorphic w-full pl-12 pr-4 py-4 rounded-xl text-lg font-mono
              placeholder-gray-400 transition-all duration-200
              ${isFocused ? 'ring-2 ring-blue-300' : ''}
            `}
          />
        </div>
        <p className="text-xs text-neumorphic mt-2">
          Enter your Ethereum wallet address to view your curation signals
        </p>
      </div>
    </div>
  );
}