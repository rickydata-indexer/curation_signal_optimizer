import React, { useState, useEffect } from 'react';
import { UserSignal, Opportunity } from '@/api/entities';
import WalletInput from '../components/WalletInput';
import TabNavigation from '../components/TabNavigation';
import SummaryTab from '../components/SummaryTab';
import SignalsTab from '../components/SignalsTab';
import OpportunitiesTab from '../components/OpportunitiesTab';
import SubgraphsTab from '../components/SubgraphsTab';

const DEFAULT_WALLET = "0x742d35cc6644c4532b156b8d90e1c65f5c1b5fdb";

// Mock data generation
const generateMockUserSignals = (walletAddress) => {
  const signals = [];
  const sampleHashes = [
    "QmR6A1vqgDVFGhj47R89UJBZJKqJNwfq8pGbmFY7k5HwA2",
    "QmS7B2wrhEVGij58S90VKCZJLrKpOx1gq9HcnFZ8m6KxB3",
    "QmT8C3xsiHVHjk69T01WLDaMLsLqPy2hr0IdOG9n7LyC4",
    "QmU9D4ytkIWIjl70U12XMEbNTtMrQz3is1JdPH0o8MyD5",
    "QmV0E5zuljXJkm81V23YOFcOUtOsS{4jt2KeQI1p9NzE6"
  ];
  
  sampleHashes.forEach((hash, index) => {
    signals.push({
      id: `${walletAddress}-${hash}`,
      wallet_address: walletAddress,
      ipfs_hash: hash,
      signal_amount: Math.random() * 5000 + 500,
      total_signal: Math.random() * 50000 + 10000,
      portion_owned: Math.random() * 0.1 + 0.01,
      estimated_earnings: Math.random() * 1000 + 100,
      apr: Math.random() * 20 + 5,
      weekly_queries: Math.floor(Math.random() * 10000 + 1000)
    });
  });
  
  return signals;
};

const generateMockOpportunities = () => {
  const opportunities = [];
  
  for (let i = 0; i < 100; i++) {
    const hash = `QmExample${i.toString().padStart(3, '0')}${Math.random().toString(36).substr(2, 30)}`;
    opportunities.push({
      id: hash,
      ipfs_hash: hash,
      subgraph_name: `Subgraph ${i + 1}`,
      signal_amount: Math.random() * 10000 + 1000,
      signalled_tokens: Math.random() * 100000 + 20000,
      annual_queries: Math.floor(Math.random() * 1000000 + 100000),
      total_earnings: Math.random() * 5000 + 500,
      curator_share: Math.random() * 500 + 50,
      estimated_earnings: Math.random() * 2000 + 200,
      apr: Math.random() * 25 + 2,
      weekly_queries: Math.floor(Math.random() * 20000 + 2000)
    });
  }
  
  return opportunities.sort((a, b) => b.apr - a.apr);
};

export default function Dashboard() {
  const [walletAddress, setWalletAddress] = useState(DEFAULT_WALLET);
  const [activeTab, setActiveTab] = useState('summary');
  const [userSignals, setUserSignals] = useState([]);
  const [opportunities, setOpportunities] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [grtPrice] = useState(0.0892); // Mock GRT price

  useEffect(() => {
    if (walletAddress) {
      loadData();
    }
  }, [walletAddress]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      // Simulate API calls with mock data
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const mockUserSignals = generateMockUserSignals(walletAddress);
      const mockOpportunities = generateMockOpportunities();
      
      setUserSignals(mockUserSignals);
      setOpportunities(mockOpportunities);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const calculateTotalValue = () => {
    return userSignals.reduce((sum, signal) => sum + (signal.signal_amount * grtPrice), 0);
  };

  const calculateTotalEarnings = () => {
    return userSignals.reduce((sum, signal) => sum + signal.estimated_earnings, 0);
  };

  const calculateAverageAPR = () => {
    if (userSignals.length === 0) return 0;
    const totalValue = calculateTotalValue();
    const weightedAPR = userSignals.reduce((sum, signal) => {
      const weight = (signal.signal_amount * grtPrice) / totalValue;
      return sum + (signal.apr * weight);
    }, 0);
    return weightedAPR;
  };

  const renderActiveTab = () => {
    switch (activeTab) {
      case 'summary':
        return (
          <SummaryTab
            walletAddress={walletAddress}
            grtPrice={grtPrice}
            userSignals={userSignals}
            totalValue={calculateTotalValue()}
            totalEarnings={calculateTotalEarnings()}
            averageAPR={calculateAverageAPR()}
          />
        );
      case 'signals':
        return <SignalsTab userSignals={userSignals} grtPrice={grtPrice} />;
      case 'opportunities':
        return <OpportunitiesTab opportunities={opportunities} grtPrice={grtPrice} />;
      case 'subgraphs':
        return <SubgraphsTab opportunities={opportunities} />;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-8">
      <WalletInput
        value={walletAddress}
        onChange={setWalletAddress}
        className="max-w-2xl mx-auto"
      />

      {walletAddress && (
        <>
          <TabNavigation
            activeTab={activeTab}
            onTabChange={setActiveTab}
          />

          {isLoading ? (
            <div className="card-neumorphic p-12 text-center">
              <div className="neumorphic-subtle rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-6">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
              <p className="text-neumorphic text-lg">Loading your curation data...</p>
            </div>
          ) : (
            renderActiveTab()
          )}
        </>
      )}
    </div>
  );
}