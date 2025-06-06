import React from 'react';
import MetricCard from './MetricCard';
import { DollarSign, TrendingUp, Wallet, Target } from 'lucide-react';

export default function SummaryTab({ 
  walletAddress, 
  grtPrice, 
  userSignals, 
  totalValue, 
  totalEarnings, 
  averageAPR 
}) {
  const formatCurrency = (value) => `$${value.toFixed(2)}`;
  const formatGRT = (value) => `${value.toFixed(0)} GRT`;
  const formatPercent = (value) => `${value.toFixed(2)}%`;

  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Portfolio Value"
          value={formatCurrency(totalValue)}
          subtitle={formatGRT(totalValue / grtPrice)}
          icon={DollarSign}
          iconColor="text-emerald-600"
          trend={{ value: "12.5%", label: "vs last month", isPositive: true }}
        />
        
        <MetricCard
          title="Annual Earnings"
          value={formatCurrency(totalEarnings)}
          subtitle="Estimated returns"
          icon={TrendingUp}
          iconColor="text-blue-600"
          trend={{ value: "8.3%", label: "vs projection", isPositive: true }}
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
          trend={{ value: "2.1%", label: "vs market", isPositive: true }}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="card-neumorphic p-6">
          <h3 className="text-xl font-bold text-neumorphic-dark mb-4">
            Portfolio Distribution
          </h3>
          <div className="space-y-4">
            {userSignals.slice(0, 5).map((signal, index) => (
              <div key={signal.ipfs_hash} className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="neumorphic-subtle w-10 h-10 rounded-full flex items-center justify-center">
                    <span className="text-sm font-bold text-neumorphic-dark">
                      {index + 1}
                    </span>
                  </div>
                  <div>
                    <p className="font-medium text-neumorphic-dark">
                      {signal.ipfs_hash.slice(0, 8)}...
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
            ))}
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
                <span className="text-sm font-bold text-emerald-600">Low</span>
              </div>
              <div className="neumorphic-inset rounded-full h-2 overflow-hidden">
                <div className="h-full bg-gradient-to-r from-emerald-400 to-emerald-600 w-1/4"></div>
              </div>
            </div>
            
            <div className="neumorphic-subtle rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-neumorphic">Diversification</span>
                <span className="text-sm font-bold text-blue-600">Good</span>
              </div>
              <div className="neumorphic-inset rounded-full h-2 overflow-hidden">
                <div className="h-full bg-gradient-to-r from-blue-400 to-blue-600 w-3/4"></div>
              </div>
            </div>
            
            <div className="neumorphic-subtle rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-neumorphic">Optimization Score</span>
                <span className="text-sm font-bold text-purple-600">Excellent</span>
              </div>
              <div className="neumorphic-inset rounded-full h-2 overflow-hidden">
                <div className="h-full bg-gradient-to-r from-purple-400 to-purple-600 w-5/6"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}