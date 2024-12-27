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
    STEP_SIZE = 10  # How much to increase allocations each time
    MAX_ITERATIONS = 1000  # Prevent infinite loops
    
    def __init__(self, opportunities: List[Opportunity], grt_price: float):
        self.opportunities = opportunities
        self.grt_price = grt_price
    
    def calculate_opportunity_apr(self, opp: Opportunity, additional_signal: float) -> tuple:
        """Calculate APR and earnings for an opportunity with additional signal."""
        # Calculate total signal after allocation
        signal_amount = opp.signal_amount + additional_signal
        signalled_tokens = opp.signalled_tokens + additional_signal
        
        # Calculate total earnings based on $4 per 100,000 queries
        total_earnings = (opp.annual_queries / 100000) * self.EARNINGS_PER_100K_QUERIES
        
        # Calculate curator share (10% of total earnings)
        curator_share = total_earnings * self.CURATOR_SHARE
        
        # Calculate portion owned
        portion_owned = signal_amount / signalled_tokens if signalled_tokens > 0 else 0
        
        # Calculate estimated earnings
        estimated_earnings = curator_share * portion_owned
        
        # Calculate APR
        apr = (estimated_earnings / (signal_amount * self.grt_price)) * 100 if signal_amount > 0 else 0
        
        return apr, estimated_earnings

    def find_best_opportunity(self, current_allocations: Dict[str, float], step_size: float) -> tuple:
        """Find the best opportunity for the next allocation step."""
        best_apr = -1
        best_opp = None
        best_metrics = None
        
        for opp in self.opportunities:
            current_allocation = current_allocations.get(opp.ipfs_hash, 0)
            
            # Skip if we've hit the 10% limit
            if current_allocation >= self.total_grt * 0.10:
                continue
            
            # Calculate APR with additional step_size allocation
            apr, earnings = self.calculate_opportunity_apr(
                opp,
                current_allocation + step_size
            )
            
            # Consider entry cost if this is a new position
            if current_allocation == 0:
                apr -= (self.ENTRY_COST_PERCENTAGE * 100)
            
            if apr > best_apr:
                best_apr = apr
                best_opp = opp
                best_metrics = (apr, earnings)
        
        return best_opp, best_metrics

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
        position_aprs = []
        for opp in self.opportunities:
            allocation = allocations.get(opp.ipfs_hash, 0)
            if allocation > 0:
                apr, earnings = self.calculate_opportunity_apr(opp, allocation)
                total_earnings += earnings
                position_aprs.append(apr)
        
        # Subtract entry costs from earnings
        net_earnings = total_earnings - (total_entry_cost * self.grt_price)
        
        # Calculate average APR
        portfolio_apr = sum(position_aprs) / len(position_aprs) if position_aprs else 0
        
        return net_earnings, portfolio_apr

    def optimize_allocation(self, available_grt: float) -> AllocationResult:
        """Optimize GRT allocation using iterative approach."""
        if available_grt <= 0:
            raise Exception("Available GRT must be greater than 0")
        
        self.total_grt = available_grt  # Store for 10% limit check
        allocations = {}
        remaining_grt = available_grt
        iterations = 0
        current_step = self.STEP_SIZE
        
        while remaining_grt > 0 and iterations < self.MAX_ITERATIONS:
            iterations += 1
            made_progress = False
            
            # Adjust step size if needed
            if current_step > remaining_grt:
                current_step = remaining_grt
            
            # Try to find best opportunity
            best_opp, metrics = self.find_best_opportunity(allocations, current_step)
            
            if not best_opp or not metrics:
                # If no opportunities found with current step size, try smaller step
                if current_step > 10:
                    current_step = max(10, current_step / 2)
                    continue
                else:
                    break
            
            # Calculate how much we can allocate
            current_allocation = allocations.get(best_opp.ipfs_hash, 0)
            max_allocation = min(
                self.total_grt * 0.10,  # 10% limit
                remaining_grt  # Can't allocate more than we have
            )
            space_available = max_allocation - current_allocation
            
            if space_available <= 0:
                continue
            
            # Allocate what we can
            allocation_size = min(current_step, space_available)
            if allocation_size > 0:
                if best_opp.ipfs_hash in allocations:
                    allocations[best_opp.ipfs_hash] += allocation_size
                else:
                    allocations[best_opp.ipfs_hash] = allocation_size
                remaining_grt -= allocation_size
                made_progress = True
            
            # If we couldn't make progress with any opportunity, reduce step size
            if not made_progress and current_step > 10:
                current_step = max(10, current_step / 2)
            
            # Break if we can't make progress even with minimum step
            if not made_progress and current_step <= 10:
                break
        
        # Calculate final metrics
        earnings, apr = self.calculate_portfolio_metrics(allocations)
        
        return AllocationResult(
            allocations=allocations,
            total_allocated=float(sum(allocations.values())),
            expected_apr=apr,
            expected_earnings=earnings
        )
