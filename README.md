# Curation Signal Optimizer

An app to find the best curation opportunities where the share of the 10% query fees going to the curators provides a high APR.

The app helps locate any low APR active signals, and identifies the best opportunities to move signal into.

## Project Structure

The application is organized into several modules:

```
python_app/
├── api/
│   ├── graph_api.py      # The Graph API interactions
│   └── supabase_api.py   # Supabase API interactions
├── models/
│   ├── opportunities.py  # Opportunity calculations
│   └── signals.py       # Signal-related calculations
├── ui/
│   └── tabs/
│       ├── summary_tab.py          # Summary view
│       ├── curation_signal_tab.py  # Current signals
│       ├── opportunities_tab.py    # New opportunities
│       └── subgraph_list_tab.py   # Full subgraph list
├── utils/
│   ├── config.py        # Configuration and environment
│   └── formatting.py    # Display formatting
└── streamlit_curation.py  # Main application
```

## Setup

1. Install dependencies:
```bash
cd python_app
pip install -r requirements.txt
```

2. Create a `.env` file in the python_app directory with the following variables:
```env
SUPABASE_USERNAME=your_username
SUPABASE_PASSWORD=your_password
THEGRAPH_API_KEY=your_api_key
```

3. Run the application:
```bash
cd python_app
streamlit run streamlit_curation.py
```

## Features

- **Summary Tab**: Overview of your curation portfolio with total signal, APR, and earnings estimates
- **Current Curation Signal**: Detailed view of your active signals with performance metrics
- **Find Opportunities**: Tool to discover and analyze new curation opportunities
- **Full Subgraph List**: Complete list of subgraphs with key metrics and download option

## Development

When making changes to the curation streamlit app shown on the website:
```bash
sudo supervisorctl restart streamlit_curation
```

## Components

### API Layer
- `graph_api.py`: Handles all interactions with The Graph API, including fetching deployments, prices, and user signals
- `supabase_api.py`: Manages Supabase interactions for query volume data

### Models
- `opportunities.py`: Contains the Opportunity data class and calculation logic
- `signals.py`: Handles user signal calculations and optimal allocation strategies

### UI Components
- Each tab is modularized in its own file under `ui/tabs/`
- Components use shared formatting utilities for consistent display

### Utilities
- `config.py`: Centralizes configuration and environment variables
- `formatting.py`: Provides consistent formatting for currency, GRT amounts, and percentages

## Data Sources

- The Graph API: Subgraph deployments, GRT price, and user signals
- Supabase: Query volume and fee data

## Deployment

The application can be run locally for development or deployed using supervisor for production:

1. Local development:
```bash
streamlit run streamlit_curation.py
```

2. Production deployment:
```bash
sudo supervisorctl restart streamlit_curation
