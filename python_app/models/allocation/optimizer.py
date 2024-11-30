from dataclasses import dataclass
from typing import List, Dict, Optional
import numpy as np
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
    
    ENTRY_COST_PERCENTAGE = 0.005  # 0.5% entry cost
    CURATOR_SHARE = 0.10  # 10% of query fees
    EARNINGS_PER_100K_QUERIES = 4  # $4 per 100k queries
    STEP_SIZE = 10  # Allocate 10 GRT at a time
    
    def __init__(self, opportunities: List[Opportunity], grt_price: float):
        self.opportunities = sorted(opportunities, key=lambda x: x.apr, reverse=True)
        self.grt_price = grt_price
    
    def calculate_opportunity_metrics(self, opp: Opportunity, additional_signal: float = 0) -> tuple:
        """Calculate APR and earnings for an opportunity with additional signal."""
        total_signal = opp.signalled_tokens + additional_signal
        
        if total_signal <= 0:
            return 0, 0
            
        # Calculate total earnings based on $4 per 100,000 queries
        total_earnings = (opp.annual_queries / 100000) * self.EARNINGS_PER_100K_QUERIES
        
        # Calculate curator share (10% of total earnings)
        curator_share = total_earnings * self.CURATOR_SHARE
        
        # Calculate portion owned
        portion_owned = additional_signal / total_signal
        
        # Calculate estimated earnings
        estimated_earnings = curator_share * portion_owned
        
        # Calculate APR
        investment_value = additional_signal * self.grt_price
        apr = (estimated_earnings / investment_value) * 100 if investment_value > 0 else 0
        
        return apr, estimated_earnings

    def find_best_opportunity(self, current_allocations: Dict[str, float], step_size: float) -> tuple:
        """Find the best opportunity for the next allocation step."""
        best_apr = -1
        best_opp = None
        
        for opp in self.opportunities:
            current_allocation = current_allocations.get(opp.ipfs_hash, 0)
            
            # Calculate metrics with additional step_size allocation
            apr, _ = self.calculate_opportunity_metrics(opp, current_allocation + step_size)
            
            # Consider entry cost if this is a new position
            if current_allocation == 0:
                # Reduce APR by entry cost
                apr -= (self.ENTRY_COST_PERCENTAGE * 100)
            
            if apr > best_apr:
                best_apr = apr
                best_opp = opp
        
        return best_opp, best_apr

    def calculate_portfolio_metrics(self, allocations: Dict[str, float]) -> tuple:
        """Calculate portfolio-wide metrics."""
        total_earnings = 0
        total_allocated = sum(allocations.values())
        
        if total_allocated == 0:
            return 0, 0
        
        # Calculate entry costs
        active_positions = len([v for v in allocations.values() if v > 0])
        total_entry_cost = total_allocated * self.ENTRY_COST_PERCENTAGE * active_positions
        
        # Calculate earnings for each position
        weighted_aprs = []
        for opp in self.opportunities:
            allocation = allocations.get(opp.ipfs_hash, 0)
            if allocation > 0:
                apr, earnings = self.calculate_opportunity_metrics(opp, allocation)
                total_earnings += earnings
                # Weight APR by allocation size
                weighted_aprs.append(apr * (allocation / total_allocated))
        
        # Subtract entry costs from earnings
        net_earnings = total_earnings - (total_entry_cost * self.grt_price)
        
        # Calculate weighted average APR
        portfolio_apr = sum(weighted_aprs) if weighted_aprs else 0
        
        return net_earnings, portfolio_apr

    def optimize_allocation(self, available_grt: float) -> AllocationResult:
        """Optimize GRT allocation using iterative approach."""
        if available_grt <= 0:
            raise Exception("Available GRT must be greater than 0")
        
        # Initialize allocations
        allocations = {}
        remaining_grt = available_grt
        min_step = self.STEP_SIZE
        
        # Keep track of APRs to detect diminishing returns
        last_best_apr = float('inf')
        apr_decline_count = 0
        
        while remaining_grt >= min_step:
            # Find best opportunity for next allocation
            best_opp, best_apr = self.find_best_opportunity(allocations, min_step)
            
            # Stop if no good opportunities left
            if best_opp is None or best_apr <= 0:
                break
                
            # Track APR decline
            if best_apr < last_best_apr:
                apr_decline_count += 1
            else:
                apr_decline_count = 0
            last_best_apr = best_apr
            
            # Increase step size if APR is still good
            current_step = min_step
            if apr_decline_count < 3 and remaining_grt >= min_step * 10:
                current_step = min_step * 10
            
            # Allocate to best opportunity
            current_allocation = allocations.get(best_opp.ipfs_hash, 0)
            allocations[best_opp.ipfs_hash] = current_allocation + current_step
            remaining_grt -= current_step
            
            # If APR is declining rapidly, try other opportunities
            if apr_decline_count >= 5:
                break
        
        # If we have remaining GRT, distribute it proportionally
        if remaining_grt > 0 and allocations:
            total_allocated = sum(allocations.values())
            for ipfs_hash in allocations:
                portion = allocations[ipfs_hash] / total_allocated
                allocations[ipfs_hash] += remaining_grt * portion
        
        # Calculate final metrics
        earnings, apr = self.calculate_portfolio_metrics(allocations)
        
        return AllocationResult(
            allocations=allocations,
            total_allocated=float(sum(allocations.values())),
            expected_apr=apr,
            expected_earnings=earnings
        )
