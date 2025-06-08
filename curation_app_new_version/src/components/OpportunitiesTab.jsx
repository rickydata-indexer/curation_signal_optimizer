import React, { useState } from 'react';
import { Search, Filter, TrendingUp, DollarSign } from 'lucide-react';
import { openSubgraphLink } from '../utils/subgraphLinks';

export default function OpportunitiesTab({ opportunities, grtPrice }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [minAPR, setMinAPR] = useState('');
  const [sortBy, setSortBy] = useState('apr');
  const [showCount, setShowCount] = useState(20);

  const formatCurrency = (value) => `$${value.toFixed(2)}`;
  const formatGRT = (value) => `${value.toFixed(0)} GRT`;
  const formatPercent = (value) => `${value.toFixed(2)}%`;
  const formatNumber = (value) => value.toLocaleString();

  const filteredOpportunities = opportunities
    .filter(opp => {
      const matchesSearch = opp.ipfs_hash.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesAPR = !minAPR || opp.apr >= parseFloat(minAPR);
      return matchesSearch && matchesAPR;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'apr':
          return b.apr - a.apr;
        case 'earnings':
          return b.estimated_earnings - a.estimated_earnings;
        case 'queries':
          return b.weekly_queries - a.weekly_queries;
        default:
          return b.apr - a.apr;
      }
    })
    .slice(0, showCount);

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="card-neumorphic p-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0 lg:space-x-6">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search by IPFS hash..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="input-neumorphic w-full pl-12 pr-4 py-4 rounded-xl"
              />
            </div>
          </div>
          
          <div className="flex flex-wrap gap-4">
            <div>
              <input
                type="number"
                placeholder="Min APR %"
                value={minAPR}
                onChange={(e) => setMinAPR(e.target.value)}
                className="input-neumorphic px-4 py-4 rounded-xl w-32"
              />
            </div>
            
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="input-neumorphic px-4 py-4 rounded-xl"
            >
              <option value="apr">Sort by APR</option>
              <option value="earnings">Sort by Earnings</option>
              <option value="queries">Sort by Queries</option>
            </select>
          </div>
        </div>
      </div>

      {/* Opportunities List */}
      <div className="card-neumorphic p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-neumorphic-dark">
            Investment Opportunities
          </h2>
          <div className="neumorphic-subtle rounded-xl px-4 py-2">
            <span className="text-sm font-medium text-neumorphic">
              Showing {filteredOpportunities.length} of {opportunities.length}
            </span>
          </div>
        </div>

        <div className="space-y-4">
          {filteredOpportunities.map((opportunity, index) => (
            <div key={opportunity.ipfs_hash} className="neumorphic-subtle rounded-xl p-6">
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
                        Subgraph #{opportunity.ipfs_hash.slice(0, 8)}
                      </h3>
                      <p className="text-sm text-neumorphic font-mono">
                        {opportunity.ipfs_hash}
                      </p>
                    </div>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 lg:gap-8">
                  <div className="text-center">
                    <p className="text-sm font-medium text-neumorphic mb-1">APR</p>
                    <p className="text-xl font-bold text-emerald-600">
                      {formatPercent(opportunity.apr)}
                    </p>
                  </div>
                  
                  <div className="text-center">
                    <p className="text-sm font-medium text-neumorphic mb-1">Est. Earnings</p>
                    <p className="text-lg font-bold text-neumorphic-dark">
                      {formatCurrency(opportunity.estimated_earnings)}
                    </p>
                  </div>
                  
                  <div className="text-center">
                    <p className="text-sm font-medium text-neumorphic mb-1">Total Signal</p>
                    <p className="text-lg font-bold text-neumorphic-dark">
                      {formatGRT(opportunity.signalled_tokens)}
                    </p>
                  </div>
                  
                  <div className="text-center">
                    <p className="text-sm font-medium text-neumorphic mb-1">Weekly Queries</p>
                    <p className="text-lg font-bold text-blue-600">
                      {formatNumber(opportunity.weekly_queries)}
                    </p>
                  </div>
                  
                  <div className="text-center">
                    <button
                      onClick={() => openSubgraphLink(opportunity.deployment_id, opportunity.ipfs_hash)}
                      className="btn-neumorphic px-6 py-3 rounded-xl font-medium text-neumorphic-dark hover:scale-105 transition-transform"
                      title="Signal on this subgraph in The Graph Explorer"
                    >
                      Signal
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {filteredOpportunities.length < opportunities.length && (
          <div className="text-center mt-8">
            <button
              onClick={() => setShowCount(prev => prev + 20)}
              className="btn-neumorphic px-8 py-4 rounded-xl font-medium text-neumorphic-dark"
            >
              Load More Opportunities
            </button>
          </div>
        )}
      </div>
    </div>
  );
}