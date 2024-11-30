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
    STEP_SIZE = 100  # Base step size
    
    def __init__(self, opportunities: List[Opportunity], grt_price: float):
        # Sort opportunities by query volume to signal ratio
        self.opportunities = sorted(
            opportunities,
            key=lambda x: (x.weekly_queries / (x.signalled_tokens + 1)) * (x.apr / 100),
            reverse=True
        )
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
        best_score = -1
        best_opp = None
        best_metrics = None
        
        for opp in self.opportunities:
            current_allocation = current_allocations.get(opp.ipfs_hash, 0)
            
            # Skip if we already have significant allocation
            if current_allocation > opp.signalled_tokens * 0.3:
                continue
            
            # Calculate metrics with additional step_size allocation
            apr, earnings = self.calculate_opportunity_metrics(opp, current_allocation + step_size)
            
            # Consider entry cost if this is a new position
            if current_allocation == 0:
                apr -= (self.ENTRY_COST_PERCENTAGE * 100)
            
            # Calculate opportunity score based on multiple factors
            query_to_signal_ratio = opp.weekly_queries / (opp.signalled_tokens + current_allocation + 1)
            earnings_potential = earnings * (1 + query_to_signal_ratio)
            
            # Score considers both immediate APR and growth potential
            score = apr * query_to_signal_ratio * (1 + earnings_potential)
            
            if score > best_score:
                best_score = score
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
                apr, earnings = self.calculate_opportunity_metrics(opp, allocation)
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
        
        allocations = {}
        remaining_grt = available_grt
        
        # Initial larger steps to quickly capture best opportunities
        current_step = self.STEP_SIZE * 2
        min_step = self.STEP_SIZE / 2
        
        while remaining_grt >= min_step:
            best_opp, metrics = self.find_best_opportunity(allocations, current_step)
            
            if not best_opp or not metrics:
                # Reduce step size if no good opportunities found
                if current_step > min_step:
                    current_step = max(current_step / 2, min_step)
                    continue
                break
            
            apr, _ = metrics
            
            # Skip if APR is too low
            if apr < 5:  # 5% minimum APR threshold
                if current_step > min_step:
                    current_step = max(current_step / 2, min_step)
                    continue
                break
            
            # Calculate allocation for this opportunity
            current_allocation = allocations.get(best_opp.ipfs_hash, 0)
            
            # Determine allocation size based on opportunity quality
            if apr > 50:  # Very good opportunity
                allocation_size = min(current_step * 2, remaining_grt)
            elif apr > 20:  # Good opportunity
                allocation_size = min(current_step, remaining_grt)
            else:  # Decent opportunity
                allocation_size = min(current_step / 2, remaining_grt)
            
            # Update allocation
            allocations[best_opp.ipfs_hash] = current_allocation + allocation_size
            remaining_grt -= allocation_size
            
            # Adjust step size based on remaining GRT
            if remaining_grt < available_grt * 0.2:  # Last 20%
                current_step = min_step
        
        # Calculate final metrics
        earnings, apr = self.calculate_portfolio_metrics(allocations)
        
        return AllocationResult(
            allocations=allocations,
            total_allocated=float(sum(allocations.values())),
            expected_apr=apr,
            expected_earnings=earnings
        )
