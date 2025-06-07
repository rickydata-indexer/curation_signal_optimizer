import React, { useState, useEffect } from 'react';
import WalletInput from '../components/WalletInput';
import TabNavigation from '../components/TabNavigation';
import SummaryTab from '../components/SummaryTab';
import SignalsTab from '../components/SignalsTab';
import OpportunitiesTab from '../components/OpportunitiesTab';
import SubgraphsTab from '../components/SubgraphsTab';

// Import real APIs
import { getSubgraphDeployments, getUserCurationSignal, getGrtPrice } from '../api/graphApi';
import { processQueryData } from '../api/supabaseApi';
import { 
  calculateOpportunities, 
  calculateUserOpportunities,
  calculatePortfolioMetrics,
  calculateDiversificationMetrics
} from '../utils/opportunityCalculator';
import { validateAndNormalizeAddress } from '../utils/addressValidation';

const DEFAULT_WALLET = "0x74dbb201ecc0b16934e68377bc13013883d9417b";

export default function Dashboard() {
  const [walletAddress, setWalletAddress] = useState(DEFAULT_WALLET);
  const [activeTab, setActiveTab] = useState('summary');
  const [userSignals, setUserSignals] = useState([]);
  const [userOpportunities, setUserOpportunities] = useState([]);
  const [allOpportunities, setAllOpportunities] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [grtPrice, setGrtPrice] = useState(0.0892);
  const [error, setError] = useState(null);
  const [portfolioMetrics, setPortfolioMetrics] = useState({
    totalValue: 0,
    totalEarnings: 0,
    averageAPR: 0,
    totalSignalAmount: 0,
    positionCount: 0
  });
  const [diversificationMetrics, setDiversificationMetrics] = useState({
    riskLevel: 'Unknown',
    diversificationScore: 0,
    optimizationScore: 0,
    concentration: 1.0
  });

  useEffect(() => {
    if (walletAddress) {
      loadData();
    }
  }, [walletAddress]);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      console.log('Loading data for wallet:', walletAddress);
      
      // Validate wallet address first
      const validation = validateAndNormalizeAddress(walletAddress);
      if (!validation.isValid) {
        throw new Error(`Invalid wallet address: ${validation.error}`);
      }
      
      const normalizedAddress = validation.normalized;
      console.log('Normalized address:', normalizedAddress);
      
      // Load basic data in parallel
      const [deployments, queryData, currentGrtPrice] = await Promise.all([
        getSubgraphDeployments(),
        processQueryData(),
        getGrtPrice()
      ]);

      console.log('Loaded deployments:', deployments.length);
      console.log('Loaded query data:', Object.keys(queryData.queryFees).length, 'subgraphs');
      
      setGrtPrice(currentGrtPrice);

      // Calculate all opportunities
      const opportunities = calculateOpportunities(
        deployments, 
        queryData.queryFees, 
        queryData.queryCounts, 
        currentGrtPrice
      );
      
      console.log('Calculated opportunities:', opportunities.length);
      setAllOpportunities(opportunities);

      // Load user-specific data
      const signals = await getUserCurationSignal(normalizedAddress);
      console.log('Loaded user signals for', normalizedAddress, ':', signals.length);
      console.log('Signal details:', signals);
      setUserSignals(signals);

      if (signals.length > 0) {
        // Calculate user opportunities
        const userOpps = calculateUserOpportunities(signals, opportunities, currentGrtPrice);
        console.log('Calculated user opportunities:', userOpps.length);
        console.log('User opportunities:', userOpps);
        setUserOpportunities(userOpps);

        // Calculate portfolio metrics
        const portfolioMetrics = calculatePortfolioMetrics(userOpps, currentGrtPrice);
        console.log('Portfolio metrics:', portfolioMetrics);
        setPortfolioMetrics(portfolioMetrics);

        // Calculate diversification metrics
        const diversificationMetrics = calculateDiversificationMetrics(userOpps);
        setDiversificationMetrics(diversificationMetrics);
      } else {
        console.log('No signals found for address:', normalizedAddress);
        setUserOpportunities([]);
        setPortfolioMetrics({
          totalValue: 0,
          totalEarnings: 0,
          averageAPR: 0,
          totalSignalAmount: 0,
          positionCount: 0
        });
        setDiversificationMetrics({
          riskLevel: 'Unknown',
          diversificationScore: 0,
          optimizationScore: 0,
          concentration: 1.0
        });
      }

    } catch (error) {
      console.error('Error loading data:', error);
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const renderActiveTab = () => {
    if (error) {
      return (
        <div className="card-neumorphic p-12 text-center">
          <div className="text-red-600 mb-4">
            <svg className="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.314 18.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h3 className="text-xl font-bold text-neumorphic-dark mb-2">Error Loading Data</h3>
          <p className="text-neumorphic mb-4">{error}</p>
          <button 
            onClick={loadData}
            className="btn-neumorphic px-6 py-2 rounded-lg"
          >
            Retry
          </button>
        </div>
      );
    }

    switch (activeTab) {
      case 'summary':
        return (
          <SummaryTab
            walletAddress={walletAddress}
            grtPrice={grtPrice}
            userSignals={userOpportunities}
            totalValue={portfolioMetrics.totalValue}
            totalEarnings={portfolioMetrics.totalEarnings}
            averageAPR={portfolioMetrics.averageAPR}
            diversificationMetrics={diversificationMetrics}
          />
        );
      case 'signals':
        return <SignalsTab userSignals={userOpportunities} grtPrice={grtPrice} />;
      case 'opportunities':
        return <OpportunitiesTab opportunities={allOpportunities} grtPrice={grtPrice} />;
      case 'subgraphs':
        return <SubgraphsTab opportunities={allOpportunities} />;
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
              <p className="text-neumorphic text-sm mt-2">
                Fetching subgraph deployments and query volume data...
              </p>
            </div>
          ) : (
            renderActiveTab()
          )}
        </>
      )}

      {walletAddress && userSignals.length === 0 && !isLoading && !error && (
        <div className="card-neumorphic p-12 text-center">
          <div className="text-neumorphic mb-4">
            <svg className="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <h3 className="text-xl font-bold text-neumorphic-dark mb-2">No Curation Signals Found</h3>
          <p className="text-neumorphic mb-4">
            This wallet doesn't have any active curation signals yet.
          </p>
          <div className="space-y-3">
            <p className="text-neumorphic text-sm">
              Try one of these addresses with active signals:
            </p>
            <div className="bg-gray-100 rounded-lg p-3 font-mono text-sm">
              <button 
                onClick={() => setWalletAddress("0x74dbb201ecc0b16934e68377bc13013883d9417b")}
                className="text-blue-600 hover:text-blue-800 underline block mb-1"
                title="Click to load this address"
              >
                0x74dbb201ecc0b16934e68377bc13013883d9417b
              </button>
              <button 
                onClick={() => setWalletAddress("0x7849e1c1f1a54ee6d1e3c5bb7b2e68dfbc5a5cd4")}
                className="text-blue-600 hover:text-blue-800 underline block"
                title="Click to load this address"
              >
                0x7849e1c1f1a54ee6d1e3c5bb7b2e68dfbc5a5cd4
              </button>
            </div>
            <p className="text-neumorphic text-xs">
              Or start curating subgraphs to see your signals here!
            </p>
          </div>
        </div>
      )}
    </div>
  );
}