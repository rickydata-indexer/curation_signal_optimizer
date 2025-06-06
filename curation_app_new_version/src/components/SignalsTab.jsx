import React from 'react';
import { ExternalLink, TrendingUp, DollarSign } from 'lucide-react';

export default function SignalsTab({ userSignals, grtPrice }) {
  const formatCurrency = (value) => `$${value.toFixed(2)}`;
  const formatGRT = (value) => `${value.toFixed(2)} GRT`;
  const formatPercent = (value) => `${value.toFixed(2)}%`;

  if (!userSignals.length) {
    return (
      <div className="card-neumorphic p-12 text-center">
        <div className="neumorphic-subtle rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-6">
          <TrendingUp className="w-10 h-10 text-gray-400" />
        </div>
        <h3 className="text-xl font-bold text-neumorphic-dark mb-2">
          No Curation Signals Found
        </h3>
        <p className="text-neumorphic">
          Start curating subgraphs to see your signals here
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="card-neumorphic p-6">
        <h2 className="text-2xl font-bold text-neumorphic-dark mb-6">
          Your Active Curation Signals
        </h2>
        
        <div className="overflow-hidden">
          <div className="grid grid-cols-1 gap-4">
            {userSignals.map((signal, index) => (
              <div key={signal.ipfs_hash} className="neumorphic-subtle rounded-xl p-6">
                <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-3">
                      <div className="neumorphic-subtle w-12 h-12 rounded-full flex items-center justify-center">
                        <span className="text-lg font-bold text-neumorphic-dark">
                          {index + 1}
                        </span>
                      </div>
                      <div>
                        <h3 className="text-lg font-bold text-neumorphic-dark">
                          Subgraph #{signal.ipfs_hash.slice(0, 8)}
                        </h3>
                        <p className="text-sm text-neumorphic font-mono">
                          {signal.ipfs_hash}
                        </p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex flex-wrap gap-4 lg:gap-8">
                    <div className="text-center">
                      <p className="text-sm font-medium text-neumorphic mb-1">Signal Amount</p>
                      <p className="text-lg font-bold text-neumorphic-dark">
                        {formatGRT(signal.signal_amount)}
                      </p>
                      <p className="text-sm text-neumorphic">
                        {formatCurrency(signal.signal_amount * grtPrice)}
                      </p>
                    </div>
                    
                    <div className="text-center">
                      <p className="text-sm font-medium text-neumorphic mb-1">Portfolio Share</p>
                      <p className="text-lg font-bold text-neumorphic-dark">
                        {formatPercent(signal.portion_owned * 100)}
                      </p>
                    </div>
                    
                    <div className="text-center">
                      <p className="text-sm font-medium text-neumorphic mb-1">Est. Earnings</p>
                      <p className="text-lg font-bold text-emerald-600">
                        {formatCurrency(signal.estimated_earnings)}
                      </p>
                      <p className="text-sm text-neumorphic">per year</p>
                    </div>
                    
                    <div className="text-center">
                      <p className="text-sm font-medium text-neumorphic mb-1">APR</p>
                      <p className="text-xl font-bold text-blue-600">
                        {formatPercent(signal.apr)}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <button className="btn-neumorphic p-3 rounded-xl">
                      <ExternalLink className="w-5 h-5 text-neumorphic" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}