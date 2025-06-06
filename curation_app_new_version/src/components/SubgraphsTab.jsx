import React, { useState } from 'react';
import { Search, ExternalLink } from 'lucide-react';

export default function SubgraphsTab({ opportunities }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [showCount, setShowCount] = useState(50);

  const formatGRT = (value) => `${value.toFixed(0)} GRT`;
  const formatPercent = (value) => `${value.toFixed(2)}%`;
  const formatNumber = (value) => value.toLocaleString();

  const filteredSubgraphs = opportunities
    .filter(opp => 
      opp.ipfs_hash.toLowerCase().includes(searchTerm.toLowerCase())
    )
    .slice(0, showCount);

  return (
    <div className="space-y-6">
      {/* Search */}
      <div className="card-neumorphic p-6">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search subgraphs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input-neumorphic w-full pl-12 pr-4 py-4 rounded-xl text-lg"
          />
        </div>
      </div>

      {/* Subgraphs Table */}
      <div className="card-neumorphic p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-neumorphic-dark">
            All Subgraphs
          </h2>
          <div className="neumorphic-subtle rounded-xl px-4 py-2">
            <span className="text-sm font-medium text-neumorphic">
              {filteredSubgraphs.length} subgraphs
            </span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <div className="neumorphic-inset rounded-xl p-4">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-300">
                  <th className="text-left py-4 px-4 text-sm font-semibold text-neumorphic">
                    Subgraph
                  </th>
                  <th className="text-right py-4 px-4 text-sm font-semibold text-neumorphic">
                    APR
                  </th>
                  <th className="text-right py-4 px-4 text-sm font-semibold text-neumorphic">
                    Total Signal
                  </th>
                  <th className="text-right py-4 px-4 text-sm font-semibold text-neumorphic">
                    Weekly Queries
                  </th>
                  <th className="text-right py-4 px-4 text-sm font-semibold text-neumorphic">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredSubgraphs.map((subgraph, index) => (
                  <tr 
                    key={subgraph.ipfs_hash}
                    className="border-b border-gray-200 hover:bg-gray-50 hover:bg-opacity-30 transition-colors"
                  >
                    <td className="py-4 px-4">
                      <div>
                        <p className="font-medium text-neumorphic-dark">
                          #{subgraph.ipfs_hash.slice(0, 8)}
                        </p>
                        <p className="text-sm text-neumorphic font-mono">
                          {subgraph.ipfs_hash}
                        </p>
                      </div>
                    </td>
                    <td className="py-4 px-4 text-right">
                      <span className={`font-bold ${
                        subgraph.apr > 10 ? 'text-emerald-600' : 
                        subgraph.apr > 5 ? 'text-blue-600' : 'text-neumorphic-dark'
                      }`}>
                        {formatPercent(subgraph.apr)}
                      </span>
                    </td>
                    <td className="py-4 px-4 text-right">
                      <span className="font-medium text-neumorphic-dark">
                        {formatGRT(subgraph.signalled_tokens)}
                      </span>
                    </td>
                    <td className="py-4 px-4 text-right">
                      <span className="font-medium text-neumorphic-dark">
                        {formatNumber(subgraph.weekly_queries)}
                      </span>
                    </td>
                    <td className="py-4 px-4 text-right">
                      <button className="neumorphic-subtle p-2 rounded-lg hover:scale-105 transition-transform">
                        <ExternalLink className="w-4 h-4 text-neumorphic" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {filteredSubgraphs.length < opportunities.length && (
          <div className="text-center mt-8">
            <button
              onClick={() => setShowCount(prev => prev + 50)}
              className="btn-neumorphic px-8 py-4 rounded-xl font-medium text-neumorphic-dark"
            >
              Load More Subgraphs
            </button>
          </div>
        )}
      </div>
    </div>
  );
}