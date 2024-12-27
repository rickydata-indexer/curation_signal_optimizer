import pytest
import numpy as np
from models.opportunities import Opportunity
from models.allocation.optimizer import AllocationOptimizer, AllocationResult

@pytest.fixture
def sample_opportunities():
    """Create sample opportunities for testing."""
    return [
        Opportunity(
            ipfs_hash="hash1",
            signal_amount=1000,
            signalled_tokens=10000,
            annual_queries=1000000,
            total_earnings=40,  # $4 per 100k queries
            curator_share=4,    # 10% of total earnings
            estimated_earnings=0.4,  # Based on current signal
            apr=5.0,
            weekly_queries=19230  # Roughly 1M annual
        ),
        Opportunity(
            ipfs_hash="hash2",
            signal_amount=2000,
            signalled_tokens=20000,
            annual_queries=2000000,
            total_earnings=80,
            curator_share=8,
            estimated_earnings=0.8,
            apr=4.0,
            weekly_queries=38460
        ),
        Opportunity(
            ipfs_hash="hash3",
            signal_amount=500,
            signalled_tokens=5000,
            annual_queries=500000,
            total_earnings=20,
            curator_share=2,
            estimated_earnings=0.2,
            apr=6.0,
            weekly_queries=9615
        )
    ]

@pytest.fixture
def diverse_opportunities():
    """Create more diverse opportunities for testing."""
    return [
        # High APR, low signal - emerging opportunity
        Opportunity(
            ipfs_hash="high_apr_low_signal",
            signal_amount=1000,
            signalled_tokens=10000,
            annual_queries=2000000,
            total_earnings=80,
            curator_share=8,
            estimated_earnings=0.8,
            apr=12.0,
            weekly_queries=38460
        ),
        # Medium APR, medium signal - established subgraph
        Opportunity(
            ipfs_hash="med_apr_med_signal",
            signal_amount=10000,
            signalled_tokens=100000,
            annual_queries=5000000,
            total_earnings=200,
            curator_share=20,
            estimated_earnings=2.0,
            apr=6.0,
            weekly_queries=96150
        ),
        # Low APR, high signal - mature subgraph
        Opportunity(
            ipfs_hash="low_apr_high_signal",
            signal_amount=50000,
            signalled_tokens=500000,
            annual_queries=10000000,
            total_earnings=400,
            curator_share=40,
            estimated_earnings=4.0,
            apr=3.0,
            weekly_queries=192300
        ),
        # Very high APR, very low signal - new opportunity
        Opportunity(
            ipfs_hash="very_high_apr_very_low_signal",
            signal_amount=500,
            signalled_tokens=5000,
            annual_queries=1000000,
            total_earnings=40,
            curator_share=4,
            estimated_earnings=0.4,
            apr=15.0,
            weekly_queries=19230
        )
    ]

def test_allocation_optimizer_initialization(sample_opportunities):
    """Test optimizer initialization."""
    grt_price = 0.1
    optimizer = AllocationOptimizer(sample_opportunities, grt_price)
    assert len(optimizer.opportunities) == 3
    assert optimizer.grt_price == 0.1

def test_portfolio_metrics_calculation(sample_opportunities):
    """Test portfolio metrics calculation."""
    grt_price = 0.1
    optimizer = AllocationOptimizer(sample_opportunities, grt_price)
    
    # Test with equal allocations
    allocations = np.array([1000, 1000, 1000])
    earnings, apr = optimizer.calculate_portfolio_metrics(allocations)
    
    assert earnings > 0
    assert apr > 0

def test_optimize_allocation(sample_opportunities):
    """Test allocation optimization."""
    grt_price = 0.1
    optimizer = AllocationOptimizer(sample_opportunities, grt_price)
    
    available_grt = 5000
    result = optimizer.optimize_allocation(available_grt)
    
    assert isinstance(result, AllocationResult)
    assert abs(result.total_allocated - available_grt) < 0.01  # Should allocate all available GRT
    assert result.expected_apr > 0
    assert result.expected_earnings > 0
    assert len(result.allocations) <= len(sample_opportunities)

def test_min_allocation_constraint(sample_opportunities):
    """Test minimum allocation constraint."""
    grt_price = 0.1
    optimizer = AllocationOptimizer(sample_opportunities, grt_price)
    
    available_grt = 5000
    min_allocation = 500
    result = optimizer.optimize_allocation(available_grt, min_allocation)
    
    # Check that all allocations meet minimum requirement
    for allocation in result.allocations.values():
        assert allocation >= min_allocation

def test_zero_available_grt(sample_opportunities):
    """Test optimization with zero available GRT."""
    grt_price = 0.1
    optimizer = AllocationOptimizer(sample_opportunities, grt_price)
    
    with pytest.raises(Exception):
        optimizer.optimize_allocation(0)

def test_allocation_sum_constraint(sample_opportunities):
    """Test that allocations sum to available GRT."""
    grt_price = 0.1
    optimizer = AllocationOptimizer(sample_opportunities, grt_price)
    
    available_grt = 5000
    result = optimizer.optimize_allocation(available_grt)
    
    total_allocated = sum(result.allocations.values())
    assert abs(total_allocated - available_grt) < 0.01

def test_optimization_improves_apr(diverse_opportunities):
    """Test that optimization improves APR compared to equal allocation."""
    grt_price = 0.1
    optimizer = AllocationOptimizer(diverse_opportunities, grt_price)
    
    available_grt = 10000
    
    # Calculate APR with equal allocation
    equal_allocation = np.full(len(diverse_opportunities), available_grt / len(diverse_opportunities))
    _, equal_apr = optimizer.calculate_portfolio_metrics(equal_allocation)
    
    # Get optimized allocation
    result = optimizer.optimize_allocation(available_grt)
    
    # Optimized APR should be better than equal allocation
    assert result.expected_apr > equal_apr

def test_diverse_scenario_optimization(diverse_opportunities):
    """Test optimization with diverse opportunities."""
    grt_price = 0.1
    optimizer = AllocationOptimizer(diverse_opportunities, grt_price)
    
    available_grt = 10000
    result = optimizer.optimize_allocation(available_grt)
    
    # Higher APR opportunities should get more allocation
    allocations = [(opp.ipfs_hash, result.allocations.get(opp.ipfs_hash, 0))
                   for opp in diverse_opportunities]
    allocations.sort(key=lambda x: x[1], reverse=True)
    
    # The highest APR opportunity should get significant allocation
    assert allocations[0][0] in ["very_high_apr_very_low_signal", "high_apr_low_signal"]
    
    # But not all funds (due to risk management)
    assert allocations[0][1] < available_grt * 0.5
