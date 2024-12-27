from typing import Dict, List, Optional
from dataclasses import dataclass
from models.opportunities import Opportunity

@dataclass
class UserOpportunity:
    """Data class representing a user's curation opportunity."""
    ipfs_hash: str
    user_signal: float
    total_signal: float
    portion_owned: float
    estimated_earnings: float
    apr: float
    weekly_queries: int

def calculate_user_opportunities(
    user_signals: Dict[str, float],
    opportunities: List[Opportunity],
    grt_price: float
) -> List[UserOpportunity]:
    """Calculate user-specific opportunities from their current signals."""
    user_opportunities = []
    
    for opp in opportunities:
        ipfs_hash = opp.ipfs_hash
        
        if ipfs_hash in user_signals:
            user_signal = user_signals[ipfs_hash]
            total_signal = opp.signalled_tokens
            portion_owned = user_signal / total_signal if total_signal > 0 else 0
            estimated_earnings = opp.curator_share * portion_owned
            apr = (estimated_earnings / (user_signal * grt_price)) * 100 if user_signal > 0 else 0
            
            user_opportunities.append(UserOpportunity(
                ipfs_hash=ipfs_hash,
                user_signal=user_signal,
                total_signal=total_signal,
                portion_owned=portion_owned,
                estimated_earnings=estimated_earnings,
                apr=apr,
                weekly_queries=opp.weekly_queries
            ))
    
    return sorted(user_opportunities, key=lambda x: x.apr, reverse=True)

def calculate_optimal_allocations(
    opportunities: List[Opportunity],
    user_signals: Dict[str, float],
    total_signal: float,
    grt_price: float,
    num_subgraphs: int
) -> Dict[str, float]:
    """Calculate optimal allocation of signals considering current holdings."""
    # Adjust opportunities based on user's current allocations
    adjusted_opportunities = []
    for opp in opportunities:
        if opp.ipfs_hash in user_signals:
            user_signal = user_signals[opp.ipfs_hash]
            adjusted_signalled_tokens = opp.signalled_tokens - user_signal
            
            # Create adjusted opportunity
            adjusted_opp = Opportunity(
                ipfs_hash=opp.ipfs_hash,
                signal_amount=0,  # Reset signal amount for recalculation
                signalled_tokens=adjusted_signalled_tokens,
                annual_queries=opp.annual_queries,
                total_earnings=opp.total_earnings,
                curator_share=opp.curator_share,
                estimated_earnings=opp.estimated_earnings,
                apr=opp.apr,
                weekly_queries=opp.weekly_queries
            )
            adjusted_opportunities.append(adjusted_opp)
        else:
            adjusted_opportunities.append(opp)

    # Sort adjusted opportunities by APR in descending order
    adjusted_opportunities.sort(key=lambda x: x.apr, reverse=True)

    # Select top opportunities
    top_opportunities = adjusted_opportunities[:num_subgraphs]

    # Initialize allocation dictionary
    allocations = {opp.ipfs_hash: 0 for opp in top_opportunities}
    remaining_signal = total_signal

    # Iterative allocation process
    while remaining_signal > 0:
        best_apr = -1
        best_opp = None

        for opp in top_opportunities:
            ipfs_hash = opp.ipfs_hash
            signal_amount = opp.signal_amount + allocations[ipfs_hash]
            signalled_tokens = opp.signalled_tokens + allocations[ipfs_hash]
            
            # Calculate APR if we add 100 more tokens
            new_signal_amount = signal_amount + 100
            new_signalled_tokens = signalled_tokens + 100
            portion_owned = new_signal_amount / new_signalled_tokens
            estimated_earnings = opp.curator_share * portion_owned
            apr = (estimated_earnings / (new_signal_amount * grt_price)) * 100

            if apr > best_apr:
                best_apr = apr
                best_opp = opp

        # Allocate 100 tokens to the best opportunity
        if best_opp:
            allocations[best_opp.ipfs_hash] += min(100, remaining_signal)
            remaining_signal -= 100
        else:
            break

    return allocations
