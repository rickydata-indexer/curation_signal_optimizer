import React from 'react';
import MetricCard from './MetricCard';
import { DollarSign, TrendingUp, Wallet, Target } from 'lucide-react';

export default function SummaryTab({ 
  walletAddress, 
  grtPrice, 
  userSignals, 
  totalValue, 
  totalEarnings, 
  averageAPR,
  diversificationMetrics
}) {
  const formatCurrency = (value) => `$${value.toFixed(2)}`;
  const formatGRT = (value) => `${value.toFixed(0)} GRT`;
  const formatPercent = (value) => `${value.toFixed(2)}%`;

  // Get risk level color
  const getRiskLevelColor = (riskLevel) => {
    switch (riskLevel?.toLowerCase()) {
      case 'low': return 'text-emerald-600';
      case 'medium': return 'text-yellow-600';
      case 'high': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  // Get diversification level
  const getDiversificationLevel = (score) => {
    if (score >= 75) return { label: 'Excellent', color: 'text-emerald-600' };
    if (score >= 50) return { label: 'Good', color: 'text-blue-600' };
    if (score >= 25) return { label: 'Fair', color: 'text-yellow-600' };
    return { label: 'Poor', color: 'text-red-600' };
  };

  // Get optimization level
  const getOptimizationLevel = (score) => {
    if (score >= 80) return { label: 'Excellent', color: 'text-purple-600' };
    if (score >= 60) return { label: 'Good', color: 'text-blue-600' };
    if (score >= 40) return { label: 'Fair', color: 'text-yellow-600' };
    return { label: 'Needs Work', color: 'text-red-600' };
  };

  const diversificationLevel = getDiversificationLevel(diversificationMetrics?.diversificationScore || 0);
  const optimizationLevel = getOptimizationLevel(diversificationMetrics?.optimizationScore || 0);

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Portfolio Value"
          value={formatCurrency(totalValue)}
          subtitle={formatGRT(totalValue / grtPrice)}
          icon={DollarSign}
          iconColor="text-emerald-600"
        />
        
        <MetricCard
          title="Annual Earnings"
          value={formatCurrency(totalEarnings)}
          subtitle="Estimated returns"
          icon={TrendingUp}
          iconColor="text-blue-600"
        />
        
        <MetricCard
          title="Active Signals"
          value={userSignals.length}
          subtitle="Subgraphs curated"
          icon={Target}
          iconColor="text-purple-600"
        />
        
        <MetricCard
          title="Average APR"
          value={formatPercent(averageAPR)}
          subtitle="Weighted average"
          icon={Wallet}
          iconColor="text-orange-600"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="card-neumorphic p-6">
          <h3 className="text-xl font-bold text-neumorphic-dark mb-4">
            Portfolio Distribution
          </h3>
          <div className="space-y-4">
            {userSignals.length > 0 ? (
              userSignals.slice(0, 5).map((signal, index) => (
                <div key={signal.ipfs_hash} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="neumorphic-subtle w-10 h-10 rounded-full flex items-center justify-center">
                      <span className="text-sm font-bold text-neumorphic-dark">
                        {index + 1}
                      </span>
                    </div>
                    <div>
                      <p className="font-medium text-neumorphic-dark">
                        {signal.subgraph_name || `${signal.ipfs_hash.slice(0, 8)}...`}
                      </p>
                      <p className="text-sm text-neumorphic">
                        {formatGRT(signal.signal_amount)}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-medium text-neumorphic-dark">
                      {formatPercent(signal.apr)}
                    </p>
                    <p className="text-sm text-neumorphic">APR</p>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8">
                <p className="text-neumorphic">No active signals found</p>
              </div>
            )}
          </div>
        </div>

        <div className="card-neumorphic p-6">
          <h3 className="text-xl font-bold text-neumorphic-dark mb-4">
            Performance Insights
          </h3>
          <div className="space-y-6">
            <div className="neumorphic-subtle rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-neumorphic">Risk Level</span>
                <span className={`text-sm font-bold ${getRiskLevelColor(diversificationMetrics?.riskLevel)}`}>
                  {diversificationMetrics?.riskLevel || 'Unknown'}
                </span>
              </div>
              <div className="neumorphic-inset rounded-full h-2 overflow-hidden">
                <div 
                  className={`h-full bg-gradient-to-r ${
                    diversificationMetrics?.riskLevel?.toLowerCase() === 'low' 
                      ? 'from-emerald-400 to-emerald-600 w-1/4'
                      : diversificationMetrics?.riskLevel?.toLowerCase() === 'medium'
                      ? 'from-yellow-400 to-yellow-600 w-2/4'
                      : diversificationMetrics?.riskLevel?.toLowerCase() === 'high'
                      ? 'from-red-400 to-red-600 w-3/4'
                      : 'from-gray-400 to-gray-600 w-1/6'
                  }`}
                ></div>
              </div>
            </div>
            
            <div className="neumorphic-subtle rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-neumorphic">Diversification</span>
                <span className={`text-sm font-bold ${diversificationLevel.color}`}>
                  {diversificationLevel.label}
                </span>
              </div>
              <div className="neumorphic-inset rounded-full h-2 overflow-hidden">
                <div 
                  className={`h-full bg-gradient-to-r ${diversificationLevel.color.includes('emerald') ? 'from-emerald-400 to-emerald-600' :
                    diversificationLevel.color.includes('blue') ? 'from-blue-400 to-blue-600' :
                    diversificationLevel.color.includes('yellow') ? 'from-yellow-400 to-yellow-600' :
                    'from-red-400 to-red-600'}`}
                  style={{ width: `${Math.max(10, diversificationMetrics?.diversificationScore || 0)}%` }}
                ></div>
              </div>
            </div>
            
            <div className="neumorphic-subtle rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-neumorphic">Optimization Score</span>
                <span className={`text-sm font-bold ${optimizationLevel.color}`}>
                  {optimizationLevel.label}
                </span>
              </div>
              <div className="neumorphic-inset rounded-full h-2 overflow-hidden">
                <div 
                  className={`h-full bg-gradient-to-r ${optimizationLevel.color.includes('purple') ? 'from-purple-400 to-purple-600' :
                    optimizationLevel.color.includes('blue') ? 'from-blue-400 to-blue-600' :
                    optimizationLevel.color.includes('yellow') ? 'from-yellow-400 to-yellow-600' :
                    'from-red-400 to-red-600'}`}
                  style={{ width: `${Math.max(10, diversificationMetrics?.optimizationScore || 0)}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}