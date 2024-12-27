def color_apr(val):
    """Apply color formatting to APR values in tables."""
    if val is None or val == '-':
        return 'color: gray'
    try:
        val = float(val)
        if val > 5:
            color = 'green'
        elif val < 1:
            color = 'red'
        else:
            color = 'black'
        return f'color: {color}'
    except ValueError:
        return 'color: gray'

def format_currency(amount: float, decimals: int = 2) -> str:
    """Format a number as currency with commas and specified decimal places."""
    return f"${amount:,.{decimals}f}"

def format_grt(amount: float, decimals: int = 2) -> str:
    """Format a number as GRT with commas and specified decimal places."""
    return f"{amount:,.{decimals}f} GRT"

def format_percentage(value: float, decimals: int = 2) -> str:
    """Format a number as a percentage with specified decimal places."""
    return f"{value:.{decimals}f}%"
