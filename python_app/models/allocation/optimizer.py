from dataclasses import dataclass
from typing import List, Dict, Optional
import numpy as np
from scipy.optimize import minimize
from models.opportunities import Opportunity

@dataclass
class AllocationResult:
    """Results from allocation optimization."""
    allocations: Dict[str, float]  # IPFS hash to GRT amount
    total_allocated: float
    expected_apr: float
    expected_earnings: float

class AllocationOptimizer:
    """Optimizes allocation of GRT across opportunities."""
    
    def __init__(self, opportunities: List[Opportunity], grt_price: float):
        self.opportunities = sorted(opportunities, key=lambda x: x.apr, reverse=True)
        self.grt_price = grt_price
        
    def calculate_portfolio_metrics(self, allocations: np.ndarray) -> tuple:
        """Calculate expected earnings and APR for given allocations."""
        total_earnings = 0
        total_allocated = sum(allocations)
        
        if total_allocated == 0:
            return 0, 0
            
        for i, opp in enumerate(self.opportunities):
            if allocations[i] > 0:
                # Calculate portion owned with new allocation
                new_total_signal = opp.signalled_tokens + allocations[i]
                portion_owned = allocations[i] / new_total_signal
                
                # Calculate earnings with very mild diminishing returns
                base_earnings = opp.curator_share * portion_owned
                # Logarithmic diminishing returns with minimal impact
                diminishing_factor = 1 / (1 + 0.01 * np.log1p(allocations[i] / opp.signalled_tokens))
                earnings = base_earnings * diminishing_factor
                
                total_earnings += earnings
        
        # Calculate overall APR
        apr = (total_earnings / (total_allocated * self.grt_price)) * 100
        
        return total_earnings, apr

    def optimize_high_apr_allocation(self, available_grt: float, min_allocation: float) -> np.ndarray:
        """First phase: Optimize allocation for high APR opportunities."""
        n_opportunities = len(self.opportunities)
        max_apr = max(opp.apr for opp in self.opportunities)
        
        # Calculate APR scores with aggressive weighting
        apr_scores = np.array([(opp.apr / max_apr) ** 2 for opp in self.opportunities])
        
        # Allocate to opportunities with APR above median
        median_apr = np.median([opp.apr for opp in self.opportunities])
        high_apr_mask = np.array([opp.apr >= median_apr for opp in self.opportunities])
        
        # Calculate initial allocation for high APR opportunities
        high_apr_total = available_grt * 0.7  # 70% to high APR
        if np.sum(high_apr_mask) > 0:
            high_apr_weights = apr_scores * high_apr_mask
            high_apr_weights /= np.sum(high_apr_weights)
            initial_allocation = high_apr_weights * high_apr_total
        else:
            initial_allocation = np.zeros(n_opportunities)
            
        return initial_allocation

    def optimize_allocation(self, available_grt: float, min_allocation: float = 100) -> AllocationResult:
        """Optimize GRT allocation across opportunities using a two-phase approach."""
        if available_grt <= 0:
            raise Exception("Available GRT must be greater than 0")
            
        n_opportunities = len(self.opportunities)
        
        # Phase 1: Initial allocation favoring high APR opportunities
        initial_allocation = self.optimize_high_apr_allocation(available_grt, min_allocation)
        
        def objective(x):
            """Objective function balancing APR and risk."""
            earnings, apr = self.calculate_portfolio_metrics(x)
            
            # Calculate concentration penalty
            total_alloc = sum(x)
            if total_alloc > 0:
                weights = x / total_alloc
                concentration = np.sum(weights ** 2)  # HHI
            else:
                concentration = 1
                
            # Calculate market impact
            market_impact = sum(
                (alloc / opp.signalled_tokens) ** 1.5
                for alloc, opp in zip(x, self.opportunities)
                if opp.signalled_tokens > 0 and alloc > 0
            )
            
            # Combine metrics with strong preference for APR
            return -(apr - 0.5 * concentration - 0.5 * market_impact)
        
        # Constraints
        constraints = [
            {'type': 'eq', 'fun': lambda x: sum(x) - available_grt}
        ]
        
        # Bounds - allow larger allocations for high APR opportunities
        bounds = []
        for i, opp in enumerate(self.opportunities):
            max_allocation = min(
                available_grt,
                opp.signalled_tokens * (1 + opp.apr / 100)  # Allow allocation proportional to APR
            )
            bounds.append((min_allocation, max_allocation))
        
        # Phase 2: Optimize with risk considerations
        result = minimize(
            objective,
            initial_allocation,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 1000}
        )
        
        if not result.success:
            raise Exception(f"Optimization failed: {result.message}")
        
        # Calculate final metrics
        earnings, apr = self.calculate_portfolio_metrics(result.x)
        
        # Create allocation dictionary
        allocations = {
            opp.ipfs_hash: float(alloc)
            for opp, alloc in zip(self.opportunities, result.x)
            if alloc >= min_allocation
        }
        
        return AllocationResult(
            allocations=allocations,
            total_allocated=float(sum(result.x)),
            expected_apr=apr,
            expected_earnings=earnings
        )
